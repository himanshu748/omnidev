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
from urllib.parse import urlparse

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


def validate_proxy(proxy: str | None) -> str | None:
    """Validate a user-supplied proxy URL. Returns it unchanged, or raises."""
    if not proxy:
        return proxy
    parsed = urlparse(proxy)
    if parsed.scheme.lower() not in {"http", "https", "socks5"}:
        raise BlockedURLError(f"Unsupported proxy scheme {parsed.scheme!r}.")
    if not parsed.hostname:
        raise BlockedURLError("Proxy has no host.")
    return proxy
