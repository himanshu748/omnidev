# Contributing to OmniDev

Thank you for your interest in contributing to OmniDev! This guide will help you get started.

<br />

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Commit Conventions](#commit-conventions)
- [Pull Request Process](#pull-request-process)
- [Code Style](#code-style)
- [Reporting Issues](#reporting-issues)

<br />

## 📜 Code of Conduct

This project follows our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold these standards.

<br />

## 🚀 Getting Started

### Prerequisites

- Python 3.11+ (tested on 3.13)
- Node.js 18+ (tested with Node 22)
- npm (comes with Node.js)
- Git

### Fork & Clone

```bash
# Fork the repo on GitHub, then:
git clone https://github.com/<your-username>/omnidev.git
cd omnidev
```

### Setup

```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env
# Edit .env with your credentials

# Frontend
cd ../frontend
npm install
```

### Run Locally

```bash
# Terminal 1 — Backend
cd backend && source .venv/bin/activate
uvicorn app.main:app --reload

# Terminal 2 — Frontend
cd frontend && npm run dev
```

<br />

## 🔄 Development Workflow

### Branch Strategy

| Branch | Purpose |
|--------|---------|
| `main` | Stable, production-ready code |
| `develop` | Integration branch for new features |
| `feature/<name>` | New features |
| `bugfix/<name>` | Bug fixes |
| `hotfix/<name>` | Urgent production fixes |
| `docs/<name>` | Documentation updates |

### Creating a Feature Branch

```bash
git checkout develop
git pull origin develop
git checkout -b feature/my-awesome-feature
```

<br />

## 📝 Commit Conventions

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short summary>

<optional body>

<optional footer>
```

### Types

| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Code style (formatting, no logic change) |
| `refactor` | Code restructuring (no feature/fix) |
| `perf` | Performance improvement |
| `test` | Adding or updating tests |
| `chore` | Build process / tooling |
| `ci` | CI/CD configuration |

### Scopes

| Scope | Applies To |
|-------|-----------|
| `backend` | FastAPI backend |
| `frontend` | Next.js frontend |
| `devops` | DevOps Agent module |
| `scraper` | Web Scraper module |
| `vision` | Vision Lab module |
| `storage` | Cloud Storage module |
| `location` | Location Services module |
| `docs` | Documentation |
| `deps` | Dependencies |

### Examples

```
feat(scraper): add proxy rotation support
fix(backend): handle missing API key gracefully
docs(readme): update quick start instructions
refactor(frontend): extract FeatureLayout component
chore(deps): upgrade fastapi to 0.115.0
```

<br />

## 🔀 Pull Request Process

1. **Update your branch** with the latest `develop`:
   ```bash
   git fetch origin
   git rebase origin/develop
   ```

2. **Ensure all checks pass**:
   - Backend starts without errors
   - Frontend builds successfully (`npm run build`)
   - No linting warnings

3. **Write a clear PR description**:
   - What does this PR do?
   - Why is this change needed?
   - Any breaking changes?
   - Screenshots (if UI changes)

4. **Request a review** from a maintainer.

5. **Address feedback** and push updates to your branch.

6. **Squash and merge** once approved.

<br />

## 🎨 Code Style

### Python (Backend)

- Follow [PEP 8](https://peps.python.org/pep-0008/)
- Use type hints for all function parameters and return types
- Use `async def` for endpoint handlers
- Use Pydantic models for request/response schemas
- Keep services in `app/services/`, routers in `app/routers/`, schemas in `app/schemas/`

```python
# ✅ Good
async def scrape(request: ScrapeRequest) -> ScrapeResponse:
    """Scrape a URL and return extracted content."""
    ...

# ❌ Bad
def scrape(data):
    ...
```

### TypeScript (Frontend)

- Use functional components with hooks
- Use TypeScript types (no `any`)
- Use the `"use client"` directive for client components
- Follow the Next.js App Router conventions
- Use the `api()` helper from `lib/api.ts` for backend calls

```tsx
// ✅ Good
const [loading, setLoading] = useState<boolean>(false);
const res = await fetch(api("/api/scraper/scrape"), { ... });

// ❌ Bad
const [loading, setLoading] = useState(false); // implicit type OK for primitives
const res = await fetch("http://localhost:8000/api/scraper/scrape"); // hardcoded URL
```

### CSS

- Use CSS custom properties (variables) from `globals.css`
- Follow the existing naming conventions (camelCase class names)
- Use `var(--accent)`, `var(--bg-card)`, etc. — never hardcode colors
- Keep styles in `globals.css` unless component-specific

<br />

## 🐛 Reporting Issues

When reporting a bug, please include:

1. **Description**: Clear summary of the issue
2. **Steps to Reproduce**: Numbered steps to trigger the bug
3. **Expected Behavior**: What should happen
4. **Actual Behavior**: What actually happens
5. **Environment**: OS, Python version, Node version, browser
6. **Screenshots/Logs**: If applicable

Use the GitHub Issues tab with the appropriate label (`bug`, `enhancement`, `question`).

<br />

---

<p align="center">
  Thank you for contributing to OmniDev! 🚀
</p>
