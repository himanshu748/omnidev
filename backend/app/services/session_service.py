"""
SQLite-backed conversation memory for chat.

Sessions and messages live in DATA_DIR/omnidev.db (default ~/.omnidev), so
"now add auth" works across turns. Everything stays on-disk and local; there
is no sync, telemetry, or remote storage.
"""

from __future__ import annotations

import asyncio
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.config import settings

# Bound how much history is replayed into the model context.
CONTEXT_MESSAGE_LIMIT = 20
CONTEXT_CHAR_BUDGET = 24_000
TITLE_MAX_CHARS = 64


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
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
            role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, id)")
    return conn


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _create_session_sync(first_message: str) -> str:
    session_id = uuid.uuid4().hex
    title = first_message.strip().replace("\n", " ")[:TITLE_MAX_CHARS]
    with _connect() as conn:
        conn.execute(
            "INSERT INTO sessions (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (session_id, title, _now(), _now()),
        )
    return session_id


def _session_exists_sync(session_id: str) -> bool:
    with _connect() as conn:
        row = conn.execute("SELECT 1 FROM sessions WHERE id = ?", (session_id,)).fetchone()
    return row is not None


def _append_message_sync(session_id: str, role: str, content: str) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO messages (session_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (session_id, role, content, _now()),
        )
        conn.execute("UPDATE sessions SET updated_at = ? WHERE id = ?", (_now(), session_id))


def _context_messages_sync(session_id: str) -> list[dict[str, str]]:
    """The most recent messages, oldest first, bounded by count and chars."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT role, content FROM messages WHERE session_id = ? ORDER BY id DESC LIMIT ?",
            (session_id, CONTEXT_MESSAGE_LIMIT),
        ).fetchall()

    budget = CONTEXT_CHAR_BUDGET
    kept: list[dict[str, str]] = []
    for row in rows:  # newest → oldest
        budget -= len(row["content"])
        if budget < 0 and kept:
            break
        kept.append({"role": row["role"], "content": row["content"]})
    kept.reverse()
    return kept


def _list_sessions_sync(limit: int) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT s.id, s.title, s.created_at, s.updated_at,
                   (SELECT COUNT(*) FROM messages m WHERE m.session_id = s.id) AS message_count
            FROM sessions s ORDER BY s.updated_at DESC LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def _list_messages_sync(session_id: str) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT role, content, created_at FROM messages WHERE session_id = ? ORDER BY id",
            (session_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def _delete_session_sync(session_id: str) -> bool:
    with _connect() as conn:
        conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        deleted = conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,)).rowcount
    return deleted > 0


# ── Async facade (sqlite3 is sync; keep the event loop free) ─
async def create_session(first_message: str) -> str:
    return await asyncio.to_thread(_create_session_sync, first_message)


async def session_exists(session_id: str) -> bool:
    return await asyncio.to_thread(_session_exists_sync, session_id)


async def append_message(session_id: str, role: str, content: str) -> None:
    await asyncio.to_thread(_append_message_sync, session_id, role, content)


async def context_messages(session_id: str) -> list[dict[str, str]]:
    return await asyncio.to_thread(_context_messages_sync, session_id)


async def list_sessions(limit: int = 50) -> list[dict]:
    return await asyncio.to_thread(_list_sessions_sync, limit)


async def list_messages(session_id: str) -> list[dict]:
    return await asyncio.to_thread(_list_messages_sync, session_id)


async def delete_session(session_id: str) -> bool:
    return await asyncio.to_thread(_delete_session_sync, session_id)
