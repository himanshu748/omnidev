"""Schemas for the Web Scraper module."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


class ExtractMode(str, Enum):
    text = "text"
    html = "html"
    screenshot = "screenshot"


# ── Request ─────────────────────────────────────────────────
class ScrapeRequest(BaseModel):
    url: HttpUrl
    wait_for: Optional[str] = Field(
        None,
        description="CSS selector to wait for before extracting.",
    )
    extract: ExtractMode = ExtractMode.text
    stealth: bool = True
    headers: Optional[dict[str, str]] = None
    javascript: Optional[str] = Field(
        None,
        description="JS snippet to execute on the page before extraction.",
    )
    timeout_ms: int = Field(30000, ge=1000, le=120000)
    wait_seconds: float = Field(
        0,
        ge=0,
        le=30,
        description="Seconds to wait after page load (and wait_for) before extracting. "
        "Useful for JS-heavy sites that need extra rendering time.",
    )


# ── Response ────────────────────────────────────────────────
class ScrapeResponse(BaseModel):
    url: str
    title: str = ""
    status_code: int | None = None
    content: str = ""
    screenshot_b64: str | None = None
