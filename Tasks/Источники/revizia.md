# Ревизия проекта hebrew-corpus-v2 (Референс)

**Дата:** 2026-03-31
**Версия проекта:** v0.9.0
**Пакет:** `kadima/`
**Python:** 3.10+

---

## 1. Структура проекта (дерево каталогов)

```
hebrew-corpus-v2/
├── kadima/                          # Основной пакет
│   ├── __init__.py                  # Версия пакета
│   ├── app.py                       # PyQt GUI entrypoint (stub)
│   ├── cli.py                       # CLI (gui, run, api, migrate)
│   ├── annotation/                  # Label Studio интеграция
│   │   ├── __init__.py
│   │   ├── exporter.py              # Экспорт аннотаций
│   │   ├── ls_client.py             # Label Studio API клиент
│   │   ├── ml_backend.py            # ML backend для pre-annotation
│   │   ├── project_manager.py       # Управление проектами LS
│   │   └── sync.py                  # Синхронизация данных
│   ├── api/                         # FastAPI REST API
│   │   ├── __init__.py
│   │   ├── app.py                   # App factory (create_app)
│   │   ├── schemas.py               # Pydantic схемы API
│   │   └── routers/
│   │       ├── __init__.py
│   │       ├── annotation.py        # /api/v1/annotation/*
│   │       ├── corpora.py           # /api/v1/corpora/*
│   │       ├── kb.py                # /api/v1/kb/*
│   │       ├── llm.py               # /api/v1/llm/*
│   │       ├── pipeline.py          # /api/v1/pipeline/*
│   │       └── validation.py        # /api/v1/validation/*
│   ├── corpus/                      # Корпусный менеджер
│   │   ├── __init__.py
│   │   ├── exporter.py              # Экспорт корпуса
│   │   ├── importer.py              # Импорт корпуса
│   │   └── statistics.py            # Статистика корпуса
│   ├── data/                        # Data Layer (SQLite)
│   │   ├── __init__.py
│   │   ├── db.py                    # Подключение, миграции
│   │   ├── models.py                # ORM/SQL модели
│   │   ├── repositories.py         # Repository паттерн
│   │   └── migrations/
│   │       ├── 001_initial.sql      # corpora, documents, pipeline_runs
│   │       ├── 002_annotation.sql   # annotation_projects, annotations
│   │       ├── 003_kb.sql           # kb_entries, kb_links
│   │       └── 004_llm.sql          # llm_interactions
│   ├── engine/                      # Engine Layer (NLP модули)
│   │   ├── __init__.py
│   │   ├── base.py                  # Processor ABC, ProcessorResult, PipelineResult
│   │   ├── contracts.py             # ProcessorProtocol, TypedDict контракты
│   │   ├── association_measures.py  # M7: PMI, LLR, Dice
│   │   ├── canonicalizer.py         # M6: нормализация поверхностных форм
│   │   ├── hebpipe_wrappers.py      # M1: SentSplit, M2: Tokenizer, M3: MorphAnalyzer
│   │   ├── ngram_extractor.py       # M4: N-gram extraction
│   │   ├── noise_classifier.py      # M12: классификация шума
│   │   ├── np_chunker.py            # M5: NP chunking
│   │   └── term_extractor.py        # M8: Term extraction + ranking
│   ├── kb/                          # Knowledge Base
│   │   ├── __init__.py
│   │   ├── generator.py             # Автогенерация KB entries
│   │   ├── models.py                # KB модели данных
│   │   ├── repository.py            # KB хранилище
│   │   └── search.py                # Поиск по KB
│   ├── llm/                         # LLM интеграция (Dicta-LM)
│   │   ├── __init__.py
│   │   ├── client.py                # HTTP клиент к llama.cpp
│   │   ├── prompts.py               # Промпты для LLM
│   │   └── service.py               # LLM сервис-оркестрация
│   ├── nlp/                         # spaCy компоненты
│   │   ├── __init__.py
│   │   ├── pipeline.py              # spaCy pipeline регистрация
│   │   └── components/
│   │       ├── __init__.py
│   │       ├── hebpipe_morph_analyzer.py  # spaCy компонент M3
│   │       ├── hebpipe_sent_splitter.py   # spaCy компонент M1
│   │       ├── ngram_component.py         # spaCy компонент M4
│   │       ├── noise_component.py         # spaCy компонент M12
│   │       └── np_chunk_component.py      # spaCy компонент M5
│   ├── pipeline/                    # Pipeline Orchestrator
│   │   ├── __init__.py
│   │   ├── config.py                # Pydantic config (PipelineConfig)
│   │   └── orchestrator.py          # PipelineService (run, run_on_text)
│   ├── ui/                          # PyQt UI (stubbed)
│   │   ├── __init__.py
│   │   ├── annotation_view.py
│   │   ├── dashboard.py
│   │   ├── kb_view.py
│   │   ├── llm_view.py
│   │   ├── main_window.py
│   │   ├── pipeline_view.py
│   │   ├── validation_view.py
│   │   └── widgets/
│   ├── utils/                       # Утилиты
│   │   ├── __init__.py
│   │   ├── hebrew.py                # Hebrew helpers
│   │   └── logging.py               # Logging setup
│   └── validation/                  # Gold corpus валидация
│       ├── __init__.py
│       ├── check_engine.py          # Validation checks
│       ├── gold_importer.py         # Импорт gold data
│       └── report.py                # Validation report
├── config/
│   ├── config.default.yaml          # Дефолтный конфиг pipeline
│   └── config.schema.json           # JSON Schema
├── doc/                             # Документация (ТЗ + продуктовый анализ)
├── scripts/                         # Shell скрипты
│   ├── download_models.sh
│   ├── run_label_studio.sh
│   └── setup_dev.sh
├── templates/                       # Label Studio XML шаблоны
│   ├── hebrew_ner.xml
│   ├── hebrew_pos.xml
│   └── hebrew_term_review.xml
├── tests/                           # Тесты (~298 тестов)
│   ├── conftest.py
│   ├── fixture_loader.py
│   ├── corpus/                      # test_exporter, test_importer
│   ├── engine/                      # 7 test файлов (M1-M8, M12)
│   ├── integration/                 # test_pipeline_e2e.py (stub)
│   ├── validation/                  # test_check_engine, gold_importer, report
│   ├── test_config.py
│   ├── test_corpus.py
│   ├── test_data_layer.py
│   ├── test_fixtures.py
│   └── data/                        # 26 gold corpus наборов (he_01–he_26)
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── README.md
├── CLAUDE.md
└── ENV_SETUP.md
```

---

## 2. Модуль за модулем

### 2.1 Engine Layer (`kadima/engine/`)

#### base.py — Базовые интерфейсы
- **Путь:** `kadima/engine/base.py`
- **Назначение:** ABC Processor, ProcessorResult, PipelineResult, ProcessorStatus enum
- **Ключевые классы:**
  - `Processor(ABC)` — абстрактный базовый класс с методами `name`, `module_id`, `process()`, `validate_input()`, `get_status()`
  - `ProcessorResult` — dataclass результата модуля (module_name, status, data, metadata, errors, processing_time_ms)
  - `PipelineResult` — dataclass результата всего pipeline (corpus_id, profile, module_results, terms, ngrams, np_chunks)
  - `ProcessorStatus(Enum)` — READY, RUNNING, FAILED, SKIPPED
- **Зависимости:** stdlib only

#### contracts.py — Typed контракты
- **Путь:** `kadima/engine/contracts.py`
- **Назначение:** TypedDict контракты для входных данных модулей + Protocol для structural typing
- **Ключевые:**
  - `ProcessorProtocol(Protocol)` — structural typing контракт
  - `AMScoreDict`, `TermExtractInput` — TypedDict для входов M7, M8
- **Зависимости:** stdlib (typing)

#### hebpipe_wrappers.py — M1, M2, M3
- **Путь:** `kadima/engine/hebpipe_wrappers.py`
- **Назначение:** Sentence splitting, Tokenization, Morphological analysis
- **Ключевые классы:**
  - `HebPipeSentSplitter(M1)` — разбиение текста на предложения по `. ` после ивритских символов
  - `HebPipeTokenizer(M2)` — токенизация по пробелам с сохранением позиций
  - `HebPipeMorphAnalyzer(M3)` — **STUB**: lemma=surface, POS="NOUN" всегда, только определение ה- определяет `is_det`
- **Data types:** `Sentence`, `Token`, `MorphAnalysis`, `SentenceSplitResult`, `TokenizeResult`, `MorphResult`
- **Зависимости:** stdlib (re, time)

#### ngram_extractor.py — M4
- **Путь:** `kadima/engine/ngram_extractor.py`
- **Назначение:** Извлечение n-grams (2-5) из токенизированных предложений
- **Ключевые классы:** `NgramExtractor`, `Ngram`, `NgramResult`
- **Зависимости:** stdlib

#### np_chunker.py — M5
- **Путь:** `kadima/engine/np_chunker.py`
- **Назначение:** NP chunking — извлечение noun phrases из морфологических анализов
- **Ключевые классы:** `NPChunker`, `NPChunk`, `NPChunkResult`
- **Зависимости:** stdlib

#### canonicalizer.py — M6
- **Путь:** `kadima/engine/canonicalizer.py`
- **Назначение:** Нормализация поверхностных форм токенов к каноническому виду
- **Ключевые классы:** `Canonicalizer`, `CanonicalMapping`, `CanonicalResult`
- **Зависимости:** stdlib

#### association_measures.py — M7
- **Путь:** `kadima/engine/association_measures.py`
- **Назначение:** Вычисление ассоциативных мер: PMI, LLR, Dice для bigram pairs
- **Ключевые классы:** `AMEngine`, `AMScore`, `AMResult`
- **Зависимости:** stdlib (math)

#### term_extractor.py — M8
- **Путь:** `kadima/engine/term_extractor.py`
- **Назначение:** Агрегация n-gram + AM + NP → ранжированные термины
- **Ключевые классы:** `TermExtractor`, `Term`, `TermResult`
- **Ключевые параметры:** profile (precise/balanced/recall), min_freq, pmi_threshold
- **Зависимости:** stdlib

#### noise_classifier.py — M12
- **Путь:** `kadima/engine/noise_classifier.py`
- **Назначение:** Классификация токенов/текстов как noise (латиница, числа, пунктуация и т.д.)
- **Ключевые классы:** `NoiseClassifier`, `NoiseResult`
- **Зависимости:** stdlib

### 2.2 Pipeline Layer (`kadima/pipeline/`)

#### config.py — Конфигурация
- **Путь:** `kadima/pipeline/config.py`
- **Назначение:** Pydantic v2 конфигурация pipeline с YAML loader и JSON Schema export
- **Ключевые классы:**
  - `PipelineConfig` — основная конфигурация (language, profile, modules, thresholds, annotation, llm, kb, logging, storage)
  - `Profile(Enum)` — PRECISE, BALANCED, RECALL
  - `ThresholdsConfig` — min_freq, pmi_threshold, hapax_filter + profile overrides
  - `AnnotationConfig`, `LLMConfig`, `KBConfig`, `LoggingConfig`, `StorageConfig`
- **Константы:** `VALID_MODULES = frozenset([...])` — только 9 NLP модулей (M1-M8, M12)
- **Ключевые функции:** `load_config()`, `export_json_schema()`, `validate_config_file()`
- **Зависимости:** pydantic, PyYAML

#### orchestrator.py — Оркестратор
- **Путь:** `kadima/pipeline/orchestrator.py`
- **Назначение:** Оркестрация выполнения M1→M2→...→M8→M12
- **Ключевые классы:**
  - `PipelineService` — регистрирует модули, трансформирует данные между ними
  - `_register_modules()` — создаёт все 9 модулей (M1-M8, M12)
  - `run_on_text(text)` — полный pipeline на одном тексте
  - `run(corpus_id)` — **STUB** (TODO: загрузка из БД, запуск, сохранение)
- **Зависимости:** engine modules, pipeline.config

### 2.3 Data Layer (`kadima/data/`)
- **db.py** — подключение к SQLite (WAL mode), миграции, `get_connection()`, `ensure_db()`
- **models.py** — SQL-модели данных
- **repositories.py** — Repository паттерн для CRUD операций
- **Миграции:** 4 SQL файла (initial, annotation, kb, llm)

### 2.4 API Layer (`kadima/api/`)
- **app.py** — FastAPI app factory, CORS, health endpoint
- **Роутеры:** corpora, pipeline, validation (ядро) + annotation, kb, llm (расширение)
- **schemas.py** — Pydantic схемы запросов/ответов
- **Примечание:** Нет generative router (отсутствует в референсе)

### 2.5 Annotation (`kadima/annotation/`)
- Label Studio integration: client, exporter, sync, ML backend, project manager
- 3 XML шаблона: hebrew_ner.xml, hebrew_pos.xml, hebrew_term_review.xml

### 2.6 LLM (`kadima/llm/`)
- HTTP клиент к llama.cpp, промпты, сервис-оркестрация
- Интеграция с Dicta-LM

### 2.7 KB (`kadima/kb/`)
- Knowledge Base: модели, репозиторий, поиск, автогенерация

### 2.8 NLP Components (`kadima/nlp/components/`)
- spaCy компоненты-обёртки для M1, M3, M4, M5, M12

### 2.9 UI (`kadima/ui/`)
- PyQt desktop UI — **все файлы-заглушки (stubs)**
- Виджеты: dashboard, pipeline_view, annotation_view, kb_view, llm_view, validation_view

### 2.10 Utils (`kadima/utils/`)
- `hebrew.py` — Hebrew text helpers
- `logging.py` — Logging configuration

### 2.11 Validation (`kadima/validation/`)
- `check_engine.py` — валидационные проверки
- `gold_importer.py` — импорт gold corpus данных
- `report.py` — генерация отчётов валидации

### 2.12 CLI (`kadima/cli.py`)
- Команды: `gui`, `run --text/--corpus`, `api`, `migrate`, `--init`, `--version`

---

## 3. NLP Pipeline

### Шаги пайплайна (последовательность)
```
Text input
  → M1 (SentSplit) — разбиение на предложения
  → M2 (Tokenizer) — токенизация каждого предложения
  → M3 (MorphAnalyzer) — морфологический анализ токенов
  → M4 (NgramExtractor) — извлечение n-grams из токенов
  → M5 (NPChunker) — извлечение NP из морф. анализов
  → M6 (Canonicalizer) — нормализация поверхностных форм
  → M7 (AMEngine) — вычисление PMI, LLR, Dice
  → M8 (TermExtractor) — ранжирование терминов
  → M12 (NoiseClassifier) — классификация шума
```

### Инструменты
- **Токенизация/морфология:** заглушка (M3 STUB) + интеграционные точки для hebpipe
- **Конфигурация:** Pydantic v2, YAML, JSON Schema
- **Хранение:** SQLite с WAL mode, 4 миграции
- **API:** FastAPI + uvicorn
- **GUI:** PyQt6 (заглушка)
- **Аннотация:** Label Studio integration
- **LLM:** llama.cpp (Dicta-LM)

---

## 4. Масштабирование

- **Batch обработка:** `run(corpus_id)` — **STUB** (TODO)
- **Параллелизм:** Не реализован (последовательная обработка)
- **Конфигурируемость:**
  - 3 профиля: precise, balanced, recall
  - Пороговые значения: min_freq, pmi_threshold, hapax_filter
  - Возможность включения/отключения модулей через `modules` list
  - Profile overrides для thresholds

---

## 5. Тесты

### Покрытие (~298 тестов)
| Модуль | Файл | Статус |
|--------|------|--------|
| Config | `test_config.py` | 33 теста |
| Corpus | `test_corpus.py`, `corpus/test_exporter.py`, `corpus/test_importer.py` | Рабочие |
| Data Layer | `test_data_layer.py` | Рабочий |
| Fixtures | `test_fixtures.py` | Проверка gold corpus fixtures |
| Engine M4 | `test_ngram_extractor.py` | Рабочие |
| Engine M5 | `test_np_chunker.py` | Рабочие |
| Engine M6 | `test_canonicalizer.py` | Рабочие |
| Engine M7 | `test_association_measures.py` | Рабочие |
| Engine M8 | `test_term_extractor.py` | Рабочие |
| Engine M12 | `test_noise_classifier.py` | Рабочие |
| Engine M1-M3 | `test_hebpipe_wrappers.py` | 14 тестов |
| Validation | `test_check_engine.py`, `test_gold_importer.py`, `test_report.py` | Рабочие |
| Integration | `test_pipeline_e2e.py` | **ПУСТОЙ** (stub) |

### Gold corpus: 26 наборов (he_01 — he_26)
- Каждый: corpus_manifest.json, expected_counts.yaml, expected_lemmas.csv, expected_terms.csv, review_sheet.csv, manual_checklist.md, raw/*.txt
- Дополнительные метаданные: METHODOLOGY.md, ACCEPTANCE_CRITERIA.md, COVERAGE_ANALYSIS.md и т.д.

---

## 6. Документация

### Статус
- **README.md** — описание архитектуры, quick start, Docker
- **CLAUDE.md** — полная карта проекта, 25 модулей (M1-M25), порядок реализации, конвенции кода
- **doc/ТЗ/** — полное техзадание: Vision, Scope, PRD, Architecture, API Spec, Data Model, NLP Stack, и т.д.
- **doc/Продуктовый анализ/** — анализ 10 конкурентов (Sketch Engine, TermSuite, spaCy, Stanford, brat, INCEpTION, AntConc, Label Studio, IAHLT, Lilt)
- **tests/data/** — обширная документация тестовых данных (методология, acceptance criteria, quality review)

---

## 7. Экспорт/Импорт форматов

- **Импорт:** corpus/importer.py (поддержка различных форматов текста)
- **Экспорт:** corpus/exporter.py (экспорт корпуса и результатов)
- **Label Studio:** annotation/exporter.py, sync.py
- **JSON Schema:** config/schema export
- **Templates:** XML шаблоны для Label Studio (NER, POS, term review)

---

## 8. Итоговая сводка

**Что проект умеет (реализовано):**
- Токенизация и разбиение на предложения ивритского текста (M1, M2)
- Морфологический анализ (M3 — STUB, lemma=surface)
- Извлечение n-grams, NP chunks, нормализация форм (M4, M5, M6)
- Ассоциативные меры PMI/LLR/Dice (M7)
- Ранжирование терминов с 3 профилями (M8)
- Классификация шума (M12)
- Конфигурация pipeline через YAML/Pydantic
- REST API (FastAPI) с роутерами corpora, pipeline, validation
- Label Studio интеграция для аннотации
- LLM интеграция (Dicta-LM через llama.cpp)
- Knowledge Base с поиском
- Gold corpus валидация (26 наборов)
- SQLite хранилище с миграциями

**Критические проблемы:**
1. **M3 MorphAnalyzer — STUB** (lemma=surface, POS="NOUN" всегда) → искажает M4-M8
2. **run(corpus_id) — STUB** (TODO)
3. **E2E тесты — пустые** (test_pipeline_e2e.py = stub)
4. **VALID_MODULES** — только 9 NLP модулей, нет поддержки M13-M25
5. **UI** — все виджеты-заглушки
6. **pyproject.toml** — нет optional dependency groups для ML модулей

**Не реализовано (согласно CLAUDE.md roadmap):**
- M13 Diacritizer, M14 Translator, M15 TTS, M16 STT, M17 NER
- M18 Sentiment, M19 Summarizer, M20 QA, M21 MorphGenerator
- M22 Transliterator, M23 Grammar, M24 Keyphrase, M25 Paraphraser
- Generative API router
- Generative UI views
