# OmniDev

Local-first AI developer workbench for shipping, inspecting, and operating software from one cockpit.

[Architecture](docs/ARCHITECTURE.md) · [API Reference](docs/API.md) · [Deployment](docs/DEPLOYMENT.md) · [Contributing](CONTRIBUTING.md)

![Python 3.13](https://img.shields.io/badge/Python-3.13-blue?logo=python&logoColor=white)
![Next.js 16](https://img.shields.io/badge/Next.js-16-black?logo=next.js&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.128%2B-009688?logo=fastapi&logoColor=white)
![Google Gemini](https://img.shields.io/badge/AI-Gemini-4285F4?logo=google&logoColor=white)
![AWS boto3](https://img.shields.io/badge/AWS-boto3-FF9900?logo=amazonaws&logoColor=white)
![License MIT](https://img.shields.io/badge/License-MIT-green)

OmniDev is a full-stack local developer toolkit built with a FastAPI backend and a Next.js frontend. It brings together AI-assisted code generation, AWS operations, browser automation, visual analysis, and S3 file management in one place.

The product direction is a polished local-first developer cockpit: run it on your machine, keep credentials under your control, ask it questions about real infrastructure, and require human confirmation before risky agent actions.

## What It Does

| Module | Purpose | Backend |
|--------|---------|---------|
| DevOps Agent | Parse natural-language AWS requests, inspect resources, and gate destructive actions behind confirmation. | Gemini + boto3 |
| Code Gen | Generate project files for common web/backend frameworks with validation and browser-isolated preview/download flows. | Gemini + optional Context7 |
| Web Scraper | Extract text, HTML, metadata, links, PDFs, or screenshots from authorized pages with Playwright-powered browser automation. | Playwright |
| Vision Lab | Analyze images, run OCR-style prompts, and ask custom visual questions. | Gemini multimodal |
| Cloud Storage | Browse S3 buckets, list objects, upload files, delete objects, and generate presigned download URLs. | boto3 S3 |

## Product Surface

- `/` is the product landing page: positioning, modules, local-first story, platform direction, and calls to launch the app.
- `/app` is the main cockpit: setup status, command center, agent mode, approvals, and module launcher.
- Feature pages live under `frontend/app/` and share API helpers through `frontend/lib/api.ts`.

The current app includes a native macOS SwiftUI/WebKit shell around the Next.js frontend, with the FastAPI backend and frontend dev server managed as local sidecars. Windows and Linux packages are planned next.

## Architecture

```text
omnidev/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app and Playwright lifespan
│   │   ├── config.py            # env/.env-backed settings
│   │   ├── routers/             # HTTP endpoints
│   │   ├── services/            # Gemini, boto3, and Playwright logic
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
├── docs/
├── AGENTS.md
└── README.md
```

## Quick Start

### Prerequisites

- Python 3.11+; Python 3.13 is used for local verification.
- Node.js 20.9+; Node 22 works with Next.js 16.
- npm.

### Backend

```bash
cd backend
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env
uvicorn app.main:app --reload
```

If `python3.13` is not available, use any supported Python 3.11+ interpreter.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`. If that port is occupied, run:

```bash
npm run dev -- -p 3001
```

The backend API docs are available at `http://localhost:8000/docs`.

## Configuration

Create `backend/.env` from `backend/.env.example`.

```bash
# Required for DevOps Agent, Code Gen, and Vision Lab
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

| Module | Gemini | AWS | Context7 |
|--------|--------|-----|----------|
| DevOps Agent | Required | Required through boto3 chain | No |
| Code Gen | Required | No | Optional |
| Web Scraper | No | No | No |
| Vision Lab | Required | No | No |
| Cloud Storage | No | Required through boto3 chain | No |

## API Snapshot

All backend routes are served from `http://localhost:8000` by default.

| Method | Endpoint | Notes |
|--------|----------|-------|
| `GET` | `/health` | Service health check. |
| `POST` | `/api/devops/command` | Natural-language AWS command; destructive operations require `confirm_destructive: true`. |
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

## Verification

Common checks:

```bash
cd frontend && npm run lint
cd frontend && npm run build
cd backend && pytest
```

Local verification on June 18, 2026:

| Check | Result |
|-------|--------|
| Frontend typecheck | Passed via `npm run lint`. |
| Frontend production build | Passed via `npm run build`. |
| Backend tests | Passed: 58 tests. |
| Live `/health` | Passed. |
| Live scraper/preview probes | Passed against local frontend. |
| Live S3 bucket listing | Passed through local AWS profile with zero bucket names printed. |
| AI-only endpoints without `GEMINI_API_KEY` | Return service-unavailable responses instead of crashing. |

## Desktop Packaging Direction

OmniDev includes a native macOS `.app` shell for local developer use. See [docs/MACOS_APP.md](docs/MACOS_APP.md).

The broader packaging plan is:

- macOS native shell now; Windows and Linux builds next.
- Local FastAPI sidecar process managed by the desktop shell.
- Next.js frontend loaded inside the macOS shell, with a future path to bundled static/runtime assets.
- Local credential discovery through the user's existing AWS/Gemini environment.
- Human-in-the-loop approval UI for agent actions before infrastructure changes.

## Documentation

| Document | Description |
|----------|-------------|
| [Architecture](docs/ARCHITECTURE.md) | System design and project structure. |
| [API Reference](docs/API.md) | REST endpoints and examples. |
| [Deployment](docs/DEPLOYMENT.md) | Docker, Render, and Vercel notes. |
| [Design System](docs/DESIGN.md) | Visual system and UI references. |
| [Contributing](CONTRIBUTING.md) | Contribution guide. |
| [Changelog](CHANGELOG.md) | Release notes. |
| [Code of Conduct](CODE_OF_CONDUCT.md) | Community standards. |

## License

MIT. See [LICENSE](LICENSE).
