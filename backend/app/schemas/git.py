"""Schemas for landing generated projects in a local git repo."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.codegen import FileEntry


class GitLandRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=40, examples=["todo-app"])
    files: list[FileEntry] = Field(..., min_length=1, max_length=40)
    message: str = Field("", max_length=200)


class GitLandResponse(BaseModel):
    path: str
    commit: str = ""
    files_written: int = 0
    message: str = ""


class GitStatusResponse(BaseModel):
    exists: bool
    path: str
    dirty: bool = False
    last_commit: str = ""
