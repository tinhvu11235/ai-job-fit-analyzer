import ipaddress
<<<<<<< HEAD
import json
=======
>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144
import re
import socket
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from fastapi import HTTPException, status

from app.config import get_settings


BLOCKED_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "::1"}
WHITESPACE_RE = re.compile(r"\s+")
<<<<<<< HEAD
JOB_JSON_KEYS = {
    "title",
    "description",
    "responsibilities",
    "qualifications",
    "skills",
    "experienceRequirements",
    "employmentType",
    "jobLocation",
    "hiringOrganization",
    "baseSalary",
}
=======
>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144


def clean_text(text: str, max_chars: int | None = None) -> str:
    cleaned = WHITESPACE_RE.sub(" ", text).strip()
    if max_chars is not None and len(cleaned) > max_chars:
        return cleaned[:max_chars]
    return cleaned


def ensure_text_within_limit(text: str, field_name: str) -> str:
    settings = get_settings()
    cleaned = clean_text(text)
    if len(cleaned) > settings.max_input_chars:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"{field_name} is too long. Limit is {settings.max_input_chars} characters.",
        )
    return cleaned


def _is_blocked_ip(hostname: str) -> bool:
    try:
        ip = ipaddress.ip_address(hostname)
        return ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved
    except ValueError:
        return False


def _validate_public_http_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only http/https URLs are supported.")

    hostname = parsed.hostname
    if not hostname or hostname.lower() in BLOCKED_HOSTS or _is_blocked_ip(hostname):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This URL host is not allowed.")

    try:
        resolved = socket.getaddrinfo(hostname, None)
    except socket.gaierror as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not resolve URL host.") from exc

    for result in resolved:
        ip_address = result[4][0]
        if _is_blocked_ip(ip_address):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This URL resolves to a private host.")


<<<<<<< HEAD
def _json_value_to_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        return " ".join(_json_value_to_text(item) for item in value)
    if isinstance(value, dict):
        if "name" in value:
            return _json_value_to_text(value["name"])
        if "address" in value:
            return _json_value_to_text(value["address"])
        return " ".join(_json_value_to_text(item) for item in value.values())
    return ""


def _flatten_json_ld(node: object) -> list[dict[str, object]]:
    if isinstance(node, list):
        result: list[dict[str, object]] = []
        for item in node:
            result.extend(_flatten_json_ld(item))
        return result
    if not isinstance(node, dict):
        return []
    nodes = [node]
    graph = node.get("@graph")
    if isinstance(graph, list):
        for item in graph:
            nodes.extend(_flatten_json_ld(item))
    return nodes


def _extract_json_ld_text(soup: BeautifulSoup) -> str:
    chunks: list[str] = []
    for script in soup.find_all("script", type=lambda value: value and "ld+json" in value):
        raw = script.string or script.get_text()
        if not raw:
            continue
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue
        for item in _flatten_json_ld(payload):
            item_type = item.get("@type")
            types = item_type if isinstance(item_type, list) else [item_type]
            if "JobPosting" not in types:
                continue
            for key in JOB_JSON_KEYS:
                if key in item:
                    chunks.append(_json_value_to_text(item[key]))
    return clean_text(" ".join(chunks))


def _extract_best_html_text(soup: BeautifulSoup) -> str:
    selectors = (
        "main",
        "article",
        "[itemtype*='JobPosting']",
        "[class*='job']",
        "[id*='job']",
        "[class*='description']",
        "[id*='description']",
        "[class*='content']",
    )
    candidates: list[str] = []
    for selector in selectors:
        for node in soup.select(selector):
            text = clean_text(node.get_text(" "))
            if len(text) >= 180:
                candidates.append(text)
    candidates.append(clean_text(soup.get_text(" ")))
    return max(candidates, key=len) if candidates else ""


=======
>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144
async def fetch_url_text(url: str) -> tuple[str, list[str]]:
    _validate_public_http_url(url)
    settings = get_settings()
    warnings: list[str] = []

    try:
        async with httpx.AsyncClient(
            timeout=15.0,
            follow_redirects=True,
<<<<<<< HEAD
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/126.0 Safari/537.36 AIJobFitAnalyzer/1.0"
                ),
                "Accept": "text/html,application/xhtml+xml,text/plain;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9,vi;q=0.8",
            },
=======
            headers={"User-Agent": "AIJobFitAnalyzer/1.0"},
>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not fetch job URL. Ask the user to paste the JD text manually. Reason: {exc}",
        ) from exc

    content_type = response.headers.get("content-type", "")
    if "text/html" not in content_type and "text/plain" not in content_type:
        warnings.append(f"Unexpected content type: {content_type or 'unknown'}")

    html = response.text[: settings.max_source_chars]
<<<<<<< HEAD
    if "text/plain" in content_type:
        text = clean_text(html, max_chars=settings.max_input_chars)
        if len(text) < 200:
            warnings.append("Fetched text is very short; the job site may have blocked extraction.")
        return text, warnings

    soup = BeautifulSoup(html, "html.parser")
    json_ld_text = _extract_json_ld_text(soup)
    for tag in soup(["script", "style", "noscript", "svg", "header", "footer", "nav", "form", "button"]):
        tag.decompose()

    html_text = _extract_best_html_text(soup)
    text = clean_text(" ".join(part for part in (json_ld_text, html_text) if part), max_chars=settings.max_input_chars)
=======
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg", "header", "footer", "nav"]):
        tag.decompose()

    text = clean_text(soup.get_text(" "), max_chars=settings.max_input_chars)
>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144
    if len(text) < 200:
        warnings.append("Fetched content is very short; the job site may have blocked extraction.")
    if "sign in" in text.lower() or "login" in text.lower():
        warnings.append("Fetched content may include login or navigation text.")

    return text, warnings
<<<<<<< HEAD
=======

>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144
