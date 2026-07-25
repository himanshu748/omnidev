# OmniDev PRD: v0.6.0 "Ask your Mac, offline" + v0.6.5 "Agent mode"

**Version:** 1.0 · 2026-07-13
**Owner:** himanshu748 · **Repo:** https://github.com/himanshu748/omnidev (local: `/Users/himanshujha/Documents/Codex/omnidev`)
**Status: BOTH RELEASES SHIPPED.** v0.6.0 on 2026-07-14 (commit 9f5d8a4) and v0.6.5 on 2026-07-14 (commit e4e7df1). Kept for the record; the live brief is now `docs/PRD-v0.7.md`.

**Deviations made while building v0.6.5, and why:**
1. `apply_patch(path, unified_diff)` became `edit_file(path, old_text, new_text)`. Small local models reliably botch hunk headers and line numbers but handle exact-snippet replacement fine. A failed match echoes the closest region back via difflib so the model self-corrects. This is what made the live gemma4:12b run succeed first time.
2. The agent records git HEAD before its first mutation but does **not** create a checkpoint commit. Once workspaces became the user's real repositories rather than only generated projects, committing their in-progress work unasked was worse than the problem it solved.
3. Approval scope became allow_once / allow_always / deny, with allow_always scoped per tool plus parent directory for one run only.

**Original status:** the definitive brief for the next two releases. Written to be pasted into a fresh agent session with zero prior context. Current shipped version: **0.5.3** (`AppInfo.version` in `macos/Sources/OmniDevMac/Support/AppSettings.swift`).

---

## 0. Critical environment notes (read before doing anything)

- **NEVER run builds, package installs or tests inside `~/Documents`** on this machine. The repo lives in an iCloud-synced folder that stalls processes at 0% CPU. Workflow: edit in place, then `rsync` (excluding `.venv`) to a `/tmp` scratch copy and run pytest / uvicorn there. Git operations and file edits in `~/Documents` are fine but slow; run commits and pushes as long-timeout background commands.
- Backend tests: run with system `python3 -m pytest` (the project `.venv` under Documents intermittently hangs with `[Errno 60]`).
- CI (`.github/workflows/ci.yml`) runs backend pytest + `swift build` on every push and is the off-machine verifier. Release CI (`release.yml`) publishes `OmniDev-vX.Y.Z.zip` on `v*` tags. Publish flow: bump `AppInfo.version`, tag, push.
- The dev machine has 16GB RAM. Installed Ollama models: `gemma4:12b` (7.6GB, the default text+vision model) and `mxbai-embed-large` (669MB). Under memory pressure (browsers open) 12b generation collapsed to ~0.4 tok/s once; treat headroom as a first-class constraint.
- A running MCP server process does not pick up code changes; restart the session or server after editing `backend/app/mcp/`.
- EngineInstaller's `.engine-version` marker means two same-version builds do not re-sync the App Support engine; `rm` the marker when iterating locally.
- Writing rule for all docs, commits and UI copy in this repo: no em or en dashes, no Oxford comma.

## 1. Context and goal

OmniDev at 0.5.3 is a fully native SwiftUI macOS app with a FastAPI engine sidecar, a provider-agnostic AI layer (local Ollama gemma4:12b by default, Gemini when keyed), an MCP server registered with Claude Code, an MCP marketplace, an in-app model manager, SQLite chat memory and a hardened scraper/devops surface (244 backend tests). It chats and generates, but it has no knowledge of the user's own files and it cannot act iteratively.

The next two releases fix both, in this order, for an audience of **strangers installing from GitHub Releases**:

- **v0.6.0**: local RAG ("Ask your Mac, offline") plus free-tier distribution polish (demo GIF, DMG, first-run resilience). No code signing yet (no $99 Apple Developer spend this cycle).
- **v0.6.5**: agent mode in ChatView, grounded in the v0.6.0 index.

Success is judged equally on portfolio impact, GitHub traction and daily-driver utility. Tie-breaker for any scope decision: **does it make the 10-second README GIF better?**

## 2. v0.6.0 scope

### 2.1 Local RAG index

**Priority order if anything must be cut: notes and docs first, then code projects, then chat history.**

- **Storage**: `sqlite-vec` extension on the existing `~/.omnidev/omnidev.db`. New tables: `knowledge_sources` (id, path, kind, added_at, last_indexed_at, file_count), `knowledge_chunks` (id, source_id, file_path, chunk_index, text, mtime) and a vec0 virtual table for embeddings keyed to chunk id.
- **Embeddings**: `mxbai-embed-large` via Ollama (already installed on the dev machine, 669MB, 1024-dim). Do NOT embed with gemma4:12b; a dedicated small embedder keeps generation headroom free. Add `mxbai-embed-large` to `RECOMMENDED_MODELS` and `LocalModelCatalog` as the embedding entry, auto-pulled the first time the user adds a source (with the same progress UX as model downloads). Gemini provider path uses its embedding endpoint when keyed; provider-agnostic via a new `embed_texts()` in `ai_service.py` raising `AIConfigurationError` on setup problems (routers map to 503, matching the existing pattern).
- **Ingestion**, in priority order:
  1. **Notes and docs**: `.md`, `.txt`, `.pdf` (PyMuPDF or pypdf, no new heavyweight deps), `.rst`, `.html` (strip tags). User picks folders.
  2. **Code projects**: same folder picker, code-aware chunking (respect function boundaries where cheap, otherwise fixed-size with overlap), honor `.gitignore`, skip binaries, `node_modules`, `.venv`, `.git`.
  3. **Chat history**: embed past OmniDev sessions from the existing chat memory tables so memory compounds.
- **Chunking**: ~512 tokens with ~64 overlap, store file path + mtime, re-index only changed files (mtime + size check). Full re-index is a button, not a default.
- **Indexing runs in the backend** as a background job with a progress endpoint (`GET /api/knowledge/status`), never blocking chat. Cap concurrent embedding calls at 1 to protect generation latency.

### 2.2 Backend API

New router `backend/app/routers/knowledge.py`:

- `POST /api/knowledge/sources` {path, kind} → registers and starts indexing (400 on nonexistent path, path must be a directory).
- `GET /api/knowledge/sources` → list with per-source status and counts.
- `DELETE /api/knowledge/sources/{id}` → remove source and its chunks.
- `POST /api/knowledge/search` {query, top_k=8, source_ids?} → chunks with file path, snippet and score.
- `GET /api/knowledge/status` → indexing progress.

Chat integration: `POST /api/chat/stream` gains `use_knowledge: bool`. When true, retrieve top-k chunks for the user message, prepend a grounding block with file citations to the prompt and stream as usual. Responses carry which files were cited (NDJSON metadata event) so the UI can show sources.

Security notes: paths are user-chosen local directories; validate they are absolute, exist and are not inside `~/.omnidev` itself. The loopback-only middleware already gates remote access. Never index outside the registered roots (resolve symlinks, reject escapes).

### 2.3 macOS app

- **New "Knowledge" module page** (SwiftUI, follows the existing module-page pattern in `BackendModules.swift` and gets the next ⌘ shortcut in the Go menu): add/remove folders via `NSOpenPanel`, per-source status, indexing progress, re-index button.
- **ChatView**: a "Knowledge" toggle next to the existing Tools toggle. When on, answers show a compact citations row (file names, click to reveal in Finder).
- **Onboarding**: after the model step, an optional "Add a folder OmniDev can answer questions about" step that pulls the embedder on first use.

### 2.4 MCP exposure

New tools in `backend/app/mcp/` (same FastMCP server):

- `search_knowledge(query, top_k=8)` → grounded chunks with paths and scores.
- `list_knowledge_sources()`.
- `index_folder(path)` → registers a source (kind auto-detected).

This makes Claude Code inherit the local index on day one and is the most differentiated part of the release: OmniDev becomes the offline knowledge organ for any MCP client.

### 2.5 Free-tier distribution polish (same release)

- **README demo GIF**: the RAG demo is the GIF. Script: drop a docs folder in, toggle wifi off (visible in the menu bar), ask a question, get a cited answer. Record on a quiet machine (close browsers first; see the swap incident).
- **DMG**: `create-dmg` in `build-app.sh`, drag-to-Applications layout. Release CI uploads the DMG alongside the zip. Still unsigned; README keeps clear right-click-to-open instructions with a screenshot of the Gatekeeper dialog.
- **Cold-machine first-run resilience**: onboarding and EngineInstaller must produce actionable messages for: no Python ≥3.11, 8GB RAM (recommend the e2b tier automatically, the "Best for this Mac" preset already exists), Intel Mac (universal binary already ships), Ollama missing (already handled). No silent failures; strangers do not file issues, they delete the app.
- **Homebrew cask is out of scope** (main repo requires a signed app). Signing and notarization are deferred to a later release.

### 2.6 Acceptance (v0.6.0)

1. Fresh install from the release DMG on a machine with nothing but Ollama: onboarding completes, a docs folder indexes and a question about its content is answered with citations, wifi off.
2. `search_knowledge` works through real MCP stdio from Claude Code against the app's sidecar (port probe 8000→8010 already exists in `_backend_url()`).
3. Indexing a ~500-file folder does not degrade chat latency (embedding concurrency cap verified).
4. Re-running indexing after touching one file re-embeds only that file.
5. Backend suite green (target ~270+ tests including knowledge router, chunking, ingestion filters and MCP tools). CI green.
6. README has the GIF above the fold and DMG install instructions.
7. Memory headroom spike documented: RSS of embedder + 12b resident together, recorded in this doc's appendix before the feature is merged.

## 3. v0.6.5 scope: agent mode

Built on the shipped index. Smaller release, one headline feature.

### 3.1 Design

- **Surface**: a mode toggle in ChatView next to Tools and Knowledge (no new page). Plan and act steps stream inline as structured NDJSON events (`step_started`, `tool_call`, `tool_result`, `approval_required`, `step_done`).
- **Brain**: hybrid, prefer local. Default gemma4:12b; when a Gemini key is set, agent mode automatically uses Gemini (Settings shows which brain is active). Design constraint for the local path: **narrow, forgiving tools**, not free-form bash.
- **Tools (v0.6.5 set, deliberately small)**:
  - `read_file(path)`, `list_dir(path)` (read-only, sandbox-scoped by default)
  - `write_file(path, content)` and `apply_patch(path, unified_diff)` with retry-friendly errors (echo back the closest matching context on failure so a 12B model can self-correct)
  - `run_command(argv)` restricted to an allowlist (git status/diff/add/commit argv-only, python, pytest, npm test) inside the sandbox
  - `search_knowledge(query)` reused from v0.6.0 for grounding
- **Blast radius**: free rein inside `~/OmniDev/projects` (the existing git-landing root). Any path outside it, and any `run_command`, surfaces a native approval sheet in the app (per action, with the exact argv or diff shown). Approvals resolve over the existing NDJSON stream via a `POST /api/agent/approvals/{id}` callback. Deny is the timeout default.
- **Loop**: plan → act → observe with a hard step cap (default 15) and a stop button. Every file mutation is recorded so a session can be reviewed; git-commit checkpoints inside sandbox projects before the first mutation.
- **Grounding**: when Knowledge is on, retrieval runs on the task statement and between steps on demand via the `search_knowledge` tool.

### 3.2 Acceptance (v0.6.5)

1. Local-only machine: agent completes a scoped task in a sandbox project ("add a README section describing X from the indexed docs") within the step cap, on gemma4:12b.
2. An out-of-sandbox write triggers the approval sheet; deny blocks it; the timeout denies it.
3. With a Gemini key set, the same task runs on Gemini without any other config change.
4. `apply_patch` failure paths verified: malformed diff from the model yields a corrective error and the model recovers at least once in a live test.
5. Step cap and stop button verified live. Backend suite and CI green.

## 4. Sequencing and out of scope

- v0.6.0 first, fully shipped and released, then v0.6.5. The agent inherits a proven index; do not build both at once.
- Out of scope for both releases: code signing and notarization ($99 spend deferred), Homebrew cask, arbitrary MCP marketplace installs, indexing cloud sources, multi-machine sync, voice (gemma4:e4b audio stays a catalog option only).

## 5. Appendix: memory headroom spike (measured 2026-07-13, 16GB M-series, swift build running concurrently)

- [x] mxbai-embed-large resident: 685 MB, 100% GPU, swap 0.
- [x] gemma4:12b generation with the embedder just used: **11.8 tok/s** (296 tokens), swap grew to 2.1 GB used, 21% memory free. Well above the 5 tok/s threshold even under build load.
- [x] Both models co-resident after an embed call with 12b loaded (8.5 GB combined, both 100% GPU); the embed round trip including model load took 1.1 s.
- Verdict: no indexing/chat lock needed at v0.6.0. The single-flight embed queue plus Ollama's own scheduling keep generation healthy. Revisit only if users report sub-5 tok/s during indexing on 8GB machines (e2b tier).
