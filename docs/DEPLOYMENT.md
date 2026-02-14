# 🚀 OmniDev — Deployment Guide

> How to deploy OmniDev to production environments.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development](#local-development)
3. [Docker Deployment](#docker-deployment)
4. [Render Deployment](#render-deployment)
5. [Vercel + Render Split](#vercel--render-split)
6. [Environment Variables](#environment-variables)
7. [Post-Deploy Checklist](#post-deploy-checklist)

---

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.11+ | Backend runtime |
| Node.js | 18+ | Frontend build |
| npm | 9+ | Package management |
| Git | 2.30+ | Version control |
| Docker *(optional)* | 24+ | Container deployment |

---

## Local Development

### Backend

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

**Access:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs

---

## Docker Deployment

### Backend Dockerfile

```dockerfile
# backend/Dockerfile
FROM python:3.13-slim

WORKDIR /app

# System deps for Playwright
RUN apt-get update && apt-get install -y \
    libglib2.0-0 libnss3 libnspr4 libdbus-1-3 \
    libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libdrm2 libxkbcommon0 libatspi2.0-0 libxcomposite1 \
    libxdamage1 libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 \
    libcairo2 libasound2 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install chromium

COPY app/ ./app/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend Dockerfile

```dockerfile
# frontend/Dockerfile
FROM node:22-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:22-alpine AS runner
WORKDIR /app
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

EXPOSE 3000
CMD ["node", "server.js"]
```

### Docker Compose

```yaml
# docker-compose.yml
version: "3.9"

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    env_file:
      - ./backend/.env
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

```bash
# Build and run
docker compose up --build -d

# View logs
docker compose logs -f

# Stop
docker compose down
```

---

## Render Deployment

### Backend (Web Service)

1. **Create** a new **Web Service** on [Render](https://render.com)
2. **Connect** your GitHub repository
3. **Configure:**

   | Setting | Value |
   |---------|-------|
   | **Root Directory** | `backend` |
   | **Runtime** | Python 3 |
   | **Build Command** | `pip install -r requirements.txt && playwright install chromium --with-deps` |
   | **Start Command** | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |

4. **Add Environment Variables:**
   - `OPENAI_API_KEY`
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `AWS_DEFAULT_REGION`
   - `CORS_ORIGINS` = `https://your-frontend.vercel.app`
   - `IPINFO_TOKEN` *(optional)*

### Frontend (Static Site)

1. **Create** a new **Static Site** on Render
2. **Configure:**

   | Setting | Value |
   |---------|-------|
   | **Root Directory** | `frontend` |
   | **Build Command** | `npm install && npm run build` |
   | **Publish Directory** | `out` |

3. **Add Environment Variable:**
   - `NEXT_PUBLIC_API_URL` = `https://your-backend.onrender.com`

---

## Vercel + Render Split

For optimal performance, deploy frontend on **Vercel** and backend on **Render**:

### Frontend on Vercel

1. Import the repo on [Vercel](https://vercel.com)
2. Set **Root Directory** to `frontend`
3. Add env var: `NEXT_PUBLIC_API_URL` = `https://your-backend.onrender.com`
4. Deploy

### Backend on Render

Follow the [Render Backend](#backend-web-service) steps above.

### CORS Configuration

Update `.env` in backend:

```env
CORS_ORIGINS=https://your-app.vercel.app,https://your-custom-domain.com
```

---

## Environment Variables

### Backend (Required)

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | `sk-proj-...` |
| `AWS_ACCESS_KEY_ID` | AWS access key | `AKIA...` |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | `wJalr...` |

### Backend (Optional)

| Variable | Description | Default |
|----------|-------------|---------|
| `AWS_DEFAULT_REGION` | AWS region | `us-east-1` |
| `CORS_ORIGINS` | Allowed origins (comma-separated) | `http://localhost:3000` |
| `IPINFO_TOKEN` | IPInfo API token | — |

### Frontend

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API base URL | `http://localhost:8000` |

---

## Post-Deploy Checklist

- [ ] **Health check**: `GET /health` returns `{"status": "ok"}`
- [ ] **CORS**: Frontend can reach backend without CORS errors
- [ ] **Scraper**: Test a simple URL scrape
- [ ] **Vision**: Upload an image and verify analysis
- [ ] **DevOps**: Run "List my EC2 instances"
- [ ] **Storage**: List S3 buckets
- [ ] **Location**: Detect location works with correct IP
- [ ] **SSL**: Both frontend and backend serve over HTTPS
- [ ] **Env vars**: No secrets in client-side code
- [ ] **Monitoring**: Set up uptime checks on `/health`

---

<p align="center">
  <em>For architecture details, see <a href="ARCHITECTURE.md">ARCHITECTURE.md</a>. For API reference, see <a href="API.md">API.md</a>.</em>
</p>
