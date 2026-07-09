# 🏗️ Architecture Overview

> OmniDev is a native SwiftUI macOS app that supervises a local Python/FastAPI backend sidecar (plus an optional MCP server).

<br />

## High-Level Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                  NATIVE APP (SwiftUI, macos/)                    │
│                                                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐            │
│  │ DevOps   │ │ Scraper  │ │ Vision   │ │ Storage  │            │
│  │ Agent    │ │ Module   │ │ Lab      │ │ Manager  │            │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘            │
│       └────────────┴────────────┴────────────┘                  │
│            BackendClient (URLSession, loopback only)             │
└─────────────────────────────┬────────────────────────────────────┘
                              │ HTTP/REST (127.0.0.1)
┌─────────────────────────────┴────────────────────────────────────┐
│                       BACKEND (FastAPI)                           │
│                                                                  │
│  main.py ─── Lifespan (Playwright browser pool)                  │
│     │                                                            │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │                     ROUTERS (API Layer)                   │    │
│  │       devops.py  codegen.py  scraper.py  vision.py        │    │
│  │       storage.py                                          │    │
│  └───────────────────────┬──────────────────────────────────┘    │
│  ┌───────────────────────┴──────────────────────────────────┐    │
│  │                   SERVICES (Business Logic)                │    │
│  │    AI provider layer, boto3, Playwright, StackBlitz        │    │
│  └───────────────────────┬──────────────────────────────────┘    │
│  ┌───────────────────────┴──────────────────────────────────┐    │
│  │                    SCHEMAS (Pydantic Models)               │    │
│  └───────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
          │                  │                    │
          ▼                  ▼                    ▼
    ┌──────────┐       ┌──────────┐        ┌──────────┐
    │ Ollama / │       │Playwright│        │ AWS/S3   │
    │ Gemini AI│       │Chromium  │        │ boto3    │
    └──────────┘       └──────────┘        └──────────┘
```

<br />

## Directory Structure

```
omnidev/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py            # FastAPI app entry point + lifespan
│   │   ├── config.py          # Pydantic Settings (env vars)
│   │   ├── routers/           # API endpoint definitions
│   │   │   ├── devops.py      # /api/devops/*
│   │   │   ├── scraper.py     # /api/scraper/*
│   │   │   ├── vision.py      # /api/vision/*
│   │   │   └── storage.py     # /api/storage/*
│   │   ├── services/          # Business logic layer
│   │   │   ├── devops_agent.py
│   │   │   ├── scraper_service.py
│   │   │   ├── vision_service.py
│   │   │   └── storage_service.py
│   │   └── schemas/           # Pydantic request/response models
│   │       ├── devops.py
│   │       ├── scraper.py
│   │       ├── vision.py
│   │       └── storage.py
│   ├── requirements.txt
│   └── .env.example
├── macos/
│   ├── Package.swift          # SwiftPM app definition
│   └── Sources/OmniDevMac/
│       ├── App/               # App entry point
│       ├── Models/            # Routes and stack state
│       ├── Views/             # One SwiftUI view per module + ModuleKit chrome
│       ├── Services/          # BackendClient, LocalStackManager, etc.
│       └── Support/           # Settings, project paths
├── docs/                      # Documentation
├── README.md
├── CONTRIBUTING.md
├── CHANGELOG.md
├── CODE_OF_CONDUCT.md
├── LICENSE (MIT)
└── .gitignore
```

<br />

## Design Patterns

### 1. Router → Service → Schema

Each feature follows a 3-layer pattern:

| Layer | Role | Example |
|-------|------|---------|
| **Router** | HTTP endpoint, request validation | `routers/scraper.py` |
| **Service** | Core business logic, external API calls | `services/scraper_service.py` |
| **Schema** | Pydantic models for input/output typing | `schemas/scraper.py` |

### 2. Lifespan-Managed Resources

Playwright's browser is started once via FastAPI's `lifespan` context manager and shared across all requests via `app.state.browser`. This avoids cold-start overhead per scrape request.

### 3. Native Module Views

Each module in the macOS app follows a consistent pattern:
- One SwiftUI view per module (`macos/Sources/OmniDevMac/Views/`)
- Shared chrome and layout helpers in `ModuleKit.swift`
- Backend calls via `BackendClient`/`BackendModules` over loopback (URLSession, NDJSON streaming for chat and model pulls)

### 4. Design System

App styling is native SwiftUI, with shared tokens and chrome in `ModuleKit.swift` (see [DESIGN.md](DESIGN.md) for the visual language the app inherits).

<br />

## External Services

| Service | Usage | Config |
|---------|-------|--------|
| **Ollama** (local, offline) | DevOps NLU, code generation, and Vision analysis without any API key | `AI_PROVIDER`, `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `OLLAMA_VISION_MODEL` |
| **Google Gemini** (cloud) | Same AI workloads when a key is configured | `GEMINI_API_KEY`, `GEMINI_MODEL` |
| **Context7** | Optional docs grounding for Code Gen prompts | `CONTEXT7_API_KEY` |
| **StackBlitz** | Browser-isolated preview for generated web projects; OmniDev backend does not execute generated code | None |
| **AWS** | EC2/S3 management via boto3 | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` |
| **Playwright** | Headless Chromium for web scraping | Installed via `playwright install chromium` |
