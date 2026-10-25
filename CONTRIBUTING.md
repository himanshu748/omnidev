# Contributing to OmniDev

Thanks for helping build OmniDev, the local-first AI cockpit for macOS. Bug reports, docs fixes, tests, and features are all welcome, and you don't need to be a Swift or AI expert to help.

## Table of contents

- [Ground rules](#ground-rules)
- [Ways to contribute](#ways-to-contribute)
- [Finding something to work on](#finding-something-to-work-on)
- [Development setup](#development-setup)
- [Project map](#project-map)
- [Making a change](#making-a-change)
- [Safety invariants](#safety-invariants)
- [Testing](#testing)
- [Code style](#code-style)
- [Commit conventions](#commit-conventions)
- [Pull request process](#pull-request-process)
- [Dependencies](#dependencies)
- [Releases](#releases)
- [Reporting bugs and requesting features](#reporting-bugs-and-requesting-features)
- [Security issues](#security-issues)
- [License](#license)

## Ground rules

- Follow the [Code of Conduct](CODE_OF_CONDUCT.md). Be kind, assume good intent, and keep feedback about the code.
- **Local-first is the product.** Every feature must work offline through Ollama. Nothing may leave the machine without an explicit opt-in such as Gemini, AWS, or a URL the user asked to scrape.
- **Keep public copy honest.** No fake testimonials, unsupported benchmarks or pricing, or claims of guaranteed bot-protection bypass.
- **Small, focused PRs get merged faster.** Before writing a large feature, open an issue or comment on an existing one so we can agree on the approach.

## Ways to contribute

| You have... | Good places to start |
|---|---|
| 15 minutes | Fix a typo or stale command in the docs, or reproduce an open bug and add details |
| An afternoon | Pick up a [`good first issue`](https://github.com/himanshu748/omnidev/labels/good%20first%20issue), add a missing test, or improve an error message |
| Python skills | Backend routers, services, MCP tools, knowledge indexing, test coverage |
| Swift skills | SwiftUI views, accessibility, onboarding, menu-bar extra, XCTest coverage |
| DevOps skills | CI, release signing, Dependabot, devcontainer |
| A Mac and some time | Test release candidates on different chips and macOS versions, then report what breaks |

## Finding something to work on

1. Browse [open issues](https://github.com/himanshu748/omnidev/issues). Labels help you filter:
   - `good first issue`: small and well scoped, with pointers to the relevant files
   - `help wanted`: larger items where maintainers would welcome a contributor
   - `area: backend`, `area: macos`, `area: mcp`, `area: ci`, `area: docs`, `area: security`: which part of the codebase is involved
2. Comment on the issue to say you're working on it, so nobody duplicates the effort. If you go quiet for two weeks, a maintainer may reassign it.
3. Read [ROADMAP.md](ROADMAP.md) to see where the project is heading.

## Development setup

### Prerequisites

- **Python 3.11+.** CI runs 3.13.
- **macOS 13+ with Xcode command-line tools** for the native app (CI builds on macOS 14). The backend alone runs on any OS.
- **[Ollama](https://ollama.com)** for local AI, or a `GEMINI_API_KEY`. The test suite needs neither.
- Git and `make`.

### Fork, clone, and install

```bash
# Fork on GitHub first, then:
git clone https://github.com/<your-username>/omnidev.git
cd omnidev
git remote add upstream https://github.com/himanshu748/omnidev.git

make setup        # backend/.venv, hashed deps from requirements.lock, Playwright Chromium, backend/.env
make models       # optional: pull the default local model (gemma4:12b, ~7.6 GB)
```

`make setup` installs from `backend/requirements.lock` with `--require-hashes`, the same way CI does. Please don't install from `requirements.txt` directly, because that file only lists the inputs to the lock.

On machines with less memory, set `OLLAMA_MODEL=gemma4:e2b` and `OLLAMA_VISION_MODEL=gemma4:e2b` in `backend/.env`.

### Run

```bash
make backend      # FastAPI on http://localhost:8000; interactive API docs at /docs
make mac          # native macOS app; it starts and manages its own backend sidecar
make mcp          # MCP server on stdio
make help         # every target
```

When you run from source, the app's launcher log is written to `.omnidev-macos/launcher.log` in the repository root.

## Project map

```text
backend/app/
  main.py        FastAPI app, lifespan, router registration
  config.py      settings from env and .env (AI provider, models, data dir)
  routers/       HTTP endpoints: thin, validate input, call a service
  services/      business logic (ai_service.py is the only provider entry point)
  schemas/       Pydantic request and response models
  mcp/           MCP server exposing OmniDev tools
backend/tests/   pytest suite (no network, Ollama, or AWS needed)
macos/Sources/OmniDevMac/
  App/           entry point, menu-bar extra, Settings
  Services/      BackendClient / BackendModules (URLSession), sidecar lifecycle
  Support/       Keychain, paths, model catalog, settings
  Views/         module views built on ModuleKit.swift
site/            static landing page and Agent Lab (WebMCP adapters are generated and checked in CI)
scripts/         launch, stop, and package scripts, plus WebMCP contract checks
docs/            architecture, API reference, deployment, PRDs
```

Start with [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) and [docs/API.md](docs/API.md).

### Adding a backend feature end to end

1. **Schema:** add request and response models in `backend/app/schemas/<module>.py`.
2. **Service:** put the logic in `backend/app/services/<module>_service.py`. Route AI calls through `ai_service` (`generate_text`, `generate_structured`, `analyze_image_bytes`); never call Ollama or Gemini directly.
3. **Router:** add a thin `async def` handler in `backend/app/routers/<module>.py` and register new routers in `main.py`.
4. **Tests:** cover the happy path and the refusal path in `backend/tests/test_<module>.py`. Add any new endpoint to `EXPECTED_ENDPOINTS` in `tests/conftest.py` so the endpoint coverage report stays accurate.
5. **Docs:** update `docs/API.md`, and keep its examples consistent with the Pydantic schemas.
6. **App and MCP (optional):** expose the endpoint in `BackendModules.swift` and a view, or as a tool in `app/mcp/server.py`.

## Making a change

```bash
git fetch upstream
git checkout -b feature/short-description upstream/main
# ...edit, test, commit...
git push origin feature/short-description
```

| Branch prefix | Use for |
|---|---|
| `feature/` | New features |
| `bugfix/` | Bug fixes |
| `docs/` | Documentation only |
| `chore/` | Tooling, CI, dependencies |

Add an entry under `## [Unreleased]` in [CHANGELOG.md](CHANGELOG.md) for any user-facing change, following [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## Safety invariants

OmniDev runs AI-driven actions on a real machine. PRs that weaken any of the following will not be merged without an explicit design discussion in an issue first:

- **Agent:** no delete tool. Changed files are snapshotted before every write. Replacing existing file contents, or acting outside trusted folders, requires approval. Destructive shell commands stay blocked.
- **Agent sandbox:** `run_command` runs only inside the OS sandbox (`services/command_sandbox.py`) unless the user explicitly turns it off. It never falls back to running unsandboxed. Secrets stay unreadable, `.git` hooks and config stay read-only, and network stays off by default.
- **Knowledge:** sensitive paths and files (credentials, keychains, browser profiles, `.env*`, private keys, password vaults) are never indexed, even under an added parent folder. The index stays at `0600`.
- **Code Gen:** generation only. The backend validates returned files, blocks secret-like output and risky npm scripts, and **never executes** generated code.
- **Scraper:** every URL passes the SSRF guard (`services/url_guard.py`), which refuses loopback, private, link-local, and metadata addresses.
- **DevOps:** the exact boto3 plan is shown before execution, destructive actions need confirmation, and `DEVOPS_READ_ONLY=1` refuses all mutations. MCP AWS tools only preview.
- **Secrets:** stored in the macOS Keychain, never in UserDefaults or logs, and scrubbed from API error responses.

When you touch one of these areas, add or extend a test that proves the guard still refuses the unsafe case.

## Testing

```bash
make test                          # backend suite (same as CI)
cd backend && .venv/bin/pytest tests/test_scraper.py -q -k ssrf   # one focused test
cd macos && swift build            # native app must compile (CI builds -c release)
```

- Tests must not need the network, Ollama, Gemini, or real AWS. Use `moto` for AWS, `tests/fake_mcp_server.py` for MCP, and monkeypatch the `ai_service` calls.
- Tests use a temporary `data_dir` (see `conftest.py`). Never write to `~/.omnidev` from a test.
- macOS-only code such as Vision OCR via `pyobjc` is installed only on `darwin`, and backend CI runs on Ubuntu. Guard those tests with a platform skip.
- For UI changes, include before and after screenshots in the PR.

## Code style

### Python

- PEP 8, type hints on every function signature, and `async def` for endpoint handlers.
- Keep routers thin. Logic belongs in services, and request and response shapes in Pydantic schemas.
- Raise errors through the helpers in `routers/errors.py` (`bad_request`, `not_found`, `service_unavailable`, `internal_error`) rather than returning ad-hoc error dicts, and never echo secrets back.

```python
# Good
async def scrape(request: ScrapeRequest) -> ScrapeResponse:
    """Scrape an authorized URL and return extracted content."""
    ...

# Bad
def scrape(data):
    ...
```

### Swift

- Views live in `Views/`, services in `Services/`, and shared helpers in `Support/`.
- Use the shared chrome in `ModuleKit.swift` (`ModuleCard`, `ErrorBanner`, `MonoResult`, `ModuleRun`) so module pages stay consistent.
- Page identity belongs in the toolbar (`navigationTitle` and `navigationSubtitle`), not in headers inside the view body.
- Talk to the backend through `BackendClient` / `BackendModules`, and never spawn processes from views.
- Secrets go in the Keychain via `KeychainStore`.
- Give icon-only buttons an `accessibilityLabel`.

## Commit conventions

We use [Conventional Commits](https://www.conventionalcommits.org/):

```text
<type>(<scope>): <short imperative summary>
```

**Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`, `ci`, `security`

**Scopes:** `backend`, `macos`, `agent`, `knowledge`, `chat`, `devops`, `codegen`, `scraper`, `vision`, `storage`, `models`, `mcp`, `site`, `docs`, `ci`, `deps`

```text
feat(knowledge): add per-source re-index action
fix(scraper): reject IPv6 link-local targets
docs(contributing): document lockfile regeneration
```

## Pull request process

1. Rebase on the latest `upstream/main`.
2. Run `make test` and `cd macos && swift build` locally.
3. Fill in the PR template: what changed, why, how you tested it, and screenshots for UI changes. Link the issue with `Closes #123`.
4. CI must pass: the WebMCP contract check, backend pytest, and the macOS build.
5. A maintainer reviews, usually within a few days. Push follow-up commits rather than force-pushing during review, so the review history stays readable.
6. PRs are **squash-merged**, so the PR title becomes the commit message and must follow Conventional Commits.

## Dependencies

Python dependencies are pinned with hashes. To add or bump one:

```bash
# 1. Edit backend/requirements.txt (direct dependencies only)
# 2. Regenerate the lock with uv (https://docs.astral.sh/uv/)
cd backend
uv pip compile requirements.txt --python-version 3.11 --universal --generate-hashes -o requirements.lock
# 3. Reinstall and run the tests
cd .. && make setup && make test
```

Explain in the PR why the dependency is needed. Prefer the standard library or an existing dependency where possible.

## Releases

Maintainers cut releases from `main` by bumping the version, moving `[Unreleased]` notes into a dated section of `CHANGELOG.md`, and pushing a `vX.Y.Z` tag. `.github/workflows/release.yml` builds the app, DMG, and checksums. See [docs/MACOS_APP.md](docs/MACOS_APP.md).

## Reporting bugs and requesting features

Use the [issue forms](https://github.com/himanshu748/omnidev/issues/new/choose). For bugs, include the OmniDev version, macOS version and chip, AI provider and model, steps to reproduce, and relevant log lines. Search existing issues first.

## Security issues

**Do not open public issues for vulnerabilities.** Follow [SECURITY.md](SECURITY.md) and use GitHub private vulnerability reporting.

## License

By contributing, you agree that your contributions are licensed under the [MIT License](LICENSE) that covers the project.
