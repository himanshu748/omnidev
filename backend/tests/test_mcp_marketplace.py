"""Tests for the MCP marketplace: catalog, config safety, runtime, tool chat."""

import json
import pathlib
import sys

import pytest
import pytest_asyncio

from app.services import mcp_client_service as mcp
from app.services.mcp_client_service import MCPError

BACKEND_DIR = pathlib.Path(__file__).resolve().parents[1]


@pytest_asyncio.fixture(autouse=True)
async def _fresh_manager():
    yield
    await mcp.shutdown_manager()


# ── catalog & config safety ─────────────────────────────────
def test_catalog_is_curated_only():
    entries = mcp.catalog()
    assert {e["id"] for e in entries} >= {"filesystem", "fetch", "memory", "time"}
    for entry in entries:
        assert entry["argv"][0] in {"npx", "uvx"}, "catalog runtimes are npx/uvx only"


def test_add_server_rejects_unknown_catalog_id():
    with pytest.raises(MCPError, match="Unknown catalog entry"):
        mcp.add_server("evil; rm -rf /", {})


def test_add_server_rejects_path_outside_home(tmp_path, monkeypatch):
    monkeypatch.setattr(mcp.shutil, "which", lambda _: "/usr/bin/true")
    with pytest.raises(MCPError, match="inside your home folder"):
        mcp.add_server("filesystem", {"directory": "/etc"})
    with pytest.raises(MCPError, match="not an existing directory"):
        mcp.add_server("filesystem", {"directory": str(tmp_path / "missing")})


def test_add_server_rejects_bad_names(monkeypatch):
    monkeypatch.setattr(mcp.shutil, "which", lambda _: "/usr/bin/true")
    with pytest.raises(MCPError, match="Server name"):
        mcp.add_server("memory", {}, name="Bad Name!")


def test_add_list_toggle_remove_server(monkeypatch):
    monkeypatch.setattr(mcp.shutil, "which", lambda _: "/usr/bin/true")
    record = mcp.add_server("memory", {}, name="mem1")
    assert record["enabled"] is True
    assert any(s["name"] == "mem1" for s in mcp.list_servers())

    with pytest.raises(MCPError, match="already exists"):
        mcp.add_server("memory", {}, name="mem1")

    assert mcp.set_enabled("mem1", False)
    assert mcp.list_servers()[0]["enabled"] is False
    assert mcp.remove_server("mem1")
    assert mcp.list_servers() == []


# ── runtime: real stdio round-trip against a fake server ────
def _install_fake_catalog(monkeypatch):
    fake_entry = {
        "id": "fake",
        "name": "Fake",
        "description": "test server",
        "capabilities": "read-only",
        "runtime": sys.executable,
        "argv": [sys.executable, str(BACKEND_DIR / "tests" / "fake_mcp_server.py")],
        "params": [],
    }
    monkeypatch.setitem(mcp._CATALOG_BY_ID, "fake", fake_entry)


@pytest.mark.asyncio
async def test_manager_lists_and_calls_tools(monkeypatch):
    _install_fake_catalog(monkeypatch)
    record = {"name": "fake", "catalog_id": "fake", "params": {}, "enabled": True}

    manager = mcp.get_manager()
    tools = await manager.list_tools(record)
    assert [t["name"] for t in tools] == ["echo"]

    result = await manager.call_tool(record, "echo", {"text": "hello"})
    assert result == "echo: hello"


@pytest.mark.asyncio
async def test_child_env_has_no_secrets(monkeypatch):
    _install_fake_catalog(monkeypatch)
    captured = {}
    real_params = mcp.StdioServerParameters

    def spy(**kwargs):
        captured.update(kwargs)
        return real_params(**kwargs)

    monkeypatch.setattr(mcp, "StdioServerParameters", spy)
    record = {"name": "fake", "catalog_id": "fake", "params": {}, "enabled": True}
    await mcp.get_manager().list_tools(record)
    assert set(captured["env"].keys()) <= {"PATH", "HOME"}


# ── tool-calling chat loop ──────────────────────────────────
@pytest.mark.asyncio
async def test_run_tool_chat_executes_and_answers(monkeypatch):
    _install_fake_catalog(monkeypatch)
    monkeypatch.setattr(
        mcp, "list_servers",
        lambda: [{"name": "fake", "catalog_id": "fake", "params": {}, "enabled": True}],
    )

    rounds = [
        {
            "content": "",
            "tool_calls": [{"function": {"name": "fake__echo", "arguments": {"text": "ping"}}}],
        },
        {"content": "The tool said: echo: ping"},
    ]
    calls = iter(rounds)

    async def fake_round(messages, *, tools, temperature=None, max_tokens=2048):
        return next(calls)

    monkeypatch.setattr(mcp, "ollama_chat_round", fake_round)

    events = [e async for e in mcp.run_tool_chat([{"role": "user", "content": "use echo"}])]
    kinds = [next(iter(e)) for e in events]
    assert kinds == ["tool_call", "tool_result", "delta"]
    assert events[1]["tool_result"]["result"] == "echo: ping"
    assert events[2]["delta"] == "The tool said: echo: ping"


@pytest.mark.asyncio
async def test_run_tool_chat_requires_servers(monkeypatch):
    monkeypatch.setattr(mcp, "list_servers", lambda: [])
    with pytest.raises(MCPError, match="No MCP tools available"):
        async for _ in mcp.run_tool_chat([{"role": "user", "content": "hi"}]):
            pass


# ── endpoints ───────────────────────────────────────────────
@pytest.mark.asyncio
async def test_catalog_endpoint(client, coverage_tracker):
    resp = await client.get("/api/mcp/catalog")
    assert resp.status_code == 200
    ids = {e["id"] for e in resp.json()["entries"]}
    assert "filesystem" in ids
    coverage_tracker("GET /api/mcp/catalog")


@pytest.mark.asyncio
async def test_server_endpoints(client, monkeypatch, coverage_tracker):
    monkeypatch.setattr(mcp.shutil, "which", lambda _: "/usr/bin/true")

    added = await client.post("/api/mcp/servers", json={"catalog_id": "memory"})
    assert added.status_code == 200
    coverage_tracker("POST /api/mcp/servers")

    listed = await client.get("/api/mcp/servers")
    assert listed.status_code == 200
    assert listed.json()["servers"][0]["name"] == "memory"
    coverage_tracker("GET /api/mcp/servers")

    toggled = await client.patch("/api/mcp/servers/memory", json={"enabled": False})
    assert toggled.status_code == 200
    assert toggled.json()["servers"][0]["enabled"] is False

    removed = await client.delete("/api/mcp/servers/memory")
    assert removed.status_code == 200
    assert (await client.delete("/api/mcp/servers/memory")).status_code == 404


@pytest.mark.asyncio
async def test_add_server_endpoint_rejects_arbitrary_commands(client):
    resp = await client.post(
        "/api/mcp/servers", json={"catalog_id": "custom", "params": {"cmd": "rm -rf /"}}
    )
    assert resp.status_code == 400
    assert "Unknown catalog entry" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_chat_stream_with_tools_emits_events(client, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "ai_provider", "ollama")

    async def fake_tool_chat(messages, temperature=None):
        yield {"tool_call": {"tool": "fake__echo", "arguments": {"text": "hi"}}}
        yield {"tool_result": {"tool": "fake__echo", "result": "echo: hi"}}
        yield {"delta": "done via tools"}

    import app.services.mcp_client_service as mcp_service

    monkeypatch.setattr(mcp_service, "run_tool_chat", fake_tool_chat)

    resp = await client.post(
        "/api/chat/stream", json={"message": "use tools", "use_tools": True}
    )
    assert resp.status_code == 200
    events = [json.loads(l) for l in resp.text.splitlines() if l.strip()]
    assert "session_id" in events[0]
    kinds = [next(iter(e)) for e in events[1:]]
    assert kinds == ["tool_call", "tool_result", "delta", "done"]
