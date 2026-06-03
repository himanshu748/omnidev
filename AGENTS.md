# OmniDev Agent Notes

## Project Shape
- Full-stack developer toolkit with a FastAPI backend in `backend/` and a Next.js frontend in `frontend/`.
- Backend modules follow `routers/` -> `services/` -> `schemas/`.
- Frontend feature routes live under `frontend/app/` and share UI chrome through `frontend/app/components/FeatureLayout.tsx`.

## Common Commands
- Frontend typecheck: `cd frontend && npm run lint`
- Frontend build: `cd frontend && npm run build`
- Frontend e2e: `cd frontend && npm run test:e2e`
- Backend tests: `cd backend && pytest`

## Conventions
- Keep public copy honest: avoid fake testimonials, unsupported pricing, and claims that imply guaranteed bot-protection bypass.
- Keep API examples aligned with Pydantic schemas in `backend/app/schemas/`.
- Use Gemini naming consistently for AI features unless the implementation changes.
- Code Gen must stay generation-only on the backend: validate returned files, block secret-like output and risky npm scripts, and leave execution to isolated client-side preview/download flows.
