# OmniDev

Native macOS AI developer app. Ship, inspect, and operate software from one local cockpit — fully offline with Ollama, or connected with Gemini.

[Architecture](docs/ARCHITECTURE.md) · [API Reference](docs/API.md) · [macOS App](docs/MACOS_APP.md) · [Contributing](CONTRIBUTING.md)

![macOS](https://img.shields.io/badge/macOS-SwiftUI%20%2B%20WebKit-000000?logo=apple&logoColor=white)
![Ollama](https://img.shields.io/badge/AI-Ollama%20(offline)-222222?logo=ollama&logoColor=white)
![Google Gemini](https://img.shields.io/badge/AI-Gemini%20(cloud)-4285F4?logo=google&logoColor=white)
![Python 3.13](https://img.shields.io/badge/Python-3.13-blue?logo=python&logoColor=white)
![Next.js 16](https://img.shields.io/badge/Next.js-16-black?logo=next.js&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.128%2B-009688?logo=fastapi&logoColor=white)
![License MIT](https://img.shields.io/badge/License-MIT-green)

OmniDev is a native macOS app: a SwiftUI/WebKit shell that launches and supervises a local FastAPI backend and Next.js cockpit as sidecar processes. It brings together AI-assisted code generation, AWS operations, browser automation, visual analysis, and S3 file management in one place.

Everything runs on your machine. With a local [Ollama](https://ollama.com) server, every AI-backed module — DevOps Agent, Code Gen, and Vision Lab — works completely offline with no API key and no data leaving your Mac. Prefer a hosted model? Set a free `GEMINI_API_KEY` and OmniDev uses Gemini instead. Risky agent actions always require human confirmation.

## What It Does

| Module | Purpose | Backend |
|--------|---------|---------|
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
ollama pull gemma4:e4b        # text, structured intents, vision & OCR (~9.6GB)
```

No API keys required. [Gemma 4 E4B](https://ollama.com/library/gemma4:e4b) — the same edge model featured in Google's AI Edge Gallery — handles DevOps intent parsing, code generation, and Vision Lab image analysis in a single download, with a 128K context window. On lower-memory machines, `ollama pull gemma4:e2b` and set both model vars to it. Override models and endpoint via `OLLAMA_MODEL`, `OLLAMA_VISION_MODEL`, and `OLLAMA_BASE_URL` in `backend/.env`; any Ollama model with structured-output support works.

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
| `list_models` / `pull_model` | Inspect provider status and pull local models. |

The server is a thin stdio bridge to the running backend (set `OMNIDEV_BACKEND_URL` if yours isn't on `http://127.0.0.1:8000`). From `backend/` you can also run it directly with `python -m app.mcp` or `make mcp`.

## The macOS App

OmniDev ships as a native macOS `.app`: a SwiftUI/WebKit shell (`macos/`) that starts the FastAPI backend (port 8010) and Next.js frontend (port 3010) as managed sidecars, waits for both health checks, and presents the cockpit in a native window with sidebar navigation.

```bash
# Build and run the macOS app from source
./script/build_and_run.sh
```

Stop the sidecars any time with `scripts/macos/stop-omnidev.sh`. See [docs/MACOS_APP.md](docs/MACOS_APP.md) for packaging details. Windows and Linux packages are planned next.

## Product Surface

- `/` is the product landing page: positioning, modules, local-first story, platform direction.
- `/app` is the main cockpit: setup status, command center, agent mode, approvals, and module launcher.
- Feature pages live under `frontend/app/` and share API helpers through `frontend/lib/api.ts`.

## Architecture

```text
omnidev/
├── macos/                       # native SwiftUI/WebKit shell
│   └── Sources/OmniDevMac/
│       ├── App/                 # app entry
│       ├── Services/            # sidecar lifecycle (LocalStackManager)
│       └── Views/               # native window, sidebar, web cockpit
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
├── frontend/
│   ├── app/
│   │   ├── page.tsx             # landing page
│   │   ├── app/page.tsx         # app cockpit
│   │   ├── components/          # shared frontend chrome
│   │   ├── devops/page.tsx
│   │   ├── codegen/page.tsx
│   │   ├── scraper/page.tsx
│   │   ├── vision/page.tsx
│   │   └── storage/page.tsx
│   ├── lib/api.ts
│   └── package.json
├── scripts/macos/               # launch/stop/package sidecar scripts
├── docs/
└── README.md
```

## Quick Start

### Prerequisites

- macOS with Xcode command-line tools (for the native app), or any OS for the dev stack.
- Python 3.11+; Python 3.13 is used for local verification.
- Node.js 20.9+; Node 22 works with Next.js 16.
- [Ollama](https://ollama.com) for offline AI (or a `GEMINI_API_KEY` for cloud AI).

### Option A — Native macOS app

```bash
./script/build_and_run.sh
```

This builds the SwiftUI shell, starts both sidecars, and opens the cockpit in a native window.

### Option B — Dev stack (any OS)

Backend:

```bash
cd backend
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`. Backend API docs are at `http://localhost:8000/docs`.

## Configuration

Create `backend/.env` from `backend/.env.example`.

```bash
# AI provider: auto | gemini | ollama  (auto = Gemini if key set, else local Ollama)
AI_PROVIDER=auto

# Ollama (local, offline) — gemma4:e4b covers text + vision in one model
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma4:e4b
OLLAMA_VISION_MODEL=gemma4:e4b

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

# Local frontend origins
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001
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
| `POST` | `/api/codegen/generate` | Returns validated generated files and instructions. Backend does not execute generated code. |
| `POST` | `/api/scraper/scrape` | Browser-based extraction for text, HTML, screenshots, links, metadata, and PDFs. |
| `POST` | `/api/preview/check` | Captures page preview and basic metadata. |
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
cd frontend && npm run lint
cd frontend && npm run build
cd backend && pytest
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
