"""
Web Scraper service — v2.
Uses the Playwright browser from app.state with stealth evasion.

Capabilities:
- text | html | screenshot | links | metadata | pdf | markdown | article extraction
- Same-domain shallow crawl
- Cookie injection
- Proxy support (per-request)
- Resource blocking
- Viewport configuration
"""

from __future__ import annotations

import asyncio
import base64
import time
from html import unescape
from typing import Optional
from urllib.parse import urljoin, urlparse

from playwright.async_api import Browser, BrowserContext, Page
from playwright_stealth import Stealth

from app.schemas.scraper import ArticleContent, ExtractMode, LinkItem, PageMetadata
from app.services.url_guard import BlockedURLError, validate_proxy, validate_public_url

_stealth = Stealth()

# Guard against pathologically large pages — extracting/serializing a huge DOM
# can pin memory and stall the event loop. Applied to text/markdown/article.
_MAX_CONTENT_CHARS = 5_000_000

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


# ── HTML → Markdown ─────────────────────────────────────────
# A small, dependency-free converter for the common block/inline tags. It walks
# an HTML fragment with the stdlib HTMLParser (no new pip deps) and emits clean
# Markdown for headings, links, lists, paragraphs, blockquotes, code, hr and
# emphasis. Anything it does not understand degrades to its inline text.

from html.parser import HTMLParser as _HTMLParser

_BLOCK_TAGS = {
    "p", "div", "section", "article", "header", "footer", "main",
    "ul", "ol", "li", "blockquote", "pre", "h1", "h2", "h3", "h4", "h5", "h6",
    "table", "tr", "hr", "br",
}
_SKIP_TAGS = {"script", "style", "noscript", "template", "svg", "head"}


class _MarkdownParser(_HTMLParser):
    """Convert an HTML fragment to Markdown. Best-effort, tolerant of bad markup."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []
        self._skip_depth = 0
        self._list_stack: list[str] = []  # "ul" / "ol"
        self._ol_counters: list[int] = []
        self._href_stack: list[tuple[str, int]] = []
        self._in_pre = 0
        self._pending_emphasis: list[str] = []

    # -- helpers --
    def _emit(self, text: str) -> None:
        self._parts.append(text)

    def _newline(self, n: int = 1) -> None:
        self._parts.append("\n" * n)

    # -- tag handling --
    def handle_starttag(self, tag: str, attrs):  # noqa: ANN001
        tag = tag.lower()
        if tag in _SKIP_TAGS:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        a = dict(attrs)
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._newline(2)
            self._emit("#" * int(tag[1]) + " ")
        elif tag == "p":
            self._newline(2)
        elif tag == "br":
            self._newline(1)
        elif tag == "hr":
            self._newline(2)
            self._emit("---")
            self._newline(2)
        elif tag == "blockquote":
            self._newline(2)
            self._emit("> ")
        elif tag == "pre":
            self._in_pre += 1
            self._newline(2)
            self._emit("```\n")
        elif tag == "code" and not self._in_pre:
            self._emit("`")
        elif tag in ("strong", "b"):
            self._emit("**")
            self._pending_emphasis.append("**")
        elif tag in ("em", "i"):
            self._emit("*")
            self._pending_emphasis.append("*")
        elif tag == "ul":
            self._list_stack.append("ul")
            self._newline(1)
        elif tag == "ol":
            self._list_stack.append("ol")
            self._ol_counters.append(0)
            self._newline(1)
        elif tag == "li":
            self._newline(1)
            indent = "  " * (len(self._list_stack) - 1) if self._list_stack else ""
            if self._list_stack and self._list_stack[-1] == "ol":
                self._ol_counters[-1] += 1
                self._emit(f"{indent}{self._ol_counters[-1]}. ")
            else:
                self._emit(f"{indent}- ")
        elif tag == "a":
            href = (a.get("href") or "").strip()
            # Record where the opening "[" lands so a hrefless link can undo it.
            self._href_stack.append((href, len(self._parts)))
            self._emit("[")
        elif tag == "img":
            alt = (a.get("alt") or "").strip()
            src = (a.get("src") or "").strip()
            if src:
                self._emit(f"![{alt}]({src})")

    def handle_endtag(self, tag: str):  # noqa: ANN001
        tag = tag.lower()
        if tag in _SKIP_TAGS:
            if self._skip_depth:
                self._skip_depth -= 1
            return
        if self._skip_depth:
            return
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6", "p", "blockquote"):
            self._newline(2)
        elif tag == "pre":
            if self._in_pre:
                self._in_pre -= 1
            self._emit("\n```")
            self._newline(2)
        elif tag == "code" and not self._in_pre:
            self._emit("`")
        elif tag in ("strong", "b", "em", "i"):
            if self._pending_emphasis:
                self._emit(self._pending_emphasis.pop())
        elif tag == "ul":
            if self._list_stack:
                self._list_stack.pop()
            self._newline(1)
        elif tag == "ol":
            if self._list_stack:
                self._list_stack.pop()
            if self._ol_counters:
                self._ol_counters.pop()
            self._newline(1)
        elif tag == "a":
            href, bracket_idx = self._href_stack.pop() if self._href_stack else ("", -1)
            if href and not href.startswith(("javascript:", "#")):
                self._emit(f"]({href})")
            elif 0 <= bracket_idx < len(self._parts) and self._parts[bracket_idx] == "[":
                # No usable href: drop the "[" we emitted, keep the link text.
                self._parts[bracket_idx] = ""

    def handle_data(self, data: str):  # noqa: ANN001
        if self._skip_depth:
            return
        if self._in_pre:
            self._emit(data)
            return
        # Collapse whitespace runs in normal flow.
        collapsed = _re.sub(r"[ \t\r\f\v]+", " ", data)
        collapsed = collapsed.replace("\n", " ")
        if collapsed.strip() == "" and collapsed != " ":
            return
        self._emit(collapsed)

    def result(self) -> str:
        text = "".join(self._parts)
        text = unescape(text)
        # Normalise excessive blank lines and trailing spaces.
        text = _re.sub(r"[ \t]+\n", "\n", text)
        text = _re.sub(r"\n{3,}", "\n\n", text)
        # Tidy stray empty links "[]()" the tolerant path can leave behind.
        text = text.replace("[]()", "")
        return text.strip()


def html_to_markdown(html: str) -> str:
    """Convert an HTML string (fragment or document) to clean Markdown.

    Dependency-free and defensive: malformed markup degrades to text rather than
    raising. Exposed as a module-level helper so it can be unit-tested directly.
    """
    if not html:
        return ""
    parser = _MarkdownParser()
    try:
        parser.feed(html)
        parser.close()
    except Exception:
        # HTMLParser is tolerant, but never let a parse blow up a scrape.
        pass
    return parser.result()


# In-page heuristic that returns the main content HTML + article fields. Runs in
# the browser via page.evaluate so it sees the rendered DOM. It reads the DOM
# only (no network), so it does not need the dangerous-JS guard.
_MAIN_CONTENT_JS = r"""() => {
    const pick = (sels) => {
        for (const s of sels) {
            const el = document.querySelector(s);
            if (el && (el.innerText || '').trim().length > 40) return el;
        }
        return null;
    };
    // Prefer semantic containers; fall back to the largest text block.
    let root = pick(['article', 'main', '[role="main"]', '#content', '.post', '.article', '.entry-content']);
    if (!root) {
        const candidates = Array.from(document.querySelectorAll('div, section'));
        let best = null, bestLen = 0;
        for (const el of candidates) {
            const t = (el.innerText || '').trim();
            // Penalise nav/aside/footer-heavy blocks.
            const linkDensity = el.querySelectorAll('a').length;
            const score = t.length - linkDensity * 40;
            if (score > bestLen) { bestLen = score; best = el; }
        }
        root = best || document.body;
    }
    const getMeta = (name) => {
        const el = document.querySelector(`meta[name="${name}"], meta[property="${name}"]`);
        return el ? (el.getAttribute('content') || '') : '';
    };
    const title =
        getMeta('og:title') ||
        (document.querySelector('h1') ? document.querySelector('h1').innerText.trim() : '') ||
        document.title || '';
    const byline =
        getMeta('author') ||
        getMeta('article:author') ||
        (document.querySelector('[rel="author"], .author, .byline')
            ? document.querySelector('[rel="author"], .author, .byline').innerText.trim()
            : '');
    const text = (root.innerText || '').trim();
    return { html: root.innerHTML || '', title, byline, text };
}"""

_METADATA_JS = r"""() => {
    const getMeta = (name) => {
        const el = document.querySelector(`meta[name="${name}"], meta[property="${name}"]`);
        return el ? el.getAttribute('content') || '' : '';
    };
    const getLink = (rel) => {
        const el = document.querySelector(`link[rel="${rel}"]`);
        return el ? el.getAttribute('href') || '' : '';
    };
    const h1s = Array.from(document.querySelectorAll('h1')).map(h => (h.innerText || '').trim());
    const allMeta = {};
    const ogTags = {};
    const twitterTags = {};
    document.querySelectorAll('meta[name], meta[property]').forEach(m => {
        const key = m.getAttribute('name') || m.getAttribute('property') || '';
        const val = m.getAttribute('content') || '';
        if (!key || !val) return;
        allMeta[key] = val;
        if (key.toLowerCase().startsWith('og:')) ogTags[key] = val;
        if (key.toLowerCase().startsWith('twitter:')) twitterTags[key] = val;
    });
    const jsonLd = [];
    document.querySelectorAll('script[type="application/ld+json"]').forEach(s => {
        try {
            const parsed = JSON.parse(s.textContent || 'null');
            if (parsed && typeof parsed === 'object') {
                if (Array.isArray(parsed)) { parsed.forEach(p => jsonLd.push(p)); }
                else { jsonLd.push(parsed); }
            }
        } catch (e) { /* ignore malformed JSON-LD */ }
    });
    const bodyText = document.body ? document.body.innerText : '';
    return {
        title: document.title || '',
        description: getMeta('description'),
        og_title: getMeta('og:title'),
        og_description: getMeta('og:description'),
        og_image: getMeta('og:image'),
        canonical: getLink('canonical'),
        language: (document.documentElement && document.documentElement.lang) || '',
        favicon: getLink('icon') || getLink('shortcut icon'),
        h1_tags: h1s,
        meta_tags: allMeta,
        og_tags: ogTags,
        twitter_tags: twitterTags,
        json_ld: jsonLd,
        word_count: bodyText.split(/\s+/).filter(w => w).length,
    };
}"""


async def _build_context(browser: Browser, *, url: str, stealth: bool,
                         headers: Optional[dict[str, str]],
                         cookies: Optional[list[dict[str, str]]],
                         proxy: Optional[str],
                         viewport_width: int, viewport_height: int) -> BrowserContext:
    """Create a configured browser context (stealth, proxy, headers, cookies)."""
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
    if proxy:
        parsed = urlparse(proxy)
        proxy_cfg = {"server": f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"}
        if parsed.username:
            proxy_cfg["username"] = parsed.username
        if parsed.password:
            proxy_cfg["password"] = parsed.password
        ctx_opts["proxy"] = proxy_cfg

    context = await browser.new_context(**ctx_opts)
    if stealth:
        await _stealth.apply_stealth_async(context)
    if headers:
        await context.set_extra_http_headers(headers)
    if cookies:
        playwright_cookies = []
        for c in cookies:
            cookie = {"name": c["name"], "value": c["value"], "url": url}
            if "domain" in c:
                cookie["domain"] = c["domain"]
                del cookie["url"]
            if "path" in c:
                cookie["path"] = c["path"]
            playwright_cookies.append(cookie)
        await context.add_cookies(playwright_cookies)
    return context


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

    context = await _build_context(
        browser,
        url=url,
        stealth=stealth,
        headers=headers,
        cookies=cookies,
        proxy=proxy,
        viewport_width=viewport_width,
        viewport_height=viewport_height,
    )

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
        markdown: str | None = None
        article: ArticleContent | None = None
        word_count: int | None = None

        if extract == ExtractMode.text:
            content = (await page.inner_text("body"))[:_MAX_CONTENT_CHARS]
            word_count = len(content.split())

        elif extract == ExtractMode.html:
            content = (await page.content())[:_MAX_CONTENT_CHARS]
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

        elif extract == ExtractMode.markdown:
            # Convert the main content region to clean Markdown. Fall back to the
            # whole body if the heuristic can't find a good root.
            main = await page.evaluate(_MAIN_CONTENT_JS)
            main_html = (main.get("html") or "")[:_MAX_CONTENT_CHARS]
            markdown = html_to_markdown(main_html)
            if not markdown:
                body_html = (await page.content())[:_MAX_CONTENT_CHARS]
                markdown = html_to_markdown(body_html)
            content = markdown
            word_count = len(markdown.split())

        elif extract == ExtractMode.article:
            main = await page.evaluate(_MAIN_CONTENT_JS)
            text = (main.get("text") or "")[:_MAX_CONTENT_CHARS]
            art_title = (main.get("title") or title or "").strip()
            byline = (main.get("byline") or "").strip()
            excerpt = " ".join(text.split())[:280]
            article = ArticleContent(
                title=art_title,
                byline=byline,
                excerpt=excerpt,
                text=text,
                word_count=len(text.split()),
            )
            content = text
            word_count = article.word_count

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
            meta_result = await page.evaluate(_METADATA_JS)
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
            "markdown": markdown,
            "article": article.model_dump() if article else None,
            "word_count": word_count,
            "elapsed_ms": elapsed_ms,
        }
    finally:
        await context.close()


# ── Same-domain shallow crawl ───────────────────────────────
# Hard bounds so a crawl can never run away: the request schema caps max_pages
# at 10 and max_depth at 2, and this total-time budget stops a slow site early.
_CRAWL_TIME_BUDGET_S = 45.0


def _strip_www(host: str) -> str:
    return host[4:] if host.startswith("www.") else host


def _same_registered_domain(a: str, b: str) -> bool:
    """True if hosts share the same registered domain (last two labels)."""
    ha = _strip_www((urlparse(a).hostname or "").lower())
    hb = _strip_www((urlparse(b).hostname or "").lower())
    if not ha or not hb:
        return False
    if ha == hb:
        return True
    la = ha.split(".")
    lb = hb.split(".")
    return la[-2:] == lb[-2:] and len(la) >= 2 and len(lb) >= 2


async def crawl(
    browser: Browser,
    *,
    url: str,
    max_pages: int = 5,
    max_depth: int = 1,
    stealth: bool = True,
    timeout_ms: int = 20000,
) -> dict:
    """
    Breadth-first, same-domain shallow crawl.

    Every discovered URL is validated through validate_public_url before it is
    visited, stays on the start URL's registered domain, is deduplicated, and is
    bounded by a hard page cap (<=10), depth cap (<=2), and a total time budget.
    Returns {start_url, domain, pages: [{url, title, excerpt, depth, status}]}.
    """
    start_url = validate_public_url(url)
    max_pages = max(1, min(int(max_pages), 10))
    max_depth = max(0, min(int(max_depth), 2))
    start_time = time.time()
    domain = (urlparse(start_url).hostname or "").lower()

    context = await _build_context(
        browser,
        url=start_url,
        stealth=stealth,
        headers=None,
        cookies=None,
        proxy=None,
        viewport_width=1280,
        viewport_height=800,
    )

    pages: list[dict] = []
    # BFS queue of (url, depth). Track seen by normalised URL (drop fragment).
    queue: list[tuple[str, int]] = [(start_url, 0)]
    seen: set[str] = {start_url.split("#")[0].rstrip("/")}

    try:
        while queue and len(pages) < max_pages:
            if time.time() - start_time > _CRAWL_TIME_BUDGET_S:
                break
            current, depth = queue.pop(0)

            page: Page = await context.new_page()
            status_code: int | None = None

            def _capture(response, _target=current):
                nonlocal status_code
                if response.url.rstrip("/") == _target.rstrip("/") and status_code is None:
                    status_code = response.status

            page.on("response", _capture)
            try:
                await page.goto(current, wait_until="commit", timeout=timeout_ms)
                try:
                    await page.wait_for_load_state("domcontentloaded", timeout=5000)
                except Exception:
                    pass

                title = await page.title()
                body_text = ""
                try:
                    body_text = await page.inner_text("body")
                except Exception:
                    pass
                excerpt = " ".join(body_text.split())[:280]

                pages.append({
                    "url": current,
                    "title": title,
                    "excerpt": excerpt,
                    "depth": depth,
                    "status_code": status_code,
                })

                # Enqueue same-domain child links when there is depth budget left.
                if depth < max_depth and len(pages) + len(queue) < max_pages:
                    hrefs = await page.evaluate("""() => {
                        const anchors = document.querySelectorAll('a[href]');
                        return Array.from(anchors).map(a => a.href);
                    }""")
                    for href in hrefs:
                        if len(pages) + len(queue) >= max_pages:
                            break
                        if not href or href.startswith(("javascript:", "mailto:", "tel:")):
                            continue
                        norm = href.split("#")[0].rstrip("/")
                        if not norm or norm in seen:
                            continue
                        if not _same_registered_domain(start_url, href):
                            continue
                        try:
                            safe = validate_public_url(href)
                        except BlockedURLError:
                            continue
                        seen.add(norm)
                        queue.append((safe, depth + 1))
            except Exception:
                # A single bad page should not abort the whole crawl.
                pass
            finally:
                await page.close()

        elapsed_ms = int((time.time() - start_time) * 1000)
        return {
            "start_url": start_url,
            "domain": domain,
            "pages": pages,
            "pages_crawled": len(pages),
            "elapsed_ms": elapsed_ms,
        }
    finally:
        await context.close()
