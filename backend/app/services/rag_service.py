"""
RAG (Retrieval-Augmented Generation) service.
In-memory vector store using OpenAI embeddings; retrieval + LLM for chat.
Answers questions strictly from ingested documents (text or uploaded PDF/TXT).
"""

from __future__ import annotations

import math
from typing import Any

from openai import AsyncOpenAI
from pypdf import PdfReader
from io import BytesIO

from app.config import settings

_openai = AsyncOpenAI(api_key=settings.openai_api_key)

# In-memory store: list of { "text": str, "embedding": list[float] }
_chunks: list[dict[str, Any]] = []

EMBEDDING_MODEL = "text-embedding-3-small"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


def _split_into_chunks(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks (by character, with sentence awareness)."""
    text = text.strip()
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        if end < len(text):
            # Try to break at sentence or word boundary
            search = text[start:end]
            last_period = search.rfind(". ")
            last_newline = search.rfind("\n")
            last_space = search.rfind(" ")
            break_at = max(last_period, last_newline, last_space)
            if break_at > chunk_size // 2:
                end = start + break_at + 1
        chunks.append(text[start:end].strip())
        start = end - overlap if end < len(text) else len(text)
    return [c for c in chunks if c]


async def _embed(texts: list[str]) -> list[list[float]]:
    """Get embeddings for a list of texts (OpenAI)."""
    if not texts:
        return []
    resp = await _openai.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts,
    )
    by_idx = {item.index: item.embedding for item in resp.data}
    return [by_idx[i] for i in range(len(texts))]


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def extract_text_from_pdf(data: bytes) -> str:
    """Extract plain text from a PDF file."""
    reader = PdfReader(BytesIO(data))
    parts = []
    for page in reader.pages:
        try:
            parts.append(page.extract_text() or "")
        except Exception:
            parts.append("")
    return "\n".join(parts).strip()


async def ingest(text: str | None = None, documents: list[str] | None = None) -> tuple[int, int]:
    """
    Add documents to the RAG store. Returns (chunks_added, total_chunks).
    """
    global _chunks
    to_embed: list[str] = []
    if documents:
        to_embed.extend(doc.strip() for doc in documents if doc.strip())
    if text:
        to_embed.extend(_split_into_chunks(text))
    if not to_embed:
        return 0, len(_chunks)
    embeddings = await _embed(to_embed)
    for t, emb in zip(to_embed, embeddings):
        _chunks.append({"text": t, "embedding": emb})
    return len(to_embed), len(_chunks)


async def chat(message: str, top_k: int = 5) -> tuple[str, list[str], str]:
    """
    Retrieve relevant chunks, then generate a reply using OpenAI chat.
    Returns (reply, sources_used, model).
    """
    # Embed the user message
    query_embeddings = await _embed([message])
    query_emb = query_embeddings[0]

    # Retrieve top-k by cosine similarity
    if _chunks:
        scored = [
            (_cosine_similarity(query_emb, c["embedding"]), c["text"])
            for c in _chunks
        ]
        scored.sort(key=lambda x: -x[0])
        top = scored[:top_k]
        context_parts = [t for _, t in top]
        sources_used = context_parts
    else:
        context_parts = []
        sources_used = []

    context = "\n\n---\n\n".join(context_parts) if context_parts else ""

    system = """You are a document Q&A assistant. You answer questions ONLY using the provided document excerpts below.

Rules:
- Base your answer strictly on the "Document excerpts" provided. Do not use outside knowledge.
- If the excerpts contain enough information to answer the question, give a clear, concise answer and refer to the documents.
- If the excerpts do not contain relevant information, say: "The documents don't contain information about that." Do not guess or make up an answer.
- Keep answers concise. You can quote or paraphrase from the excerpts when helpful."""

    if not context:
        system += "\n\nRight now no documents have been added. Tell the user to add documents (paste text or upload files) first, then ask questions about them."
        user_content = f"User question: {message}"
    else:
        user_content = f"Document excerpts (use only these to answer):\n\n{context}\n\n---\n\nUser question: {message}"

    resp = await _openai.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ],
        max_tokens=1024,
    )
    choice = resp.choices[0]
    reply = choice.message.content or ""
    model = resp.model or ""
    return reply, sources_used, model
