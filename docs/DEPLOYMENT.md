# Deployment Guide

Deploy OmniDev to production using Render, Docker, or split frontend/backend hosts.

## Prerequisites

- Python 3.11+ and Node.js 20.9+
- All environment variables configured (see [Configuration](#configuration))
- Playwright Chromium browser installed

## Configuration

### Required Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# Google Gemini
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.0-flash

# Context7 (optional, used by Code Gen for live docs)
CONTEXT7_API_KEY=

# AWS (for DevOps Agent + Cloud Storage)
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_DEFAULT_REGION=us-east-1

# CORS (comma-separated origins for production)
CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com
```

### Frontend Environment

Create `.env.local` in the `frontend/` directory:

```env
NEXT_PUBLIC_API_URL=https://api.your-domain.com
```

## Option 1: Render Blueprint

The repo includes a root-level `render.yaml` Blueprint with two services:

| Service | Type | URL | Purpose |
|---|---|---|---|
| `omnidev-api` | Python web service | `https://omnidev-api.onrender.com` | FastAPI backend, Playwright browser, Gemini, boto3 |
| `omnidev-web` | Node web service | `https://omnidev-web.onrender.com` | Next.js frontend |

The Blueprint uses Render's free plan and assumes the service names above are available. If Render reports a name collision, rename both services and update:

- Backend `CORS_ORIGINS`
- Frontend `NEXT_PUBLIC_API_URL`

### Render Setup

1. Commit and push `render.yaml` to the `main` branch.
2. Open the Blueprint deeplink:
   `https://dashboard.render.com/blueprint/new?repo=https://github.com/himanshu748/omnidev`
3. Connect GitHub if Render asks.
4. Fill secret environment variables:
   - `GEMINI_API_KEY`
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `CONTEXT7_API_KEY` (optional, leave blank if unused)
5. Apply the Blueprint.
6. Wait for both deploys to finish.
7. Check backend health:

```bash
curl https://omnidev-api.onrender.com/health
```

Expected response:

```json
{"status":"ok","service":"omnidev"}
```

### Render Notes

- The backend build installs Playwright Chromium with Linux dependencies:
  `python -m playwright install --with-deps chromium`.
- The backend start command binds to Render's required `$PORT`.
- The frontend build reads `NEXT_PUBLIC_API_URL` at build time, so update it before redeploying if the API URL changes.
- Render free instances can sleep when idle; first request after sleep may be slow.

## Option 2: Render Backend + Vercel Frontend

### Backend

1. Create a **Web Service** on [render.com](https://render.com)
2. Connect your GitHub repo
3. Configure:
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt && python -m playwright install --with-deps chromium`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Environment**: Python 3
4. Add all environment variables in the Render dashboard

### Frontend

1. Create a Vercel project from the same GitHub repo
2. Configure:
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
3. Set `NEXT_PUBLIC_API_URL` to your Render backend URL
4. Add the Vercel domain to `CORS_ORIGINS` in the backend environment

## Option 3: Docker

### Backend Dockerfile

```dockerfile
FROM python:3.13-slim

WORKDIR /app

# Install system deps for Playwright
RUN apt-get update && apt-get install -y \
    libnss3 libnspr4 libatk-bridge2.0-0 libdrm2 libxcomposite1 \
    libxdamage1 libxrandr2 libgbm1 libpango-1.0-0 libcairo2 \
    libasound2 libatspi2.0-0 libxshmfence1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install chromium

COPY app/ app/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend Dockerfile

```dockerfile
FROM node:22-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:22-alpine AS runner
WORKDIR /app
COPY --from=builder /app/.next .next
COPY --from=builder /app/public public
COPY --from=builder /app/node_modules node_modules
COPY --from=builder /app/package.json package.json

EXPOSE 3000
CMD ["npm", "start"]
```

### Docker Compose

```yaml
version: "3.9"
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    env_file: ./backend/.env
    restart: unless-stopped

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    depends_on:
      - backend
    restart: unless-stopped
```

## Option 4: Vercel Frontend + Railway Backend

### Frontend on Vercel

```bash
npm i -g vercel
cd frontend
vercel --prod
```

Set `NEXT_PUBLIC_API_URL` in Vercel project settings.

### Backend on Railway

1. Push to GitHub
2. Create a Railway project → Deploy from repo
3. Set root directory to `backend`
4. Add environment variables
5. Railway auto-detects Python and deploys

## Production Checklist

- [ ] All environment variables set
- [ ] `CORS_ORIGINS` configured for your domain (not `*`)
- [ ] Playwright Chromium installed in backend container
- [ ] `NEXT_PUBLIC_API_URL` points to production backend
- [ ] HTTPS enabled on both frontend and backend
- [ ] Rate limiting configured (consider adding middleware)
- [ ] Error monitoring set up (e.g., Sentry)
- [ ] Health check endpoint (`/health`) monitored

## Monitoring

### Health Check

```bash
curl https://api.your-domain.com/health
# {"status":"ok","service":"omnidev"}
```

### API Docs

- Swagger UI: `https://api.your-domain.com/docs`
- ReDoc: `https://api.your-domain.com/redoc`
