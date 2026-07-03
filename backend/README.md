# OmniDev Backend

All-in-One AI Developer Platform — FastAPI backend.

## Features

| Module | Description |
|---|---|
| DevOps Agent | Manage AWS with natural language (Google Gemini + boto3) |
| Web Scraper | Playwright browser extraction for authorized pages, screenshots, PDFs, links, and metadata |
| Vision Lab | Gemini multimodal for image analysis & OCR |
| Cloud Storage | S3 file manager with upload/download |
| Code Gen | Gemini project generation with optional Context7 docs, validated file output, and no backend execution |

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

See `.env.example` for variable names (`GEMINI_API_KEY`, `GEMINI_MODEL`, AWS, Context7, CORS). For AWS setup steps, see [CREDENTIALS.md](CREDENTIALS.md).
