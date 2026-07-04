import pytest

from app.routers import vision as vision_router
from app.services.ai_service import AIConfigurationError


@pytest.mark.asyncio
async def test_vision_rejects_bad_type(client):
    files = {"image": ("sample.txt", b"nope", "text/plain")}
    data = {"mode": "analyze", "prompt": ""}
    resp = await client.post("/api/vision/analyze", files=files, data=data)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_vision_rejects_oversized_image(client):
    from app.routers.vision import MAX_IMAGE_BYTES

    big = b"\x89PNG" + b"0" * (MAX_IMAGE_BYTES + 1)
    files = {"image": ("big.png", big, "image/png")}
    data = {"mode": "analyze", "prompt": ""}
    resp = await client.post("/api/vision/analyze", files=files, data=data)
    assert resp.status_code == 413


@pytest.mark.asyncio
async def test_vision_success(client, monkeypatch, coverage_tracker):
    async def fake_analyze(
        image_bytes: bytes,
        content_type: str,
        mode,
        custom_prompt=None,
    ):
        return {
            "mode": mode,
            "result": "ok",
            "model": "test",
            "tokens_used": 10,
        }

    monkeypatch.setattr(vision_router, "analyze_image", fake_analyze)
    files = {"image": ("sample.png", b"pngdata", "image/png")}
    data = {"mode": "analyze", "prompt": ""}
    resp = await client.post("/api/vision/analyze", files=files, data=data)
    assert resp.status_code == 200
    assert resp.json()["result"] == "ok"
    coverage_tracker("POST /api/vision/analyze")


@pytest.mark.asyncio
async def test_vision_missing_gemini_key_returns_503(client, monkeypatch):
    async def fake_analyze(**kwargs):
        raise AIConfigurationError(
            "GEMINI_API_KEY is not set. Get a free key at https://aistudio.google.com/apikey"
        )

    monkeypatch.setattr(vision_router, "analyze_image", fake_analyze)
    files = {"image": ("sample.png", b"pngdata", "image/png")}
    data = {"mode": "analyze", "prompt": ""}
    resp = await client.post("/api/vision/analyze", files=files, data=data)

    assert resp.status_code == 503
    assert "GEMINI_API_KEY" in resp.json()["detail"]
