"""Schemas for the Vision Lab module."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class VisionMode(str, Enum):
    analyze = "analyze"
    ocr = "ocr"
    custom = "custom"


# ── Response ────────────────────────────────────────────────
class VisionResponse(BaseModel):
    mode: VisionMode
    result: str = Field(..., description="Model output text")
    model: str = ""
    tokens_used: int | None = None
