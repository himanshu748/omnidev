"""
Agent mode: a bounded plan/act/observe loop over the built-in tools plus
any enabled MCP marketplace servers.

Safety model:
- Inside a workspace (see workspace_service) file tools run freely. Anywhere
  else, and for every shell command and every third-party MCP tool, the run
  pauses and asks the app for approval. Denial is the default if nothing
  answers, so a closed window can never authorise anything.
- The loop is capped at MAX_STEPS and can be stopped by disconnecting.
- Before the first mutation the current git HEAD is recorded and reported so
  the user always has a way back. The agent deliberately does NOT create a
  commit of its own: workspaces are the user's real repositories, and
  committing their in-progress work without asking would be worse than the
  problem it solves.
"""

from __future__ import annotations

import asyncio
import subprocess
import shutil
import time
import uuid
from pathlib import Path
from typing import Any, AsyncIterator

from app.services import agent_tools, workspace_service
from app.services.agent_tools import ToolError
from app.services.ai_service import (
    AIConfigurationError,
    AIResponseError,
    chat_round_with_tools,
    get_model,
    get_provider,
)

MAX_STEPS = 15
APPROVAL_TIMEOUT_SECONDS = 300
TOOL_RESULT_MAX_CHARS = 8_000

SYSTEM_PROMPT = """You are OmniDev's coding agent, running locally on the user's Mac.

Work in small, verifiable steps:
1. Look before you act. Read files and list directories before editing them.
2. Make one change at a time with edit_file, copying old_text verbatim from
   what you just read.
3. Verify your work with run_command when a test or build command applies.
4. Stop as soon as the task is done and reply with a short summary of what
   you changed. Do not keep calling tools after the work is finished.

Rules:
- You cannot delete anything. There is no delete tool, and shell commands that
  remove files are refused. If something truly needs deleting, say so in your
  summary and let the user do it.
- Replacing a whole file with write_file destroys what was there, so prefer
  edit_file for changes to an existing file. Use write_file for new files.
- Paths must be absolute.
- If a tool returns an error, read it carefully and correct your next call.
  Errors tell you exactly what went wrong.
- Some actions ask the user for approval. If one is denied, do not retry it;
  adapt or explain what you need.
- Never invent file contents. If you have not read a file, read it first.

Your workspaces (you may edit freely here):
{workspaces}
"""


class AgentError(ValueError):
    """User-facing agent problem."""


# ── Approval registry ───────────────────────────────────────
_pending: dict[str, dict[str, Any]] = {}


def _new_approval(tool: str, summary: str, detail: str) -> tuple[str, asyncio.Event]:
    approval_id = uuid.uuid4().hex[:12]
    event = asyncio.Event()
    _pending[approval_id] = {
        "event": event,
        "decision": None,
        "tool": tool,
        "summary": summary,
        "detail": detail,
        "created": time.time(),
    }
    return approval_id, event


def resolve_approval(approval_id: str, decision: str) -> bool:
    """Called by the router when the app answers an approval sheet."""
    if decision not in {"allow_once", "allow_always", "deny"}:
        raise AgentError("decision must be allow_once, allow_always or deny.")
    record = _pending.get(approval_id)
    if record is None:
        return False
    record["decision"] = decision
    record["event"].set()
    return True


def pending_approvals() -> list[dict[str, Any]]:
    return [
        {"id": key, "tool": rec["tool"], "summary": rec["summary"], "detail": rec["detail"]}
        for key, rec in _pending.items()
        if rec["decision"] is None
    ]


# ── Helpers ─────────────────────────────────────────────────
def _always_key(tool: str, arguments: dict[str, Any]) -> str:
    """Scope for an 'always allow' decision within a single run."""
    if tool == "run_command":
        args = arguments.get("args") or []
        first = str(args[0]) if args else ""
        return f"run_command:{arguments.get('command', '')} {first}".strip()
    path = agent_tools.target_path(tool, arguments)
    if path is not None:
        return f"{tool}:{path.parent}"
    return tool


def _git_head(path: Path) -> dict[str, Any] | None:
    """HEAD hash and dirty flag for the repo containing `path`, if any."""
    git = shutil.which("git")
    if git is None:
        return None
    directory = path if path.is_dir() else path.parent
    if not directory.is_dir():
        return None
    env = {"HOME": str(Path.home()), "PATH": "/usr/bin:/bin:/opt/homebrew/bin:/usr/local/bin",
           "GIT_TERMINAL_PROMPT": "0"}
    try:
        head = subprocess.run(
            [git, "rev-parse", "--short", "HEAD"], cwd=directory, env=env,
            capture_output=True, text=True, timeout=10,
        )
        if head.returncode != 0:
            return None
        status = subprocess.run(
            [git, "status", "--porcelain"], cwd=directory, env=env,
            capture_output=True, text=True, timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    toplevel = subprocess.run(
        [git, "rev-parse", "--show-toplevel"], cwd=directory, env=env,
        capture_output=True, text=True, timeout=10,
    )
    return {
        "repo": toplevel.stdout.strip() or str(directory),
        "head": head.stdout.strip(),
        "dirty": bool(status.stdout.strip()),
    }


async def _gather_tools(use_mcp: bool) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Built-in specs plus optional MCP tools, and the MCP dispatch map."""
    specs = list(agent_tools.TOOL_SPECS)
    dispatch: dict[str, Any] = {}
    if not use_mcp:
        return specs, dispatch
    try:
        from app.services.mcp_client_service import gather_ollama_tools

        mcp_tools, dispatch = await gather_ollama_tools()
    except Exception:
        # A broken MCP server must never take agent mode down.
        return specs, {}
    for tool in mcp_tools:
        function = tool.get("function") or {}
        name = function.get("name")
        if not name or name in agent_tools.TOOL_NAMES:
            continue
        specs.append(
            {
                "name": name,
                "description": function.get("description", ""),
                "parameters": function.get("parameters")
                or {"type": "object", "properties": {}},
            }
        )
    return specs, dispatch


# ── The loop ────────────────────────────────────────────────
async def run_agent(
    task: str,
    *,
    use_mcp: bool = True,
    temperature: float | None = None,
    max_steps: int = MAX_STEPS,
) -> AsyncIterator[dict[str, Any]]:
    """
    Run one agent task, yielding NDJSON-ready events.

    Events: {"agent": {...}} · {"step": {...}} · {"tool_call": {...}} ·
    {"approval_required": {...}} · {"tool_result": {...}} · {"delta": str} ·
    {"checkpoint": {...}} · {"error": str} · {"done": true}
    """
    workspaces = [str(root) for root in workspace_service.roots()]
    specs, mcp_dispatch = await _gather_tools(use_mcp)

    yield {
        "agent": {
            "status": "started",
            "provider": get_provider(),
            "model": get_model(),
            "workspaces": workspaces,
            "tools": [spec["name"] for spec in specs],
            "max_steps": max_steps,
        }
    }

    system = SYSTEM_PROMPT.format(
        workspaces="\n".join(f"- {w}" for w in workspaces) or "- (none configured yet)"
    )
    messages: list[dict[str, Any]] = [{"role": "user", "content": task}]
    always_allowed: set[str] = set()
    checkpointed = False

    for step in range(1, max_steps + 1):
        try:
            reply = await chat_round_with_tools(
                messages, tools=specs, system=system, temperature=temperature
            )
        except (AIConfigurationError, AIResponseError) as exc:
            yield {"error": str(exc)}
            return

        calls = reply.get("tool_calls") or []
        content = reply.get("content", "") or ""

        if not calls:
            yield {"delta": content or "(The agent finished without a summary.)"}
            yield {"done": True}
            return

        yield {"step": {"n": step, "thought": content[:2000], "tool_count": len(calls)}}
        messages.append({"role": "assistant", "content": content, "tool_calls": calls})

        for call in calls:
            tool = call.get("name", "")
            arguments = call.get("arguments") or {}
            is_builtin = tool in agent_tools.TOOL_NAMES
            yield {"tool_call": {"tool": tool, "arguments": arguments}}

            # Checkpoint the repo state before the first mutation.
            if not checkpointed and (
                tool in agent_tools.MUTATING_TOOLS or not is_builtin
            ):
                path = agent_tools.target_path(tool, arguments)
                if path is not None:
                    info = await asyncio.to_thread(_git_head, path)
                    if info:
                        yield {"checkpoint": info}
                checkpointed = True

            # Approval gate.
            requires = (
                agent_tools.needs_approval(tool, arguments) if is_builtin else True
            )
            key = _always_key(tool, arguments)
            if requires and key in always_allowed:
                requires = False

            if requires:
                summary, detail = (
                    agent_tools.describe(tool, arguments)
                    if is_builtin
                    else (f"Run MCP tool: {tool}", str(arguments)[:1500])
                )
                approval_id, event = _new_approval(tool, summary, detail)
                yield {
                    "approval_required": {
                        "id": approval_id,
                        "tool": tool,
                        "summary": summary,
                        "detail": detail,
                        "timeout_seconds": APPROVAL_TIMEOUT_SECONDS,
                    }
                }
                try:
                    await asyncio.wait_for(event.wait(), timeout=APPROVAL_TIMEOUT_SECONDS)
                    decision = _pending[approval_id]["decision"] or "deny"
                except asyncio.TimeoutError:
                    decision = "deny"
                except asyncio.CancelledError:
                    _pending.pop(approval_id, None)
                    raise
                finally:
                    _pending.pop(approval_id, None)

                yield {"approval_resolved": {"id": approval_id, "decision": decision}}
                if decision == "deny":
                    denial = (
                        f"The user denied '{summary}'. Do not retry this action. "
                        "Either work another way or explain what you need."
                    )
                    yield {"tool_result": {"tool": tool, "result": denial, "ok": False}}
                    messages.append({"role": "tool", "tool_name": tool, "content": denial})
                    continue
                if decision == "allow_always":
                    always_allowed.add(key)

            # Execute.
            try:
                if is_builtin:
                    result = await agent_tools.call_tool(tool, arguments)
                elif tool in mcp_dispatch:
                    from app.services.mcp_client_service import get_manager

                    record, tool_name = mcp_dispatch[tool]
                    result = await get_manager().call_tool(record, tool_name, arguments)
                else:
                    result = (
                        f"Unknown tool '{tool}'. Available tools: "
                        + ", ".join(spec["name"] for spec in specs)
                    )
                ok = True
            except ToolError as exc:
                result, ok = str(exc), False
            except Exception as exc:
                result, ok = f"Tool failed: {exc}", False

            if len(result) > TOOL_RESULT_MAX_CHARS:
                result = result[:TOOL_RESULT_MAX_CHARS] + "\n…(truncated)"
            yield {"tool_result": {"tool": tool, "result": result[:4000], "ok": ok}}
            messages.append({"role": "tool", "tool_name": tool, "content": result})

    yield {
        "delta": f"Stopped after {max_steps} steps without finishing. "
        "Ask me to continue if it was on the right track."
    }
    yield {"done": True}
