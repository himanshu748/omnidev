"""Knowledge router: local RAG sources, background indexing and search."""

from __future__ import annotations

from fastapi import APIRouter

from app.routers.errors import bad_request, not_found, service_unavailable
from app.schemas.knowledge import (
    IndexStatusResponse,
    SearchHit,
    SearchRequest,
    SearchResponse,
    SourceCreateRequest,
    SourceInfo,
    SourceListResponse,
)
from app.services import knowledge_service
from app.services.ai_service import AIConfigurationError, AIResponseError

router = APIRouter()


@router.post("/sources", response_model=SourceInfo, status_code=201)
async def add_source(body: SourceCreateRequest):
    """Register a folder (or the chat history) and start indexing it."""
    try:
        source = await knowledge_service.add_source(body.path, body.kind)
    except knowledge_service.KnowledgeError as exc:
        raise bad_request(str(exc)) from exc
    knowledge_service.start_index_job(source["id"])
    return SourceInfo(**source)


@router.get("/sources", response_model=SourceListResponse)
async def list_sources():
    sources = await knowledge_service.list_sources()
    return SourceListResponse(sources=[SourceInfo(**s) for s in sources])


@router.post("/sources/{source_id}/reindex", response_model=IndexStatusResponse)
async def reindex_source(source_id: int, full: bool = False):
    """Start a re-index; `full=true` re-embeds every file."""
    source = await knowledge_service.get_source(source_id)
    if source is None:
        raise not_found("Unknown source id.")
    if knowledge_service.indexing_status()["running"]:
        raise bad_request("An indexing job is already running.")
    knowledge_service.start_index_job(source_id, full=full)
    return IndexStatusResponse(**knowledge_service.indexing_status())


@router.delete("/sources/{source_id}")
async def delete_source(source_id: int):
    if not await knowledge_service.delete_source(source_id):
        raise not_found("Unknown source id.")
    return {"deleted": source_id}


@router.post("/search", response_model=SearchResponse)
async def search(body: SearchRequest):
    try:
        results = await knowledge_service.search(
            body.query, top_k=body.top_k, source_ids=body.source_ids
        )
    except AIConfigurationError as exc:
        raise service_unavailable(str(exc)) from exc
    except AIResponseError as exc:
        raise service_unavailable(str(exc)) from exc
    return SearchResponse(results=[SearchHit(**r) for r in results])


@router.get("/status", response_model=IndexStatusResponse)
async def status():
    return IndexStatusResponse(**knowledge_service.indexing_status())
