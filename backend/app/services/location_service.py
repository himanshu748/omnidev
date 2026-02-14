"""
Location Services.
- IP geolocation via ipinfo (with httpx fallback)
- Reverse geocoding via Nominatim (free, no API key)
- Public IP detection via ipify
"""

from __future__ import annotations

from typing import Any

import httpx
import ipinfo  # type: ignore[import-untyped]

from app.config import settings

NOMINATIM_REVERSE_URL = "https://nominatim.openstreetmap.org/reverse"
NOMINATIM_SEARCH_URL = "https://nominatim.openstreetmap.org/search"
PUBLIC_IP_URL = "https://api.ipify.org?format=json"
IPINFO_API_URL = "https://ipinfo.io"


# ── IP geolocation ──────────────────────────────────────────
async def ip_lookup(ip: str | None = None) -> dict[str, Any]:
    """
    Look up location data for an IP address.
    If ip is None, uses the caller's public IP.

    Tries ipinfo library first (with increased timeout), falls back to
    direct httpx call to the ipinfo REST API.
    """
    try:
        return await _ip_lookup_via_library(ip)
    except Exception:
        return await _ip_lookup_via_httpx(ip)


async def _ip_lookup_via_library(ip: str | None) -> dict[str, Any]:
    handler = ipinfo.getHandlerAsync(
        settings.ipinfo_token or None,
        request_options={"timeout": 10},
    )
    try:
        details = await handler.getDetails(ip, timeout=10)
        return _parse_ipinfo(details.all, ip)
    finally:
        await handler.deinit()


async def _ip_lookup_via_httpx(ip: str | None) -> dict[str, Any]:
    """Fallback: call ipinfo.io REST API directly with httpx."""
    url = f"{IPINFO_API_URL}/{ip}/json" if ip else f"{IPINFO_API_URL}/json"
    headers = {"Accept": "application/json"}
    if settings.ipinfo_token:
        headers["Authorization"] = f"Bearer {settings.ipinfo_token}"

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()

    return _parse_ipinfo(data, ip)


def _parse_ipinfo(data: dict[str, Any], ip: str | None = None) -> dict[str, Any]:
    lat, lng = None, None
    loc = data.get("loc", "")
    if loc and "," in loc:
        parts = loc.split(",")
        lat, lng = float(parts[0]), float(parts[1])

    return {
        "ip": data.get("ip", ip or ""),
        "city": data.get("city", ""),
        "region": data.get("region", ""),
        "country": data.get("country", ""),
        "postal": data.get("postal", ""),
        "latitude": lat,
        "longitude": lng,
        "timezone": data.get("timezone", ""),
        "org": data.get("org", ""),
    }


# ── Reverse geocoding (Nominatim) ───────────────────────────
async def reverse_geocode(lat: float, lng: float) -> dict[str, Any]:
    """Convert latitude/longitude to a human-readable address."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            NOMINATIM_REVERSE_URL,
            params={
                "lat": lat,
                "lon": lng,
                "format": "json",
                "addressdetails": 1,
            },
            headers={"User-Agent": "OmniDev/1.0"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

    return {
        "latitude": lat,
        "longitude": lng,
        "display_name": data.get("display_name", ""),
        "address": data.get("address", {}),
    }


# ── Forward geocoding (Nominatim search) ────────────────────
def _parse_nominatim_search_response(data: Any) -> list[dict[str, Any]]:
    """Parse Nominatim search JSON into our result shape."""
    results = []
    for item in (data if isinstance(data, list) else []):
        try:
            lat = float(item["lat"])
            lon = float(item["lon"])
        except (KeyError, TypeError, ValueError):
            continue
        results.append({
            "display_name": item.get("display_name", ""),
            "latitude": lat,
            "longitude": lon,
            "type": item.get("type") or item.get("class", ""),
            "address": item.get("address") or {},
        })
    return results


async def geocode(
    query: str,
    limit: int = 5,
    countrycodes: str | None = None,
    fallback_if_empty: bool = True,
) -> list[dict[str, Any]]:
    """Convert an address or place name to latitude/longitude via Nominatim."""
    if not query or not query.strip():
        return []
    q = query.strip()
    limit = min(max(1, limit), 10)
    params_base: dict[str, Any] = {
        "format": "json",
        "addressdetails": 1,
        "limit": limit,
    }
    if countrycodes:
        params_base["countrycodes"] = countrycodes

    async with httpx.AsyncClient() as client:
        params = {**params_base, "q": q}
        resp = await client.get(
            NOMINATIM_SEARCH_URL,
            params=params,
            headers={"User-Agent": "OmniDev/1.0 (https://github.com/omnidev)"},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

    results = _parse_nominatim_search_response(data)

    # If no results and query has a comma, try the last part (e.g. "..., Lucknow" -> "Lucknow")
    if fallback_if_empty and not results and "," in q:
        fallback_q = q.split(",")[-1].strip()
        if fallback_q and fallback_q != q:
            async with httpx.AsyncClient() as client:
                params = {**params_base, "q": fallback_q}
                resp2 = await client.get(
                    NOMINATIM_SEARCH_URL,
                    params=params,
                    headers={"User-Agent": "OmniDev/1.0 (https://github.com/omnidev)"},
                    timeout=15,
                )
                resp2.raise_for_status()
                data2 = resp2.json()
            results = _parse_nominatim_search_response(data2)
    return results


# ── My public IP + location ────────────────────────────────
async def my_location() -> dict[str, Any]:
    """Detect the server's public IP and resolve its location."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(PUBLIC_IP_URL, timeout=10)
        resp.raise_for_status()
        public_ip = resp.json()["ip"]

    loc = await ip_lookup(public_ip)
    return {
        "ip": public_ip,
        "city": loc.get("city", ""),
        "region": loc.get("region", ""),
        "country": loc.get("country", ""),
        "latitude": loc.get("latitude"),
        "longitude": loc.get("longitude"),
    }
