"""
Safety guards for indexing a whole laptop.

Three jobs, in order of how badly they bite:

1. Never hang. An iCloud-evicted file blocks open() forever when the file
   provider is unhealthy, at 0% CPU, with no timeout and no error. This is
   not hypothetical: it cost a full release cycle on the dev machine and 19
   of that machine's Desktop screenshots are evicted right now. stat() does
   NOT materialise a file, so the flag check is free and safe; open() is the
   only thing that blocks. Every read also runs under a wall-clock timeout so
   a stalling network volume degrades to a skipped file.

2. Never index a secret. The denylist below is checked at discovery, before
   a file is opened, and it wins over an explicitly added source: adding ~ as
   a folder still does not index ~/.ssh. There is deliberately no override,
   because a private key sitting in a plaintext chunk table, retrievable by
   any question that happens to match it, is far worse than the inconvenience.

3. Never lie about coverage. Skips are counted by reason and reported, so
   "indexed everything" is never implied when it is not true.
"""

from __future__ import annotations

import concurrent.futures
import fnmatch
import os
import shutil
import stat
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any, Callable

# macOS: the file exists in the listing but its data lives in iCloud.
SF_DATALESS = 0x40000000

# Per-file wall clock for any extraction. Generous enough for a big PDF,
# short enough that a wedged volume does not stall the whole job.
READ_TIMEOUT_SECONDS = 25
MAX_FILE_BYTES = 4_000_000
MIN_FREE_DISK_BYTES = 2 * 1024 * 1024 * 1024  # 2 GB

# Directory names refused anywhere in a path.
DENY_DIR_NAMES = {
    ".ssh", ".gnupg", ".gpg", ".aws", ".kube", ".docker", ".azure",
    ".git", ".hg", ".svn", ".bzr",
    "Keychains", "KeyChains", "MobileDevice", "Mobile Documents",
    "node_modules", ".venv", "venv", "__pycache__", ".next", ".nuxt",
    "dist", "build", ".build", "target", ".cache", ".pytest_cache",
    ".mypy_cache", ".tox", "Pods", "DerivedData", ".Trash",
    "1Password", "1Password 7", "1Password 8", "Bitwarden", "KeePass",
    "Firefox", "Chrome", "Chromium", "Arc", "BraveSoftware", "Safari",
}

# Absolute roots refused outright (expanded against $HOME at call time).
DENY_HOME_SUBPATHS = (
    "Library",
    ".ssh",
    ".gnupg",
    ".aws",
    ".kube",
    ".docker",
    ".config/gh",
    ".config/op",
    ".local/share/keyrings",
)

# Filename globs refused anywhere.
DENY_FILE_GLOBS = (
    ".env", ".env.*", "*.env",
    "*.pem", "*.key", "*.p12", "*.pfx", "*.keystore", "*.jks",
    "id_rsa*", "id_dsa*", "id_ecdsa*", "id_ed25519*", "*.ppk",
    "*.kdbx", "*.agilekeychain", "*.opvault", "*.keychain", "*.keychain-db",
    "credentials", "credentials.*", ".netrc", ".npmrc", ".pypirc",
    ".git-credentials", "*.mobileprovision", "*.p8",
    ".bash_history", ".zsh_history", ".python_history", ".node_repl_history",
    "*.sqlite-wal", "*.sqlite-shm",
)


class SkipReason:
    EVICTED = "evicted"
    TIMEOUT = "timed_out"
    TOO_LARGE = "too_large"
    EXCLUDED = "excluded"
    UNREADABLE = "unreadable"
    BINARY = "binary"


class SkipTally:
    """Counts skips by reason so coverage can be reported honestly."""

    def __init__(self) -> None:
        self._counts: Counter[str] = Counter()
        self._examples: dict[str, str] = {}

    def add(self, reason: str, path: str | Path = "") -> None:
        self._counts[reason] += 1
        if reason not in self._examples and path:
            self._examples[reason] = str(path)

    def merge(self, other: "SkipTally") -> None:
        self._counts.update(other._counts)
        for reason, example in other._examples.items():
            self._examples.setdefault(reason, example)

    @property
    def total(self) -> int:
        return sum(self._counts.values())

    def as_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "by_reason": dict(self._counts),
            "examples": dict(self._examples),
        }

    def summary(self) -> str:
        """A sentence a human can act on, or empty when nothing was skipped."""
        if not self._counts:
            return ""
        phrases = {
            SkipReason.EVICTED: "stored in iCloud (download them in Finder to include them)",
            SkipReason.TIMEOUT: "timed out while reading",
            SkipReason.TOO_LARGE: "too large",
            SkipReason.EXCLUDED: "excluded for safety",
            SkipReason.UNREADABLE: "unreadable",
            SkipReason.BINARY: "not text",
        }
        parts = [
            f"{count} {phrases.get(reason, reason)}"
            for reason, count in self._counts.most_common()
        ]
        return "Skipped " + ", ".join(parts) + "."


# ── Eviction ────────────────────────────────────────────────
def is_evicted(path: Path) -> bool:
    """
    True when the file's data lives in iCloud and reading it would block.

    Uses stat(), which never triggers materialisation. Never call brctl to
    download implicitly: on a full account that wedges the file provider,
    and it silently consumes the user's quota and disk.
    """
    try:
        return bool(os.stat(path).st_flags & SF_DATALESS)
    except (OSError, AttributeError):
        return False


# ── Denylist ────────────────────────────────────────────────
def _home() -> Path:
    return Path.home()


def denied_reason(path: Path) -> str | None:
    """Why this path must never be indexed, or None when it is allowed."""
    try:
        resolved = Path(path).expanduser()
    except (OSError, RuntimeError):
        return "unresolvable path"

    home = _home()
    for relative in DENY_HOME_SUBPATHS:
        root = home / relative
        if resolved == root or root in resolved.parents:
            return f"inside {root}"

    for part in resolved.parts[:-1]:
        if part in DENY_DIR_NAMES:
            return f"inside a {part} directory"
    if resolved.name in DENY_DIR_NAMES:
        return f"is a {resolved.name} directory"

    name = resolved.name
    for pattern in DENY_FILE_GLOBS:
        if fnmatch.fnmatch(name, pattern):
            return f"matches the protected pattern {pattern}"

    # Dotfiles are skipped by default; a secret is far more likely than a doc.
    if name.startswith(".") and name not in {".gitignore", ".gitattributes"}:
        return "is a hidden file"
    return None


def is_denied(path: Path) -> bool:
    return denied_reason(path) is not None


def matches_user_exclusions(path: Path, patterns: list[str]) -> bool:
    """User-configured exclusions, applied on top of the hard denylist."""
    text = str(path)
    name = path.name
    for raw in patterns:
        pattern = raw.strip()
        if not pattern:
            continue
        if pattern.startswith("/") or pattern.startswith("~"):
            root = Path(pattern).expanduser()
            if text == str(root) or str(root) in [str(p) for p in path.parents]:
                return True
        elif fnmatch.fnmatch(name, pattern) or fnmatch.fnmatch(text, pattern):
            return True
    return False


# ── Safe reads ──────────────────────────────────────────────
_read_pool = concurrent.futures.ThreadPoolExecutor(
    max_workers=2, thread_name_prefix="omnidev-extract"
)


class ReadTimeout(TimeoutError):
    """An extraction exceeded its wall clock and was abandoned."""


def run_with_timeout(
    function: Callable[..., Any],
    *args,
    timeout: float = READ_TIMEOUT_SECONDS,
    **kwargs,
) -> Any:
    """
    Run a blocking extraction under a hard wall clock.

    The worker thread cannot be killed if it is stuck in an uninterruptible
    read, so it is abandoned rather than joined. That leaks at most a couple
    of threads per pathological volume, which is the right trade against
    stalling the entire index job forever.
    """
    future = _read_pool.submit(function, *args, **kwargs)
    try:
        return future.result(timeout=timeout)
    except concurrent.futures.TimeoutError as exc:
        future.cancel()
        raise ReadTimeout(f"Read exceeded {timeout:.0f}s and was skipped.") from exc


def precheck(path: Path, *, user_exclusions: list[str] | None = None) -> str | None:
    """
    Everything that can be decided without opening the file.

    Returns a SkipReason, or None when the file is safe to read.
    """
    if is_denied(path):
        return SkipReason.EXCLUDED
    if user_exclusions and matches_user_exclusions(path, user_exclusions):
        return SkipReason.EXCLUDED
    if is_evicted(path):
        return SkipReason.EVICTED
    try:
        info = os.stat(path)
    except OSError:
        return SkipReason.UNREADABLE
    if not stat.S_ISREG(info.st_mode):
        return SkipReason.UNREADABLE
    if info.st_size > MAX_FILE_BYTES:
        return SkipReason.TOO_LARGE
    return None


# ── Machine health ──────────────────────────────────────────
def free_disk_bytes(path: Path | None = None) -> int:
    try:
        usage = shutil.disk_usage(str(path or Path.home()))
        return usage.free
    except OSError:
        return MIN_FREE_DISK_BYTES


def check_disk_headroom(path: Path | None = None) -> None:
    """Raise before starting work that would fill the disk."""
    free = free_disk_bytes(path)
    if free < MIN_FREE_DISK_BYTES:
        raise OSError(
            f"Only {free / 1e9:.1f} GB of disk free. Free up space to at least "
            f"{MIN_FREE_DISK_BYTES / 1e9:.0f} GB before indexing."
        )


# ── Index privacy ───────────────────────────────────────────
def protect_index_file(path: Path) -> None:
    """
    The index holds plaintext excerpts of everything indexed, so it is at
    least as sensitive as the documents themselves. Lock the file down and
    keep it out of Time Machine.
    """
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    tmutil = shutil.which("tmutil")
    if tmutil is None:
        return
    try:
        subprocess.run(
            [tmutil, "addexclusion", str(path)],
            capture_output=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        pass
