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


# Foreign-key regressions: all databases remain inside the temporary data_dir.
def test_connections_enable_foreign_keys():
    for _ in range(2):
        with session_service._connect() as conn:
            assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1


def test_missing_and_deleted_sessions_reject_messages():
    session_id = session_service._create_session_sync("deleted")
    session_service._delete_session_sync(session_id)
    for missing_id in ("never-existed", session_id):
        with pytest.raises(session_service.SessionNotFoundError):
            session_service._append_message_sync(missing_id, "user", "not saved")
    with session_service._connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0] == 0


def test_direct_session_delete_cascades():
    session_id = session_service._create_session_sync("cascade")
    session_service._append_message_sync(session_id, "user", "hello")
    with session_service._connect() as conn:
        conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    assert session_service._list_messages_sync(session_id) == []


def test_delete_committed_while_append_is_preparing(monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event, current_thread

    session_id = session_service._create_session_sync("concurrent")
    preparing, deleted = Event(), Event()
    original_now = session_service._now

    def pause_writer() -> str:
        if current_thread().name.startswith("append-regression"):
            preparing.set()
            assert deleted.wait(5), "delete did not complete"
        return original_now()

    monkeypatch.setattr(session_service, "_now", pause_writer)
    with ThreadPoolExecutor(max_workers=1, thread_name_prefix="append-regression") as pool:
        future = pool.submit(session_service._append_message_sync, session_id, "user", "late")
        try:
            assert preparing.wait(5), "append did not start"
            assert session_service._delete_session_sync(session_id)
        finally:
            deleted.set()
        with pytest.raises(session_service.SessionNotFoundError):
            future.result(timeout=5)
    with session_service._connect() as conn:
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
        assert conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0] == 0


def test_existing_database_preserves_history_and_enforces_new_writes():
    session_id = session_service._create_session_sync("legacy")
    session_service._append_message_sync(session_id, "user", "keep me")
    # Simulate a database written by the old implementation, including an orphan.
    with session_service._connect() as conn:
        conn.execute("PRAGMA foreign_keys = OFF")
        conn.execute(
            "INSERT INTO messages (session_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            ("legacy-orphan", "user", "preserve old data", session_service._now()),
        )
    session_service._append_message_sync(session_id, "assistant", "still works")
    assert [m["content"] for m in session_service._list_messages_sync(session_id)] == [
        "keep me", "still works"
    ]
    with pytest.raises(session_service.SessionNotFoundError):
        session_service._append_message_sync("new-orphan", "user", "refused")
    assert len(session_service._list_messages_sync("legacy-orphan")) == 1


def test_other_integrity_errors_are_not_missing_sessions():
    import sqlite3

    session_id = session_service._create_session_sync("valid")
    with pytest.raises(sqlite3.IntegrityError):
        session_service._append_message_sync(session_id, "invalid-role", "refused")


@pytest.mark.asyncio
async def test_chat_delete_between_lookup_and_append_returns_404(client, monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "ollama")
    session_id = await session_service.create_session("race")
    original_exists = session_service.session_exists

    async def delete_after_lookup(value: str) -> bool:
        exists = await original_exists(value)
        await session_service.delete_session(value)
        return exists

    monkeypatch.setattr(session_service, "session_exists", delete_after_lookup)
    response = await client.post(
        "/api/chat/stream", json={"session_id": session_id, "message": "late"}
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Unknown session_id."}


@pytest.mark.asyncio
async def test_chat_deleted_during_generation_emits_missing_session(client, monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "ollama")
    session_id = await session_service.create_session("stream race")

    async def delete_while_streaming(*args, **kwargs):
        yield "answer"
        await session_service.delete_session(session_id)

    monkeypatch.setattr("app.routers.chat.stream_chat", delete_while_streaming)
    response = await client.post(
        "/api/chat/stream", json={"session_id": session_id, "message": "hello"}
    )
    assert response.status_code == 200
    events = [json.loads(line) for line in response.text.splitlines()]
    assert events[-1] == {"error": "Unknown session_id."}
    assert {"done": True} not in events
    assert await session_service.list_messages(session_id) == []
