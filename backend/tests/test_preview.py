import pytest

from app.routers import preview as preview_router


@pytest.mark.asyncio
async def test_preview_requires_mode(client):
    resp = await client.post(
        "/api/preview/check",
        json={"url": "https://example.com", "desktop": False, "mobile": False},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_preview_success(client, monkeypatch, coverage_tracker):
    async def fake_capture(
        browser,
        url: str,
        desktop: bool = True,
        mobile: bool = True,
        wait_seconds: float = 0,
    ):
        return {
            "url": url,
            "title": "Example",
            "status_code": 200,
            "elapsed_ms": 10,
            "desktop_screenshot_b64": "abc",
            "mobile_screenshot_b64": None,
        }

    monkeypatch.setattr(preview_router, "capture_preview", fake_capture)
    resp = await client.post("/api/preview/check", json={"url": "https://example.com"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "Example"
    coverage_tracker("POST /api/preview/check")
