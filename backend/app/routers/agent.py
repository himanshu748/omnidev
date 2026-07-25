"""Agent router: the streaming plan/act loop, approvals and workspaces."""

from __future__ import annotations

import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.routers.errors import bad_request, not_found, service_unavailable
from app.schemas.agent import (
    AgentRunRequest,
    ApprovalDecisionRequest,
    PendingApproval,
    PendingApprovalsResponse,
    WorkspaceCreateRequest,
    WorkspaceInfo,
    WorkspaceListResponse,
)
from app.services import agent_service, workspace_service
from app.services.ai_service import AIConfigurationError, ensure_ai_configured

router = APIRouter()


@router.post("/stream")
async def agent_stream(body: AgentRunRequest):
    """
    Run an agent task, streaming newline-delimited JSON.

    Event kinds: `agent` (run started), `step`, `tool_call`,
    `approval_required` (answer it via POST /api/agent/approvals/{id}),
    `approval_resolved`, `tool_result`, `checkpoint`, `delta`, `error`,
    `done`. Disconnecting stops the run.
    """
    try:
        ensure_ai_configured()
    except AIConfigurationError as exc:
        raise service_unavailable(str(exc)) from exc

    async def _events():
        try:
            async for event in agent_service.run_agent(
                body.task,
                use_mcp=body.use_mcp,
                temperature=body.temperature,
                max_steps=body.max_steps,
            ):
                yield json.dumps(event) + "\n"
        except Exception:
            yield json.dumps({"error": "Agent run failed."}) + "\n"

    return StreamingResponse(_events(), media_type="application/x-ndjson")


@router.post("/approvals/{approval_id}")
async def resolve_approval(approval_id: str, body: ApprovalDecisionRequest):
    """Answer a pending approval: allow_once, allow_always or deny."""
    try:
        resolved = agent_service.resolve_approval(approval_id, body.decision)
    except agent_service.AgentError as exc:
        raise bad_request(str(exc)) from exc
    if not resolved:
        raise not_found("Unknown or already-answered approval.")
    return {"id": approval_id, "decision": body.decision}


@router.get("/approvals", response_model=PendingApprovalsResponse)
async def list_approvals():
    """Approvals waiting for an answer (for a UI that reconnects)."""
    return PendingApprovalsResponse(
        approvals=[PendingApproval(**a) for a in agent_service.pending_approvals()]
    )


@router.get("/workspaces", response_model=WorkspaceListResponse)
async def list_workspaces():
    records = await workspace_service.list_workspaces_async()
    return WorkspaceListResponse(workspaces=[WorkspaceInfo(**r) for r in records])


@router.post("/workspaces", response_model=WorkspaceInfo, status_code=201)
async def add_workspace(body: WorkspaceCreateRequest):
    """Trust a folder so the agent can edit inside it without asking."""
    try:
        record = await workspace_service.add_workspace_async(body.path)
    except workspace_service.WorkspaceError as exc:
        raise bad_request(str(exc)) from exc
    return WorkspaceInfo(**record)


@router.delete("/workspaces")
async def remove_workspace(path: str):
    if not await workspace_service.remove_workspace_async(path):
        raise not_found("That folder is not a workspace.")
    return {"removed": path}
