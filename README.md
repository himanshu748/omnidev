# OmniDev

Native macOS AI developer app. Ship, inspect, and operate software from one local cockpit — fully offline with Ollama, or connected with Gemini.

[Architecture](docs/ARCHITECTURE.md) · [API Reference](docs/API.md) · [macOS App](docs/MACOS_APP.md) · [Contributing](CONTRIBUTING.md)

![macOS](https://img.shields.io/badge/macOS-SwiftUI%20%2B%20WebKit-000000?logo=apple&logoColor=white)
![Ollama](https://img.shields.io/badge/AI-Ollama%20(offline)-222222?logo=ollama&logoColor=white)
![Google Gemini](https://img.shields.io/badge/AI-Gemini%20(cloud)-4285F4?logo=google&logoColor=white)
![Python 3.13](https://img.shields.io/badge/Python-3.13-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.128%2B-009688?logo=fastapi&logoColor=white)
![License MIT](https://img.shields.io/badge/License-MIT-green)

OmniDev is a fully native macOS app: every surface — cockpit, chat, DevOps, codegen, scraper, vision, storage — is SwiftUI, backed by a supervised local FastAPI engine on loopback. It brings together AI-assisted code generation, AWS operations, browser automation, visual analysis, and S3 file management in one place.

Everything runs on your machine. With a local [Ollama](https://ollama.com) server, every AI-backed module (Knowledge, DevOps Agent, Code Gen and Vision Lab) works completely offline with no API key and no data leaving your Mac. Prefer a hosted model? Set a free `GEMINI_API_KEY` and OmniDev uses Gemini instead. Risky agent actions always require human confirmation.

## Ask Your Mac, Offline (new in 0.6)

Add any folder (an Obsidian vault, a project's docs, a whole repo) and OmniDev chunks it, embeds it with a small local model (`mxbai-embed-large`, one ~670MB download) and stores the index in `~/.omnidev`. Flip the Knowledge toggle in Chat and answers are grounded in your own files, with citations. Indexing is incremental (only changed files re-embed), the index never leaves your Mac, and the same index is served to Claude Code through MCP (`search_knowledge`).

## Agent Mode (new in 0.6.5)

Flip the Agent toggle in Chat and a prompt becomes a task. OmniDev reads your files, edits them, runs the tests and tells you what it changed, streaming every step as it goes. It runs on the local model by default, so this works with wifi off.

You decide where it may act. Folders you add under Settings, Agent are workspaces: inside one the agent works freely. Everywhere else, and for every shell command, it stops and shows you exactly what it wants to run or change, with Allow Once, Always Allow or Deny. An unanswered prompt is a denial, never an approval.

Shell access is an argv allowlist (git without push or reset, pytest, npm test, swift build, make and friends), so the agent cannot reach a remote or rewrite history. It records your git HEAD before its first change, and never commits on your behalf.

## What It Does

| Module | Purpose | Backend |
|--------|---------|---------|
| Agent | Give it a task: it reads, edits, runs tests and reports back, asking permission outside your workspaces. | Ollama or Gemini tool calling |
| Knowledge | Index your notes, docs, code and chat history locally, then ask grounded questions with file citations. Works with wifi off. | Ollama embeddings + SQLite |
| DevOps Agent | Parse natural-language AWS requests, inspect resources, and gate destructive actions behind confirmation. | Ollama or Gemini + boto3 |
| Code Gen | Generate project files for common web/backend frameworks with validation and browser-isolated preview/download flows. | Ollama or Gemini + optional Context7 |
| Web Scraper | Extract text, HTML, metadata, links, PDFs, or screenshots from authorized pages with Playwright-powered browser automation. | Playwright |
| Vision Lab | Analyze images, run OCR-style prompts, and ask custom visual questions. | Ollama vision or Gemini multimodal |
| Cloud Storage | Browse S3 buckets, list objects, upload files, delete objects, and generate presigned download URLs. | boto3 S3 |

## AI Providers: Offline by Default

OmniDev picks its AI provider through one setting, `AI_PROVIDER`:

| Mode | Behaviour |
|------|-----------|
| `auto` (default) | Uses Gemini when `GEMINI_API_KEY` is set; otherwise falls back to local Ollama. |
| `ollama` | Forces local Ollama — every AI service runs offline. |
| `gemini` | Forces Google Gemini (cloud). |

### Run fully offline with Ollama

```bash
# 1. Install Ollama (https://ollama.com), then:
ollama serve

# 2. Pull the default model — one model covers everything
ollama pull gemma4:12b        # text, structured intents, vision & OCR (~7.6GB, 256K context)
```

No API keys required. [Gemma 4 12B](https://ollama.com/library/gemma4:12b) — the encoder-free unified multimodal model — handles DevOps intent parsing, code generation, and Vision Lab image analysis in a single download, with a 256K context window and the strongest coding of the laptop-class tiers (use Ollama ≥ 0.31 for the Apple Silicon multi-token-prediction speedup). On lower-memory machines, `ollama pull gemma4:e2b` and set both model vars to it. Override models and endpoint via `OLLAMA_MODEL`, `OLLAMA_VISION_MODEL`, and `OLLAMA_BASE_URL` in `backend/.env`; any Ollama model with structured-output support works.

The `/health` endpoint reports the active provider and model.

## Use OmniDev from Claude Code (MCP)

OmniDev ships an [MCP](https://modelcontextprotocol.io) server, so Claude Code, Claude Desktop, Cursor — any MCP client — can delegate work to your **free, private, on-device model** and the rest of the local engine.

```bash
# From the repo root, with the backend set up (make setup) and running (make backend):
claude mcp add omnidev -- "$PWD/backend/.venv/bin/python" "$PWD/backend/mcp_server.py"
```

Then, inside a Claude Code session:

> Use the omnidev local_llm tool to write a haiku about local models.

| Tool | What it does |
|------|--------------|
| `local_llm` | Text generation on the local Gemma 4 model — zero cloud calls, zero cost. |
| `local_vision` | Analyze or OCR a local image with the on-device vision model. |
| `scrape_url` / `crawl_site` | SSRF-guarded Playwright scraping and bounded same-domain crawling. |
| `generate_project` / `refine_project` | Validated multi-file codegen — files are returned as data, never written or executed. |
| `aws_plan` | Preview the boto3 plan for a natural-language AWS command. **Never executes** — approval stays in the OmniDev UI. |
| `search_knowledge` / `index_folder` / `list_knowledge_sources` | Query and manage the local knowledge index. Claude Code inherits everything you indexed, fully offline. |
| `list_models` / `pull_model` | Inspect provider status and pull local models. |

The server is a thin stdio bridge to the running backend (set `OMNIDEV_BACKEND_URL` if yours isn't on `http://127.0.0.1:8000`). From `backend/` you can also run it directly with `python -m app.mcp` or `make mcp`.

MCP works in both directions: the app's **MCP Marketplace** installs curated servers (Filesystem, Fetch, Memory, Time, Git, Sequential Thinking) whose tools Gemma 4 calls from chat — flip the Tools toggle and watch every call land in the transcript. Only the curated catalog can be installed, folder access is scoped to directories you pick inside your home folder, and server processes never see backend credentials.

## The macOS App

OmniDev ships as a native macOS `.app` (`macos/`): pure SwiftUI — Command Center, streaming Chat, and all five modules are native views over the local engine (port 8010). The app supervises only the FastAPI sidecar; Node/Next.js is not needed to run it. First launch opens a native onboarding window that checks Ollama and pulls `gemma4:12b` with live progress, a menu-bar extra tracks engine health, and Settings (⌘,) controls provider, read-only DevOps mode, and the engine port.

```bash
# Build and run the macOS app from source
./script/build_and_run.sh
```

Stop the engine sidecar any time with `scripts/macos/stop-omnidev.sh`. See [docs/MACOS_APP.md](docs/MACOS_APP.md) for packaging details. Windows and Linux packages are planned next.

## Claude Code on the Local Model

Ollama exposes an Anthropic-compatible API, so Claude Code can run entirely on the same local Gemma model OmniDev manages — no cloud, no API key:

```bash
make claude-local
# or directly:
ANTHROPIC_BASE_URL=http://localhost:11434 ANTHROPIC_AUTH_TOKEN=ollama claude --model gemma4:12b
```

Since OmniDev's onboarding installs Ollama's default model for you, any machine running OmniDev is one command away from a fully-offline Claude Code session. Expect weaker tool-calling than Claude's own models — best for quick offline edits, not complex agentic work. OmniDev's MCP server (`claude mcp add omnidev`) is the complementary integration: cloud Claude for the reasoning, free local Gemma for delegated generation.

## Product Surface

- The native macOS app is the product: Command Center, streaming Chat, and all module pages are SwiftUI views over the local FastAPI engine.
- The backend also serves interactive API docs at `/docs` and an MCP server for external agents.

## Architecture

```text
omnidev/
├── macos/                       # fully native SwiftUI app
│   └── Sources/OmniDevMac/
│       ├── App/                 # app entry, menu-bar extra, Settings
│       ├── Services/            # sidecar lifecycle + URLSession API bridge
│       └── Views/               # cockpit, chat, and all module views
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app and Playwright lifespan
│   │   ├── config.py            # env/.env-backed settings (AI provider, models)
│   │   ├── routers/             # HTTP endpoints
│   │   ├── services/
│   │   │   ├── ai_service.py    # provider layer: Ollama (local) / Gemini (cloud)
│   │   │   └── ...              # boto3, Playwright, codegen, vision logic
│   │   └── schemas/             # Pydantic request/response models
│   ├── requirements.txt
│   └── .env.example
├── scripts/macos/               # launch/stop/package sidecar scripts
├── docs/
└── README.md
```

## Quick Start

### Prerequisites

- macOS with Xcode command-line tools (for the native app), or any OS for the backend alone.
- Python 3.11+; Python 3.13 is used for local verification.
- [Ollama](https://ollama.com) for offline AI (or a `GEMINI_API_KEY` for cloud AI).

### Option A — Download the app (recommended)

Grab `OmniDev-vX.Y.Z.dmg` from [GitHub Releases](https://github.com/himanshu748/omnidev/releases), open it, and drag `OmniDev.app` to Applications (a zip of the same app is also attached). The build is unsigned, so on first launch right-click → Open (or `xattr -d com.apple.quarantine /Applications/OmniDev.app`).

The engine self-installs into `~/Library/Application Support/OmniDev` on first run (needs Python 3.11+ on the machine) and starts automatically every time the app opens. In-app **Check for Updates…** points at new releases.

### Option B — Build from source

```bash
./script/build_and_run.sh
```

This builds the SwiftUI app, starts the FastAPI engine sidecar from the checkout, and opens the native window.

### Option C — Backend only (any OS)

```bash
cd backend
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env
uvicorn app.main:app --reload
```

API docs are at `http://localhost:8000/docs`.

## Configuration

Create `backend/.env` from `backend/.env.example`.

```bash
# AI provider: auto | gemini | ollama  (auto = Gemini if key set, else local Ollama)
AI_PROVIDER=auto

# Ollama (local, offline) — gemma4:12b covers text + vision in one model
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma4:12b
OLLAMA_VISION_MODEL=gemma4:12b

# Gemini (cloud, optional — free key at https://aistudio.google.com/apikey)
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.0-flash

# Optional docs grounding for Code Gen
CONTEXT7_API_KEY=

# Optional explicit AWS credentials.
# If omitted, boto3 uses the standard AWS credential chain:
# ~/.aws/credentials, AWS SSO/session env, instance role, etc.
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_DEFAULT_REGION=us-east-1

```

Credential needs by module:

| Module | AI (Ollama or Gemini) | AWS | Context7 |
|--------|----------------------|-----|----------|
| DevOps Agent | Required (offline OK with Ollama) | Required through boto3 chain | No |
| Code Gen | Required (offline OK with Ollama) | No | Optional |
| Web Scraper | No | No | No |
| Vision Lab | Required (offline OK with Ollama) | No | No |
| Cloud Storage | No | Required through boto3 chain | No |

## API Snapshot

All backend routes are served from `http://localhost:8000` by default (`8010` under the macOS app).

| Method | Endpoint | Notes |
|--------|----------|-------|
| `GET` | `/health` | Service health check; reports active AI provider and model. |
| `POST` | `/api/devops/command` | Natural-language AWS command; destructive operations require `confirm_destructive: true`. |
| `POST` | `/api/devops/plan` | Plan preview for a natural-language AWS command — never executes (used by the MCP `aws_plan` tool). |
| `POST` | `/api/chat/stream` | Streaming chat with SQLite session memory (`session_id`), optional MCP tool calling (`use_tools`) and knowledge grounding (`use_knowledge`). |
| `POST` | `/api/knowledge/sources` | Register a folder (or chat history) in the local knowledge index; `/api/knowledge/search` retrieves grounded excerpts. |
| `GET` | `/api/mcp/catalog` | Curated MCP server catalog; `/api/mcp/servers` CRUD + per-server tool listing. |
| `POST` | `/api/git/land` | Commit a validated generated project under `~/OmniDev/projects/<slug>` — no shell, no hooks, no remotes. |
| `POST` | `/api/codegen/generate` | Returns validated generated files and instructions. Backend does not execute generated code. |
| `POST` | `/api/scraper/scrape` | Browser-based extraction for text, HTML, screenshots, links, metadata, and PDFs. |
| `POST` | `/api/vision/analyze` | Multipart image analysis. |
| `GET` | `/api/storage/buckets` | Lists S3 buckets as `{ name, creation_date }` objects. |
| `GET` | `/api/storage/files` | Lists S3 objects for a bucket and optional prefix. |
| `POST` | `/api/storage/upload` | Uploads a file to S3. |
| `GET` | `/api/storage/download` | Returns a presigned download URL. |
| `DELETE` | `/api/storage/files` | Deletes an S3 object. |

See [docs/API.md](docs/API.md) for request and response examples.

## Agent Safety

- Generated code is returned as files for review, download, or isolated browser preview; OmniDev does not run generated projects on the backend.
- Code Gen blocks unsafe paths, duplicate case-insensitive paths, secret-like outputs, risky npm lifecycle hooks, and suspicious script bodies.
- DevOps operations are mapped to explicit boto3 actions before execution.
- Destructive DevOps actions require a confirmation flag.
- AWS credentials stay local and are resolved by boto3; no credential values should be committed to the repo.
- In Ollama mode, prompts and images never leave your machine.

## Verification

Common checks:

```bash
cd backend && pytest
cd macos && swift build
```

## Documentation

| Document | Description |
|----------|-------------|
| [Architecture](docs/ARCHITECTURE.md) | System design and project structure. |
| [API Reference](docs/API.md) | REST endpoints and examples. |
| [macOS App](docs/MACOS_APP.md) | Native shell build and packaging. |
| [Deployment](docs/DEPLOYMENT.md) | Local-first policy; marketing-site and app releases. |
| [Design System](docs/DESIGN.md) | Visual system and UI references. |
| [Contributing](CONTRIBUTING.md) | Contribution guide. |
| [Changelog](CHANGELOG.md) | Release notes. |
| [Code of Conduct](CODE_OF_CONDUCT.md) | Community standards. |

## License

MIT. See [LICENSE](LICENSE).
