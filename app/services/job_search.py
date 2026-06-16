import asyncio
import html as html_lib
import json
import re
import unicodedata
from dataclasses import dataclass
from urllib.parse import urlencode, urljoin, urlparse, urlunparse

import httpx
from bs4 import BeautifulSoup

from app.config import get_settings
from app.schemas import (
    AnalyzeRequest,
    JobRecommendRequest,
    JobResult,
    JobSearchRequest,
    JobSearchResponse,
    JobSource,
    TopCVJobSearchRequest,
)
from app.services.browser_crawler import fetch_rendered_html
from app.services.local_analyzer import analyze_fit_locally, normalize_jd_locally
from app.services.source_loader import clean_text
from app.services.topcv_jobs import (
    build_topcv_search_url,
    derive_topcv_keywords_from_cv,
    parse_topcv_search_html,
    search_topcv_jobs,
)


SOURCE_LABELS: dict[str, str] = {
    "topcv": "TopCV",
    "joboko": "JobOKO",
    "vietnamworks": "VietnamWorks",
    "glints": "Glints",
    "itviec": "ITviec",
}

CITY_WORDS = (
    "Hà Nội",
    "Hồ Chí Minh",
    "TP. HCM",
    "TP HCM",
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
    "jobs",
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
SALARY_RE = re.compile(
    r"(?i)(?:"
    r"\$?\d{1,4}(?:[.,]\d+)?\s*(?:tr|triệu|million|m|usd|\$)"
    r"\s*(?:-|–|đến|to)?\s*\$?\d{0,4}(?:[.,]\d+)?\s*(?:tr|triệu|million|m|usd|\$)?"
    r"|thỏa thuận|cạnh tranh|negotiable|competitive|lên tới\s*\d{1,4}\s*(?:tr|triệu|m)"
    r")"
)
CHALLENGE_MARKERS = ("captcha", "cloudflare", "verify", "robot", "access denied", "forbidden")


@dataclass(frozen=True)
class JobProvider:
    source: JobSource
    label: str
    blocked_status_codes: set[int]
    detail_url_re: re.Pattern[str]

    def build_search_url(self, request: JobSearchRequest) -> str:
        params: dict[str, object] = {}
        if self.source == "joboko":
            params = {"keywords": request.keyword}
            if request.page > 1:
                params["page"] = request.page
            return f"https://vn.joboko.com/tim-viec-lam?{urlencode(params)}"
        if self.source == "vietnamworks":
            params = {"q": request.keyword}
            if request.page > 1:
                params["page"] = request.page
            return f"https://www.vietnamworks.com/viec-lam?{urlencode(params)}"
        if self.source == "glints":
            params = {"keyword": request.keyword}
            if request.page > 1:
                params["page"] = request.page
            return f"https://glints.com/vn/opportunities/jobs/explore?{urlencode(params)}"
        if self.source == "itviec":
            params = {"query": request.keyword}
            if request.page > 1:
                params["page"] = request.page
            return f"https://itviec.com/it-jobs?{urlencode(params)}"
        return build_topcv_search_url(
            TopCVJobSearchRequest(keyword=request.keyword, location=request.location, page=request.page)
        )


PROVIDERS: dict[JobSource, JobProvider] = {
    "topcv": JobProvider(
        source="topcv",
        label=SOURCE_LABELS["topcv"],
        blocked_status_codes={403, 429},
        detail_url_re=re.compile(r"/viec-lam/[^\"'#?<>\s]+", re.IGNORECASE),
    ),
    "joboko": JobProvider(
        source="joboko",
        label=SOURCE_LABELS["joboko"],
        blocked_status_codes={403, 429},
        detail_url_re=re.compile(r"/viec-lam-[^\"'#?<>\s]+-xvi\d+", re.IGNORECASE),
    ),
    "vietnamworks": JobProvider(
        source="vietnamworks",
        label=SOURCE_LABELS["vietnamworks"],
        blocked_status_codes={403, 429},
        detail_url_re=re.compile(r"(?:https?://(?:www\.)?vietnamworks\.com)?/[^\"'#?<>\s]+-jv", re.IGNORECASE),
    ),
    "glints": JobProvider(
        source="glints",
        label=SOURCE_LABELS["glints"],
        blocked_status_codes={403, 429},
        detail_url_re=re.compile(
            r"(?:https?://glints\.com)?/(?:vn/)?opportunities/jobs/(?!explore)[^\"'#?<>\s]+",
            re.IGNORECASE,
        ),
    ),
    "itviec": JobProvider(
        source="itviec",
        label=SOURCE_LABELS["itviec"],
        blocked_status_codes={403, 429},
        detail_url_re=re.compile(r"(?:https?://(?:www\.)?itviec\.com)?/it-jobs/[^\"'#?<>\s]+", re.IGNORECASE),
    ),
}


def _fold_text(text: str | None) -> str:
    if not text:
        return ""
    normalized = unicodedata.normalize("NFD", text.lower().replace("đ", "d"))
    return "".join(char for char in normalized if unicodedata.category(char) != "Mn")


def _content_words(text: str | None) -> set[str]:
    if not text:
        return set()
    words = re.findall(r"[a-zA-ZÀ-ỹ0-9+#.]{3,}", text.lower())
    return {word for word in words if _fold_text(word) not in STOPWORDS}


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
        ("Khớp Python", ("python",), ("python",)),
        ("Khớp Computer Vision", ("computer vision",), ("computer vision", "thi giac may tinh")),
        ("Khớp NLP", ("nlp", "natural language"), ("nlp", "xu ly ngon ngu")),
    )

    reasons: list[str] = []
    for label, intent_terms, target_terms in rules:
        if any(term in intent for term in intent_terms) and any(term in target for term in target_terms):
            reasons.append(label)
    return reasons


def _canonical_job_url(url: str, base_url: str) -> str:
    clean_url = html_lib.unescape(url).replace("\\u0026", "&").replace("\\/", "/")
    absolute = urljoin(base_url, clean_url)
    parsed = urlparse(absolute)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path.rstrip("/"), "", "", ""))


def _title_from_url(url: str) -> str:
    path = urlparse(url).path.strip("/")
    slug = path.rsplit("/", 1)[-1]
    slug = re.sub(r"-(?:xvi)?\d+(?:-jv)?$", "", slug, flags=re.IGNORECASE)
    slug = re.sub(r"-jv$", "", slug, flags=re.IGNORECASE)
    words = [word for word in slug.replace("_", "-").split("-") if word and not word.isdigit()]
    title = " ".join(words).strip()
    return title.title() if title else "Job posting"


def _nearest_card_text(anchor) -> str:
    current = anchor
    for _ in range(6):
        if current is None:
            break
        class_text = " ".join(current.get("class", [])) if hasattr(current, "get") else ""
        if current.name in {"article", "li"} or any(
            marker in class_text.lower() for marker in ("job", "card", "item", "posting")
        ):
            return clean_text(current.get_text(" "))
        current = current.parent
    return clean_text(anchor.parent.get_text(" ") if anchor.parent else anchor.get_text(" "))


def _extract_company(title: str, card_text: str) -> str | None:
    lines = [clean_text(line) for line in re.split(r"[\n\r]+| {2,}", card_text) if clean_text(line)]
    for line in lines:
        if line == title or len(line) < 3:
            continue
        lowered = line.lower()
        if any(
            marker in lowered
            for marker in ("công ty", "company", "tnhh", "jsc", "corporation", "co.,", "ltd", "inc")
        ):
            cleaned = line.replace(title, " ")
            salary_match = SALARY_RE.search(cleaned)
            if salary_match:
                cleaned = cleaned[: salary_match.start()]
            for city in CITY_WORDS:
                cleaned = re.sub(re.escape(city), " ", cleaned, flags=re.IGNORECASE)
            return clean_text(cleaned)[:160] or None
    return None


def _extract_location(card_text: str) -> str | None:
    folded = _fold_text(card_text)
    found = [city for city in CITY_WORDS if _fold_text(city) in folded]
    return ", ".join(dict.fromkeys(found)) or None


def _extract_salary(card_text: str) -> str | None:
    match = SALARY_RE.search(card_text)
    return clean_text(match.group(0)) if match else None


def _score_job(result: JobResult, cv_text: str | None, keyword: str) -> JobResult:
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


def _job_matches_keyword(result: JobResult, keyword: str) -> bool:
    keyword_words = _content_words(keyword)
    if not keyword_words:
        return True
    haystack = " ".join(
        part
        for part in (result.title, result.company_name, result.location, result.salary, result.snippet)
        if part
    )
    return bool(keyword_words & _content_words(haystack))


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


def _result_from_json_ld(provider: JobProvider, item: dict[str, object], search_url: str) -> JobResult | None:
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
    return JobResult(
        source=provider.source,
        source_label=provider.label,
        title=title,
        company_name=company_name,
        location=clean_text(json.dumps(item.get("jobLocation"), ensure_ascii=False))[:180]
        if item.get("jobLocation")
        else None,
        salary=clean_text(json.dumps(item.get("baseSalary"), ensure_ascii=False))[:120]
        if item.get("baseSalary")
        else None,
        url=_canonical_job_url(url, search_url),
        snippet=clean_text(description, max_chars=260) or None,
    )


def _parse_generic_search_html(
    provider: JobProvider,
    html: str,
    *,
    search_url: str,
    keyword: str,
    cv_text: str | None,
    limit: int,
) -> tuple[list[JobResult], list[str]]:
    soup = BeautifulSoup(html, "html.parser")
    warnings: list[str] = []
    page_title = clean_text(soup.title.get_text(" ") if soup.title else "")
    page_text = clean_text(soup.get_text(" "), max_chars=300)
    challenge_text = " ".join([page_title, page_text]).lower()
    if any(marker in challenge_text for marker in CHALLENGE_MARKERS):
        return [], [f"{provider.label} đang trả trang xác minh/chống bot nên crawler không thể đọc danh sách job."]

    results: list[JobResult] = []
    seen_urls: set[str] = set()

    for script in soup.find_all("script", type=lambda value: value and "ld+json" in value):
        try:
            payload = json.loads(script.string or script.get_text())
        except json.JSONDecodeError:
            continue
        for item in _flatten_json_ld(payload):
            result = _result_from_json_ld(provider, item, search_url)
            if result and result.url not in seen_urls:
                seen_urls.add(result.url)
                results.append(_score_job(result, cv_text, keyword))
                if len(results) >= limit:
                    break
        if len(results) >= limit:
            break

    if len(results) < limit:
        for anchor in soup.find_all("a", href=True):
            href = str(anchor["href"])
            if not provider.detail_url_re.search(href):
                continue
            url = _canonical_job_url(href, search_url)
            if url in seen_urls:
                continue
            title = clean_text(anchor.get_text(" ") or anchor.get("title") or anchor.get("aria-label") or "")
            if not title or len(title) < 4:
                title = _title_from_url(url)
            card_text = _nearest_card_text(anchor)
            result = JobResult(
                source=provider.source,
                source_label=provider.label,
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

    if not results:
        if page_title or page_text:
            warnings.append(
                f"{provider.label} trả HTML nhưng chưa đọc được job card. "
                f"Tiêu đề: {page_title or 'không có'}; mẫu nội dung: {page_text or 'rỗng'}"
            )
        else:
            warnings.append(f"{provider.label} trả HTML rỗng hoặc không có nội dung job để đọc.")

    keyword_words = _content_words(keyword)
    if results and keyword_words:
        matched_results = [job for job in results if _job_matches_keyword(job, keyword)]
        if matched_results:
            dropped_count = len(results) - len(matched_results)
            if dropped_count:
                warnings.append(
                    f"{provider.label} trả thêm {dropped_count} job không khớp từ khóa; đã ẩn các kết quả đó."
                )
            results = matched_results
        else:
            warnings.append(
                f"{provider.label} có thể không áp dụng bộ lọc từ khóa trên HTML public; chưa thấy job nào khớp trực tiếp."
            )
            results = []

    return sorted(results, key=lambda result: result.fit_score, reverse=True)[:limit], warnings


async def _fetch_provider_html(provider: JobProvider, search_url: str) -> tuple[str, list[str]]:
    warnings: list[str] = []
    settings = get_settings()
    try:
        async with httpx.AsyncClient(
            timeout=16.0,
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
            if response.status_code in provider.blocked_status_codes:
                warnings.append(
                    f"{provider.label} từ chối request từ môi trường hiện tại (HTTP {response.status_code}). "
                    "Trên Render, nguồn này có thể cần API chính thức hoặc người dùng mở link gốc."
                )
                if getattr(settings, "job_browser_crawler_enabled", False):
                    warnings.append(f"Đang dùng Chromium headless trong container để render {provider.label}.")
                    html, browser_warning = await fetch_rendered_html(
                        search_url,
                        getattr(settings, "job_browser_timeout_seconds", 18.0),
                    )
                    if browser_warning:
                        warnings.append(browser_warning)
                    if html:
                        return html, warnings
                return "", warnings
            response.raise_for_status()
            return response.text, warnings
    except httpx.HTTPError as exc:
        return "", [f"Không thể tải {provider.label} lúc này: {exc}"]


def _convert_topcv_result(result) -> JobResult:
    return JobResult(
        source="topcv",
        source_label=SOURCE_LABELS["topcv"],
        title=result.title,
        company_name=result.company_name,
        location=result.location,
        salary=result.salary,
        url=result.url,
        snippet=result.snippet,
        fit_score=result.fit_score,
        fit_reasons=list(result.fit_reasons or []),
        analysis_status=result.analysis_status,
        analysis_error=result.analysis_error,
        detail_text=result.detail_text,
        normalized_job_description=result.normalized_job_description,
        analysis=result.analysis,
    )


async def _search_source(request: JobSearchRequest, source: JobSource) -> tuple[str, str, list[JobResult], list[str]]:
    provider = PROVIDERS[source]
    search_url = provider.build_search_url(request)
    if source == "topcv":
        topcv_response = await search_topcv_jobs(
            TopCVJobSearchRequest(
                keyword=request.keyword,
                location=request.location,
                cv_text=request.cv_text,
                page=request.page,
                limit=request.limit,
                analyze_results=False,
                output_language=request.output_language,
                user_preferences=request.user_preferences,
            )
        )
        return source, topcv_response.search_url, [_convert_topcv_result(item) for item in topcv_response.results], [
            f"{provider.label}: {warning}" for warning in topcv_response.warnings
        ]

    html, fetch_warnings = await _fetch_provider_html(provider, search_url)
    if not html:
        return source, search_url, [], fetch_warnings

    results, parse_warnings = _parse_generic_search_html(
        provider,
        html,
        search_url=search_url,
        keyword=request.keyword,
        cv_text=request.cv_text,
        limit=request.limit,
    )
    if not results and getattr(get_settings(), "job_browser_crawler_enabled", False):
        browser_warnings = [f"Đang dùng Chromium headless trong container để render lại {provider.label}."]
        rendered_html, browser_warning = await fetch_rendered_html(
            search_url,
            getattr(get_settings(), "job_browser_timeout_seconds", 18.0),
        )
        if browser_warning:
            browser_warnings.append(browser_warning)
        if rendered_html and rendered_html != html:
            rendered_results, rendered_parse_warnings = _parse_generic_search_html(
                provider,
                rendered_html,
                search_url=search_url,
                keyword=request.keyword,
                cv_text=request.cv_text,
                limit=request.limit,
            )
            if rendered_results:
                return source, search_url, rendered_results, [*fetch_warnings, *parse_warnings, *browser_warnings, *rendered_parse_warnings]
        parse_warnings.extend(browser_warnings)
    return source, search_url, results, [*fetch_warnings, *parse_warnings]


def _dedupe_results(results: list[JobResult], limit: int) -> list[JobResult]:
    seen: set[str] = set()
    deduped: list[JobResult] = []
    for result in sorted(results, key=lambda item: item.fit_score, reverse=True):
        key = result.url.lower() or f"{_fold_text(result.source)}:{_fold_text(result.title)}:{_fold_text(result.company_name)}"
        if key in seen:
            continue
        seen.add(key)
        deduped.append(result)
        if len(deduped) >= limit:
            break
    return deduped


def _job_to_analysis_text(job: JobResult) -> str:
    parts = [
        f"Job title: {job.title}",
        f"Company: {job.company_name}" if job.company_name else "",
        f"Location: {job.location}" if job.location else "",
        f"Salary: {job.salary}" if job.salary else "",
        f"{job.source_label} URL: {job.url}",
        (
            f"Source note: Nội dung bên dưới được trích từ card kết quả {job.source_label}. "
            "Mở link gốc để đọc JD đầy đủ trước khi ứng tuyển."
        ),
        f"Job card text: {job.snippet}" if job.snippet else "",
        f"Fit hints from crawler: {', '.join(job.fit_reasons)}" if job.fit_reasons else "",
    ]
    return clean_text("\n".join(part for part in parts if part), max_chars=6000)


async def analyze_job_response(
    response: JobSearchResponse,
    *,
    cv_text: str | None,
    analyze_limit: int,
    output_language: str,
    user_preferences: str | None = None,
) -> JobSearchResponse:
    if not cv_text or analyze_limit <= 0 or not response.results:
        return response

    analyzed_jobs: list[JobResult] = []
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
                        "analysis_error": f"Không đủ dữ liệu JD từ {job.source_label} để phân tích.",
                        "detail_text": detail_text,
                    }
                )
            )
            continue

        try:
            normalized = normalize_jd_locally(
                detail_text,
                source_type="text",
                warnings=[
                    f"Phân tích nhanh từ thông tin card {job.source_label}; hãy mở link gốc để kiểm tra JD đầy đủ."
                ],
            )
            analysis = analyze_fit_locally(
                AnalyzeRequest(
                    cv_text=cv_text,
                    normalized_job_description=normalized,
                    user_preferences=user_preferences,
                    output_language=output_language,
                ),
                reason=f"Phân tích nhanh cục bộ cho kết quả {job.source_label} để phản hồi ngay trong demo.",
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
        f"Đã phân tích nhanh {analyzed_count} việc làm đầu tiên bằng thông tin crawl được.",
    ]
    return response.model_copy(
        update={
            "results": analyzed_jobs,
            "warnings": list(dict.fromkeys(warnings)),
        }
    )


async def search_jobs(request: JobSearchRequest) -> JobSearchResponse:
    tasks = [_search_source(request, source) for source in request.sources]
    source_results = await asyncio.gather(*tasks)

    search_urls: dict[str, str] = {}
    warnings: list[str] = []
    results: list[JobResult] = []
    for source, search_url, source_jobs, source_warnings in source_results:
        search_urls[source] = search_url
        results.extend(source_jobs)
        warnings.extend(source_warnings)

    response = JobSearchResponse(
        sources=request.sources,
        query=request.keyword,
        search_url=next(iter(search_urls.values()), ""),
        search_urls=search_urls,
        results=_dedupe_results(results, request.limit),
        warnings=list(dict.fromkeys(warnings)),
    )
    if request.analyze_results:
        return await analyze_job_response(
            response,
            cv_text=request.cv_text,
            analyze_limit=request.analyze_limit,
            output_language=request.output_language,
            user_preferences=request.user_preferences,
        )
    return response


def derive_job_keywords_from_cv(cv_text: str) -> list[str]:
    return derive_topcv_keywords_from_cv(cv_text)


async def recommend_jobs_from_cv(request: JobRecommendRequest) -> JobSearchResponse:
    suggested_keywords = derive_job_keywords_from_cv(request.cv_text)
    warnings = [f"Từ khóa suy ra từ CV: {suggested_keywords[0]}"]
    fallback_response: JobSearchResponse | None = None

    for keyword in suggested_keywords[:5]:
        response = await search_jobs(
            JobSearchRequest(
                keyword=keyword,
                location=request.location,
                sources=request.sources,
                cv_text=request.cv_text,
                page=request.page,
                limit=request.limit,
                analyze_results=False,
                output_language=request.output_language,
                user_preferences=request.user_preferences,
            )
        )
        warnings.append(f"Đã thử {', '.join(SOURCE_LABELS[source] for source in request.sources)} với từ khóa: {keyword}")
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
                return await analyze_job_response(
                    final_response,
                    cv_text=request.cv_text,
                    analyze_limit=request.analyze_limit,
                    output_language=request.output_language,
                    user_preferences=request.user_preferences,
                )
            return final_response

    response = fallback_response or JobSearchResponse(
        sources=request.sources,
        query=suggested_keywords[0],
        suggested_keywords=suggested_keywords,
        search_url="",
        search_urls={},
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
        return await analyze_job_response(
            final_response,
            cv_text=request.cv_text,
            analyze_limit=request.analyze_limit,
            output_language=request.output_language,
            user_preferences=request.user_preferences,
        )
    return final_response


def parse_job_search_html_for_source(
    source: JobSource,
    html: str,
    *,
    search_url: str,
    keyword: str,
    cv_text: str | None = None,
    limit: int = 8,
) -> tuple[list[JobResult], list[str]]:
    if source == "topcv":
        topcv_results, warnings = parse_topcv_search_html(
            html,
            search_url=search_url,
            keyword=keyword,
            cv_text=cv_text,
            limit=limit,
        )
        return [_convert_topcv_result(item) for item in topcv_results], warnings
    return _parse_generic_search_html(
        PROVIDERS[source],
        html,
        search_url=search_url,
        keyword=keyword,
        cv_text=cv_text,
        limit=limit,
    )
