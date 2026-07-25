"""Schemas for agent mode and its workspaces."""

from __future__ import annotations

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
