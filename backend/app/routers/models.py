"""Model management router — list, recommend, and pull local Ollama models."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.schemas.models import (
    InstalledModel,
    ModelsResponse,
    ProviderStatus,
    PullModelRequest,
    RecommendedModel,
)
from app.services import models_service
from app.services.ai_service import AIConfigurationError
from app.routers.errors import bad_request, internal_error, not_found, service_unavailable

router = APIRouter()


@router.get("", response_model=ModelsResponse)
async def list_models():
    """Provider status plus installed and recommended models."""
    try:
        status = await models_service.provider_status()
    except AIConfigurationError as exc:
        raise service_unavailable(str(exc)) from exc
    except Exception as exc:
        raise internal_error("Failed to read model status.") from exc

    installed: list[InstalledModel] = []
    if status.get("reachable") and status.get("provider") == "ollama":
        try:
            installed = [InstalledModel(**m) for m in await models_service.list_installed()]
        except AIConfigurationError:
            installed = []

    return ModelsResponse(
        status=ProviderStatus(**status),
        installed=installed,
        recommended=[RecommendedModel(**m) for m in models_service.RECOMMENDED_MODELS],
    )


@router.delete("")
async def delete_model(name: str):
    """Delete an installed local model to free disk space."""
    try:
        ref = models_service.validate_model_ref(name)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc

    try:
        await models_service.delete_model(ref)
    except FileNotFoundError as exc:
        raise not_found(str(exc)) from exc
    except ValueError as exc:
        raise bad_request(str(exc)) from exc
    except AIConfigurationError as exc:
        raise service_unavailable(str(exc)) from exc
    except Exception as exc:
        raise internal_error("Model deletion failed.") from exc

    return {"deleted": ref}


@router.post("/pull")
async def pull_model(payload: PullModelRequest):
    """
    Pull a local model, streaming newline-delimited JSON progress from Ollama.

    The response is `application/x-ndjson`; each line is a progress event and the
    stream ends on `{"status": "success"}` or `{"error": "..."}`.
    """
    try:
        name = models_service.validate_model_ref(payload.name)
    except ValueError as exc:
        raise service_unavailable(str(exc)) from exc

    async def _events():
        try:
            async for line in models_service.pull_model_events(name):
                yield line
        except AIConfigurationError as exc:
            import json

            yield json.dumps({"error": str(exc)}) + "\n"

    return StreamingResponse(_events(), media_type="application/x-ndjson")
