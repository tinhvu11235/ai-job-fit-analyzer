import asyncio
import json
import os
import re
import shutil
import socket
import subprocess
import tempfile
import time
import unicodedata
from pathlib import Path
from urllib.parse import quote, urlencode, urljoin

import httpx
from bs4 import BeautifulSoup

from app.config import get_settings
from app.schemas import (
    AnalyzeRequest,
    TopCVJobRecommendRequest,
    TopCVJobResult,
    TopCVJobSearchRequest,
    TopCVJobSearchResponse,
)
from app.services.local_analyzer import analyze_fit_locally, normalize_jd_locally
from app.services.browser_crawler import fetch_rendered_html
from app.services.source_loader import clean_text


TOPCV_BASE_URL = "https://www.topcv.vn"
TOPCV_SEARCH_URL = f"{TOPCV_BASE_URL}/tim-viec-lam-moi-nhat"
DETAIL_PATH_RE = re.compile(r"/viec-lam/[^\"'#?]+", re.IGNORECASE)
TOPCV_BLOCKED_STATUS_CODES = {403, 429}
ZERO_RESULT_RE = re.compile(r"tuyển\s+dụng\s+0\s+việc\s+làm", re.IGNORECASE)
SALARY_RE = re.compile(
    r"(?i)(?:\d{1,3}\s*(?:tr|triệu|million|m)\s*(?:-|–|đến)?\s*\d{0,3}\s*(?:tr|triệu|million|m)?|"
    r"thỏa thuận|cạnh tranh|lên tới\s*\d{1,3}\s*(?:tr|triệu|m))"
)

EDGE_CANDIDATES = (
    r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe",
    r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe",
    r"%LocalAppData%\Microsoft\Edge\Application\msedge.exe",
)
CITY_WORDS = (
    "Hà Nội",
    "Hồ Chí Minh",
    "TP. HCM",
    "Đà Nẵng",
    "Hải Phòng",
    "Cần Thơ",
    "Bình Dương",
    "Đồng Nai",
    "Remote",
    "Toàn Quốc",
)
STOPWORDS = {
    "and",
    "the",
    "for",
    "with",
    "job",
    "viec",
    "lam",
    "cong",
    "ty",
    "kinh",
    "nghiem",
    "ung",
    "vien",
    "cau",
    "yeu",
    "duoc",
    "cac",
    "cho",
}

ROLE_KEYWORDS = (
    ("ai engineer", "AI Engineer"),
    ("machine learning engineer", "Machine Learning Engineer"),
    ("data scientist", "Data Scientist"),
    ("data engineer", "Data Engineer"),
    ("backend engineer", "Backend Engineer"),
    ("software engineer", "Software Engineer"),
    ("python developer", "Python Developer"),
)

SKILL_KEYWORDS = (
    "Python",
    "Machine Learning",
    "Deep Learning",
    "Computer Vision",
    "NLP",
    "RAG",
    "LLM",
    "Semantic Search",
    "PyTorch",
    "TensorFlow",
    "FastAPI",
    "Docker",
    "SQL",
)


def _slugify_keyword(keyword: str) -> str:
    normalized = unicodedata.normalize("NFD", keyword.strip().lower().replace("đ", "d"))
    ascii_text = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", ascii_text).strip("-")


def build_topcv_search_url(request: TopCVJobSearchRequest) -> str:
    slug = _slugify_keyword(request.keyword)
    if slug:
        url = f"{TOPCV_BASE_URL}/tim-viec-lam-{slug}"
        if request.page > 1:
            return f"{url}?{urlencode({'page': request.page})}"
        return url

    params = {"keyword": request.keyword, "page": request.page}
    return f"{TOPCV_SEARCH_URL}?{urlencode(params)}"


def _find_edge_executable(configured_path: str | None) -> str | None:
    candidates = [configured_path, *EDGE_CANDIDATES]
    for candidate in candidates:
        if not candidate:
            continue
        expanded = os.path.expandvars(candidate)
        if Path(expanded).is_file():
            return expanded

    return shutil.which("msedge") or shutil.which("microsoft-edge") or shutil.which("microsoft-edge-stable")


def _free_local_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


async def _wait_for_edge_target(port: int, target_url: str, timeout_seconds: float) -> str | None:
    base_url = f"http://127.0.0.1:{port}"
    deadline = time.monotonic() + min(8.0, max(2.0, timeout_seconds / 2))

    async with httpx.AsyncClient(timeout=1.5, trust_env=False) as client:
        while time.monotonic() < deadline:
            try:
                response = await client.get(f"{base_url}/json/version")
                if response.status_code == 200:
                    break
            except httpx.HTTPError:
                pass
            await asyncio.sleep(0.25)
        else:
            return None

        try:
            response = await client.put(f"{base_url}/json/new?{quote('about:blank', safe='')}")
            response.raise_for_status()
            payload = response.json()
            websocket_url = payload.get("webSocketDebuggerUrl")
            if isinstance(websocket_url, str) and websocket_url:
                return websocket_url
        except (httpx.HTTPError, json.JSONDecodeError):
            pass

        try:
            response = await client.get(f"{base_url}/json")
            response.raise_for_status()
            targets = response.json()
        except (httpx.HTTPError, json.JSONDecodeError):
            return None

    if not isinstance(targets, list):
        return None
    for target in targets:
        if isinstance(target, dict) and target.get("type") == "page":
            websocket_url = target.get("webSocketDebuggerUrl")
            if isinstance(websocket_url, str) and websocket_url:
                return websocket_url
    return None


async def _cdp_call(websocket, message_id: int, method: str, params: dict[str, object] | None = None) -> dict:
    await websocket.send(json.dumps({"id": message_id, "method": method, "params": params or {}}))
    while True:
        payload = json.loads(await websocket.recv())
        if payload.get("id") == message_id:
            return payload


def _runtime_value(payload: dict) -> str:
    result = payload.get("result")
    if not isinstance(result, dict):
        return ""
    runtime_result = result.get("result")
    if not isinstance(runtime_result, dict):
        return ""
    value = runtime_result.get("value")
    return value if isinstance(value, str) else ""


async def _read_rendered_html(websocket_url: str, target_url: str, timeout_seconds: float) -> str:
    import asyncio
    import websockets

    html = ""
    message_id = 0

    async with websockets.connect(websocket_url, max_size=25_000_000, proxy=None) as websocket:
        for method in ("Page.enable", "Runtime.enable"):
            message_id += 1
            await asyncio.wait_for(_cdp_call(websocket, message_id, method), timeout=5.0)

        message_id += 1
        await asyncio.wait_for(
            _cdp_call(websocket, message_id, "Page.navigate", {"url": target_url}),
            timeout=5.0,
        )

        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            await asyncio.sleep(0.75)

            message_id += 1
            ready_state = _runtime_value(
                await asyncio.wait_for(
                    _cdp_call(
                        websocket,
                        message_id,
                        "Runtime.evaluate",
                        {"expression": "document.readyState", "returnByValue": True},
                    ),
                    timeout=5.0,
                )
            )

            message_id += 1
            html = _runtime_value(
                await asyncio.wait_for(
                    _cdp_call(
                        websocket,
                        message_id,
                        "Runtime.evaluate",
                        {"expression": "document.documentElement.outerHTML", "returnByValue": True},
                    ),
                    timeout=5.0,
                )
            )

            if ready_state == "complete" and DETAIL_PATH_RE.search(html):
                await asyncio.sleep(1.0)
                message_id += 1
                final_html = _runtime_value(
                    await asyncio.wait_for(
                        _cdp_call(
                            websocket,
                            message_id,
                            "Runtime.evaluate",
                            {"expression": "document.documentElement.outerHTML", "returnByValue": True},
                        ),
                        timeout=5.0,
                    )
                )
                return final_html or html

    return html


async def fetch_topcv_with_edge(search_url: str) -> tuple[str, str | None]:
    settings = get_settings()
    edge_path = _find_edge_executable(settings.topcv_edge_path)
    if not edge_path:
        return "", "Không tìm thấy Microsoft Edge local để crawl TopCV bằng trình duyệt."

    port = _free_local_port()
    user_data_dir = tempfile.mkdtemp(prefix="topcv-edge-")
    args = [
        edge_path,
        "--disable-extensions",
        "--disable-background-networking",
        "--disable-dev-shm-usage",
        "--no-first-run",
        "--no-default-browser-check",
        "--remote-allow-origins=*",
        f"--remote-debugging-port={port}",
        f"--user-data-dir={user_data_dir}",
        "about:blank",
    ]
    if settings.topcv_edge_headless:
        args[1:1] = ["--headless=new", "--disable-gpu"]
    else:
        args[1:1] = ["--start-minimized"]

    process: subprocess.Popen | None = None
    try:
        process = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        websocket_url = await _wait_for_edge_target(port, search_url, settings.topcv_browser_timeout_seconds)
        if not websocket_url:
            return "", "Không mở được phiên CDP của Edge để crawl TopCV."

        html = await _read_rendered_html(websocket_url, search_url, settings.topcv_browser_timeout_seconds)
        if not html:
            return "", "Edge đã mở TopCV nhưng không trả về HTML sau khi render."
        return html, None
    except Exception as exc:
        return "", f"Không thể crawl TopCV bằng Edge local: {exc}"
    finally:
        if process is not None:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
        shutil.rmtree(user_data_dir, ignore_errors=True)


def derive_topcv_keywords_from_cv(cv_text: str) -> list[str]:
    lowered = cv_text.lower()
    roles: list[str] = []
    for needle, label in ROLE_KEYWORDS:
        pattern = rf"(?<![a-z]){re.escape(needle)}(?![a-z])"
        if re.search(pattern, lowered):
            roles.append(label)

    skills: list[str] = []
    for skill in SKILL_KEYWORDS:
        if skill.lower() in lowered:
            skills.append(skill)

    role = roles[0] if roles else "AI Engineer"
    supporting = [item for item in skills if item != role][:2]
    primary_query = " ".join([role, *supporting]).strip()

    return list(dict.fromkeys([primary_query, role, *skills, *roles[1:]]))[:8]


def _content_words(text: str | None) -> set[str]:
    if not text:
        return set()
    words = re.findall(r"[a-zA-ZÀ-ỹ0-9+#.]{3,}", text.lower())
    return {word for word in words if word not in STOPWORDS}


def _fold_text(text: str | None) -> str:
    if not text:
        return ""
    normalized = unicodedata.normalize("NFD", text.lower().replace("đ", "d"))
    return "".join(char for char in normalized if unicodedata.category(char) != "Mn")


def _semantic_fit_reasons(keyword: str, cv_text: str | None, haystack: str) -> list[str]:
    intent = _fold_text(" ".join([keyword, cv_text or ""]))
    target = _fold_text(haystack)
    rules = (
        (
            "Khớp nhóm AI/ML",
            ("ai engineer", "machine learning", "deep learning", "artificial intelligence"),
            ("ai engineer", "ky su ai", "tri tue nhan tao", "ai/ml", "ai automation", "ung dung ai"),
        ),
        (
            "Khớp nhóm LLM/RAG/AI Agent",
            ("llm", "rag", "ai agent"),
            ("llm", "rag", "ai agent", "agent"),
        ),
        (
            "Khớp Python",
            ("python",),
            ("python",),
        ),
        (
            "Khớp Computer Vision",
            ("computer vision",),
            ("computer vision", "thi giac may tinh"),
        ),
        (
            "Khớp NLP",
            ("nlp", "natural language"),
            ("nlp", "xu ly ngon ngu"),
        ),
    )

    reasons: list[str] = []
    for label, intent_terms, target_terms in rules:
        if any(term in intent for term in intent_terms) and any(term in target for term in target_terms):
            reasons.append(label)
    return reasons


def _nearest_card_text(anchor) -> str:
    current = anchor
    for _ in range(5):
        if current is None:
            break
        class_text = " ".join(current.get("class", [])) if hasattr(current, "get") else ""
        if current.name in {"article", "li"} or "job" in class_text.lower() or "card" in class_text.lower():
            return clean_text(current.get_text(" "))
        current = current.parent
    return clean_text(anchor.parent.get_text(" ") if anchor.parent else anchor.get_text(" "))


def _extract_company(title: str, card_text: str) -> str | None:
    lines = [clean_text(line) for line in re.split(r"[\n\r]+| {2,}", card_text) if clean_text(line)]
    for line in lines:
        if line == title or len(line) < 3:
            continue
        lowered = line.lower()
        if any(marker in lowered for marker in ("công ty", "company", "tnhh", "jsc", "cp ", "corporation")):
            cleaned = line.replace(title, " ")
            salary_match = SALARY_RE.search(cleaned)
            if salary_match:
                cleaned = cleaned[: salary_match.start()]
            for city in CITY_WORDS:
                cleaned = re.sub(re.escape(city), " ", cleaned, flags=re.IGNORECASE)
            cleaned = clean_text(cleaned)
            match = re.search(
                r"(?i)(công\s+ty|company|tnhh|jsc|corporation|cp\s+).+",
                cleaned,
            )
            return clean_text(match.group(0) if match else cleaned)[:160] or None
    return None


def _extract_location(card_text: str) -> str | None:
    found = [city for city in CITY_WORDS if city.lower() in card_text.lower()]
    return ", ".join(dict.fromkeys(found)) or None


def _extract_salary(card_text: str) -> str | None:
    match = SALARY_RE.search(card_text)
    return clean_text(match.group(0)) if match else None


def _score_job(result: TopCVJobResult, cv_text: str | None, keyword: str) -> TopCVJobResult:
    haystack = " ".join(
        part
        for part in (result.title, result.company_name, result.location, result.salary, result.snippet)
        if part
    )
    cv_words = _content_words(cv_text)
    job_words = _content_words(haystack)
    keyword_words = _content_words(keyword)

    overlap = sorted((cv_words | keyword_words) & job_words)
    score = 30
    if keyword_words & job_words:
        score += 30
    score += min(35, len(overlap) * 7)
    if result.salary:
        score += 3
    if result.location:
        score += 2
    semantic_reasons = _semantic_fit_reasons(keyword, cv_text, haystack)
    score += min(25, len(semantic_reasons) * 12)
    score = max(0, min(100, score))

    reasons: list[str] = []
    if keyword_words & job_words:
        reasons.append("Khớp từ khóa tìm kiếm")
    reasons.extend(semantic_reasons)
    if cv_words and overlap:
        reasons.append("Có tín hiệu trùng với CV: " + ", ".join(overlap[:5]))
    if result.salary:
        reasons.append("Có thông tin lương")
    return result.model_copy(update={"fit_score": score, "fit_reasons": reasons})


def _job_to_analysis_text(job: TopCVJobResult) -> str:
    parts = [
        f"Job title: {job.title}",
        f"Company: {job.company_name}" if job.company_name else "",
        f"Location: {job.location}" if job.location else "",
        f"Salary: {job.salary}" if job.salary else "",
        f"TopCV URL: {job.url}",
        "Source note: Nội dung bên dưới được trích từ card kết quả TopCV. Mở link gốc để đọc JD đầy đủ trước khi ứng tuyển.",
        f"Job card text: {job.snippet}" if job.snippet else "",
        f"Fit hints from crawler: {', '.join(job.fit_reasons)}" if job.fit_reasons else "",
    ]
    return clean_text("\n".join(part for part in parts if part), max_chars=6000)


async def analyze_topcv_response(
    response: TopCVJobSearchResponse,
    *,
    cv_text: str | None,
    analyze_limit: int,
    output_language: str,
    user_preferences: str | None = None,
) -> TopCVJobSearchResponse:
    if not cv_text or analyze_limit <= 0 or not response.results:
        return response

    analyzed_jobs: list[TopCVJobResult] = []
    analyzed_count = 0

    for job in response.results:
        if analyzed_count >= analyze_limit:
            analyzed_jobs.append(job)
            continue

        detail_text = _job_to_analysis_text(job)
        if len(detail_text) < 20:
            analyzed_jobs.append(
                job.model_copy(
                    update={
                        "analysis_status": "failed",
                        "analysis_error": "Không đủ dữ liệu JD từ TopCV để phân tích.",
                        "detail_text": detail_text,
                    }
                )
            )
            continue

        try:
            normalized = normalize_jd_locally(
                detail_text,
                source_type="text",
                warnings=["Phân tích nhanh từ thông tin card TopCV; hãy mở link gốc để kiểm tra JD đầy đủ."],
            )
            analysis = analyze_fit_locally(
                AnalyzeRequest(
                    cv_text=cv_text,
                    normalized_job_description=normalized,
                    user_preferences=user_preferences,
                    output_language=output_language,
                ),
                reason="Phân tích nhanh cục bộ cho kết quả TopCV để phản hồi ngay trong demo.",
            )
            analyzed_jobs.append(
                job.model_copy(
                    update={
                        "analysis_status": "ready",
                        "detail_text": detail_text,
                        "normalized_job_description": normalized,
                        "analysis": analysis,
                    }
                )
            )
            analyzed_count += 1
        except Exception as exc:
            analyzed_jobs.append(
                job.model_copy(
                    update={
                        "analysis_status": "failed",
                        "analysis_error": str(exc),
                        "detail_text": detail_text,
                    }
                )
            )

    warnings = [
        *response.warnings,
        f"Đã phân tích nhanh {analyzed_count} việc làm TopCV đầu tiên bằng thông tin crawl được.",
    ]
    return response.model_copy(
        update={
            "results": analyzed_jobs,
            "warnings": list(dict.fromkeys(warnings)),
        }
    )


def _result_from_json_ld(item: dict[str, object]) -> TopCVJobResult | None:
    item_type = item.get("@type")
    types = item_type if isinstance(item_type, list) else [item_type]
    if "JobPosting" not in types:
        return None
    title = clean_text(str(item.get("title") or ""))
    url = clean_text(str(item.get("url") or ""))
    if not title or not url:
        return None
    company = item.get("hiringOrganization")
    company_name = None
    if isinstance(company, dict):
        company_name = clean_text(str(company.get("name") or "")) or None
    description = BeautifulSoup(str(item.get("description") or ""), "html.parser").get_text(" ")
    return TopCVJobResult(
        title=title,
        company_name=company_name,
        location=clean_text(json.dumps(item.get("jobLocation"), ensure_ascii=False))[:180]
        if item.get("jobLocation")
        else None,
        salary=clean_text(json.dumps(item.get("baseSalary"), ensure_ascii=False))[:120]
        if item.get("baseSalary")
        else None,
        url=urljoin(TOPCV_BASE_URL, url),
        snippet=clean_text(description, max_chars=260) or None,
    )


def _flatten_json_ld(value: object) -> list[dict[str, object]]:
    if isinstance(value, list):
        result: list[dict[str, object]] = []
        for item in value:
            result.extend(_flatten_json_ld(item))
        return result
    if not isinstance(value, dict):
        return []
    result = [value]
    graph = value.get("@graph")
    if isinstance(graph, list):
        for item in graph:
            result.extend(_flatten_json_ld(item))
    return result


def parse_topcv_search_html(
    html: str,
    *,
    search_url: str,
    keyword: str,
    cv_text: str | None = None,
    limit: int = 8,
) -> tuple[list[TopCVJobResult], list[str]]:
    soup = BeautifulSoup(html, "html.parser")
    warnings: list[str] = []
    page_title = clean_text(soup.title.get_text(" ") if soup.title else "")
    if ZERO_RESULT_RE.search(page_title):
        warnings.append(f"TopCV chưa có kết quả trực tiếp cho từ khóa: {keyword}.")
        return [], warnings

    results: list[TopCVJobResult] = []
    seen_urls: set[str] = set()

    for script in soup.find_all("script", type=lambda value: value and "ld+json" in value):
        try:
            payload = json.loads(script.string or script.get_text())
        except json.JSONDecodeError:
            continue
        for item in _flatten_json_ld(payload):
            result = _result_from_json_ld(item)
            if result and result.url not in seen_urls:
                seen_urls.add(result.url)
                results.append(_score_job(result, cv_text, keyword))

    for anchor in soup.find_all("a", href=True):
        href = str(anchor["href"])
        if not DETAIL_PATH_RE.search(href) or "{{" in href:
            continue
        url = urljoin(search_url, href)
        if url in seen_urls:
            continue
        title = clean_text(anchor.get_text(" ") or anchor.get("title") or anchor.get("aria-label") or "")
        if not title or "{{" in title or len(title) < 4:
            continue
        card_text = _nearest_card_text(anchor)
        result = TopCVJobResult(
            title=title[:180],
            company_name=_extract_company(title, card_text),
            location=_extract_location(card_text),
            salary=_extract_salary(card_text),
            url=url,
            snippet=clean_text(card_text, max_chars=300) or None,
        )
        seen_urls.add(url)
        results.append(_score_job(result, cv_text, keyword))
        if len(results) >= limit:
            break

    if not results and "{{ job.title }}" in html:
        warnings.append(
            "TopCV đang render danh sách việc làm bằng JavaScript; HTML public không chứa dữ liệu job để đọc trực tiếp."
        )
    if not results:
        page_text = clean_text(soup.get_text(" "), max_chars=240)
        challenge_text = " ".join([page_title, page_text]).lower()
        if any(marker in challenge_text for marker in ("captcha", "cloudflare", "verify", "robot", "access denied")):
            warnings.append("TopCV đang trả trang xác minh/chống bot nên crawler không thể đọc danh sách job hợp lệ.")
        elif page_title or page_text:
            warnings.append(
                f"TopCV trả HTML nhưng không thấy job card. Tiêu đề: {page_title or 'không có'}; mẫu nội dung: {page_text or 'rỗng'}"
            )
        else:
            warnings.append("TopCV trả HTML rỗng hoặc không có nội dung job để đọc.")

    return sorted(results, key=lambda result: result.fit_score, reverse=True)[:limit], warnings


async def search_topcv_jobs(request: TopCVJobSearchRequest) -> TopCVJobSearchResponse:
    search_url = build_topcv_search_url(request)
    settings = get_settings()
    warnings: list[str] = []
    html = ""

    try:
        async with httpx.AsyncClient(
            timeout=20.0,
            follow_redirects=True,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml,text/plain;q=0.9,*/*;q=0.8",
                "Accept-Language": "vi,en-US;q=0.9,en;q=0.8",
            },
        ) as client:
            response = await client.get(search_url)
            if response.status_code in TOPCV_BLOCKED_STATUS_CODES:
                warnings.append(
                    f"TopCV từ chối request từ môi trường hiện tại (HTTP {response.status_code}). "
                    "Ứng dụng sẽ thử crawler Edge local nếu đã bật cấu hình; không bypass đăng nhập/CAPTCHA."
                )
            else:
                response.raise_for_status()
                html = response.text
    except httpx.HTTPError as exc:
        warnings.append(f"Không thể tải TopCV lúc này: {exc}")

    if not html and settings.topcv_enable_edge_crawler:
        warnings.append("Đang dùng Edge local để render TopCV và đọc danh sách việc làm.")
        html, edge_warning = await fetch_topcv_with_edge(search_url)
        if edge_warning:
            warnings.append(edge_warning)

    if not html and getattr(settings, "job_browser_crawler_enabled", False):
        warnings.append("Đang dùng Chromium headless trong container để render TopCV.")
        html, browser_warning = await fetch_rendered_html(
            search_url,
            getattr(settings, "job_browser_timeout_seconds", settings.topcv_browser_timeout_seconds),
        )
        if browser_warning:
            warnings.append(browser_warning)

    results: list[TopCVJobResult] = []
    if html:
        parsed_results, parse_warnings = parse_topcv_search_html(
            html,
            search_url=search_url,
            keyword=request.keyword,
            cv_text=request.cv_text,
            limit=request.limit,
        )
        results = parsed_results
        warnings.extend(parse_warnings)

    response = TopCVJobSearchResponse(
        query=request.keyword,
        search_url=search_url,
        results=results,
        warnings=list(dict.fromkeys(warnings)),
    )
    if request.analyze_results:
        return await analyze_topcv_response(
            response,
            cv_text=request.cv_text,
            analyze_limit=request.analyze_limit,
            output_language=request.output_language,
            user_preferences=request.user_preferences,
        )
    return response


async def recommend_topcv_jobs_from_cv(request: TopCVJobRecommendRequest) -> TopCVJobSearchResponse:
    suggested_keywords = derive_topcv_keywords_from_cv(request.cv_text)
    warnings = [f"Từ khóa suy ra từ CV: {suggested_keywords[0]}"]
    fallback_response: TopCVJobSearchResponse | None = None

    for keyword in suggested_keywords[:5]:
        search_request = TopCVJobSearchRequest(
            keyword=keyword,
            location=request.location,
            cv_text=request.cv_text,
            page=request.page,
            limit=request.limit,
            analyze_results=False,
        )
        response = await search_topcv_jobs(search_request)
        warnings.append(f"Đã thử TopCV với từ khóa: {keyword}")
        warnings.extend(response.warnings)
        if fallback_response is None:
            fallback_response = response
        if response.results:
            final_response = response.model_copy(
                update={
                    "suggested_keywords": suggested_keywords,
                    "warnings": list(dict.fromkeys(warnings)),
                }
            )
            if request.analyze_results:
                return await analyze_topcv_response(
                    final_response,
                    cv_text=request.cv_text,
                    analyze_limit=request.analyze_limit,
                    output_language=request.output_language,
                    user_preferences=request.user_preferences,
                )
            return final_response

    response = fallback_response or TopCVJobSearchResponse(
        query=suggested_keywords[0],
        suggested_keywords=suggested_keywords,
        search_url=build_topcv_search_url(
            TopCVJobSearchRequest(keyword=suggested_keywords[0], location=request.location, page=request.page)
        ),
        results=[],
        warnings=[],
    )
    final_response = response.model_copy(
        update={
            "suggested_keywords": suggested_keywords,
            "warnings": list(dict.fromkeys(warnings)),
        }
    )
    if request.analyze_results:
        return await analyze_topcv_response(
            final_response,
            cv_text=request.cv_text,
            analyze_limit=request.analyze_limit,
            output_language=request.output_language,
            user_preferences=request.user_preferences,
        )
    return final_response
