"""
Local model management for the Ollama provider.

Lets the cockpit and the native macOS app see which models are installed,
pull new ones with live progress, and know whether the configured default
model is ready — so OmniDev can guide a first-run user to a working offline
setup without dropping to a terminal.
"""

from __future__ import annotations

import json
import re
from typing import Any, AsyncIterator

import httpx

from app.config import settings
from app.services.ai_service import (
    AIConfigurationError,
    OLLAMA_INSTALL_HINT,
    _get_ollama_client,
    get_provider,
)

# A model reference is `name[:tag]`, optionally namespaced (`library/name`) or
# from a registry host (`host/ns/name:tag`). Keep it strict so a bad value is
# rejected before it ever reaches Ollama.
_MODEL_REF = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._/-]{0,127}(?::[a-zA-Z0-9._-]{1,64})?$")

# Curated picks OmniDev recommends, matched to what each module needs.
RECOMMENDED_MODELS: list[dict[str, Any]] = [
    {
        "name": "gemma4:12b",
        "label": "Gemma 4 12B",
        "size_gb": 7.6,
        "roles": ["text", "structured", "vision"],
        "note": "Default. Encoder-free multimodal, 256K context, the best coding of the laptop tiers.",
        "recommended": True,
    },
    {
        "name": "gemma4:e4b",
        "label": "Gemma 4 E4B",
        "size_gb": 9.6,
        "roles": ["text", "structured", "vision", "audio"],
        "note": "Edge model with native audio input. Google's edge model from AI Edge Gallery.",
        "recommended": False,
    },
    {
        "name": "gemma4:e2b",
        "label": "Gemma 4 E2B",
        "size_gb": 5.5,
        "roles": ["text", "structured", "vision"],
        "note": "Lighter Gemma 4 for lower-memory Macs. Same capabilities, smaller footprint.",
        "recommended": False,
    },
    {
        "name": "qwen2.5-coder:7b",
        "label": "Qwen2.5 Coder 7B",
        "size_gb": 4.7,
        "roles": ["text", "structured"],
        "note": "Stronger code generation. Pair as OLLAMA_MODEL for the Code Gen module.",
        "recommended": False,
    },
    {
        "name": "llama3.2:3b",
        "label": "Llama 3.2 3B",
        "size_gb": 2.0,
        "roles": ["text", "structured"],
        "note": "Fast and tiny for DevOps intent parsing on constrained machines.",
        "recommended": False,
    },
]


def _require_ollama() -> None:
    if get_provider() != "ollama":
        raise AIConfigurationError(
            "Model management is only available for the local Ollama provider. "
            "Set AI_PROVIDER=ollama (or unset GEMINI_API_KEY) to manage local models."
        )


def validate_model_ref(name: str) -> str:
    name = (name or "").strip()
    if not _MODEL_REF.match(name):
        raise ValueError(f"Invalid model reference: {name!r}")
    return name


async def list_installed() -> list[dict[str, Any]]:
    """Return the models installed in the local Ollama server."""
    _require_ollama()
    url = settings.ollama_base_url.rstrip("/") + "/api/tags"
    try:
        resp = await _get_ollama_client().get(url)
    except httpx.HTTPError as exc:
        raise AIConfigurationError(
            f"Cannot reach Ollama at {settings.ollama_base_url}. "
            + OLLAMA_INSTALL_HINT.format(model=settings.ollama_model)
        ) from exc
    if resp.status_code >= 400:
        raise AIConfigurationError(
            f"Ollama returned {resp.status_code} listing models. Is 'ollama serve' running?"
        )
    data = resp.json()
    models = []
    for m in data.get("models", []):
        size = m.get("size") or 0
        details = m.get("details") or {}
        models.append(
            {
                "name": m.get("name", ""),
                "size_gb": round(size / 1_000_000_000, 2) if size else None,
                "parameter_size": details.get("parameter_size", ""),
                "quantization": details.get("quantization_level", ""),
                "modified_at": m.get("modified_at", ""),
            }
        )
    models.sort(key=lambda x: x["name"])
    return models


async def provider_status() -> dict[str, Any]:
    """
    Report the active provider, configured models, and — for Ollama — whether
    the server is reachable and the default text/vision models are installed.
    """
    provider = get_provider()
    status: dict[str, Any] = {
        "provider": provider,
        "text_model": settings.ollama_model if provider == "ollama" else settings.gemini_model,
        "vision_model": settings.ollama_vision_model if provider == "ollama" else settings.gemini_model,
        "ollama_base_url": settings.ollama_base_url if provider == "ollama" else None,
        "reachable": provider == "gemini",  # gemini reachability is not probed here
        "installed": [],
        "text_model_ready": provider == "gemini",
        "vision_model_ready": provider == "gemini",
    }
    if provider != "ollama":
        return status

    try:
        installed = await list_installed()
    except AIConfigurationError:
        status["reachable"] = False
        return status

    status["reachable"] = True
    status["installed"] = [m["name"] for m in installed]
    names = {m["name"] for m in installed}

    # Ollama reports names with an implicit `:latest`; match a bare ref loosely.
    def _ready(ref: str) -> bool:
        return ref in names or f"{ref}:latest" in names

    status["text_model_ready"] = _ready(settings.ollama_model)
    status["vision_model_ready"] = _ready(settings.ollama_vision_model)
    return status


async def pull_model_events(name: str) -> AsyncIterator[str]:
    """
    Pull a model, yielding newline-delimited JSON progress events from Ollama.

    Each yielded line is a JSON object such as
    {"status": "pulling manifest"} or
    {"status": "downloading", "completed": 12345, "total": 99999}.
    A terminal {"status": "success"} or {"error": "..."} ends the stream.
    """
    _require_ollama()
    name = validate_model_ref(name)
    url = settings.ollama_base_url.rstrip("/") + "/api/pull"
    payload = {"model": name, "stream": True}
    try:
        async with _get_ollama_client().stream("POST", url, json=payload) as resp:
            if resp.status_code >= 400:
                body = (await resp.aread()).decode("utf-8", "ignore")[:200]
                yield json.dumps({"error": f"Ollama pull failed ({resp.status_code}): {body}"}) + "\n"
                return
            async for line in resp.aiter_lines():
                line = line.strip()
                if line:
                    yield line + "\n"
    except httpx.HTTPError as exc:
        yield json.dumps(
            {"error": f"Cannot reach Ollama at {settings.ollama_base_url}: {exc}"}
        ) + "\n"
