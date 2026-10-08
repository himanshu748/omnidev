"""
Snapshots of every file the agent is about to change.

The agent has no delete tool, but overwriting a file destroys what was there,
which is the same loss from the user's point of view. So before any mutation
of an existing file its exact bytes are copied aside, and the copy is
restorable by id. This is what makes "the agent changed the wrong thing" a
30-second recovery rather than an argument with git about staged work.

Backups live in DATA_DIR/agent-backups with a JSONL manifest. They are capped
by count and age so this never becomes an unbounded second copy of a project.
"""

from __future__ import annotations

import json
import os
import shutil
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.services.data_paths import private_subdir

MAX_BACKUPS = 200
MAX_AGE_DAYS = 14
MAX_BACKUP_BYTES = 8_000_000


def _root() -> Path:
    return private_subdir("agent-backups")


def _manifest_path() -> Path:
    return _root() / "manifest.jsonl"


def snapshot(path: Path, *, reason: str = "") -> dict[str, Any] | None:
    """
    Copy a file aside before it is changed. Returns the backup record, or
    None when there is nothing to preserve (a brand new file).

    Never raises: a failed backup must not block the edit the user asked for,
    but it is reported as `backed_up: false` so the caller can say so.
    """
    try:
        if not path.is_file():
            return None
        size = path.stat().st_size
        if size > MAX_BACKUP_BYTES:
            return {
                "id": "",
                "path": str(path),
                "backed_up": False,
                "note": f"file is {size / 1e6:.1f} MB, too large to snapshot",
            }
        backup_id = f"{int(time.time())}-{uuid.uuid4().hex[:8]}"
        destination = _root() / f"{backup_id}{path.suffix or '.bak'}"
        shutil.copy2(path, destination)
        os.chmod(destination, 0o600)
        record = {
            "id": backup_id,
            "path": str(path),
            "backup_path": str(destination),
            "bytes": size,
            "reason": reason,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "backed_up": True,
        }
        with _manifest_path().open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record) + "\n")
        _prune()
        return record
    except Exception as exc:  # never block the user's edit
        return {"id": "", "path": str(path), "backed_up": False, "note": str(exc)[:120]}


def _load_manifest() -> list[dict[str, Any]]:
    path = _manifest_path()
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


def _write_manifest(records: list[dict[str, Any]]) -> None:
    with _manifest_path().open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record) + "\n")


def _prune() -> None:
    records = _load_manifest()
    cutoff = time.time() - MAX_AGE_DAYS * 86400
    kept: list[dict[str, Any]] = []
    dropped: list[dict[str, Any]] = []
    for record in records:
        try:
            created = datetime.fromisoformat(record["created_at"]).timestamp()
        except (KeyError, ValueError):
            created = time.time()
        (dropped if created < cutoff else kept).append(record)
    if len(kept) > MAX_BACKUPS:
        dropped.extend(kept[: len(kept) - MAX_BACKUPS])
        kept = kept[-MAX_BACKUPS:]
    for record in dropped:
        try:
            Path(record.get("backup_path", "")).unlink(missing_ok=True)
        except OSError:
            pass
    if dropped:
        _write_manifest(kept)


def list_backups(limit: int = 50) -> list[dict[str, Any]]:
    records = [r for r in _load_manifest() if r.get("backed_up")]
    return list(reversed(records))[:limit]


class RestoreError(ValueError):
    """The backup cannot be restored."""


def restore(backup_id: str) -> dict[str, Any]:
    """Put a snapshot back where it came from."""
    record = next((r for r in _load_manifest() if r.get("id") == backup_id), None)
    if record is None:
        raise RestoreError(f"Unknown backup id {backup_id!r}.")
    source = Path(record.get("backup_path", ""))
    if not source.is_file():
        raise RestoreError("The snapshot file is gone; it may have been pruned.")
    target = Path(record["path"])
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    except OSError as exc:
        raise RestoreError(f"Could not restore to {target}: {exc}") from exc
    return {"id": backup_id, "restored_to": str(target), "bytes": record.get("bytes", 0)}
