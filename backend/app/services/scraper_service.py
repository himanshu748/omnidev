"""
Web Scraper service.
Uses the Playwright browser from app.state with stealth evasion.
"""

from __future__ import annotations

import asyncio
import base64
from typing import Optional

from playwright.async_api import Browser, BrowserContext, Page
from playwright_stealth import Stealth

from app.schemas.scraper import ExtractMode


_stealth = Stealth()


async def scrape(
    browser: Browser,
    *,
    url: str,
    wait_for: Optional[str] = None,
    extract: ExtractMode = ExtractMode.text,
    stealth: bool = True,
    headers: Optional[dict[str, str]] = None,
    javascript: Optional[str] = None,
    timeout_ms: int = 30000,
    wait_seconds: float = 0,
) -> dict:
    """
    Open a page, optionally apply stealth, extract content, and close.
    Returns dict matching ScrapeResponse fields.
    """
    context: BrowserContext
    if stealth:
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1920, "height": 1080},
            java_script_enabled=True,
        )
        await _stealth.apply_stealth_async(context)
    else:
        context = await browser.new_context()

    if headers:
        await context.set_extra_http_headers(headers)

    page: Page = await context.new_page()

    status_code: int | None = None

    def _capture_status(response):
        nonlocal status_code
        if response.url == url and status_code is None:
            status_code = response.status

    page.on("response", _capture_status)

    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)

        if wait_for:
            await page.wait_for_selector(wait_for, timeout=timeout_ms)

        if javascript:
            await page.evaluate(javascript)

        if wait_seconds > 0:
            await asyncio.sleep(wait_seconds)

        title = await page.title()

        content = ""
        screenshot_b64: str | None = None

        if extract == ExtractMode.text:
            content = await page.inner_text("body")
        elif extract == ExtractMode.html:
            content = await page.content()
        elif extract == ExtractMode.screenshot:
            raw_bytes = await page.screenshot(full_page=True, type="png")
            screenshot_b64 = base64.b64encode(raw_bytes).decode()

        return {
            "url": url,
            "title": title,
            "status_code": status_code,
            "content": content,
            "screenshot_b64": screenshot_b64,
        }
    finally:
        await context.close()
