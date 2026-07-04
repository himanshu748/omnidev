# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### ✨ Added
- **Local model manager** — `GET /api/models` reports provider status (which default text/vision models are installed) plus a curated recommended list, and `POST /api/models/pull` streams `ollama pull` progress as NDJSON. The cockpit surfaces a first-run banner and one-click pull so a new user reaches a working offline setup without a terminal.
- **SSRF guard** — the Web Scraper and Site Preview now validate every target URL and refuse loopback, private, link-local, reserved, and cloud-metadata addresses (`169.254.169.254`, `localhost`, `10/8`, …); the scraper proxy parameter is validated too.
- Project trust & contributor infrastructure: GitHub Actions CI (backend pytest, frontend typecheck/build, macOS swift build), `SECURITY.md`, issue/PR templates, a `Makefile` one-command bootstrap, and `ROADMAP.md`.

### 🔧 Fixed
- **License mismatch** — `LICENSE` now matches the MIT declared in the README badge/footer (was Apache 2.0 text).
- **Version drift** — backend, frontend, and tests now report `0.3.0` (was hardcoded `0.1.0`).
- `backend/README.md` updated to describe the dual-provider (Ollama + Gemini) layer instead of Gemini-only.

## [0.3.0] — 2026-07-03

### ✨ Added
- **Ollama provider** — every AI-backed module (DevOps Agent, Code Gen, Vision Lab) can now run fully offline against a local Ollama server. New settings: `AI_PROVIDER` (`auto`/`gemini`/`ollama`), `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `OLLAMA_VISION_MODEL`. `auto` uses Gemini when a key is set and falls back to Ollama otherwise. Default model is `gemma4:e4b` — Google's edge model (AI Edge Gallery) covering text, structured output, and vision in one ~9.6GB download.
- Provider-agnostic AI layer (`ai_service.py`) with structured-output support on both providers and typed `AIConfigurationError`/`AIResponseError` handling; `/health` now reports the active provider and model.
- Provider-layer test suite (mocked Ollama transport, provider selection, schema conversion).

### 🎨 Changed
- README and docs repositioned around the native macOS app with offline-first AI.
- Landing page rebuilt as a dark, premium product page: privacy-first hero with a real cockpit screenshot, module bento, Gemma 4 offline section, and GitHub Releases download CTA. Replaces the old glassmorphism landing and its div-built fake app preview.

### 🗑️ Removed
- Stale `frontend/public/downloads/OmniDev-macOS.zip` build artifact and local `dist/` output (the path is now gitignored; packages attach to GitHub Releases).

---

## [0.2.0] — 2026-02-15

### ✨ Added
- **Stitch Design System** — Full frontend redesign with Space Grotesk typography, glassmorphism panels, custom scrollbars, and indigo accent palette
- **Comprehensive documentation** — CONTRIBUTING.md, CODE_OF_CONDUCT.md, ARCHITECTURE.md, API.md, DEPLOYMENT.md, DESIGN.md
- **Git repository** initialized with proper `.gitignore` and MIT License
- Custom CSS range slider and input-glass utilities
- Syntax highlighting classes for code blocks

### 🎨 Changed
- Typography upgraded from Inter to **Space Grotesk** (matching Stitch designs)
- Gradient text updated to purple-to-indigo (`#a78bfa → #6567f1`)
- Added `glass-panel`, `glass-nav`, `input-glass`, `glow` CSS utilities

---

## [0.1.0] — 2026-01-13

### ✨ Added
- **DevOps Agent** — Natural language AWS infrastructure management via OpenAI + boto3
- **Web Scraper** — Playwright-powered stealth scraping with Cloudflare bypass, text/HTML/screenshot extraction
- **Vision Lab** — Image analysis and OCR powered by OpenAI GPT-4.1 Vision
- **Cloud Storage** — S3 bucket browser with upload, download, list, and delete operations
- **Location Services** — IP geolocation, forward/reverse geocoding via IPInfo + Nominatim
- **Premium landing page** — Hero, features grid, code demo, testimonials, pricing, FAQ, comparison
- **Feature pages** — Dedicated dashboard for each service with response display
- Backend: FastAPI with Pydantic, async Playwright browser pool, CORS middleware
- Frontend: Next.js 16 + React 19 with Framer Motion animations
- Reusable `FeatureLayout` component for consistent navigation across feature pages

### 🔧 Fixed
- Correct client IP extraction from `X-Forwarded-For` headers for location detection
- Manual location setting with browser `localStorage` persistence
