<p align="center">
  <br />
  <strong style="font-size: 2rem;">🚀 OmniDev</strong>
  <br />
  <em>All-in-One AI Developer Platform</em>
  <br /><br />
  <a href="#features">Features</a> · <a href="#quick-start">Quick Start</a> · <a href="#api-reference">API Reference</a> · <a href="#architecture">Architecture</a>
  <br /><br />
  <img src="https://img.shields.io/badge/Python-3.13-blue?logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Next.js-16-black?logo=next.js&logoColor=white" alt="Next.js" />
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/OpenAI-GPT--4.1-412991?logo=openai&logoColor=white" alt="OpenAI" />
  <img src="https://img.shields.io/badge/License-MIT-green?logo=opensourceinitiative&logoColor=white" alt="License" />
  <img src="https://img.shields.io/badge/Playwright-Stealth-2EAD33?logo=playwright&logoColor=white" alt="Playwright" />
  <img src="https://img.shields.io/badge/Design-Stitch-6567f1?logo=google&logoColor=white" alt="Stitch Design" />
  <img src="https://img.shields.io/badge/PRs-Welcome-brightgreen?logo=github" alt="PRs Welcome" />
</p>

---

**OmniDev** is a full-stack AI developer platform that combines **DevOps automation**, **stealth web scraping**, **AI vision analysis**, **cloud storage management**, and **location intelligence** into a single, cohesive application. It features a **FastAPI** backend with a beautiful **Next.js 16** frontend designed with **Space Grotesk** typography.

### 📚 Documentation

| Document | Description |
|----------|-------------|
| [Architecture](docs/ARCHITECTURE.md) | System design, directory structure, design patterns |
| [API Reference](docs/API.md) | All endpoints with request/response examples |
| [Design System](docs/DESIGN.md) | Typography, colors, glassmorphism, Stitch screens |
| [Deployment](docs/DEPLOYMENT.md) | Render, Docker, Vercel deployment guides |
| [Contributing](CONTRIBUTING.md) | Branch strategy, commit conventions, code style |
| [Changelog](CHANGELOG.md) | Version history and release notes |
| [Code of Conduct](CODE_OF_CONDUCT.md) | Community standards |



## ✨ Features

| Module | Description | Tech |
|--------|-------------|------|
| 🤖 **DevOps Agent** | Manage AWS infrastructure with natural language commands — list EC2 instances, launch servers, manage security groups | OpenAI + boto3 |
| ⚡ **Code Gen** | Generate full-stack projects (React, Next.js, Streamlit, Node, Python, Vue, Svelte) using live docs from Context7; instructions are ready for Vercel Sandbox | OpenAI + Context7 |
| 🕷️ **Web Scraper** | Playwright-powered stealth scraping with anti-detection, Cloudflare bypass, full-page screenshots, and custom JS execution | Playwright + Stealth |
| 🖼️ **Vision Lab** | AI-powered image analysis, OCR text extraction, and custom visual Q&A | OpenAI Vision |
| 📦 **Cloud Storage** | Full S3 file manager — browse buckets, upload/download files, generate presigned URLs, delete objects | boto3 S3 |
| 📍 **Location Services** | IP geolocation, forward & reverse geocoding, public IP detection | IPInfo + Nominatim |

<br />

## 🏗️ Architecture

```
omnidev/
├── backend/                  # FastAPI (Python 3.13)
│   ├── app/
│   │   ├── main.py           # FastAPI app + Playwright lifespan
│   │   ├── config.py         # Pydantic settings (env vars)
│   │   ├── routers/          # API endpoint definitions
│   │   │   ├── devops.py     # POST /api/devops/command
│   │   │   ├── codegen.py    # POST /api/codegen/generate
│   │   │   ├── scraper.py    # POST /api/scraper/scrape
│   │   │   ├── preview.py    # POST /api/preview/check
│   │   │   ├── vision.py     # POST /api/vision/analyze
│   │   │   ├── storage.py    # GET/POST/DELETE /api/storage/*
│   │   │   └── location.py   # GET /api/location/*
│   │   ├── services/         # Business logic
│   │   │   ├── devops_agent.py
│   │   │   ├── codegen_service.py
│   │   │   ├── context7_service.py
│   │   │   ├── scraper_service.py
│   │   │   ├── preview_service.py
│   │   │   ├── vision_service.py
│   │   │   ├── storage_service.py
│   │   │   └── location_service.py
│   │   └── schemas/          # Pydantic request/response models
│   ├── requirements.txt
│   ├── .env.example
│   └── CREDENTIALS.md        # Step-by-step credential setup guide
├── frontend/                 # Next.js 16 (React 19)
│   ├── app/
│   │   ├── page.tsx          # Landing page (OmniDev hero, features, pricing)
│   │   ├── layout.tsx        # Root layout (Syne + DM Sans + JetBrains Mono)
│   │   ├── globals.css       # Premium dark theme + industrial/AI styling
│   │   ├── components/       # Shared components
│   │   ├── devops/page.tsx   # DevOps Agent UI
│   │   ├── codegen/page.tsx  # Code Gen UI (generate + live preview)
│   │   ├── codegen/review/   # Code Gen · Site Review (UI overview)
│   │   ├── scraper/page.tsx  # Web Scraper UI
│   │   ├── vision/page.tsx   # Vision Lab UI
│   │   ├── storage/page.tsx  # Cloud Storage UI
│   │   └── location/page.tsx # Location Services UI
│   ├── lib/api.ts            # API base URL config
│   └── package.json
├── docs/                     # Documentation
│   ├── ARCHITECTURE.md       # System design & patterns
│   ├── API.md                # Full API reference
│   ├── DESIGN.md             # Design system & Stitch screens
│   └── DEPLOYMENT.md         # Deployment guides
├── CONTRIBUTING.md           # Contribution guidelines
├── CHANGELOG.md              # Version history
├── CODE_OF_CONDUCT.md        # Community standards
├── LICENSE                   # MIT License
├── .gitignore
└── README.md                 # ← You are here
```

### Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.13, FastAPI, Pydantic Settings, Uvicorn |
| **Frontend** | Next.js 16, React 19, Framer Motion, TypeScript, StackBlitz SDK (live previews) |
| **AI** | OpenAI GPT-4.1, Vision API, DALL·E, Context7 (code docs) |
| **Cloud** | AWS (EC2, S3) via boto3 |
| **Scraping** | Playwright (Chromium), playwright-stealth |
| **Geolocation** | IPInfo, OpenStreetMap Nominatim, ipify |
| **HTTP** | httpx (async), python-multipart |

<br />

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+** (tested on 3.13)
- **Node.js 18+** (tested with Node 22)
- **npm** (comes with Node.js)

### 1. Clone the Repository

```bash
git clone https://github.com/himanshu748/omnidev.git
cd omnidev
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate        # macOS/Linux
# .venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium

# Configure environment
cp .env.example .env
# Edit .env with your credentials (see CREDENTIALS.md for help)
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install
```

### 4. Run Both Servers

**Terminal 1 — Backend (port 8000):**
```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

**Terminal 2 — Frontend (port 3000):**
```bash
cd frontend
npm run dev
```

Open **http://localhost:3000** in your browser to see the UI.  
Open **http://localhost:8000/docs** for the interactive Swagger API docs.

<br />

## 🔑 Environment Variables

Create a `backend/.env` file based on `backend/.env.example`:

```bash
# OpenAI (required for DevOps Agent + Vision Lab)
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4.1-mini

# Context7 (optional, recommended for Code Gen)
CONTEXT7_API_KEY=ctx7_...

# AWS (required for DevOps Agent + Cloud Storage)
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_DEFAULT_REGION=us-east-1

# IPInfo (optional — free tier works without a token)
IPINFO_TOKEN=

# CORS (frontend URL)
CORS_ORIGINS=http://localhost:3000
```

> 📖 **Need help getting credentials?** See [`backend/CREDENTIALS.md`](backend/CREDENTIALS.md) for step-by-step instructions for each service.

### Which Credentials Are Needed for Each Feature?

| Feature | OpenAI | AWS | IPInfo |
|---------|--------|-----|--------|
| DevOps Agent | ✅ Required | ✅ Required | — |
| Code Gen | ✅ Required | — | — |
| Web Scraper | — | — | — |
| Vision Lab | ✅ Required | — | — |
| Cloud Storage | — | ✅ Required | — |
| Location Services | — | — | Optional |

> **Web Scraper** and **Location Services** work with zero configuration!

<br />

## 📡 API Reference

All endpoints are prefixed with the backend URL (default: `http://localhost:8000`).

### Health Check

```
GET /health
→ { "status": "ok", "service": "omnidev" }
```

### 🤖 DevOps Agent

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/devops/command` | Execute a natural language AWS command |

**Request Body:**
```json
{
  "message": "List my EC2 instances",
  "confirm_destructive": false
}
```

**Response:**
```json
{
  "action": "list_ec2",
  "params": {},
  "raw_result": [...],
  "summary": "You have 3 EC2 instances...",
  "needs_confirmation": false
}
```

**Supported Actions:** `list_ec2`, `launch_ec2`, `stop_ec2`, `terminate_ec2`, `list_s3_buckets`, `describe_security_groups`

> ⚠️ Destructive actions (`stop_ec2`, `terminate_ec2`) require `confirm_destructive: true`.

---

### 🕷️ Web Scraper

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/scraper/scrape` | Scrape a URL with optional stealth mode |

**Request Body:**
```json
{
  "url": "https://example.com",
  "extract": "text",
  "stealth": true,
  "wait_for": ".main-content",
  "javascript": "document.querySelector('.cookie-btn')?.click()",
  "timeout_ms": 30000
}
```

**Extract Modes:** `text` (inner text), `html` (full HTML), `screenshot` (full-page PNG as base64)

**Response:**
```json
{
  "url": "https://example.com",
  "title": "Example Domain",
  "status_code": 200,
  "content": "...",
  "screenshot_b64": null
}
```

---

### 🖼️ Vision Lab

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/vision/analyze` | Analyze an uploaded image |

**Form Data:**
- `image` (file, required) — The image file
- `mode` (string) — `analyze`, `ocr`, or `custom`
- `prompt` (string) — Custom prompt when mode is `custom`

**Response:**
```json
{
  "mode": "analyze",
  "result": "This image shows...",
  "model": "gpt-4.1-mini",
  "tokens_used": 1250
}
```

---

### ⚡ Code Gen

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/codegen/generate` | Generate a full project for the requested framework |

**Request Body:**
```json
{
  "prompt": "A todo app with dark mode and local storage",
  "framework": "react"
}
```

**Response (simplified):**
```json
{
  "files": [
    { "path": "package.json", "content": "{...}" },
    { "path": "src/main.tsx", "content": "..." }
  ],
  "instructions": "npm install && npm run dev (or run in Vercel Sandbox)"
}
```

> The frontend Code Gen page lets you pick a framework, view generated files, copy code, download a ZIP, and open a live preview via StackBlitz.

---

### 📦 Cloud Storage

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/storage/buckets` | List all S3 buckets |
| `GET` | `/api/storage/files/{bucket}` | List files in a bucket (optional `?prefix=`) |
| `POST` | `/api/storage/upload` | Upload a file (form: `file`, `bucket`, `key`) |
| `GET` | `/api/storage/download/{bucket}/{key}` | Generate presigned download URL |
| `DELETE` | `/api/storage/delete/{bucket}/{key}` | Delete a file |

---

### 📍 Location Services

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/location/me` | Detect server's public IP + location |
| `GET` | `/api/location/ip?ip=8.8.8.8` | Look up any IP (omit for own IP) |
| `GET` | `/api/location/reverse?lat=40.71&lng=-74.01` | Reverse geocode coordinates |
| `GET` | `/api/location/geocode?q=New+York&limit=5` | Forward geocode an address |

<br />

## 🎨 Frontend Features

The frontend provides a **premium dark-themed dashboard** for each service:

- **🏠 Landing Page** — Hero section, feature cards, tech stack, process walkthrough, testimonials, pricing, FAQ
- **🤖 DevOps** — Natural language command input with suggestion chips, structured result display, destructive action safeguards
- **⚡ Code Gen** — Prompt + framework selector, generated file tree + code viewer, one-click copy, ZIP download, and live StackBlitz preview
- **🕷️ Scraper** — URL input with demo suggestions, extraction mode toggles (text/HTML/screenshot), stealth toggle, elapsed time
- **🖼️ Vision** — Drag-and-drop image upload with preview, mode pills (Analyze/OCR/Custom), token & model info
- **📦 Storage** — Bucket chip selector, file browser with icons/sizes/dates, prefix filter, upload form, download links
- **📍 Location** — Tabbed interface (My Location / IP Lookup / Reverse Geocode / Address Search), suggestion chips, Google Maps links

### Design Highlights

- 🌑 Premium dark theme with glassmorphism and subtle grid background
- ✨ Animated gradient orbs and micro-interactions
- 🎯 API endpoint badges showing HTTP methods (GET/POST/DELETE)
- 📱 Fully responsive on mobile, tablet, and desktop
- ⚡ JetBrains Mono for code/technical elements

<br />

## 🧪 Testing the API

You can test the backend directly using `curl`:

```bash
# Health check
curl http://localhost:8000/health

# Scrape a website (no auth required)
curl -X POST http://localhost:8000/api/scraper/scrape \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "extract": "text"}'

# Detect location (no auth required)
curl http://localhost:8000/api/location/me

# Forward geocode
curl "http://localhost:8000/api/location/geocode?q=Eiffel+Tower&limit=3"

# DevOps command (requires OpenAI + AWS keys)
curl -X POST http://localhost:8000/api/devops/command \
  -H "Content-Type: application/json" \
  -d '{"message": "List my EC2 instances"}'
```

Or visit **http://localhost:8000/docs** for the interactive Swagger UI.

<br />

## 📝 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

<br />

## 📚 Documentation

| Document | Description |
|----------|-------------|
| 📋 [CHANGELOG](CHANGELOG.md) | Release history and version notes |
| 🤝 [CONTRIBUTING](CONTRIBUTING.md) | How to contribute to OmniDev |
| 💜 [CODE OF CONDUCT](CODE_OF_CONDUCT.md) | Community standards |
| 🏗️ [Architecture](docs/ARCHITECTURE.md) | System design, data flow, and module deep dives |
| 📡 [API Reference](docs/API.md) | Complete REST API documentation |
| 🚀 [Deployment](docs/DEPLOYMENT.md) | Docker, Render, and Vercel deployment guides |
| 🎨 [Design System](docs/DESIGN.md) | Stitch prototypes, design tokens, and component library |

<br />

---

<p align="center">
  Built with ❤️ using FastAPI, Next.js, and OpenAI
</p>
