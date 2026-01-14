"""
OmniDev - Web Scraper Router
API endpoints for web scraping with Playwright
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.scraper_service import scraper_service


router = APIRouter()


class ScrapeRequest(BaseModel):
    """Request model for scraping a URL"""
    url: str
    wait_time_ms: int = 2000
    capture_screenshot: bool = False
    extract_selector: Optional[str] = None


class ScrapeResponse(BaseModel):
    """Response model for scraping results"""
    success: bool
    url: str
    title: str
    html: str
    text: str
    screenshot: Optional[str] = None
    error: Optional[str] = None
    engine: str
    load_time_ms: int


class ScreenshotRequest(BaseModel):
    """Request model for taking a screenshot"""
    url: str


class StatusResponse(BaseModel):
    """Response model for scraper status"""
    playwright: dict


@router.post("/scrape", response_model=ScrapeResponse)
async def scrape_url(request: ScrapeRequest):
    """
    Scrape a URL using Playwright
    
    - **url**: The URL to scrape
    - **wait_time_ms**: Time to wait for page to load (default: 2000ms)
    - **capture_screenshot**: Whether to capture a screenshot (base64)
    - **extract_selector**: CSS selector to extract specific content
    """
    try:
        result = await scraper_service.scrape(
            url=request.url,
            wait_time_ms=request.wait_time_ms,
            capture_screenshot=request.capture_screenshot,
            extract_selector=request.extract_selector,
        )
        
        return ScrapeResponse(
            success=result.success,
            url=result.url,
            title=result.title,
            html=result.html,
            text=result.text,
            screenshot=result.screenshot,
            error=result.error,
            engine=result.engine,
            load_time_ms=result.load_time_ms,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/screenshot", response_model=ScrapeResponse)
async def take_screenshot(request: ScreenshotRequest):
    """
    Take a screenshot of a URL
    
    - **url**: The URL to screenshot
    """
    try:
        result = await scraper_service.take_screenshot(url=request.url)
        
        return ScrapeResponse(
            success=result.success,
            url=result.url,
            title=result.title,
            html=result.html,
            text=result.text,
            screenshot=result.screenshot,
            error=result.error,
            engine=result.engine,
            load_time_ms=result.load_time_ms,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=StatusResponse)
async def get_scraper_status():
    """
    Get the status of Playwright scraper engine
    
    Returns information about Playwright availability
    """
    status = scraper_service.get_status()
    return StatusResponse(**status)


@router.post("/cleanup")
async def cleanup_browsers():
    """
    Cleanup browser instances
    
    Closes any open browser instances to free resources
    """
    try:
        await scraper_service.cleanup()
        return {"status": "success", "message": "Browser instances cleaned up"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
