# OmniDev — one-command developer workflow.
# Run `make help` for the full list.

BACKEND := backend
FRONTEND := frontend
VENV := $(BACKEND)/.venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

.DEFAULT_GOAL := help

.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

.PHONY: setup
setup: setup-backend setup-frontend ## Full first-run setup (backend venv + frontend deps + .env)

.PHONY: setup-backend
setup-backend: ## Create the backend venv, install deps + Playwright, seed .env
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r $(BACKEND)/requirements.txt
	$(PY) -m playwright install chromium
	@test -f $(BACKEND)/.env || cp $(BACKEND)/.env.example $(BACKEND)/.env

.PHONY: setup-frontend
setup-frontend: ## Install frontend deps and seed .env.local
	cd $(FRONTEND) && npm ci
	@test -f $(FRONTEND)/.env.local || echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > $(FRONTEND)/.env.local

.PHONY: backend
backend: ## Run the FastAPI backend (http://localhost:8000)
	cd $(BACKEND) && .venv/bin/uvicorn app.main:app --reload

.PHONY: frontend
frontend: ## Run the Next.js cockpit (http://localhost:3000)
	cd $(FRONTEND) && npm run dev

.PHONY: models
models: ## Pull the default local model for fully-offline use
	ollama pull gemma4:e4b

.PHONY: test
test: test-backend test-frontend ## Run all checks

.PHONY: test-backend
test-backend: ## Run backend tests
	cd $(BACKEND) && .venv/bin/pytest -q

.PHONY: test-frontend
test-frontend: ## Typecheck the frontend
	cd $(FRONTEND) && npm run lint

.PHONY: build-frontend
build-frontend: ## Production build of the frontend
	cd $(FRONTEND) && npm run build

.PHONY: mac
mac: ## Build and run the native macOS app
	cd macos && swift run OmniDev

.PHONY: clean
clean: ## Remove build artifacts and virtualenvs
	rm -rf $(VENV) $(FRONTEND)/.next $(FRONTEND)/node_modules macos/.build
