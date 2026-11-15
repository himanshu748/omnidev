"""The loopback-only middleware fails safe if the API is exposed remotely."""

import httpx
import pytest

from app.config import settings
from app.main import app


def _client(host: str, base_url: str = "http://127.0.0.1:8000") -> httpx.AsyncClient:
    transport = httpx.ASGITransport(app=app, client=(host, 12345))
    return httpx.AsyncClient(transport=transport, base_url=base_url)


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


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "base_url",
    ["http://127.0.0.1:8010", "http://localhost:8000", "http://LOCALHOST", "http://[::1]:8010"],
)
async def test_loopback_host_names_allowed(monkeypatch, base_url):
    monkeypatch.setattr(settings, "allow_remote_clients", False)
    async with _client("127.0.0.1", base_url) as ac:
        resp = await ac.get("/health")
    assert resp.status_code == 200


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "host",
    [
        "rebind.attacker.example:8010",  # resolves to 127.0.0.1 after rebinding
        "127.0.0.1.nip.io:8010",
        "localhost.attacker.example",
        "evil.localhost:8010",
        "",
    ],
)
async def test_rebinding_hosts_refused(monkeypatch, host):
    monkeypatch.setattr(settings, "allow_remote_clients", False)
    async with _client("127.0.0.1") as ac:
        resp = await ac.post("/api/agent/sandbox", json={"mode": "off"}, headers={"host": host})
    assert resp.status_code == 403
    assert "DNS rebinding" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_host_check_skipped_when_remote_clients_allowed(monkeypatch):
    monkeypatch.setattr(settings, "allow_remote_clients", True)
    async with _client("127.0.0.1", "http://omnidev.lan:8000") as ac:
        resp = await ac.get("/health")
    assert resp.status_code != 403
