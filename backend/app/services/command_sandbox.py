"""
OS-level sandbox for the agent's shell commands.

The argv allowlist in agent_tools decides which programs may start. It cannot
decide what they do once running: python3, node, make and every test runner
execute arbitrary project code, so a hostile test file could otherwise read
~/.ssh or rewrite files anywhere in the home folder. This module confines the
process itself.

Policy, identical on every backend:
- Writes: only the workspace that contains the working directory, a fresh
  per-command scratch dir, the per-user temp/cache dirs, and build-tool caches.
  A command whose working directory is outside every workspace gets no project
  write access at all.
- Every repository's .git/hooks and .git/config stay read-only, and no .git
  can be renamed or created, so sandboxed code cannot plant a hook or config
  that git would run later outside the sandbox. Seatbelt matches these by
  path pattern; bubblewrap mount-pins every repository found in the workspace.
- Secrets (SSH/GPG keys, cloud and registry credentials, keychains, browser and
  password-manager data, OmniDev's own data dir) can be neither read nor
  written.
- Network: off by default, including localhost, so sandboxed code cannot drive
  OmniDev's own loopback API (approve itself, add workspaces). When the user
  enables it, OmniDev's API ports and container-engine sockets stay blocked on
  macOS.

Backends: macOS Seatbelt through /usr/bin/sandbox-exec, Linux bubblewrap.
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterator

from app.config import settings
from app.services import workspace_service
from app.services.data_paths import private_data_root, write_private_text

MODES = ("enforce", "off")
SEATBELT = "seatbelt"
BUBBLEWRAP = "bubblewrap"
SANDBOX_EXEC = "/usr/bin/sandbox-exec"
BACKEND_LABELS = {SEATBELT: "macOS Seatbelt", BUBBLEWRAP: "bubblewrap"}

# Home-relative paths that sandboxed code may neither read nor write.
SECRET_HOME_PATHS = (
    ".ssh", ".gnupg", ".aws", ".azure", ".kube", ".docker", ".config/gcloud",
    ".config/gh", ".config/op", ".password-store", ".local/share/keyrings",
    ".netrc", ".git-credentials", ".pypirc", ".bash_history", ".zsh_history",
    "Library/Keychains", "Library/Cookies", "Library/Safari", "Library/Mail",
    "Library/Messages", "Library/Application Support/Google/Chrome",
    "Library/Application Support/BraveSoftware", "Library/Application Support/Firefox",
    "Library/Application Support/Arc", "Library/Application Support/Microsoft Edge",
    "Library/Application Support/1Password", "Library/Application Support/Bitwarden",
    "Library/Group Containers/2BUA8C4S2C.com.1password",
)

# Home-relative build-tool caches that stay writable so builds still work.
CACHE_HOME_PATHS = (
    ".cache", ".npm", ".swiftpm", "Library/Caches", "Library/pnpm",
    "Library/org.swift.swiftpm",
)

# Loopback ports OmniDev's API listens on (dev and native-app defaults).
DEFAULT_API_PORTS = (8000, 8010)

# Container engines run as a more privileged daemon; reaching one from inside
# the sandbox would be an escape, so their sockets stay blocked.
DOCKER_SOCKET_PATHS = ("/var/run/docker.sock",)
DOCKER_SOCKET_HOME_PATHS = (
    ".docker/run/docker.sock", ".colima/default/docker.sock",
    ".orbstack/run/docker.sock", ".rd/docker.sock",
)

_DENIAL_MARKERS = (
    "operation not permitted", "read-only file system", "permission denied",
    "could not resolve host", "getaddrinfo", "enotfound", "eai_again",
    "network is unreachable", "nodename nor servname", "name resolution",
)


# ── Settings ────────────────────────────────────────────────
def _config_path() -> Path:
    return private_data_root() / "agent_sandbox.json"


def load_settings() -> dict[str, Any]:
    """Effective settings: env/.env defaults overlaid with the app's choices."""
    mode = settings.agent_sandbox if settings.agent_sandbox in MODES else "enforce"
    current: dict[str, Any] = {
        "mode": mode,
        "network": bool(settings.agent_sandbox_network),
        "auto_approve": bool(settings.agent_sandbox_auto_approve),
    }
    path = _config_path()
    try:
        stored = json.loads(path.read_text()) if path.exists() else {}
    except (OSError, json.JSONDecodeError):
        stored = {}
    if isinstance(stored, dict):
        if stored.get("mode") in MODES:
            current["mode"] = stored["mode"]
        for key in ("network", "auto_approve"):
            if isinstance(stored.get(key), bool):
                current[key] = stored[key]
    return current


def update_settings(
    *, mode: str | None = None, network: bool | None = None, auto_approve: bool | None = None
) -> dict[str, Any]:
    current = load_settings()
    if mode is not None:
        if mode not in MODES:
            raise ValueError(f"mode must be one of: {', '.join(MODES)}")
        current["mode"] = mode
    if network is not None:
        current["network"] = bool(network)
    if auto_approve is not None:
        current["auto_approve"] = bool(auto_approve)
    write_private_text(_config_path(), json.dumps(current, indent=2))
    return current


# ── Backend detection ───────────────────────────────────────
@lru_cache(maxsize=1)
def detect_backend() -> tuple[str | None, str]:
    """(backend, reason). backend is None when no sandbox can run here."""
    system = platform.system()
    if system == "Darwin":
        if not Path(SANDBOX_EXEC).exists():
            return None, "sandbox-exec is missing from this Mac."
        probe = [SANDBOX_EXEC, "-p", "(version 1)(allow default)", "/usr/bin/true"]
    elif system == "Linux":
        exe = shutil.which("bwrap")
        if exe is None:
            return None, (
                "Install bubblewrap (for example `sudo apt install bubblewrap`) "
                "to sandbox agent commands."
            )
        probe = [exe, "--ro-bind", "/", "/", "--dev", "/dev", "--unshare-net", "true"]
    else:
        return None, f"No command sandbox is available on {system}."

    try:
        proc = subprocess.run(probe, capture_output=True, text=True, timeout=15)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, f"The sandbox could not start: {exc}"
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip().splitlines()
        reason = detail[-1] if detail else f"exit code {proc.returncode}"
        if system == "Linux":
            return None, (
                f"bubblewrap cannot create a sandbox here ({reason}). Unprivileged "
                "user namespaces may be disabled on this system."
            )
        return None, f"The sandbox could not start: {reason}"
    return (SEATBELT if system == "Darwin" else BUBBLEWRAP), ""


# ── Per-command plan ────────────────────────────────────────
def _real(path: Path) -> Path:
    # Seatbelt matches resolved paths (/tmp is /private/tmp on macOS).
    return Path(os.path.realpath(path))


def _home() -> Path:
    return _real(Path.home())


def _darwin_user_dirs() -> list[Path]:
    dirs = []
    for name in ("DARWIN_USER_TEMP_DIR", "DARWIN_USER_CACHE_DIR"):
        try:
            out = subprocess.run(
                ["/usr/bin/getconf", name], capture_output=True, text=True, timeout=5
            ).stdout.strip()
        except (OSError, subprocess.TimeoutExpired):
            continue
        if out:
            dirs.append(_real(Path(out)))
    return dirs


def secret_paths() -> list[Path]:
    home = _home()
    paths = [home / rel for rel in SECRET_HOME_PATHS]
    paths.append(_real(Path(settings.data_dir).expanduser()))
    return paths


def docker_socket_paths() -> list[Path]:
    home = _home()
    return [_real(Path(p)) for p in DOCKER_SOCKET_PATHS] + [
        home / rel for rel in DOCKER_SOCKET_HOME_PATHS
    ]


def api_ports() -> list[int]:
    ports = set(DEFAULT_API_PORTS)
    raw = os.environ.get("OMNIDEV_BACKEND_PORT", "")
    if raw.isdigit():
        ports.add(int(raw))
    return sorted(ports)


def writable_root_for(cwd: Path) -> Path | None:
    """The workspace that contains `cwd`, which is the only writable project."""
    resolved = _real(cwd)
    best: Path | None = None
    for root in workspace_service.roots():
        real_root = _real(root)
        if resolved == real_root or real_root in resolved.parents:
            if best is None or len(real_root.parts) > len(best.parts):
                best = real_root
    return best


# Generated trees that never hold the user's own repositories.
_GIT_SCAN_SKIP = {
    "node_modules", ".build", ".venv", "venv", "__pycache__", "dist", "build",
    "target", ".next", ".nuxt", "Pods", "DerivedData", ".tox", ".cache",
}
GIT_SCAN_MAX_DIRS = 20_000


def git_entries_under(root: Path | None) -> list[Path]:
    """Every .git (directory or worktree file) inside the writable root."""
    if root is None:
        return []
    found: list[Path] = []
    for seen, (dirpath, dirnames, filenames) in enumerate(os.walk(root)):
        if seen >= GIT_SCAN_MAX_DIRS:
            break
        if ".git" in dirnames or ".git" in filenames:
            found.append(Path(dirpath) / ".git")
        dirnames[:] = [d for d in dirnames if d != ".git" and d not in _GIT_SCAN_SKIP]
    return found


def bubblewrap_git_mounts(root: Path | None, entries: list[Path]) -> list[str]:
    """
    Bind mounts cannot be renamed (EBUSY), so pin each .git, its repository
    directory and every directory up to the root: nothing can be moved aside to
    make room for a planted repository. Hooks and config are then remounted
    read-only on top.
    """
    if root is None:
        return []
    pinned: list[Path] = []
    for entry in entries:
        current = entry.parent
        while current != root and root in current.parents:
            if current not in pinned:
                pinned.append(current)
            current = current.parent
    # Parents before children, so child mounts land on top.
    args: list[str] = []
    for path in sorted(pinned, key=lambda p: len(p.parts)):
        args += ["--bind", str(path), str(path)]
    for entry in entries:
        if entry.is_dir():
            args += ["--bind", str(entry), str(entry)]
            for name in ("hooks", "config"):
                if (entry / name).exists():
                    args += ["--ro-bind", str(entry / name), str(entry / name)]
        else:
            args += ["--ro-bind", str(entry), str(entry)]
    return args


@dataclass
class SandboxPlan:
    mode: str
    backend: str | None
    network: bool
    writable_root: Path | None
    reason: str = ""
    extra_writable: list[Path] = field(default_factory=list)
    # bubblewrap only; Seatbelt protects .git by path pattern instead.
    git_entries: list[Path] = field(default_factory=list)

    @property
    def active(self) -> bool:
        return self.mode == "enforce" and self.backend is not None

    @property
    def refusal(self) -> str | None:
        """Why the command must not run at all, or None."""
        if self.mode == "enforce" and self.backend is None:
            return (
                "Command refused: the agent sandbox is required but unavailable. "
                f"{self.reason} Or turn the sandbox off in Settings → Agent, which "
                "runs commands with your full permissions."
            )
        return None

    def summary(self) -> str:
        if not self.active:
            if self.mode == "off":
                return "Not sandboxed: the sandbox is off, so this runs with your full account permissions."
            return "Sandbox unavailable: this command will be refused."
        where = (
            f"writes only inside {self.writable_root}"
            if self.writable_root
            else "no project write access (the working directory is not in a workspace)"
        )
        net = "network on" if self.network else "network off"
        return (
            f"Sandboxed ({BACKEND_LABELS[self.backend or '']}): {where}; {net}; "
            "secrets and credentials hidden; .git hooks and config read-only."
        )

    def as_event(self) -> dict[str, Any]:
        return {
            "active": self.active,
            "mode": self.mode,
            "backend": self.backend,
            "network": self.network,
            "writable_root": str(self.writable_root) if self.writable_root else None,
            "summary": self.summary(),
        }


def plan_for(cwd: Path) -> SandboxPlan:
    config = load_settings()
    backend, reason = detect_backend()
    root = writable_root_for(cwd)
    plan = SandboxPlan(
        mode=config["mode"],
        backend=backend,
        network=config["network"],
        writable_root=root,
        reason=reason,
    )
    if plan.active:
        home = _home()
        extra = [home / rel for rel in CACHE_HOME_PATHS]
        if backend == SEATBELT:
            extra += _darwin_user_dirs()
        plan.extra_writable = extra
        if backend == BUBBLEWRAP:
            plan.git_entries = git_entries_under(root)
    return plan


def auto_approves(cwd: Path | None) -> bool:
    """True when a command may skip approval: sandboxed and inside a workspace."""
    if cwd is None:
        return False
    if not load_settings()["auto_approve"]:
        return False
    plan = plan_for(cwd)
    return plan.active and plan.writable_root is not None


# ── Wrapping ────────────────────────────────────────────────
def seatbelt_profile(plan: SandboxPlan, scratch: Path) -> tuple[str, dict[str, str]]:
    """SBPL text plus -D parameters. Paths travel as parameters, never as
    string literals, so no path can break out of the profile syntax.
    Seatbelt applies the last matching rule, so order matters."""
    params: dict[str, str] = {}

    def param(prefix: str, path: Path) -> str:
        key = f"{prefix}_{sum(k.startswith(prefix + '_') for k in params)}"
        params[key] = str(path)
        return f'(param "{key}")'

    writable = [scratch, *plan.extra_writable]
    if plan.writable_root is not None:
        writable.insert(0, plan.writable_root)

    lines = [
        "(version 1)",
        "(allow default)",
        "(deny file-write*)",
        "(allow file-write*",
        '    (literal "/dev/null") (literal "/dev/zero") (literal "/dev/tty")',
        '    (literal "/dev/dtracehelper") (literal "/dev/stdout") (literal "/dev/stderr")',
        '    (subpath "/dev/fd")',
    ]
    lines += [f"    (subpath {param('WRITE', p)})" for p in writable]
    lines.append(")")
    # Any .git anywhere: hooks and config read-only, and no .git may be
    # created, renamed or replaced. Patterns, not paths, so moving a repository
    # aside cannot shed the protection.
    lines += [
        "(deny file-write*",
        '    (regex #"^.*/\\.git$")',
        '    (regex #"^.*/\\.git/hooks$")',
        '    (regex #"^.*/\\.git/hooks/.*$")',
        '    (regex #"^.*/\\.git/config$")',
        ")",
    ]
    lines.append("(deny file-read* file-write*")
    lines += [f"    (subpath {param('SECRET', p)})" for p in secret_paths()]
    lines.append(")")
    if plan.network:
        lines += [
            f'(deny network-outbound (remote ip "localhost:{port}"))' for port in api_ports()
        ]
        lines += [
            f"(deny network-outbound (literal {param('SOCKET', p)}))"
            for p in docker_socket_paths()
        ]
    else:
        lines.append("(deny network*)")
    return "\n".join(lines) + "\n", params


def bubblewrap_args(plan: SandboxPlan, scratch: Path, cwd: Path) -> list[str]:
    exe = shutil.which("bwrap") or "bwrap"
    args = [
        exe, "--die-with-parent", "--new-session",
        "--unshare-pid", "--unshare-ipc", "--unshare-uts", "--unshare-cgroup-try",
    ]
    if not plan.network:
        args.append("--unshare-net")
    args += ["--ro-bind", "/", "/", "--dev", "/dev", "--proc", "/proc"]
    writable = [scratch, *plan.extra_writable]
    if plan.writable_root is not None:
        writable.insert(0, plan.writable_root)
    for path in writable:
        if path.exists():
            args += ["--bind", str(path), str(path)]
    # Later mounts win, so protections go after the writable binds.
    args += bubblewrap_git_mounts(plan.writable_root, plan.git_entries)
    for path in secret_paths():
        if path.is_dir():
            args += ["--tmpfs", str(path)]
        elif path.exists():
            args += ["--ro-bind", "/dev/null", str(path)]
    args += ["--chdir", str(cwd), "--"]
    return args


def adjust_args(command: str, args: list[str], plan: SandboxPlan) -> list[str]:
    """SwiftPM sandboxes its own manifest builds, and Seatbelt profiles cannot
    nest, so it must skip that inner sandbox; the outer one still applies."""
    if (
        plan.active
        and plan.backend == SEATBELT
        and command == "swift"
        and args[:1] and args[0] in {"build", "test"}
        and "--disable-sandbox" not in args
    ):
        return [args[0], "--disable-sandbox", *args[1:]]
    return args


@contextmanager
def scratch_dir() -> Iterator[Path]:
    """A private temp dir for one command, removed afterwards (it is OmniDev's
    own scratch space, never user content)."""
    path = _real(Path(tempfile.mkdtemp(prefix="omnidev-agent-")))
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def wrap(plan: SandboxPlan, argv: list[str], cwd: Path, scratch: Path) -> list[str]:
    if not plan.active:
        return argv
    if plan.backend == SEATBELT:
        profile, params = seatbelt_profile(plan, scratch)
        prefix = [SANDBOX_EXEC, "-p", profile]
        for key, value in params.items():
            prefix += ["-D", f"{key}={value}"]
        return prefix + argv
    return bubblewrap_args(plan, scratch, _real(cwd)) + argv


def denial_hint(plan: SandboxPlan, returncode: int, output: str) -> str:
    """A note the model can act on when the sandbox probably caused a failure."""
    if not plan.active or returncode == 0:
        return ""
    lowered = output.lower()
    if not any(marker in lowered for marker in _DENIAL_MARKERS):
        return ""
    return (
        "\n[sandbox] This may have been blocked by OmniDev's sandbox: "
        + plan.summary()
        + " Do not try to work around it; tell the user what was blocked."
    )


# ── Status for the API and UI ───────────────────────────────
def _display(path: Path) -> str:
    home = _home()
    try:
        return "~/" + str(path.relative_to(home))
    except ValueError:
        return str(path)


def status(*, refresh: bool = False) -> dict[str, Any]:
    if refresh:
        detect_backend.cache_clear()
    config = load_settings()
    backend, reason = detect_backend()
    active = config["mode"] == "enforce" and backend is not None
    if active:
        summary = (
            f"Commands run inside {BACKEND_LABELS[backend or '']}: writes only in the "
            f"command's workspace, network {'on' if config['network'] else 'off'}, "
            "secrets hidden."
        )
    elif config["mode"] == "off":
        summary = "Sandbox off: commands run with your full account permissions."
    else:
        summary = f"Sandbox unavailable, so agent commands are refused. {reason}"
    return {
        **config,
        "backend": backend,
        "backend_label": BACKEND_LABELS.get(backend or "", ""),
        "available": backend is not None,
        "active": active,
        "reason": reason,
        "summary": summary,
        "protected_paths": [_display(p) for p in secret_paths()],
        "writable_caches": [_display(_home() / rel) for rel in CACHE_HOME_PATHS],
    }
