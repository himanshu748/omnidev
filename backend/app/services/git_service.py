"""
Land generated projects in a real local git repo — safely.

Scope, by construction:
- Writes ONLY under LAND_ROOT (default ~/OmniDev/projects); project names
  are strict slugs, and every file path re-runs the codegen sanitizer.
- git runs as an argv subprocess (no shell), in the project directory,
  with a minimal environment, hooks disabled, and a local identity — and
  only ever `init`, `add`, `commit`, `status`, `log`. No remotes, no push.
"""

from __future__ import annotations

import asyncio
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from app.config import settings
from app.services.codegen_service import _sanitize_file_entries

PROJECT_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,39}$")
GIT_TIMEOUT_SECONDS = 30

# Minimal env: no credential helpers, no user hooks, no inherited secrets.
_GIT_ENV = {
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_TERMINAL_PROMPT": "0",
    "HOME": str(Path.home()),
    "PATH": "/usr/bin:/bin:/opt/homebrew/bin:/usr/local/bin",
}
_GIT_IDENTITY = [
    "-c", "user.name=OmniDev",
    "-c", "user.email=omnidev@localhost",
    "-c", "core.hooksPath=/dev/null",
]


class GitLandError(ValueError):
    """User-facing landing failure (bad name, unsafe files, git problem)."""


def _land_root() -> Path:
    root = Path(settings.land_root).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _project_dir(name: str) -> Path:
    if not PROJECT_NAME_RE.match(name):
        raise GitLandError(
            "Project name must be 1-40 chars of lowercase letters, digits, or dashes."
        )
    root = _land_root()
    path = (root / name).resolve()
    if path.parent != root:
        raise GitLandError("Project path escaped the landing root.")
    if path.exists() and path.is_symlink():
        raise GitLandError("Project path is a symlink; refusing to write through it.")
    return path


def _run_git(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    git = shutil.which("git")
    if git is None:
        raise GitLandError("git is not installed.")
    return subprocess.run(
        [git, *_GIT_IDENTITY, *args],
        cwd=cwd,
        env=_GIT_ENV,
        capture_output=True,
        text=True,
        timeout=GIT_TIMEOUT_SECONDS,
    )


def _land_sync(name: str, files: list[dict[str, str]], message: str) -> dict[str, Any]:
    # Re-run the exact codegen sanitizer: path safety, secret scan, npm checks.
    try:
        validated = _sanitize_file_entries(files)
    except ValueError as exc:
        raise GitLandError(f"Files failed validation: {exc}") from exc

    project = _project_dir(name)
    project.mkdir(parents=True, exist_ok=True)

    for entry in validated:
        destination = (project / entry["path"]).resolve()
        if project not in destination.parents and destination != project:
            raise GitLandError(f"File path escaped the project directory: {entry['path']}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(entry["content"], encoding="utf-8")

    if not (project / ".git").is_dir():
        result = _run_git(["init", "-b", "main"], cwd=project)
        if result.returncode != 0:
            raise GitLandError(f"git init failed: {result.stderr.strip()[:300]}")

    result = _run_git(["add", "-A"], cwd=project)
    if result.returncode != 0:
        raise GitLandError(f"git add failed: {result.stderr.strip()[:300]}")

    commit_message = (message or "Land generated project").strip()[:200]
    result = _run_git(["commit", "-m", commit_message], cwd=project)
    if result.returncode != 0:
        combined = (result.stdout + result.stderr).lower()
        if "nothing to commit" in combined:
            commit_hash = _head_hash(project)
            return {
                "path": str(project),
                "commit": commit_hash,
                "files_written": len(validated),
                "message": "No changes since the last landing.",
            }
        raise GitLandError(f"git commit failed: {result.stderr.strip()[:300]}")

    return {
        "path": str(project),
        "commit": _head_hash(project),
        "files_written": len(validated),
        "message": f"Committed {len(validated)} files.",
    }


def _head_hash(project: Path) -> str:
    result = _run_git(["log", "-1", "--format=%h"], cwd=project)
    return result.stdout.strip() if result.returncode == 0 else ""


def _status_sync(name: str) -> dict[str, Any]:
    project = _project_dir(name)
    if not (project / ".git").is_dir():
        return {"exists": False, "path": str(project), "dirty": False, "last_commit": ""}
    status = _run_git(["status", "--porcelain"], cwd=project)
    log = _run_git(["log", "-1", "--format=%h %s"], cwd=project)
    return {
        "exists": True,
        "path": str(project),
        "dirty": bool(status.stdout.strip()),
        "last_commit": log.stdout.strip() if log.returncode == 0 else "",
    }


async def land_project(name: str, files: list[dict[str, str]], message: str = "") -> dict[str, Any]:
    return await asyncio.to_thread(_land_sync, name, files, message)


async def project_status(name: str) -> dict[str, Any]:
    return await asyncio.to_thread(_status_sync, name)
