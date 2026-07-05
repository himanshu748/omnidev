"""MCP marketplace router — curated servers the local model can use as tools."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.mcp import (
    AddServerRequest,
    CatalogEntry,
    CatalogResponse,
    ServerListResponse,
    ServerRecord,
    SetEnabledRequest,
    ToolInfo,
    ToolListResponse,
)
from app.services import mcp_client_service as mcp
from app.routers.errors import internal_error

router = APIRouter()


@router.get("/catalog", response_model=CatalogResponse)
async def catalog():
    """The curated server catalog. Only these can be installed — the API
    never accepts arbitrary commands."""
    return CatalogResponse(entries=[CatalogEntry(**entry) for entry in mcp.catalog()])


@router.get("/servers", response_model=ServerListResponse)
async def servers():
    """Configured servers."""
    return ServerListResponse(servers=[ServerRecord(**s) for s in mcp.list_servers()])


@router.post("/servers", response_model=ServerRecord)
async def add_server(body: AddServerRequest):
    """Install a server from the catalog. Path params must be directories
    inside your home folder."""
    try:
        return ServerRecord(**mcp.add_server(body.catalog_id, body.params, body.name))
    except mcp.MCPError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise internal_error("Adding the MCP server failed.") from exc


@router.delete("/servers/{name}")
async def remove_server(name: str):
    if not mcp.remove_server(name):
        raise HTTPException(status_code=404, detail=f"No server named '{name}'.")
    await mcp.shutdown_manager()  # drop any running session for it
    return {"deleted": name}


@router.patch("/servers/{name}", response_model=ServerListResponse)
async def set_enabled(name: str, body: SetEnabledRequest):
    if not mcp.set_enabled(name, body.enabled):
        raise HTTPException(status_code=404, detail=f"No server named '{name}'.")
    return ServerListResponse(servers=[ServerRecord(**s) for s in mcp.list_servers()])


@router.get("/servers/{name}/tools", response_model=ToolListResponse)
async def server_tools(name: str):
    """Start the server (if needed) and list its tools."""
    record = next((s for s in mcp.list_servers() if s["name"] == name), None)
    if record is None:
        raise HTTPException(status_code=404, detail=f"No server named '{name}'.")
    try:
        tools = await mcp.get_manager().list_tools(record)
    except mcp.MCPError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502, detail=f"MCP server '{name}' failed: {exc}"
        ) from exc
    return ToolListResponse(server=name, tools=[ToolInfo(**tool) for tool in tools])
