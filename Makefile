# Makefile — KADIMA development & Docker shortcuts

.PHONY: build up down restart logs shell init migrate clean \
        test lint typecheck format ci install install-ml install-gpu

# ── Development ──────────────────────────────────────────────────────────────

install:                        ## Install core + dev deps
	pip install -e ".[dev]"

install-ml:                     ## Install with ML modules (CPU)
	pip install -e ".[ml,dev]"

install-gpu:                    ## Install with ML modules (GPU)
	pip install -e ".[gpu,ml,dev]"

test:                           ## Run all tests
	pytest tests/ -v --tb=short

test-engine:                    ## Run engine tests only
	pytest tests/engine/ -v

test-integration:               ## Run integration tests only
	pytest tests/integration/ -v

test-cov:                       ## Run tests with coverage report
	pytest tests/ -v --cov=kadima --cov-report=term-missing --cov-report=html

lint:                           ## Run ruff linter
	ruff check kadima/ tests/

format:                         ## Format code with ruff
	ruff format kadima/ tests/
	ruff check --fix kadima/ tests/

typecheck:                      ## Run mypy type checker
	mypy kadima/ --ignore-missing-imports

ci: lint typecheck test         ## Full CI pipeline (lint + typecheck + test)

# ── Docker ───────────────────────────────────────────────────────────────────

build:                          ## Build API image
	docker compose build

up:                             ## Start API + Label Studio
	docker compose up -d

up-gpu:                         ## Start API with GPU + Label Studio
	docker compose --profile gpu up -d

up-llm:                         ## Start all (including llama.cpp)
	docker compose --profile llm up -d

down:                           ## Stop all services
	docker compose down

restart:                        ## Restart API
	docker compose restart api

logs:                           ## Tail API logs
	docker compose logs -f api

logs-all:                       ## Tail all services
	docker compose logs -f

# ── DB ───────────────────────────────────────────────────────────────────────

init:                           ## Initialize DB (run migrations)
	docker compose exec api kadima --init

migrate:                        ## Apply pending migrations
	docker compose exec api kadima migrate

migrate-status:                 ## Show current schema version
	docker compose exec api kadima migrate --status

# ── Debug ────────────────────────────────────────────────────────────────────

shell:                          ## Shell into API container
	docker compose exec api bash

psql:                           ## Open sqlite3 in container
	docker compose exec api sqlite3 /data/kadima.db

health:                         ## Check API health
	curl -s http://localhost:8501/health | python3 -m json.tool

# ── Config ───────────────────────────────────────────────────────────────────

schema:                         ## Regenerate JSON Schema from Pydantic models
	python -c "from kadima.pipeline.config import save_json_schema; save_json_schema()"

# ── Cleanup ──────────────────────────────────────────────────────────────────

clean:                          ## Remove containers + volumes (DESTRUCTIVE)
	docker compose down -v

clean-all:                      ## Remove everything including images
	docker compose down -v --rmi all

clean-py:                       ## Remove Python caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true

help:                           ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
