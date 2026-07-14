# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.6.0] - 2026-07-13

### ✨ Added
- **Knowledge (local RAG)**: register any folder (notes, docs or a whole repo) plus the built-in chat history, and OmniDev chunks it, embeds it locally with `mxbai-embed-large` via Ollama (Gemini embeddings when keyed) and stores vectors in `~/.omnidev/omnidev.db`. New `/api/knowledge/*` endpoints (sources CRUD, background indexing with progress, search), incremental re-indexing (only changed files re-embed), light `.gitignore` support, PDF/HTML/Markdown extraction and a single-flight embedding queue so chat latency stays protected.
- **Knowledge page** in the app: add and remove folders via the native folder picker, watch indexing progress, re-index and search the index directly. If the embedding model is missing, a one-click download fixes it and re-runs indexing.
- **Grounded chat**: a Knowledge toggle in Chat sends `use_knowledge` to `/api/chat/stream`; answers are grounded in retrieved excerpts and the cited files render in the transcript.
- **MCP tools**: `search_knowledge`, `list_knowledge_sources` and `index_folder`, so Claude Code and any MCP client inherit the local index, fully offline.
- **DMG packaging**: releases now attach `OmniDev-vX.Y.Z.dmg` with the standard drag-to-Applications layout, alongside the zip.

### 🎨 Changed
- Chat's `POST /api/chat/stream` accepts `use_knowledge` and emits a `{"knowledge": {"cited_files": [...]}}` event before deltas.
- New backend deps: `numpy` (vector search) and `pypdf` (PDF extraction).

### ✨ Added
- **MCP marketplace** — give the local model tools. A curated catalog (Filesystem, Fetch, Memory, Time, Git, Sequential Thinking) installs MCP servers that Gemma 4 can call from chat via a new Tools toggle; every tool call and result renders in the transcript. Safety by construction: only catalog entries can be installed (no arbitrary commands via API or UI), path params must be directories inside `$HOME`, server processes get a minimal environment (PATH/HOME only — backend credentials are never leaked), results are truncated before re-entering context, and tool rounds are bounded. New endpoints under `/api/mcp/*`; native "MCP Marketplace" page in the app.
- **Conversation memory** — chat is session-backed (SQLite in `~/.omnidev`), so "now add auth" works. `POST /api/chat/stream` accepts `session_id` (returned as the stream's first event) plus session list/history/delete endpoints; the native Chat gets a New Chat button and remembers the thread.
- **Land in repo** — `POST /api/git/land` writes a generated project under `~/OmniDev/projects/<slug>` and commits it. Scoped by construction: strict slug names, the codegen file sanitizer re-runs on every file, git runs with no shell, no hooks, a minimal env, and no remotes — nothing is ever pushed. The native Code Gen page gains a "Land in Repo" action that reveals the repo in Finder.
- **Fully native macOS app** — every module page is now SwiftUI: DevOps Agent (plan preview + in-app destructive confirmation), Code Gen (file browser, refine loop, isolated `WKWebView` HTML preview, save-to-folder), Web Scraper (all extract modes incl. screenshot/PDF + bounded crawl), Vision Lab (file picker, 10 MB cap), and Cloud Storage (buckets/objects, upload, presigned download, confirmed delete). The webview bridge is gone and the app no longer needs Node — it supervises only the FastAPI engine (`OMNIDEV_SKIP_FRONTEND=1`); Next.js remains the web dev stack and marketing site. The web `LogoMark` is now the terminal-window mark, matching the app icon.
- **Native macOS surfaces** — the cockpit ("Command Center": engine status, local model manager with one-click pull, module launcher) and streaming chat are now native SwiftUI, talking to the local engine via URLSession NDJSON streaming; module pages remain in the webview bridge. New first-run onboarding window checks the engine → Ollama → default model and pulls `gemma4:e4b` with live progress — zero terminal use. Plus: a menu-bar extra (engine status, active model, quick actions), a Settings window (AI provider, read-only DevOps mode, ports — applied to the sidecars via environment on restart), a GitHub-releases update check, and a proper app icon rendered from the LogoMark (dock icon works even under `swift run`; the old multi-color logo PNG is replaced).
- **MCP server** — `python -m app.mcp` (or `make mcp`) exposes the local engine to Claude Code, Claude Desktop, Cursor, and any MCP client over stdio: `local_llm` (delegate generation to the free on-device Gemma 4), `local_vision`, `scrape_url`/`crawl_site`, `generate_project`/`refine_project`, `aws_plan`, and `list_models`/`pull_model`. The server is a thin localhost bridge to the FastAPI backend; codegen output is returned as data (never written or executed) and `aws_plan` is preview-only. A cwd-independent `backend/mcp_server.py` launcher backs the one-line `claude mcp add omnidev` registration.
- **`POST /api/devops/plan`** — plan preview for a natural-language AWS command that never dispatches boto3 (not even read-only calls). Backs the MCP `aws_plan` tool; execution and destructive-action approval stay in the OmniDev UI.
- **Web Scraper, deepened** — new `markdown` (dependency-free HTML→Markdown) and `article` (readability main-content) extract modes; `metadata` now returns Open Graph, Twitter cards, JSON-LD, canonical, favicon, language, and word count; and a new `POST /api/scraper/crawl` performs a bounded, same-domain shallow crawl (every discovered URL is SSRF-validated). The scraper page gains a Scrape/Crawl switch, all output modes, demo URLs, and rich per-mode result rendering.
- **Code Gen, deepened** — more first-class frameworks (Astro, Remix, SolidJS, SvelteKit, Django, Flask, Go, static HTML), a new `POST /api/codegen/refine` to iterate on a generated project ("add auth", "convert to TypeScript") through the same path/secret validation, and a detected entry file. The page gains a file tree, per-file viewer/copy, a refine box, and keeps the sandboxed preview.
- **DevOps Agent, deepened** — nine new read-only AWS actions (ECS, ELBv2, Route53, CloudFront, S3 bucket config, SNS, SQS, ECR, STS caller identity); the boto3 plan is enriched with `read_only`, a human `impact` string, and an `estimated_scope`; a deterministic in-process throttle bounds destructive calls. The page renders the enriched plan with impact and service badges.
- **Streaming chat** — `POST /api/chat/stream` streams the answer token by token (Ollama or Gemini) as NDJSON, and the cockpit's "Ask OmniDev anything" bar renders it live with a blinking caret. Watch the model think instead of waiting for a full response.

### 🎨 Changed
- **Cockpit UI** — setup progress is now derived from real signals (backend health, provider/model, model readiness) instead of a hardcoded count; the module launcher links to each tool; mock demo data is clearly labeled "Example".
- **Landing page** — sharper hero, a "How it works" flow, deeper module and trust sections, honest fact chips (100% offline · no account/key/bill · MIT · Gemma 4), and reveal-on-scroll motion.
- **Local model manager** — `GET /api/models` reports provider status (which default text/vision models are installed) plus a curated recommended list, and `POST /api/models/pull` streams `ollama pull` progress as NDJSON. The cockpit surfaces a first-run banner and one-click pull so a new user reaches a working offline setup without a terminal.
- **SSRF guard** — the Web Scraper and Site Preview now validate every target URL and refuse loopback, private, link-local, reserved, and cloud-metadata addresses (`169.254.169.254`, `localhost`, `10/8`, …); the scraper proxy parameter is validated too. Injected page JavaScript may no longer use network primitives (`fetch`/`XMLHttpRequest`/`WebSocket`/…) — closing an SSRF bypass through the page context — and the Vision endpoint caps uploads at 10 MB.
- Project trust & contributor infrastructure: GitHub Actions CI (backend pytest, frontend typecheck/build, macOS swift build), `SECURITY.md`, issue/PR templates, a `Makefile` one-command bootstrap, and `ROADMAP.md`.

### 🗑️ Removed
- **Stale files** — `render.yaml` and the Render sections of `docs/DEPLOYMENT.md` (hosting the backend publicly contradicts the local-first non-goals and would expose the scraper and AWS credentials), `backend/CREDENTIALS.md` (pre-Ollama, Gemini-required era; superseded by the README Configuration section), and a personal grant-application draft that didn't belong in the repo.

### 🔧 Fixed
- **License mismatch** — `LICENSE` now matches the MIT declared in the README badge/footer (was Apache 2.0 text).
- **Version drift** — backend, frontend, and tests now report `0.3.0` (was hardcoded `0.1.0`).
- `backend/README.md` updated to describe the dual-provider (Ollama + Gemini) layer instead of Gemini-only.

## [0.3.0] — 2026-07-03

### ✨ Added
- **Ollama provider** — every AI-backed module (DevOps Agent, Code Gen, Vision Lab) can now run fully offline against a local Ollama server. New settings: `AI_PROVIDER` (`auto`/`gemini`/`ollama`), `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `OLLAMA_VISION_MODEL`. `auto` uses Gemini when a key is set and falls back to Ollama otherwise. Default model is `gemma4:e4b` — Google's edge model (AI Edge Gallery) covering text, structured output, and vision in one ~9.6GB download.
- Provider-agnostic AI layer (`ai_service.py`) with structured-output support on both providers and typed `AIConfigurationError`/`AIResponseError` handling; `/health` now reports the active provider and model.
- Provider-layer test suite (mocked Ollama transport, provider selection, schema conversion).

### 🎨 Changed
- README and docs repositioned around the native macOS app with offline-first AI.
- Landing page rebuilt as a dark, premium product page: privacy-first hero with a real cockpit screenshot, module bento, Gemma 4 offline section, and GitHub Releases download CTA. Replaces the old glassmorphism landing and its div-built fake app preview.

### 🗑️ Removed
- Stale `frontend/public/downloads/OmniDev-macOS.zip` build artifact and local `dist/` output (the path is now gitignored; packages attach to GitHub Releases).

---

## [0.2.0] — 2026-02-15

### ✨ Added
- **Stitch Design System** — Full frontend redesign with Space Grotesk typography, glassmorphism panels, custom scrollbars, and indigo accent palette
- **Comprehensive documentation** — CONTRIBUTING.md, CODE_OF_CONDUCT.md, ARCHITECTURE.md, API.md, DEPLOYMENT.md, DESIGN.md
- **Git repository** initialized with proper `.gitignore` and MIT License
- Custom CSS range slider and input-glass utilities
- Syntax highlighting classes for code blocks

### 🎨 Changed
- Typography upgraded from Inter to **Space Grotesk** (matching Stitch designs)
- Gradient text updated to purple-to-indigo (`#a78bfa → #6567f1`)
- Added `glass-panel`, `glass-nav`, `input-glass`, `glow` CSS utilities

---

## [0.1.0] — 2026-01-13

### ✨ Added
- **DevOps Agent** — Natural language AWS infrastructure management via OpenAI + boto3
- **Web Scraper** — Playwright-powered stealth scraping with Cloudflare bypass, text/HTML/screenshot extraction
- **Vision Lab** — Image analysis and OCR powered by OpenAI GPT-4.1 Vision
- **Cloud Storage** — S3 bucket browser with upload, download, list, and delete operations
- **Location Services** — IP geolocation, forward/reverse geocoding via IPInfo + Nominatim
- **Premium landing page** — Hero, features grid, code demo, testimonials, pricing, FAQ, comparison
- **Feature pages** — Dedicated dashboard for each service with response display
- Backend: FastAPI with Pydantic, async Playwright browser pool, CORS middleware
- Frontend: Next.js 16 + React 19 with Framer Motion animations
- Reusable `FeatureLayout` component for consistent navigation across feature pages

### 🔧 Fixed
- Correct client IP extraction from `X-Forwarded-For` headers for location detection
- Manual location setting with browser `localStorage` persistence
