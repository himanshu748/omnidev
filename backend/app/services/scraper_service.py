"""
Web Scraper service — v2.
Uses the Playwright browser from app.state with stealth evasion.

Capabilities:
- text | html | screenshot | links | metadata | pdf extraction
- Cookie injection
- Proxy support (per-request)
- Resource blocking
- Viewport configuration
"""

from __future__ import annotations

import asyncio
import base64
import time
from typing import Optional
from urllib.parse import urlparse

from playwright.async_api import Browser, BrowserContext, Page
from playwright_stealth import Stealth

from app.schemas.scraper import ExtractMode, LinkItem, PageMetadata
from app.services.url_guard import BlockedURLError, validate_proxy, validate_public_url

_stealth = Stealth()

# Injected page JS runs inside a headless browser on the SERVER's network, so a
# fetch to an internal host would bypass the URL guard. Reject the network
# primitives that could exfiltrate data or reach internal services.
import re as _re

_DANGEROUS_JS = _re.compile(
    r"\b(?:fetch|XMLHttpRequest|sendBeacon|WebSocket|EventSource|importScripts)\b|"
    r"\bimport\s*\(",
    _re.IGNORECASE,
)


def _reject_dangerous_js(code: str) -> None:
    if len(code) > 20_000:
        raise BlockedURLError("Injected JavaScript is too large.")
    if _DANGEROUS_JS.search(code):
        raise BlockedURLError(
            "Injected JavaScript may not use network primitives "
            "(fetch, XMLHttpRequest, sendBeacon, WebSocket, EventSource, dynamic import)."
        )


async def scrape(
    browser: Browser,
    *,
    url: str,
    wait_for: Optional[str] = None,
    extract: ExtractMode = ExtractMode.text,
    stealth: bool = True,
    headers: Optional[dict[str, str]] = None,
    cookies: Optional[list[dict[str, str]]] = None,
    javascript: Optional[str] = None,
    timeout_ms: int = 30000,
    wait_seconds: float = 0,
    proxy: Optional[str] = None,
    viewport_width: int = 1920,
    viewport_height: int = 1080,
    block_resources: Optional[list[str]] = None,
) -> dict:
    """
    Open a page, optionally apply stealth, extract content, and close.
    Returns dict matching ScrapeResponse fields.
    """
    # SSRF guard: reject private/reserved/metadata targets before navigating.
    url = validate_public_url(url)
    proxy = validate_proxy(proxy)
    start_time = time.time()

    # Build context options
    ctx_opts: dict = {
        "viewport": {"width": viewport_width, "height": viewport_height},
        "java_script_enabled": True,
    }

    if stealth:
        ctx_opts["user_agent"] = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )

    # Proxy support — create a new browser context with proxy if specified
    if proxy:
        parsed = urlparse(proxy)
        proxy_cfg = {"server": f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"}
        if parsed.username:
            proxy_cfg["username"] = parsed.username
        if parsed.password:
            proxy_cfg["password"] = parsed.password
        ctx_opts["proxy"] = proxy_cfg

    context: BrowserContext = await browser.new_context(**ctx_opts)

    if stealth:
        await _stealth.apply_stealth_async(context)

    if headers:
        await context.set_extra_http_headers(headers)

    # Cookie injection
    if cookies:
        playwright_cookies = []
        for c in cookies:
            cookie = {
                "name": c["name"],
                "value": c["value"],
                "url": url,
            }
            if "domain" in c:
                cookie["domain"] = c["domain"]
                del cookie["url"]
            if "path" in c:
                cookie["path"] = c["path"]
            playwright_cookies.append(cookie)
        await context.add_cookies(playwright_cookies)

    page: Page = await context.new_page()

    # Resource blocking
    if block_resources:
        resource_types_to_block = set(block_resources)

        async def handle_route(route):
            if route.request.resource_type in resource_types_to_block:
                await route.abort()
            else:
                await route.continue_()

        await page.route("**/*", handle_route)

    status_code: int | None = None

    def _capture_status(response):
        nonlocal status_code
        # Accept exact match OR trailing-slash redirect (github.com → github.com/)
        resp_url = response.url.rstrip("/")
        target_url = url.rstrip("/")
        if resp_url == target_url and status_code is None:
            status_code = response.status

    page.on("response", _capture_status)

    try:
        # Use "commit" instead of "domcontentloaded" — much faster for heavy
        # JS-heavy sites (GitHub, SPAs) that take long to fire DOMContentLoaded.
        # The page still renders fine because we add optional wait_seconds after.
        await page.goto(url, wait_until="commit", timeout=timeout_ms)
        # Wait for DOM to be ready (with a short timeout) so title is available
        try:
            await page.wait_for_load_state("domcontentloaded", timeout=5000)
        except Exception:
            pass  # Page is still usable even without full DOM ready

        if wait_for:
            # A bad or slow selector should not hang forever or 500 the request.
            if len(wait_for) > 1000:
                raise BlockedURLError("wait_for selector is too long.")
            try:
                await page.wait_for_selector(wait_for, timeout=min(timeout_ms, 15000))
            except Exception:
                pass  # selector never matched — continue with what loaded

        if javascript:
            _reject_dangerous_js(javascript)
            await page.evaluate(javascript)

        if wait_seconds > 0:
            await asyncio.sleep(wait_seconds)

        title = await page.title()

        content = ""
        screenshot_b64: str | None = None
        pdf_b64: str | None = None
        links: list[LinkItem] | None = None
        metadata: PageMetadata | None = None
        word_count: int | None = None

        if extract == ExtractMode.text:
            content = await page.inner_text("body")
            word_count = len(content.split())

        elif extract == ExtractMode.html:
            content = await page.content()
            body_text = await page.inner_text("body")
            word_count = len(body_text.split())

        elif extract == ExtractMode.screenshot:
            raw_bytes = await page.screenshot(full_page=True, type="png")
            screenshot_b64 = base64.b64encode(raw_bytes).decode()

        elif extract == ExtractMode.pdf:
            # Chromium native PDF print (A4, with backgrounds)
            pdf_bytes = await page.pdf(
                format="A4",
                print_background=True,
                margin={"top": "0.5in", "bottom": "0.5in", "left": "0.5in", "right": "0.5in"},
            )
            pdf_b64 = base64.b64encode(pdf_bytes).decode()

        elif extract == ExtractMode.links:
            raw_links = await page.evaluate("""() => {
                const anchors = document.querySelectorAll('a[href]');
                return Array.from(anchors).map(a => ({
                    href: a.href,
                    text: (a.innerText || a.textContent || '').trim().substring(0, 200)
                }));
            }""")
            page_host = urlparse(url).netloc
            links = []
            seen = set()
            for lnk in raw_links:
                href = lnk.get("href", "")
                if not href or href.startswith("javascript:") or href.startswith("#"):
                    continue
                if href in seen:
                    continue
                seen.add(href)
                is_external = urlparse(href).netloc != page_host
                links.append(
                    LinkItem(
                        href=href,
                        text=lnk.get("text", ""),
                        is_external=is_external,
                    )
                )

        elif extract == ExtractMode.metadata:
            meta_result = await page.evaluate("""() => {
                const getMeta = (name) => {
                    const el = document.querySelector(`meta[name="${name}"], meta[property="${name}"]`);
                    return el ? el.getAttribute('content') || '' : '';
                };
                const getLink = (rel) => {
                    const el = document.querySelector(`link[rel="${rel}"]`);
                    return el ? el.getAttribute('href') || '' : '';
                };
                const h1s = Array.from(document.querySelectorAll('h1')).map(h => h.innerText.trim());
                const allMeta = {};
                document.querySelectorAll('meta[name], meta[property]').forEach(m => {
                    const key = m.getAttribute('name') || m.getAttribute('property') || '';
                    const val = m.getAttribute('content') || '';
                    if (key && val) allMeta[key] = val;
                });
                const bodyText = document.body?.innerText || '';
                return {
                    title: document.title || '',
                    description: getMeta('description'),
                    og_title: getMeta('og:title'),
                    og_description: getMeta('og:description'),
                    og_image: getMeta('og:image'),
                    canonical: getLink('canonical'),
                    language: document.documentElement?.lang || '',
                    favicon: getLink('icon') || getLink('shortcut icon'),
                    h1_tags: h1s,
                    meta_tags: allMeta,
                    word_count: bodyText.split(/\\s+/).filter(w => w).length,
                };
            }""")
            elapsed_ms = int((time.time() - start_time) * 1000)
            meta_result["load_time_ms"] = elapsed_ms
            metadata = PageMetadata(**meta_result)

        elapsed_ms = int((time.time() - start_time) * 1000)

        return {
            "url": url,
            "title": title,
            "status_code": status_code,
            "content": content,
            "screenshot_b64": screenshot_b64,
            "pdf_b64": pdf_b64,
            "links": [l.model_dump() for l in links] if links else None,
            "metadata": metadata.model_dump() if metadata else None,
            "word_count": word_count,
            "elapsed_ms": elapsed_ms,
        }
    finally:
        await context.close()
