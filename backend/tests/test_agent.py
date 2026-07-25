"""Agent mode tests: workspaces, tool safety, the loop and the approval gate."""

from __future__ import annotations

import asyncio
import json

import pytest

from app.services import agent_service, agent_tools, workspace_service
from app.services.agent_tools import ToolError


@pytest.fixture
def fake_home(tmp_path, monkeypatch):
    """Workspaces must live inside $HOME, so point $HOME at tmp_path."""
    from pathlib import Path

    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    return tmp_path


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    """A trusted workspace directory with a couple of files."""
    root = tmp_path / "proj"
    root.mkdir()
    (root / "main.py").write_text("def greet():\n    return 'hello'\n")
    (root / "notes.md").write_text("# Notes\n\nAlpha\n")
    monkeypatch.setattr(workspace_service, "roots", lambda: [root])
    return root


def _scripted(rounds):
    """A fake model that returns each scripted round in order."""
    calls = list(rounds)
    state = {"i": 0}

    async def fake_round(messages, *, tools, system=None, temperature=None, max_tokens=2048):
        i = state["i"]
        state["i"] += 1
        if i < len(calls):
            return calls[i]
        return {"content": "Done.", "tool_calls": []}

    fake_round.state = state
    return fake_round


# ── Workspaces ──────────────────────────────────────────────
@pytest.mark.asyncio
async def test_workspace_crud(client, tmp_path, fake_home, coverage_tracker):
    coverage_tracker("GET /api/agent/workspaces")
    coverage_tracker("POST /api/agent/workspaces")
    coverage_tracker("DELETE /api/agent/workspaces")
    folder = tmp_path / "ws"
    folder.mkdir()

    resp = await client.post("/api/agent/workspaces", json={"path": str(folder)})
    assert resp.status_code == 201

    resp = await client.get("/api/agent/workspaces")
    paths = [w["path"] for w in resp.json()["workspaces"]]
    assert str(folder) in paths

    # The landing root shows up as an implicit workspace.
    assert any(w["implicit"] for w in resp.json()["workspaces"])

    resp = await client.delete("/api/agent/workspaces", params={"path": str(folder)})
    assert resp.status_code == 200
    resp = await client.delete("/api/agent/workspaces", params={"path": str(folder)})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_workspace_rejects_unsafe_paths(client, tmp_path, fake_home):
    from pathlib import Path

    for bad in ["relative/path", str(tmp_path / "missing"), str(Path.home())]:
        resp = await client.post("/api/agent/workspaces", json={"path": bad})
        assert resp.status_code == 400, bad


@pytest.mark.asyncio
async def test_duplicate_workspace_rejected(client, tmp_path, fake_home):
    folder = tmp_path / "ws"
    folder.mkdir()
    body = {"path": str(folder)}
    assert (await client.post("/api/agent/workspaces", json=body)).status_code == 201
    assert (await client.post("/api/agent/workspaces", json=body)).status_code == 400


def test_contains_resolves_symlinks(tmp_path, monkeypatch):
    root = tmp_path / "ws"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.txt").write_text("x")
    link = root / "escape"
    link.symlink_to(outside)
    monkeypatch.setattr(workspace_service, "roots", lambda: [root.resolve()])

    assert workspace_service.contains(root / "a.txt")
    assert not workspace_service.contains(link / "secret.txt")


# ── Tools ───────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_read_file_and_list_dir(workspace):
    text = await agent_tools.call_tool("read_file", {"path": str(workspace / "main.py")})
    assert "def greet" in text
    listing = await agent_tools.call_tool("list_dir", {"path": str(workspace)})
    assert "main.py" in listing and "notes.md" in listing


@pytest.mark.asyncio
async def test_read_missing_file_suggests_neighbour(workspace):
    with pytest.raises(ToolError) as exc:
        await agent_tools.call_tool("read_file", {"path": str(workspace / "man.py")})
    assert "main.py" in str(exc.value)


@pytest.mark.asyncio
async def test_relative_path_rejected(workspace):
    with pytest.raises(ToolError) as exc:
        await agent_tools.call_tool("read_file", {"path": "main.py"})
    assert "absolute" in str(exc.value).lower()


@pytest.mark.asyncio
async def test_edit_file_applies_and_reports(workspace):
    result = await agent_tools.call_tool(
        "edit_file",
        {
            "path": str(workspace / "main.py"),
            "old_text": "return 'hello'",
            "new_text": "return 'hi there'",
        },
    )
    assert "Edited" in result
    assert "hi there" in (workspace / "main.py").read_text()


@pytest.mark.asyncio
async def test_edit_file_miss_echoes_closest_region(workspace):
    """The retry hint is what lets a small model self-correct."""
    with pytest.raises(ToolError) as exc:
        await agent_tools.call_tool(
            "edit_file",
            {
                "path": str(workspace / "main.py"),
                "old_text": "return \"hello\"",  # wrong quote style
                "new_text": "return 'bye'",
            },
        )
    message = str(exc.value)
    assert "not found" in message
    assert "return 'hello'" in message  # the real text is handed back


@pytest.mark.asyncio
async def test_edit_file_ambiguous_match_refused(workspace):
    path = workspace / "dup.py"
    path.write_text("x = 1\nx = 1\n")
    with pytest.raises(ToolError) as exc:
        await agent_tools.call_tool(
            "edit_file", {"path": str(path), "old_text": "x = 1", "new_text": "x = 2"}
        )
    assert "2 times" in str(exc.value)


@pytest.mark.asyncio
async def test_write_file_creates_and_updates(workspace):
    target = workspace / "sub" / "new.txt"
    result = await agent_tools.call_tool(
        "write_file", {"path": str(target), "content": "one\ntwo\n"}
    )
    assert "Created" in result and target.read_text() == "one\ntwo\n"
    result = await agent_tools.call_tool(
        "write_file", {"path": str(target), "content": "three\n"}
    )
    assert "Updated" in result


@pytest.mark.asyncio
async def test_write_refuses_symlink(workspace, tmp_path):
    victim = tmp_path / "victim.txt"
    victim.write_text("original")
    link = workspace / "link.txt"
    link.symlink_to(victim)
    with pytest.raises(ToolError) as exc:
        await agent_tools.call_tool("write_file", {"path": str(link), "content": "pwned"})
    assert "symlink" in str(exc.value)
    assert victim.read_text() == "original"


@pytest.mark.asyncio
async def test_run_command_allowlist(workspace):
    with pytest.raises(ToolError) as exc:
        await agent_tools.call_tool(
            "run_command", {"command": "rm", "args": ["-rf", "/"], "cwd": str(workspace)}
        )
    assert "not allowed" in str(exc.value)

    with pytest.raises(ToolError) as exc:
        await agent_tools.call_tool(
            "run_command", {"command": "git", "args": ["push"], "cwd": str(workspace)}
        )
    assert "not allowed" in str(exc.value)

    with pytest.raises(ToolError):
        await agent_tools.call_tool(
            "run_command", {"command": "/bin/sh", "args": [], "cwd": str(workspace)}
        )


@pytest.mark.asyncio
async def test_run_command_executes_allowed(workspace):
    result = await agent_tools.call_tool(
        "run_command",
        {"command": "python3", "args": ["-c", "print('agent ok')"], "cwd": str(workspace)},
    )
    assert "agent ok" in result and "exit code 0" in result


# ── Approval policy ─────────────────────────────────────────
def test_needs_approval_policy(workspace, tmp_path):
    inside = {"path": str(workspace / "main.py"), "content": "x"}
    outside = {"path": str(tmp_path / "elsewhere.txt"), "content": "x"}
    assert not agent_tools.needs_approval("write_file", inside)
    assert agent_tools.needs_approval("write_file", outside)
    # Shell always asks, even inside a workspace.
    assert agent_tools.needs_approval("run_command", {"cwd": str(workspace), "command": "git"})
    # Knowledge search never touches the filesystem.
    assert not agent_tools.needs_approval("search_knowledge", {"query": "x"})


# ── The loop ────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_agent_runs_tool_then_answers(workspace, monkeypatch):
    fake = _scripted([
        {
            "content": "Reading the file first.",
            "tool_calls": [
                {"name": "read_file", "arguments": {"path": str(workspace / "main.py")}}
            ],
        },
        {"content": "The function returns hello.", "tool_calls": []},
    ])
    monkeypatch.setattr(agent_service, "chat_round_with_tools", fake)

    events = [e async for e in agent_service.run_agent("what does greet do?", use_mcp=False)]
    kinds = [k for e in events for k in e]
    assert kinds[0] == "agent"
    assert "tool_call" in kinds and "tool_result" in kinds
    result = next(e["tool_result"] for e in events if "tool_result" in e)
    assert result["ok"] and "def greet" in result["result"]
    assert events[-1] == {"done": True}


@pytest.mark.asyncio
async def test_agent_denied_approval_blocks_write(workspace, tmp_path, monkeypatch):
    outside = tmp_path / "outside.txt"
    fake = _scripted([
        {
            "content": "Writing.",
            "tool_calls": [
                {"name": "write_file", "arguments": {"path": str(outside), "content": "nope"}}
            ],
        },
        {"content": "I could not write there.", "tool_calls": []},
    ])
    monkeypatch.setattr(agent_service, "chat_round_with_tools", fake)

    events = []
    async for event in agent_service.run_agent("write outside", use_mcp=False):
        events.append(event)
        if "approval_required" in event:
            agent_service.resolve_approval(event["approval_required"]["id"], "deny")

    assert any("approval_required" in e for e in events)
    resolved = next(e["approval_resolved"] for e in events if "approval_resolved" in e)
    assert resolved["decision"] == "deny"
    assert not outside.exists()


@pytest.mark.asyncio
async def test_agent_allow_always_skips_second_prompt(workspace, tmp_path, monkeypatch):
    a, b = tmp_path / "out" / "a.txt", tmp_path / "out" / "b.txt"
    fake = _scripted([
        {
            "content": "",
            "tool_calls": [
                {"name": "write_file", "arguments": {"path": str(a), "content": "1"}}
            ],
        },
        {
            "content": "",
            "tool_calls": [
                {"name": "write_file", "arguments": {"path": str(b), "content": "2"}}
            ],
        },
        {"content": "Both written.", "tool_calls": []},
    ])
    monkeypatch.setattr(agent_service, "chat_round_with_tools", fake)

    prompts = 0
    async for event in agent_service.run_agent("write two files", use_mcp=False):
        if "approval_required" in event:
            prompts += 1
            agent_service.resolve_approval(event["approval_required"]["id"], "allow_always")

    assert prompts == 1  # same tool, same parent directory
    assert a.read_text() == "1" and b.read_text() == "2"


@pytest.mark.asyncio
async def test_agent_approval_times_out_to_deny(workspace, tmp_path, monkeypatch):
    monkeypatch.setattr(agent_service, "APPROVAL_TIMEOUT_SECONDS", 0.05)
    outside = tmp_path / "timeout.txt"
    fake = _scripted([
        {
            "content": "",
            "tool_calls": [
                {"name": "write_file", "arguments": {"path": str(outside), "content": "x"}}
            ],
        },
        {"content": "Denied.", "tool_calls": []},
    ])
    monkeypatch.setattr(agent_service, "chat_round_with_tools", fake)

    events = [e async for e in agent_service.run_agent("write", use_mcp=False)]
    resolved = next(e["approval_resolved"] for e in events if "approval_resolved" in e)
    assert resolved["decision"] == "deny"
    assert not outside.exists()


@pytest.mark.asyncio
async def test_agent_stops_at_step_cap(workspace, monkeypatch):
    async def always_calls(messages, *, tools, system=None, temperature=None, max_tokens=2048):
        return {
            "content": "again",
            "tool_calls": [
                {"name": "read_file", "arguments": {"path": str(workspace / "main.py")}}
            ],
        }

    monkeypatch.setattr(agent_service, "chat_round_with_tools", always_calls)
    events = [
        e async for e in agent_service.run_agent("loop forever", use_mcp=False, max_steps=3)
    ]
    steps = [e for e in events if "step" in e]
    assert len(steps) == 3
    assert "Stopped after 3 steps" in next(e["delta"] for e in events if "delta" in e)


@pytest.mark.asyncio
async def test_agent_tool_error_is_fed_back(workspace, monkeypatch):
    """A failed edit must reach the model so it can retry."""
    fake = _scripted([
        {
            "content": "",
            "tool_calls": [
                {
                    "name": "edit_file",
                    "arguments": {
                        "path": str(workspace / "main.py"),
                        "old_text": "nonexistent snippet",
                        "new_text": "x",
                    },
                }
            ],
        },
        {"content": "I will retry.", "tool_calls": []},
    ])
    monkeypatch.setattr(agent_service, "chat_round_with_tools", fake)
    events = [e async for e in agent_service.run_agent("edit it", use_mcp=False)]
    result = next(e["tool_result"] for e in events if "tool_result" in e)
    assert not result["ok"]
    assert "closest text" in result["result"]


@pytest.mark.asyncio
async def test_agent_unknown_tool_is_reported(workspace, monkeypatch):
    fake = _scripted([
        {"content": "", "tool_calls": [{"name": "delete_everything", "arguments": {}}]},
        {"content": "ok", "tool_calls": []},
    ])
    monkeypatch.setattr(agent_service, "chat_round_with_tools", fake)
    events = []
    async for event in agent_service.run_agent("do it", use_mcp=False):
        events.append(event)
        if "approval_required" in event:
            agent_service.resolve_approval(event["approval_required"]["id"], "allow_once")
    result = next(e["tool_result"] for e in events if "tool_result" in e)
    assert "Unknown tool" in result["result"]


# ── Router ──────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_approval_endpoint_validates(client, coverage_tracker):
    coverage_tracker("POST /api/agent/approvals")
    resp = await client.post("/api/agent/approvals/missing", json={"decision": "allow_once"})
    assert resp.status_code == 404
    resp = await client.post("/api/agent/approvals/missing", json={"decision": "nonsense"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_agent_stream_endpoint(client, workspace, monkeypatch, coverage_tracker):
    coverage_tracker("POST /api/agent/stream")
    monkeypatch.setattr("app.routers.agent.ensure_ai_configured", lambda: None)
    fake = _scripted([{"content": "Nothing to do.", "tool_calls": []}])
    monkeypatch.setattr(agent_service, "chat_round_with_tools", fake)

    resp = await client.post("/api/agent/stream", json={"task": "say hi", "use_mcp": False})
    assert resp.status_code == 200
    events = [json.loads(line) for line in resp.text.strip().splitlines()]
    assert "agent" in events[0]
    assert events[-1] == {"done": True}
