"""Tests for the OmniDev MCP server (app/mcp) — the stdio bridge to the backend."""

import json
import os
import pathlib
import subprocess
import sys
import threading

import httpx
import pytest
import pytest_asyncio
from contextlib import asynccontextmanager

from app.mcp import server as mcp_server
from app.mcp.server import FileInput

BACKEND_DIR = pathlib.Path(__file__).resolve().parents[1]


def _mock_client(handler):
    transport = httpx.MockTransport(handler)
    return httpx.AsyncClient(
        transport=transport, base_url="http://test", timeout=mcp_server.REQUEST_TIMEOUT
    )


def _use_handler(monkeypatch, handler):
    async def fake_client():
        return _mock_client(handler)

    monkeypatch.setattr(mcp_server, "_client", fake_client)


# ── local_llm ───────────────────────────────────────────────
@pytest.mark.asyncio
async def test_local_llm_concatenates_stream(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/chat/stream"
        body = json.loads(request.content)
        assert body["message"] == "write a haiku"
        ndjson = b'{"delta": "Local "}\n{"delta": "leaves fall"}\n{"done": true}\n'
        return httpx.Response(200, content=ndjson)

    _use_handler(monkeypatch, handler)
    result = await mcp_server.local_llm("write a haiku")
    assert result == "Local leaves fall"


@pytest.mark.asyncio
async def test_local_llm_surfaces_stream_error(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b'{"error": "Ollama is not reachable"}\n')

    _use_handler(monkeypatch, handler)
    with pytest.raises(RuntimeError, match="Ollama is not reachable"):
        await mcp_server.local_llm("hi")


@pytest.mark.asyncio
async def test_local_llm_surfaces_http_detail(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"detail": "No AI provider is configured."})

    _use_handler(monkeypatch, handler)
    with pytest.raises(RuntimeError, match="No AI provider is configured."):
        await mcp_server.local_llm("hi")


@pytest.mark.asyncio
async def test_local_llm_unreachable_backend_message(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused")

    _use_handler(monkeypatch, handler)
    with pytest.raises(RuntimeError, match="stopped responding|not reachable"):
        await mcp_server.local_llm("hi")


# ── aws_plan ────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_aws_plan_calls_plan_endpoint_only(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/devops/plan", "aws_plan must never hit /command"
        return httpx.Response(
            200,
            json={
                "action": "stop_ec2",
                "params": {"instance_ids": ["i-123"]},
                "plan": {"service": "ec2", "operation": "stop_instances", "destructive": True},
                "summary": "Plan preview for stop_ec2. Nothing was executed.",
            },
        )

    _use_handler(monkeypatch, handler)
    result = json.loads(await mcp_server.aws_plan("stop instance i-123"))
    assert result["plan"]["destructive"] is True
    assert "Nothing was executed" in result["summary"]


# ── local_vision ────────────────────────────────────────────
@pytest.mark.asyncio
async def test_local_vision_uploads_image(monkeypatch, tmp_path):
    image = tmp_path / "shot.png"
    image.write_bytes(b"\x89PNG fake")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/vision/analyze"
        assert b"image/png" in request.content
        return httpx.Response(200, json={"mode": "analyze", "result": "a terminal window"})

    _use_handler(monkeypatch, handler)
    result = await mcp_server.local_vision(str(image))
    assert result == "a terminal window"


@pytest.mark.asyncio
async def test_local_vision_prompt_implies_custom_mode(monkeypatch, tmp_path):
    image = tmp_path / "shot.png"
    image.write_bytes(b"\x89PNG fake")
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["content"] = request.content
        return httpx.Response(200, json={"mode": "custom", "result": "ok"})

    _use_handler(monkeypatch, handler)
    await mcp_server.local_vision(str(image), prompt="what color is the button?")
    assert b"custom" in seen["content"]


@pytest.mark.asyncio
async def test_local_vision_rejects_missing_and_oversized_files(monkeypatch, tmp_path):
    with pytest.raises(ValueError, match="not found"):
        await mcp_server.local_vision(str(tmp_path / "nope.png"))

    monkeypatch.setattr(mcp_server, "MAX_IMAGE_BYTES", 4)
    big = tmp_path / "big.png"
    big.write_bytes(b"12345")
    with pytest.raises(ValueError, match="limit"):
        await mcp_server.local_vision(str(big))

    weird = tmp_path / "notes.txt"
    weird.write_bytes(b"hello")
    with pytest.raises(ValueError, match="Unsupported image type"):
        await mcp_server.local_vision(str(weird))


# ── scraper ─────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_scrape_url_passes_extract_mode(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/scraper/scrape"
        body = json.loads(request.content)
        assert body["extract"] == "markdown"
        return httpx.Response(200, json={"url": body["url"], "extract": "markdown", "data": "# Hi"})

    _use_handler(monkeypatch, handler)
    result = json.loads(await mcp_server.scrape_url("https://example.com"))
    assert result["data"] == "# Hi"


@pytest.mark.asyncio
async def test_crawl_site_passes_bounds(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/scraper/crawl"
        body = json.loads(request.content)
        assert body["max_pages"] == 3 and body["max_depth"] == 2
        return httpx.Response(200, json={"pages": []})

    _use_handler(monkeypatch, handler)
    result = json.loads(await mcp_server.crawl_site("https://example.com", max_pages=3, max_depth=2))
    assert result["pages"] == []


# ── codegen ─────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_generate_and_refine_round_trip(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        if request.url.path == "/api/codegen/generate":
            assert body["framework"] == "fastapi"
            return httpx.Response(
                200,
                json={"files": [{"path": "main.py", "content": "app = 1"}], "summary": "done"},
            )
        assert request.url.path == "/api/codegen/refine"
        assert body["instruction"] == "add auth"
        assert body["files"][0]["path"] == "main.py"
        return httpx.Response(
            200,
            json={"files": [{"path": "main.py", "content": "app = 2"}], "summary": "refined"},
        )

    _use_handler(monkeypatch, handler)
    generated = json.loads(await mcp_server.generate_project("an api", framework="fastapi"))
    refined = json.loads(
        await mcp_server.refine_project(
            [FileInput(**f) for f in generated["files"]], instruction="add auth"
        )
    )
    assert refined["files"][0]["content"] == "app = 2"


# ── models ──────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_list_models_returns_status_json(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/models"
        return httpx.Response(
            200,
            json={"status": {"provider": "ollama", "reachable": True}, "installed": []},
        )

    _use_handler(monkeypatch, handler)
    result = json.loads(await mcp_server.list_models())
    assert result["status"]["provider"] == "ollama"


@pytest.mark.asyncio
async def test_pull_model_reports_success(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/models/pull"
        ndjson = b'{"status": "downloading"}\n{"status": "success"}\n'
        return httpx.Response(200, content=ndjson)

    _use_handler(monkeypatch, handler)
    assert "pulled successfully" in await mcp_server.pull_model("gemma4:e4b")


@pytest.mark.asyncio
async def test_pull_model_fails_without_success_status(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b'{"status": "downloading"}\n')

    _use_handler(monkeypatch, handler)
    with pytest.raises(RuntimeError, match="without success"):
        await mcp_server.pull_model("gemma4:e4b")


# ── stdio protocol smoke test ───────────────────────────────
def test_mcp_stdio_handshake_lists_tools():
    """Spawn `python -m app.mcp` and speak real JSON-RPC over stdio.

    Keeps stdin open until both responses are read — closing it early (EOF)
    shuts the server down while requests are still in flight.
    """
    messages = [
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "pytest", "version": "0"},
            },
        },
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
    ]
    proc = subprocess.Popen(
        [sys.executable, "-m", "app.mcp"],
        cwd=BACKEND_DIR,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        env={**os.environ, "OMNIDEV_BACKEND_URL": "http://127.0.0.1:1"},
    )
    responses: dict[int, dict] = {}
    try:
        for message in messages:
            proc.stdin.write((json.dumps(message) + "\n").encode())
        proc.stdin.flush()

        def _read():
            for raw in proc.stdout:
                line = raw.decode().strip()
                if not line:
                    continue
                msg = json.loads(line)
                if "id" in msg:
                    responses[msg["id"]] = msg
                if {1, 2} <= set(responses):
                    return

        reader = threading.Thread(target=_read, daemon=True)
        reader.start()
        reader.join(timeout=60)
        proc.stdin.close()
        proc.wait(timeout=10)
    finally:
        proc.kill()

    assert responses[1]["result"]["serverInfo"]["name"] == "omnidev"
    tool_names = {t["name"] for t in responses[2]["result"]["tools"]}
    assert tool_names == {
        "local_llm",
        "local_vision",
        "scrape_url",
        "crawl_site",
        "generate_project",
        "refine_project",
        "aws_plan",
        "search_knowledge",
        "list_knowledge_sources",
        "ask_file",
        "index_folder",
        "list_models",
        "pull_model",
    }


# ── Stateless MCP mounted in the engine ─────────────────────
def _mcp_payloads(body: str):
    """Streamable HTTP answers as JSON or as a single SSE event."""
    import json as _json

    for line in body.splitlines():
        line = line.strip()
        if line.startswith("data:"):
            line = line[5:].strip()
        if line.startswith("{"):
            yield _json.loads(line)


@asynccontextmanager
async def mounted_mcp_client():
    """
    The real app with the MCP session manager running, as in production.

    Deliberately not a fixture: the session manager's cancel scope must be
    entered and exited in the same task, and a pytest-asyncio fixture does
    not guarantee that. base_url is a real loopback address because the MCP
    transport rejects unknown Host headers with 421.
    """
    import httpx

    from app.main import app as real_app
    from app.mcp.server import mcp as mcp_server

    async with mcp_server.session_manager.run():
        transport = httpx.ASGITransport(app=real_app, client=("127.0.0.1", 5555))
        async with httpx.AsyncClient(
            transport=transport, base_url="http://127.0.0.1:5555"
        ) as client:
            yield client


MCP_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}


@pytest.mark.asyncio
async def test_mounted_mcp_surface(monkeypatch):
    """
    End to end over the real app's routes, in one session-manager run.

    The SDK allows run() once per manager instance, so these assertions share
    a single client rather than splitting into separate tests:

    1. /mcp and /mcp/ both answer directly. A Mount would 307 the bare path,
       and MCP clients handle a redirected POST inconsistently.
    2. No session is established, so a cold tools/call works with no prior
       initialize. That is what lets several clients share one engine.
    3. The tools target the port we are actually served on, not a guess of
       8000 or 8010.
    """
    from app.mcp import server as mcp_module

    monkeypatch.setattr(mcp_module, "_resolved_url", None)
    init = {
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                   "clientInfo": {"name": "test", "version": "1"}},
    }

    async with mounted_mcp_client() as client:
        for path in ("/mcp", "/mcp/"):
            resp = await client.post(path, headers=MCP_HEADERS, json=init)
            assert resp.status_code == 200, f"{path} did not answer directly"
            payload = list(_mcp_payloads(resp.text))[0]
            assert payload["result"]["serverInfo"]["name"] == "omnidev"

        # Cold call: no initialize on this request, no session header.
        cold = await client.post(
            "/mcp",
            headers=MCP_HEADERS,
            json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        )

    assert cold.status_code == 200
    assert "mcp-session-id" not in {k.lower() for k in cold.headers}
    names = {t["name"] for t in list(_mcp_payloads(cold.text))[0]["result"]["tools"]}
    assert {"search_knowledge", "ask_file", "local_llm"} <= names
    assert mcp_module._resolved_url == "http://127.0.0.1:5555"


def test_set_backend_url_respects_an_explicit_override(monkeypatch):
    """An operator's OMNIDEV_BACKEND_URL outranks self-detection."""
    from app.mcp import server as mcp_module

    monkeypatch.setattr(mcp_module, "_ENV_URL", "http://example.invalid")
    monkeypatch.setattr(mcp_module, "_resolved_url", "http://example.invalid")
    mcp_module.set_backend_url("http://127.0.0.1:9999")
    assert mcp_module._resolved_url == "http://example.invalid"
