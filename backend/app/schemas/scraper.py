"""Schemas for the Web Scraper module — v2."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


class ExtractMode(str, Enum):
    text = "text"
    html = "html"
    screenshot = "screenshot"
    links = "links"
    metadata = "metadata"
    pdf = "pdf"


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
    cookies: Optional[list[dict[str, str]]] = Field(
        None,
        description="List of cookie dicts: [{name, value, domain?, path?}].",
    )
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
    proxy: Optional[str] = Field(
        None,
        description="HTTP/SOCKS proxy URL, e.g. http://user:pass@proxy:8080",
    )
    viewport_width: int = Field(1920, ge=320, le=3840)
    viewport_height: int = Field(1080, ge=480, le=2160)
    block_resources: Optional[list[str]] = Field(
        None,
        description="Resource types to block: image, stylesheet, font, media, script",
    )


# ── Link item ──────────────────────────────────────────────
class LinkItem(BaseModel):
    href: str
    text: str
    is_external: bool = False


# ── Metadata item ──────────────────────────────────────────
class PageMetadata(BaseModel):
    title: str = ""
    description: str = ""
    og_title: str = ""
    og_description: str = ""
    og_image: str = ""
    canonical: str = ""
    language: str = ""
    favicon: str = ""
    h1_tags: list[str] = []
    meta_tags: dict[str, str] = {}
    word_count: int = 0
    load_time_ms: int = 0


# ── Response ────────────────────────────────────────────────
class ScrapeResponse(BaseModel):
    url: str
    title: str = ""
    status_code: int | None = None
    content: str = ""
    screenshot_b64: str | None = None
    pdf_b64: str | None = None
    links: list[LinkItem] | None = None
    metadata: PageMetadata | None = None
    word_count: int | None = None
    elapsed_ms: int | None = None
