"""Tests for the git landing service and endpoints."""

from pathlib import Path

import pytest

from app.config import settings
from app.services import git_service
from app.services.git_service import GitLandError, land_project, project_status

FILES = [
    {"path": "index.html", "content": "<h1>Hi</h1>"},
    {"path": "src/app.js", "content": "console.log('hi')"},
]


@pytest.mark.asyncio
async def test_land_creates_repo_and_commits():
    result = await land_project("todo-app", FILES, "first landing")
    project = Path(result["path"])
    assert project.name == "todo-app"
    assert project.parent == Path(settings.land_root).expanduser().resolve()
    assert (project / ".git").is_dir()
    assert (project / "src/app.js").read_text() == "console.log('hi')"
    assert result["commit"]
    assert result["files_written"] == 2

    status = await project_status("todo-app")
    assert status["exists"] is True
    assert status["dirty"] is False
    assert "first landing" in status["last_commit"]


@pytest.mark.asyncio
async def test_land_again_is_idempotent_when_unchanged():
    await land_project("same-app", FILES)
    result = await land_project("same-app", FILES)
    assert "No changes" in result["message"]


@pytest.mark.asyncio
async def test_land_rejects_bad_names():
    for name in ["../escape", "UPPER", "a b", "-lead", "x" * 41, ".hidden"]:
        with pytest.raises(GitLandError):
            await land_project(name, FILES)


@pytest.mark.asyncio
async def test_land_rejects_unsafe_files():
    with pytest.raises(GitLandError):
        await land_project("bad-files", [{"path": "../../evil.sh", "content": "x"}])


@pytest.mark.asyncio
async def test_git_runs_without_secrets_env(monkeypatch):
    """The git env must not inherit backend secrets."""
    captured = {}
    real_run = git_service.subprocess.run

    def spy(cmd, **kwargs):
        captured["env"] = kwargs.get("env")
        return real_run(cmd, **kwargs)

    monkeypatch.setattr(git_service.subprocess, "run", spy)
    await land_project("env-check", FILES)
    env = captured["env"]
    assert "AWS_SECRET_ACCESS_KEY" not in env
    assert "GEMINI_API_KEY" not in env
    assert env["GIT_TERMINAL_PROMPT"] == "0"


# ── endpoints ───────────────────────────────────────────────
@pytest.mark.asyncio
async def test_land_endpoint(client, coverage_tracker):
    resp = await client.post(
        "/api/git/land",
        json={"name": "api-app", "files": FILES, "message": "land via api"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["commit"]
    coverage_tracker("POST /api/git/land")

    status = await client.get("/api/git/status", params={"name": "api-app"})
    assert status.status_code == 200
    assert status.json()["exists"] is True
    coverage_tracker("GET /api/git/status")


@pytest.mark.asyncio
async def test_land_endpoint_rejects_bad_name(client):
    resp = await client.post(
        "/api/git/land", json={"name": "Bad Name", "files": FILES}
    )
    assert resp.status_code == 400
