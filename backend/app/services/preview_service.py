"""
Site Preview / Website Check service.
Captures desktop and mobile screenshots + metadata using Playwright.
No API keys required — uses the same browser as the scraper.
"""

from __future__ import annotations

import asyncio
import base64
import time
from typing import Optional

from playwright.async_api import Browser, BrowserContext, Page
from playwright_stealth import Stealth

_stealth = Stealth()

DESKTOP_VIEWPORT = {"width": 1440, "height": 900}
MOBILE_VIEWPORT = {"width": 390, "height": 844}


async def capture_preview(
    browser: Browser,
    *,
    url: str,
    desktop: bool = True,
    mobile: bool = True,
    wait_seconds: float = 0,
    timeout_ms: int = 25000,
) -> dict:
    """
    Load a URL, capture screenshot(s) at desktop and/or mobile viewport,
    and return base64 image(s) plus title, status_code, elapsed_ms.
    """
    start = time.time()
    ctx_opts: dict = {
        "viewport": DESKTOP_VIEWPORT,
        "java_script_enabled": True,
        "user_agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ),
    }
    context: BrowserContext = await browser.new_context(**ctx_opts)
    await _stealth.apply_stealth_async(context)

    page: Page = await context.new_page()
    status_code: Optional[int] = None

    def _on_response(response):
        nonlocal status_code
        if response.url.rstrip("/") == url.rstrip("/") and status_code is None:
            status_code = response.status

    page.on("response", _on_response)

    try:
        await page.goto(url, wait_until="commit", timeout=timeout_ms)
        try:
            await page.wait_for_load_state("domcontentloaded", timeout=5000)
        except Exception:
            pass
        if wait_seconds > 0:
            await asyncio.sleep(wait_seconds)

        title = await page.title()
        desktop_b64: Optional[str] = None
        mobile_b64: Optional[str] = None

        if desktop:
            raw = await page.screenshot(full_page=True, type="png")
            desktop_b64 = base64.b64encode(raw).decode()

        if mobile:
            await page.set_viewport_size(MOBILE_VIEWPORT)
            await asyncio.sleep(0.3)
            raw = await page.screenshot(full_page=True, type="png")
            mobile_b64 = base64.b64encode(raw).decode()

        elapsed_ms = int((time.time() - start) * 1000)
        return {
            "url": url,
            "title": title,
            "status_code": status_code,
            "elapsed_ms": elapsed_ms,
            "desktop_screenshot_b64": desktop_b64,
            "mobile_screenshot_b64": mobile_b64,
        }
    finally:
        await context.close()
