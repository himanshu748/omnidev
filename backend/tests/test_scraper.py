import pytest

from app.routers import scraper as scraper_router


@pytest.mark.asyncio
async def test_scraper_endpoint(client, monkeypatch, coverage_tracker):
    async def fake_scrape(
        browser,
        url: str,
        wait_for=None,
        extract="text",
        stealth=True,
        headers=None,
        cookies=None,
        javascript=None,
        timeout_ms=30000,
        wait_seconds=0,
        proxy=None,
        viewport_width=1920,
        viewport_height=1080,
        block_resources=None,
    ):
        return {
            "url": url,
            "title": "Example",
            "status_code": 200,
            "content": "Hello",
            "screenshot_b64": None,
            "pdf_b64": None,
            "links": None,
            "metadata": None,
        }

    monkeypatch.setattr(scraper_router, "scrape", fake_scrape)
    resp = await client.post("/api/scraper/scrape", json={"url": "https://example.com"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "Example"
    coverage_tracker("POST /api/scraper/scrape")


@pytest.mark.asyncio
async def test_scraper_error(client, monkeypatch):
    async def fake_scrape(*args, **kwargs):
        raise RuntimeError("Scrape failed")

    monkeypatch.setattr(scraper_router, "scrape", fake_scrape)
    resp = await client.post("/api/scraper/scrape", json={"url": "https://example.com"})
    assert resp.status_code == 500


@pytest.mark.asyncio
async def test_scraper_returns_503_when_browser_unavailable(client, app, monkeypatch):
    app.state.browser = None

    async def fake_scrape(*args, **kwargs):
        raise AssertionError("scrape should not be called without a browser")

    monkeypatch.setattr(scraper_router, "scrape", fake_scrape)
    resp = await client.post("/api/scraper/scrape", json={"url": "https://example.com"})

    assert resp.status_code == 503
    assert "Playwright browser is unavailable" in resp.json()["detail"]
    app.state.browser = object()
