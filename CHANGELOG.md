# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.2.0] — 2026-02-14

### ✨ Added
- **Stitch Design System**: Professional UI designs for all 6 screens created in Google Stitch
- **Documentation Suite**: Comprehensive docs — CONTRIBUTING.md, CODE_OF_CONDUCT.md, ARCHITECTURE.md, API.md, DEPLOYMENT.md, DESIGN.md
- **Git Repository**: Initialized with proper `.gitignore`, MIT License, and conventional commit standards
- **Frontend Upgrades**: Enhanced glassmorphism cards, split-panel layouts, syntax-highlighted JSON results inspired by Stitch prototypes
- **Location Services**: Manual location input with "Set as My Location" feature
- **IP Detection Fix**: Backend now extracts client IP from `X-Forwarded-For` headers instead of server IP

### 🔧 Changed
- Upgraded feature page layouts with split-panel command/output design (DevOps, Scraper)
- Improved result displays with structured JSON rendering and status indicators
- Enhanced navigation with pill-shaped active tab indicators on feature pages
- Refined CSS with additional micro-animations and hover state transitions

### 📦 Dependencies
- Next.js 16.1.6 with Turbopack
- React 19
- FastAPI 0.115+
- Framer Motion for animations

---

## [0.1.0] — 2026-01-13

### ✨ Added
- **DevOps Agent**: Natural language AWS infrastructure management via OpenAI + boto3
  - EC2 instance management (list, launch, stop, terminate)
  - S3 bucket operations (list, create, upload, download)
  - Security group management
  - Destructive action confirmation safeguards
- **Web Scraper**: Playwright-powered stealth scraping engine
  - Text, HTML, and full-page screenshot extraction
  - Stealth mode with anti-detection fingerprinting (Cloudflare bypass)
  - Custom JavaScript execution and CSS selector waiting
  - Configurable page load wait times
- **Vision Lab**: AI-powered image analysis
  - General image analysis via OpenAI GPT-4.1 Vision
  - OCR text extraction
  - Custom prompt queries on uploaded images
  - Token usage and model metadata reporting
- **Cloud Storage**: S3-compatible file manager
  - Multi-bucket browsing and selection
  - File upload with custom key paths
  - Presigned download URL generation
  - File deletion with confirmation
- **Location Services**: Multi-mode geolocation dashboard
  - Client IP detection (with X-Forwarded-For support)
  - IP address lookup via IPInfo
  - Reverse geocoding (coordinates → address) via OpenStreetMap Nominatim
  - Forward geocoding (address → coordinates) with multiple results
  - Google Maps integration links
- **Frontend**: Next.js 16 with premium dark theme
  - Landing page with hero, features grid, code demo, testimonials, pricing, FAQ
  - Individual feature dashboards with FeatureLayout component
  - Framer Motion page transitions and micro-animations
  - Glassmorphism card design with gradient accents
  - Responsive design for mobile and desktop
- **Backend**: FastAPI with async Playwright lifecycle management
  - Modular router/service/schema architecture
  - CORS middleware with configurable origins
  - Health check endpoint
  - Pydantic settings for environment configuration

### 🏗️ Architecture
- Monorepo structure: `backend/` (Python) + `frontend/` (Next.js)
- Backend: `app/routers/` → `app/services/` → `app/schemas/` layered pattern
- Frontend: Next.js App Router with `app/[feature]/page.tsx` convention
- Shared Playwright browser instance across all scraper requests via FastAPI lifespan

---

## [Unreleased]

### Planned
- WebSocket streaming for long-running DevOps operations
- Batch scraping with queue management
- Vision Lab video stream analysis
- Storage: multi-cloud support (GCS, Azure Blob)
- Authentication: Supabase Auth integration
- Rate limiting and API key management
- Docker Compose production deployment
- CI/CD pipeline with GitHub Actions
