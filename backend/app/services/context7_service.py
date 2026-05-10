"""
Optional Context7 integration — fetch up-to-date library docs for code generation.
API: https://context7.com (search libs, get context).
"""

from __future__ import annotations

import httpx

from app.config import settings

CONTEXT7_BASE = "https://context7.com"


async def search_library(library_name: str, query: str) -> list[dict]:
    """Search for a library by name. Returns list of { id, name, description, ... }."""
    if not settings.context7_api_key:
        return []
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{CONTEXT7_BASE}/api/v2/libs/search",
            params={"libraryName": library_name, "query": query},
            headers={"Authorization": f"Bearer {settings.context7_api_key}"},
            timeout=15,
        )
        if resp.status_code != 200:
            return []
        data = resp.json()
        return data if isinstance(data, list) else []


async def get_context(library_id: str, query: str, as_text: bool = True) -> str:
    """
    Get documentation context for a library. Returns plain text (type=txt) for LLM prompts.
    library_id: e.g. "/facebook/react", "/vercel/next.js"
    """
    if not settings.context7_api_key:
        return ""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{CONTEXT7_BASE}/api/v2/context",
            params={"libraryId": library_id, "query": query, "type": "txt" if as_text else "json"},
            headers={"Authorization": f"Bearer {settings.context7_api_key}"},
            timeout=20,
        )
        if resp.status_code != 200:
            return ""
        if as_text:
            return resp.text
        return str(resp.json())
