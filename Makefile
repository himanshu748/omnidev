# OmniDev — one-command developer workflow.
# Run `make help` for the full list.

BACKEND := backend
VENV := $(BACKEND)/.venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
REQUIREMENTS := $(BACKEND)/requirements.lock

.DEFAULT_GOAL := help

.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

.PHONY: setup
setup: ## Full first-run setup (backend venv + deps + .env)
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install --require-hashes -r $(REQUIREMENTS)
	$(PY) -m playwright install chromium
	@test -f $(BACKEND)/.env || cp $(BACKEND)/.env.example $(BACKEND)/.env

.PHONY: backend
backend: ## Run the FastAPI backend (http://localhost:8000)
	cd $(BACKEND) && .venv/bin/uvicorn app.main:app --reload

.PHONY: models
models: ## Pull the default local model for fully-offline use
	ollama pull gemma4:12b

.PHONY: mcp
mcp: ## Run the MCP server on stdio (register with: claude mcp add omnidev)
	cd $(BACKEND) && .venv/bin/python -m app.mcp

.PHONY: claude-local
claude-local: ## Run Claude Code on the local Gemma model (no cloud, no API key)
	ANTHROPIC_BASE_URL=http://localhost:11434 ANTHROPIC_AUTH_TOKEN=ollama claude --model gemma4:12b

.PHONY: test
test: ## Run backend tests
	cd $(BACKEND) && .venv/bin/pytest -q

.PHONY: mac
mac: ## Build and run the native macOS app
	cd macos && swift run OmniDev

.PHONY: clean
clean: ## Remove build artifacts and virtualenvs
	rm -rf $(VENV) macos/.build
