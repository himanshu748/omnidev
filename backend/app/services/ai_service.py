"""
Provider-agnostic AI helpers for AI-backed services.

Two providers:
- "ollama": a local Ollama server — fully offline, no API key needed.
- "gemini": Google's Gemini API (google-genai SDK, needs GEMINI_API_KEY).

AI_PROVIDER=auto (the default) uses Gemini when GEMINI_API_KEY is set and
falls back to local Ollama otherwise, so OmniDev works out of the box on a
machine with no cloud credentials.
"""

from __future__ import annotations

import asyncio
import base64
import json
from typing import Any

import httpx
from google import genai
from google.genai import types

from app.config import settings

OLLAMA_INSTALL_HINT = (
    "Install Ollama from https://ollama.com, run 'ollama serve', "
    "and pull the models: 'ollama pull {model}'."
)


class AIConfigurationError(ValueError):
    """The active AI provider is missing configuration or unreachable."""


class AIResponseError(ValueError):
    """The model reply could not be parsed into the expected shape."""


# ── Provider selection ──────────────────────────────────────
def get_provider() -> str:
    provider = settings.ai_provider.lower().strip()
    if provider == "auto":
        return "gemini" if settings.gemini_api_key else "ollama"
    if provider not in {"gemini", "ollama"}:
        raise AIConfigurationError(
            f"Unknown AI_PROVIDER {settings.ai_provider!r}. Use 'auto', 'gemini', or 'ollama'."
        )
    return provider


def get_model(*, vision: bool = False) -> str:
    if get_provider() == "gemini":
        return settings.gemini_model
    return settings.ollama_vision_model if vision else settings.ollama_model


def ensure_ai_configured() -> None:
    """Raise AIConfigurationError when the active provider cannot possibly work."""
    if get_provider() == "gemini" and not settings.gemini_api_key:
        raise AIConfigurationError(
            "GEMINI_API_KEY is not set. Get a free key at https://aistudio.google.com/apikey, "
            "or set AI_PROVIDER=ollama to run fully offline with a local Ollama server."
        )


# ── Gemini client ───────────────────────────────────────────
_client: genai.Client | None = None


def get_client() -> genai.Client:
    global _client
    if _client is None:
        api_key = settings.gemini_api_key
        if not api_key:
            raise AIConfigurationError(
                "GEMINI_API_KEY is not set. Get a free key at https://aistudio.google.com/apikey, "
                "or set AI_PROVIDER=ollama to run fully offline."
            )
        _client = genai.Client(api_key=api_key)
    return _client


_GEMINI_TYPE_MAP = {
    "object": "OBJECT",
    "array": "ARRAY",
    "string": "STRING",
    "number": "NUMBER",
    "integer": "INTEGER",
    "boolean": "BOOLEAN",
}


def _to_gemini_schema(schema: dict[str, Any]) -> types.Schema:
    """Convert a plain JSON-schema dict into a Gemini types.Schema."""
    kwargs: dict[str, Any] = {}
    if "type" in schema:
        kwargs["type"] = _GEMINI_TYPE_MAP[str(schema["type"]).lower()]
    if "description" in schema:
        kwargs["description"] = schema["description"]
    if "enum" in schema:
        kwargs["enum"] = list(schema["enum"])
    if "required" in schema:
        kwargs["required"] = list(schema["required"])
    if schema.get("properties"):
        kwargs["properties"] = {
            key: _to_gemini_schema(value) for key, value in schema["properties"].items()
        }
    if schema.get("items"):
        kwargs["items"] = _to_gemini_schema(schema["items"])
    return types.Schema(**kwargs)


# ── Ollama client ───────────────────────────────────────────
async def _ollama_chat(
    messages: list[dict[str, Any]],
    *,
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int = 2048,
    format_schema: dict[str, Any] | None = None,
) -> dict[str, Any]:
    model = model or settings.ollama_model
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"num_predict": max_tokens},
    }
    if temperature is not None:
        payload["options"]["temperature"] = temperature
    if format_schema is not None:
        payload["format"] = format_schema

    url = settings.ollama_base_url.rstrip("/") + "/api/chat"
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(600.0, connect=10.0)) as client:
            resp = await client.post(url, json=payload)
    except httpx.HTTPError as exc:
        raise AIConfigurationError(
            f"Cannot reach Ollama at {settings.ollama_base_url}. "
            + OLLAMA_INSTALL_HINT.format(model=model)
        ) from exc

    if resp.status_code == 404:
        raise AIConfigurationError(
            f"Ollama model {model!r} is not available locally. Run 'ollama pull {model}'."
        )
    if resp.status_code >= 400:
        detail = ""
        try:
            detail = resp.json().get("error", "")
        except Exception:
            detail = resp.text[:200]
        raise AIResponseError(f"Ollama request failed ({resp.status_code}): {detail}")
    return resp.json()


def _ollama_messages(system: str | None, prompt: str) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    return messages


def _ollama_tokens(data: dict[str, Any]) -> int | None:
    total = int(data.get("prompt_eval_count") or 0) + int(data.get("eval_count") or 0)
    return total or None


# ── Text generation ─────────────────────────────────────────
async def generate_text(
    prompt: str,
    *,
    system: str | None = None,
    temperature: float | None = None,
    max_tokens: int = 2048,
) -> str:
    """Simple text generation (no tools) via the active provider."""
    if get_provider() == "ollama":
        data = await _ollama_chat(
            _ollama_messages(system, prompt),
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return (data.get("message") or {}).get("content", "") or ""

    config = types.GenerateContentConfig(
        max_output_tokens=max_tokens,
        system_instruction=system,
    )
    if temperature is not None:
        config.temperature = temperature

    response = await asyncio.to_thread(
        get_client().models.generate_content,
        model=settings.gemini_model,
        contents=prompt,
        config=config,
    )
    return response.text or ""


# ── Structured generation ───────────────────────────────────
async def generate_structured(
    prompt: str,
    *,
    system: str | None = None,
    schema: dict[str, Any],
    tool_name: str,
    tool_description: str = "",
    max_tokens: int = 4096,
) -> dict[str, Any]:
    """
    Generate a JSON object matching `schema` (a plain JSON-schema dict).

    Gemini: forced function calling. Ollama: structured outputs (`format`).
    Raises AIResponseError when the reply cannot be parsed into a dict.
    """
    if get_provider() == "ollama":
        data = await _ollama_chat(
            _ollama_messages(system, prompt),
            max_tokens=max_tokens,
            format_schema=schema,
        )
        content = (data.get("message") or {}).get("content", "") or ""
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            raise AIResponseError(
                f"Local model reply for {tool_name!r} was not valid JSON."
            ) from exc
        if not isinstance(parsed, dict):
            raise AIResponseError(f"Local model reply for {tool_name!r} was not a JSON object.")
        return parsed

    tool = types.FunctionDeclaration(
        name=tool_name,
        description=tool_description or f"Return the {tool_name} payload.",
        parameters=_to_gemini_schema(schema),
    )
    config = types.GenerateContentConfig(
        max_output_tokens=max_tokens,
        system_instruction=system,
        tools=[types.Tool(function_declarations=[tool])],
        tool_config=types.ToolConfig(
            function_calling_config=types.FunctionCallingConfig(
                mode="ANY",
                allowed_function_names=[tool_name],
            )
        ),
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )
    response = await asyncio.to_thread(
        get_client().models.generate_content,
        model=settings.gemini_model,
        contents=prompt,
        config=config,
    )
    try:
        return extract_function_call(response, tool_name)
    except ValueError:
        raw = get_response_text(response)
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise AIResponseError(
                f"Gemini reply did not include a {tool_name!r} call or valid JSON."
            ) from exc
        if not isinstance(parsed, dict):
            raise AIResponseError(f"Gemini reply for {tool_name!r} was not a JSON object.")
        return parsed


# ── Vision ──────────────────────────────────────────────────
async def analyze_image_bytes(
    prompt: str,
    image_bytes: bytes,
    content_type: str,
    *,
    max_tokens: int = 2048,
) -> dict[str, Any]:
    """Analyze an image with the active provider. Returns result/model/tokens_used."""
    if get_provider() == "ollama":
        encoded = base64.b64encode(image_bytes).decode("ascii")
        data = await _ollama_chat(
            [{"role": "user", "content": prompt, "images": [encoded]}],
            model=settings.ollama_vision_model,
            max_tokens=max_tokens,
        )
        return {
            "result": (data.get("message") or {}).get("content", "") or "",
            "model": settings.ollama_vision_model,
            "tokens_used": _ollama_tokens(data),
        }

    image_part = types.Part.from_bytes(data=image_bytes, mime_type=content_type)
    response = await asyncio.to_thread(
        get_client().models.generate_content,
        model=settings.gemini_model,
        contents=[prompt, image_part],
        config=types.GenerateContentConfig(max_output_tokens=max_tokens),
    )
    return {
        "result": get_response_text(response),
        "model": settings.gemini_model,
        "tokens_used": total_tokens_used(response),
    }


# ── Gemini response helpers ─────────────────────────────────
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
