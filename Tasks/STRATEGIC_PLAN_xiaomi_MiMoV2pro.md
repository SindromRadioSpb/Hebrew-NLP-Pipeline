# Стратегический план развития KADIMA → HDLE-level

> Дата: 2026-04-01
> Источники: анализ v_book (HDLE Premium v1.0.1) и Kadima_1.0 (v0.9.1)
> Цель: Перенять лучшие практики v_book, сохранить и масштабировать уникальные преимущества KADIMA

---

## 1. Сравнительный анализ: что у кого есть

### ✅ Что v_book делает лучше (перенять)

| Область | v_book (HDLE) | KADIMA (сейчас) | Приоритет |
|---|---|---|---|
| **Архитектура** | Clean architecture: domain/infra/services/ui | Смешанная: engine + data + pipeline без чёткого разделения | 🔴 P0 |
| **Data Layer** | SQLAlchemy ORM, миграции Alembic, WAL | Прямой sqlite3 + repository pattern | 🔴 P0 |
| **Ingestion** | TXT, DOCX, PDF (text+OCR), PPTX, drag-drop | TXT, CSV, JSON | 🟡 P1 |
| **FTS5 Search** | sentence_fts + term_fts, triggers, self-healing | Нет | 🟡 P1 |
| **Translation Memory** | Global TM + local, offline dict + MT providers | translator module (batch нет) | 🟡 P1 |
| **User Dictionary** | UD items + study progress + SM-2 SRS | KB (basic) | 🟡 P1 |
| **KWIC Concordance** | FTS5 + Hebrew-aware normalization | Нет | 🟡 P1 |
| **Security** | AES-256-GCM, audit log, path validation, FTS5 sanitizer | Базовый | 🟢 P2 |
| **Reliability** | Circuit breaker, rate limiter, process lock | Нет | 🟢 P2 |
| **Pronunciation** | phonikud adapter, audio gen, quality service | M13 Diacritizer (phonikud) | 🟢 P2 |
| **Project Exchange** | .hdleproj bundles (ZIP + SHA256 + ID remap) | Нет | 🟢 P2 |
| **Resource Manager** | Registry, download service, health check | Нет | 🟢 P2 |
| **NLP Engine** | Pluggable (Stanza), subprocess worker | Pluggable (HebPipe/Stanza/Transformers) | — |

### ✅ Что KADIMA делает лучше (сохранить и развить)

| Область | KADIMA | v_book (HDLE) | Статус |
|---|---|---|---|
| **Pipeline Orchestrator** | M1→M8, profiles, configurable | Нет (монолитный process) | ✅ Сохранить |
| **Association Measures** | PMI, LLR, Dice, T-score | PMI, T-score только | ✅ Сохранить |
| **NP Chunker** | M5 отдельный модуль | Встроен в NLP | ✅ Сохранить |
| **Генеративные модули (22!)** | M13–M25: diacritizer, translator, NER, TTS, STT, sentiment, QA, morph_gen, transliterator, keyphrase, grammar, summarizer | Нет генеративных модулей | ✅ Уникальное преимущество |
| **KB Generation** | Модуль kb/generator (auto from terms) | Нет | ✅ Сохранить |
| **LLM Integration** | client/prompts/service (llama.cpp) | Нет | ✅ Уникальное преимущество |
| **Validation Framework** | Gold corpora, check engine, report | Нет | ✅ Сохранить |
| **Label Studio** | Annotation integration (sync, ML backend) | Нет | ✅ Сохранить |
| **CLI** | `kadima gui/run/api/migrate/init` | Только `python -m app.main` | ✅ Сохранить |
| **API** | FastAPI, 7 роутеров (pipeline, generative, kb, llm, annotation) | Нет API | ✅ Сохранить |
| **Config** | Pydantic v2, 22 модуля, 13 generative sub-configs, profiles | YAML settings | ✅ Сохранить |

---

## 2. Стратегия: что и как перенимать

### Принцип 1: Не переписывать — адаптировать
v_book — production-ready desktop app. KADIMA — NLP platform с API. Не надо копировать архитектуру PyQt-приложения. Надо перенять **паттерны** и **практики**.

### Принцип 2: Сохранить pipeline-first
KADIMA — это pipeline-ориентированная платформа. v_book — терминологический лексикон. У KADIMA более широкий scope (22 модуля, генеративные, KB, LLM). Pipeline Orchestrator — это ядро, которое v_book не имеет.

### Принцип 3: Инкрементально, не big bang
Каждый шаг = реализация + тесты + commit. Никаких «переделаю всё за раз».

---

## 3. План по фазам

### Фаза A: Архитектурный фундамент (P0) — 2-3 недели

#### A1. Clean Architecture Refactor
**Что:** Разделить Kadima/ на доменные слои, как в v_book:
```
kadima/
  domain/          # Бизнес-логика (DTO, contracts, scoring, normalization)
    dto.py         # ProcessorResult, PipelineResult, TermDTO, KWICResult и т.д.
    scoring.py     # PMI, T-score, LLR, Dice (перенести из engine/)
    normalization/ # Hebrew normalization (strip nikud, cantillation, articles)
    hebrew_utils.py
  engine/          # NLP модули (оставить как есть, переименовать modules/)
    base.py        # Processor ABC
    pipeline/      # M1–M8 + generative
    __init__.py
  infra/           # Инфраструктура
    db.py          # SQLAlchemy engine + session
    sa_models.py   # ORM модели
    fts_manager.py # FTS5 management
    security/      # Path validation, sanitizer, audit
    reliability/   # Circuit breaker, rate limiter
    settings.py    # Pydantic settings
  services/        # Сервисный слой
    pipeline_service.py    # Orchestrator (было pipeline/orchestrator.py)
    corpus_service.py      # Import/export/statistics
    term_service.py        # Term extraction + curation
    kb_service.py          # KB operations
    translation_service.py # TM + MT providers
    study_service.py       # SRS (SM-2) для user dictionary
    concordance_service.py # KWIC search
    export_service.py      # Multi-format export
    ingest_service.py      # Multi-format ingestion
  api/             # FastAPI (оставить)
  ui/              # PyQt (оставить)
```

**Зачем:** Чёткое разделение облегчит навигацию, тестирование и масштабирование.
**Риск:** Large refactor, breaking imports. Митигация: делать по одному модулю, тесты после каждого шага.

#### A2. SQLAlchemy Migration
**Что:** Заменить прямой sqlite3 на SQLAlchemy ORM + Alembic migrations.
**Источник:** v_book `app/infra/sa_models.py` — 500+ строк ORM моделей с relationships, constraints, indexes.

Что взять из v_book:
- `Library → DictProject → SourceCorpus → SourceDocument` иерархию (адаптировать под KADIMA concepts)
- `Lemma`, `Ngram`, `Term` модели с proper FK и indexes
- `TMGlobal` + `TMEntry` для translation memory
- `StudyProgress` для SM-2 SRS
- FTS5 virtual tables + triggers (DDL)
- JSON type для features/metadata

**KADIMA-specific additions:**
- `PipelineRun` с module_results (JSON)
- `KBTerm` + `KBDefinition` + `KBEmbedding`
- `LLMConversation` + `LLMMessage`
- `AnnotationTask` + `AnnotationResult`
- `ValidationReport` + `GoldCorpus`

**Риск:** Data migration от sqlite3. Митигация: Alembic autogenerate + dry-run.

#### A3. FTS5 Search
**Что:** Добавить FTS5 virtual tables для sentence search и term search.
**Источник:** v_book `app/infra/fts_manager.py` — triggers, self-healing, unicode61 tokenizer.

KADIMA-specific:
- `sentence_fts` — поиск по предложениям корпуса
- `term_fts` — поиск по терминам + переводам + KB definitions
- `annotation_fts` — поиск по аннотациям (Label Studio sync)
- Hebrew-aware query normalization (strip nikud, article variants)

---

### Фаза B: Data Layer + Services (P1) — 3-4 недели

#### B1. Ingestion Service
**Что:** Multi-format ingestion: TXT, DOCX, PDF, PPTX.
**Источник:** v_book `app/infra/extractors/` — 5 экстракторов + SHA256 dedup.

KADIMA-specific:
- Сохранить существующий CSV/JSON importer
- Добавить DOCX (python-docx), PDF (PyPDF2 + OCR optional), PPTX (python-pptx)
- SHA256-based duplicate detection
- Incremental processing (watch folders)

#### B2. Translation Memory
**Что:** Global TM + per-project entries, offline dict + pluggable MT providers.
**Источник:** v_book `app/infra/translators/` — provider registry, offline dict, 7 providers.

KADIMA-specific:
- Сохранить M14 Translator как backend
- Добавить TM layer (tm_global + tm_entry tables)
- Provider registry: Google Translate, DeepL, LibreTranslate, local NLLB
- Batch translation service (M11 analog)

#### B3. User Dictionary + SRS
**Что:** UD items с study progress, SM-2 spaced repetition.
**Источник:** v_book `app/services/study_service.py` — SM-2 algorithm, due queue.

KADIMA-specific:
- Интегрировать с KB (terms → UD items → study cards)
- Pronunciation support (M13 diacritizer → audio via M15 TTS)
- Export/import UD как часть project exchange

#### B4. KWIC Concordance
**Что:** FTS5-powered concordance с Hebrew-aware normalization.
**Источник:** v_book `app/services/concordance_service.py` + `app/domain/kwic.py`.

KADIMA-specific:
- Интегрировать с pipeline results (показывать контекст для найденных терминов)
- Multi-corpus search

---

### Фаза C: Security + Reliability (P2) — 1-2 недели

#### C1. Security Infrastructure
**Что:** Path validation, FTS5/query sanitizer, audit logging, credential encryption.
**Источник:** v_book `app/infra/security/` — 8 модулей.

KADIMA-specific:
- API key management для LLM providers
- Input validation для FastAPI endpoints
- Rate limiting для API

#### C2. Reliability Patterns
**Что:** Circuit breaker для external services, rate limiter, process lock.
**Источник:** v_book `app/infra/reliability/`.

KADIMA-specific:
- Circuit breaker для Label Studio API
- Rate limiter для LLM API calls
- Process lock для singleton pipeline runs

---

### Фаза D: Project Exchange + Export (P2) — 1-2 недели

#### D1. Project Exchange
**Что:** Portable .hdleproj bundles (ZIP + SHA256 + ID remapping).
**Источник:** v_book `app/services/project_exchange/` — 6 файлов.

KADIMA-specific:
- Включать KB definitions + embeddings в bundle
- Включать LLM conversation history
- Включать annotation tasks + results
- CLI tools для export/import

#### D2. Enhanced Export
**Что:** Excel, CSV, JSONL, TBX, TMX форматы.
**Источник:** v_book `app/services/export_service.py`.

KADIMA-specific:
- Сохранить существующий exporter
- Добавить TBX (TermBase eXchange) для терминологов
- Добавить TMX для translation memory
- Export pipeline run reports

---

### Фаза E: Generative Modules Enhancement (P3) — 2-3 недели

Это уникальное преимущество KADIMA. Надо не потерять, а усилить.

#### E1. Module Registry + Lazy Loading
**Что:** Resource manager для ML моделей, lazy loading + LRU eviction.
**Источник:** v_book `app/services/local_models/model_resource_manager.py`.

KADIMA-specific:
- Orchestrator уже делает lazy loading — добавить LRU eviction
- VRAM budget management (для RTX 3070 8GB)
- Model health checks

#### E2. Generative Module Completion
**Реализовать недостающие:**
- M18 Sentiment Analyzer (уже есть stub)
- M15 TTS Synthesizer (уже есть stub)
- M16 STT Transcriber (уже есть stub)
- M20 Active Learning
- M24 Keyphrase Extractor
- M23 Grammar Corrector
- M25 Summarizer

---

## 4. Порядок выполнения (критический путь)

```
A1 (Clean Arch) → A2 (SQLAlchemy) → A3 (FTS5)
                                        ↓
                    B1 (Ingestion) → B2 (TM) → B3 (UD+SRS) → B4 (KWIC)
                                        ↓
                    C1 (Security) → C2 (Reliability)
                                        ↓
                    D1 (Project Exchange) → D2 (Export)
                                        ↓
                    E1 (Module Registry) → E2 (Generative Completion)
```

**Критический путь:** A1 → A2 → A3 → B1 → B2 → B3
**Параллельно с B:** можно делать C1, C2 (security не зависит от TM)
**После B:** D и E можно параллельно

---

## 5. Метрики успеха

| Метрика | Текущее | Цель |
|---|---|---|
| Архитектурные слои | 2 (engine + data) | 4 (domain + engine + infra + services) |
| SQLAlchemy coverage | 0% | 100% |
| FTS5 tables | 0 | 3+ |
| Ingestion formats | 3 (TXT, CSV, JSON) | 6+ (TXT, DOCX, PDF, PPTX, CSV, JSON) |
| Translation providers | 1 (dict) | 4+ (dict, Google, DeepL, local NLLB) |
| Test coverage | ~500 tests | 800+ tests |
| Security modules | 0 | 5+ |
| Export formats | 2 (CSV, JSON) | 5+ (CSV, JSON, Excel, TBX, TMX) |

---

## 6. Риски и митигации

| Риск | Влияние | Митигация |
|---|---|---|
| Big refactor ломает существующий код | 🔴 Высокое | Инкрементально, тесты после каждого шага |
| SQLAlchemy migration теряет данные | 🔴 Высокое | Alembic dry-run, backup перед миграцией |
| Слишком много зависимостей | 🟡 Среднее | Optional deps, lazy loading |
| Потеря уникальных фич KADIMA | 🟡 Среднее | Pipeline-first, не переписывать engine/ |
| VRAM budget на RTX 3070 | 🟡 Среднее | LRU eviction, lazy loading, CPU fallback |

---

## 7. Definition of Done (для всего плана)

- [ ] Архитектура: 4 домена (domain/engine/infra/services), чёткие границы
- [ ] SQLAlchemy: все таблицы в ORM, Alembic миграции, FTS5
- [ ] Ingestion: 6+ форматов, SHA256 dedup
- [ ] TM: global + local, 4+ providers, batch translation
- [ ] UD: items + SM-2 study progress + pronunciation
- [ ] KWIC: FTS5-powered, Hebrew-aware
- [ ] Security: path validation, audit log, credential encryption
- [ ] Project Exchange: .hdleproj bundles с KB + annotations
- [ ] Tests: 800+ passing, E2E покрытие pipeline
- [ ] Документация: актуальная README, API docs, архитектурная диаграмма
