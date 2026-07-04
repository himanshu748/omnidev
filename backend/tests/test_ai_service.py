"""Tests for the provider-agnostic AI layer (Gemini / Ollama selection and Ollama HTTP path)."""

import json

import httpx
import pytest

from app.config import settings
from app.services import ai_service
from app.services.ai_service import (
    AIConfigurationError,
    AIResponseError,
    ensure_ai_configured,
    generate_structured,
    generate_text,
    get_model,
    get_provider,
)


@pytest.fixture(autouse=True)
def _reset_shared_ollama_client():
    """Drop the shared client so each test builds one from its own transport."""
    ai_service._ollama_client = None
    yield
    ai_service._ollama_client = None


def _install_mock_ollama(monkeypatch, handler):
    """Route ai_service's shared httpx.AsyncClient through a mock transport."""
    transport = httpx.MockTransport(handler)
    real_client = httpx.AsyncClient

    def factory(**kwargs):
        kwargs.pop("transport", None)
        return real_client(transport=transport, **kwargs)

    monkeypatch.setattr(ai_service.httpx, "AsyncClient", factory)


# ── Provider selection ──────────────────────────────────────
def test_auto_prefers_gemini_when_key_set(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "auto")
    monkeypatch.setattr(settings, "gemini_api_key", "some-key")
    assert get_provider() == "gemini"
    assert get_model() == settings.gemini_model


def test_auto_falls_back_to_ollama_without_key(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "auto")
    monkeypatch.setattr(settings, "gemini_api_key", "")
    assert get_provider() == "ollama"
    assert get_model() == settings.ollama_model
    assert get_model(vision=True) == settings.ollama_vision_model


def test_unknown_provider_raises(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "hal9000")
    with pytest.raises(AIConfigurationError):
        get_provider()


def test_ensure_ai_configured_gemini_without_key(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "gemini")
    monkeypatch.setattr(settings, "gemini_api_key", "")
    with pytest.raises(AIConfigurationError, match="GEMINI_API_KEY"):
        ensure_ai_configured()


def test_ensure_ai_configured_ollama_needs_no_key(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "ollama")
    monkeypatch.setattr(settings, "gemini_api_key", "")
    ensure_ai_configured()


# ── Ollama HTTP path ────────────────────────────────────────
@pytest.mark.asyncio
async def test_ollama_generate_text(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "ollama")

    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        assert payload["model"] == settings.ollama_model
        assert payload["stream"] is False
        assert payload["messages"][0] == {"role": "system", "content": "be brief"}
        return httpx.Response(200, json={"message": {"role": "assistant", "content": "hello"}})

    _install_mock_ollama(monkeypatch, handler)
    result = await generate_text("hi", system="be brief")
    assert result == "hello"


@pytest.mark.asyncio
async def test_ollama_generate_structured(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "ollama")
    schema = {
        "type": "object",
        "properties": {"action": {"type": "string"}},
        "required": ["action"],
    }

    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        assert payload["format"] == schema
        return httpx.Response(
            200,
            json={"message": {"role": "assistant", "content": '{"action": "list_ec2"}'}},
        )

    _install_mock_ollama(monkeypatch, handler)
    result = await generate_structured("list instances", schema=schema, tool_name="return_intent")
    assert result == {"action": "list_ec2"}


@pytest.mark.asyncio
async def test_ollama_structured_invalid_json_raises(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "ollama")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"message": {"role": "assistant", "content": "not json"}})

    _install_mock_ollama(monkeypatch, handler)
    with pytest.raises(AIResponseError):
        await generate_structured("x", schema={"type": "object"}, tool_name="return_intent")


@pytest.mark.asyncio
async def test_ollama_unreachable_raises_configuration_error(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "ollama")

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused")

    _install_mock_ollama(monkeypatch, handler)
    with pytest.raises(AIConfigurationError, match="Cannot reach Ollama"):
        await generate_text("hi")


@pytest.mark.asyncio
async def test_ollama_missing_model_raises_configuration_error(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "ollama")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"error": "model not found"})

    _install_mock_ollama(monkeypatch, handler)
    with pytest.raises(AIConfigurationError, match="ollama pull"):
        await generate_text("hi")


@pytest.mark.asyncio
async def test_ollama_vision_uses_vision_model(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "ollama")

    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        assert payload["model"] == settings.ollama_vision_model
        assert payload["messages"][0]["images"]
        return httpx.Response(
            200,
            json={
                "message": {"role": "assistant", "content": "a cat"},
                "prompt_eval_count": 5,
                "eval_count": 7,
            },
        )

    _install_mock_ollama(monkeypatch, handler)
    result = await ai_service.analyze_image_bytes("describe", b"pngdata", "image/png")
    assert result["result"] == "a cat"
    assert result["model"] == settings.ollama_vision_model
    assert result["tokens_used"] == 12


# ── Shared client lifecycle ─────────────────────────────────
@pytest.mark.asyncio
async def test_ollama_client_is_reused_and_closed(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "ollama")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"message": {"role": "assistant", "content": "ok"}})

    _install_mock_ollama(monkeypatch, handler)
    await generate_text("one")
    first = ai_service._ollama_client
    assert first is not None
    await generate_text("two")
    assert ai_service._ollama_client is first
    await ai_service.close_ai_clients()
    assert ai_service._ollama_client is None
    assert first.is_closed


# ── Gemini schema conversion ────────────────────────────────
def test_to_gemini_schema_roundtrip():
    schema = {
        "type": "object",
        "properties": {
            "files": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path"},
                    },
                    "required": ["path"],
                },
            },
            "mode": {"type": "string", "enum": ["a", "b"]},
        },
        "required": ["files"],
    }
    converted = ai_service._to_gemini_schema(schema)
    assert converted.type.name == "OBJECT"
    assert converted.required == ["files"]
    assert converted.properties["files"].type.name == "ARRAY"
    assert converted.properties["files"].items.properties["path"].type.name == "STRING"
    assert converted.properties["mode"].enum == ["a", "b"]
