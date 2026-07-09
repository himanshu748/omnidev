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
- macOS with Xcode command-line tools (for the native app; the backend alone runs on any OS)
- [Ollama](https://ollama.com) for local AI, or a `GEMINI_API_KEY`
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
# Edit .env with your credentials (optional — the defaults run fully local)
```

### Run Locally

```bash
# Backend only
cd backend && source .venv/bin/activate
uvicorn app.main:app --reload

# Native macOS app (starts its own backend sidecar)
make mac
```

### Test

```bash
make test                  # backend pytest suite
cd macos && swift build    # native app compiles
```

<br />

## 🔄 Development Workflow

### Branch Strategy

| Branch | Purpose |
|--------|---------|
| `main` | Stable, release-ready code |
| `feature/<name>` | New features |
| `bugfix/<name>` | Bug fixes |
| `docs/<name>` | Documentation updates |

### Creating a Feature Branch

```bash
git checkout main
git pull origin main
git checkout -b feature/my-awesome-feature
```

Releases are cut from `main` by tagging `vX.Y.Z` (see `docs/MACOS_APP.md`).

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
| `macos` | Native SwiftUI app |
| `chat` | Chat + session memory |
| `devops` | DevOps Agent module |
| `codegen` | Code Gen module |
| `scraper` | Web Scraper module |
| `vision` | Vision Lab module |
| `storage` | Cloud Storage module |
| `mcp` | MCP server + marketplace |
| `docs` | Documentation |
| `deps` | Dependencies |

### Examples

```
feat(scraper): add proxy rotation support
fix(backend): handle missing API key gracefully
feat(macos): add AWS section to the Settings window
docs(readme): update quick start instructions
chore(deps): upgrade fastapi to 0.115.0
```

<br />

## 🔀 Pull Request Process

1. **Update your branch** with the latest `main`:
   ```bash
   git fetch origin
   git rebase origin/main
   ```

2. **Ensure all checks pass**:
   - Backend tests pass (`make test`)
   - The macOS app builds (`cd macos && swift build`)
   - Backend starts without errors

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
- Keep new AI features provider-agnostic: go through `app/services/ai_service.py` (`generate_text`, `generate_structured`, `analyze_image_bytes`) rather than calling a provider directly

```python
# ✅ Good
async def scrape(request: ScrapeRequest) -> ScrapeResponse:
    """Scrape a URL and return extracted content."""
    ...

# ❌ Bad
def scrape(data):
    ...
```

### Swift (macOS App)

- SwiftUI views live in `macos/Sources/OmniDevMac/Views/`, services in `Services/`, shared helpers in `Support/`
- Use the shared chrome in `ModuleKit.swift` (`ModuleCard`, `ErrorBanner`, `MonoResult`, `ModuleRun`) so module pages stay consistent
- Page identity belongs in the toolbar: `navigationTitle` + `navigationSubtitle`, not in-body headers
- Talk to the backend through `BackendClient` / `BackendModules` (URLSession) — never spawn processes from views
- Secrets go in the Keychain (`KeychainStore`), never in UserDefaults

<br />

## 🐛 Reporting Issues

When reporting a bug, please include:

1. **Description**: Clear summary of the issue
2. **Steps to Reproduce**: Numbered steps to trigger the bug
3. **Expected Behavior**: What should happen
4. **Actual Behavior**: What actually happens
5. **Environment**: macOS version, Python version, Ollama version, app version
6. **Screenshots/Logs**: If applicable (launcher logs: `.omnidev-macos/launcher.log`)

Use the GitHub Issues tab with the appropriate label (`bug`, `enhancement`, `question`).

<br />

---

<p align="center">
  Thank you for contributing to OmniDev! 🚀
</p>
