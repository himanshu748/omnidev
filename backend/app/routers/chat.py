"""Chat router — streaming responses with SQLite conversation memory and
optional MCP tool calling."""

from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.schemas.chat import (
    ChatRequest,
    SessionInfo,
    SessionListResponse,
    SessionMessage,
    SessionMessagesResponse,
)
from app.services import session_service
from app.services.ai_service import (
    AIConfigurationError,
    AIResponseError,
    ensure_ai_configured,
    stream_chat,
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
    - `{"session_id": "..."}` — first event; persists across turns
    - `{"delta": "..."}` — a token/chunk of the answer
    - `{"tool_call": {...}}` / `{"tool_result": {...}}` — MCP tool activity
      (only with `use_tools: true`)
    - `{"error": "..."}` — a terminal error (e.g. provider unreachable)
    - `{"done": true}`    — end of stream
    """
    try:
        ensure_ai_configured()
    except AIConfigurationError as exc:
        raise service_unavailable(str(exc)) from exc

    session_id = body.session_id
    if session_id is not None and not await session_service.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Unknown session_id.")
    if session_id is None:
        session_id = await session_service.create_session(body.message)

    history = await session_service.context_messages(session_id)
    await session_service.append_message(session_id, "user", body.message)
    messages = history + [{"role": "user", "content": body.message}]
    system = body.system or DEFAULT_SYSTEM

    async def _events():
        answer_parts: list[str] = []
        yield json.dumps({"session_id": session_id}) + "\n"
        try:
            if body.use_tools:
                # Import here so chat works even if MCP deps are absent.
                from app.services.mcp_client_service import MCPError, run_tool_chat

                try:
                    tool_messages = [{"role": "system", "content": system}, *messages]
                    async for event in run_tool_chat(tool_messages, temperature=body.temperature):
                        if "delta" in event:
                            answer_parts.append(event["delta"])
                        yield json.dumps(event) + "\n"
                except MCPError as exc:
                    yield json.dumps({"error": str(exc)}) + "\n"
                    return
            else:
                async for delta in stream_chat(
                    messages,
                    system=system,
                    temperature=body.temperature,
                ):
                    answer_parts.append(delta)
                    yield json.dumps({"delta": delta}) + "\n"

            if answer_parts:
                await session_service.append_message(
                    session_id, "assistant", "".join(answer_parts)
                )
            yield json.dumps({"done": True}) + "\n"
        except (AIConfigurationError, AIResponseError) as exc:
            yield json.dumps({"error": str(exc)}) + "\n"
        except Exception:
            yield json.dumps({"error": "Generation failed."}) + "\n"

    return StreamingResponse(_events(), media_type="application/x-ndjson")


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions():
    """Recent conversations, newest first."""
    sessions = await session_service.list_sessions()
    return SessionListResponse(sessions=[SessionInfo(**s) for s in sessions])


@router.get("/sessions/{session_id}", response_model=SessionMessagesResponse)
async def session_messages(session_id: str):
    """Full message history for one conversation."""
    if not await session_service.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Unknown session_id.")
    messages = await session_service.list_messages(session_id)
    return SessionMessagesResponse(
        session_id=session_id,
        messages=[SessionMessage(**m) for m in messages],
    )


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a conversation and its messages."""
    if not await session_service.delete_session(session_id):
        raise HTTPException(status_code=404, detail="Unknown session_id.")
    return {"deleted": session_id}
