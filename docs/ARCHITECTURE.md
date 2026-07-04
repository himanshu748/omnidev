# 🏗️ Architecture Overview

> OmniDev follows a clean **Client-Server** architecture with a Python/FastAPI backend and Next.js frontend.

<br />

## High-Level Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js 16)                     │
│                                                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐            │
│  │ DevOps   │ │ Scraper  │ │ Vision   │ │ Storage  │            │
│  │ Agent    │ │Dashboard │ │ Lab      │ │ Manager  │            │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘            │
│       └────────────┴────────────┴────────────┘                  │
│                FeatureLayout + globals.css + api.ts              │
└─────────────────────────────┬────────────────────────────────────┘
                              │ HTTP/REST
┌─────────────────────────────┴────────────────────────────────────┐
│                       BACKEND (FastAPI)                           │
│                                                                  │
│  main.py ─── Lifespan (Playwright browser pool)                  │
│     │                                                            │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │                     ROUTERS (API Layer)                   │    │
│  │       devops.py  codegen.py  scraper.py  vision.py        │    │
│  │       preview.py storage.py                               │    │
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
├── frontend/
│   ├── app/
│   │   ├── layout.tsx         # Root layout and metadata
│   │   ├── page.tsx           # Landing page with 8 sections
│   │   ├── globals.css        # Design system (2600+ lines)
│   │   ├── devops/page.tsx    # DevOps Agent dashboard
│   │   ├── scraper/page.tsx   # Web Scraper dashboard
│   │   ├── vision/page.tsx    # Vision Lab dashboard
│   │   └── storage/page.tsx   # Cloud Storage dashboard
│   ├── components/
│   │   └── FeatureLayout.tsx  # Shared navigation + header layout
│   ├── lib/
│   │   └── api.ts             # Backend API URL helper
│   ├── package.json
│   └── next.config.ts
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

### 3. Frontend Feature Pages

Each feature page follows a consistent pattern:
- Uses `FeatureLayout` for navigation and header
- Client-side component (`"use client"`)
- Local state management via React hooks
- API calls via `fetch(api("/api/..."))` helper
- Displays results with structured layouts

### 4. Design System

All styling flows from `globals.css` via CSS custom properties:
- **No inline colors** — use `var(--accent)`, `var(--bg-card)`, etc.
- **Typography**: offline-safe system sans stack for display/UI + system mono stack for code/technical values
- **Glassmorphism**: `.glass-panel`, `.glass-nav` utility classes
- **Responsive**: `clamp()`, `min()`, and media queries throughout

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
