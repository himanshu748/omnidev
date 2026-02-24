# AGENTS.md

## Cursor Cloud specific instructions

### Overview

OmniDev is a full-stack AI developer platform with a **FastAPI** backend (Python) and a **Next.js 16** frontend (React 19/TypeScript). See `README.md` for full architecture and API reference.

### Services

| Service | Port | Start Command |
|---------|------|---------------|
| Backend (FastAPI) | 8000 | `cd backend && source .venv/bin/activate && uvicorn app.main:app --reload` |
| Frontend (Next.js) | 3000 | `cd frontend && npm run dev` |

### Non-obvious caveats

- **`python3.12-venv`** must be installed at the system level (`sudo apt-get install python3.12-venv`) before creating the Python virtual environment. The base VM image does not include it.
- **Playwright Chromium** is launched at backend startup via the FastAPI lifespan handler. The backend will fail to start if `playwright install chromium` has not been run inside the venv. Playwright also needs system dependencies installed via `playwright install --with-deps chromium`.
- **No ESLint config** exists in the frontend. `npm run lint` (`next lint`) errors out on Next.js 16 because it treats `lint` as a directory argument. Use `npx tsc --noEmit` for type-checking instead.
- **No database** is required. The app is stateless; all data comes from external APIs.
- **External API keys are optional** for basic testing. The Web Scraper and Location Services modules work without any credentials. DevOps Agent, Vision Lab, Cloud Storage, RAG Chatbot, and Code Gen require `OPENAI_API_KEY` and/or AWS credentials configured in `backend/.env`.
- The backend `.env` file is created from `backend/.env.example`. All keys default to empty strings, which is safe for startup.
- The frontend connects to the backend at `http://localhost:8000` by default (configured in `frontend/lib/api.ts`). Override with `NEXT_PUBLIC_API_URL` env var if needed.
