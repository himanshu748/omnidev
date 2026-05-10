# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
- **DevOps Agent** — Natural language AWS infrastructure management via the then-configured optional external OpenAI provider + boto3 (current docs use an optional provider abstraction)
- **Web Scraper** — Playwright-powered stealth scraping with Cloudflare bypass, text/HTML/screenshot extraction
- **Vision Lab** — Image analysis and OCR powered by the then-configured optional external OpenAI GPT-4.1 Vision provider (current docs use an optional provider abstraction)
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
