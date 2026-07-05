"""Tests for SQLite conversation memory and the session endpoints."""

import json

import httpx
import pytest

from app.config import settings
from app.services import ai_service, session_service


def _install_mock_ollama(monkeypatch, handler):
    transport = httpx.MockTransport(handler)
    real_client = httpx.AsyncClient

    def factory(**kwargs):
        kwargs.pop("transport", None)
        return real_client(transport=transport, **kwargs)

    monkeypatch.setattr(ai_service.httpx, "AsyncClient", factory)
    ai_service._ollama_client = None


def _stream_handler_capturing(seen_payloads, reply="ok"):
    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        seen_payloads.append(payload)
        lines = [json.dumps({"message": {"content": reply}}), json.dumps({"done": True})]
        return httpx.Response(200, text="\n".join(lines))

    return handler


# ── service ─────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_session_roundtrip():
    session_id = await session_service.create_session("Build me a todo app please")
    assert await session_service.session_exists(session_id)

    await session_service.append_message(session_id, "user", "Build me a todo app")
    await session_service.append_message(session_id, "assistant", "Here is a todo app.")

    context = await session_service.context_messages(session_id)
    assert [m["role"] for m in context] == ["user", "assistant"]

    sessions = await session_service.list_sessions()
    assert sessions[0]["id"] == session_id
    assert sessions[0]["message_count"] == 2
    assert "todo app" in sessions[0]["title"]

    assert await session_service.delete_session(session_id)
    assert not await session_service.session_exists(session_id)


@pytest.mark.asyncio
async def test_context_is_bounded():
    session_id = await session_service.create_session("long chat")
    for i in range(40):
        await session_service.append_message(session_id, "user", f"message {i}")
    context = await session_service.context_messages(session_id)
    assert len(context) <= session_service.CONTEXT_MESSAGE_LIMIT
    assert context[-1]["content"] == "message 39"


# ── endpoint: memory across turns ───────────────────────────
@pytest.mark.asyncio
async def test_chat_second_turn_includes_history(client, monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "ollama")
    payloads: list[dict] = []
    _install_mock_ollama(monkeypatch, _stream_handler_capturing(payloads, reply="A todo app."))

    first = await client.post("/api/chat/stream", json={"message": "Build a todo app"})
    assert first.status_code == 200
    events = [json.loads(l) for l in first.text.splitlines() if l.strip()]
    session_id = events[0]["session_id"]

    second = await client.post(
        "/api/chat/stream",
        json={"message": "now add auth", "session_id": session_id},
    )
    assert second.status_code == 200

    # The second model call must include the first turn's user+assistant messages.
    second_messages = payloads[1]["messages"]
    contents = [m["content"] for m in second_messages]
    assert "Build a todo app" in contents
    assert "A todo app." in contents
    assert contents[-1] == "now add auth"


@pytest.mark.asyncio
async def test_chat_unknown_session_404(client, monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "ollama")
    resp = await client.post(
        "/api/chat/stream", json={"message": "hi", "session_id": "does-not-exist"}
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_session_endpoints(client, monkeypatch, coverage_tracker):
    monkeypatch.setattr(settings, "ai_provider", "ollama")
    payloads: list[dict] = []
    _install_mock_ollama(monkeypatch, _stream_handler_capturing(payloads))

    resp = await client.post("/api/chat/stream", json={"message": "hello there"})
    session_id = json.loads(resp.text.splitlines()[0])["session_id"]

    listed = await client.get("/api/chat/sessions")
    assert listed.status_code == 200
    assert any(s["id"] == session_id for s in listed.json()["sessions"])
    coverage_tracker("GET /api/chat/sessions")

    messages = await client.get(f"/api/chat/sessions/{session_id}")
    assert messages.status_code == 200
    roles = [m["role"] for m in messages.json()["messages"]]
    assert roles == ["user", "assistant"]

    deleted = await client.delete(f"/api/chat/sessions/{session_id}")
    assert deleted.status_code == 200
    assert (await client.get(f"/api/chat/sessions/{session_id}")).status_code == 404
