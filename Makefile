# Makefile — KADIMA Docker shortcuts

.PHONY: build up down restart logs shell init migrate clean

# ── Core ─────────────────────────────────────────────────────────────────────

build:                          ## Build API image
	docker compose build

up:                             ## Start API + Label Studio
	docker compose up -d

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

# ── Cleanup ──────────────────────────────────────────────────────────────────

clean:                          ## Remove containers + volumes (DESTRUCTIVE)
	docker compose down -v

clean-all:                      ## Remove everything including images
	docker compose down -v --rmi all
