"""Git landing router — commit generated projects under the landing root."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.git import GitLandRequest, GitLandResponse, GitStatusResponse
from app.services.git_service import GitLandError, land_project, project_status
from app.routers.errors import internal_error

router = APIRouter()


@router.post("/land", response_model=GitLandResponse)
async def land(body: GitLandRequest):
    """
    Write validated generated files into `LAND_ROOT/<name>` and commit them.

    Scoped by construction: strict slug names, the codegen file sanitizer
    re-runs on every file, and git runs with no shell, no hooks, and no
    remotes. Nothing is ever pushed.
    """
    try:
        result = await land_project(
            body.name,
            [{"path": f.path, "content": f.content} for f in body.files],
            body.message,
        )
        return GitLandResponse(**result)
    except GitLandError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise internal_error("Landing the project failed.") from exc


@router.get("/status", response_model=GitStatusResponse)
async def status(name: str):
    """Repo status for a landed project (exists, dirty, last commit)."""
    try:
        result = await project_status(name)
        return GitStatusResponse(**result)
    except GitLandError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise internal_error("Reading project status failed.") from exc
