# KADIMA — Hebrew NLP Platform

Term extraction, validation, and knowledge base for Hebrew corpus linguistics.

**Status:** v0.9.0 — pre-release, API skeleton + engine modules in development

---

## Quick Start

```bash
# Install
pip install -e .

# Initialize
kadima --init

# Run pipeline on text
kadima run --text "פלדה חזקה משמשת בבניין"

# Start API server
kadima api

# Start with Docker
make build && make up
# API → http://localhost:8501/docs
# Label Studio → http://localhost:8080
```

## Architecture

```
CLI / API / GUI
    ↓
Pipeline Orchestrator (pipeline/)
    ↓
Engine Layer (engine/)        ← M1–M8, M12 NLP modules
    ↓
Data Layer (data/)            ← SQLite + migrations
    ↑
Annotation (annotation/)     ← Label Studio sync
LLM (llm/)                   ← Dicta-LM integration
KB (kb/)                     ← Knowledge Base
```

## Modules

| Module | Description | Status |
|--------|-------------|--------|
| `engine/` | NLP processors (tokenization, morphology, ngrams, terms) | 🔨 In progress |
| `pipeline/` | Orchestrator: M1→M2→...→M8 | 🔨 In progress |
| `validation/` | Gold corpus validation framework (M11) | ✅ Structured |
| `corpus/` | Import/export/statistics (M14) | ✅ Structured |
| `annotation/` | Label Studio integration (M15) | ✅ Client + sync + ML backend |
| `kb/` | Knowledge Base (M19) | ✅ Structured |
| `llm/` | Dicta-LM service (M18) | ✅ Client + prompts |
| `api/` | FastAPI REST API (M17) | ✅ Routers + schemas |
| `data/` | SQLite migrations + repositories | ✅ 4 migrations |
| `ui/` | PyQt desktop UI | 📋 Stubbed |

## Development

```powershell
# Setup (Windows / primary workflow)
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[all]"

# Test
python -m pytest tests\ -v

# Lint
python -m ruff check kadima\

# Database migrations
python -m kadima migrate --new my_change    # Create migration
python -m kadima migrate                    # Apply pending
python -m kadima migrate --status           # Show version
```

Only `.venv` is supported as the working virtual environment for this repository. Legacy directories such as `.venv-311` should not be used and may be removed.

## Docker

```bash
make build              # Build API image
make up                 # API + Label Studio
make up-llm             # + llama.cpp (GPU)
make shell              # Shell into container
make logs               # Tail API logs
```

| Service | Port | Description |
|---------|------|-------------|
| `api` | 8501 | KADIMA REST API |
| `label-studio` | 8080 | Annotation UI |
| `ml-backend` | 9090 | Pre-annotation service |
| `llm` | 8081 | llama.cpp (optional, `--profile llm`) |

## Project Structure

See [CLAUDE.md](CLAUDE.md) for the full project map (where to put code).

## Documentation

Full technical documentation in `doc/Техническое задание разработка KADIMA/`:

- `01_Концепт/` — Vision, Scope
- `02_Продукт/` — PRD, Functional Spec
- `04_Система/` — Architecture, API Spec, Data Model
- `07_Качество/` — Test Strategy
- `10_Разработка/` — Project Structure, Coding Standards

## License

MIT
