"""Schemas for the Code Gen module."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CodeGenRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="What to build (e.g. 'A todo app with dark mode')")
    framework: str = Field(
        "react",
        description="Framework: react, next, nextjs, streamlit, node, express, python, fastapi, vue, svelte",
    )


class FileEntry(BaseModel):
    path: str
    content: str


class CodeGenResponse(BaseModel):
    files: list[FileEntry]
    instructions: str = ""
