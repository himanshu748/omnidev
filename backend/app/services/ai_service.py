"""
Shared Gemini client helpers for AI-backed services.
Uses Google's free Gemini API (google-genai SDK).
"""

from __future__ import annotations

import json
from typing import Any

from google import genai
from google.genai import types

from app.config import settings

_client: genai.Client | None = None


def get_client() -> genai.Client:
    global _client
    if _client is None:
        api_key = settings.gemini_api_key
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY is not set. Get a free key at https://aistudio.google.com/apikey"
            )
        _client = genai.Client(api_key=api_key)
    return _client


def get_model() -> str:
    return settings.gemini_model


async def generate_text(
    prompt: str,
    *,
    system: str | None = None,
    temperature: float | None = None,
    max_tokens: int = 2048,
) -> str:
    """Simple text generation (no tools)."""
    config = types.GenerateContentConfig(
        max_output_tokens=max_tokens,
        system_instruction=system,
    )
    if temperature is not None:
        config.temperature = temperature

    response = get_client().models.generate_content(
        model=settings.gemini_model,
        contents=prompt,
        config=config,
    )
    return response.text or ""


async def generate_with_tool(
    prompt: str,
    *,
    system: str | None = None,
    tools: list[types.FunctionDeclaration],
    forced_function: str | None = None,
    max_tokens: int = 4096,
) -> types.GenerateContentResponse:
    """Generate content with function-calling tools. Returns raw response."""
    tool_config = None
    if forced_function:
        tool_config = types.ToolConfig(
            function_calling_config=types.FunctionCallingConfig(
                mode="ANY",
                allowed_function_names=[forced_function],
            )
        )

    config = types.GenerateContentConfig(
        max_output_tokens=max_tokens,
        system_instruction=system,
        tools=[types.Tool(function_declarations=tools)],
        tool_config=tool_config,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )

    return get_client().models.generate_content(
        model=settings.gemini_model,
        contents=prompt,
        config=config,
    )


def extract_function_call(response: Any, function_name: str) -> dict[str, Any]:
    """Extract the arguments of a specific function call from a Gemini response."""
    for candidate in getattr(response, "candidates", []):
        for part in getattr(candidate.content, "parts", []):
            fc = getattr(part, "function_call", None)
            if fc and fc.name == function_name:
                return dict(fc.args) if fc.args else {}
    raise ValueError(f"Gemini response did not include function call for {function_name!r}")


def get_response_text(response: Any) -> str:
    """Extract plain text from a Gemini response."""
    return getattr(response, "text", "") or ""


def total_tokens_used(response: Any) -> int | None:
    usage = getattr(response, "usage_metadata", None)
    if usage is None:
        return None
    return int(getattr(usage, "total_token_count", 0) or 0)
