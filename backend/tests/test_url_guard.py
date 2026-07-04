"""Tests for the SSRF URL guard used by the scraper and preview services."""

import pytest

from app.services import url_guard
from app.services.url_guard import BlockedURLError, validate_proxy, validate_public_url


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


def test_proxy_validation():
    assert validate_proxy(None) is None
    assert validate_proxy("http://proxy.example.com:8080") == "http://proxy.example.com:8080"
    with pytest.raises(BlockedURLError):
        validate_proxy("gopher://proxy/")
    with pytest.raises(BlockedURLError):
        validate_proxy("http://")
