"""
OmniDev — All-in-One AI Developer Platform
FastAPI entry point with lifespan-managed Playwright browser.
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
import logging
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from playwright.async_api import async_playwright, Playwright, Browser

from app.config import settings
from app.routers import (
    chat,
    codegen,
    devops,
    git,
    knowledge,
    mcp,
    models,
    scraper,
    storage,
    vision,
)
from app.services.ai_service import close_ai_clients
from app.services.mcp_client_service import shutdown_manager as shutdown_mcp

logger = logging.getLogger(__name__)

PLAYWRIGHT_STARTUP_TIMEOUT_SECONDS = 12


async def _start_playwright_browser() -> tuple[Playwright, Browser]:
    pw = await async_playwright().start()
    try:
        browser = await pw.chromium.launch(headless=True)
    except Exception:
        await pw.stop()
        raise
    return pw, browser


# ── Lifespan ────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Start Playwright browser once; share it across requests via app.state."""
    pw: Playwright | None = None
    browser: Browser | None = None
    try:
        pw, browser = await asyncio.wait_for(
            _start_playwright_browser(),
            timeout=PLAYWRIGHT_STARTUP_TIMEOUT_SECONDS,
        )
    except Exception as exc:
        logger.warning(
            "Playwright browser failed to start; scraper endpoints will return 503. Error: %s",
            exc,
        )
    app.state.playwright = pw
    app.state.browser = browser
    yield
    # During dev shutdown, transports can already be closed; ignore cleanup races.
    if browser is not None:
        try:
            await browser.close()
        except Exception:
            pass
    if pw is not None:
        try:
            await pw.stop()
        except Exception:
            pass
    try:
        await close_ai_clients()
    except Exception:
        pass
    try:
        await shutdown_mcp()
    except Exception:
        pass


# ── App ─────────────────────────────────────────────────────
app = FastAPI(
    title="OmniDev",
    description="All-in-One AI Developer Platform",
    version="0.3.0",
    lifespan=lifespan,
)

# Loopback-only guard: refuse non-loopback clients unless explicitly allowed.
# The API is unauthenticated and may hold cloud credentials, so this fails safe
# if the backend is ever bound to a routable interface by mistake.
_LOOPBACK_HOSTS = {"127.0.0.1", "::1", "::ffff:127.0.0.1"}


@app.middleware("http")
async def _loopback_only(request, call_next):
    if not settings.allow_remote_clients:
        client = request.client.host if request.client else None
        if client not in _LOOPBACK_HOSTS:
            from fastapi.responses import JSONResponse

            return JSONResponse(
                status_code=403,
                content={
                    "detail": "OmniDev's API is loopback-only. Set ALLOW_REMOTE_CLIENTS=1 "
                    "to allow remote access (not recommended — the API has no authentication)."
                },
            )
    return await call_next(request)


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ─────────────────────────────────────────────────
app.include_router(devops.router, prefix="/api/devops", tags=["DevOps Agent"])
app.include_router(scraper.router, prefix="/api/scraper", tags=["Web Scraper"])
app.include_router(vision.router, prefix="/api/vision", tags=["Vision Lab"])
app.include_router(storage.router, prefix="/api/storage", tags=["Cloud Storage"])
app.include_router(codegen.router, prefix="/api/codegen", tags=["Code Gen"])
app.include_router(models.router, prefix="/api/models", tags=["Models"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(git.router, prefix="/api/git", tags=["Git Landing"])
app.include_router(mcp.router, prefix="/api/mcp", tags=["MCP Marketplace"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["Knowledge"])


# ── Health ──────────────────────────────────────────────────
@app.get("/health", tags=["System"])
async def health():
    from app.services.ai_service import AIConfigurationError, get_model, get_provider

    try:
        ai_provider = get_provider()
        ai_model = get_model()
    except AIConfigurationError:
        ai_provider = "unconfigured"
        ai_model = ""
    return {
        "status": "ok",
        "service": "omnidev",
        "ai_provider": ai_provider,
        "ai_model": ai_model,
    }
