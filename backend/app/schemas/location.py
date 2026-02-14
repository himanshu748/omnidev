"""Schemas for the Location Services module."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class IPLocationResponse(BaseModel):
    ip: str
    city: str = ""
    region: str = ""
    country: str = ""
    postal: str = ""
    latitude: float | None = None
    longitude: float | None = None
    timezone: str = ""
    org: str = ""


class ReverseGeocodeResponse(BaseModel):
    latitude: float
    longitude: float
    display_name: str = ""
    address: dict[str, str] = Field(default_factory=dict)


class MyLocationResponse(BaseModel):
    ip: str
    city: str = ""
    region: str = ""
    country: str = ""
    latitude: float | None = None
    longitude: float | None = None


class GeocodeResultItem(BaseModel):
    display_name: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    type: str = ""
    address: dict[str, str] = Field(default_factory=dict)


class GeocodeResponse(BaseModel):
    results: list[GeocodeResultItem]
