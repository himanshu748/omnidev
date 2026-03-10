import pytest

from app.routers import vision as vision_router


@pytest.mark.asyncio
async def test_vision_rejects_bad_type(client):
    files = {"image": ("sample.txt", b"nope", "text/plain")}
    data = {"mode": "analyze", "prompt": ""}
    resp = await client.post("/api/vision/analyze", files=files, data=data)
    assert resp.status_code == 400


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
