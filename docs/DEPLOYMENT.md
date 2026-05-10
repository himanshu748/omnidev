# 🚀 Deployment Guide

> Deploy OmniDev to production using various hosting providers.

<br />

## Prerequisites

- Python 3.11+ and Node.js 18+
- All environment variables configured (see [Configuration](#configuration))
- Playwright Chromium browser installed

<br />

## Configuration

### Required Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# Optional AI provider (Google Gemini; needed for DevOps Agent, Code Gen, Vision Lab)
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.0-flash

# Optional cloud provider (AWS; needed for DevOps Agent + Cloud Storage)
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_DEFAULT_REGION=us-east-1

# Optional geolocation provider (IPInfo; Location Services have keyless defaults)
IPINFO_TOKEN=...

# CORS (comma-separated origins for production)
CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com
```

### Frontend Environment

Create `.env.local` in the `frontend/` directory:

```env
NEXT_PUBLIC_API_URL=https://api.your-domain.com
```

<br />

## Option 1: Render (Recommended)

### Backend

1. Create a **Web Service** on [render.com](https://render.com)
2. Connect your GitHub repo
3. Configure:
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt && playwright install chromium && playwright install-deps`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Environment**: Python 3
4. Add all environment variables in the Render dashboard

### Frontend

1. Create a **Static Site** on Render
2. Configure:
   - **Root Directory**: `frontend`
   - **Build Command**: `npm install && npm run build`
   - **Publish Directory**: `frontend/out` (or use Next.js standalone)
3. Set `NEXT_PUBLIC_API_URL` to your backend URL

<br />

## Option 2: Docker

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
      - NEXT_PUBLIC_API_URL=http://backend:8000
    depends_on:
      - backend
    restart: unless-stopped
```

<br />

## Option 3: Optional Vercel (Frontend) + Railway (Backend)

### Frontend on Vercel (optional external deployment provider)

```bash
npm i -g vercel
cd frontend
vercel --prod
```

Set `NEXT_PUBLIC_API_URL` in Vercel project settings if you choose this optional external deployment provider.

### Backend on Railway

1. Push to GitHub
2. Create a Railway project → Deploy from repo
3. Set root directory to `backend`
4. Add environment variables
5. Railway auto-detects Python and deploys

<br />

## Production Checklist

- [ ] All environment variables set
- [ ] `CORS_ORIGINS` configured for your domain (not `*`)
- [ ] Playwright Chromium installed in backend container
- [ ] `NEXT_PUBLIC_API_URL` points to production backend
- [ ] HTTPS enabled on both frontend and backend
- [ ] Rate limiting configured (consider adding middleware)
- [ ] Error monitoring set up (e.g., Sentry)
- [ ] Health check endpoint (`/health`) monitored

<br />

## Monitoring

### Health Check

```bash
curl https://api.your-domain.com/health
# {"status":"ok","service":"omnidev"}
```

### API Docs

- Swagger UI: `https://api.your-domain.com/docs`
- ReDoc: `https://api.your-domain.com/redoc`
