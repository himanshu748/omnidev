"""Chat router — stream AI responses token by token via the active provider."""

from __future__ import annotations

import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.schemas.chat import ChatRequest
from app.services.ai_service import (
    AIConfigurationError,
    AIResponseError,
    ensure_ai_configured,
    stream_text,
)
from app.routers.errors import service_unavailable

router = APIRouter()

DEFAULT_SYSTEM = (
    "You are OmniDev, a concise local-first developer assistant. "
    "Answer clearly and practically. Prefer short code blocks over prose when relevant."
)


@router.post("/stream")
async def chat_stream(body: ChatRequest):
    """
    Stream a chat completion as newline-delimited JSON.

    Each line is one of:
    - `{"delta": "..."}` — a token/chunk of the answer
    - `{"error": "..."}` — a terminal error (e.g. provider unreachable)
    - `{"done": true}`    — end of stream
    """
    try:
        ensure_ai_configured()
    except AIConfigurationError as exc:
        raise service_unavailable(str(exc)) from exc

    async def _events():
        try:
            async for delta in stream_text(
                body.message,
                system=body.system or DEFAULT_SYSTEM,
                temperature=body.temperature,
            ):
                yield json.dumps({"delta": delta}) + "\n"
            yield json.dumps({"done": True}) + "\n"
        except (AIConfigurationError, AIResponseError) as exc:
            yield json.dumps({"error": str(exc)}) + "\n"
        except Exception:
            yield json.dumps({"error": "Generation failed."}) + "\n"

    return StreamingResponse(_events(), media_type="application/x-ndjson")
