"""Live agent-mode acceptance run against the real local model.

Plants a failing test in a scratch workspace, asks the agent to fix it, and
auto-approves the shell command so the full read -> edit -> verify loop runs.
"""

import asyncio
import shutil
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path.home() / "n/omnidev/backend"))

from app.config import settings  # noqa: E402

# Keep the real ~/.omnidev/workspaces.json untouched.
settings.data_dir = tempfile.mkdtemp(prefix="omnidev-live-")

from app.services import agent_service, workspace_service  # noqa: E402

WS = Path.home() / "omnidev-agent-livetest"


def setup():
    if WS.exists():
        shutil.rmtree(WS)
    WS.mkdir(parents=True)
    (WS / "calc.py").write_text("def add(a, b):\n    return a - b\n")
    (WS / "test_calc.py").write_text(
        "from calc import add\n\n\ndef test_add():\n    assert add(2, 3) == 5\n"
    )
    workspace_service.add_workspace(str(WS))
    print(f"workspace: {WS}")
    print("planted bug: add() subtracts instead of adding\n")


async def main():
    setup()
    task = (
        f"The test in {WS}/test_calc.py fails. Read {WS}/calc.py, fix the bug so the "
        f"test passes, then run pytest in {WS} to confirm it works."
    )
    t0 = time.time()
    approvals = 0
    tool_calls = []

    async for event in agent_service.run_agent(task, use_mcp=False, max_steps=8):
        kind = next(iter(event))
        if kind == "agent":
            info = event["agent"]
            print(f"[agent] {info['provider']}/{info['model']} tools={len(info['tools'])}")
        elif kind == "step":
            thought = event["step"]["thought"].strip().replace("\n", " ")[:110]
            print(f"[step {event['step']['n']}] {thought}")
        elif kind == "tool_call":
            name = event["tool_call"]["tool"]
            tool_calls.append(name)
            args = str(event["tool_call"]["arguments"])[:100]
            print(f"  -> {name} {args}")
        elif kind == "approval_required":
            approvals += 1
            req = event["approval_required"]
            print(f"  [APPROVAL] {req['summary']}  (auto-allowing)")
            agent_service.resolve_approval(req["id"], "allow_always")
        elif kind == "tool_result":
            res = event["tool_result"]
            mark = "ok" if res["ok"] else "ERR"
            print(f"  <- [{mark}] {res['result'].strip()[:160]}")
        elif kind == "checkpoint":
            print(f"  [checkpoint] {event['checkpoint']}")
        elif kind == "delta":
            print(f"\n[answer] {event['delta'].strip()[:400]}")

    elapsed = time.time() - t0
    source = (WS / "calc.py").read_text()
    print("\n" + "=" * 60)
    print(f"elapsed: {elapsed:.0f}s   tool calls: {tool_calls}   approvals: {approvals}")
    print(f"final calc.py:\n{source}")

    verify = await asyncio.to_thread(
        lambda: __import__("subprocess").run(
            [sys.executable, "-m", "pytest", "-q", str(WS)],
            capture_output=True, text=True, cwd=str(WS), timeout=120,
        )
    )
    passed = verify.returncode == 0
    print(f"independent pytest: {'PASS' if passed else 'FAIL'}")
    print(verify.stdout.strip()[-300:])
    print("RESULT:", "AGENT_FIXED_THE_BUG" if passed else "AGENT_DID_NOT_FIX")


asyncio.run(main())
