"""
Code Gen service — generate website/project code.

Frameworks: Streamlit, React, Next.js, Node/Express, Python/FastAPI, etc.
Context7 is an optional external docs provider. Vercel Sandbox is an optional
external run target mentioned in the returned instructions.
"""

from __future__ import annotations

import json
from typing import Any

from google.genai import types

from app.config import settings
from app.services.ai_service import (
    extract_function_call,
    generate_with_tool,
    get_response_text,
)
from app.services.context7_service import get_context

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

PROJECT_TOOL = types.FunctionDeclaration(
    name="return_project",
    description="Return the generated project files and run instructions.",
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "files": types.Schema(
                type="ARRAY",
                description="List of project files",
                items=types.Schema(
                    type="OBJECT",
                    properties={
                        "path": types.Schema(type="STRING", description="File path"),
                        "content": types.Schema(type="STRING", description="File content"),
                    },
                    required=["path", "content"],
                ),
            ),
            "instructions": types.Schema(
                type="STRING",
                description="Instructions on how to run the project",
            ),
        },
        required=["files", "instructions"],
    ),
)


async def _fetch_docs_for_framework(framework: str, prompt: str) -> str:
    key = framework.lower().replace(" ", "")
    libs = FRAMEWORK_CONTEXT7.get(key)
    if not libs:
        libs = [(key, f"/{key}/{key}")]
    combined = []
    for lib_name, lib_id in libs[:2]:
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
    Uses optional Context7 docs when CONTEXT7_API_KEY is set.
    """
    docs_block = await _fetch_docs_for_framework(framework, prompt)
    system = """You are an expert full-stack developer. Generate a complete, runnable project based on the user's request and the framework they chose.

Rules:
- Create all necessary files (package.json, main entry, components, etc.) for the chosen framework.
- ALWAYS include a .gitignore file appropriate for the framework (node_modules, .env, dist, __pycache__, etc.) so the project is Git-ready.
- If the user's request suggests a hero section, landing page, or background imagery, include a placeholder (e.g. CSS gradient, commented image tag, or a simple SVG/placeholder) that they can replace later.
- Use the provided documentation excerpts when present to follow best practices and correct APIs.
- Return the result by calling the return_project tool. Do not answer in plain text."""

    user = f"Framework: {framework}\n\nUser request: {prompt}\n\n"
    if docs_block:
        user += f"Relevant documentation (use for correct APIs and patterns):\n\n{docs_block}\n\n"
    user += "Generate the project now."

    resp = await generate_with_tool(
        user,
        system=system,
        tools=[PROJECT_TOOL],
        forced_function="return_project",
        max_tokens=8192,
    )

    try:
        data = extract_function_call(resp, "return_project")
    except ValueError:
        raw = get_response_text(resp)
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return {
                "files": [{"path": "README.md", "content": f"# Generated for: {prompt}\n\nParse error. Raw model output:\n\n```\n{raw[:2000]}\n```"}],
                "instructions": "Fix the generation or try again.",
            }
    if not isinstance(data, dict):
        return {
            "files": [{"path": "README.md", "content": f"# Generated for: {prompt}\n\nModel returned an unexpected payload shape."}],
            "instructions": "Fix the generation or try again.",
        }
    files = data.get("files") or []
    instructions = data.get("instructions") or "Run the project with the usual commands for your framework (e.g. npm install && npm run dev, or streamlit run app.py). You can optionally use Vercel Sandbox for a live preview: https://vercel.com/docs/vercel-sandbox"
    return {"files": files, "instructions": instructions}
