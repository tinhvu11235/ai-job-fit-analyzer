from app.services.source_loader import clean_text


async def fetch_rendered_html(url: str, timeout_seconds: float) -> tuple[str, str | None]:
    try:
        from playwright.async_api import TimeoutError as PlaywrightTimeoutError
        from playwright.async_api import async_playwright
    except ImportError:
        return "", "Playwright Chromium chưa được cài trong môi trường hiện tại."

    browser = None
    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(
                headless=True,
                args=[
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--no-sandbox",
                ],
            )
            context = await browser.new_context(
                locale="vi-VN",
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
                ),
            )
            page = await context.new_page()
            timeout_ms = int(max(5.0, timeout_seconds) * 1000)
            await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            try:
                await page.wait_for_load_state("networkidle", timeout=min(timeout_ms, 8000))
            except PlaywrightTimeoutError:
                pass
            await page.wait_for_timeout(1200)
            html = await page.content()
            title = clean_text(await page.title())
            if not html:
                return "", "Chromium đã mở trang nhưng không trả về HTML."
            lowered = " ".join([title, clean_text(html, max_chars=400)]).lower()
            if any(marker in lowered for marker in ("captcha", "cloudflare", "verify", "access denied", "forbidden")):
                return html, "Trang render bằng Chromium có dấu hiệu xác minh/chống bot."
            return html, None
    except Exception as exc:
        return "", f"Không thể render trang bằng Chromium trong container: {exc}"
    finally:
        if browser is not None:
            await browser.close()
