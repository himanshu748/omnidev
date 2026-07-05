"""DevOps Agent router — natural-language AWS management."""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.devops import (
    DevOpsCommandRequest,
    DevOpsCommandResponse,
    DevOpsPlanRequest,
    DevOpsPlanResponse,
)
from app.services.ai_service import AIConfigurationError, ensure_ai_configured
from app.services.devops_agent import plan_command, run_command
from app.routers.errors import internal_error, service_unavailable

router = APIRouter()


@router.post("/plan", response_model=DevOpsPlanResponse)
async def devops_plan(body: DevOpsPlanRequest):
    """
    Preview the boto3 plan for a natural-language AWS command.

    Never executes anything — not even read-only calls. This is the endpoint
    the MCP server exposes to external agents; applying a plan requires the
    OmniDev DevOps module and its confirmation flow.
    """
    try:
        ensure_ai_configured()
        result = await plan_command(body.message)
        return DevOpsPlanResponse(**result)
    except AIConfigurationError as exc:
        raise service_unavailable(str(exc)) from exc
    except Exception as exc:
        raise internal_error("DevOps plan failed.") from exc


@router.post("/command", response_model=DevOpsCommandResponse)
async def devops_command(body: DevOpsCommandRequest):
    """
    Send a natural-language AWS command.

    Examples:
    - "List my EC2 instances"
    - "Launch a t2.micro instance"
    - "Show my S3 buckets"
    """
    try:
        ensure_ai_configured()
        result = await run_command(body.message, body.confirm_destructive)
        return DevOpsCommandResponse(**result)
    except AIConfigurationError as exc:
        raise service_unavailable(str(exc)) from exc
    except Exception as exc:
        raise internal_error("DevOps command failed.") from exc
