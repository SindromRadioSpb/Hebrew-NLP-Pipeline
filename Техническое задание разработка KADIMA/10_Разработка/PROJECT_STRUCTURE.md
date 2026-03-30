# 10.1. Project Structure — KADIMA

> Версия: 1.0 (2026-03-30)
> Связанные: ARCHITECTURE.md, DATA_MODEL.md, API_SPEC.md, INTERFACE_CONTRACTS.md

---

## Root Layout

```
hebrew-nlp-pipeline/
│
├── pyproject.toml                    # Проект, зависимости, build
├── README.md                         # Описание, быстрый старт
├── LICENSE                           # Apache 2.0
├── CHANGELOG.md                      # История версий
├── .gitignore
├── .python-version                   # 3.12
│
├── docker-compose.kadima-ls.yml      # Label Studio + ML backend + (LLM v1.x)
├── Dockerfile.ml-backend             # KADIMA ML backend для Label Studio
│
├── config/
│   ├── config.default.yaml           # Дефолтная конфигурация pipeline
│   └── config.schema.json            # JSON Schema для валидации config.yaml
│
├── kadima/                           # Основной Python-пакет
│   ├── __init__.py                   # __version__, __all__
│   ├── cli.py                        # CLI entrypoint (kadima run, kadima gui, kadima --init)
│   ├── app.py                        # PyQt application bootstrap
│   │
│   ├── engine/                       # Engine Layer (M1–M8, M12)
│   │   ├── __init__.py
│   │   ├── base.py                   # Processor ABC, PipelineResult dataclass
│   │   ├── hebpipe_wrappers.py       # M1 SentSplit, M2 Tokenizer, M3 MorphAnalyzer
│   │   ├── ngram_extractor.py        # M4
│   │   ├── np_chunker.py             # M5
│   │   ├── canonicalizer.py          # M6
│   │   ├── association_measures.py   # M7
│   │   ├── term_extractor.py         # M8
│   │   └── noise_classifier.py       # M12
│   │
│   ├── pipeline/                     # Pipeline orchestrator
│   │   ├── __init__.py
│   │   ├── orchestrator.py           # PipelineService: M1→M2→...→M8
│   │   └── config.py                 # PipelineConfig dataclass + YAML loader
│   │
│   ├── validation/                   # M11: Validation Framework
│   │   ├── __init__.py
│   │   ├── gold_importer.py          # Импорт gold corpus (manifest + expected CSV)
│   │   ├── check_engine.py           # ExpectedCheck → actual → comparison
│   │   └── report.py                 # PASS/WARN/FAIL report generation
│   │
│   ├── corpus/                       # M14: Corpus Manager
│   │   ├── __init__.py
│   │   ├── importer.py               # Import TXT, CSV, CoNLL-U, JSON
│   │   ├── exporter.py               # Export CSV, JSON, TBX, TMX, CoNLL-U
│   │   └── statistics.py             # Token/lemma/freq statistics
│   │
│   ├── annotation/                   # M15: Label Studio integration
│   │   ├── __init__.py
│   │   ├── ls_client.py              # Label Studio REST API client
│   │   ├── project_manager.py        # CRUD annotation projects
│   │   ├── preannotator.py           # KADIMA pipeline → LS predictions
│   │   └── exporter.py               # LS annotations → gold/training/KB
│   │
│   ├── kb/                           # M19: Knowledge Base (v1.x)
│   │   ├── __init__.py
│   │   ├── models.py                 # KBTerm, KBRelation, KBDefinition dataclasses
│   │   ├── repository.py             # SQLite CRUD для KB
│   │   ├── search.py                 # Full-text + embedding similarity search
│   │   └── generator.py              # Dicta-LM definition generation
│   │
│   ├── llm/                          # M18: LLM Service (v1.x)
│   │   ├── __init__.py
│   │   ├── client.py                 # llama.cpp HTTP client
│   │   ├── prompts.py                # Prompt templates (Hebrew)
│   │   └── service.py                # Define, explain, QA, exercises
│   │
│   ├── nlp/                          # spaCy pipeline setup
│   │   ├── __init__.py
│   │   ├── pipeline.py               # spaCy pipeline builder (config.cfg → nlp)
│   │   └── components/               # Custom spaCy components
│   │       ├── __init__.py
│   │       ├── hebpipe_sent_splitter.py
│   │       ├── hebpipe_morph_analyzer.py
│   │       ├── ngram_component.py
│   │       ├── np_chunk_component.py
│   │       └── noise_component.py
│   │
│   ├── data/                         # Data Layer
│   │   ├── __init__.py
│   │   ├── db.py                     # SQLite connection + migrations
│   │   ├── models.py                 # SQLAlchemy/dataclass models (15 tables)
│   │   ├── repositories.py           # CorpusRepo, RunRepo, GoldRepo, etc.
│   │   └── migrations/
│   │       ├── 001_initial.sql
│   │       ├── 002_annotation.sql
│   │       ├── 003_kb.sql
│   │       └── 004_llm.sql
│   │
│   ├── api/                          # M17: REST API (FastAPI)
│   │   ├── __init__.py
│   │   ├── app.py                    # FastAPI app factory
│   │   ├── routers/
│   │   │   ├── corpora.py
│   │   │   ├── pipeline.py
│   │   │   ├── validation.py
│   │   │   ├── annotation.py
│   │   │   ├── kb.py
│   │   │   └── llm.py
│   │   └── schemas.py                # Pydantic request/response models
│   │
│   ├── ui/                           # PyQt UI
│   │   ├── __init__.py
│   │   ├── main_window.py            # MainWindow
│   │   ├── dashboard.py              # Dashboard tab
│   │   ├── pipeline_view.py          # Pipeline config + results
│   │   ├── validation_view.py        # Validation report
│   │   ├── annotation_view.py        # LS integration panel
│   │   ├── kb_view.py                # KB browse/search (v1.x)
│   │   ├── llm_view.py               # LLM chat (v1.x)
│   │   └── widgets/                  # Reusable widgets
│   │       ├── __init__.py
│   │       ├── term_table.py
│   │       ├── progress_bar.py
│   │       └── error_dialog.py
│   │
│   └── utils/                        # Утилиты
│       ├── __init__.py
│       ├── logging.py                # Logging setup
│       ├── config_loader.py          # YAML config → dataclass
│       └── hebrew.py                 # Hebrew-specific helpers (RTL, maqaf, etc.)
│
├── ml_backends/                      # Label Studio ML backend (отдельный Docker)
│   ├── Dockerfile
│   ├── requirements.txt
│   └── kadima_ner_backend.py         # KADIMA NER pre-annotation backend
│
├── templates/                        # Label Studio templates
│   ├── hebrew_ner.xml
│   ├── hebrew_term_review.xml
│   └── hebrew_pos.xml
│
├── models/                           # Модели (gitignored, download scripts)
│   ├── download_neodictabert.py
│   └── download_dictalm.py
│
├── tests/                            # Тесты
│   ├── __init__.py
│   ├── conftest.py                   # Fixtures (gold corpora, DB, mock LLM)
│   ├── engine/
│   │   ├── test_hebpipe_wrappers.py
│   │   ├── test_ngram_extractor.py
│   │   ├── test_np_chunker.py
│   │   ├── test_canonicalizer.py
│   │   ├── test_association_measures.py
│   │   ├── test_term_extractor.py
│   │   └── test_noise_classifier.py
│   ├── validation/
│   │   ├── test_gold_importer.py
│   │   ├── test_check_engine.py
│   │   └── test_report.py
│   ├── corpus/
│   │   ├── test_importer.py
│   │   └── test_exporter.py
│   ├── annotation/
│   │   ├── test_ls_client.py
│   │   └── test_preannotator.py
│   ├── kb/                           # v1.x
│   │   ├── test_repository.py
│   │   ├── test_search.py
│   │   └── test_generator.py
│   ├── llm/                          # v1.x
│   │   ├── test_client.py
│   │   └── test_service.py
│   ├── integration/
│   │   ├── test_pipeline_e2e.py      # M1→M8 on gold corpora
│   │   ├── test_validation_e2e.py    # gold → pipeline → report
│   │   └── test_annotation_e2e.py    # LS round-trip
│   └── data/                         # Test data (26 gold corpora)
│       ├── he_01_sentence_token_lemma_basics/
│       ├── he_02_noise_and_borderline/
│       ├── ...                       # he_03 through he_26
│       └── he_26_homographs/
│
├── scripts/                          # Utility scripts
│   ├── setup_dev.sh                  # Dev environment setup
│   ├── download_models.sh            # Download all models
│   └── run_label_studio.sh           # Start LS Docker
│
└── docs/                             # Документация (эти файлы)
    └── Техническое задание разработка KADIMA/
        └── ... (все 26+ документов)
```

---

## Naming Conventions

| Элемент | Формат | Пример |
|---------|--------|--------|
| Python файлы | `snake_case.py` | `term_extractor.py` |
| Классы | `PascalCase` | `TermExtractor`, `PipelineService` |
| Функции/методы | `snake_case` | `run_pipeline()`, `get_terms()` |
| Константы | `UPPER_SNAKE` | `DEFAULT_MIN_FREQ`, `SUPPORTED_FORMATS` |
| Dataclass поля | `snake_case` | `surface: str`, `pmi: float` |
| SQL таблицы | `snake_case` | `pipeline_runs`, `kb_terms` |
| SQL колонки | `snake_case` | `created_at`, `doc_freq` |
| Модули engine/ | по номеру модуля | `ngram_extractor.py` (M4) |
| Тесты | `test_<module>.py` | `test_term_extractor.py` |
| Label Studio templates | `hebrew_<type>.xml` | `hebrew_ner.xml` |

---

## Import Order (PEP 8)

```python
# 1. Standard library
import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

# 2. Third-party
import spacy
from pydantic import BaseModel
from label_studio_sdk.client import LabelStudio

# 3. Local
from kadima.engine.base import Processor, PipelineResult
from kadima.data.models import Corpus, Term
from kadima.pipeline.config import PipelineConfig
```

---

## Entrypoints

| Команда | Модуль | Описание |
|---------|--------|----------|
| `kadima gui` | `kadima/app.py` | Запуск PyQt UI |
| `kadima run` | `kadima/cli.py` | CLI pipeline run |
| `kadima --init` | `kadima/cli.py` | Инициализация config + DB |
| `kadima --version` | `kadima/__init__.py` | Версия |
| `kadima api` | `kadima/api/app.py` | Запуск FastAPI сервера |
| `uvicorn kadima.api.app:app` | — | Альтернативный запуск API |
| `python -m kadima.cli ...` | — | Без pip install |
