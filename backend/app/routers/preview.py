"""Site Preview / Website Check router — capture screenshots and meta for any URL."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.schemas.preview import PreviewRequest, PreviewResponse
from app.services.preview_service import capture_preview
from app.routers.errors import internal_error

router = APIRouter()


@router.post("/check", response_model=PreviewResponse)
async def preview_check(body: PreviewRequest, request: Request):
    """
    Preview or check any website: desktop and/or mobile screenshot plus title and status.
    No API keys required. Uses the same Playwright browser as the scraper.
    """
    if not body.desktop and not body.mobile:
        raise HTTPException(
            status_code=400,
            detail="Enable at least one of desktop or mobile",
        )
    browser = request.app.state.browser
    try:
        result = await capture_preview(
            browser,
            url=str(body.url),
            desktop=body.desktop,
            mobile=body.mobile,
            wait_seconds=body.wait_seconds,
        )
        return PreviewResponse(**result)
    except Exception as exc:
        raise internal_error("Website preview failed.") from exc
