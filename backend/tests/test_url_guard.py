"""Tests for the SSRF URL guard used by the scraper and preview services."""

import pytest

from app.services import url_guard
from app.services.url_guard import (
    BlockedURLError,
    is_blocked_host,
    validate_proxy,
    validate_public_url,
)


@pytest.mark.parametrize(
    "url",
    [
        "http://localhost/",
        "http://localhost:8000/health",
        "http://127.0.0.1/",
        "https://169.254.169.254/latest/meta-data/",
        "http://100.100.100.200/",
        "http://10.0.0.5/",
        "http://192.168.1.1/",
        "http://172.16.5.4/",
        "http://[::1]/",
        "http://metadata.google.internal/",
        "file:///etc/passwd",
        "ftp://example.com/",
        "http://0.0.0.0/",
        "not-a-url",
        "",
    ],
)
def test_blocks_dangerous_urls(url):
    with pytest.raises(BlockedURLError):
        validate_public_url(url)


def test_allows_public_ip_literal():
    assert validate_public_url("http://1.1.1.1/") == "http://1.1.1.1/"


def test_allows_public_host(monkeypatch):
    # Resolve to a public address deterministically (no real DNS in CI).
    monkeypatch.setattr(
        url_guard.socket,
        "getaddrinfo",
        lambda host, port: [(2, 1, 6, "", ("93.184.216.34", 0))],
    )
    assert validate_public_url("https://example.com/path") == "https://example.com/path"


def test_blocks_host_resolving_to_private(monkeypatch):
    # DNS-rebinding style: a public name that points at a private IP.
    monkeypatch.setattr(
        url_guard.socket,
        "getaddrinfo",
        lambda host, port: [(2, 1, 6, "", ("10.1.2.3", 0))],
    )
    with pytest.raises(BlockedURLError, match="private/reserved"):
        validate_public_url("https://sneaky.example.com/")


def test_blocks_unresolvable_host(monkeypatch):
    def _boom(host, port):
        raise url_guard.socket.gaierror("nope")

    monkeypatch.setattr(url_guard.socket, "getaddrinfo", _boom)
    with pytest.raises(BlockedURLError, match="resolve"):
        validate_public_url("https://does-not-exist.invalid/")


@pytest.mark.parametrize(
    "host",
    ["127.0.0.1", "localhost", "169.254.169.254", "10.0.0.5", "192.168.1.1",
     "::1", "metadata.google.internal", "", None],
)
def test_is_blocked_host_rejects_internal(host):
    # The per-hop redirect/rebinding guard must reject every internal target.
    assert is_blocked_host(host) is True


def test_is_blocked_host_allows_public_literal():
    assert is_blocked_host("1.1.1.1") is False


def test_is_blocked_host_reresolves_dns(monkeypatch):
    # A name that resolves to a private IP is blocked at fetch time (rebinding).
    monkeypatch.setattr(
        url_guard.socket, "getaddrinfo",
        lambda host, port: [(2, 1, 6, "", ("10.9.9.9", 0))],
    )
    assert is_blocked_host("rebind.example.com") is True


@pytest.mark.asyncio
async def test_resolve_safe_url_blocks_redirect_to_internal(monkeypatch):
    # Public entry that 302-redirects to a loopback host must be refused.
    monkeypatch.setattr(
        url_guard.socket, "getaddrinfo",
        lambda host, port: [(2, 1, 6, "", ("93.184.216.34", 0))]
        if host == "public.example" else
        (_ for _ in ()).throw(url_guard.socket.gaierror("n/a")),
    )

    def handler(request):
        return url_guard.httpx.Response(302, headers={"location": "http://127.0.0.1:9/"})

    transport = url_guard.httpx.MockTransport(handler)
    real = url_guard.httpx.AsyncClient

    def factory(**kw):
        kw.pop("transport", None)
        return real(transport=transport, **kw)

    monkeypatch.setattr(url_guard.httpx, "AsyncClient", factory)
    with pytest.raises(BlockedURLError, match="private/reserved"):
        await url_guard.resolve_safe_url("http://public.example/go")


@pytest.mark.asyncio
async def test_resolve_safe_url_allows_public_chain(monkeypatch):
    monkeypatch.setattr(
        url_guard.socket, "getaddrinfo",
        lambda host, port: [(2, 1, 6, "", ("93.184.216.34", 0))],
    )
    hops = {"http://public.example/go": "https://public.example/final"}

    def handler(request):
        loc = hops.get(str(request.url))
        if loc:
            return url_guard.httpx.Response(302, headers={"location": loc})
        return url_guard.httpx.Response(200, text="ok")

    transport = url_guard.httpx.MockTransport(handler)
    real = url_guard.httpx.AsyncClient
    monkeypatch.setattr(
        url_guard.httpx, "AsyncClient",
        lambda **kw: real(transport=transport, **{k: v for k, v in kw.items() if k != "transport"}),
    )
    final = await url_guard.resolve_safe_url("http://public.example/go")
    assert final == "https://public.example/final"


def test_proxy_validation():
    assert validate_proxy(None) is None
    assert validate_proxy("http://1.1.1.1:8080") == "http://1.1.1.1:8080"
    with pytest.raises(BlockedURLError):
        validate_proxy("gopher://proxy/")
    with pytest.raises(BlockedURLError):
        validate_proxy("http://")


@pytest.mark.parametrize(
    "proxy",
    [
        "http://127.0.0.1:8080",
        "socks5://localhost:9050",
        "http://169.254.169.254:80",
        "http://10.0.0.5:3128",
    ],
)
def test_validate_proxy_blocks_private_and_metadata_hosts(proxy):
    with pytest.raises(BlockedURLError, match="private/reserved"):
        validate_proxy(proxy)
