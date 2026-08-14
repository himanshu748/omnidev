"""
Agent workspaces: the folders where the agent may act without asking.

A workspace is a user-designated directory. Inside one, the agent reads,
writes and patches freely. Everywhere else every action needs an explicit
approval from the app. The landing root (~/OmniDev/projects) is always an
implicit workspace so generated projects stay frictionless.

Config lives in DATA_DIR/workspaces.json, next to the MCP server config.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config import settings
from app.services.data_paths import private_data_root, write_private_text


class WorkspaceError(ValueError):
    """User-facing workspace problem (bad path, duplicate, unknown)."""


def _config_path() -> Path:
    return private_data_root() / "workspaces.json"


def _load() -> list[dict[str, Any]]:
    path = _config_path()
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return []
    return data if isinstance(data, list) else []


def _save(records: list[dict[str, Any]]) -> None:
    write_private_text(_config_path(), json.dumps(records, indent=2))


def _implicit_roots() -> list[Path]:
    """Always-trusted roots that need no user configuration."""
    try:
        return [Path(settings.land_root).expanduser().resolve()]
    except OSError:
        return []


def validate_dir(raw_path: str) -> Path:
    """Resolve a user-supplied workspace path, refusing unsafe choices."""
    if not raw_path or not raw_path.strip():
        raise WorkspaceError("Path is required.")
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        raise WorkspaceError("Path must be absolute.")
    path = path.resolve()
    if not path.is_dir():
        raise WorkspaceError(f"Not a directory: {path}")

    home = Path.home().resolve()
    if path == home:
        raise WorkspaceError(
            "Your whole home folder cannot be a workspace. Pick a project folder inside it."
        )
    if path == Path("/") or home not in path.parents:
        raise WorkspaceError("Workspaces must live inside your home folder.")

    data_root = Path(settings.data_dir).expanduser().resolve()
    if path == data_root or data_root in path.parents or path in data_root.parents:
        raise WorkspaceError("OmniDev's own data directory cannot be a workspace.")
    if (home / "Library") in path.parents or path == home / "Library":
        raise WorkspaceError("~/Library cannot be a workspace.")
    return path


def list_workspaces() -> list[dict[str, Any]]:
    records = _load()
    known = {r["path"] for r in records}
    implicit = [
        {"path": str(root), "added_at": "", "implicit": True}
        for root in _implicit_roots()
        if str(root) not in known
    ]
    return implicit + [{**r, "implicit": False} for r in records]


def add_workspace(raw_path: str) -> dict[str, Any]:
    path = validate_dir(raw_path)
    records = _load()
    if any(r["path"] == str(path) for r in records):
        raise WorkspaceError("That folder is already a workspace.")
    record = {
        "path": str(path),
        "added_at": datetime.now(timezone.utc).isoformat(),
    }
    records.append(record)
    _save(records)
    return {**record, "implicit": False}


def remove_workspace(raw_path: str) -> bool:
    target = str(Path(raw_path).expanduser().resolve())
    records = _load()
    remaining = [r for r in records if r["path"] != target]
    if len(remaining) == len(records):
        return False
    _save(remaining)
    return True


def roots() -> list[Path]:
    """Every trusted root: implicit plus user-configured."""
    configured = []
    for record in _load():
        try:
            configured.append(Path(record["path"]).resolve())
        except OSError:
            continue
    return _implicit_roots() + configured


def contains(path: Path) -> bool:
    """True when `path` sits inside a workspace root (symlinks resolved)."""
    try:
        resolved = Path(path).expanduser().resolve()
    except OSError:
        return False
    for root in roots():
        if resolved == root or root in resolved.parents:
            return True
    return False


# ── Async facade ────────────────────────────────────────────
async def list_workspaces_async() -> list[dict[str, Any]]:
    return await asyncio.to_thread(list_workspaces)


async def add_workspace_async(path: str) -> dict[str, Any]:
    return await asyncio.to_thread(add_workspace, path)


async def remove_workspace_async(path: str) -> bool:
    return await asyncio.to_thread(remove_workspace, path)
