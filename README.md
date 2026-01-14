# OmniDev v4.0

> **All-in-One AI Developer Platform Powered by OpenAI GPT-5 Nano**

![Next.js](https://img.shields.io/badge/Next.js-16-black?style=for-the-badge&logo=next.js)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?style=for-the-badge&logo=fastapi)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--5_Nano-412991?style=for-the-badge&logo=openai)
![Playwright](https://img.shields.io/badge/Playwright-1.40-2eac52?style=for-the-badge&logo=playwright)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python)
![Framer Motion](https://img.shields.io/badge/Framer_Motion-11-FF0055?style=for-the-badge&logo=framer)

## 🚀 Overview

OmniDev is a powerful all-in-one AI developer platform, rebuilt from the ground up with cutting-edge technology. Originally a Python Tkinter desktop application (2024), it's now a modern full-stack web platform featuring:

- 🤖 **AI Chat** - Powered by OpenAI GPT-5 Nano
- 🕷️ **Web Scraper** - Playwright browser automation with stealth mode
- 🛠️ **Smart DevOps Agent** - AI-powered AWS infrastructure management
- 🖼️ **Vision Lab** - Image analysis with GPT-5 Nano Vision
- 📦 **Cloud Storage** - S3 file manager
- 📍 **Location Services** - Geolocation and geocoding



## 🏗️ Architecture

```
OmniDev/
├── backend/                 # FastAPI Python backend
│   ├── app/
│   │   ├── main.py         # Application entry
│   │   ├── config.py       # Environment config
│   │   ├── routers/        # API endpoints
│   │   │   ├── ai.py       # AI chat endpoints
│   │   │   ├── scraper.py  # Web scraping endpoints
│   │   │   ├── devops.py   # DevOps agent
│   │   │   └── ...
│   │   └── services/       # Business logic
│   │       ├── openai_service.py    # GPT-5 Nano
│   │       ├── scraper_service.py   # Playwright
│   │       └── ...
│   └── requirements.txt
├── frontend/                # Next.js 16 frontend
│   └── src/app/            # App Router pages
│       ├── scraper/        # Web Scraper UI
│       └── ...
├── docker-compose.yml       # Container orchestration
└── .env.example            # Environment template
```

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20+
- [uv](https://docs.astral.sh/uv/) (recommended Python package manager)
- OpenAI API key
- Chrome/Chromium (for scraping)
- AWS credentials (optional, for cloud features)

### 1. Clone & Setup

```bash
cd OmniDev

# Copy environment file
cp .env.example backend/.env

# Edit backend/.env and add your OpenAI API key
```

### 2. Start Backend

```bash
cd backend

# Create virtual environment with uv
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies with uv
uv pip install -r requirements.txt

# Install Playwright browsers (required for web scraping)
playwright install chromium

# Start the server
uvicorn app.main:app --reload --port 8000
```

### 3. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

### 4. Open the App

Visit [http://localhost:3000](http://localhost:3000) 🎉

## 🐳 Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build
```

## 🔑 Environment Variables

```env
# OpenAI API (required)
OPENAI_API_KEY=your_openai_api_key

# AWS (optional - for DevOps Agent & Storage)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_DEFAULT_REGION=ap-south-1
```

## 📱 Features

### 🤖 AI Chat
- Powered by OpenAI GPT-5 Nano
- Conversation memory & streaming responses
- Code assistance & debugging

### 🕷️ Web Scraper
- **Playwright-only** for best performance and reliability
- **Anti-detection**: Stealth mode with anti-bot bypass
- **Features**:
  - JavaScript rendering for SPAs
  - Screenshot capture
  - CSS selector extraction
  - Cloudflare bypass capabilities
  - Export to JSON/HTML/TXT

### 🛠️ DevOps Agent
Natural language cloud management:
- "List my EC2 instances"
- "Launch a new t2.micro instance"
- "Show my S3 buckets"
- "What's my infrastructure status?"

### 🖼️ Vision Lab
- Image analysis & description
- OCR text extraction
- Object identification
- Custom analysis prompts

### 📦 Cloud Storage
- Browse S3 buckets
- Upload/download files
- Delete objects

### 📍 Location Services
- IP-based geolocation
- Browser GPS location (precise)
- Location search
- Reverse geocoding
- Google Maps integration

## 🕷️ Web Scraping API

### Scrape a URL
```bash
curl -X POST http://localhost:8000/api/scraper/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "wait_time_ms": 2000,
    "capture_screenshot": true
  }'
```

### Take Screenshot
```bash
curl -X POST http://localhost:8000/api/scraper/screenshot \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

### Check Status
```bash
curl http://localhost:8000/api/scraper/status
```

## 🛠️ Tech Stack

- **Frontend**: Next.js 16, React 19, TypeScript, Tailwind CSS, Framer Motion
- **Backend**: FastAPI, Python 3.12, Playwright
- **AI**: OpenAI GPT-5 Nano
- **Cloud**: AWS boto3

## 👥 Creator

**Himanshu Kumar** (2024 - 2026)
- Rebuilt with modern stack & OpenAI GPT-5 Nano

## 📄 License

MIT License - feel free to use and modify!

---

<p align="center">
  Built with ❤️ using Next.js, FastAPI, OpenAI GPT-5 Nano & Playwright
</p>
