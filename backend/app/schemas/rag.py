"""Schemas for the RAG Chatbot module."""

from __future__ import annotations

from pydantic import BaseModel, Field


# ── Ingest: add documents to the knowledge base ─────────────────
class RAGIngestRequest(BaseModel):
    """Add text or document chunks to the RAG store."""

    text: str | None = Field(None, description="Single text block to chunk and embed")
    documents: list[str] | None = Field(
        None,
        description="List of text chunks (each will be embedded as-is)",
    )


class RAGIngestResponse(BaseModel):
    chunks_added: int
    total_chunks: int


# ── Chat: send a message and get a RAG-backed reply ───────────
class RAGChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    top_k: int = Field(5, ge=1, le=20, description="Number of chunks to retrieve")


class RAGChatResponse(BaseModel):
    reply: str
    sources_used: list[str] = Field(default_factory=list)
    model: str = ""
