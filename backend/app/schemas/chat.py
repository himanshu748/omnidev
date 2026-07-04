"""Schemas for the streaming chat endpoint."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000)
    system: str | None = Field(default=None, max_length=4000)
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
