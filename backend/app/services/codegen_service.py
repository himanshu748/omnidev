"""
Code Gen service — generate website/project code with Context7 docs.
Frameworks: Streamlit, React, Next.js, Node/Express, Python/FastAPI, etc.
Output is meant to be run in Vercel Sandbox (instructions returned to user).
"""

from __future__ import annotations

import json
from typing import Any

from app.config import settings
from app.services.anthropic_service import (
    extract_text_from_message,
    extract_tool_input,
    get_claude_client,
)
from app.services.context7_service import get_context

_claude = get_claude_client()

# Map our framework key to Context7 library search names and IDs (fallback if no API key)
FRAMEWORK_CONTEXT7: dict[str, list[tuple[str, str]]] = {
    "react": [("react", "/facebook/react"), ("next.js", "/vercel/next.js")],
    "next": [("next.js", "/vercel/next.js")],
    "nextjs": [("next.js", "/vercel/next.js")],
    "streamlit": [("streamlit", "/streamlit/streamlit")],
    "node": [("express", "/expressjs/express")],
    "express": [("express", "/expressjs/express")],
    "python": [("fastapi", "/tiangolo/fastapi")],
    "fastapi": [("fastapi", "/tiangolo/fastapi")],
    "vue": [("vue", "/vuejs/core")],
    "svelte": [("svelte", "/sveltejs/svelte")],
}

PROJECT_TOOL = {
    "name": "return_project",
    "description": "Return the generated project files and run instructions.",
    "input_schema": {
        "type": "object",
        "properties": {
            "files": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "content": {"type": "string"},
                    },
                    "required": ["path", "content"],
                    "additionalProperties": False,
                },
            },
            "instructions": {"type": "string"},
        },
        "required": ["files", "instructions"],
        "additionalProperties": False,
    },
}


async def _fetch_docs_for_framework(framework: str, prompt: str) -> str:
    """Fetch Context7 docs for the given framework and user prompt. Returns combined text."""
    key = framework.lower().replace(" ", "")
    libs = FRAMEWORK_CONTEXT7.get(key)
    if not libs:
        libs = [(key, f"/{key}/{key}")]
    combined = []
    for lib_name, lib_id in libs[:2]:  # at most 2 libs
        try:
            ctx = await get_context(lib_id, prompt, as_text=True)
            if ctx:
                combined.append(f"--- Docs for {lib_name} ---\n{ctx[:8000]}")
        except Exception:
            pass
    return "\n\n".join(combined) if combined else ""


async def generate_project(prompt: str, framework: str) -> dict[str, Any]:
    """
    Generate a full project (multiple files) for the given prompt and framework.
    Uses Context7 docs when CONTEXT7_API_KEY is set. Returns { files: [{ path, content }], instructions }.
    """
    docs_block = await _fetch_docs_for_framework(framework, prompt)
    system = """You are an expert full-stack developer. Generate a complete, runnable project based on the user's request and the framework they chose.

Rules:
- Create all necessary files (package.json, main entry, components, etc.) for the chosen framework.
- ALWAYS include a .gitignore file appropriate for the framework (node_modules, .env, dist, __pycache__, etc.) so the project is Git-ready.
- If the user's request suggests a hero section, landing page, or background imagery, include a placeholder (e.g. CSS gradient, commented image tag, or a simple SVG/placeholder) that they can replace later.
- Use the provided documentation excerpts when present to follow best practices and correct APIs.
- Return the result by calling the provided tool. Do not answer in plain text."""
    user = f"Framework: {framework}\n\nUser request: {prompt}\n\n"
    if docs_block:
        user += f"Relevant documentation (use for correct APIs and patterns):\n\n{docs_block}\n\n"
    user += "Generate the project now."

    resp = await _claude.messages.create(
        model=settings.anthropic_model,
        system=system,
        messages=[{"role": "user", "content": user}],
        max_tokens=8192,
        tools=[PROJECT_TOOL],
        tool_choice={"type": "tool", "name": PROJECT_TOOL["name"]},
    )

    try:
        data = extract_tool_input(resp, PROJECT_TOOL["name"])
    except ValueError:
        raw = extract_text_from_message(resp)
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return {
                "files": [{"path": "README.md", "content": f"# Generated for: {prompt}\n\nParse error. Raw model output:\n\n```\n{raw[:2000]}\n```"}],
                "instructions": "Fix the generation or try again.",
            }
    if not isinstance(data, dict):
        return {
            "files": [{"path": "README.md", "content": f"# Generated for: {prompt}\n\nClaude returned an unexpected payload shape."}],
            "instructions": "Fix the generation or try again.",
        }
    files = data.get("files") or []
    instructions = data.get("instructions") or "Run the project with the usual commands for your framework (e.g. npm install && npm run dev, or streamlit run app.py). You can use Vercel Sandbox for a live preview: https://vercel.com/docs/vercel-sandbox"
    return {"files": files, "instructions": instructions}
