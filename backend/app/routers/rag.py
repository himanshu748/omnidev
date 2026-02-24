"""RAG Chatbot router — ingest documents, chat with retrieval-augmented generation."""

from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas.rag import RAGChatRequest, RAGChatResponse, RAGIngestRequest, RAGIngestResponse
from app.services.rag_service import chat, extract_text_from_pdf, ingest

router = APIRouter()

ALLOWED_INGEST_TYPES = {"application/pdf", "text/plain", "text/markdown"}


@router.post("/ingest", response_model=RAGIngestResponse)
async def rag_ingest(body: RAGIngestRequest):
    """
    Add documents to the RAG knowledge base.
    Provide either `text` (single block, will be chunked) or `documents` (list of chunks).
    """
    if not body.text and not body.documents:
        raise HTTPException(
            status_code=400,
            detail="Provide either 'text' or 'documents'",
        )
    try:
        chunks_added, total = await ingest(text=body.text, documents=body.documents)
        return RAGIngestResponse(chunks_added=chunks_added, total_chunks=total)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/ingest/file", response_model=RAGIngestResponse)
async def rag_ingest_file(file: UploadFile = File(...)):
    """
    Upload a document (PDF or TXT). Text is extracted and added to the knowledge base.
    Then you can ask questions about the document via POST /chat.
    """
    content_type = (file.content_type or "").lower()
    if content_type not in ALLOWED_INGEST_TYPES and not (file.filename or "").lower().endswith((".pdf", ".txt", ".md")):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Use PDF or plain text (allowed: {', '.join(ALLOWED_INGEST_TYPES)})",
        )
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")
    try:
        if content_type == "application/pdf" or (file.filename or "").lower().endswith(".pdf"):
            text = extract_text_from_pdf(data)
        else:
            text = data.decode("utf-8", errors="replace")
        if not text.strip():
            raise HTTPException(status_code=400, detail="No text could be extracted from the file")
        chunks_added, total = await ingest(text=text)
        return RAGIngestResponse(chunks_added=chunks_added, total_chunks=total)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/chat", response_model=RAGChatResponse)
async def rag_chat(body: RAGChatRequest):
    """
    Send a message; retrieve relevant chunks from the knowledge base and generate a reply.
    """
    try:
        reply, sources, model = await chat(message=body.message, top_k=body.top_k)
        return RAGChatResponse(reply=reply, sources_used=sources, model=model)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
