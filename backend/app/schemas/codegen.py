"""Schemas for the Code Gen module."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CodeGenRequest(BaseModel):
    prompt: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="What to build (e.g. 'A todo app with dark mode')",
    )
    framework: str = Field(
        "react",
        min_length=1,
        max_length=32,
        description="Framework: react, next, nextjs, streamlit, node, express, python, fastapi, vue, svelte",
    )


class FileEntry(BaseModel):
    path: str = Field(..., min_length=1, max_length=160)
    content: str = Field(..., max_length=200_000)


class CodeGenResponse(BaseModel):
    files: list[FileEntry]
    instructions: str = ""
