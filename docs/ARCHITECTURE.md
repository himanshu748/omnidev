# 🏗️ OmniDev — Architecture

> Detailed technical architecture of the OmniDev AI Developer Platform.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [High-Level Architecture](#high-level-architecture)
3. [Backend Architecture](#backend-architecture)
4. [Frontend Architecture](#frontend-architecture)
5. [Data Flow](#data-flow)
6. [Module Deep Dives](#module-deep-dives)
7. [Security Considerations](#security-considerations)

---

## System Overview

OmniDev is a **monorepo** containing two main applications:

| Component | Technology | Port | Directory |
|-----------|-----------|------|-----------|
| **Backend** | Python 3.13 + FastAPI | `:8000` | `backend/` |
| **Frontend** | Next.js 16 + React 19 | `:3000` | `frontend/` |

The backend serves as an **API gateway** that orchestrates calls to external services (OpenAI, AWS, IPInfo, OSM). The frontend is a **standalone Next.js app** that communicates with the backend via REST.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     USER (Browser)                      │
│                  Next.js 16 Frontend                    │
│          React 19 • Framer Motion • TypeScript          │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP (REST)
                       ▼
┌─────────────────────────────────────────────────────────┐
│                   FastAPI Backend                        │
│              Uvicorn ASGI • Python 3.13                  │
│                                                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │  DevOps  │ │ Scraper  │ │  Vision  │ │ Storage  │   │
│  │  Router  │ │  Router  │ │  Router  │ │  Router  │   │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘   │
│       │             │            │             │         │
│  ┌────▼─────┐ ┌────▼─────┐ ┌────▼─────┐ ┌────▼─────┐   │
│  │  DevOps  │ │ Scraper  │ │  Vision  │ │ Storage  │   │
│  │ Service  │ │ Service  │ │ Service  │ │ Service  │   │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘   │
│       │             │            │             │         │
│  ┌────▼─────┐ ┌────▼─────┐ ┌────▼─────┐ ┌────▼─────┐   │
│  │  DevOps  │ │ Scraper  │ │  Vision  │ │ Storage  │   │
│  │  Schema  │ │  Schema  │ │  Schema  │ │  Schema  │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │               Location Module                     │   │
│  │        Router → Service → Schema                  │   │
│  └──────────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────────┘
                       │
          ┌────────────┼────────────────────┐
          ▼            ▼                    ▼
   ┌────────────┐ ┌──────────┐     ┌──────────────┐
   │   OpenAI   │ │   AWS    │     │  Third-Party  │
   │  GPT-4.1   │ │ EC2, S3  │     │  IPInfo, OSM  │
   └────────────┘ └──────────┘     └──────────────┘
```

---

## Backend Architecture

### Directory Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app with lifespan
│   ├── config.py             # Pydantic Settings
│   ├── routers/              # API route handlers
│   │   ├── devops.py
│   │   ├── scraper.py
│   │   ├── vision.py
│   │   ├── storage.py
│   │   └── location.py
│   ├── services/             # Business logic
│   │   ├── devops_service.py
│   │   ├── scraper_service.py
│   │   ├── vision_service.py
│   │   ├── storage_service.py
│   │   └── location_service.py
│   └── schemas/              # Pydantic request/response models
│       ├── devops.py
│       ├── scraper.py
│       ├── vision.py
│       ├── storage.py
│       └── location.py
├── requirements.txt
├── .env.example
└── .env                      # (git-ignored)
```

### Layered Pattern

Every module follows the same **Router → Service → Schema** pattern:

1. **Router** (`routers/`): Handles HTTP I/O — validates input, calls service, returns response.
2. **Service** (`services/`): Contains pure business logic — interacts with external APIs, processes data.
3. **Schema** (`schemas/`): Pydantic models for request validation and response serialization.

### App Lifecycle

The FastAPI app uses **lifespan context** to manage a single Playwright browser instance:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    pw = await async_playwright().start()
    browser = await pw.chromium.launch(headless=True)
    app.state.browser = browser
    yield
    await browser.close()
    await pw.stop()
```

This avoids cold-starting a browser on every scrape request.

### Configuration

Uses `pydantic-settings` with `.env` file:

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | ✅ | OpenAI API key for GPT-4.1 |
| `AWS_ACCESS_KEY_ID` | ✅ | AWS credentials |
| `AWS_SECRET_ACCESS_KEY` | ✅ | AWS credentials |
| `AWS_DEFAULT_REGION` | ❌ | Default: `us-east-1` |
| `IPINFO_TOKEN` | ❌ | IPInfo API for enhanced geo data |
| `CORS_ORIGINS` | ❌ | Default: `http://localhost:3000` |

---

## Frontend Architecture

### Directory Structure

```
frontend/
├── app/
│   ├── layout.tsx            # Root layout (fonts, metadata)
│   ├── page.tsx              # Landing page (/)
│   ├── globals.css           # Design system + all styles
│   ├── devops/page.tsx       # DevOps Agent (/devops)
│   ├── scraper/page.tsx      # Web Scraper (/scraper)
│   ├── vision/page.tsx       # Vision Lab (/vision)
│   ├── storage/page.tsx      # Cloud Storage (/storage)
│   ├── location/page.tsx     # Location Services (/location)
│   └── components/
│       └── FeatureLayout.tsx  # Shared layout for feature pages
├── lib/
│   └── api.ts                # API base URL helper
├── package.json
├── next.config.ts
└── tsconfig.json
```

### Design System

All styles live in `globals.css` using CSS custom properties:

| Token | Value | Usage |
|-------|-------|-------|
| `--bg` | `#06090f` | Page background |
| `--bg-card` | `rgba(14, 21, 38, 0.65)` | Card backgrounds |
| `--accent` | `#6366f1` | Primary indigo accent |
| `--accent3` | `#a78bfa` | Secondary purple accent |
| `--emerald` | `#34d399` | Success states |
| `--rose` | `#f87171` | Error states |
| `--border` | `rgba(42, 62, 102, 0.4)` | Card borders |

### Component Patterns

- **`"use client"`**: All feature pages are Client Components (state, effects, API calls)
- **`FeatureLayout`**: Reusable wrapper providing navigation + page header for feature pages
- **`api(path)`**: Helper function to construct backend API URLs

### Animations

Uses Framer Motion for:
- Page entrance animations (fade + slide)
- Staggered grid reveals
- Interactive hover effects
- Smooth section transitions

---

## Data Flow

### Example: Web Scraper Request

```
User enters URL → clicks "Start Scraping"
       │
       ▼
Frontend: fetch(api("/api/scraper/scrape"), {
  method: "POST",
  body: JSON.stringify({ url, extract, stealth, ... })
})
       │
       ▼
Backend Router: POST /api/scraper/scrape
  → Validates ScrapeRequest (Pydantic)
  → Calls scraper_service.scrape()
       │
       ▼
Scraper Service:
  → Opens new page in shared Playwright browser
  → Applies stealth patches (if enabled)
  → Navigates to URL, waits for content
  → Extracts text/HTML/screenshot
  → Returns ScrapeResponse
       │
       ▼
Frontend: Displays results (text, HTML, or image)
```

---

## Module Deep Dives

### 1. DevOps Agent
- **Flow**: User command → OpenAI parses intent → maps to boto3 action → executes → returns result
- **Safety**: Destructive actions require explicit `confirm: true` flag
- **Supported**: EC2 (list, launch, stop, terminate), S3 (list, create), Security Groups

### 2. Web Scraper
- **Engine**: Playwright Chromium with `playwright-stealth` patches
- **Modes**: `text` (innerText), `html` (outerHTML), `screenshot` (full-page PNG)
- **Features**: Custom JS execution, CSS selector waiting, configurable load delay

### 3. Vision Lab
- **Model**: OpenAI GPT-4.1 Vision API
- **Modes**: `analyze` (general), `ocr` (text extraction), `custom` (user prompt)
- **Input**: Base64-encoded image upload via multipart form

### 4. Cloud Storage
- **Provider**: AWS S3 via boto3
- **Operations**: List buckets, list objects, upload, download (presigned URL), delete
- **Filtering**: Prefix-based object filtering

### 5. Location Services
- **IP Detection**: ipify.org for public IP
- **IP Geolocation**: IPInfo API
- **Geocoding**: OpenStreetMap Nominatim (forward + reverse)
- **Client IP**: Extracted from `X-Forwarded-For` header for accurate location

---

## Security Considerations

| Concern | Mitigation |
|---------|-----------|
| API Keys | Stored in `.env`, never exposed to frontend |
| CORS | Restricted to configured origins |
| Destructive AWS ops | Require explicit confirmation flag |
| Scraper abuse | Rate limiting recommended for production |
| File upload size | Configured via FastAPI/Uvicorn limits |
| XSS | React auto-escapes rendered content |

---

<p align="center">
  <em>For API reference, see <a href="API.md">API.md</a>. For deployment, see <a href="DEPLOYMENT.md">DEPLOYMENT.md</a>.</em>
</p>
