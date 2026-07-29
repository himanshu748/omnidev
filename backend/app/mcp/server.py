"""
OmniDev MCP server.

Exposes the local OmniDev engine (Gemma 4 via Ollama, vision, scraping,
codegen, AWS planning, model management) to Claude Code, Claude Desktop,
Cursor, and any other MCP client over stdio.

This module is a thin bridge: every tool is an HTTP call to the running
FastAPI backend on localhost. It never talks to the cloud, never executes
AWS actions (aws_plan returns the plan only), and never writes files —
generated code is returned to the calling agent as data.

Run with the backend directory on sys.path:

    python -m app.mcp

Configuration:
    OMNIDEV_BACKEND_URL — backend base URL (default: probe 8000, then 8010)
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import httpx
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

# Candidate backend URLs, probed in order at first use. An explicit
# OMNIDEV_BACKEND_URL is authoritative; otherwise try the dev-stack port,
# then the native app's sidecar port.
_ENV_URL = os.environ.get("OMNIDEV_BACKEND_URL")
_CANDIDATE_URLS = (
    [_ENV_URL] if _ENV_URL else ["http://127.0.0.1:8000", "http://127.0.0.1:8010"]
)
_resolved_url: str | None = None


def set_backend_url(url: str) -> None:
    """
    Pin the backend URL instead of probing for it.

    Used when the MCP surface is mounted inside the engine (app/main.py):
    the server IS the backend, so probing fixed ports would be both wasteful
    and wrong whenever the engine runs anywhere other than 8000 or 8010. An
    explicit OMNIDEV_BACKEND_URL still wins, because the operator asked for it.
    """
    global _resolved_url
    if _ENV_URL is None:
        _resolved_url = url


async def _backend_url() -> str:
    """Find the running OmniDev backend, caching the first URL that answers."""
    global _resolved_url
    if _resolved_url:
        return _resolved_url
    for url in _CANDIDATE_URLS:
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(2.0)) as probe:
                resp = await probe.get(url.rstrip("/") + "/health")
            if resp.status_code == 200 and resp.json().get("service") == "omnidev":
                _resolved_url = url
                return url
        except Exception:
            continue
    raise RuntimeError(
        "OmniDev backend is not reachable at "
        + " or ".join(_CANDIDATE_URLS)
        + ". Launch the OmniDev app (or `make backend`) and retry."
    )

# Local generation and model pulls can run for minutes; connect stays short so
# "backend not running" fails fast, reads are unbounded on purpose.
REQUEST_TIMEOUT = httpx.Timeout(connect=5.0, read=None, write=60.0, pool=5.0)

MAX_IMAGE_BYTES = 10 * 1024 * 1024  # mirror the backend's vision cap
IMAGE_CONTENT_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
}

# stateless_http: every HTTP request is independent, with no server-side
# session to create, resume or leak. That is what lets the MCP surface be
# mounted straight into the running backend (see app/main.py) instead of
# spawning a separate stdio process per client, and it means several clients
# can use it at once without coordinating.
mcp = FastMCP(
    "omnidev",
    stateless_http=True,
    json_response=True,
    instructions=(
        "OmniDev runs a local Gemma 4 model and developer tools entirely on "
        "this machine — no cloud calls, no API keys, no cost. Use local_llm "
        "to delegate generation to the free on-device model. aws_plan only "
        "previews AWS actions; execution requires the OmniDev UI."
    ),
)


async def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient(base_url=await _backend_url(), timeout=REQUEST_TIMEOUT)


def _unreachable() -> RuntimeError:
    return RuntimeError(
        "OmniDev backend stopped responding at "
        + (_resolved_url or " / ".join(_CANDIDATE_URLS))
        + ". Launch the OmniDev app (or `make backend`) and retry."
    )


def _http_detail(response: httpx.Response, body: bytes) -> str:
    try:
        detail = json.loads(body).get("detail")
    except Exception:
        detail = None
    return detail or f"OmniDev backend returned HTTP {response.status_code}."


async def _request_json(method: str, path: str, **kwargs) -> dict:
    try:
        async with await _client() as client:
            response = await client.request(method, path, **kwargs)
    except httpx.ConnectError as exc:
        raise _unreachable() from exc
    if not 200 <= response.status_code < 300:
        raise RuntimeError(_http_detail(response, response.content))
    return response.json()


class FileInput(BaseModel):
    """One project file, as returned by generate_project."""

    path: str = Field(..., description="Relative file path, e.g. src/App.tsx")
    content: str


@mcp.tool()
async def local_llm(prompt: str, system: str = "", temperature: float = 0.7) -> str:
    """Generate text with the local Gemma 4 model (via Ollama). Runs fully
    on-device: free, private, no cloud calls. Use this to delegate drafting,
    summarising, or brainstorming work to a local model."""
    payload: dict = {"message": prompt, "temperature": temperature}
    if system:
        payload["system"] = system
    parts: list[str] = []
    try:
        async with await _client() as client:
            async with client.stream("POST", "/api/chat/stream", json=payload) as response:
                if response.status_code != 200:
                    raise RuntimeError(_http_detail(response, await response.aread()))
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    event = json.loads(line)
                    if "delta" in event:
                        parts.append(event["delta"])
                    elif "error" in event:
                        raise RuntimeError(event["error"])
    except httpx.ConnectError as exc:
        raise _unreachable() from exc
    return "".join(parts)


@mcp.tool()
async def local_vision(image_path: str, mode: str = "analyze", prompt: str = "") -> str:
    """Analyze a local image with the on-device vision model. Modes: analyze
    (describe), ocr (extract text), custom (use `prompt`). Passing a prompt
    implies custom mode. Max 10 MB; png/jpeg/webp/gif."""
    path = Path(image_path).expanduser()
    if not path.is_file():
        raise ValueError(f"Image not found: {path}")
    content_type = IMAGE_CONTENT_TYPES.get(path.suffix.lower())
    if content_type is None:
        raise ValueError(
            f"Unsupported image type '{path.suffix}'. "
            f"Allowed: {', '.join(sorted(IMAGE_CONTENT_TYPES))}"
        )
    image_bytes = path.read_bytes()
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise ValueError(f"Image exceeds the {MAX_IMAGE_BYTES // (1024 * 1024)} MB limit.")
    if prompt and mode == "analyze":
        mode = "custom"
    result = await _request_json(
        "POST",
        "/api/vision/analyze",
        files={"image": (path.name, image_bytes, content_type)},
        data={"mode": mode, "prompt": prompt},
    )
    return result.get("result", "")


@mcp.tool()
async def scrape_url(url: str, extract: str = "markdown", wait_seconds: float = 0) -> str:
    """Scrape a URL with the local SSRF-guarded Playwright scraper. Extract
    modes: text, html, markdown, article, links, metadata. Returns the
    extraction result as JSON."""
    result = await _request_json(
        "POST",
        "/api/scraper/scrape",
        json={"url": url, "extract": extract, "wait_seconds": wait_seconds},
    )
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
async def crawl_site(url: str, max_pages: int = 5, max_depth: int = 1) -> str:
    """Shallow same-domain crawl from a start URL (SSRF-guarded, capped at
    10 pages / depth 2 by the backend). Returns JSON pages with url, title,
    excerpt, depth, and status_code."""
    result = await _request_json(
        "POST",
        "/api/scraper/crawl",
        json={"url": url, "max_pages": max_pages, "max_depth": max_depth},
    )
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
async def generate_project(prompt: str, framework: str = "react") -> str:
    """Generate a multi-file project with the local model. Output is validated
    (path/secret/npm-script sanitization) and returned as JSON — nothing is
    written to disk or executed; the caller decides where files land.
    Frameworks: react, next, streamlit, node, express, python, fastapi, vue,
    svelte, astro, remix, solid, sveltekit, django, flask, go, html."""
    result = await _request_json(
        "POST",
        "/api/codegen/generate",
        json={"prompt": prompt, "framework": framework},
    )
    return json.dumps(result, indent=2)


@mcp.tool()
async def refine_project(files: list[FileInput], instruction: str, framework: str = "react") -> str:
    """Iterate on a previously generated project: apply a natural-language
    instruction to the given files and return the modified, re-validated file
    set as JSON. Nothing is written to disk or executed."""
    result = await _request_json(
        "POST",
        "/api/codegen/refine",
        json={
            "files": [{"path": f.path, "content": f.content} for f in files],
            "instruction": instruction,
            "framework": framework,
        },
    )
    return json.dumps(result, indent=2)


@mcp.tool()
async def aws_plan(command: str) -> str:
    """Preview the boto3 plan for a natural-language AWS command. NEVER
    executes anything — not even read-only calls. Returns JSON with service,
    operation, params, destructive/read_only flags, impact, and scope.
    Applying a plan requires the OmniDev UI and its confirmation flow."""
    result = await _request_json("POST", "/api/devops/plan", json={"message": command})
    return json.dumps(result, indent=2)


@mcp.tool()
async def search_knowledge(query: str, top_k: int = 8) -> str:
    """Search the user's local knowledge index (their indexed docs, code and
    chat history) and return the best-matching excerpts as JSON with file
    paths and scores. Fully local: the index and the embedding model live on
    this machine. Use this to ground answers in the user's own files."""
    result = await _request_json(
        "POST", "/api/knowledge/search", json={"query": query, "top_k": top_k}
    )
    return json.dumps(result, indent=2)


@mcp.tool()
async def ask_file(path: str, question: str) -> str:
    """Pull the parts of ONE local file that answer a question, without
    indexing it. Works on any readable file on this Mac, including images and
    screenshots (on-device OCR), PDFs, Office and iWork documents. Nothing is
    stored. Use this when the user points at a specific file."""
    result = await _request_json(
        "POST", "/api/knowledge/ask-file", json={"path": path, "question": question}
    )
    excerpts = result.get("excerpts") or []
    header = f"{result.get('file_path', path)}"
    if result.get("truncated"):
        header += " (most relevant excerpts)"
    return header + "\n\n" + "\n\n---\n\n".join(excerpts)


@mcp.tool()
async def list_knowledge_sources() -> str:
    """List the folders (and built-in chat history) registered in the local
    knowledge index, with file and chunk counts. Returns JSON."""
    result = await _request_json("GET", "/api/knowledge/sources")
    return json.dumps(result, indent=2)


@mcp.tool()
async def index_folder(path: str, kind: str = "") -> str:
    """Register a local folder in the knowledge index and start indexing it
    in the background. `kind` is docs or code; when omitted it is guessed
    from the folder contents. Poll progress via the OmniDev app or re-call
    search_knowledge once indexing settles."""
    if not kind:
        folder = Path(path).expanduser()
        code_markers = {".git", "package.json", "pyproject.toml", "Cargo.toml", "go.mod"}
        kind = "code" if any((folder / m).exists() for m in code_markers) else "docs"
    result = await _request_json(
        "POST", "/api/knowledge/sources", json={"path": path, "kind": kind}
    )
    return json.dumps(result, indent=2)


@mcp.tool()
async def list_models() -> str:
    """List the AI provider status plus installed and recommended local
    models. Returns JSON."""
    result = await _request_json("GET", "/api/models")
    return json.dumps(result, indent=2)


@mcp.tool()
async def pull_model(name: str) -> str:
    """Pull a local Ollama model (e.g. gemma4:12b). Blocks until the download
    finishes; may take several minutes on first pull."""
    last_status = ""
    try:
        async with await _client() as client:
            async with client.stream("POST", "/api/models/pull", json={"name": name}) as response:
                if response.status_code != 200:
                    raise RuntimeError(_http_detail(response, await response.aread()))
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    event = json.loads(line)
                    if "error" in event:
                        raise RuntimeError(event["error"])
                    last_status = event.get("status", last_status)
    except httpx.ConnectError as exc:
        raise _unreachable() from exc
    if last_status != "success":
        raise RuntimeError(f"Model pull ended without success (last status: {last_status or 'none'}).")
    return f"Model '{name}' pulled successfully."
