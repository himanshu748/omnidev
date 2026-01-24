# OmniDev

OmniDev is an **AI-powered developer workspace** that bundles:
- **AI Chat**
- **Vision**
- **Web Scraper (Playwright)**
- **DevOps / AWS helper**
- **Cloud Storage (S3)**
- **Location utilities**

## Live
- **App**: `https://omnidev-flame.vercel.app`

## Repository structure

```text
omnidev/
├── backend/    # FastAPI services
└── frontend/   # Next.js (App Router)
```

The frontend talks to the backend via Next.js rewrites (local dev defaults to `http://localhost:8000`).

## Local development

### Prerequisites
- Node.js 20+
- Python 3.9+

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

## Environment variables

### Frontend (`frontend/.env.local`)

```env
NEXT_PUBLIC_SUPABASE_URL=https://<project-ref>.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<anon-key>
```

### Backend (`backend/.env` or Render env vars)

```env
APP_ENV=development
FRONTEND_URL=http://localhost:3000

# OpenAI (optional – can also be provided via Settings UI)
OPENAI_API_KEY=

# AWS (optional – can also be provided via Settings UI)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_DEFAULT_REGION=ap-south-1

# Auth verification (Supabase)
# Prefer JWKS for modern Supabase projects:
SUPABASE_JWKS_URL=https://<project-ref>.supabase.co/auth/v1/.well-known/jwks.json
SUPABASE_JWT_ISSUER=https://<project-ref>.supabase.co/auth/v1
#
# Legacy HS256 projects can use:
# SUPABASE_JWT_SECRET=

# Required: server-side secret for API key generation/validation
API_KEY_SALT=<random-hex>
```

## Scraper (what it returns)

`/scraper` runs Playwright and returns:
- `title`
- `text` (visible page text)
- `html` (page HTML)
- optional `screenshot` (base64 PNG)

Example: scraping the live homepage `https://omnidev-flame.vercel.app/` returns title **“OmniDev v1.0 | AI-Powered Developer Platform”** and the landing page text (hero, features, footer).

## Testing

- Backend:

```bash
cd backend
pytest
```

- Frontend:

```bash
cd frontend
npm run lint
npm run build
npm run test
```

See `TESTING_CHECKLIST.md` for the full demo checklist.

