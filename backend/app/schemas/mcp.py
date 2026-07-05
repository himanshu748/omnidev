"""Schemas for the MCP marketplace."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CatalogParam(BaseModel):
    name: str
    type: str
    description: str = ""


class CatalogEntry(BaseModel):
    id: str
    name: str
    description: str = ""
    capabilities: str = ""
    runtime: str = ""
    runtime_available: bool = True
    params: list[CatalogParam] = []


class CatalogResponse(BaseModel):
    entries: list[CatalogEntry]


class AddServerRequest(BaseModel):
    catalog_id: str = Field(..., min_length=1, max_length=40)
    name: str | None = Field(default=None, max_length=32)
    params: dict[str, str] = {}


class ServerRecord(BaseModel):
    name: str
    catalog_id: str
    params: dict[str, str] = {}
    enabled: bool = True


class ServerListResponse(BaseModel):
    servers: list[ServerRecord]


class SetEnabledRequest(BaseModel):
    enabled: bool


class ToolInfo(BaseModel):
    name: str
    description: str = ""
    input_schema: dict[str, Any] = {}


class ToolListResponse(BaseModel):
    server: str
    tools: list[ToolInfo]
