# OmniDev v4.0

> **All-in-One AI Developer Platform Powered by OpenAI GPT-4.1 & O3**

![Next.js](https://img.shields.io/badge/Next.js-15-black?style=for-the-badge&logo=next.js)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?style=for-the-badge&logo=fastapi)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4.1-412991?style=for-the-badge&logo=openai)
![Playwright](https://img.shields.io/badge/Playwright-1.40-2eac52?style=for-the-badge&logo=playwright)
![Selenium](https://img.shields.io/badge/Selenium-4.15-43b02a?style=for-the-badge&logo=selenium)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python)

## 🚀 Overview

OmniDev is a powerful all-in-one AI developer platform, rebuilt from the ground up with cutting-edge technology. Originally a Python Tkinter desktop application (2024), it's now a modern full-stack web platform featuring:

- 🤖 **AI Chat** - Powered by OpenAI GPT-4.1 & O3 reasoning model
- 🕷️ **Web Scraper** - Selenium + Playwright browser automation
- 🛠️ **Smart DevOps Agent** - AI-powered AWS infrastructure management
- 🖼️ **Vision Lab** - Image analysis with GPT-4.1 Vision
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
│   │       ├── openai_service.py    # GPT-4.1 & O3
│   │       ├── scraper_service.py   # Selenium/Playwright
│   │       └── ...
│   └── requirements.txt
├── frontend/                # Next.js 15 frontend
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
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Install Playwright browsers (required for web scraping)
playwright install chromium

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
- Powered by OpenAI GPT-4.1 (best for coding)
- O3 reasoning model available for complex tasks
- Conversation memory & streaming responses
- Code assistance & debugging

### 🕷️ Web Scraper
- **Dual-engine support**: Playwright (recommended) & Selenium
- **Anti-detection**: Stealth mode, undetected-chromedriver
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
    "engine": "playwright",
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

## 👥 Creator

**Himanshu Kumar** (2024 - 2026)
- Rebuilt with modern stack & OpenAI GPT-4.1 + O3

## 📄 License

MIT License - feel free to use and modify!

---

<p align="center">
  Built with ❤️ using Next.js, FastAPI, OpenAI GPT-4.1 & Playwright
</p>
