"""
SSRF protection for user-supplied URLs.

The scraper service fetches arbitrary URLs on behalf of the user
(or, dangerously, on behalf of a prompt-injected page). Without validation a
request could reach the cloud metadata endpoint (169.254.169.254), localhost
services, or a private LAN host. This guard rejects any URL that resolves to a
loopback / link-local / private / reserved address before the browser navigates.
"""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urljoin, urlparse

import httpx

# Hostnames that must never be fetched, regardless of DNS.
_BLOCKED_HOSTS = {
    "localhost",
    "metadata.google.internal",
    "metadata",
}

# Cloud metadata IPs and other addresses that are dangerous even though some
# are technically "public" (link-local).
_BLOCKED_EXACT_IPS = {
    "169.254.169.254",  # AWS / GCP / Azure IMDS
    "100.100.100.200",  # Alibaba Cloud metadata
}


class BlockedURLError(ValueError):
    """The URL is not allowed (bad scheme, private/reserved IP, or DNS failure)."""


def is_blocked_host(host: str | None) -> bool:
    """
    True if a host (literal IP or name) must not be fetched.

    Unlike validate_public_url this takes a bare host, resolves it, and returns
    a bool — used to re-check every redirect hop and navigation at request time,
    where only the host is available. A name that resolves to ANY private /
    reserved address (or fails to resolve) is treated as blocked.
    """
    if not host:
        return True
    host = host.strip().rstrip(".")
    if host.lower() in _BLOCKED_HOSTS:
        return True
    try:
        ipaddress.ip_address(host)
        return _ip_is_blocked(host)
    except ValueError:
        pass  # not a literal IP — resolve it
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return True
    resolved = {info[4][0] for info in infos}
    return not resolved or any(_ip_is_blocked(ip) for ip in resolved)


def _ip_is_blocked(ip: str) -> bool:
    if ip in _BLOCKED_EXACT_IPS:
        return True
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return True
    return (
        addr.is_private
        or addr.is_loopback
        or addr.is_link_local
        or addr.is_reserved
        or addr.is_multicast
        or addr.is_unspecified
    )


def validate_public_url(url: str, *, allow_schemes: tuple[str, ...] = ("http", "https")) -> str:
    """
    Return the URL if it is safe to fetch, else raise BlockedURLError.

    Enforces: an allowed scheme, a resolvable hostname, and that EVERY resolved
    address is a routable public address (blocks loopback / private / link-local /
    reserved, plus known metadata endpoints and `localhost`).
    """
    if not isinstance(url, str) or not url.strip():
        raise BlockedURLError("A URL is required.")
    url = url.strip()

    parsed = urlparse(url)
    if parsed.scheme.lower() not in allow_schemes:
        raise BlockedURLError(
            f"URL scheme {parsed.scheme!r} is not allowed. Use {' or '.join(allow_schemes)}."
        )
    host = parsed.hostname
    if not host:
        raise BlockedURLError("URL has no host.")

    if host.lower() in _BLOCKED_HOSTS:
        raise BlockedURLError(f"Refusing to fetch a local/metadata host: {host}")

    # If the host is a literal IP, check it directly.
    try:
        ipaddress.ip_address(host)
        if _ip_is_blocked(host):
            raise BlockedURLError(f"Refusing to fetch a private/reserved address: {host}")
        return url
    except ValueError:
        pass  # not a literal IP — resolve it

    # Resolve the hostname and reject if ANY resolved address is non-public
    # (defends against DNS records that point at internal ranges).
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror as exc:
        raise BlockedURLError(f"Could not resolve host {host!r}.") from exc

    resolved = {info[4][0] for info in infos}
    if not resolved:
        raise BlockedURLError(f"Could not resolve host {host!r}.")
    for ip in resolved:
        if _ip_is_blocked(ip):
            raise BlockedURLError(
                f"Refusing to fetch {host!r}: it resolves to a private/reserved address ({ip})."
            )
    return url


async def resolve_safe_url(url: str, *, max_redirects: int = 10) -> str:
    """
    Follow the redirect chain ourselves, validating every hop, and return the
    final URL — safe to hand to the browser.

    Chromium follows HTTP redirects internally without re-invoking Playwright's
    route interception, so an open redirect from a public entry to an internal
    host (169.254.169.254, 127.0.0.1, LAN) would otherwise bypass the guard.
    Resolving the chain here means the browser only ever navigates to a
    fully-validated final URL. Transport errors fall back to the (validated)
    entry URL so a pre-flight hiccup doesn't break normal scraping.
    """
    validate_public_url(url)
    current = url
    try:
        async with httpx.AsyncClient(follow_redirects=False, timeout=10.0) as client:
            for _ in range(max_redirects):
                if is_blocked_host(urlparse(current).hostname):
                    raise BlockedURLError(
                        f"Refusing a redirect to a private/reserved host: {urlparse(current).hostname}"
                    )
                async with client.stream("GET", current) as resp:
                    if resp.status_code in (301, 302, 303, 307, 308) and "location" in resp.headers:
                        current = urljoin(current, resp.headers["location"])
                        continue
                    if is_blocked_host(urlparse(current).hostname):
                        raise BlockedURLError(
                            f"Refusing a redirect to a private/reserved host: {urlparse(current).hostname}"
                        )
                    return current
        raise BlockedURLError("Too many redirects.")
    except httpx.HTTPError:
        # Could not pre-flight (DNS/connect/timeout). The entry URL was already
        # validated; let the browser proceed (its per-request guard still fires
        # on any direct sub-request to an internal host).
        return url


def validate_proxy(proxy: str | None) -> str | None:
    """Validate a user-supplied proxy URL. Returns it unchanged, or raises."""
    if not proxy:
        return proxy
    parsed = urlparse(proxy)
    if parsed.scheme.lower() not in {"http", "https", "socks5", "gopher"}:
        raise BlockedURLError(f"Unsupported proxy scheme {parsed.scheme!r}.")
    if not parsed.hostname:
        raise BlockedURLError("Proxy has no host.")
    return proxy
