"""
Centralised configuration via environment variables.
Reads from a .env file in the backend/ directory if present.
"""

from __future__ import annotations

from urllib.parse import urlparse

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── AI provider ─────────────────────────────────────────
    # "auto" uses Gemini when GEMINI_API_KEY is set, otherwise local Ollama.
    ai_provider: str = "auto"  # auto | gemini | ollama

    # ── Google Gemini (cloud, free tier) ────────────────────
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    # ── Ollama (local, fully offline) ───────────────────────
    # gemma4:e4b handles text, structured output, and vision in one model.
    # Use gemma4:e2b on lower-memory machines.
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "gemma4:e4b"
    ollama_vision_model: str = "gemma4:e4b"

    # ── AWS ─────────────────────────────────────────────────
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_default_region: str = "us-east-1"

    # ── DevOps safety ───────────────────────────────────────
    # Read-only mode refuses all destructive AWS actions.
    devops_read_only: bool = False
    # When set, executed DevOps actions are appended as JSON lines.
    audit_log_path: str = ""

    # ── Local data (sessions, MCP config) ───────────────────
    # Chat history and MCP server config live here, outside the repo.
    data_dir: str = "~/.omnidev"
    # Codegen "Land in repo" writes ONLY under this root.
    land_root: str = "~/OmniDev/projects"

    # ── IPInfo ──────────────────────────────────────────────
    ipinfo_token: str = ""

    # ── Context7 (docs for codegen) ─────────────────────────
    context7_api_key: str = ""

    # ── CORS ────────────────────────────────────────────────
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        configured = [
            origin
            for origin in (self._safe_cors_origin(o) for o in self.cors_origins.split(","))
            if origin
        ]
        local_defaults = [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3001",
            # Native macOS app runs the frontend sidecar on 3010.
            "http://localhost:3010",
            "http://127.0.0.1:3010",
        ]
        # Keep configured values first, then add missing local dev origins.
        return list(dict.fromkeys([*configured, *local_defaults]))

    @staticmethod
    def _safe_cors_origin(raw_origin: str) -> str | None:
        origin = raw_origin.strip().rstrip("/")
        if not origin or origin == "*":
            return None
        parsed = urlparse(origin)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return None
        if parsed.path or parsed.params or parsed.query or parsed.fragment:
            return None
        return origin


settings = Settings()
