# OmniDev — Product Requirements Document

**Version:** 1.0 · 2026-07-05
**Owner:** himanshu748 · **Repo:** https://github.com/himanshu748/omnidev (local: `/Users/himanshujha/Documents/Codex/omnidev`)
**Status of this doc:** the definitive brief for what OmniDev should become. Written to be pasted into a fresh agent session with zero prior context.

---

## 0. Critical environment notes (read before doing anything)

- **NEVER run builds, dev servers, package installs, or tests inside `~/Documents`** on this machine — the repo lives in an iCloud-synced folder whose file provider stalls processes forever at 0% CPU (broken quota). **Workflow: edit in place, then `rsync` (excluding `.venv`, `node_modules`, `.next`) to a `/tmp` scratch copy and run pytest / tsc / next build / uvicorn there.** Git operations and file edits in `~/Documents` are fine.
- CI (GitHub Actions, `.github/workflows/ci.yml`) runs backend pytest + macOS `swift build` on every push — it is the off-machine verifier.
- ~~Vercel hosts the marketing site.~~ The Next.js web frontend (and the Vercel marketing deploy) was removed in favor of the native SwiftUI app.
- Local Ollama exists on the dev machine but has only `:cloud` models signed into ollama.com; `gemma4:e4b` is not yet pulled locally.

---

## 1. One-liner

**OmniDev is the local-first AI dev cockpit for macOS: a native app that runs Gemma 4 entirely on your machine, gives it safe, human-approved tools (AWS, code generation, scraping, vision, storage), and exposes that local intelligence to any agent harness via MCP.**

Positioning: *"Your AI dev cockpit. Nothing leaves your Mac."*

## 2. Audience (in priority order)

1. **Grant reviewers / employers** evaluating the author's engineering craft — the repo, README, landing page, and app must read as current, serious, and beautifully executed within a 60-second skim.
2. **Developers who will actually run it** — indie/solo devs and privacy-conscious professionals who want AI tooling with zero cloud dependency, zero API keys, zero bills.

## 3. Design language (non-negotiable)

- **Dark and minimal.** Benchmark: **Vercel, Claude Code, Factory AI.** Near-black grounds (`#0A0C10`–`#0E1117`), off-white ink (`#EEF1F7`), ONE accent (electric blue `#4DA2FF`), generous spacing, tight display type (Space Grotesk display + system/Inter body + mono for data).
- **One brand mark everywhere.** `LogoMarkView` in the macOS app (terminal-prompt glyph) is the single source (the original web `LogoMark` component was removed with the frontend); no emojis in navigation or chrome. The old multi-logo/emoji drift was the #1 "outdated" signal — never reintroduce it.
- No AI-slop: no purple gradients, no bouncy easing, no fake testimonials/metrics/logos. Honest facts only ("Runs 100% offline", "MIT licensed", "No account, no key, no bill", "Powered by Gemma 4").
- The name is **OmniDev** (locked; alternatives — Enclave, Onyx, Basalt, Ferro, Klave — are all taken by existing AI products).

## 4. What exists today (v0.3, all verified + CI-green)

> **Note (2026-07):** this section is a historical v0.3 snapshot. The Next.js web frontend and the `/api/preview` + `/api/location` backend modules described below were since removed — the current stack is the native SwiftUI app + FastAPI backend sidecar + optional MCP server.

**Backend** — FastAPI (Python 3.13), 184 passing tests:
- Provider-agnostic AI layer: `AI_PROVIDER=auto|gemini|ollama`; default local `gemma4:e4b` via Ollama (text + structured JSON + vision in one model); Gemini optional fallback. Streaming (`stream_text`) on both providers.
- Endpoints: `/health` · `/api/chat/stream` (NDJSON token streaming) · `/api/models` + `/api/models/pull` (model manager, streams `ollama pull` progress) · `/api/devops/command` (NL→boto3 with **plan preview** {service, operation, params, destructive, read_only, impact, estimated_scope}, human confirmation for destructive ops, `DEVOPS_READ_ONLY` mode, audit log, in-process destructive throttle; ~25 actions across EC2/S3/VPC/IAM/RDS/CloudWatch/Lambda/ECS/ELB/Route53/CloudFront/SNS/SQS/ECR/STS) · `/api/codegen/generate` + `/api/codegen/refine` (validated file output — path/secret/npm-script sanitization, never executed; ~16 frameworks; iterate loop) · `/api/scraper/scrape` (text/html/screenshot/pdf/links/markdown/article/enriched-metadata) + `/api/scraper/crawl` (bounded same-domain) · `/api/vision/analyze` (10 MB cap) · `/api/storage/*` (S3) · `/api/preview/check` · `/api/location/*`.
- Security posture (preserve at all costs): SSRF guard (`url_guard.py`) on every scraper/preview/crawl navigation incl. proxy validation; injected-JS network-primitive ban; secret-scrubbing error boundaries; CORS allowlist (3000/3001/3010 + configured).

**Frontend** — Next.js 16 (App Router), custom CSS in `globals.css` + per-page css files, lucide-react, TS strict:
- `/` marketing landing (dark premium: hero + real cockpit screenshot, how-it-works, module bento with real screenshots, trust grid, honest fact chips, Reveal-on-scroll).
- `/app` cockpit: live backend/health strip, **streaming "Ask OmniDev anything"** chat bar, **Model Manager** (detects missing `gemma4:e4b`, one-click pull with progress), honest setup progress from real signals, dev panel with copy-curl for every route, "Example" labels on demo data.
- Module pages `/devops` `/codegen` `/scraper` `/vision` `/storage` — functional, wired to the API.

**macOS** — SwiftPM app (`macos/`, ~650 lines): SwiftUI + WKWebView shell; `LocalStackManager` launches backend (8010) + frontend (3010) sidecars via `scripts/macos/launch-omnidev.sh`, polls health, menu commands (restart/logs/open-in-browser). Builds in CI.

**Repo hygiene** — MIT (fixed), v0.3.0 aligned, SECURITY.md, CI, Makefile (`make setup/test/backend/frontend/mac`), ROADMAP.md, issue/PR templates, CHANGELOG discipline. Promo video exists at `videos/omnidev-promo/renders/video.mp4` (46s, HyperFrames-rendered) — outside the repo, in `~/n/videos/`.

## 5. The gap (why it can still read as outdated)

1. The **UI is a webview**, not native — fine as a bridge, but "native macOS app" is the promise.
2. **No agent-harness integration** — in 2026, a local-AI tool that other agents can't call is a dead end.
3. README opens with badges + a table instead of a **demo**.
4. Committed screenshots predate the current UI.
5. No conversation memory; codegen can't land output in a real git repo.

## 6. Requirements

### P0 — the killer feature: OmniDev MCP server ("run Gemma inside Claude Code")

Build `omnidev-mcp`: an **MCP (Model Context Protocol) server** that exposes OmniDev's local engine to Claude Code, Claude Desktop, Cursor, and any MCP client.

- **Tools to expose:** `local_llm` (prompt → local Gemma 4 completion, streaming; the headline: *Claude Code can delegate work to a free, private, on-device model*), `local_vision` (image → analysis/OCR), `scrape_url` / `crawl_site` (SSRF-guarded), `generate_project` / `refine_project` (validated files), `aws_plan` (returns the boto3 plan ONLY — MCP never executes destructive actions; approval stays in the OmniDev UI), `list_models` / `pull_model`.
- **Transport:** stdio (`omnidev mcp` entrypoint) speaking to the running FastAPI backend over localhost; ship as a small Python module in `backend/` (e.g. `python -m app.mcp`) plus a one-line Claude Code registration snippet (`claude mcp add omnidev -- python -m app.mcp`) documented in the README.
- **Acceptance:** from a Claude Code session, `local_llm("write a haiku")` returns Gemma output with zero cloud calls; `aws_plan` returns a plan and refuses execution; README shows the registration + a GIF of Claude Code using it.
- Why P0: it converts OmniDev from "another local AI app" into **infrastructure other agents build on** — the strongest possible signal to employers and the community.

### P1 — native macOS migration (two-phase, keep the engine)

**Decision: keep the FastAPI engine; replace the UI shell progressively. Do NOT rewrite the backend in Swift.**
- Phase 1 (bridge hardening): app bundles/discovers Python; first-run onboarding window (native SwiftUI: checks Ollama → offers model pull with progress via `/api/models/pull` → opens cockpit); menu-bar extra (status item: backend health, model, quick actions); Settings window (ports, provider, read-only mode); Sparkle-style update check; proper app icon using the LogoMark.
- Phase 2 (native surfaces): rebuild the **cockpit** and **chat** in SwiftUI (streaming via URLSession to `/api/chat/stream`), keeping module pages in the webview until each earns a native rewrite. Next.js remains only for the hosted marketing site.
- Machine-only (needs the owner): Developer ID signing, notarization, DMG, Homebrew cask, `release.yml` on `v*` tags.

### P1 — the loop: memory + land-in-repo

- **Sessions:** SQLite-backed conversation memory (`/api/chat` gains `session_id`; devops/codegen accept prior context) so "now add auth" works.
- **Git landing:** `POST /api/git/init|commit|status` scoped ONLY to codegen output dirs (reuse codegen's path-safety sets); codegen UI gets "Land in repo" after refine.

### P1 — README as a product page

Hero order: 1-line promise → **demo GIF/video** (embed the promo MP4 or a fresh GIF; re-capture ALL screenshots from the current UI at 2x, no dev badges) → 3-command quickstart (`make setup` · `ollama pull gemma4:e4b` · `make backend`+`make frontend` or the app) → MCP registration snippet → modules table → safety story → architecture diagram. Badges live lower.

### P2

Delete/import models in the manager · scraper result export (save markdown/JSON) · devcontainer/docker-compose · a11y pass (focus rings, reduced-motion, contrast AA everywhere) · landing "Works with Claude Code" section once MCP ships · rotate the DevOps audit log.

## 7. Non-goals

- No cloud/hosted OmniDev service; no accounts, telemetry, or billing — ever.
- No arbitrary code **execution** service (generated code is written, never run server-side; sandboxed iframe preview only).
- No general git server / push to arbitrary repos from the backend.
- No second accent color, no light-mode-first, no rename.

## 8. Success criteria

- A Claude Code user registers the MCP server and offloads a task to local Gemma in < 2 minutes from the README.
- A stranger's 60-second skim (README hero → landing → cockpit) reads "current, native, serious" — no logo drift, no emoji chrome, no stale screenshots.
- `make test` and CI stay green (backend ≥ 184 tests; every new endpoint tested with the existing mock patterns — httpx.MockTransport for Ollama, moto/monkeypatch for AWS).
- The macOS app first-run: install → onboarding pulls model → chat streams — with zero terminal use.

## 9. Architecture (target)

```
┌────────────────────────── macOS app (SwiftUI) ──────────────────────────┐
│  Menu-bar extra · Onboarding · Settings · Native cockpit/chat (P1.2)    │
│  WKWebView bridge for remaining module pages (transitional)             │
└───────────────┬──────────────────────────────────────────────────────────┘
                │ localhost (127.0.0.1:8010)
┌───────────────▼───────────────┐     ┌─────────────────────────────┐
│  FastAPI engine (Python)      │◄────│  omnidev-mcp (stdio)        │◄─ Claude Code /
│  chat·models·devops·codegen·  │     │  local_llm · vision · scrape│   Cursor / any
│  scraper·vision·storage·git   │     │  codegen · aws_plan (RO)    │   MCP client
└───────────────┬───────────────┘     └─────────────────────────────┘
                │
        ┌───────▼────────┐   optional   ┌──────────┐
        │ Ollama · gemma4│◄────────────►│  Gemini  │
        │ (fully local)  │              │ (opt-in) │
        └────────────────┘              └──────────┘
```

## 10. Working agreements for any agent executing this PRD

1. Verify everything: run the backend suite + tsc + `next build` from the `/tmp` scratch copy after every change set; browser-check UI changes; keep CI green.
2. Preserve the security layer (SSRF guard, codegen sanitization, devops approval/read-only/audit) — additive changes only.
3. Match existing idioms (custom CSS w/ prefixed classes, lucide icons, pydantic schemas per module, one test file per module).
4. Small, honest, Conventional-ish commits; update CHANGELOG `[Unreleased]`; never fake data in UI — label examples as examples.
5. Ship order: MCP server → README/demo refresh → macOS Phase 1 → memory+git → macOS Phase 2.
