"""Private local-data paths shared by chat, knowledge, MCP, and agent state."""

from __future__ import annotations

import os
from pathlib import Path

from app.config import settings


def private_data_root() -> Path:
    """Create DATA_DIR and keep it traversable by this account only."""
    root = Path(settings.data_dir).expanduser()
    root.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(root, 0o700)
    except OSError:
        pass
    return root


def private_subdir(*parts: str) -> Path:
    root = private_data_root().resolve()
    path = root.joinpath(*parts).resolve()
    if path != root and root not in path.parents:
        raise ValueError("Private data path escapes DATA_DIR")
    path.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(path, 0o700)
    except OSError:
        pass
    return path


def protect_file(path: Path) -> None:
    """Best-effort owner-only permissions for a sensitive local data file."""
    try:
        if path.exists():
            os.chmod(path, 0o600)
    except OSError:
        pass


def write_private_text(path: Path, content: str) -> None:
    """Create or replace a text file without a world-readable creation window."""
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags, 0o600)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            fd = -1  # ownership transferred to the file object
            handle.write(content)
    finally:
        if fd >= 0:
            os.close(fd)
