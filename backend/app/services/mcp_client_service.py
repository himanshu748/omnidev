"""
MCP marketplace: run curated MCP servers locally and let the local model
call their tools from chat.

Safety model:
- Only catalog entries can be installed — no arbitrary commands from the API.
- Params are validated per type; path params must resolve inside $HOME.
- Server processes get a minimal environment (PATH/HOME only) so backend
  secrets (AWS keys, API keys) are never leaked to third-party servers.
- Tool calling is opt-in per request (`use_tools`), every call is surfaced
  to the UI as an event, and results are truncated before re-entering the
  model context.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import shutil
from contextlib import AsyncExitStack
from pathlib import Path
from typing import Any, AsyncIterator

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.config import settings
from app.services.ai_service import ollama_chat_round

TOOL_TIMEOUT_SECONDS = 60
TOOL_RESULT_MAX_CHARS = 8_000
MAX_TOOL_ROUNDS = 5
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,31}$")
STRING_PARAM_RE = re.compile(r"^[A-Za-z0-9._/:@= -]{1,200}$")


class MCPError(ValueError):
    """User-facing MCP configuration or runtime problem."""


# ── Curated catalog ─────────────────────────────────────────
# argv templates only — the API can never supply a raw command line.
CATALOG: list[dict[str, Any]] = [
    {
        "id": "filesystem",
        "name": "Filesystem",
        "description": "Read and edit files inside ONE directory you choose. The model can create and modify files there.",
        "capabilities": "read + write (scoped to the chosen directory)",
        "runtime": "npx",
        "argv": ["npx", "-y", "@modelcontextprotocol/server-filesystem", "{directory}"],
        "params": [
            {"name": "directory", "type": "path", "description": "The only directory the server may touch."}
        ],
    },
    {
        "id": "fetch",
        "name": "Fetch",
        "description": "Fetch a web page as markdown for the model to read.",
        "capabilities": "read-only (network)",
        "runtime": "uvx",
        "argv": ["uvx", "mcp-server-fetch"],
        "params": [],
    },
    {
        "id": "memory",
        "name": "Memory",
        "description": "A local knowledge-graph memory the model can read and write across chats.",
        "capabilities": "read + write (local file)",
        "runtime": "npx",
        "argv": ["npx", "-y", "@modelcontextprotocol/server-memory"],
        "params": [],
    },
    {
        "id": "time",
        "name": "Time",
        "description": "Current time and timezone conversions.",
        "capabilities": "read-only",
        "runtime": "uvx",
        "argv": ["uvx", "mcp-server-time"],
        "params": [],
    },
    {
        "id": "git",
        "name": "Git",
        "description": "Inspect and stage changes in ONE local git repository you choose.",
        "capabilities": "read + write (scoped to the chosen repository)",
        "runtime": "uvx",
        "argv": ["uvx", "mcp-server-git", "--repository", "{repository}"],
        "params": [
            {"name": "repository", "type": "path", "description": "Path to the git repository."}
        ],
    },
    {
        "id": "sequential-thinking",
        "name": "Sequential Thinking",
        "description": "A scratchpad tool that helps the model reason step by step.",
        "capabilities": "read-only (no side effects)",
        "runtime": "npx",
        "argv": ["npx", "-y", "@modelcontextprotocol/server-sequential-thinking"],
        "params": [],
    },
]

_CATALOG_BY_ID = {entry["id"]: entry for entry in CATALOG}


def catalog() -> list[dict[str, Any]]:
    available = []
    for entry in CATALOG:
        runtime_ok = shutil.which(entry["runtime"]) is not None
        available.append({**entry, "runtime_available": runtime_ok})
    return available


# ── Config store (JSON in DATA_DIR) ─────────────────────────
def _config_path() -> Path:
    root = Path(settings.data_dir).expanduser()
    root.mkdir(parents=True, exist_ok=True)
    return root / "mcp_servers.json"


def list_servers() -> list[dict[str, Any]]:
    path = _config_path()
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return []
    return data if isinstance(data, list) else []


def _save_servers(servers: list[dict[str, Any]]) -> None:
    _config_path().write_text(json.dumps(servers, indent=2))


def _validate_params(entry: dict[str, Any], params: dict[str, str]) -> dict[str, str]:
    validated: dict[str, str] = {}
    for spec in entry["params"]:
        raw = (params.get(spec["name"]) or "").strip()
        if not raw:
            raise MCPError(f"Missing required parameter '{spec['name']}'.")
        if spec["type"] == "path":
            resolved = Path(raw).expanduser().resolve()
            home = Path.home().resolve()
            if not resolved.is_dir():
                raise MCPError(f"'{resolved}' is not an existing directory.")
            if resolved == home or home not in resolved.parents:
                raise MCPError(
                    f"Path parameters must be a directory inside your home folder (got '{resolved}')."
                )
            validated[spec["name"]] = str(resolved)
        else:
            if raw.startswith("-") or not STRING_PARAM_RE.match(raw):
                raise MCPError(f"Invalid value for parameter '{spec['name']}'.")
            validated[spec["name"]] = raw
    return validated


def add_server(catalog_id: str, params: dict[str, str], name: str | None = None) -> dict[str, Any]:
    entry = _CATALOG_BY_ID.get(catalog_id)
    if entry is None:
        raise MCPError(f"Unknown catalog entry '{catalog_id}'. Custom commands are not supported.")
    if shutil.which(entry["runtime"]) is None:
        raise MCPError(
            f"'{entry['runtime']}' is not installed. Install it first (Node for npx, uv for uvx)."
        )
    server_name = (name or catalog_id).strip().lower()
    if not NAME_RE.match(server_name):
        raise MCPError("Server name must be 1-32 chars of lowercase letters, digits, or dashes.")

    servers = list_servers()
    if any(s["name"] == server_name for s in servers):
        raise MCPError(f"A server named '{server_name}' already exists.")

    record = {
        "name": server_name,
        "catalog_id": catalog_id,
        "params": _validate_params(entry, params),
        "enabled": True,
    }
    servers.append(record)
    _save_servers(servers)
    return record


def remove_server(name: str) -> bool:
    servers = list_servers()
    remaining = [s for s in servers if s["name"] != name]
    if len(remaining) == len(servers):
        return False
    _save_servers(remaining)
    return True


def set_enabled(name: str, enabled: bool) -> bool:
    servers = list_servers()
    for server in servers:
        if server["name"] == name:
            server["enabled"] = enabled
            _save_servers(servers)
            return True
    return False


def _argv_for(record: dict[str, Any]) -> list[str]:
    entry = _CATALOG_BY_ID.get(record["catalog_id"])
    if entry is None:
        raise MCPError(f"Server '{record['name']}' references an unknown catalog entry.")
    params = _validate_params(entry, record.get("params") or {})
    return [part.format(**params) if "{" in part else part for part in entry["argv"]]


# ── Runtime manager ─────────────────────────────────────────
class MCPManager:
    """Lazily-started stdio sessions for enabled servers."""

    def __init__(self) -> None:
        self._sessions: dict[str, ClientSession] = {}
        self._stack = AsyncExitStack()
        self._lock = asyncio.Lock()

    async def _session(self, record: dict[str, Any]) -> ClientSession:
        name = record["name"]
        if name in self._sessions:
            return self._sessions[name]

        argv = _argv_for(record)
        executable = shutil.which(argv[0])
        if executable is None:
            raise MCPError(f"'{argv[0]}' is not installed.")

        # Minimal environment: never leak backend secrets to MCP servers.
        env = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": os.environ.get("HOME", str(Path.home())),
        }
        params = StdioServerParameters(command=executable, args=argv[1:], env=env)
        read, write = await self._stack.enter_async_context(stdio_client(params))
        session = await self._stack.enter_async_context(ClientSession(read, write))
        await asyncio.wait_for(session.initialize(), timeout=45)
        self._sessions[name] = session
        return session

    async def list_tools(self, record: dict[str, Any]) -> list[dict[str, Any]]:
        async with self._lock:
            session = await self._session(record)
        result = await asyncio.wait_for(session.list_tools(), timeout=30)
        return [
            {
                "name": tool.name,
                "description": tool.description or "",
                "input_schema": tool.inputSchema or {"type": "object", "properties": {}},
            }
            for tool in result.tools
        ]

    async def call_tool(self, record: dict[str, Any], tool: str, arguments: dict[str, Any]) -> str:
        async with self._lock:
            session = await self._session(record)
        result = await asyncio.wait_for(
            session.call_tool(tool, arguments), timeout=TOOL_TIMEOUT_SECONDS
        )
        parts: list[str] = []
        for item in result.content:
            text = getattr(item, "text", None)
            if text:
                parts.append(text)
        text = "\n".join(parts) or "(no text content)"
        if len(text) > TOOL_RESULT_MAX_CHARS:
            text = text[:TOOL_RESULT_MAX_CHARS] + "\n…(truncated)"
        if getattr(result, "isError", False):
            return f"Tool error: {text}"
        return text

    async def shutdown(self) -> None:
        self._sessions.clear()
        try:
            await self._stack.aclose()
        except Exception:
            pass
        self._stack = AsyncExitStack()


_manager: MCPManager | None = None


def get_manager() -> MCPManager:
    global _manager
    if _manager is None:
        _manager = MCPManager()
    return _manager


async def shutdown_manager() -> None:
    global _manager
    if _manager is not None:
        await _manager.shutdown()
        _manager = None


# ── Tool-calling chat loop ──────────────────────────────────
def _namespaced(server: str, tool: str) -> str:
    return f"{server}__{tool}"


async def gather_ollama_tools() -> tuple[list[dict[str, Any]], dict[str, tuple[dict, str]]]:
    """Tools from all enabled servers in Ollama format, plus a dispatch map."""
    manager = get_manager()
    ollama_tools: list[dict[str, Any]] = []
    dispatch: dict[str, tuple[dict, str]] = {}
    for record in list_servers():
        if not record.get("enabled", True):
            continue
        try:
            tools = await manager.list_tools(record)
        except Exception as exc:
            raise MCPError(f"MCP server '{record['name']}' failed to start: {exc}") from exc
        for tool in tools:
            full = _namespaced(record["name"], tool["name"])
            dispatch[full] = (record, tool["name"])
            ollama_tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": full,
                        "description": f"[{record['name']}] {tool['description']}"[:1000],
                        "parameters": tool["input_schema"],
                    },
                }
            )
    return ollama_tools, dispatch


async def run_tool_chat(
    messages: list[dict[str, Any]],
    *,
    temperature: float | None = None,
) -> AsyncIterator[dict[str, Any]]:
    """
    Chat with MCP tools available. Yields NDJSON-ready events:
    {"tool_call": {...}} · {"tool_result": {...}} · {"delta": str}.

    Bounded at MAX_TOOL_ROUNDS tool rounds; the final answer arrives as one
    delta (tool rounds are non-streaming on the Ollama API).
    """
    tools, dispatch = await gather_ollama_tools()
    if not tools:
        raise MCPError("No MCP tools available. Add and enable a server in the MCP marketplace.")

    manager = get_manager()
    convo = list(messages)
    for _ in range(MAX_TOOL_ROUNDS):
        reply = await ollama_chat_round(convo, tools=tools, temperature=temperature)
        tool_calls = reply.get("tool_calls") or []
        if not tool_calls:
            yield {"delta": reply.get("content", "") or ""}
            return

        convo.append(
            {"role": "assistant", "content": reply.get("content", "") or "", "tool_calls": tool_calls}
        )
        for call in tool_calls:
            function = call.get("function") or {}
            full_name = function.get("name", "")
            arguments = function.get("arguments") or {}
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except json.JSONDecodeError:
                    arguments = {}

            yield {"tool_call": {"tool": full_name, "arguments": arguments}}

            if full_name not in dispatch:
                result_text = f"Unknown tool '{full_name}'."
            else:
                record, tool_name = dispatch[full_name]
                try:
                    result_text = await manager.call_tool(record, tool_name, arguments)
                except Exception as exc:
                    result_text = f"Tool call failed: {exc}"

            yield {"tool_result": {"tool": full_name, "result": result_text[:2000]}}
            convo.append({"role": "tool", "content": result_text, "tool_name": full_name})

    yield {"delta": "(Stopped after the maximum number of tool rounds.)"}
