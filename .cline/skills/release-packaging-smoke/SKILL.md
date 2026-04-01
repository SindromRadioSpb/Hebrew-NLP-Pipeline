---
name: release-packaging-smoke
description: Use this skill when adding new Kadima modules, migrations, assets, or changing import paths. Ensures Docker image build includes new files, keeps packaging deterministic, and provides a release smoke checklist for API start, health check, and core features.
---

# Release Packaging + Smoke

## When to use
- Adding new engine modules (`kadima/engine/*.py`)
- Adding new migrations (`kadima/data/migrations/`)
- Adding new API routers or schemas
- Changing `pyproject.toml` dependencies
- Before any production Docker build

## Kadima packaging: Docker (primary)

### 1. Verify Dockerfile COPY patterns include new files
```dockerfile
# Check Dockerfile for COPY patterns
# New files must be in a directory already covered by COPY . .
# or explicitly added
COPY kadima/ /app/kadima/
COPY kadima/data/migrations/ /app/kadima/data/migrations/
```

### 2. Verify pyproject.toml optional groups
New ML dependencies → add to correct group:
```toml
[project.optional-dependencies]
ml = ["new-package>=1.0,<2"]   # CPU inference
gpu = ["new-package[cuda]"]     # GPU-accelerated
```

### 3. Build smoke
```bash
# Build image
docker build -t kadima:smoke .

# Start API
docker compose up -d

# Health check
curl http://localhost:8501/health
# Expected: {"status": "ok"}

# Self-check (CI gate)
docker compose exec api kadima --self-check import
docker compose exec api kadima --self-check db_open
docker compose exec api kadima --self-check health
docker compose exec api kadima --self-check migrations
```

### 4. Core features smoke
```bash
# New engine module
curl -X POST http://localhost:8501/api/v1/generative/<endpoint> \
  -H "Content-Type: application/json" \
  -d '{"text": "שלום עולם"}'
# Expected: 200, valid response body

# Pipeline
curl -X POST http://localhost:8501/api/v1/pipeline/run-text \
  -H "Content-Type: application/json" \
  -d '{"text": "ירושלים היא עיר הבירה של ישראל."}'
# Expected: 200, terms array
```

### 5. Release checklist

```
□ docker build exits 0
□ /health returns {"status": "ok"}
□ --self-check import passes (all core imports)
□ --self-check db_open passes (migrations applied)
□ --self-check migrations passes (current version)
□ New endpoint returns 200 with valid schema
□ Existing tests pass: pytest tests/ -v
□ No hardcoded secrets in committed files
□ .env.example updated if new env vars added
□ CLAUDE.md updated (new module, new endpoint, new migration)
□ pyproject.toml updated (new deps in correct optional group)
```

## Local (non-Docker) smoke
```bash
pip install -e ".[dev]"
kadima --self-check import
kadima --self-check health
pytest tests/ -v
kadima api --host 127.0.0.1 --port 8501 &
curl http://127.0.0.1:8501/health
```
