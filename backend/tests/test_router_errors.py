import pytest

from app.config import settings
from app.routers import devops, scraper, storage, vision


SECRET_LIKE_ERROR = "provider failed with sk-live-secret-token and /private/local/path"


@pytest.mark.asyncio
async def test_storage_error_details_are_sanitized(client, monkeypatch):
    async def fake_list_buckets():
        raise RuntimeError(SECRET_LIKE_ERROR)

    monkeypatch.setattr(storage, "list_buckets", fake_list_buckets)

    response = await client.get("/api/storage/buckets")

    assert response.status_code == 500
    assert response.json()["detail"] == "Storage bucket listing failed."
    assert "sk-live-secret-token" not in response.text
    assert "/private/local/path" not in response.text


@pytest.mark.asyncio
async def test_vision_error_details_are_sanitized(client, monkeypatch):
    async def fake_analyze_image(**kwargs):
        raise RuntimeError(SECRET_LIKE_ERROR)

    monkeypatch.setattr(vision, "analyze_image", fake_analyze_image)

    response = await client.post(
        "/api/vision/analyze",
        files={"image": ("sample.png", b"pngdata", "image/png")},
        data={"mode": "analyze", "prompt": ""},
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "Vision analysis failed."
    assert "sk-live-secret-token" not in response.text


@pytest.mark.asyncio
async def test_devops_error_details_are_sanitized(client, monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", "test-gemini-key")
    monkeypatch.setattr(settings, "aws_access_key_id", "test-access-key")
    monkeypatch.setattr(settings, "aws_secret_access_key", "test-secret-key")

    async def fake_run_command(*args, **kwargs):
        raise RuntimeError(SECRET_LIKE_ERROR)

    monkeypatch.setattr(devops, "run_command", fake_run_command)

    response = await client.post(
        "/api/devops/command",
        json={"message": "List instances", "confirm_destructive": False},
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "DevOps command failed."
    assert "sk-live-secret-token" not in response.text


@pytest.mark.asyncio
async def test_scraper_error_details_are_sanitized(client, monkeypatch):
    async def fake_scrape(*args, **kwargs):
        raise RuntimeError(SECRET_LIKE_ERROR)

    monkeypatch.setattr(scraper, "scrape", fake_scrape)

    response = await client.post("/api/scraper/scrape", json={"url": "https://example.com"})

    assert response.status_code == 500
    assert response.json()["detail"] == "Web scraping failed."
    assert "sk-live-secret-token" not in response.text
