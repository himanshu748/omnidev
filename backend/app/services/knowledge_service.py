"""
Local knowledge index for grounded chat (RAG).

Sources are user-chosen local folders (docs or code) plus the built-in chat
history. Files are chunked and embedded with the provider's embedding model;
vectors live as float32 blobs in DATA_DIR/omnidev.db next to chat memory and
search is a numpy dot product over an in-memory matrix cache. Everything
stays on-disk and local.

Indexing is incremental (mtime + size) and runs as a single background job;
embedding calls run one batch at a time so chat generation keeps headroom.
"""

from __future__ import annotations

import asyncio
import fnmatch
import html.parser
import io
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from app.config import settings
from app.services import ai_service

# Chunking: ~512 tokens approximated in characters, with overlap so answers
# spanning a boundary still retrieve.
CHUNK_CHARS = 2000
CHUNK_OVERLAP = 200
EMBED_BATCH = 16
MAX_FILE_BYTES = 4_000_000

DOC_EXTS = {".md", ".markdown", ".txt", ".rst", ".pdf", ".html", ".htm"}
CODE_EXTS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".swift", ".go", ".rs", ".java",
    ".kt", ".rb", ".c", ".h", ".cpp", ".hpp", ".m", ".cs", ".php", ".css",
    ".scss", ".sql", ".sh", ".zsh", ".bash", ".yaml", ".yml", ".toml",
    ".json", ".xml", ".proto", ".graphql", ".dockerfile", ".makefile",
}
EXCLUDED_DIRS = {
    ".git", ".hg", ".svn", "node_modules", ".venv", "venv", "__pycache__",
    ".next", ".nuxt", "dist", "build", ".build", "target", ".cache",
    ".pytest_cache", ".mypy_cache", ".tox", "Pods", "DerivedData",
}

VALID_KINDS = {"docs", "code", "chat"}
CHAT_SOURCE_PATH = "builtin:chat-history"


class KnowledgeError(ValueError):
    """A knowledge request that cannot be fulfilled (bad path, busy index)."""


# ── Schema ──────────────────────────────────────────────────
def _db_path() -> Path:
    root = Path(settings.data_dir).expanduser()
    root.mkdir(parents=True, exist_ok=True)
    return root / "omnidev.db"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(_db_path())
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
    return conn


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Indexing job state ──────────────────────────────────────
_index_lock = asyncio.Lock()
_status: dict[str, Any] = {
    "running": False,
    "source_id": None,
    "files_total": 0,
    "files_done": 0,
    "error": None,
}
# Bumped on every index/delete so the search matrix cache invalidates. The
# cache key also includes the DB path so a data_dir change never serves a
# stale matrix.
_index_version = 0
_matrix_cache: dict[str, Any] = {"key": None, "ids": None, "matrix": None}


def indexing_status() -> dict[str, Any]:
    return dict(_status)


# ── Text extraction ─────────────────────────────────────────
class _HTMLTextParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self._skip += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style"} and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip:
            self._parts.append(data)

    def text(self) -> str:
        return re.sub(r"\n{3,}", "\n\n", "".join(self._parts))


def _extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(path.read_bytes()))
        return "\n\n".join((page.extract_text() or "") for page in reader.pages)
    raw = path.read_text(encoding="utf-8", errors="ignore")
    if suffix in {".html", ".htm"}:
        parser = _HTMLTextParser()
        parser.feed(raw)
        return parser.text()
    return raw


def _chunk_text(text: str) -> list[str]:
    """Fixed-size chunks with overlap, preferring paragraph boundaries."""
    text = text.strip()
    if not text:
        return []
    if len(text) <= CHUNK_CHARS:
        return [text]
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + CHUNK_CHARS, len(text))
        if end < len(text):
            # Prefer breaking on a paragraph, then a line, inside the tail.
            window = text[start:end]
            for sep in ("\n\n", "\n"):
                cut = window.rfind(sep, CHUNK_CHARS // 2)
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


# ── File discovery ──────────────────────────────────────────
def _gitignore_patterns(root: Path) -> list[str]:
    """Light .gitignore support: top-level file, no negations."""
    gi = root / ".gitignore"
    if not gi.is_file():
        return []
    patterns = []
    for line in gi.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("!"):
            continue
        patterns.append(line.rstrip("/"))
    return patterns


def _ignored(rel: str, patterns: list[str]) -> bool:
    parts = rel.split("/")
    for pattern in patterns:
        if "/" in pattern:
            if fnmatch.fnmatch(rel, pattern) or fnmatch.fnmatch(rel, pattern + "/*"):
                return True
        elif any(fnmatch.fnmatch(part, pattern) for part in parts):
            return True
    return False


def _discover_files(root: Path, kind: str) -> list[Path]:
    exts = DOC_EXTS if kind == "docs" else (CODE_EXTS | DOC_EXTS)
    patterns = _gitignore_patterns(root)
    found: list[Path] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        rel_parts = path.relative_to(root).parts
        if any(part in EXCLUDED_DIRS or part.startswith(".") for part in rel_parts[:-1]):
            continue
        if path.name.startswith("."):
            continue
        if path.suffix.lower() not in exts:
            continue
        rel = "/".join(rel_parts)
        if patterns and _ignored(rel, patterns):
            continue
        try:
            if path.stat().st_size > MAX_FILE_BYTES:
                continue
        except OSError:
            continue
        # Never escape the registered root through symlinked parents.
        if not path.resolve().is_relative_to(root.resolve()):
            continue
        found.append(path)
    return found


# ── Embedding helpers ───────────────────────────────────────
def _encode(vec: list[float]) -> bytes:
    arr = np.asarray(vec, dtype=np.float32)
    norm = float(np.linalg.norm(arr))
    if norm > 0:
        arr = arr / norm
    return arr.tobytes()


async def _embed_batches(texts: list[str]) -> list[bytes]:
    """Embed sequentially in small batches (concurrency 1 by design)."""
    blobs: list[bytes] = []
    for i in range(0, len(texts), EMBED_BATCH):
        batch = texts[i : i + EMBED_BATCH]
        vectors = await ai_service.embed_texts(batch)
        blobs.extend(_encode(v) for v in vectors)
    return blobs


# ── Sources CRUD ────────────────────────────────────────────
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
    return path


def _add_source_sync(path: str, kind: str) -> dict:
    with _connect() as conn:
        existing = conn.execute(
            "SELECT id FROM knowledge_sources WHERE path = ?", (path,)
        ).fetchone()
        if existing:
            raise KnowledgeError("This folder is already a knowledge source.")
        cur = conn.execute(
            "INSERT INTO knowledge_sources (path, kind, added_at) VALUES (?, ?, ?)",
            (path, kind, _now()),
        )
        row = conn.execute(
            "SELECT * FROM knowledge_sources WHERE id = ?", (cur.lastrowid,)
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


def _delete_source_sync(source_id: int) -> bool:
    with _connect() as conn:
        conn.execute("DELETE FROM knowledge_chunks WHERE source_id = ?", (source_id,))
        deleted = conn.execute(
            "DELETE FROM knowledge_sources WHERE id = ?", (source_id,)
        ).rowcount
    return deleted > 0


async def add_source(path: str, kind: str) -> dict:
    if kind not in VALID_KINDS:
        raise KnowledgeError(f"Unknown kind {kind!r}. Use docs, code or chat.")
    if kind == "chat":
        stored = CHAT_SOURCE_PATH
    else:
        stored = str(_validate_folder(path))
    return await asyncio.to_thread(_add_source_sync, stored, kind)


async def list_sources() -> list[dict]:
    return await asyncio.to_thread(_list_sources_sync)


async def get_source(source_id: int) -> dict | None:
    return await asyncio.to_thread(_get_source_sync, source_id)


async def delete_source(source_id: int) -> bool:
    global _index_version
    deleted = await asyncio.to_thread(_delete_source_sync, source_id)
    if deleted:
        _index_version += 1
    return deleted


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
) -> None:
    with _connect() as conn:
        conn.execute(
            "DELETE FROM knowledge_chunks WHERE source_id = ? AND file_path = ?",
            (source_id, file_path),
        )
        conn.executemany(
            """
            INSERT INTO knowledge_chunks
                (source_id, file_path, chunk_index, text, mtime, size, embedding)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (source_id, file_path, i, chunk, mtime, size, blob)
                for i, (chunk, blob) in enumerate(zip(chunks, blobs))
            ],
        )


def _remove_file_chunks_sync(source_id: int, file_paths: list[str]) -> None:
    with _connect() as conn:
        conn.executemany(
            "DELETE FROM knowledge_chunks WHERE source_id = ? AND file_path = ?",
            [(source_id, fp) for fp in file_paths],
        )


def _finish_source_sync(source_id: int, file_count: int) -> None:
    with _connect() as conn:
        chunk_count = conn.execute(
            "SELECT COUNT(*) AS n FROM knowledge_chunks WHERE source_id = ?",
            (source_id,),
        ).fetchone()["n"]
        conn.execute(
            """
            UPDATE knowledge_sources
            SET last_indexed_at = ?, file_count = ?, chunk_count = ?
            WHERE id = ?
            """,
            (_now(), file_count, chunk_count, source_id),
        )


async def _index_folder_source(source: dict, *, full: bool) -> None:
    root = Path(source["path"])
    if not root.is_dir():
        raise KnowledgeError(f"Source folder no longer exists: {root}")
    files = await asyncio.to_thread(_discover_files, root, source["kind"])
    existing = {} if full else await asyncio.to_thread(_existing_files_sync, source["id"])

    _status["files_total"] = len(files)
    _status["files_done"] = 0

    seen: set[str] = set()
    for path in files:
        rel = str(path)
        seen.add(rel)
        stat = path.stat()
        prior = existing.get(rel)
        if prior and prior[0] == stat.st_mtime and prior[1] == stat.st_size:
            _status["files_done"] += 1
            continue
        try:
            text = await asyncio.to_thread(_extract_text, path)
        except Exception:
            _status["files_done"] += 1
            continue
        chunks = _chunk_text(text)
        if chunks:
            blobs = await _embed_batches(chunks)
            await asyncio.to_thread(
                _replace_file_chunks_sync,
                source["id"], rel, stat.st_mtime, stat.st_size, chunks, blobs,
            )
        _status["files_done"] += 1

    stale = [fp for fp in existing if fp not in seen]
    if stale:
        await asyncio.to_thread(_remove_file_chunks_sync, source["id"], stale)
    await asyncio.to_thread(_finish_source_sync, source["id"], len(files))


def _chat_documents_sync() -> list[tuple[str, float, str]]:
    """(virtual_path, mtime, text) per chat session, from the chat tables."""
    with _connect() as conn:
        sessions = conn.execute(
            "SELECT id, title, updated_at FROM sessions ORDER BY id"
        ).fetchall()
        docs: list[tuple[str, float, str]] = []
        for s in sessions:
            rows = conn.execute(
                "SELECT role, content FROM messages WHERE session_id = ? ORDER BY id",
                (s["id"],),
            ).fetchall()
            if not rows:
                continue
            body = "\n\n".join(f"{r['role']}: {r['content']}" for r in rows)
            text = f"Conversation: {s['title']}\n\n{body}"
            mtime = datetime.fromisoformat(s["updated_at"]).timestamp()
            docs.append((f"session:{s['id']}", mtime, text))
    return docs


async def _index_chat_source(source: dict, *, full: bool) -> None:
    docs = await asyncio.to_thread(_chat_documents_sync)
    existing = {} if full else await asyncio.to_thread(_existing_files_sync, source["id"])
    _status["files_total"] = len(docs)
    _status["files_done"] = 0
    seen: set[str] = set()
    for virtual_path, mtime, text in docs:
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
                source["id"], virtual_path, mtime, size, chunks, blobs,
            )
        _status["files_done"] += 1
    stale = [fp for fp in existing if fp not in seen]
    if stale:
        await asyncio.to_thread(_remove_file_chunks_sync, source["id"], stale)
    await asyncio.to_thread(_finish_source_sync, source["id"], len(docs))


async def index_source(source_id: int, *, full: bool = False) -> None:
    """Run one indexing job. Raises KnowledgeError if a job is running."""
    global _index_version
    if _index_lock.locked():
        raise KnowledgeError("An indexing job is already running.")
    source = await get_source(source_id)
    if source is None:
        raise KnowledgeError(f"Unknown source id {source_id}.")
    async with _index_lock:
        _status.update(
            {"running": True, "source_id": source_id, "files_total": 0,
             "files_done": 0, "error": None}
        )
        try:
            if source["kind"] == "chat":
                await _index_chat_source(source, full=full)
            else:
                await _index_folder_source(source, full=full)
        except (ai_service.AIConfigurationError, ai_service.AIResponseError,
                KnowledgeError) as exc:
            _status["error"] = str(exc)
            raise
        except Exception as exc:
            _status["error"] = f"Indexing failed: {exc}"
            raise
        finally:
            _status["running"] = False
            _index_version += 1


def start_index_job(source_id: int, *, full: bool = False) -> None:
    """Fire-and-forget indexing; progress via indexing_status()."""

    async def _run():
        try:
            await index_source(source_id, full=full)
        except Exception:
            pass  # surfaced through _status["error"]

    asyncio.get_running_loop().create_task(_run())


# ── Search ──────────────────────────────────────────────────
def _load_matrix_sync() -> tuple[np.ndarray, list[dict]]:
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT c.id, c.source_id, c.file_path, c.text, c.embedding, s.kind
            FROM knowledge_chunks c JOIN knowledge_sources s ON s.id = c.source_id
            ORDER BY c.id
            """
        ).fetchall()
    if not rows:
        return np.zeros((0, 1), dtype=np.float32), []
    metas = []
    vecs = []
    dim = None
    for row in rows:
        vec = np.frombuffer(row["embedding"], dtype=np.float32)
        if dim is None:
            dim = vec.shape[0]
        if vec.shape[0] != dim:
            continue  # mixed embedder history; skip mismatched rows
        vecs.append(vec)
        metas.append(
            {
                "chunk_id": row["id"],
                "source_id": row["source_id"],
                "kind": row["kind"],
                "file_path": row["file_path"],
                "text": row["text"],
            }
        )
    return np.vstack(vecs), metas


async def search(
    query: str,
    *,
    top_k: int | None = None,
    source_ids: list[int] | None = None,
) -> list[dict]:
    """Top matching chunks with paths and cosine scores."""
    top_k = top_k or settings.knowledge_top_k
    cache_key = (str(_db_path()), _index_version)
    if _matrix_cache["key"] != cache_key:
        matrix, metas = await asyncio.to_thread(_load_matrix_sync)
        _matrix_cache.update({"key": cache_key, "matrix": matrix, "ids": metas})
    matrix: np.ndarray = _matrix_cache["matrix"]
    metas: list[dict] = _matrix_cache["ids"]
    if matrix.shape[0] == 0:
        return []

    vectors = await ai_service.embed_texts([query])
    q = np.frombuffer(_encode(vectors[0]), dtype=np.float32)
    if q.shape[0] != matrix.shape[1]:
        raise ai_service.AIConfigurationError(
            "The embedding model changed since indexing. Re-index your sources."
        )
    scores = matrix @ q
    order = np.argsort(-scores)
    results: list[dict] = []
    for idx in order:
        meta = metas[int(idx)]
        if source_ids and meta["source_id"] not in source_ids:
            continue
        results.append(
            {
                "source_id": meta["source_id"],
                "kind": meta["kind"],
                "file_path": meta["file_path"],
                "snippet": meta["text"][:800],
                "score": float(scores[int(idx)]),
            }
        )
        if len(results) >= top_k:
            break
    return results
