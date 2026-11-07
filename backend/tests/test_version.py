"""One version everywhere: backend, macOS app, and the latest CHANGELOG release."""

import re
from pathlib import Path

import pytest

from app import __version__

ROOT = Path(__file__).resolve().parents[2]


def test_backend_matches_macos_app():
    swift = (ROOT / "macos/Sources/OmniDevMac/Support/AppSettings.swift").read_text()
    match = re.search(r'static let version = "([^"]+)"', swift)
    assert match, "AppSettings.version not found"
    assert match.group(1) == __version__


def test_backend_matches_latest_changelog_release():
    changelog = (ROOT / "CHANGELOG.md").read_text()
    released = re.findall(r"^## \[(\d+\.\d+\.\d+)\]", changelog, flags=re.MULTILINE)
    assert released, "no released version in CHANGELOG.md"
    assert released[0] == __version__


@pytest.mark.asyncio
async def test_health_and_openapi_report_the_version():
    import httpx

    from app.main import app

    transport = httpx.ASGITransport(app=app, client=("127.0.0.1", 1))
    async with httpx.AsyncClient(transport=transport, base_url="http://127.0.0.1:8000") as ac:
        assert (await ac.get("/health")).json()["version"] == __version__
        assert (await ac.get("/openapi.json")).json()["info"]["version"] == __version__
