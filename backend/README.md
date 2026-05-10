# OmniDev Backend

All-in-One AI Developer Platform — FastAPI backend.

## Features

| Module | Description |
|---|---|
| DevOps Agent | Manage AWS with natural language (optional Google Gemini AI provider + optional boto3/AWS) |
| Web Scraper | Playwright with stealth mode & Cloudflare bypass |
| Vision Lab | Configured AI provider for image analysis & OCR (Google Gemini today) |
| Cloud Storage | S3 file manager with upload/download |
| Location Services | IP geolocation, reverse geocoding |
| Code Gen | Project generation with optional Google Gemini AI provider and optional Context7 docs |

## Quick Start

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium

# Copy and fill in keys only for optional external integrations you want to enable
cp .env.example .env

# Run
uvicorn app.main:app --reload
```

Open **http://localhost:8000/docs** for the interactive API docs.

## Environment Variables

See `.env.example` for variable names (`GEMINI_API_KEY`, `GEMINI_MODEL`, AWS, IPInfo, Context7, CORS). Gemini, AWS, IPInfo, and Context7 are optional external integrations; local/default features run without project-specific keys. For AWS and IPInfo setup steps, see [CREDENTIALS.md](CREDENTIALS.md).
