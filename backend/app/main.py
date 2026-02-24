"""
OmniDev — All-in-One AI Developer Platform
FastAPI entry point with lifespan-managed Playwright browser.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from playwright.async_api import async_playwright, Playwright, Browser

from app.config import settings
from app.routers import codegen, devops, location, preview, rag, scraper, storage, vision


# ── Lifespan ────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Start Playwright browser once; share it across requests via app.state."""
    pw: Playwright = await async_playwright().start()
    browser: Browser = await pw.chromium.launch(headless=True)
    app.state.playwright = pw
    app.state.browser = browser
    yield
    # During dev shutdown, transports can already be closed; ignore cleanup races.
    try:
        await browser.close()
    except Exception:
        pass
    try:
        await pw.stop()
    except Exception:
        pass


# ── App ─────────────────────────────────────────────────────
app = FastAPI(
    title="OmniDev",
    description="All-in-One AI Developer Platform",
    version="0.1.0",
    lifespan=lifespan,
)

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
app.include_router(location.router, prefix="/api/location", tags=["Location Services"])
app.include_router(rag.router, prefix="/api/rag", tags=["RAG Chatbot"])
app.include_router(codegen.router, prefix="/api/codegen", tags=["Code Gen"])
app.include_router(preview.router, prefix="/api/preview", tags=["Site Preview"])


# ── Health ──────────────────────────────────────────────────
@app.get("/health", tags=["System"])
async def health():
    return {"status": "ok", "service": "omnidev"}
