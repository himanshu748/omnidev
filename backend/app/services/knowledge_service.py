"""
Local knowledge index for grounded chat (RAG), sized for a whole laptop.

Storage is deliberately boring: float32 embedding blobs in SQLite plus a
numpy dot product, alongside an FTS5 keyword index. sqlite-vec was evaluated
and rejected because Apple's system Python has no `enable_load_extension` at
all (measured 2026-07-14 on /usr/bin/python3 3.9.6), so an extension-based
store would fail to open on a stranger's Mac. FTS5 is compiled into every
Python's SQLite, including Apple's.

Two things make this hold up at laptop scale:

- The in-memory matrix holds ids and vectors ONLY. Chunk text is fetched by
  id for the final top-k after ranking. Text was several times the size of
  the vectors and was being reloaded in full on every index run.
- The cache appends. Adding files no longer rebuilds what is already
  resident; only a deletion forces a full reload.

Retrieval fuses dense similarity with BM25 keyword search via reciprocal
rank fusion, because pure vector search cannot find an exact token such as
an error code or an order number.

Every read is gated by file_guards: iCloud-evicted files are skipped without
opening (they block forever), secrets are refused before they are opened,
and every extraction runs under a wall clock.
"""

from __future__ import annotations

import asyncio
import fnmatch
import os
import re
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from app.config import settings
from app.services.data_paths import private_data_root, protect_file
from app.services import ai_service, extractors, file_guards
from app.services.file_guards import SkipReason, SkipTally

CHUNK_CHARS = 2000
CHUNK_OVERLAP = 200
EMBED_BATCH = 16
RRF_K = 60

VALID_KINDS = {"docs", "code", "chat"}
CHAT_SOURCE_PATH = "builtin:chat-history"
EXCLUDED_DIRS = file_guards.DENY_DIR_NAMES


class KnowledgeError(ValueError):
    """A knowledge request that cannot be fulfilled (bad path, busy index)."""


# ── Schema ──────────────────────────────────────────────────
def _db_path() -> Path:
    return private_data_root() / "omnidev.db"


_protected_paths: set[str] = set()


def _connect() -> sqlite3.Connection:
    path = _db_path()
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS knowledge_sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT NOT NULL UNIQUE,
            kind TEXT NOT NULL CHECK (kind IN ('docs', 'code', 'chat')),
            added_at TEXT NOT NULL,
            last_indexed_at TEXT,
            file_count INTEGER NOT NULL DEFAULT 0,
            chunk_count INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS knowledge_chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id INTEGER NOT NULL REFERENCES knowledge_sources(id) ON DELETE CASCADE,
            file_path TEXT NOT NULL,
            chunk_index INTEGER NOT NULL,
            text TEXT NOT NULL,
            mtime REAL NOT NULL,
            size INTEGER NOT NULL,
            embedding BLOB NOT NULL
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_kchunks_source ON knowledge_chunks(source_id, file_path)"
    )
    # Columns added after v0.6.0 ships; existing indexes are upgraded in place.
    for table, column, ddl in (
        ("knowledge_sources", "skipped",
         "ALTER TABLE knowledge_sources ADD COLUMN skipped TEXT NOT NULL DEFAULT ''"),
        ("knowledge_chunks", "chunk_kind",
         "ALTER TABLE knowledge_chunks ADD COLUMN chunk_kind TEXT NOT NULL DEFAULT 'doc'"),
    ):
        existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}
        if column not in existing:
            conn.execute(ddl)
    conn.execute(
        "CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts "
        "USING fts5(text, chunk_id UNINDEXED, tokenize='unicode61')"
    )

    key = str(path)
    if key not in _protected_paths:
        file_guards.protect_index_file(path)
        _protected_paths.add(key)
    for candidate in (path, Path(f"{path}-wal"), Path(f"{path}-shm")):
        protect_file(candidate)
    return conn


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Job state ───────────────────────────────────────────────
_index_lock = asyncio.Lock()
_status: dict[str, Any] = {
    "running": False,
    "source_id": None,
    "files_total": 0,
    "files_done": 0,
    "error": None,
    "skipped": {},
    "message": "",
}
_generation_active = 0

_cache: dict[str, Any] = {"key": None, "ids": None, "matrix": None, "max_id": 0}
_needs_full_reload = True


def indexing_status() -> dict[str, Any]:
    return dict(_status)


class generation_guard:
    """Marks that a model is generating, so the index loop yields to it."""

    def __enter__(self):
        global _generation_active
        _generation_active += 1
        return self

    def __exit__(self, *exc):
        global _generation_active
        _generation_active = max(0, _generation_active - 1)
        return False


async def _yield_to_generation() -> None:
    waited = 0.0
    while _generation_active > 0 and waited < 120:
        await asyncio.sleep(0.5)
        waited += 0.5


# ── Chunking ────────────────────────────────────────────────
def _chunk_text(text: str) -> list[str]:
    text = (text or "").strip()
    if not text:
        return []
    if len(text) <= CHUNK_CHARS:
        return [text]
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + CHUNK_CHARS, len(text))
        if end < len(text):
            window = text[start:end]
            for separator in ("\n\n", "\n"):
                cut = window.rfind(separator, CHUNK_CHARS // 2)
                if cut != -1:
                    end = start + cut
                    break
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = max(end - CHUNK_OVERLAP, start + 1)
    return chunks


# ── Discovery ───────────────────────────────────────────────
def _gitignore_patterns(root: Path) -> list[str]:
    gitignore = root / ".gitignore"
    if not gitignore.is_file():
        return []
    patterns = []
    for line in gitignore.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("!"):
            continue
        patterns.append(line.rstrip("/"))
    return patterns


def _ignored(relative: str, patterns: list[str]) -> bool:
    parts = relative.split("/")
    for pattern in patterns:
        if "/" in pattern:
            if fnmatch.fnmatch(relative, pattern) or fnmatch.fnmatch(relative, pattern + "/*"):
                return True
        elif any(fnmatch.fnmatch(part, pattern) for part in parts):
            return True
    return False


def user_exclusions() -> list[str]:
    raw = (settings.knowledge_exclusions or "").strip()
    return [part.strip() for part in raw.split(",") if part.strip()]


def _discover_files(root: Path, kind: str) -> tuple[list[Path], SkipTally]:
    """
    Walk a source root, pruning excluded directories as we go.

    os.walk with in-place pruning rather than rglob: ~/Documents on the dev
    machine holds 200k+ files, almost all of them inside node_modules and
    caches, and rglob would stat every one.
    """
    allowed = (
        extractors.DOC_EXTS | extractors.IMAGE_EXTS | extractors.OFFICE_EXTS
        | extractors.IWORK_EXTS | extractors.EMAIL_EXTS
    )
    if kind == "code":
        allowed = allowed | extractors.CODE_EXTS

    patterns = _gitignore_patterns(root)
    exclusions = user_exclusions()
    tally = SkipTally()
    found: list[Path] = []
    root_resolved = root.resolve()

    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        current = Path(dirpath)
        dirnames[:] = [
            name for name in dirnames
            if name not in EXCLUDED_DIRS
            and not name.startswith(".")
            and not file_guards.is_denied(current / name)
        ]
        for filename in filenames:
            path = current / filename
            if path.suffix.lower() not in allowed:
                continue
            try:
                relative = str(path.relative_to(root))
            except ValueError:
                continue
            if patterns and _ignored(relative, patterns):
                continue
            reason = file_guards.precheck(path, user_exclusions=exclusions)
            if reason is not None:
                tally.add(reason, path)
                continue
            try:
                if not path.resolve().is_relative_to(root_resolved):
                    continue
            except OSError:
                continue
            found.append(path)
    return sorted(found), tally


def screenshots_folder() -> Path:
    """Where macOS drops screenshots. Not always ~/Desktop."""
    try:
        result = subprocess.run(
            ["defaults", "read", "com.apple.screencapture", "location"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            candidate = Path(result.stdout.strip()).expanduser()
            if candidate.is_dir():
                return candidate
    except (OSError, subprocess.TimeoutExpired):
        pass
    return Path.home() / "Desktop"


# ── Embeddings ──────────────────────────────────────────────
def _encode(vector: list[float]) -> bytes:
    array = np.asarray(vector, dtype=np.float32)
    norm = float(np.linalg.norm(array))
    if norm > 0:
        array = array / norm
    return array.tobytes()


async def _embed_batches(texts: list[str]) -> list[bytes]:
    blobs: list[bytes] = []
    for start in range(0, len(texts), EMBED_BATCH):
        await _yield_to_generation()
        vectors = await ai_service.embed_texts(texts[start : start + EMBED_BATCH])
        blobs.extend(_encode(vector) for vector in vectors)
    return blobs


# ── Sources ─────────────────────────────────────────────────
def _validate_folder(raw_path: str) -> Path:
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        raise KnowledgeError("Path must be absolute.")
    path = path.resolve()
    if not path.is_dir():
        raise KnowledgeError(f"Not a directory: {path}")
    data_root = Path(settings.data_dir).expanduser().resolve()
    if path == data_root or path.is_relative_to(data_root):
        raise KnowledgeError("OmniDev's own data directory cannot be indexed.")
    reason = file_guards.denied_reason(path)
    if reason is not None:
        raise KnowledgeError(f"That folder cannot be indexed: it {reason}.")
    return path


def _add_source_sync(path: str, kind: str) -> dict:
    with _connect() as conn:
        if conn.execute("SELECT id FROM knowledge_sources WHERE path = ?", (path,)).fetchone():
            raise KnowledgeError("This folder is already a knowledge source.")
        cursor = conn.execute(
            "INSERT INTO knowledge_sources (path, kind, added_at) VALUES (?, ?, ?)",
            (path, kind, _now()),
        )
        row = conn.execute(
            "SELECT * FROM knowledge_sources WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
    return dict(row)


def _list_sources_sync() -> list[dict]:
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM knowledge_sources ORDER BY id").fetchall()
    return [dict(row) for row in rows]


def _get_source_sync(source_id: int) -> dict | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM knowledge_sources WHERE id = ?", (source_id,)
        ).fetchone()
    return dict(row) if row else None


def _delete_fts(conn: sqlite3.Connection, chunk_ids: list[int]) -> None:
    for chunk_id in chunk_ids:
        conn.execute("DELETE FROM knowledge_fts WHERE chunk_id = ?", (chunk_id,))


def _chunk_ids_for(conn: sqlite3.Connection, source_id: int, file_path: str | None = None) -> list[int]:
    if file_path is None:
        rows = conn.execute(
            "SELECT id FROM knowledge_chunks WHERE source_id = ?", (source_id,)
        )
    else:
        rows = conn.execute(
            "SELECT id FROM knowledge_chunks WHERE source_id = ? AND file_path = ?",
            (source_id, file_path),
        )
    return [int(row["id"]) for row in rows]


def _delete_source_sync(source_id: int) -> bool:
    with _connect() as conn:
        _delete_fts(conn, _chunk_ids_for(conn, source_id))
        conn.execute("DELETE FROM knowledge_chunks WHERE source_id = ?", (source_id,))
        deleted = conn.execute(
            "DELETE FROM knowledge_sources WHERE id = ?", (source_id,)
        ).rowcount
    return deleted > 0


def _delete_everything_sync() -> dict[str, int]:
    with _connect() as conn:
        chunks = conn.execute("SELECT COUNT(*) AS n FROM knowledge_chunks").fetchone()["n"]
        sources = conn.execute("SELECT COUNT(*) AS n FROM knowledge_sources").fetchone()["n"]
        conn.execute("DELETE FROM knowledge_fts")
        conn.execute("DELETE FROM knowledge_chunks")
        conn.execute("DELETE FROM knowledge_sources")
    return {"sources": sources, "chunks": chunks}


async def add_source(path: str, kind: str) -> dict:
    if kind not in VALID_KINDS:
        raise KnowledgeError(f"Unknown kind {kind!r}. Use docs, code or chat.")
    stored = CHAT_SOURCE_PATH if kind == "chat" else str(_validate_folder(path))
    return await asyncio.to_thread(_add_source_sync, stored, kind)


async def list_sources() -> list[dict]:
    return await asyncio.to_thread(_list_sources_sync)


async def get_source(source_id: int) -> dict | None:
    return await asyncio.to_thread(_get_source_sync, source_id)


async def delete_source(source_id: int) -> bool:
    global _needs_full_reload
    deleted = await asyncio.to_thread(_delete_source_sync, source_id)
    if deleted:
        _needs_full_reload = True
    return deleted


async def delete_everything() -> dict[str, int]:
    """Erase the whole index. It holds plaintext excerpts, so this must be easy."""
    global _needs_full_reload
    result = await asyncio.to_thread(_delete_everything_sync)
    _needs_full_reload = True
    return result


# ── Indexing ────────────────────────────────────────────────
def _existing_files_sync(source_id: int) -> dict[str, tuple[float, int]]:
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT file_path, MAX(mtime) AS mtime, MAX(size) AS size
            FROM knowledge_chunks WHERE source_id = ? GROUP BY file_path
            """,
            (source_id,),
        ).fetchall()
    return {row["file_path"]: (row["mtime"], row["size"]) for row in rows}


def _replace_file_chunks_sync(
    source_id: int,
    file_path: str,
    mtime: float,
    size: int,
    chunks: list[str],
    blobs: list[bytes],
    chunk_kind: str,
) -> None:
    with _connect() as conn:
        _delete_fts(conn, _chunk_ids_for(conn, source_id, file_path))
        conn.execute(
            "DELETE FROM knowledge_chunks WHERE source_id = ? AND file_path = ?",
            (source_id, file_path),
        )
        for index, (chunk, blob) in enumerate(zip(chunks, blobs)):
            cursor = conn.execute(
                """
                INSERT INTO knowledge_chunks
                    (source_id, file_path, chunk_index, text, mtime, size, embedding, chunk_kind)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (source_id, file_path, index, chunk, mtime, size, blob, chunk_kind),
            )
            conn.execute(
                "INSERT INTO knowledge_fts (text, chunk_id) VALUES (?, ?)",
                (chunk, cursor.lastrowid),
            )


def _remove_file_chunks_sync(source_id: int, file_paths: list[str]) -> None:
    with _connect() as conn:
        for file_path in file_paths:
            _delete_fts(conn, _chunk_ids_for(conn, source_id, file_path))
            conn.execute(
                "DELETE FROM knowledge_chunks WHERE source_id = ? AND file_path = ?",
                (source_id, file_path),
            )


def _finish_source_sync(source_id: int, file_count: int, skipped: str) -> None:
    with _connect() as conn:
        chunk_count = conn.execute(
            "SELECT COUNT(*) AS n FROM knowledge_chunks WHERE source_id = ?", (source_id,)
        ).fetchone()["n"]
        conn.execute(
            """
            UPDATE knowledge_sources
            SET last_indexed_at = ?, file_count = ?, chunk_count = ?, skipped = ?
            WHERE id = ?
            """,
            (_now(), file_count, chunk_count, skipped, source_id),
        )


def _read_file_text(path: Path) -> str:
    """Extraction under a hard wall clock. Never called on an evicted file."""
    return file_guards.run_with_timeout(extractors.extract_text, path)


async def _index_folder_source(source: dict, *, full: bool) -> SkipTally:
    root = Path(source["path"])
    if not root.is_dir():
        raise KnowledgeError(f"Source folder no longer exists: {root}")

    files, tally = await asyncio.to_thread(_discover_files, root, source["kind"])
    existing = {} if full else await asyncio.to_thread(_existing_files_sync, source["id"])

    _status["files_total"] = len(files)
    _status["files_done"] = 0

    seen: set[str] = set()
    for path in files:
        key = str(path)
        seen.add(key)
        try:
            info = path.stat()
        except OSError:
            tally.add(SkipReason.UNREADABLE, path)
            _status["files_done"] += 1
            continue

        prior = existing.get(key)
        if prior and prior[0] == info.st_mtime and prior[1] == info.st_size:
            _status["files_done"] += 1
            continue

        # Re-check: a file can be evicted between discovery and read.
        if file_guards.is_evicted(path):
            tally.add(SkipReason.EVICTED, path)
            _status["files_done"] += 1
            continue

        try:
            text = await asyncio.to_thread(_read_file_text, path)
        except file_guards.ReadTimeout:
            tally.add(SkipReason.TIMEOUT, path)
            _status["files_done"] += 1
            continue
        except Exception:
            tally.add(SkipReason.UNREADABLE, path)
            _status["files_done"] += 1
            continue

        chunks = _chunk_text(text)
        if chunks:
            blobs = await _embed_batches(chunks)
            await asyncio.to_thread(
                _replace_file_chunks_sync,
                source["id"], key, info.st_mtime, info.st_size, chunks, blobs,
                extractors.kind_for(path),
            )
        _status["files_done"] += 1
        _status["skipped"] = tally.as_dict()["by_reason"]

    stale = [path for path in existing if path not in seen]
    if stale:
        await asyncio.to_thread(_remove_file_chunks_sync, source["id"], stale)
    await asyncio.to_thread(_finish_source_sync, source["id"], len(files), tally.summary())
    return tally


def _chat_documents_sync() -> list[tuple[str, float, str]]:
    with _connect() as conn:
        try:
            sessions = conn.execute(
                "SELECT id, title, updated_at FROM sessions ORDER BY id"
            ).fetchall()
        except sqlite3.OperationalError:
            return []
        documents: list[tuple[str, float, str]] = []
        for session in sessions:
            rows = conn.execute(
                "SELECT role, content FROM messages WHERE session_id = ? ORDER BY id",
                (session["id"],),
            ).fetchall()
            if not rows:
                continue
            body = "\n\n".join(f"{row['role']}: {row['content']}" for row in rows)
            text = f"Conversation: {session['title']}\n\n{body}"
            try:
                mtime = datetime.fromisoformat(session["updated_at"]).timestamp()
            except (ValueError, TypeError):
                mtime = 0.0
            documents.append((f"session:{session['id']}", mtime, text))
    return documents


async def _index_chat_source(source: dict, *, full: bool) -> SkipTally:
    documents = await asyncio.to_thread(_chat_documents_sync)
    existing = {} if full else await asyncio.to_thread(_existing_files_sync, source["id"])
    tally = SkipTally()
    _status["files_total"] = len(documents)
    _status["files_done"] = 0
    seen: set[str] = set()
    for virtual_path, mtime, text in documents:
        seen.add(virtual_path)
        size = len(text)
        prior = existing.get(virtual_path)
        if prior and prior[0] == mtime and prior[1] == size:
            _status["files_done"] += 1
            continue
        chunks = _chunk_text(text)
        if chunks:
            blobs = await _embed_batches(chunks)
            await asyncio.to_thread(
                _replace_file_chunks_sync,
                source["id"], virtual_path, mtime, size, chunks, blobs, "chat",
            )
        _status["files_done"] += 1
    stale = [path for path in existing if path not in seen]
    if stale:
        await asyncio.to_thread(_remove_file_chunks_sync, source["id"], stale)
    await asyncio.to_thread(_finish_source_sync, source["id"], len(documents), "")
    return tally


async def index_source(source_id: int, *, full: bool = False) -> None:
    global _needs_full_reload
    if _index_lock.locked():
        raise KnowledgeError("An indexing job is already running.")
    source = await get_source(source_id)
    if source is None:
        raise KnowledgeError(f"Unknown source id {source_id}.")
    try:
        await asyncio.to_thread(file_guards.check_disk_headroom, _db_path().parent)
    except OSError as exc:
        raise KnowledgeError(str(exc)) from exc

    async with _index_lock:
        _status.update(
            {"running": True, "source_id": source_id, "files_total": 0,
             "files_done": 0, "error": None, "skipped": {}, "message": ""}
        )
        try:
            if source["kind"] == "chat":
                tally = await _index_chat_source(source, full=full)
            else:
                tally = await _index_folder_source(source, full=full)
            _status["skipped"] = tally.as_dict()["by_reason"]
            _status["message"] = tally.summary()
        except (ai_service.AIConfigurationError, ai_service.AIResponseError,
                KnowledgeError) as exc:
            _status["error"] = str(exc)
            raise
        except Exception as exc:
            _status["error"] = f"Indexing failed: {exc}"
            raise
        finally:
            _status["running"] = False
            if full:
                _needs_full_reload = True


def start_index_job(source_id: int, *, full: bool = False) -> None:
    async def _run():
        try:
            await index_source(source_id, full=full)
        except Exception:
            pass  # surfaced through _status["error"]

    asyncio.get_running_loop().create_task(_run())


# ── Search ──────────────────────────────────────────────────
def _load_new_rows_sync(after_id: int) -> tuple[np.ndarray, np.ndarray]:
    """ids and vectors only. Text is fetched later, for the top-k alone."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, embedding FROM knowledge_chunks WHERE id > ? ORDER BY id",
            (after_id,),
        ).fetchall()
    empty = (np.zeros((0,), dtype=np.int64), np.zeros((0, 0), dtype=np.float32))
    if not rows:
        return empty
    ids, vectors, dimension = [], [], None
    for row in rows:
        vector = np.frombuffer(row["embedding"], dtype=np.float32)
        if dimension is None:
            dimension = vector.shape[0]
        if vector.shape[0] != dimension:
            continue  # written by a different embedder; ignore
        ids.append(int(row["id"]))
        vectors.append(vector)
    if not vectors:
        return empty
    return np.asarray(ids, dtype=np.int64), np.vstack(vectors)


def _refresh_cache_sync() -> None:
    global _needs_full_reload
    key = str(_db_path())
    if _cache["key"] != key or _needs_full_reload:
        _cache.update({"key": key, "ids": None, "matrix": None, "max_id": 0})
        _needs_full_reload = False

    ids, matrix = _load_new_rows_sync(_cache["max_id"])
    if ids.size == 0:
        if _cache["ids"] is None:
            _cache["ids"] = np.zeros((0,), dtype=np.int64)
            _cache["matrix"] = np.zeros((0, 1), dtype=np.float32)
        return

    if _cache["ids"] is None or _cache["ids"].size == 0:
        _cache["ids"], _cache["matrix"] = ids, matrix
    elif _cache["matrix"].shape[1] == matrix.shape[1]:
        _cache["ids"] = np.concatenate([_cache["ids"], ids])
        _cache["matrix"] = np.vstack([_cache["matrix"], matrix])
    else:
        _cache["ids"], _cache["matrix"] = ids, matrix  # embedder dimension changed
    _cache["max_id"] = int(_cache["ids"].max())


_FTS_TOKEN_RE = re.compile(r"[A-Za-z0-9_]{2,}")


def _fts_query(query: str) -> str:
    """A safe FTS5 expression: quoted tokens joined with OR."""
    tokens = _FTS_TOKEN_RE.findall(query)[:16]
    return " OR ".join(f'"{token}"' for token in tokens)


def _keyword_ranking_sync(query: str, limit: int) -> list[int]:
    expression = _fts_query(query)
    if not expression:
        return []
    with _connect() as conn:
        try:
            rows = conn.execute(
                "SELECT chunk_id FROM knowledge_fts WHERE knowledge_fts MATCH ? "
                "ORDER BY bm25(knowledge_fts) LIMIT ?",
                (expression, limit),
            ).fetchall()
        except sqlite3.OperationalError:
            return []
    return [int(row["chunk_id"]) for row in rows]


def _fetch_chunks_sync(chunk_ids: list[int]) -> dict[int, dict]:
    if not chunk_ids:
        return {}
    placeholders = ",".join("?" * len(chunk_ids))
    query = (
        "SELECT c.id, c.source_id, c.file_path, c.text, c.chunk_kind, c.mtime, s.kind "  # nosec B608
        "FROM knowledge_chunks c JOIN knowledge_sources s ON s.id = c.source_id "
        # Only '?' tokens are interpolated; every chunk id remains a bound value.
        f"WHERE c.id IN ({placeholders})"
    )
    with _connect() as conn:
        rows = conn.execute(query, chunk_ids).fetchall()
    return {int(row["id"]): dict(row) for row in rows}


async def search(
    query: str,
    *,
    top_k: int | None = None,
    source_ids: list[int] | None = None,
    kinds: list[str] | None = None,
    after: float | None = None,
    before: float | None = None,
    path_prefix: str | None = None,
) -> list[dict]:
    """
    Hybrid retrieval: dense similarity fused with BM25 via reciprocal rank
    fusion, so an exact token (an error code, an order number) is findable
    even when the embedding does not place it near the query.
    """
    top_k = top_k or settings.knowledge_top_k
    await asyncio.to_thread(_refresh_cache_sync)
    matrix: np.ndarray = _cache["matrix"]
    ids: np.ndarray = _cache["ids"]
    if matrix is None or matrix.shape[0] == 0:
        return []

    pool = max(top_k * 8, 64)
    vectors = await ai_service.embed_texts([query])
    probe = np.frombuffer(_encode(vectors[0]), dtype=np.float32)
    if probe.shape[0] != matrix.shape[1]:
        raise ai_service.AIConfigurationError(
            "The embedding model changed since indexing. Re-index your sources."
        )
    scores = matrix @ probe
    order = np.argsort(-scores)[:pool]
    dense_ids = [int(ids[i]) for i in order]
    dense_scores = {int(ids[i]): float(scores[i]) for i in order}

    keyword_ids = await asyncio.to_thread(_keyword_ranking_sync, query, pool)

    fused: dict[int, float] = {}
    for rank, chunk_id in enumerate(dense_ids):
        fused[chunk_id] = fused.get(chunk_id, 0.0) + 1.0 / (RRF_K + rank + 1)
    for rank, chunk_id in enumerate(keyword_ids):
        fused[chunk_id] = fused.get(chunk_id, 0.0) + 1.0 / (RRF_K + rank + 1)

    ranked = sorted(fused, key=lambda chunk_id: -fused[chunk_id])
    records = await asyncio.to_thread(_fetch_chunks_sync, ranked[: pool * 2])

    results: list[dict] = []
    for chunk_id in ranked:
        record = records.get(chunk_id)
        if record is None:
            continue
        if source_ids and record["source_id"] not in source_ids:
            continue
        if kinds and record["chunk_kind"] not in kinds:
            continue
        if after is not None and (record["mtime"] or 0) < after:
            continue
        if before is not None and (record["mtime"] or 0) > before:
            continue
        if path_prefix and not str(record["file_path"]).startswith(path_prefix):
            continue
        results.append(
            {
                "source_id": record["source_id"],
                "kind": record["chunk_kind"] or record["kind"],
                "file_path": record["file_path"],
                "snippet": record["text"][:800],
                "score": round(dense_scores.get(chunk_id, fused[chunk_id]), 4),
            }
        )
        if len(results) >= top_k:
            break
    return results


# ── Ad-hoc file questions (no indexing) ─────────────────────
async def read_for_question(path_raw: str, question: str, *, budget: int = 24_000) -> dict:
    """
    Extract a single file for one question without touching the index.

    Small files go into the prompt whole. Big ones are embedded into a scratch
    ranking, top chunks selected, and the vectors are thrown away immediately.
    Nothing is persisted, so this works on a file anywhere on the machine.
    """
    path = Path(path_raw).expanduser()
    if not path.is_absolute():
        raise KnowledgeError("Path must be absolute.")
    if path.is_dir():
        raise KnowledgeError(f"{path} is a directory. Point at a single file.")
    if not path.is_file():
        raise KnowledgeError(f"No such file: {path}")

    reason = file_guards.denied_reason(path)
    if reason is not None:
        raise KnowledgeError(f"That file cannot be read: it {reason}.")
    if file_guards.is_evicted(path):
        raise KnowledgeError(
            f"{path.name} is stored in iCloud and has no local copy. "
            "Download it in Finder, then try again."
        )
    try:
        info = path.stat()
    except OSError as exc:
        raise KnowledgeError(f"Could not read {path.name}: {exc}") from exc
    if info.st_size > file_guards.MAX_FILE_BYTES:
        raise KnowledgeError(
            f"{path.name} is {info.st_size / 1e6:.0f} MB, larger than the "
            f"{file_guards.MAX_FILE_BYTES / 1e6:.0f} MB limit."
        )

    try:
        text = await asyncio.to_thread(_read_file_text, path)
    except file_guards.ReadTimeout as exc:
        raise KnowledgeError(f"Reading {path.name} timed out.") from exc
    except Exception as exc:
        raise KnowledgeError(f"Could not extract text from {path.name}: {exc}") from exc

    if not text.strip():
        raise KnowledgeError(
            f"No text could be extracted from {path.name}."
            + (" The image may contain no readable text." if extractors.kind_for(path) == "image" else "")
        )

    if len(text) <= budget:
        return {"file_path": str(path), "excerpts": [text], "truncated": False}

    chunks = _chunk_text(text)
    vectors = await ai_service.embed_texts([question] + chunks)
    probe = np.frombuffer(_encode(vectors[0]), dtype=np.float32)
    matrix = np.vstack([np.frombuffer(_encode(v), dtype=np.float32) for v in vectors[1:]])
    order = np.argsort(-(matrix @ probe))
    selected: list[str] = []
    used = 0
    for index in order:
        chunk = chunks[int(index)]
        if used + len(chunk) > budget:
            continue
        selected.append(chunk)
        used += len(chunk)
        if used >= budget:
            break
    return {"file_path": str(path), "excerpts": selected, "truncated": True}


async def index_stats() -> dict[str, Any]:
    def _stats() -> dict[str, Any]:
        with _connect() as conn:
            chunks = conn.execute("SELECT COUNT(*) AS n FROM knowledge_chunks").fetchone()["n"]
            by_kind = {
                row["chunk_kind"]: row["n"]
                for row in conn.execute(
                    "SELECT chunk_kind, COUNT(*) AS n FROM knowledge_chunks GROUP BY chunk_kind"
                )
            }
        path = _db_path()
        return {
            "chunks": chunks,
            "by_kind": by_kind,
            "database_bytes": path.stat().st_size if path.exists() else 0,
            "database_path": str(path),
            "ocr_available": extractors.ocr_available(),
        }

    return await asyncio.to_thread(_stats)
