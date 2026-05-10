"""
Centralised configuration via environment variables.
Reads from a .env file in the backend/ directory if present.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Optional AI provider: Google Gemini (free tier) ───
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    # ── AWS ─────────────────────────────────────────────────
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_default_region: str = "us-east-1"

    # ── IPInfo ──────────────────────────────────────────────
    ipinfo_token: str = ""

    # ── Optional Context7 docs provider for Code Gen ───────
    context7_api_key: str = ""

    # ── CORS ────────────────────────────────────────────────
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        configured = [o.strip() for o in self.cors_origins.split(",") if o.strip()]
        local_defaults = [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3001",
        ]
        # Keep configured values first, then add missing local dev origins.
        return list(dict.fromkeys([*configured, *local_defaults]))


settings = Settings()
