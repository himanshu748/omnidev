"""Knowledge index tests: sources CRUD, incremental indexing, search and the
grounded chat flag. Embeddings are faked with a deterministic word-overlap
vector so retrieval quality is assertable without a model."""

from __future__ import annotations

import asyncio
import json

import pytest

from app.services import knowledge_service, session_service

VOCAB = ["solana", "swift", "recipe", "fastapi", "ollama", "keychain", "banana", "docs"]


async def fake_embed_texts(texts: list[str]) -> list[list[float]]:
    vectors = []
    for text in texts:
        lowered = text.lower()
        vec = [float(lowered.count(word)) for word in VOCAB]
        if not any(vec):
            vec[-1] = 1.0
        vectors.append(vec)
    return vectors


@pytest.fixture(autouse=True)
def _fake_embeddings(monkeypatch):
    monkeypatch.setattr(knowledge_service.ai_service, "embed_texts", fake_embed_texts)
    yield


async def _index_and_wait(source_id: int, full: bool = False):
    await knowledge_service.index_source(source_id, full=full)


def _write_docs(root):
    root.mkdir(parents=True, exist_ok=True)
    (root / "swift.md").write_text("Swift keychain notes: store secrets in the keychain.")
    (root / "solana.txt").write_text("Solana programs use accounts and instructions.")
    (root / "web.html").write_text(
        "<html><script>var x = 'banana';</script><body>FastAPI serves the docs.</body></html>"
    )
    (root / "ignored.bin").write_bytes(b"\x00\x01")
    hidden = root / ".hidden"
    hidden.mkdir(exist_ok=True)
    (hidden / "secret.md").write_text("hidden banana file")


# ── Sources CRUD ────────────────────────────────────────────
@pytest.mark.asyncio
async def test_add_list_delete_source(client, tmp_path, coverage_tracker):
    coverage_tracker("POST /api/knowledge/sources")
    coverage_tracker("GET /api/knowledge/sources")
    coverage_tracker("DELETE /api/knowledge/sources")
    folder = tmp_path / "notes"
    _write_docs(folder)

    resp = await client.post(
        "/api/knowledge/sources", json={"path": str(folder), "kind": "docs"}
    )
    assert resp.status_code == 201
    source = resp.json()
    assert source["kind"] == "docs"

    resp = await client.get("/api/knowledge/sources")
    assert resp.status_code == 200
    assert len(resp.json()["sources"]) == 1

    resp = await client.delete(f"/api/knowledge/sources/{source['id']}")
    assert resp.status_code == 200
    resp = await client.delete(f"/api/knowledge/sources/{source['id']}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_add_source_rejects_bad_paths(client, tmp_path):
    resp = await client.post(
        "/api/knowledge/sources", json={"path": "relative/path", "kind": "docs"}
    )
    assert resp.status_code == 400

    resp = await client.post(
        "/api/knowledge/sources", json={"path": str(tmp_path / "missing"), "kind": "docs"}
    )
    assert resp.status_code == 400

    from app.config import settings

    resp = await client.post(
        "/api/knowledge/sources", json={"path": settings.data_dir, "kind": "docs"}
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_duplicate_source_rejected(client, tmp_path):
    folder = tmp_path / "notes"
    _write_docs(folder)
    body = {"path": str(folder), "kind": "docs"}
    assert (await client.post("/api/knowledge/sources", json=body)).status_code == 201
    assert (await client.post("/api/knowledge/sources", json=body)).status_code == 400


# ── Indexing ────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_index_and_search(client, tmp_path, coverage_tracker):
    coverage_tracker("POST /api/knowledge/search")
    folder = tmp_path / "notes"
    _write_docs(folder)
    source = await knowledge_service.add_source(str(folder), "docs")
    await _index_and_wait(source["id"])

    sources = await knowledge_service.list_sources()
    assert sources[0]["chunk_count"] >= 3  # bin + hidden skipped

    resp = await client.post("/api/knowledge/search", json={"query": "swift keychain"})
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert results
    assert results[0]["file_path"].endswith("swift.md")
    # The html file was stripped of script content.
    html_hits = [r for r in results if r["file_path"].endswith("web.html")]
    for hit in html_hits:
        assert "banana" not in hit["snippet"]


@pytest.mark.asyncio
async def test_incremental_reindex_only_touches_changed_files(client, tmp_path, monkeypatch):
    folder = tmp_path / "notes"
    _write_docs(folder)
    source = await knowledge_service.add_source(str(folder), "docs")
    await _index_and_wait(source["id"])

    embedded: list[str] = []
    real_embed = fake_embed_texts

    async def counting_embed(texts):
        embedded.extend(texts)
        return await real_embed(texts)

    monkeypatch.setattr(knowledge_service.ai_service, "embed_texts", counting_embed)

    # Untouched re-index embeds nothing.
    await _index_and_wait(source["id"])
    assert embedded == []

    # Touch one file: only it re-embeds.
    import os

    target = folder / "solana.txt"
    target.write_text("Solana validators and banana stake.")
    os.utime(target, (1e9, 1e9))
    await _index_and_wait(source["id"])
    assert embedded and all("solana" in t.lower() or "banana" in t.lower() for t in embedded)

    # Deleted files fall out of the index.
    target.unlink()
    await _index_and_wait(source["id"])
    results = await knowledge_service.search("solana", top_k=10)
    assert not any(r["file_path"].endswith("solana.txt") for r in results)


@pytest.mark.asyncio
async def test_chat_history_source(client, tmp_path):
    session_id = await session_service.create_session("solana question")
    await session_service.append_message(session_id, "user", "How do solana accounts work?")
    await session_service.append_message(session_id, "assistant", "Accounts hold lamports.")

    source = await knowledge_service.add_source("", "chat")
    await _index_and_wait(source["id"])
    results = await knowledge_service.search("solana accounts")
    assert results
    assert results[0]["file_path"] == f"session:{session_id}"


@pytest.mark.asyncio
async def test_status_endpoint(client, coverage_tracker):
    coverage_tracker("GET /api/knowledge/status")
    resp = await client.get("/api/knowledge/status")
    assert resp.status_code == 200
    body = resp.json()
    assert body["running"] is False


@pytest.mark.asyncio
async def test_search_empty_index(client):
    resp = await client.post("/api/knowledge/search", json={"query": "anything"})
    assert resp.status_code == 200
    assert resp.json()["results"] == []


@pytest.mark.asyncio
async def test_search_maps_config_error_to_503(client, tmp_path, monkeypatch):
    folder = tmp_path / "notes"
    _write_docs(folder)
    source = await knowledge_service.add_source(str(folder), "docs")
    await _index_and_wait(source["id"])

    from app.services.ai_service import AIConfigurationError

    async def broken_embed(texts):
        raise AIConfigurationError("Embedding model 'mxbai-embed-large' is not available.")

    monkeypatch.setattr(knowledge_service.ai_service, "embed_texts", broken_embed)
    resp = await client.post("/api/knowledge/search", json={"query": "swift"})
    assert resp.status_code == 503


# ── Grounded chat ───────────────────────────────────────────
@pytest.mark.asyncio
async def test_chat_stream_use_knowledge(client, tmp_path, monkeypatch):
    folder = tmp_path / "notes"
    _write_docs(folder)
    source = await knowledge_service.add_source(str(folder), "docs")
    await _index_and_wait(source["id"])

    captured: dict = {}

    async def fake_stream_chat(messages, *, system=None, temperature=None, max_tokens=2048):
        captured["system"] = system
        yield "grounded answer"

    monkeypatch.setattr("app.routers.chat.stream_chat", fake_stream_chat)
    monkeypatch.setattr("app.routers.chat.ensure_ai_configured", lambda: None)

    resp = await client.post(
        "/api/chat/stream",
        json={"message": "How do I use the swift keychain?", "use_knowledge": True},
    )
    assert resp.status_code == 200
    events = [json.loads(line) for line in resp.text.strip().splitlines()]
    knowledge_events = [e for e in events if "knowledge" in e]
    assert knowledge_events
    assert any(f.endswith("swift.md") for f in knowledge_events[0]["knowledge"]["cited_files"])
    assert "keychain" in captured["system"].lower()
    assert any(e.get("done") for e in events)


@pytest.mark.asyncio
async def test_reindex_endpoint(client, tmp_path):
    folder = tmp_path / "notes"
    _write_docs(folder)
    source = await knowledge_service.add_source(str(folder), "docs")
    resp = await client.post(f"/api/knowledge/sources/{source['id']}/reindex")
    assert resp.status_code == 200
    # Let the background task run to completion so it does not leak.
    for _ in range(200):
        if not knowledge_service.indexing_status()["running"]:
            break
        await asyncio.sleep(0.01)
    resp = await client.post("/api/knowledge/sources/999/reindex")
    assert resp.status_code == 404
