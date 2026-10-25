"""Agent command sandbox: policy, profile generation, approval flow, API, and
real confinement whenever this machine can run a sandbox."""

from __future__ import annotations

import os
import shutil
import socket
import sys
import tempfile
from pathlib import Path

import pytest

from app.services import agent_service, agent_tools, command_sandbox, workspace_service


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    root = Path(os.path.realpath(tmp_path / "proj"))
    root.mkdir()
    monkeypatch.setattr(workspace_service, "roots", lambda: [root])
    return root


@pytest.fixture
def fake_backend(monkeypatch):
    def use(backend: str | None, reason: str = "no sandbox here"):
        monkeypatch.setattr(
            command_sandbox, "detect_backend", lambda: (backend, "" if backend else reason)
        )

    return use


def _scripted(rounds):
    calls = list(rounds)
    state = {"i": 0}

    async def fake_round(messages, *, tools, system=None, temperature=None, max_tokens=2048):
        i = state["i"]
        state["i"] += 1
        return calls[i] if i < len(calls) else {"content": "Done.", "tool_calls": []}

    return fake_round


# ── Settings ────────────────────────────────────────────────
def test_defaults_are_secure():
    current = command_sandbox.load_settings()
    assert current == {"mode": "enforce", "network": False, "auto_approve": False}


def test_settings_persist_and_validate():
    command_sandbox.update_settings(network=True)
    assert command_sandbox.load_settings()["network"] is True
    assert command_sandbox.load_settings()["mode"] == "enforce"
    with pytest.raises(ValueError):
        command_sandbox.update_settings(mode="yolo")


# ── Planning ────────────────────────────────────────────────
def test_enforce_without_backend_refuses(workspace, fake_backend):
    fake_backend(None, "Install bubblewrap.")
    plan = command_sandbox.plan_for(workspace)
    assert not plan.active
    assert "Install bubblewrap." in plan.refusal


def test_off_mode_runs_unsandboxed_without_refusal(workspace, fake_backend):
    fake_backend(command_sandbox.SEATBELT)
    command_sandbox.update_settings(mode="off")
    plan = command_sandbox.plan_for(workspace)
    assert not plan.active and plan.refusal is None
    assert "full account permissions" in plan.summary()


def test_only_the_containing_workspace_is_writable(tmp_path, monkeypatch):
    outer = tmp_path / "outer"
    inner = outer / "inner"
    other = tmp_path / "other"
    for d in (inner, other):
        d.mkdir(parents=True)
    monkeypatch.setattr(workspace_service, "roots", lambda: [outer, inner, other])
    real = lambda p: Path(os.path.realpath(p))  # noqa: E731
    assert command_sandbox.writable_root_for(inner / ".") == real(inner)
    assert command_sandbox.writable_root_for(outer) == real(outer)
    assert command_sandbox.writable_root_for(tmp_path) is None


def test_bubblewrap_finds_every_repository_in_the_workspace(workspace, fake_backend):
    fake_backend(command_sandbox.BUBBLEWRAP)
    (workspace / ".git").mkdir()
    (workspace / "apps" / "web" / ".git").mkdir(parents=True)
    (workspace / "node_modules" / "dep" / ".git").mkdir(parents=True)
    (workspace / "wt").mkdir()
    (workspace / "wt" / ".git").write_text("gitdir: elsewhere\n")
    plan = command_sandbox.plan_for(workspace / "apps")
    assert set(plan.git_entries) == {
        workspace / ".git", workspace / "apps" / "web" / ".git", workspace / "wt" / ".git",
    }


# ── Profile generation ──────────────────────────────────────
def test_seatbelt_profile_network_off(workspace, fake_backend, tmp_path):
    fake_backend(command_sandbox.SEATBELT)
    plan = command_sandbox.plan_for(workspace)
    profile, params = command_sandbox.seatbelt_profile(plan, tmp_path / "scratch")
    assert "(deny network*)" in profile
    # Paths travel as -D parameters, never inline, so they cannot inject SBPL.
    assert str(workspace) not in profile
    assert str(workspace) in params.values()
    # Last match wins: protections must come after the writable allow-list.
    assert profile.index("(allow file-write*") < profile.index('(regex #"^.*/\\.git/hooks$")')
    assert profile.index("(allow file-write*") < profile.index("(deny file-read* file-write*")
    secrets = [v for k, v in params.items() if k.startswith("SECRET_")]
    assert str(Path(os.path.realpath(Path.home())) / ".ssh") in secrets


def test_seatbelt_profile_network_on_still_blocks_omnidev_api(workspace, fake_backend, tmp_path):
    fake_backend(command_sandbox.SEATBELT)
    command_sandbox.update_settings(network=True)
    plan = command_sandbox.plan_for(workspace)
    profile, params = command_sandbox.seatbelt_profile(plan, tmp_path / "scratch")
    assert "(deny network*)" not in profile
    for port in command_sandbox.api_ports():
        assert f'(remote ip "localhost:{port}")' in profile
    assert os.path.realpath("/var/run/docker.sock") in params.values()


def test_bubblewrap_args(workspace, fake_backend, tmp_path, monkeypatch):
    fake_backend(command_sandbox.BUBBLEWRAP)
    secret_dir = tmp_path / "secret"
    secret_dir.mkdir()
    secret_file = tmp_path / "token"
    secret_file.write_text("x")
    monkeypatch.setattr(command_sandbox, "secret_paths", lambda: [secret_dir, secret_file])
    app = workspace / "group" / "app"
    (app / ".git" / "hooks").mkdir(parents=True)
    (app / ".git" / "config").write_text("[core]\n")
    plan = command_sandbox.plan_for(workspace)
    args = command_sandbox.bubblewrap_args(plan, tmp_path, workspace)
    joined = " ".join(args)
    assert "--unshare-net" in args
    assert f"--bind {workspace} {workspace}" in joined
    hooks = app / ".git" / "hooks"
    # Every directory between the root and the repository is pinned, then
    # .git, then hooks read-only on top.
    order = [
        f"--bind {workspace} {workspace}",
        f"--bind {workspace / 'group'} {workspace / 'group'}",
        f"--bind {app} {app}",
        f"--bind {app / '.git'} {app / '.git'}",
        f"--ro-bind {hooks} {hooks}",
    ]
    positions = [joined.index(item) for item in order]
    assert positions == sorted(positions)
    assert f"--ro-bind {app / '.git' / 'config'} {app / '.git' / 'config'}" in joined
    assert f"--tmpfs {secret_dir}" in joined
    assert f"--ro-bind /dev/null {secret_file}" in joined
    assert args[-1] == "--" and args[-2] == str(workspace)


def test_bubblewrap_mounts_missing_git_metadata_read_only(tmp_path):
    root = tmp_path / "ws"
    git = root / ".git"
    git.mkdir(parents=True)
    joined = " ".join(command_sandbox.bubblewrap_git_mounts(root, [git]))
    assert f"--tmpfs {git / 'hooks'} --remount-ro {git / 'hooks'}" in joined
    assert f"--ro-bind /dev/null {git / 'config'}" in joined


def test_swift_skips_its_nested_sandbox_only_under_seatbelt(workspace, fake_backend):
    fake_backend(command_sandbox.SEATBELT)
    plan = command_sandbox.plan_for(workspace)
    assert command_sandbox.adjust_args("swift", ["build"], plan) == ["build", "--disable-sandbox"]
    assert command_sandbox.adjust_args("swift", ["test", "--disable-sandbox"], plan).count(
        "--disable-sandbox"
    ) == 1
    fake_backend(command_sandbox.BUBBLEWRAP)
    plan = command_sandbox.plan_for(workspace)
    assert command_sandbox.adjust_args("swift", ["build"], plan) == ["build"]


def test_denial_hint_only_for_sandboxed_failures(workspace, fake_backend):
    fake_backend(command_sandbox.SEATBELT)
    plan = command_sandbox.plan_for(workspace)
    assert "[sandbox]" in command_sandbox.denial_hint(plan, 1, "PermissionError: Operation not permitted")
    assert command_sandbox.denial_hint(plan, 0, "Operation not permitted") == ""
    assert command_sandbox.denial_hint(plan, 1, "AssertionError") == ""


# ── Approval flow ───────────────────────────────────────────
def test_commands_ask_unless_auto_approved_in_a_sandboxed_workspace(
    workspace, fake_backend, tmp_path
):
    fake_backend(command_sandbox.SEATBELT)
    inside = {"command": "pytest", "args": [], "cwd": str(workspace)}
    outside = {"command": "pytest", "args": [], "cwd": str(tmp_path)}
    assert agent_tools.needs_approval("run_command", inside)
    command_sandbox.update_settings(auto_approve=True)
    assert not agent_tools.needs_approval("run_command", inside)
    assert agent_tools.needs_approval("run_command", outside)
    # Auto-approval never applies once the sandbox is off.
    command_sandbox.update_settings(mode="off")
    assert agent_tools.needs_approval("run_command", inside)


def test_approval_detail_states_the_sandbox(workspace, fake_backend):
    fake_backend(command_sandbox.SEATBELT)
    args = {"command": "pytest", "args": [], "cwd": str(workspace)}
    _, detail = agent_tools.describe("run_command", args)
    assert "Sandboxed (macOS Seatbelt)" in detail and "network off" in detail
    command_sandbox.update_settings(mode="off")
    _, detail = agent_tools.describe("run_command", args)
    assert "NOT SANDBOXED" in detail


def test_precheck(workspace, fake_backend):
    fake_backend(command_sandbox.SEATBELT)
    assert agent_tools.precheck("run_command", {"command": "rm", "args": [], "cwd": str(workspace)})
    assert agent_tools.precheck("run_command", {"command": "pytest", "args": []})
    assert agent_tools.precheck("run_command", {"command": "pytest", "args": [], "cwd": str(workspace)}) is None
    fake_backend(None)
    assert "unavailable" in agent_tools.precheck(
        "run_command", {"command": "pytest", "args": [], "cwd": str(workspace)}
    )


@pytest.mark.asyncio
async def test_refused_command_never_prompts(workspace, fake_backend, monkeypatch):
    fake_backend(None, "Install bubblewrap.")
    fake = _scripted([
        {"content": "", "tool_calls": [{
            "name": "run_command",
            "arguments": {"command": "pytest", "args": [], "cwd": str(workspace)},
        }]},
    ])
    monkeypatch.setattr(agent_service, "chat_round_with_tools", fake)
    events = [e async for e in agent_service.run_agent("test it", use_mcp=False)]
    assert not any("approval_required" in e for e in events)
    result = next(e["tool_result"] for e in events if "tool_result" in e)
    assert not result["ok"] and "Install bubblewrap." in result["result"]
    started = next(e["agent"] for e in events if "agent" in e)
    assert started["sandbox"]["active"] is False


@pytest.mark.asyncio
async def test_approval_event_carries_sandbox(workspace, fake_backend, monkeypatch):
    fake_backend(command_sandbox.SEATBELT)
    fake = _scripted([
        {"content": "", "tool_calls": [{
            "name": "run_command",
            "arguments": {"command": "pytest", "args": [], "cwd": str(workspace)},
        }]},
    ])
    monkeypatch.setattr(agent_service, "chat_round_with_tools", fake)
    monkeypatch.setattr(agent_service, "APPROVAL_TIMEOUT_SECONDS", 0.05)
    events = [e async for e in agent_service.run_agent("test it", use_mcp=False)]
    approval = next(e["approval_required"] for e in events if "approval_required" in e)
    assert approval["sandbox"]["active"] is True
    assert approval["sandbox"]["writable_root"] == str(workspace)


# ── API ─────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_sandbox_api(client, fake_backend, coverage_tracker):
    fake_backend(command_sandbox.SEATBELT)
    res = await client.get("/api/agent/sandbox")
    assert res.status_code == 200
    body = res.json()
    assert body["active"] and body["mode"] == "enforce" and not body["network"]
    assert "~/.ssh" in body["protected_paths"]
    coverage_tracker("GET /api/agent/sandbox")

    res = await client.post("/api/agent/sandbox", json={"network": True, "auto_approve": True})
    assert res.status_code == 200
    assert res.json()["network"] and res.json()["auto_approve"]
    res = await client.post("/api/agent/sandbox", json={"mode": "off"})
    assert res.json()["active"] is False and "full account permissions" in res.json()["summary"]
    assert (await client.post("/api/agent/sandbox", json={"mode": "nope"})).status_code == 422
    coverage_tracker("POST /api/agent/sandbox")


# ── Real confinement (runs wherever a sandbox works) ────────
def _real_backend() -> str | None:
    command_sandbox.detect_backend.cache_clear()
    backend, _ = command_sandbox.detect_backend()
    return backend


needs_sandbox = pytest.mark.skipif(
    _real_backend() is None, reason="no working OS sandbox on this machine"
)


async def _py(workspace: Path, code: str) -> str:
    return await agent_tools.call_tool(
        "run_command",
        {"command": "python3", "args": ["-c", code], "cwd": str(workspace)},
    )


@pytest.fixture
def home_outside():
    """A directory in the real home folder, outside every workspace."""
    path = Path(tempfile.mkdtemp(prefix="omnidev-sandbox-test-", dir=Path.home()))
    yield Path(os.path.realpath(path))
    shutil.rmtree(path, ignore_errors=True)


@pytest.fixture
def listener():
    servers = []

    def open_port() -> int:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(("127.0.0.1", 0))
        server.listen(4)
        servers.append(server)
        return server.getsockname()[1]

    yield open_port
    for server in servers:
        server.close()


def _connect_code(port: int) -> str:
    return (
        "import socket\n"
        "try:\n"
        f"    socket.create_connection(('127.0.0.1', {port}), timeout=3); print('CONNECTED')\n"
        "except OSError as e:\n"
        "    print('BLOCKED', e)\n"
    )


@needs_sandbox
@pytest.mark.asyncio
async def test_real_sandbox_runs_and_writes_inside_workspace(workspace):
    result = await _py(workspace, "open('made.txt','w').write('ok'); print('hi')")
    assert "exit code 0 (sandboxed)" in result and "hi" in result
    assert (workspace / "made.txt").read_text() == "ok"


@needs_sandbox
@pytest.mark.asyncio
async def test_real_sandbox_blocks_writes_outside_workspace(workspace, home_outside):
    target = home_outside / "escape.txt"
    result = await _py(workspace, f"open({str(target)!r}, 'w').write('x')")
    assert "exit code 0" not in result
    assert not target.exists()


@needs_sandbox
@pytest.mark.asyncio
async def test_real_sandbox_hides_secrets(workspace, home_outside, monkeypatch):
    secret = home_outside / "creds"
    secret.mkdir()
    (secret / "key").write_text("TOP-SECRET-VALUE")
    monkeypatch.setattr(command_sandbox, "secret_paths", lambda: [secret])
    result = await _py(workspace, f"print(open({str(secret / 'key')!r}).read())")
    assert "TOP-SECRET-VALUE" not in result


@needs_sandbox
@pytest.mark.asyncio
async def test_real_sandbox_protects_git_hooks_and_config(workspace):
    hooks = workspace / ".git" / "hooks"
    hooks.mkdir(parents=True)
    (workspace / ".git" / "config").write_text("[core]\n")
    result = await _py(
        workspace,
        "import os\n"
        "for p in ('.git/hooks/pre-commit', '.git/config'):\n"
        "    try:\n"
        "        open(p, 'a').write('evil'); print('WROTE', p)\n"
        "    except OSError as e:\n"
        "        print('BLOCKED', p)\n"
        "try:\n"
        "    os.rename('.git', '.git-moved'); print('MOVED')\n"
        "except OSError:\n"
        "    print('BLOCKED rename')\n",
    )
    assert "WROTE" not in result and "MOVED" not in result, result
    assert not (hooks / "pre-commit").exists()
    assert (workspace / ".git" / "config").read_text() == "[core]\n"


def _git(repo: Path, *args: str) -> None:
    import subprocess

    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def _init_repo(repo: Path) -> None:
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.name", "OmniDev Test")
    _git(repo, "config", "user.email", "test@example.com")


@needs_sandbox
@pytest.mark.skipif(shutil.which("git") is None, reason="needs git")
@pytest.mark.asyncio
async def test_real_sandbox_git_add_and_commit_still_work(workspace):
    _init_repo(workspace)
    (workspace / "a.txt").write_text("a\n")
    for args in (["add", "a.txt"], ["commit", "-q", "-m", "sandboxed commit"]):
        result = await agent_tools.call_tool(
            "run_command", {"command": "git", "args": args, "cwd": str(workspace)}
        )
        assert "exit code 0 (sandboxed)" in result, result
    log = await agent_tools.call_tool(
        "run_command", {"command": "git", "args": ["log", "--oneline"], "cwd": str(workspace)}
    )
    assert "sandboxed commit" in log


@needs_sandbox
@pytest.mark.skipif(shutil.which("git") is None, reason="needs git")
@pytest.mark.asyncio
async def test_real_sandbox_protects_other_repos_and_blocks_planting(workspace):
    app, other = workspace / "app", workspace / "other"
    _init_repo(app)
    _init_repo(other)
    result = await _py(
        app,
        "import os\n"
        f"other = {str(other)!r}\n"
        f"app = {str(app)!r}\n"
        "for p in ('.git/hooks/post-checkout', '.git/config'):\n"
        "    try:\n"
        "        open(os.path.join(other, p), 'a').write('evil'); print('WROTE', p)\n"
        "    except OSError:\n"
        "        print('BLOCKED', p)\n"
        "try:\n"
        "    os.rename(app, app + '-old')\n"
        "except OSError:\n"
        "    pass\n"
        "try:\n"
        "    os.makedirs(os.path.join(app, '.git', 'hooks'), exist_ok=True)\n"
        "    open(os.path.join(app, '.git', 'hooks', 'post-checkout'), 'w').write('evil')\n"
        "    print('PLANTED')\n"
        "except OSError:\n"
        "    print('BLOCKED plant')\n",
    )
    assert "WROTE" not in result and "PLANTED" not in result, result
    assert not (other / ".git" / "hooks" / "post-checkout").exists()


@needs_sandbox
@pytest.mark.skipif(shutil.which("git") is None, reason="needs git")
@pytest.mark.asyncio
async def test_real_sandbox_git_metadata_cannot_be_recreated_or_replaced(workspace):
    _init_repo(workspace)
    shutil.rmtree(workspace / ".git" / "hooks", ignore_errors=True)
    config_before = (workspace / ".git" / "config").read_text()
    result = await _py(
        workspace,
        "import os, shutil\n"
        "def attempt(label, fn):\n"
        "    try:\n"
        "        fn(); print('DID', label)\n"
        "    except OSError:\n"
        "        print('BLOCKED', label)\n"
        "def plant():\n"
        "    os.makedirs('.git/hooks', exist_ok=True)\n"
        "    open('.git/hooks/post-checkout', 'w').write('evil')\n"
        "def replace_config():\n"
        "    open('cfg.tmp', 'w').write('[core]\\n\\thooksPath = /tmp\\n')\n"
        "    os.replace('cfg.tmp', '.git/config')\n"
        "attempt('plant-missing-hook', plant)\n"
        "attempt('replace-config', replace_config)\n"
        "attempt('remove-hooks', lambda: shutil.rmtree('.git/hooks'))\n"
        "attempt('remove-config', lambda: os.remove('.git/config'))\n"
        "attempt('rename-git', lambda: os.rename('.git', '.git-old'))\n",
    )
    assert "DID" not in result, result
    assert not (workspace / ".git" / "hooks" / "post-checkout").exists()
    assert (workspace / ".git" / "config").read_text() == config_before


@needs_sandbox
@pytest.mark.skipif(sys.platform != "darwin", reason="creating new .git is pattern-blocked by Seatbelt only")
@pytest.mark.asyncio
async def test_real_sandbox_blocks_creating_a_repository(workspace):
    result = await _py(
        workspace,
        "import os\n"
        "try:\n"
        "    os.makedirs('.git/hooks'); print('CREATED')\n"
        "except OSError:\n"
        "    print('BLOCKED')\n",
    )
    assert "CREATED" not in result, result
    assert not (workspace / ".git").exists()


@needs_sandbox
@pytest.mark.asyncio
async def test_real_sandbox_network_off_blocks_localhost(workspace, listener):
    result = await _py(workspace, _connect_code(listener()))
    assert "CONNECTED" not in result and "BLOCKED" in result, result


@needs_sandbox
@pytest.mark.skipif(sys.platform != "darwin", reason="API port blocking is Seatbelt-only")
@pytest.mark.asyncio
async def test_real_sandbox_network_on_still_blocks_omnidev_api(workspace, listener, monkeypatch):
    api_port, other_port = listener(), listener()
    monkeypatch.setattr(command_sandbox, "api_ports", lambda: [api_port])
    command_sandbox.update_settings(network=True)
    assert "CONNECTED" in await _py(workspace, _connect_code(other_port))
    blocked = await _py(workspace, _connect_code(api_port))
    assert "CONNECTED" not in blocked and "BLOCKED" in blocked, blocked


@needs_sandbox
@pytest.mark.skipif(
    sys.platform != "darwin" or shutil.which("swift") is None, reason="needs SwiftPM on macOS"
)
@pytest.mark.asyncio
async def test_real_sandbox_swift_build_works_offline(workspace):
    (workspace / "Sources" / "Hello").mkdir(parents=True)
    (workspace / "Package.swift").write_text(
        "// swift-tools-version:5.7\n"
        "import PackageDescription\n"
        'let package = Package(name: "Hello", targets: [.executableTarget(name: "Hello")])\n'
    )
    (workspace / "Sources" / "Hello" / "main.swift").write_text('print("hello")\n')
    result = await agent_tools.call_tool(
        "run_command", {"command": "swift", "args": ["build"], "cwd": str(workspace)}
    )
    assert "exit code 0 (sandboxed)" in result, result
