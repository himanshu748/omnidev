"""Web Scraper router — Playwright stealth scraping v2."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.schemas.scraper import (
    CrawlRequest,
    CrawlResponse,
    ScrapeRequest,
    ScrapeResponse,
)
from app.services.scraper_service import crawl, scrape
from app.services.url_guard import BlockedURLError
from app.routers.errors import internal_error

router = APIRouter()


def _require_browser(request: Request):
    browser = getattr(request.app.state, "browser", None)
    if browser is None:
        raise HTTPException(
            status_code=503,
            detail="Playwright browser is unavailable. Restart the backend with browser permissions to use scraping.",
        )
    return browser


@router.post("/scrape", response_model=ScrapeResponse)
async def scrape_url(body: ScrapeRequest, request: Request):
    """
    Scrape a URL with optional stealth mode.

    Extraction modes:
    - **text**: Plain text from the page body
    - **html**: Full page HTML
    - **screenshot**: Full-page PNG screenshot (base64)
    - **pdf**: Full-page PDF document (base64)
    - **links**: All hyperlinks with text, href, and external flag
    - **metadata**: SEO metadata (title, description, OG/Twitter, JSON-LD, canonical, favicon, lang, word count)
    - **markdown**: Main content converted to clean Markdown
    - **article**: Readable article extraction (title, byline, body)

    Extra features: cookie injection, proxy support, resource blocking.
    """
    browser = _require_browser(request)
    try:
        result = await scrape(
            browser,
            url=str(body.url),
            wait_for=body.wait_for,
            extract=body.extract,
            stealth=body.stealth,
            headers=body.headers,
            cookies=body.cookies,
            javascript=body.javascript,
            timeout_ms=body.timeout_ms,
            wait_seconds=body.wait_seconds,
            proxy=body.proxy,
            viewport_width=body.viewport_width,
            viewport_height=body.viewport_height,
            block_resources=body.block_resources,
        )
        return ScrapeResponse(**result)
    except BlockedURLError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise internal_error("Web scraping failed.") from exc


@router.post("/crawl", response_model=CrawlResponse)
async def crawl_site(body: CrawlRequest, request: Request):
    """
    Shallow, same-domain crawl from a start URL.

    Bounded by max_pages (cap 10), max_depth (cap 2), and a total-time budget.
    Every discovered URL is SSRF-validated and must stay on the start domain.
    Returns a list of {url, title, excerpt, depth, status_code}.
    """
    browser = _require_browser(request)
    try:
        result = await crawl(
            browser,
            url=str(body.url),
            max_pages=body.max_pages,
            max_depth=body.max_depth,
            stealth=body.stealth,
            timeout_ms=body.timeout_ms,
        )
        return CrawlResponse(**result)
    except BlockedURLError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise internal_error("Web crawl failed.") from exc
