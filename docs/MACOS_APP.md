# macOS App

OmniDev is a **fully native SwiftUI app**. Every surface — Command Center, Chat, DevOps Agent, Code Gen, Web Scraper, Vision Lab, Cloud Storage — is native; there is no embedded web view for app UI. The app supervises one sidecar, the local FastAPI engine, and talks to it over loopback. An optional MCP server rounds out the stack — there is no web frontend.

This is a developer-friendly native app for a local checkout, not yet a signed production installer.

## Surfaces

| Surface | What it does |
|---------|--------------|
| Command Center | Engine status, active provider/model, local model manager (one-click pull with progress), module launcher. |
| Chat | Token streaming from `POST /api/chat/stream` via URLSession — with SQLite conversation memory ("now add auth" works) and a Tools toggle that lets the model call MCP tools; every call renders in the transcript. |
| MCP Marketplace | Install curated MCP servers (Filesystem, Fetch, Memory, Time, Git, Sequential Thinking) the local model can use as tools. Catalog-only, home-scoped paths, minimal child environment. |
| DevOps Agent | Natural-language AWS commands with the enriched boto3 plan preview; destructive actions require an explicit in-app confirmation. |
| Code Gen | Generate validated project files, browse/copy them, refine iteratively, preview HTML output in an isolated `WKWebView` (no base URL, non-persistent data store), save files to a folder you choose, or "Land in Repo" — commit under `~/OmniDev/projects/<name>` (no remotes, never pushed). |
| Web Scraper | All extract modes (text/markdown/article/links/metadata/html/screenshot/pdf) plus the bounded same-domain crawl — every navigation SSRF-guarded by the backend. |
| Vision Lab | Analyze/OCR/custom-prompt a local image (10 MB cap, matching the backend). |
| Cloud Storage | Browse S3 buckets/objects, upload, presigned-URL download, confirmed delete. |

First run opens a native onboarding window: it checks the engine, then Ollama, then the default model — and pulls `gemma4:e4b` with live progress. A menu-bar extra shows engine health and quick actions. The Settings window (⌘,) controls the AI provider, read-only DevOps mode, and the engine port; values reach the sidecar as environment variables when services restart.

## Prerequisites

- macOS 13+
- Python dependencies installed in `backend/` (`make setup-backend`)
- [Ollama](https://ollama.com) for offline AI (the onboarding window handles the model pull)

Node is **not** needed to run the app.

## Build & Launch

```bash
scripts/macos/build-app.sh     # writes dist/mac/OmniDev.app
open dist/mac/OmniDev.app
```

Or during development:

```bash
make mac                       # swift run from macos/
```

The app owns loopback port `8010` for the engine by default (change it in Settings). The launcher writes logs and PIDs under `.omnidev-macos/`; the app menu has Open Logs and Restart Local Services.

## Package a Release Zip

The landing page "Get the app" buttons point to GitHub Releases (`https://github.com/himanshu748/omnidev/releases/latest`). Build the zip to attach to a release with:

```bash
scripts/macos/package-download.sh
```

Signing, notarization, DMG, and a Homebrew cask are tracked in [ROADMAP.md](../ROADMAP.md).

## Scripted Launch (no app)

`scripts/macos/launch-omnidev.sh` starts the backend with health checks:

```bash
OMNIDEV_BACKEND_PORT=8010 scripts/macos/launch-omnidev.sh   # engine only (what the app does)
scripts/macos/stop-omnidev.sh                               # stop everything
```

## Architecture Notes

- `Services/LocalStackManager.swift` — sidecar lifecycle, health polling, provider/model info.
- `Services/BackendClient.swift` + `BackendModules.swift` — thin URLSession bridge to the engine; NDJSON streaming for chat and model pulls; multipart for vision/storage uploads.
- `Views/` — one SwiftUI view per module plus shared chrome in `ModuleKit.swift`; the brand badge is `LogoMarkView` (terminal glyph).
- Generated code is never executed: Code Gen writes files only where you choose, and its preview loads HTML strings into an isolated, non-persistent `WKWebView` with no base URL.
