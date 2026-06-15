import ipaddress
import re
import socket
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from fastapi import HTTPException, status

from app.config import get_settings


BLOCKED_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "::1"}
WHITESPACE_RE = re.compile(r"\s+")


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


async def fetch_url_text(url: str) -> tuple[str, list[str]]:
    _validate_public_http_url(url)
    settings = get_settings()
    warnings: list[str] = []

    try:
        async with httpx.AsyncClient(
            timeout=15.0,
            follow_redirects=True,
            headers={"User-Agent": "AIJobFitAnalyzer/1.0"},
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
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg", "header", "footer", "nav"]):
        tag.decompose()

    text = clean_text(soup.get_text(" "), max_chars=settings.max_input_chars)
    if len(text) < 200:
        warnings.append("Fetched content is very short; the job site may have blocked extraction.")
    if "sign in" in text.lower() or "login" in text.lower():
        warnings.append("Fetched content may include login or navigation text.")

    return text, warnings

