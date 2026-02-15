# 🏗️ Architecture Overview

> OmniDev follows a clean **Client-Server** architecture with a Python/FastAPI backend and Next.js frontend.

<br />

## High-Level Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js 16)                     │
│                                                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐│
│  │  DevOps  │ │ Scraper  │ │  Vision  │ │ Storage  │ │Location││
│  │  Agent   │ │Dashboard │ │   Lab    │ │ Manager  │ │Services││
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └───┬────┘│
│       │             │            │             │           │      │
│       └──────┬──────┴─────┬──────┴──────┬──────┴─────┬─────┘      │
│              │            │             │            │            │
│         FeatureLayout   globals.css   api.ts     layout.tsx      │
└──────────────┬────────────┬─────────────┬────────────┬───────────┘
               │            │             │            │
          HTTP/REST    HTTP/REST     HTTP/REST    HTTP/REST
               │            │             │            │
┌──────────────┴────────────┴─────────────┴────────────┴───────────┐
│                       BACKEND (FastAPI)                           │
│                                                                  │
│  main.py ─── Lifespan (Playwright browser pool)                  │
│     │                                                            │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │                     ROUTERS (API Layer)                   │    │
│  │  devops.py  scraper.py  vision.py  storage.py  location.py│   │
│  └──────┬──────────┬──────────┬──────────┬──────────┬────────┘   │
│         │          │          │          │          │             │
│  ┌──────┴──────────┴──────────┴──────────┴──────────┴────────┐   │
│  │                   SERVICES (Business Logic)                │   │
│  │  devops_svc  scraper_svc  vision_svc  storage_svc  loc_svc│   │
│  └──────┬──────────┬──────────┬──────────┬──────────┬────────┘   │
│         │          │          │          │          │             │
│  ┌──────┴──────────┴──────────┴──────────┴──────────┴────────┐   │
│  │                    SCHEMAS (Pydantic Models)               │   │
│  │  devops.py  scraper.py  vision.py  storage.py  location.py│   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                  │
│  config.py ─── Pydantic Settings (env-based configuration)       │
└──────────────────────────────────────────────────────────────────┘
               │            │             │            │
          ┌────┘            │             │            └────┐
          ▼                 ▼             ▼                 ▼
    ┌──────────┐     ┌──────────┐  ┌──────────┐     ┌──────────┐
    │  OpenAI  │     │Playwright│  │  AWS S3  │     │  IPInfo   │
    │ GPT-4.1  │     │(Chromium)│  │  (boto3) │     │ Nominatim │
    └──────────┘     └──────────┘  └──────────┘     └──────────┘
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
│   │   │   ├── storage.py     # /api/storage/*
│   │   │   └── location.py    # /api/location/*
│   │   ├── services/          # Business logic layer
│   │   │   ├── devops_service.py
│   │   │   ├── scraper_service.py
│   │   │   ├── vision_service.py
│   │   │   ├── storage_service.py
│   │   │   └── location_service.py
│   │   └── schemas/           # Pydantic request/response models
│   │       ├── devops.py
│   │       ├── scraper.py
│   │       ├── vision.py
│   │       ├── storage.py
│   │       └── location.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── app/
│   │   ├── layout.tsx         # Root layout (Space Grotesk + JetBrains Mono)
│   │   ├── page.tsx           # Landing page with 8 sections
│   │   ├── globals.css        # Design system (2600+ lines)
│   │   ├── devops/page.tsx    # DevOps Agent dashboard
│   │   ├── scraper/page.tsx   # Web Scraper dashboard
│   │   ├── vision/page.tsx    # Vision Lab dashboard
│   │   ├── storage/page.tsx   # Cloud Storage dashboard
│   │   └── location/page.tsx  # Location Services dashboard
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
- **Typography**: Space Grotesk (display/UI) + JetBrains Mono (code/technical)
- **Glassmorphism**: `.glass-panel`, `.glass-nav` utility classes
- **Responsive**: `clamp()`, `min()`, and media queries throughout

<br />

## External Services

| Service | Usage | Config |
|---------|-------|--------|
| **OpenAI** | GPT-4.1 for DevOps NLU + Vision analysis | `OPENAI_API_KEY` |
| **AWS** | EC2/S3 management via boto3 | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` |
| **Playwright** | Headless Chromium for web scraping | Installed via `playwright install chromium` |
| **IPInfo** | IP geolocation lookups | `IPINFO_TOKEN` (optional) |
| **Nominatim** | Forward/reverse geocoding (OpenStreetMap) | No key required |
