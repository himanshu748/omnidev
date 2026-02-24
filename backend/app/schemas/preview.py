"""Schemas for the Site Preview / Website Check module."""

from __future__ import annotations

from pydantic import BaseModel, Field, HttpUrl


class PreviewRequest(BaseModel):
    """Request to preview or check a website."""

    url: HttpUrl
    desktop: bool = True
    mobile: bool = True
    wait_seconds: float = Field(0, ge=0, le=10, description="Seconds to wait after load before capture")


class PreviewResponse(BaseModel):
    """Screenshot(s) and metadata for the preview."""

    url: str
    title: str = ""
    status_code: int | None = None
    elapsed_ms: int = 0
    desktop_screenshot_b64: str | None = None
    mobile_screenshot_b64: str | None = None
