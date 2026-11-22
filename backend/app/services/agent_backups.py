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

import hashlib
import json
import os
import shutil
import stat
import tempfile
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.services.data_paths import private_subdir

MAX_BACKUPS = 200
MAX_AGE_DAYS = 14
MAX_BACKUP_BYTES = 8_000_000

# Agent edits run in worker threads of the single backend process. Hold this
# across publication and restore so pruning cannot remove an in-use snapshot.
_MANIFEST_LOCK = threading.RLock()


def _root() -> Path:
    return private_subdir("agent-backups")


def _manifest_path() -> Path:
    return _root() / "manifest.jsonl"


def _stat_key(info: os.stat_result) -> tuple[int, ...]:
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def _fingerprint(path: Path) -> dict[str, Any] | None:
    """Hash a stable regular file without following a final symlink."""
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except FileNotFoundError:
        return None
    with os.fdopen(fd, "rb") as handle:
        before = os.fstat(handle.fileno())
        if not stat.S_ISREG(before.st_mode):
            raise OSError("Not a regular file.")
        digest = hashlib.sha256()
        while chunk := handle.read(65536):
            digest.update(chunk)
        after = os.fstat(handle.fileno())
        if _stat_key(before) != _stat_key(after) or _stat_key(after) != _stat_key(path.lstat()):
            raise OSError("File changed while being fingerprinted.")
    return {"sha256": digest.hexdigest(), "stat": list(_stat_key(after))}


def snapshot(path: Path, *, reason: str = "") -> dict[str, Any] | None:
    """
    Copy a file aside before it is changed. Returns the backup record, or
    None when there is nothing to preserve (a brand new file).

    Never raises: a failed backup must not block the edit the user asked for,
    but it is reported as `backed_up: false` so the caller can say so.
    """
    with _MANIFEST_LOCK:
        destination: Path | None = None
        try:
            if not path.is_file():
                return None
            if path.is_symlink():
                raise OSError("Refusing to snapshot a symlink.")
            # Accept stable aliases such as /var on macOS, then retain the
            # canonical parent path so a later symlink replacement is detected.
            path = path.resolve(strict=True)
            size = path.stat().st_size
            if size > MAX_BACKUP_BYTES:
                return {
                    "id": "",
                    "path": str(path),
                    "backed_up": False,
                    "note": f"file is {size / 1e6:.1f} MB, too large to snapshot",
                }
            original = _fingerprint(path)
            backup_id = f"{int(time.time())}-{uuid.uuid4().hex[:8]}"
            destination = _root() / f"{backup_id}{path.suffix or '.bak'}"
            shutil.copy2(path, destination)
            os.chmod(destination, 0o600)
            saved = _fingerprint(destination)
            if original is None or saved is None or original != _fingerprint(path):
                raise OSError("Source changed while being snapshotted.")
            if saved["sha256"] != original["sha256"]:
                raise OSError("Snapshot does not match the original.")
            record = {
                "id": backup_id,
                "path": str(path),
                "backup_path": str(destination),
                "bytes": size,
                "reason": reason,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "backed_up": True,
                "original_sha256": saved["sha256"],
                "original_target": original,
                "expected_target": original,
            }
            _prune([*_load_manifest(), record])
            return record
        except Exception:  # never block the user's edit or expose exception details
            if destination is not None:
                try:
                    destination.unlink(missing_ok=True)
                except OSError:
                    pass
            return {"id": "", "path": str(path), "backed_up": False, "note": "Could not save backup."}


def _load_manifest() -> list[dict[str, Any]]:
    with _MANIFEST_LOCK:
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
    """Publish a complete private manifest without truncating the old one."""
    with _MANIFEST_LOCK:
        path = _manifest_path()
        fd, temporary_name = tempfile.mkstemp(prefix=".manifest-", suffix=".tmp", dir=path.parent)
        temporary = Path(temporary_name)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                for record in records:
                    handle.write(json.dumps(record) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        finally:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass


def _prune(records: list[dict[str, Any]] | None = None) -> None:
    with _MANIFEST_LOCK:
        records = _load_manifest() if records is None else records
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
        # Publish first: if serialization or replacement fails, all old manifest
        # entries and their snapshot files remain available for restoration.
        _write_manifest(kept)
        for record in dropped:
            try:
                Path(record.get("backup_path", "")).unlink(missing_ok=True)
            except (OSError, TypeError, ValueError):
                # A stale/malformed cleanup path must not turn an already
                # published backup into a reported failure.
                pass


def list_backups(limit: int = 50) -> list[dict[str, Any]]:
    records = [r for r in _load_manifest() if r.get("backed_up")]
    return list(reversed(records))[:limit]


def record_completed_edit(backup_id: str, content: str) -> bool:
    """Remember only the agent's completed output; fail closed on a race/error."""
    with _MANIFEST_LOCK:
        try:
            records = _load_manifest()
            record = next((r for r in records if r.get("id") == backup_id), None)
            if record is None:
                return False
            current = _fingerprint(Path(record["path"]))
            intended_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
            if current is None or current["sha256"] != intended_hash:
                return False
            record["expected_target"] = current
            _write_manifest(records)
            return True
        except (OSError, ValueError, TypeError):
            # The edit already happened. Keep the old manifest so restore
            # requires an explicit overwrite rather than trusting unknown bytes.
            return False


class RestoreError(ValueError):
    """The backup cannot be restored."""


class RestoreConflict(RestoreError):
    """Restoring would overwrite an unexpected destination state."""


def _restore_target_state(target: Path) -> dict[str, Any] | None:
    # Refuse visible symlinks in the destination and its canonical parent path.
    if any(path.is_symlink() for path in (target, *target.parents)):
        raise RestoreConflict("Restore conflict: remove the destination symlink before restoring.")
    try:
        return _fingerprint(target)
    except OSError as exc:
        raise RestoreConflict("Restore conflict: destination is not a stable regular file.") from exc


def _advance_undo_chain(records: list[dict[str, Any]], record: dict[str, Any], saved: dict[str, Any]) -> bool:
    """Rebind proven predecessor expectations after our own atomic replacement."""
    original = record.get("original_target")
    if not isinstance(original, dict):
        return True  # Legacy snapshots lack proof of the pre-edit file identity.
    previous = []
    for candidate in records:
        if candidate.get("id") == record["id"]:
            break
        if candidate.get("path") == record["path"] and candidate.get("expected_target") == original:
            previous.append(candidate)
    if not previous:
        return True
    try:
        current = _restore_target_state(Path(record["path"]))
        # Rename changes ctime, but not the staged inode, bytes or mtime. Do not
        # adopt a different writer's replacement merely because its bytes match.
        if current is None or current["sha256"] != saved["sha256"] or current["stat"][:-1] != saved["stat"][:-1]:
            return False
        for candidate in previous:
            candidate["expected_target"] = current
        _write_manifest(records)
        return True
    except (OSError, ValueError, TypeError):
        # The file is restored; failed metadata publication must keep the old,
        # stricter expectations rather than authorize an unknown destination.
        return False


def restore(backup_id: str, *, force: bool = False) -> dict[str, Any]:
    """Restore unchanged/agent-edited files; other existing files need force."""
    with _MANIFEST_LOCK:
        records = _load_manifest()
        record = next((r for r in records if r.get("id") == backup_id), None)
        if record is None:
            raise RestoreError(f"Unknown backup id {backup_id!r}.")
        source = Path(record.get("backup_path", ""))
        if source.is_symlink() or not source.is_file():
            raise RestoreError("The snapshot file is gone; it may have been pruned.")
        target = Path(record["path"])
        current = _restore_target_state(target)
        result = {"id": backup_id, "restored_to": str(target), "bytes": record.get("bytes", 0)}
        # Repeated undo is harmless when the original bytes are already present.
        if current is not None and current["sha256"] == record.get("original_sha256"):
            return result
        if current is not None and current != record.get("expected_target") and not force:
            raise RestoreConflict(
                "Restore conflict: destination changed or its expected state is unknown; "
                "retry with force=true only to explicitly overwrite it."
            )
        temporary: Path | None = None
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            fd, name = tempfile.mkstemp(prefix=".restore-", suffix=".tmp", dir=target.parent)
            os.close(fd)
            temporary = Path(name)
            shutil.copy2(source, temporary)
            saved = _fingerprint(temporary)
            expected_hash = record.get("original_sha256")
            if expected_hash and (saved is None or saved["sha256"] != expected_hash):
                raise RestoreError("The snapshot no longer matches its recorded fingerprint.")
            if _restore_target_state(target) != current:
                raise RestoreConflict("Restore conflict: destination changed during restore; retry.")
            # Atomic publication avoids exposing a partially copied destination.
            # The final check is best effort across processes, not filesystem CAS.
            os.replace(temporary, target)
            if saved is not None and not _advance_undo_chain(records, record, saved):
                result["note"] = "Restored. An earlier backup may still require explicit overwrite confirmation."
        except OSError as exc:
            raise RestoreError("Could not restore the snapshot.") from exc
        finally:
            if temporary is not None:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    pass
        return result
