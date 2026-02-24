"""
Code Gen service — generate website/project code using OpenAI with Context7 docs.
Frameworks: Streamlit, React, Next.js, Node/Express, Python/FastAPI, etc.
Output is meant to be run in Vercel Sandbox (instructions returned to user).
"""

from __future__ import annotations

import json
from typing import Any

from openai import AsyncOpenAI

from app.config import settings
from app.services.context7_service import get_context, search_library

_openai = AsyncOpenAI(api_key=settings.openai_api_key)

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
- Output ONLY valid JSON: { "files": [ { "path": "relative/file/path", "content": "full file content" } ], "instructions": "Short steps to run this (e.g. npm install, npm run dev or streamlit run app.py). Mention Vercel Sandbox for live preview and git init / add to GitHub." }
- Create all necessary files (package.json, main entry, components, etc.) for the chosen framework.
- ALWAYS include a .gitignore file appropriate for the framework (node_modules, .env, dist, __pycache__, etc.) so the project is Git-ready.
- If the user's request suggests a hero section, landing page, or background imagery, include a placeholder (e.g. CSS gradient, commented image tag, or a simple SVG/placeholder) that they can replace with a generated image later.
- Use the provided documentation excerpts when present to follow best practices and correct APIs.
- No markdown, no explanation outside JSON. The response must be parseable as JSON only."""
    user = f"Framework: {framework}\n\nUser request: {prompt}\n\n"
    if docs_block:
        user += f"Relevant documentation (use for correct APIs and patterns):\n\n{docs_block}\n\n"
    user += "Generate the project JSON now."

    resp = await _openai.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        max_tokens=4096,
    )
    raw = (resp.choices[0].message.content or "").strip()
    # Strip possible markdown code fence
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {
            "files": [{"path": "README.md", "content": f"# Generated for: {prompt}\n\nParse error. Raw model output:\n\n```\n{raw[:2000]}\n```"}],
            "instructions": "Fix the generation or try again.",
        }
    files = data.get("files") or []
    instructions = data.get("instructions") or "Run the project with the usual commands for your framework (e.g. npm install && npm run dev, or streamlit run app.py). You can use Vercel Sandbox for a live preview: https://vercel.com/docs/vercel-sandbox"
    return {"files": files, "instructions": instructions}


async def generate_background_image(prompt: str) -> str:
    """
    Generate a hero/background image via DALL-E.
    Returns base64-encoded PNG.
    """
    import base64

    resp = await _openai.images.generate(
        model="dall-e-3",
        prompt=f"Abstract, modern hero or background image for a website. {prompt}. Clean, professional, suitable for web use. No text.",
        size="1792x1024",
        quality="standard",
        response_format="b64_json",
        n=1,
    )
    b64 = resp.data[0].b64_json
    return b64 or ""
