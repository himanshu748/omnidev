"""Exercise real on-device OCR through knowledge indexing on macOS."""

import asyncio
import shutil
import sys
from pathlib import Path

import pytest

from app.services import extractors, knowledge_service

pytestmark = pytest.mark.skipif(
    sys.platform != "darwin", reason="Requires macOS Vision OCR"
)


@pytest.mark.asyncio
async def test_native_vision_text_is_extracted_and_indexed(tmp_path, monkeypatch) -> None:
    """Real Vision text must survive extraction, embedding input and retrieval."""
    source_dir = tmp_path / "ocr-documents"
    source_dir.mkdir()
    image = source_dir / "ocr.png"
    shutil.copyfile(Path(__file__).parent / "fixtures" / "vision-ocr.png", image)

    # A missing/broken macOS installation must fail, rather than silently skip.
    text = await asyncio.to_thread(extractors.extract_text, image)
    assert {"ORBIT", "SEARCH"} <= set(text.upper().split())

    embedded_texts: list[str] = []

    async def offline_embeddings(texts: list[str]) -> list[list[float]]:
        embedded_texts.extend(texts)
        return [[1.0, 0.0] for _ in texts]

    # Only the provider boundary is faked; extraction and SQLite indexing are real.
    monkeypatch.setattr(knowledge_service.ai_service, "embed_texts", offline_embeddings)
    source = await knowledge_service.add_source(str(source_dir), "docs")
    await knowledge_service.index_source(source["id"], full=True)
    assert any({"ORBIT", "SEARCH"} <= set(t.upper().split()) for t in embedded_texts)
    indexed = await knowledge_service.get_source(source["id"])
    assert indexed["chunk_count"] >= 1
    hits = await knowledge_service.search("ORBIT", source_ids=[source["id"]])
    assert any(
        hit["file_path"] == str(image) and "ORBIT" in hit["snippet"].upper()
        for hit in hits
    )
