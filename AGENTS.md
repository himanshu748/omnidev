# OmniDev Agent Notes

## Project Shape
- Local-first developer toolkit: a FastAPI backend in `backend/` and a native SwiftUI macOS app in `macos/`. `site/` is the static landing page and Agent Lab.
- Backend modules follow `routers/` -> `services/` -> `schemas/`.
- macOS module views live under `macos/Sources/OmniDevMac/Views/` and share UI chrome through `ModuleKit.swift`; they reach the backend via `Services/BackendClient.swift` / `BackendModules.swift`.

## Common Commands
- Setup: `make setup`
- Backend tests: `make test` (or `cd backend && .venv/bin/pytest -q`)
- macOS build: `cd macos && swift build`
- WebMCP contract checks: `node scripts/check-webmcp.mjs && node scripts/check-agent-lab-webmcp.mjs`

## Conventions
- Keep public copy honest: avoid fake testimonials, unsupported pricing, and claims that imply guaranteed bot-protection bypass.
- Keep API examples aligned with Pydantic schemas in `backend/app/schemas/`.
- Use Gemini naming consistently for AI features unless the implementation changes.
- Code Gen must stay generation-only on the backend: validate returned files, block secret-like output and risky npm scripts, and leave execution to isolated client-side preview/download flows.
- See `CONTRIBUTING.md` for the safety invariants every change must preserve.
