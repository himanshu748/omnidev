"""The loopback-only middleware fails safe if the API is exposed remotely."""

import httpx
import pytest

from app.config import settings
from app.main import app


def _client(host: str) -> httpx.AsyncClient:
    transport = httpx.ASGITransport(app=app, client=(host, 12345))
    return httpx.AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_loopback_client_allowed():
    async with _client("127.0.0.1") as ac:
        resp = await ac.get("/health")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_remote_client_refused_by_default(monkeypatch):
    monkeypatch.setattr(settings, "allow_remote_clients", False)
    async with _client("203.0.113.7") as ac:
        resp = await ac.get("/api/storage/buckets")
    assert resp.status_code == 403
    assert "loopback-only" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_remote_client_allowed_when_opted_in(monkeypatch):
    monkeypatch.setattr(settings, "allow_remote_clients", True)
    async with _client("203.0.113.7") as ac:
        resp = await ac.get("/health")
    # Not blocked by the loopback guard (may still hit other logic, but not 403).
    assert resp.status_code != 403
