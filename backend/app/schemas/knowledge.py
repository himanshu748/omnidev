"""Schemas for the local knowledge index (RAG)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SourceCreateRequest(BaseModel):
    # Ignored for kind="chat" (the chat history is a built-in source).
    path: str = Field(default="", max_length=1024)
    kind: str = Field(default="docs", pattern="^(docs|code|chat)$")


class SourceInfo(BaseModel):
    id: int
    path: str
    kind: str
    added_at: str = ""
    last_indexed_at: str | None = None
    file_count: int = 0
    chunk_count: int = 0


class SourceListResponse(BaseModel):
    sources: list[SourceInfo]


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=4000)
    top_k: int = Field(default=8, ge=1, le=50)
    source_ids: list[int] | None = None


class SearchHit(BaseModel):
    source_id: int
    kind: str
    file_path: str
    snippet: str
    score: float


class SearchResponse(BaseModel):
    results: list[SearchHit]


class IndexStatusResponse(BaseModel):
    running: bool
    source_id: int | None = None
    files_total: int = 0
    files_done: int = 0
    error: str | None = None
