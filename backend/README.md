# OmniDev Backend

All-in-One AI Developer Platform — FastAPI backend.

## Features

| Module | Description |
|---|---|
| DevOps Agent | Manage AWS with natural language (Google Gemini + boto3) |
| Web Scraper | Playwright with stealth mode & Cloudflare bypass |
| Vision Lab | Gemini multimodal for image analysis & OCR |
| Cloud Storage | S3 file manager with upload/download |
| Location Services | IP geolocation, reverse geocoding |
| Code Gen | Project generation with optional Context7 docs |

## Quick Start

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium

# Copy and fill in your keys — see .env.example (Gemini: https://aistudio.google.com/apikey)
cp .env.example .env

# Run
uvicorn app.main:app --reload
```

Open **http://localhost:8000/docs** for the interactive API docs.

## Environment Variables

See `.env.example` for variable names (`GEMINI_API_KEY`, `GEMINI_MODEL`, AWS, IPInfo, Context7, CORS). For AWS and IPInfo setup steps, see [CREDENTIALS.md](CREDENTIALS.md).
