# OmniDev Backend

All-in-One AI Developer Platform — FastAPI backend.

## Features

| Module | Description |
|---|---|
| DevOps Agent | Manage AWS with natural language |
| Web Scraper | Playwright with stealth mode & Cloudflare bypass |
| Vision Lab | Claude vision for image analysis & OCR |
| Cloud Storage | S3 file manager with upload/download |
| Location Services | IP geolocation, reverse geocoding |

## Quick Start

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium

# Copy and fill in your keys (see CREDENTIALS.md for how to get each one)
cp .env.example .env

# Run
uvicorn app.main:app --reload
```

Open **http://localhost:8000/docs** for the interactive API docs.

## Environment Variables

See `.env.example` for variable names. **For step-by-step help getting each key (Anthropic, AWS, IPInfo), see [CREDENTIALS.md](CREDENTIALS.md).**
