"""Location Services router — IP geolocation & reverse geocoding."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.schemas.location import (
    GeocodeResponse,
    GeocodeResultItem,
    IPLocationResponse,
    MyLocationResponse,
    ReverseGeocodeResponse,
)
from app.services import location_service

router = APIRouter()


@router.get("/ip", response_model=IPLocationResponse)
async def get_ip_location(ip: str = Query(None, description="IP to look up (omit for your own)")):
    """Look up geolocation data for an IP address."""
    try:
        result = await location_service.ip_lookup(ip)
        return IPLocationResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/reverse", response_model=ReverseGeocodeResponse)
async def get_reverse_geocode(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
):
    """Convert latitude/longitude to a human-readable address via Nominatim."""
    try:
        result = await location_service.reverse_geocode(lat, lng)
        return ReverseGeocodeResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/geocode", response_model=GeocodeResponse)
async def get_geocode(
    q: str = Query(..., min_length=1, description="Address or place name"),
    limit: int = Query(5, ge=1, le=10, description="Max number of results"),
    countrycodes: str | None = Query(
        None,
        description="Restrict to countries (ISO 3166-1 alpha-2, e.g. in for India)",
    ),
):
    """Convert an address or place name to latitude/longitude (Nominatim)."""
    try:
        results = await location_service.geocode(q, limit=limit, countrycodes=countrycodes)
        return GeocodeResponse(
            results=[GeocodeResultItem(**r) for r in results]
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/me", response_model=MyLocationResponse)
async def get_my_location():
    """Detect the server's public IP and resolve its location."""
    try:
        result = await location_service.my_location()
        return MyLocationResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
