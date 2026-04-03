# Current Status — KADIMA
# Обновляй этот файл после каждого значимого изменения!
# Последнее обновление:

---

## Версия: 0.9.x → цель 1.0.0 (обновлено 2026-04-02)

---

## Что работает (доказано кодом)

| Компонент | Статус | Доказательство |
|-----------|--------|----------------|
| NLP pipeline M1-M8, M12 | Working | engine/*.py + tests/engine/ (236 PASS) |
| Noise filter UI controls | Working | pipeline_view.py: _noise_filter, _pos_filter → _get_config_dict |
| Premium Progress UX (infra) | Ready (not connected) | widgets/operation_progress.py, tests/ui/test_progress.py (24 PASS) |
| Pipeline `run_on_text()` | Working | orchestrator.py |
| Pipeline `run(corpus_id)` | Working | orchestrator.py + E2E tests |
| Generative M13-M24 (12 модулей) | Working | engine/*.py + tests/engine/ |
| REST API (29 endpoints, 6 роутеров) | Working | api/routers/ + tests/api/ |
| Desktop UI (10 views + 9+ widgets) | Working | ui/*.py + tests/ui/ |
| SQLite WAL + 4 migrations | Working | data/ |
| SQLAlchemy ORM (18 models) | Working | data/sa_models.py |
| Validation (26 gold corpus sets) | Working | validation/ + tests/ |
| Annotation client + LS sync | Working | annotation/ |
| KB (search + embedding similarity) | Working | kb/ |
| LLM service (LlamaCppClient) | Working (graceful fallback) | llm/ |
| NER training pipeline (LS→spaCy) | Working | annotation/ner_training.py |
| Term clusterer (k-means/HDBSCAN) | Working (offline tool, not in pipeline) | engine/term_clusterer.py |
| KadimaTransformer (NeoDictaBERT backbone) | Working | nlp/components/ |
| Self-check CLI | Working | `kadima --self-check import/db_open/health/migrations` |
| Docker Compose (basic) | Working | docker-compose.yml |
| CI (GitHub Actions) | Working | .github/workflows/ |

---

## Открытые технические долги

| ID | Проблема | Файл | Приоритет |
|----|---------|------|-----------|
| D6 | `Token` dataclass объявлен в двух местах с разными полями | `data/models.py` + `engine/hebpipe_wrappers.py` | Low (нет конфликта) |
| D11 | `test_term_clusterer.py::TestSilhouette::test_two_clusters` — silhouette score == 0.0 на синтетических данных | `tests/engine/test_term_clusterer.py` | Low (pre-existing) |
| — | M25 Paraphraser не реализован | `engine/` (файл отсутствует) | Medium |
| — | mBART-50 + MMS-TTS-heb = CC-BY-NC → запрещено коммерческое использование | `translator.py`, `tts_synthesizer.py` | **CRITICAL** |
| — | PyQt6 = GPL v3 → нужна коммерческая лицензия Qt для closed-source | `pyproject.toml` | **CRITICAL** |
| — | YAKE = возможно GPL v3 → проверить немедленно | `keyphrase_extractor.py` | HIGH |
| — | Docker prod-compose (docker-compose.prod.yml) не создан | — | Medium |
| — | `model_manager.py` не существует, загрузка inline per-module | `engine/` | Won't fix (задокументировано) |

---

## Следующий шаг (Next)

**R-6.1 — Docker Compose production-ready**
- `docker-compose.prod.yml` с resource limits, GPU reservation, non-root user
- Healthchecks для всех сервисов
- `.env.example` актуализировать

После этого: **Фаза F** (инфраструктурный фундамент):
1. `kadima/infra/db.py` — WAL PRAGMAs полный набор + Write Gate (RLock)
2. `kadima/infra/settings.py` — QSettings INI singleton (geometry, last view)
3. `kadima/data/migrations/005_fts5.sql` — sentence_fts, term_fts FTS5 tables
4. `kadima/domain/` — DTO layer, hebrew_utils, kwic

---

## Закрытые фазы

| Фаза | Что закрыто |
|------|------------|
| Phase 0 | Стабилизация: B1-B4, CI, Docker |
| Phase 1 | M22 Transliterator, M21 MorphGen, M13 Diacritizer, M17 NER, M14 Translator |
| T1 | KadimaTransformer, NeoDictaBERT backbone, spaCy pipeline builder |
| T2 | M5 embeddings mode, M17 NER neodictabert, NER training pipeline, KB embeddings, TermClusterer, SA ORM, async SA, model download script |
| T3 | Desktop UI: MainWindow + 6 views + 9 widgets + dark QSS |
| pre-T4 | D8 cross-view wiring, D9 engine stubs M15/M16/M18/M20, D10 T4 widgets |
| P0 | DoD checklist, Cold-Audit Framework, self-check CLI, CI gate |
| T4 | M15 TTS (XTTS→MMS), M16 STT (Whisper→faster-whisper), M18 Sentiment, M20 QA + active learning; GenerativeView + AnnotationView |
| T5 ML | M24 Keyphrase (YAKE+TF-IDF), M23 Grammar (Dicta-LM+rules), M19 Summarizer (LLM+mT5+extractive) |
| T5 UI | NLPToolsView, LLMView, ChatWidget, 60 smoke tests |
| T6 D4 | API vertical slices: validation (5ep), kb (5ep), annotation (4ep), llm (5ep) = 19 endpoints, 80 tests |
| — | Generative router расширен до 12 endpoints (M15/M16/M18/M20 добавлены) |
| — | audit_v1.md создан (1106+ строк, все 15 противоречий устранены) |
| — | M8 Term Extractor: POS-aware filtering (+21% precision), 111 tests |
| — | M8 Term Extractor: 4 режима term_mode (distinct/canonical/clustered/related), UI selector, help panel, 14 колонок, 40 тестов engine API 9/9, 172 строк) |
| — | T7-3: AlephBERT Fine-Tuning infrastructure — M8Backend (ABC) + StatisticalBackend + AlephBERTBackend, training CLI (export/train/eval), PipelineView Extraction Method selector, ResultsView backend badge |
| — | .cline/skills/ создан (13 skills) |
| — | §§5.1-5.4 M1-M4 актуализированы: статусы, строки кода, тесты, баг min_n/max_n исправлен |
| — | M5 NP Chunker: POS-aware filtering, _is_valid_np_head()/_is_valid_np_mod(), noise 43%→5%, 26/26 PASS |
| — | UI: TermsTableModel sort fix (int/float cast), NgramTable/NPChunkTable уже numeric |
| — | M8: noise_filter_enabled + pos_filter_enabled добавлены в UI (pipeline_view.py Thresholds) |
| — | OperationProgressDialog создан (widgets/operation_progress.py, 330+ строк, 24 теста) |
| — | _WorkerSignals расширены: activity, counters, stage_info сигналы |
| — | audit_v1.md обновлён: добавлены разделы 13-14 (повторный аудит M1-M8) |

---

## Test Count (последний запуск: 2026-04-02)
**823/824 PASSED** (1 pre-existing failure в M15 TTS — `test_process_mms_unavailable_returns_failed`)

M1-M8 engine tests: 236/236 PASS
Integration E2E: 16/16 PASS
API tests: 114/114 PASS
Premium Progress UX: 24/24 PASS
Noise filtering: 6/6 PASS

Основные test файлы:
- `tests/engine/test_*.py` — по одному на каждый engine модуль
- `tests/api/test_*_router.py` — 80 API тестов
- `tests/ui/test_*.py` — 62+ UI smoke tests
- `tests/integration/test_pipeline_e2e.py` — 28 E2E
- `tests/kb/`, `tests/data/`, `tests/validation/` — отдельные пакеты

Запуск регрессии: `pytest tests/ -v`
