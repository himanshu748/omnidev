"""Tests for the local model-management API and service."""

import json

import httpx
import pytest

from app.config import settings
from app.routers import models as models_router
from app.services import ai_service, models_service
from app.services.ai_service import AIConfigurationError


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


# ── validate_model_ref ──────────────────────────────────────
@pytest.mark.parametrize("ref", ["gemma4:e4b", "llama3.2:3b", "library/qwen2.5-coder:7b", "gemma4"])
def test_valid_model_refs(ref):
    assert models_service.validate_model_ref(ref) == ref


@pytest.mark.parametrize("ref", ["", "; rm -rf /", "model with spaces", "a" * 300, "../etc/passwd"])
def test_invalid_model_refs_rejected(ref):
    with pytest.raises(ValueError):
        models_service.validate_model_ref(ref)


# ── provider gating ─────────────────────────────────────────
@pytest.mark.asyncio
async def test_model_management_requires_ollama(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "gemini")
    monkeypatch.setattr(settings, "gemini_api_key", "some-key")
    with pytest.raises(AIConfigurationError):
        await models_service.list_installed()


# ── service: list + status ──────────────────────────────────
@pytest.mark.asyncio
async def test_list_installed_parses_ollama_tags(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "ollama")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/tags"
        return httpx.Response(
            200,
            json={
                "models": [
                    {
                        "name": "gemma4:e4b",
                        "size": 9_600_000_000,
                        "modified_at": "2026-07-01T00:00:00Z",
                        "details": {"parameter_size": "4B", "quantization_level": "Q4_0"},
                    }
                ]
            },
        )

    _install_mock_ollama(monkeypatch, handler)
    installed = await models_service.list_installed()
    assert installed[0]["name"] == "gemma4:e4b"
    assert installed[0]["size_gb"] == 9.6
    assert installed[0]["parameter_size"] == "4B"


@pytest.mark.asyncio
async def test_provider_status_marks_default_ready(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "ollama")
    monkeypatch.setattr(settings, "ollama_model", "gemma4:e4b")
    monkeypatch.setattr(settings, "ollama_vision_model", "gemma4:e4b")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"models": [{"name": "gemma4:e4b", "size": 9_600_000_000}]})

    _install_mock_ollama(monkeypatch, handler)
    status = await models_service.provider_status()
    assert status["provider"] == "ollama"
    assert status["reachable"] is True
    assert status["text_model_ready"] is True
    assert status["vision_model_ready"] is True


@pytest.mark.asyncio
async def test_provider_status_unreachable_ollama(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "ollama")

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused")

    _install_mock_ollama(monkeypatch, handler)
    status = await models_service.provider_status()
    assert status["reachable"] is False
    assert status["text_model_ready"] is False


# ── service: delete ─────────────────────────────────────────
@pytest.mark.asyncio
async def test_delete_model_calls_ollama(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "ollama")
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["path"] = request.url.path
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={})

    _install_mock_ollama(monkeypatch, handler)
    await models_service.delete_model("gemma4:e2b")
    assert seen == {"method": "DELETE", "path": "/api/delete", "body": {"model": "gemma4:e2b"}}


@pytest.mark.asyncio
async def test_delete_model_missing_raises(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "ollama")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"error": "model not found"})

    _install_mock_ollama(monkeypatch, handler)
    with pytest.raises(FileNotFoundError):
        await models_service.delete_model("nope:latest")


@pytest.mark.asyncio
async def test_delete_model_refuses_active_default(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "ollama")
    monkeypatch.setattr(settings, "ollama_model", "gemma4:12b")
    with pytest.raises(ValueError):
        await models_service.delete_model("gemma4:12b")


# ── HTTP endpoints ──────────────────────────────────────────
@pytest.mark.asyncio
async def test_models_endpoint_lists_recommended(client, monkeypatch, coverage_tracker):
    monkeypatch.setattr(settings, "ai_provider", "ollama")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"models": [{"name": "gemma4:e4b", "size": 9_600_000_000}]})

    _install_mock_ollama(monkeypatch, handler)
    resp = await client.get("/api/models")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"]["provider"] == "ollama"
    assert any(m["name"] == "gemma4:e4b" for m in body["recommended"])
    assert any(m["name"] == "gemma4:e4b" for m in body["installed"])
    coverage_tracker("GET /api/models")


@pytest.mark.asyncio
async def test_models_endpoint_gemini_provider(client, monkeypatch, coverage_tracker):
    monkeypatch.setattr(settings, "ai_provider", "gemini")
    monkeypatch.setattr(settings, "gemini_api_key", "k")
    resp = await client.get("/api/models")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"]["provider"] == "gemini"
    assert body["installed"] == []
    coverage_tracker("GET /api/models")


@pytest.mark.asyncio
async def test_pull_endpoint_rejects_bad_ref(client, monkeypatch, coverage_tracker):
    monkeypatch.setattr(settings, "ai_provider", "ollama")
    resp = await client.post("/api/models/pull", json={"name": "bad ref !!"})
    assert resp.status_code == 503
    coverage_tracker("POST /api/models/pull")


@pytest.mark.asyncio
async def test_pull_endpoint_streams_progress(client, monkeypatch, coverage_tracker):
    monkeypatch.setattr(settings, "ai_provider", "ollama")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/pull"
        body = "\n".join(
            [
                json.dumps({"status": "pulling manifest"}),
                json.dumps({"status": "downloading", "completed": 50, "total": 100}),
                json.dumps({"status": "success"}),
            ]
        )
        return httpx.Response(200, text=body)

    _install_mock_ollama(monkeypatch, handler)
    resp = await client.post("/api/models/pull", json={"name": "gemma4:e4b"})
    assert resp.status_code == 200
    lines = [json.loads(l) for l in resp.text.splitlines() if l.strip()]
    assert lines[0]["status"] == "pulling manifest"
    assert lines[-1]["status"] == "success"
    coverage_tracker("POST /api/models/pull")


@pytest.mark.asyncio
async def test_delete_endpoint_deletes_model(client, monkeypatch, coverage_tracker):
    monkeypatch.setattr(settings, "ai_provider", "ollama")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={})

    _install_mock_ollama(monkeypatch, handler)
    resp = await client.delete("/api/models", params={"name": "gemma4:e2b"})
    assert resp.status_code == 200
    assert resp.json() == {"deleted": "gemma4:e2b"}
    coverage_tracker("DELETE /api/models")


@pytest.mark.asyncio
async def test_delete_endpoint_rejects_bad_ref(client, monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "ollama")
    resp = await client.delete("/api/models", params={"name": "; rm -rf /"})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_delete_endpoint_missing_model_404(client, monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "ollama")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"error": "model not found"})

    _install_mock_ollama(monkeypatch, handler)
    resp = await client.delete("/api/models", params={"name": "nope:latest"})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_endpoint_refuses_active_model(client, monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "ollama")
    monkeypatch.setattr(settings, "ollama_model", "gemma4:12b")
    resp = await client.delete("/api/models", params={"name": "gemma4:12b"})
    assert resp.status_code == 400
