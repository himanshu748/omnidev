import json
import pathlib
import time

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import httpx

from app.config import settings
from app.routers import (
    agent,
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

START_TIME = time.time()
COVERED: set[str] = set()
FAILURES: list[dict[str, str]] = []

EXPECTED_ENDPOINTS = [
    "GET /health",
    "POST /api/devops/command",
    "POST /api/devops/plan",
    "POST /api/scraper/scrape",
    "POST /api/vision/analyze",
    "GET /api/storage/buckets",
    "GET /api/storage/files",
    "POST /api/storage/upload",
    "GET /api/storage/download",
    "DELETE /api/storage/files",
    "POST /api/codegen/generate",
    "GET /api/models",
    "POST /api/models/pull",
    "DELETE /api/models",
    "POST /api/chat/stream",
    "POST /api/codegen/refine",
    "POST /api/scraper/crawl",
    "GET /api/chat/sessions",
    "POST /api/git/land",
    "GET /api/git/status",
    "GET /api/mcp/catalog",
    "GET /api/mcp/servers",
    "POST /api/mcp/servers",
    "POST /api/knowledge/sources",
    "GET /api/knowledge/sources",
    "DELETE /api/knowledge/sources",
    "POST /api/knowledge/search",
    "GET /api/knowledge/status",
    "POST /api/agent/stream",
    "GET /api/agent/workspaces",
    "POST /api/agent/workspaces",
    "DELETE /api/agent/workspaces",
    "POST /api/agent/approvals",
]


def create_app() -> FastAPI:
    app = FastAPI(
        title="OmniDev",
        description="Local-first AI developer cockpit",
        version="0.3.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
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
    app.include_router(agent.router, prefix="/api/agent", tags=["Agent"])
    app.state.browser = object()

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

    return app


@pytest.fixture(autouse=True)
def _isolated_local_data(tmp_path, monkeypatch):
    """Keep chat sessions, MCP config, and git landings out of the real
    ~/.omnidev and ~/OmniDev during tests."""
    monkeypatch.setattr(settings, "data_dir", str(tmp_path / "data"))
    monkeypatch.setattr(settings, "land_root", str(tmp_path / "projects"))


@pytest.fixture(scope="session")
def app() -> FastAPI:
    return create_app()


@pytest_asyncio.fixture
async def client(app: FastAPI):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def coverage_tracker():
    def track(name: str):
        COVERED.add(name)

    return track


def pytest_runtest_logreport(report):
    if report.when == "call" and report.failed:
        FAILURES.append(
            {
                "nodeid": report.nodeid,
                "details": getattr(report, "longreprtext", str(report.longrepr)),
            }
        )


def pytest_sessionfinish(session, exitstatus):
    report_dir = pathlib.Path("test-results")
    report_dir.mkdir(exist_ok=True)
    expected_set = set(EXPECTED_ENDPOINTS)
    covered_set = set(COVERED)
    missing = sorted(expected_set - covered_set)
    coverage_percent = (
        round((len(covered_set) / len(expected_set)) * 100, 2) if expected_set else 100
    )
    report_path = report_dir / "backend-report.json"
    payload = {
        "summary": {
            "tests_collected": session.testscollected,
            "exit_status": exitstatus,
            "duration_seconds": round(time.time() - START_TIME, 3),
        },
        "endpoint_coverage": {
            "covered": sorted(covered_set),
            "missing": missing,
            "coverage_percent": coverage_percent,
            "total_endpoints": len(expected_set),
        },
        "defects": FAILURES,
    }
    report_path.write_text(json.dumps(payload, indent=2))
