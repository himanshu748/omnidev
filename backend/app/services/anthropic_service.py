"""
Shared Anthropic client helpers for Claude-backed services.
"""

from __future__ import annotations

from typing import Any

from anthropic import AsyncAnthropic

from app.config import settings

_claude = AsyncAnthropic(api_key=settings.anthropic_api_key)


def get_claude_client() -> AsyncAnthropic:
    return _claude


def extract_text_from_message(message: Any) -> str:
    parts: list[str] = []
    for block in getattr(message, "content", []):
        if getattr(block, "type", None) == "text":
            parts.append(getattr(block, "text", ""))
    return "".join(parts).strip()


def extract_tool_input(message: Any, tool_name: str) -> dict[str, Any]:
    for block in getattr(message, "content", []):
        if getattr(block, "type", None) == "tool_use" and getattr(block, "name", None) == tool_name:
            payload = getattr(block, "input", None)
            if isinstance(payload, dict):
                return payload
            break
    raise ValueError(f"Claude response did not include tool input for {tool_name!r}")


def total_tokens_used(message: Any) -> int | None:
    usage = getattr(message, "usage", None)
    if usage is None:
        return None
    input_tokens = int(getattr(usage, "input_tokens", 0) or 0)
    output_tokens = int(getattr(usage, "output_tokens", 0) or 0)
    return input_tokens + output_tokens
