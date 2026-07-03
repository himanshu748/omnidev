"""DevOps Agent router — natural-language AWS management."""

from __future__ import annotations

from fastapi import APIRouter

from app.config import settings
from app.schemas.devops import DevOpsCommandRequest, DevOpsCommandResponse
from app.services.devops_agent import run_command
from app.routers.errors import internal_error, service_unavailable

router = APIRouter()


@router.post("/command", response_model=DevOpsCommandResponse)
async def devops_command(body: DevOpsCommandRequest):
    """
    Send a natural-language AWS command.

    Examples:
    - "List my EC2 instances"
    - "Launch a t2.micro instance"
    - "Show my S3 buckets"
    """
    if not settings.gemini_api_key:
        raise service_unavailable(
            "GEMINI_API_KEY is not set. Get a free key at https://aistudio.google.com/apikey"
        )
    try:
        result = await run_command(body.message, body.confirm_destructive)
        return DevOpsCommandResponse(**result)
    except Exception as exc:
        raise internal_error("DevOps command failed.") from exc
