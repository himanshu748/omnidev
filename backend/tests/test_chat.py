"""Tests for the streaming chat endpoint and stream_text service."""

import json

import httpx
import pytest

from app.config import settings
from app.services import ai_service
from app.services.ai_service import AIConfigurationError, stream_text


@pytest.fixture(autouse=True)
def _reset_shared_ollama_client():
    ai_service._ollama_client = None
    yield
    ai_service._ollama_client = None


def _install_mock_ollama(monkeypatch, handler):
    transport = httpx.MockTransport(handler)
    real_client = httpx.AsyncClient

    def factory(**kwargs):
        kwargs.pop("transport", None)
        return real_client(transport=transport, **kwargs)

    monkeypatch.setattr(ai_service.httpx, "AsyncClient", factory)


def _ollama_stream_handler(deltas):
    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        assert payload["stream"] is True
        lines = [json.dumps({"message": {"content": d}}) for d in deltas]
        lines.append(json.dumps({"done": True}))
        return httpx.Response(200, text="\n".join(lines))

    return handler


# ── service ─────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_stream_text_ollama_yields_deltas(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "ollama")
    _install_mock_ollama(monkeypatch, _ollama_stream_handler(["Hel", "lo", " world"]))
    out = [chunk async for chunk in stream_text("hi")]
    assert "".join(out) == "Hello world"


@pytest.mark.asyncio
async def test_stream_text_ollama_missing_model(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "ollama")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"error": "not found"})

    _install_mock_ollama(monkeypatch, handler)
    with pytest.raises(AIConfigurationError):
        async for _ in stream_text("hi"):
            pass


# ── endpoint ────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_chat_stream_endpoint(client, monkeypatch, coverage_tracker):
    monkeypatch.setattr(settings, "ai_provider", "ollama")
    _install_mock_ollama(monkeypatch, _ollama_stream_handler(["Local ", "AI ", "cockpit"]))

    resp = await client.post("/api/chat/stream", json={"message": "What is OmniDev?"})
    assert resp.status_code == 200
    events = [json.loads(l) for l in resp.text.splitlines() if l.strip()]
    text = "".join(e["delta"] for e in events if "delta" in e)
    assert text == "Local AI cockpit"
    assert events[-1] == {"done": True}
    coverage_tracker("POST /api/chat/stream")


@pytest.mark.asyncio
async def test_chat_stream_unconfigured_provider(client, monkeypatch, coverage_tracker):
    monkeypatch.setattr(settings, "ai_provider", "gemini")
    monkeypatch.setattr(settings, "gemini_api_key", "")
    resp = await client.post("/api/chat/stream", json={"message": "hi"})
    assert resp.status_code == 503
    coverage_tracker("POST /api/chat/stream")


@pytest.mark.asyncio
async def test_chat_stream_error_becomes_event(client, monkeypatch, coverage_tracker):
    monkeypatch.setattr(settings, "ai_provider", "ollama")

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused")

    _install_mock_ollama(monkeypatch, handler)
    resp = await client.post("/api/chat/stream", json={"message": "hi"})
    assert resp.status_code == 200  # stream opens, error is delivered as an event
    events = [json.loads(l) for l in resp.text.splitlines() if l.strip()]
    assert any("error" in e for e in events)
    coverage_tracker("POST /api/chat/stream")


@pytest.mark.asyncio
async def test_chat_stream_validates_message(client):
    resp = await client.post("/api/chat/stream", json={"message": ""})
    assert resp.status_code == 422
