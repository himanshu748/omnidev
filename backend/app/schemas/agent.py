"""Schemas for agent mode and its workspaces."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class AgentRunRequest(BaseModel):
    task: str = Field(..., min_length=1, max_length=8000)
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    # Offer the enabled MCP marketplace servers alongside the built-in tools.
    use_mcp: bool = True
    max_steps: int = Field(default=15, ge=1, le=40)


class ApprovalDecisionRequest(BaseModel):
    decision: str = Field(..., pattern="^(allow_once|allow_always|deny)$")


class PendingApproval(BaseModel):
    id: str
    tool: str
    summary: str = ""
    detail: str = ""


class PendingApprovalsResponse(BaseModel):
    approvals: list[PendingApproval]


class WorkspaceCreateRequest(BaseModel):
    path: str = Field(..., min_length=1, max_length=1024)


class WorkspaceInfo(BaseModel):
    path: str
    added_at: str = ""
    implicit: bool = False


class WorkspaceListResponse(BaseModel):
    workspaces: list[WorkspaceInfo]


class SandboxStatus(BaseModel):
    mode: Literal["enforce", "off"]
    network: bool
    auto_approve: bool
    backend: str | None = None
    backend_label: str = ""
    available: bool
    active: bool
    reason: str = ""
    summary: str = ""
    protected_paths: list[str] = []
    writable_caches: list[str] = []


class SandboxUpdateRequest(BaseModel):
    mode: Literal["enforce", "off"] | None = None
    network: bool | None = None
    auto_approve: bool | None = None
