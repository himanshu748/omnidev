"""
Built-in agent tools: narrow, forgiving, and easy for a 12B model to get right.

Design rules that come from running Gemma-class models against tool APIs:
- Prefer search-and-replace edits over unified diffs. Small models get hunk
  headers and line numbers wrong constantly; matching a literal snippet is
  something they do reliably.
- Every failure returns a message the model can act on. A failed edit echoes
  the closest matching region back so the next attempt can correct itself,
  instead of a bare "not found".
- Shell access is an argv allowlist, never a shell string, so there is no
  quoting, globbing or chaining to reason about.

Path safety and approval are decided by the caller (agent_service) using
workspace_service; these functions only refuse what is unsafe in principle.
"""

from __future__ import annotations

import asyncio
import difflib
import shutil
import subprocess
from pathlib import Path
from typing import Any

from app.services import knowledge_service, workspace_service

MAX_READ_CHARS = 60_000
MAX_WRITE_CHARS = 400_000
MAX_LIST_ENTRIES = 300
COMMAND_TIMEOUT_SECONDS = 180
COMMAND_OUTPUT_MAX_CHARS = 12_000

# argv allowlist. A value of None means any arguments are allowed; a set
# restricts the first argument (the subcommand).
ALLOWED_COMMANDS: dict[str, set[str] | None] = {
    "git": {
        "status", "diff", "log", "show", "add", "commit",
        "branch", "rev-parse", "ls-files", "stash",
    },
    "pytest": None,
    "python3": None,
    "node": None,
    "npm": {"test", "run", "ci"},
    "pnpm": {"test", "run"},
    "yarn": {"test", "run"},
    "swift": {"build", "test"},
    "make": None,
    "ruff": None,
    "mypy": None,
    "tsc": None,
}

# Refused even when the base command is allowed.
BLOCKED_ARGS = {
    "push", "remote", "clean", "reset", "config", "rebase",
    "filter-branch", "gc", "prune", "--hard",
}

_EXCLUDED_LIST_DIRS = {
    ".git", "node_modules", ".venv", "venv", "__pycache__", ".next",
    "dist", "build", ".build", ".pytest_cache", ".mypy_cache",
}


class ToolError(ValueError):
    """A tool failure that should be shown to the model so it can retry."""


# ── Tool schemas (provider-neutral JSON Schema) ─────────────
TOOL_SPECS: list[dict[str, Any]] = [
    {
        "name": "read_file",
        "description": (
            "Read a UTF-8 text file and return its contents. Use this before "
            "editing so your edit matches the real text."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Absolute path to the file."}
            },
            "required": ["path"],
        },
    },
    {
        "name": "list_dir",
        "description": "List files and folders in a directory. Use it to find your way around.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Absolute path to the directory."}
            },
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": (
            "Create a file, or replace an existing file's entire contents. "
            "For a small change to a big file prefer edit_file."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Absolute path to the file."},
                "content": {"type": "string", "description": "The complete new file contents."},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "edit_file",
        "description": (
            "Replace one exact snippet of a file with new text. old_text must "
            "appear in the file exactly once, copied verbatim including "
            "indentation. If it does not match, the error shows you the "
            "closest text in the file so you can retry."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Absolute path to the file."},
                "old_text": {"type": "string", "description": "Exact snippet to replace."},
                "new_text": {"type": "string", "description": "Replacement text."},
            },
            "required": ["path", "old_text", "new_text"],
        },
    },
    {
        "name": "run_command",
        "description": (
            "Run one allowed command and return its output. Pass the program "
            "and arguments separately, never a shell string. Allowed: git "
            "(read and commit only), pytest, python3, node, npm/pnpm/yarn "
            "test or run, swift build/test, make, ruff, mypy, tsc."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Program name, e.g. git or pytest."},
                "args": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Arguments as separate strings.",
                },
                "cwd": {"type": "string", "description": "Absolute directory to run in."},
            },
            "required": ["command", "cwd"],
        },
    },
    {
        "name": "search_knowledge",
        "description": (
            "Search the user's indexed local documents, code and past chats. "
            "Use it to ground your work in their own files."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "What to look for."},
                "top_k": {"type": "integer", "description": "How many excerpts (default 5)."},
            },
            "required": ["query"],
        },
    },
]

MUTATING_TOOLS = {"write_file", "edit_file", "run_command"}
TOOL_NAMES = {spec["name"] for spec in TOOL_SPECS}


# ── Path handling ───────────────────────────────────────────
def resolve_path(raw: str) -> Path:
    if not raw or not str(raw).strip():
        raise ToolError("path is required.")
    path = Path(str(raw)).expanduser()
    if not path.is_absolute():
        raise ToolError(f"Path must be absolute, got {raw!r}.")
    return path


def target_path(tool: str, arguments: dict[str, Any]) -> Path | None:
    """The filesystem path an invocation touches, for the approval check."""
    key = "cwd" if tool == "run_command" else "path"
    raw = arguments.get(key)
    if not raw:
        return None
    try:
        return resolve_path(raw)
    except ToolError:
        return None


def needs_approval(tool: str, arguments: dict[str, Any]) -> bool:
    """
    run_command always asks. Other tools ask only outside a workspace.
    Reads outside a workspace still ask, because reading a stranger's
    private file is exactly what a user would want to be told about.
    """
    if tool == "run_command":
        return True
    if tool == "search_knowledge":
        return False
    path = target_path(tool, arguments)
    if path is None:
        return True
    return not workspace_service.contains(path)


def describe(tool: str, arguments: dict[str, Any]) -> tuple[str, str]:
    """(summary, detail) shown in the approval sheet."""
    if tool == "run_command":
        argv = " ".join([str(arguments.get("command", ""))] + list(arguments.get("args") or []))
        return f"Run: {argv}", f"Working directory:\n{arguments.get('cwd', '')}"
    if tool == "write_file":
        content = str(arguments.get("content", ""))
        preview = content[:1500] + ("\n…(truncated)" if len(content) > 1500 else "")
        return f"Write {arguments.get('path', '')}", preview
    if tool == "edit_file":
        old = str(arguments.get("old_text", ""))[:700]
        new = str(arguments.get("new_text", ""))[:700]
        return f"Edit {arguments.get('path', '')}", f"Replace:\n{old}\n\nWith:\n{new}"
    if tool == "read_file":
        return f"Read {arguments.get('path', '')}", ""
    if tool == "list_dir":
        return f"List {arguments.get('path', '')}", ""
    return tool, ""


# ── Tool implementations ────────────────────────────────────
def _read_file(path_raw: str) -> str:
    path = resolve_path(path_raw)
    if not path.exists():
        parent = path.parent
        hint = ""
        if parent.is_dir():
            names = [p.name for p in list(parent.iterdir())[:40]]
            close = difflib.get_close_matches(path.name, names, n=3, cutoff=0.5)
            if close:
                hint = f" Did you mean: {', '.join(close)}?"
        raise ToolError(f"No such file: {path}.{hint}")
    if path.is_dir():
        raise ToolError(f"{path} is a directory. Use list_dir.")
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise ToolError(f"Could not read {path}: {exc}") from exc
    if len(text) > MAX_READ_CHARS:
        return text[:MAX_READ_CHARS] + f"\n…(truncated at {MAX_READ_CHARS} characters)"
    return text


def _list_dir(path_raw: str) -> str:
    path = resolve_path(path_raw)
    if not path.is_dir():
        raise ToolError(f"Not a directory: {path}")
    entries = []
    for child in sorted(path.iterdir()):
        if child.name.startswith(".") or child.name in _EXCLUDED_LIST_DIRS:
            continue
        entries.append(f"{child.name}/" if child.is_dir() else child.name)
        if len(entries) >= MAX_LIST_ENTRIES:
            entries.append(f"…(more than {MAX_LIST_ENTRIES} entries)")
            break
    return "\n".join(entries) if entries else "(empty directory)"


def _write_file(path_raw: str, content: str) -> str:
    path = resolve_path(path_raw)
    if content is None:
        raise ToolError("content is required.")
    if len(content) > MAX_WRITE_CHARS:
        raise ToolError(f"content exceeds {MAX_WRITE_CHARS} characters.")
    if path.is_dir():
        raise ToolError(f"{path} is a directory.")
    if path.is_symlink():
        raise ToolError(f"{path} is a symlink; refusing to write through it.")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        existed = path.exists()
        path.write_text(content, encoding="utf-8")
    except OSError as exc:
        raise ToolError(f"Could not write {path}: {exc}") from exc
    lines = content.count("\n") + 1
    return f"{'Updated' if existed else 'Created'} {path} ({lines} lines)."


def _closest_region(haystack: str, needle: str) -> str:
    """The chunk of `haystack` most similar to `needle`, for retry hints."""
    lines = haystack.splitlines()
    needle_lines = needle.splitlines() or [needle]
    window = max(len(needle_lines), 1)
    if not lines:
        return ""
    best_score, best_start = 0.0, 0
    for start in range(max(len(lines) - window + 1, 1)):
        candidate = "\n".join(lines[start : start + window])
        score = difflib.SequenceMatcher(None, candidate, needle).ratio()
        if score > best_score:
            best_score, best_start = score, start
    region = "\n".join(lines[best_start : best_start + window])
    return region[:1200]


def _edit_file(path_raw: str, old_text: str, new_text: str) -> str:
    path = resolve_path(path_raw)
    if not path.is_file():
        raise ToolError(f"No such file: {path}")
    if path.is_symlink():
        raise ToolError(f"{path} is a symlink; refusing to write through it.")
    if not old_text:
        raise ToolError("old_text is required and cannot be empty. Use write_file to create a file.")
    try:
        original = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ToolError(f"Could not read {path}: {exc}") from exc

    count = original.count(old_text)
    if count == 0:
        closest = _closest_region(original, old_text)
        raise ToolError(
            f"old_text was not found in {path}.\n"
            "Copy the snippet verbatim from the file, including indentation.\n"
            f"The closest text in the file is:\n---\n{closest}\n---"
        )
    if count > 1:
        raise ToolError(
            f"old_text appears {count} times in {path}. Include more surrounding "
            "lines so it matches exactly once."
        )

    updated = original.replace(old_text, new_text, 1)
    try:
        path.write_text(updated, encoding="utf-8")
    except OSError as exc:
        raise ToolError(f"Could not write {path}: {exc}") from exc
    delta = updated.count("\n") - original.count("\n")
    return f"Edited {path} ({delta:+d} lines)."


def _check_command(command: str, args: list[str]) -> None:
    base = (command or "").strip()
    if not base:
        raise ToolError("command is required.")
    if "/" in base or base.startswith("-"):
        raise ToolError(f"Pass a bare program name, not a path: {base!r}")
    if base not in ALLOWED_COMMANDS:
        allowed = ", ".join(sorted(ALLOWED_COMMANDS))
        raise ToolError(f"Command {base!r} is not allowed. Allowed commands: {allowed}.")
    lowered = [str(a).lower() for a in args]
    for blocked in BLOCKED_ARGS:
        if blocked in lowered:
            raise ToolError(
                f"'{base} {blocked}' is not allowed. OmniDev's agent never pushes, "
                "resets or rewrites history."
            )
    allowed_subs = ALLOWED_COMMANDS[base]
    if allowed_subs is not None:
        if not args:
            raise ToolError(f"{base} needs a subcommand, one of: {', '.join(sorted(allowed_subs))}.")
        if str(args[0]) not in allowed_subs:
            raise ToolError(
                f"'{base} {args[0]}' is not allowed. Allowed: {', '.join(sorted(allowed_subs))}."
            )


def _run_command(command: str, args: list[str], cwd_raw: str) -> str:
    args = [str(a) for a in (args or [])]
    _check_command(command, args)
    cwd = resolve_path(cwd_raw)
    if not cwd.is_dir():
        raise ToolError(f"Working directory does not exist: {cwd}")
    executable = shutil.which(command)
    if executable is None:
        raise ToolError(f"{command} is not installed on this machine.")

    env = {
        "PATH": "/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin:/usr/local/bin",
        "HOME": str(Path.home()),
        "LANG": "en_US.UTF-8",
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_CONFIG_NOSYSTEM": "1",
    }
    try:
        proc = subprocess.run(
            [executable, *args],
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            timeout=COMMAND_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        raise ToolError(
            f"{command} timed out after {COMMAND_TIMEOUT_SECONDS}s."
        ) from None
    except OSError as exc:
        raise ToolError(f"Could not run {command}: {exc}") from exc

    output = (proc.stdout or "") + (("\n" + proc.stderr) if proc.stderr else "")
    output = output.strip() or "(no output)"
    if len(output) > COMMAND_OUTPUT_MAX_CHARS:
        output = output[:COMMAND_OUTPUT_MAX_CHARS] + "\n…(truncated)"
    return f"exit code {proc.returncode}\n{output}"


async def _search_knowledge(query: str, top_k: int = 5) -> str:
    hits = await knowledge_service.search(query, top_k=max(1, min(int(top_k or 5), 20)))
    if not hits:
        return "No matches in the local knowledge index."
    return "\n\n---\n\n".join(f"[{h['file_path']}]\n{h['snippet'][:600]}" for h in hits)


# ── Dispatch ────────────────────────────────────────────────
async def call_tool(tool: str, arguments: dict[str, Any]) -> str:
    """Run a built-in tool. Raises ToolError with a retry-friendly message."""
    arguments = arguments or {}
    if tool == "read_file":
        return await asyncio.to_thread(_read_file, arguments.get("path", ""))
    if tool == "list_dir":
        return await asyncio.to_thread(_list_dir, arguments.get("path", ""))
    if tool == "write_file":
        return await asyncio.to_thread(
            _write_file, arguments.get("path", ""), arguments.get("content", "")
        )
    if tool == "edit_file":
        return await asyncio.to_thread(
            _edit_file,
            arguments.get("path", ""),
            arguments.get("old_text", ""),
            arguments.get("new_text", ""),
        )
    if tool == "run_command":
        return await asyncio.to_thread(
            _run_command,
            arguments.get("command", ""),
            arguments.get("args") or [],
            arguments.get("cwd", ""),
        )
    if tool == "search_knowledge":
        return await _search_knowledge(arguments.get("query", ""), arguments.get("top_k", 5))
    raise ToolError(f"Unknown tool {tool!r}.")
