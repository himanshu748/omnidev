"""Web Scraper router — Playwright stealth scraping."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.schemas.scraper import ScrapeRequest, ScrapeResponse
from app.services.scraper_service import scrape

router = APIRouter()


@router.post("/scrape", response_model=ScrapeResponse)
async def scrape_url(body: ScrapeRequest, request: Request):
    """
    Scrape a URL with optional stealth mode.

    Supports text extraction, full HTML, or full-page screenshot.
    """
    browser = request.app.state.browser
    try:
        result = await scrape(
            browser,
            url=str(body.url),
            wait_for=body.wait_for,
            extract=body.extract,
            stealth=body.stealth,
            headers=body.headers,
            javascript=body.javascript,
            timeout_ms=body.timeout_ms,
            wait_seconds=body.wait_seconds,
        )
        return ScrapeResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
