"""Schemas for the DevOps Agent module."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


# ── Request ─────────────────────────────────────────────────
class DevOpsCommandRequest(BaseModel):
    message: str = Field(..., min_length=1, examples=["List my EC2 instances"])
    confirm_destructive: bool = Field(
        False,
        description="Must be True for destructive actions (stop/terminate).",
    )


# ── Internal: model-parsed intent ──────────────────────────
class ParsedIntent(BaseModel):
    action: str = Field(..., description="One of the supported action names")
    params: dict[str, Any] = Field(default_factory=dict)
    is_destructive: bool = False


# ── Response ────────────────────────────────────────────────
class DevOpsCommandResponse(BaseModel):
    action: str
    params: dict[str, Any] = {}
    raw_result: Any = None
    summary: str = ""
    needs_confirmation: bool = False
    # Enriched, backward-compatible plan preview. May be absent for
    # unsupported actions. New keys (impact, estimated_scope, read_only)
    # are additive — older clients that only read service/operation/params
    # /destructive keep working.
    plan: dict[str, Any] | None = None
