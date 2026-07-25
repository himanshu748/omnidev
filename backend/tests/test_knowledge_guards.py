"""
Guardrail tests for whole-laptop indexing.

These cover the failures that are unacceptable rather than merely annoying:
indexing a private key, hanging forever on an iCloud-evicted file, silently
under-reporting coverage, or holding the entire corpus text in memory.
"""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import pytest

from app.services import extractors, file_guards, knowledge_service
from app.services.file_guards import SkipReason

VOCAB = ["alpha", "beta", "gamma", "delta", "epsilon", "zeta"]


async def fake_embed_texts(texts: list[str]) -> list[list[float]]:
    """Deterministic bag-of-words vectors, blind to anything outside VOCAB."""
    vectors = []
    for text in texts:
        lowered = text.lower()
        vector = [float(lowered.count(word)) for word in VOCAB]
        if not any(vector):
            vector[0] = 0.01
        vectors.append(vector)
    return vectors


@pytest.fixture(autouse=True)
def _fake_embeddings(monkeypatch):
    monkeypatch.setattr(knowledge_service.ai_service, "embed_texts", fake_embed_texts)


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    return tmp_path


# ── The denylist ────────────────────────────────────────────
@pytest.mark.parametrize(
    "relative",
    [
        ".ssh/id_rsa",
        ".ssh/id_ed25519",
        ".aws/credentials",
        "Library/Keychains/login.keychain-db",
        "project/.env",
        "project/.env.production",
        "project/server.pem",
        "project/private.key",
        "vault.kdbx",
        ".bash_history",
        ".netrc",
        ".npmrc",
    ],
)
def test_denylist_refuses_secrets(home, relative):
    path = home / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("SECRET MATERIAL")
    assert file_guards.is_denied(path), f"{relative} must never be indexed"
    assert file_guards.denied_reason(path)


def test_denylist_allows_ordinary_documents(home):
    for relative in ["notes/todo.md", "code/main.py", "Desktop/shot.png", "docs/report.pdf"]:
        path = home / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x")
        assert not file_guards.is_denied(path), f"{relative} should be indexable"


@pytest.mark.asyncio
async def test_denylist_wins_over_an_explicit_source(home, monkeypatch):
    """Adding a folder must not smuggle in the secrets inside it."""
    root = home / "everything"
    (root / ".ssh").mkdir(parents=True)
    (root / ".ssh" / "id_rsa").write_text("PRIVATE KEY alpha alpha alpha")
    (root / "notes.md").write_text("alpha beta notes")
    (root / ".env").write_text("API_KEY=alpha-secret")

    source = await knowledge_service.add_source(str(root), "docs")
    await knowledge_service.index_source(source["id"])

    results = await knowledge_service.search("alpha", top_k=20)
    paths = [r["file_path"] for r in results]
    assert any(p.endswith("notes.md") for p in paths)
    assert not any("id_rsa" in p for p in paths), "a private key reached the index"
    assert not any(p.endswith(".env") for p in paths), "a .env reached the index"


def test_user_exclusions_apply_on_top(home):
    path = home / "work" / "draft.md"
    path.parent.mkdir(parents=True)
    path.write_text("x")
    assert not file_guards.matches_user_exclusions(path, [])
    assert file_guards.matches_user_exclusions(path, ["*.md"])
    assert file_guards.matches_user_exclusions(path, [str(home / "work")])


# ── Never hang ──────────────────────────────────────────────
def test_evicted_file_is_detected_without_opening(home, monkeypatch):
    """stat() must be enough; open() on a real evicted file blocks forever."""
    path = home / "cloud.md"
    path.write_text("content")

    real_stat = file_guards.os.stat

    class FakeStat:
        def __init__(self, wrapped):
            self._wrapped = wrapped
            self.st_flags = file_guards.SF_DATALESS

        def __getattr__(self, name):
            return getattr(self._wrapped, name)

    monkeypatch.setattr(file_guards.os, "stat", lambda p, *a, **k: FakeStat(real_stat(p)))
    assert file_guards.is_evicted(path)
    assert file_guards.precheck(path) == SkipReason.EVICTED


@pytest.mark.asyncio
async def test_indexing_skips_evicted_files_and_reports_them(home, monkeypatch):
    root = home / "desktop"
    root.mkdir()
    (root / "local.md").write_text("alpha beta local file")
    (root / "evicted.md").write_text("gamma delta evicted file")

    def fake_is_evicted(path):
        return Path(path).name == "evicted.md"

    monkeypatch.setattr(file_guards, "is_evicted", fake_is_evicted)
    monkeypatch.setattr(knowledge_service.file_guards, "is_evicted", fake_is_evicted)

    source = await knowledge_service.add_source(str(root), "docs")
    await knowledge_service.index_source(source["id"])

    status = knowledge_service.indexing_status()
    assert status["skipped"].get(SkipReason.EVICTED) == 1
    assert "iCloud" in status["message"]

    results = await knowledge_service.search("gamma delta", top_k=10)
    assert not any("evicted.md" in r["file_path"] for r in results)


def test_read_timeout_abandons_a_stalled_file():
    def never_returns():
        time.sleep(30)

    started = time.time()
    with pytest.raises(file_guards.ReadTimeout):
        file_guards.run_with_timeout(never_returns, timeout=0.3)
    assert time.time() - started < 5, "the timeout did not actually cut the read short"


@pytest.mark.asyncio
async def test_timed_out_file_is_skipped_not_fatal(home, monkeypatch):
    root = home / "docs"
    root.mkdir()
    (root / "fine.md").write_text("alpha beta fine")
    (root / "slow.md").write_text("gamma slow")

    def fake_read(path):
        if Path(path).name == "slow.md":
            raise file_guards.ReadTimeout("stalled")
        return Path(path).read_text()

    monkeypatch.setattr(knowledge_service, "_read_file_text", fake_read)

    source = await knowledge_service.add_source(str(root), "docs")
    await knowledge_service.index_source(source["id"])

    status = knowledge_service.indexing_status()
    assert status["skipped"].get(SkipReason.TIMEOUT) == 1
    assert status["error"] is None
    results = await knowledge_service.search("alpha beta", top_k=10)
    assert any("fine.md" in r["file_path"] for r in results)


def test_too_large_file_is_skipped(home, monkeypatch):
    path = home / "huge.txt"
    path.write_text("x" * 100)
    monkeypatch.setattr(file_guards, "MAX_FILE_BYTES", 10)
    assert file_guards.precheck(path) == SkipReason.TOO_LARGE


# ── Coverage honesty ────────────────────────────────────────
def test_skip_tally_summarises_for_humans():
    tally = file_guards.SkipTally()
    tally.add(SkipReason.EVICTED, "/a.png")
    tally.add(SkipReason.EVICTED, "/b.png")
    tally.add(SkipReason.TIMEOUT, "/c.pdf")
    summary = tally.summary()
    assert "2" in summary and "iCloud" in summary
    assert "1" in summary and "timed out" in summary
    assert tally.total == 3
    assert file_guards.SkipTally().summary() == ""


# ── Memory shape ────────────────────────────────────────────
@pytest.mark.asyncio
async def test_cache_holds_vectors_only_and_appends(home):
    root = home / "notes"
    root.mkdir()
    (root / "one.md").write_text("alpha beta one")
    source = await knowledge_service.add_source(str(root), "docs")
    await knowledge_service.index_source(source["id"])
    await knowledge_service.search("alpha", top_k=3)

    cache = knowledge_service._cache
    assert isinstance(cache["matrix"], np.ndarray)
    assert cache["matrix"].dtype == np.float32
    # ids and vectors only: no object arrays, so no text is resident.
    assert isinstance(cache["ids"], np.ndarray)
    assert cache["ids"].dtype == np.int64
    first_rows = cache["matrix"].shape[0]
    first_max_id = cache["max_id"]

    (root / "two.md").write_text("gamma delta two")
    await knowledge_service.index_source(source["id"])
    await knowledge_service.search("gamma", top_k=3)

    assert knowledge_service._cache["matrix"].shape[0] > first_rows
    assert knowledge_service._cache["max_id"] > first_max_id


# ── Hybrid retrieval ────────────────────────────────────────
@pytest.mark.asyncio
async def test_keyword_search_finds_what_embeddings_miss(home):
    """
    The fake embedder is blind to anything outside VOCAB, standing in for a
    real embedder's weakness at exact tokens. BM25 must still find it.
    """
    root = home / "docs"
    root.mkdir()
    (root / "log.md").write_text("The build failed with E_QUOTA_EXCEEDED on line 88.")
    (root / "other.md").write_text("alpha beta gamma unrelated prose")

    source = await knowledge_service.add_source(str(root), "docs")
    await knowledge_service.index_source(source["id"])

    results = await knowledge_service.search("E_QUOTA_EXCEEDED", top_k=5)
    assert any("log.md" in r["file_path"] for r in results), (
        "hybrid retrieval failed to find an exact token"
    )


@pytest.mark.asyncio
async def test_search_filters_by_kind_and_path(home):
    root = home / "mixed"
    root.mkdir()
    (root / "note.md").write_text("alpha beta shared word")
    (root / "code.py").write_text("# alpha beta shared word")

    source = await knowledge_service.add_source(str(root), "code")
    await knowledge_service.index_source(source["id"])

    docs = await knowledge_service.search("alpha beta", top_k=10, kinds=["doc"])
    assert docs and all(r["kind"] == "doc" for r in docs)

    code = await knowledge_service.search("alpha beta", top_k=10, kinds=["code"])
    assert code and all(r["kind"] == "code" for r in code)

    scoped = await knowledge_service.search(
        "alpha beta", top_k=10, path_prefix=str(root / "note")
    )
    assert scoped and all("note.md" in r["file_path"] for r in scoped)


# ── Ad-hoc file questions ───────────────────────────────────
@pytest.mark.asyncio
async def test_ask_file_reads_without_indexing(home):
    path = home / "standalone.md"
    path.write_text("alpha beta the answer is 42")

    result = await knowledge_service.read_for_question(str(path), "what is the answer?")
    assert "42" in result["excerpts"][0]
    assert result["truncated"] is False
    # Nothing was added to the index.
    assert await knowledge_service.list_sources() == []


@pytest.mark.asyncio
async def test_ask_file_refuses_secrets_and_evicted(home, monkeypatch):
    secret = home / ".ssh" / "id_rsa"
    secret.parent.mkdir(parents=True)
    secret.write_text("PRIVATE KEY")
    with pytest.raises(knowledge_service.KnowledgeError):
        await knowledge_service.read_for_question(str(secret), "what is this?")

    cloud = home / "cloud.md"
    cloud.write_text("text")
    monkeypatch.setattr(
        knowledge_service.file_guards, "is_evicted", lambda p: Path(p).name == "cloud.md"
    )
    with pytest.raises(knowledge_service.KnowledgeError) as exc:
        await knowledge_service.read_for_question(str(cloud), "what is this?")
    assert "iCloud" in str(exc.value)


@pytest.mark.asyncio
async def test_ask_file_endpoint(client, home, coverage_tracker):
    coverage_tracker("POST /api/knowledge/ask-file")
    path = home / "readme.md"
    path.write_text("alpha the deployment key rotates monthly")
    resp = await client.post(
        "/api/knowledge/ask-file",
        json={"path": str(path), "question": "how often does the key rotate?"},
    )
    assert resp.status_code == 200
    assert "monthly" in resp.json()["excerpts"][0]

    resp = await client.post(
        "/api/knowledge/ask-file",
        json={"path": str(home / "missing.md"), "question": "x"},
    )
    assert resp.status_code == 400


# ── Erasure ─────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_delete_index_erases_everything(client, home, coverage_tracker):
    coverage_tracker("DELETE /api/knowledge/index")
    coverage_tracker("GET /api/knowledge/stats")
    root = home / "notes"
    root.mkdir()
    (root / "a.md").write_text("alpha beta content")
    source = await knowledge_service.add_source(str(root), "docs")
    await knowledge_service.index_source(source["id"])
    assert (await knowledge_service.search("alpha", top_k=5))

    resp = await client.get("/api/knowledge/stats")
    assert resp.status_code == 200 and resp.json()["chunks"] > 0

    resp = await client.delete("/api/knowledge/index")
    assert resp.status_code == 200 and resp.json()["chunks"] > 0

    assert await knowledge_service.search("alpha", top_k=5) == []
    assert await knowledge_service.list_sources() == []


def test_index_file_is_not_world_readable(home):
    knowledge_service._connect().close()
    path = knowledge_service._db_path()
    mode = path.stat().st_mode & 0o777
    assert mode == 0o600, f"index mode {oct(mode)} exposes plaintext excerpts"


# ── Extractors ──────────────────────────────────────────────
def test_kind_classification():
    assert extractors.kind_for(Path("a.png")) == "image"
    assert extractors.kind_for(Path("a.heic")) == "image"
    assert extractors.kind_for(Path("a.py")) == "code"
    assert extractors.kind_for(Path("a.md")) == "doc"


def test_office_extraction_from_a_real_docx(tmp_path):
    """docx is a zip of XML; extraction must not need a heavy dependency."""
    import zipfile

    path = tmp_path / "memo.docx"
    document = (
        '<?xml version="1.0"?><w:document xmlns:w="x"><w:body>'
        "<w:p><w:r><w:t>Quarterly revenue rose</w:t></w:r></w:p>"
        "<w:p><w:r><w:t>to 4.2 million</w:t></w:r></w:p>"
        "</w:body></w:document>"
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("word/document.xml", document)
    text = extractors.extract_text(path)
    assert "Quarterly revenue rose" in text and "4.2 million" in text


def test_html_extraction_drops_scripts(tmp_path):
    path = tmp_path / "page.html"
    path.write_text("<html><script>var secret='hidden';</script><body>Visible text</body></html>")
    text = extractors.extract_text(path)
    assert "Visible text" in text and "secret" not in text
