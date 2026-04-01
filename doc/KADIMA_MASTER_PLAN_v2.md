# KADIMA Master Plan v2.0
## Hebraic Dynamic Lexicon Engine — Синтез трёх стратегических планов

> **Составлен:** 2026-04-01 | **Ревизия:** синтез Claude Code + Qwen3.6PlusPreview + MiMoV2Pro  
> **Статус:** Утверждён к реализации

---

## ЧАСТЬ I: СРАВНИТЕЛЬНАЯ ОЦЕНКА ТРЁХ ПЛАНОВ

### 1.1 Матрица качества планов

| Критерий | Claude Code | Qwen3.6Plus | MiMoV2Pro |
|----------|:-----------:|:-----------:|:---------:|
| Знание кодовой базы KADIMA | ✅ Точно | ⚠️ Неточности* | ✅ Точно |
| Глубина анализа V_book | ✅ Хорошо | ✅✅ Отлично | ✅ Достаточно |
| Инженерная дисциплина (DoD, cold-audit) | ❌ Пропущено | ✅✅ Главное | ❌ Пропущено |
| Конкретность файловых изменений | ✅✅ Детально | ✅ Хорошо | ⚠️ Поверхностно |
| Философия ("не переписывать") | ⚠️ Частично | ⚠️ Частично | ✅✅ Главный принцип |
| Временны́е оценки | ❌ Нет | ✅✅ По часам | ❌ Нет |
| Риски и митигация | ✅ Есть | ✅ Есть | ✅ Есть |
| Уникальные инсайты | Аудио-кэш, ML в workflow, Command palette | Cold-audit, DoD, Operations Center, staged first-paint | SM-2 SRS, circuit breaker, annotation_fts |
| Учёт текущего прогресса T4/T5 | ✅ Да | ⚠️ Частично | ⚠️ Частично |

*Qwen неверно предполагает отсутствие SQLAlchemy ORM (уже есть), называет M15-M20 "stubs" (уже реализованы).

---

### 1.2 Уникальный вклад каждого плана

**Qwen3.6PlusPreview — инженерная дисциплина:**
- **Cold-Audit Framework** (32+ волн, ограниченная задержка UI) — критически важно
- **Staged first-paint contracts** (каждый view ≤0.5s на первый рендер)
- **DoD документация** + P1/P2/P3 verification tiers
- **Evidence-first patches** — каждый фикс с before/after метриками
- **Operations Center / Pipeline Throttler** — ограничение одновременных heavy операций
- **Self-check modes** (`--self-check import/db_open/health`) для CI
- **Подробные часовые оценки** (P0: 116h, P1: 132h, ... итого ~36 EW / 26 недель)
- **Stanza subprocess isolation** (запуск NLP в отдельном процессе — для stability)

**MiMoV2Pro — философия и паттерны:**
- **"Не переписывать — адаптировать"** — главный принцип, всё остальное из него
- **Pipeline-first**: KADIMA — платформа, а не только Desktop app
- **SM-2 Spaced Repetition System** для User Dictionary (study cards из терминов)
- **annotation_fts** — FTS5 для аннотаций Label Studio (уникально для KADIMA)
- **Circuit breaker** для Label Studio API и LLM API (reliability pattern)
- **Rate limiter** для внешних API (LLM, MT providers)
- **Watch folders** — инкрементальная обработка (auto-import из директории)
- **Multi-corpus KWIC search** — поиск одновременно по нескольким корпусам

**Claude Code — конкретика инфраструктуры:**
- **Dual read/write SQLite engines** (PERF-SCALE PATCH-C из V_book)
- **Content-addressed audio cache** (SHA256 по term+provider+voice)
- **Audio playlist management** с очередью воспроизведения
- **Reference corpus** (Hebrew Wikipedia) через `is_reference` флаг в Project
- **ML-Enhanced Term Workflow** — колонка ML Actions в таблице терминов
- **KWIC → Audio интеграция** (каждый результат concordance с кнопкой [▶])
- **First-run wizard** + **Command palette** (Ctrl+K)
- **NLP Engine pluggable architecture** (ABC + registry для engines)
- **Backward-compatible migration** — старые таблицы не удаляются, добавляются новые

---

### 1.3 Вердикт по Задаче 1

**По глубине проработки V_book-практик:** Qwen3.6PlusPreview (первое место)  
**По знанию текущего состояния KADIMA:** Claude Code (первое место)  
**По философской зрелости:** MiMoV2Pro (первое место)  

**Ни один план не достаточен сам по себе.** Qwen — лучший на engineering discipline, но делает неверные предположения о текущем состоянии. MiMo — правильная философия, но недостаточная глубина. Claude — точное знание кода, но пропущена инженерная дисциплина как система.

**По Задаче 2:** необходим синтез всех трёх + повторный аудит.

---

## ЧАСТЬ II: ПОВТОРНЫЙ АУДИТ — КРИТИЧЕСКИЕ РАСХОЖДЕНИЯ

### 2.1 Что все три плана упустили

| Пропуск | Почему критично |
|---------|----------------|
| **SQLAlchemy ORM уже есть** в `kadima/data/sa_models.py` (18 моделей) | Qwen предлагает "внедрить SA" — уже сделано; не нужно переделывать |
| **M15-M20 уже реализованы** (Working, не stubs) | Qwen планирует их как "production hardening" — верно, но со статусом "Working" |
| **T4 завершён** (GenerativeView + AnnotationView) | Некоторые планы игнорируют это и планируют заново |
| **Async SA layer уже есть** (R-2.7) | Планы предлагают его добавить — уже добавлен |
| **API FastAPI уже работает** (10+ endpoints) | Планируют "с нуля" — нужно заполнить только stub роутеры |
| **KB с эмбеддингами работает** | Все три включают в план — нужно только улучшить, не создавать |
| **Stub роутеры** (validation, annotation, kb, llm) | 16 TODO endpoints — D4 в CLAUDE.md — критично, но не упомянуто детально |
| **CI/CD отсутствует** (.github/workflows/ есть, но пустой?) | Нет ни в одном плане |
| **Нет cross-platform path resolver** | V_book: `db_path_resolver.py` для Windows/macOS/Linux | 
| **Нет механизма backup/restore DB** | V_book имеет BackupService |

### 2.2 Конфликты между планами

| Конфликт | Claude Code | Qwen | MiMo | Решение |
|----------|------------|------|------|---------|
| Stanza subprocess | Не упоминает | Критично (P1.1) | Не упоминает | KADIMA уже использует lazy loading; subprocess нужен только при VRAM pressure — откладывается |
| Library иерархия | Добавить Library→Project | Добавить | Добавить | Да, добавить — но backward compatible через views |
| SQLAlchemy | Расширить | "Добавить" (уже есть!) | "Заменить sqlite3" | Расширить существующий SA layer |
| Alembic | Не упоминает | Не упоминает | Рекомендует | Добавить Alembic для автогенерации diff — но SQL миграции остаются |

---

## ЧАСТЬ III: МАСТЕР-ПЛАН KADIMA v2.0

### Философские принципы (обязательны к соблюдению)

```
1. НЕ ПЕРЕПИСЫВАТЬ — АДАПТИРОВАТЬ (MiMo)
   Существующий код работает → добавляем слои, не заменяем ядро
   engine/ остаётся нетронутым; pipeline/orchestrator.py — только расширяется

2. PIPELINE-FIRST (MiMo)  
   KADIMA — платформа, а не только Desktop app
   Все фичи доступны через API, CLI и UI

3. EVIDENCE-FIRST (Qwen)
   Каждый фикс производительности: before/after метрики
   Cold-audit перед релизом каждой фазы

4. ИНКРЕМЕНТАЛЬНО, НЕ BIG BANG (все три)
   Каждый патч: независимо buildable + testable
   Commit = работающая система, не "WIP"

5. ML КАК СУПЕРСИЛА (Claude)
   V_book — умный словарь. KADIMA — умный, говорящий, обучаемый словарь.
   ML модули интегрированы в каждый workflow, а не изолированы во вкладке
```

---

### Структура целевой архитектуры

```
kadima/
├── domain/          # НОВЫЙ — чистая бизнес-логика (без зависимостей)
│   ├── dto.py       # Все DTO: ProjectDTO, TermDTO, KWICResult, AudioAsset, StudyCard
│   ├── exceptions.py
│   ├── hebrew_utils.py   # nikud, cantillation, prefix, maqaf, geresh
│   ├── kwic.py           # format_kwic(), KWICResult
│   ├── scoring.py        # PMI, T-score, LLR, Dice (перенести из engine/)
│   └── normalization/    # Детерминированная нормализация иврита
│
├── engine/          # БЕЗ ИЗМЕНЕНИЙ — M1-M25 процессоры
│   └── ...          # Только добавляем M23/M24/M25 (T5)
│
├── infra/           # НОВЫЙ — инфраструктура (DB, providers, security)
│   ├── db.py        # DatabaseManager: WAL PRAGMAs + dual engines + Write Gate
│   ├── write_gate.py       # RLock сериализатор записей с телеметрией
│   ├── db_retry.py         # Retry декоратор SQLITE_BUSY
│   ├── fts_manager.py      # FTS5 DDL + triggers + self-healing
│   ├── sa_models.py        # Расширить существующий (Library, DictProject, TM, Audio)
│   ├── settings.py         # QSettings INI singleton
│   ├── db_path_resolver.py # Cross-platform: Windows M:\, macOS ~/Library, Linux ~/.local
│   ├── security/
│   │   ├── crypto.py       # AES-256-GCM для API ключей
│   │   ├── validators.py   # sanitize_fts5_query, validate_path, sanitize_csv
│   │   └── audit.py        # AuditLogger → audit_log table
│   ├── reliability/
│   │   ├── circuit_breaker.py  # Для LS API, LLM API, MT providers
│   │   └── rate_limiter.py     # Для LLM API calls
│   ├── nlp_engines/
│   │   ├── base_engine.py   # NLPEngine ABC
│   │   ├── rules_engine.py  # Текущий HebPipe (rule-based) — default
│   │   ├── stanza_engine.py # Stanza (опционально, CPU)
│   │   ├── dictabert.py     # NeoDictaBERT (GPU, наше преимущество)
│   │   └── mock_engine.py   # Для тестов
│   ├── audio/
│   │   ├── base_provider.py
│   │   ├── providers/       # xtts.py, mms.py, mock.py
│   │   └── cache.py         # Content-addressed cache (SHA256)
│   ├── extractors/          # TXT, DOCX, PDF+OCR, PPTX
│   └── translators/         # провайдеры MT (Google, DeepL, NLLB, local M14)
│
├── services/        # НОВЫЙ — бизнес-логика (использует infra/ + engine/)
│   ├── project_service.py      # CRUD проектов, Library, singleton
│   ├── corpus_service.py       # CRUD корпусов, статистика
│   ├── document_service.py     # Импорт, SHA256 dedup, watch folders
│   ├── pipeline_service.py     # Обёртка над pipeline/orchestrator (уже есть)
│   ├── concordance_service.py  # FTS5-powered KWIC с Hebrew normalization
│   ├── tm_service.py           # Translation Memory: global + per-project
│   ├── dictionary_service.py   # User dictionary + SM-2 SRS study cards
│   ├── audio_service.py        # TTS generation + cache + playlist
│   ├── export_service.py       # Excel, CSV, JSONL, TBX, TMX, CoNLL-U, project bundle
│   ├── kb_service.py           # Перенести из kb/ (оставить kb/ как модуль)
│   ├── annotation_service.py   # LS wrapper (оставить annotation/ нетронутым)
│   ├── batch_translate_service.py  # Chunked MT с pause/resume
│   ├── operations_center.py    # Singleton: ограничение concurrent heavy ops
│   ├── backup_service.py       # Backup/restore + SHA256 integrity
│   ├── health_check_service.py # Проверка моделей, провайдеров, DB
│   └── study_service.py        # SM-2 SRS алгоритм для User Dictionary
│
├── data/            # СУЩЕСТВУЮЩИЙ — только расширяется
│   ├── db.py        # → мигрирует в infra/db.py (оставить alias)
│   ├── migrations/  # Добавляем 005-020
│   ├── sa_models.py # → мигрирует в infra/sa_models.py (оставить alias)
│   └── repositories.py  # Остаётся, но вызывается только через services/
│
├── pipeline/        # БЕЗ ИЗМЕНЕНИЙ — только расширяется
├── validation/      # БЕЗ ИЗМЕНЕНИЙ
├── annotation/      # БЕЗ ИЗМЕНЕНИЙ
├── kb/              # БЕЗ ИЗМЕНЕНИЙ
├── llm/             # БЕЗ ИЗМЕНЕНИЙ
│
├── api/             # СУЩЕСТВУЮЩИЙ — заполнить stub роутеры
│   └── routers/
│       ├── validation.py   ← 5 endpoints (D4)
│       ├── annotation.py   ← 4 endpoints (D4)
│       ├── kb.py           ← 5 endpoints (D4)
│       └── llm.py          ← 5 endpoints (D4)
│
└── ui/              # СУЩЕСТВУЮЩИЙ — добавить views + polish
    ├── concordance_view.py  ← НОВЫЙ
    ├── first_run_wizard.py  ← НОВЫЙ
    ├── command_palette.py   ← НОВЫЙ
    └── dialogs/
        ├── batch_translate_dialog.py  ← НОВЫЙ
        ├── project_settings_dialog.py ← НОВЫЙ
        └── staged_progress_dialog.py  ← НОВЫЙ (по V_book паттерну)
```

---

### База данных: миграции 005–020

| Миграция | Таблицы | Источник | Приоритет |
|----------|---------|----------|-----------|
| 005 | `library`, `dict_project` (NLP settings), `source_corpus` | V_book + Claude | 🔴 |
| 006 | `sentence_fts` FTS5, `term_fts` FTS5, triggers | V_book + Qwen | 🔴 |
| 007 | `tm_entry`, `tm_global`, `user_dictionary`, `ud_entry` | V_book + MiMo | 🟠 |
| 008 | `audit_log`, `credentials` (encrypted) | V_book + Qwen | 🟠 |
| 009 | `audio_asset` (content-addressed cache) | V_book + Claude | 🟡 |
| 010 | `study_progress` (SM-2 SRS) | MiMo | 🟡 |
| 011 | `sentence_nlp_snapshot` (per-doc NLP stats cache) | Qwen | 🟡 |
| 012 | `term_curation_state` (review workflow) | V_book + Claude | 🟡 |
| 013 | `annotation_fts` FTS5 (Label Studio annotations) | MiMo | 🟡 |
| 014 | `kwic_index` (KWIC statistics cache) | Claude | 🟢 |
| 015 | `project_export_log` | Claude | 🟢 |
| 016 | `mt_usage_event` (usage tracking для batch MT) | Qwen | 🟢 |
| 017 | `processor_run` + `run_error` (pipeline history) | Qwen | 🟢 |

---

## ЧАСТЬ IV: ФАЗОВЫЙ ПЛАН РЕАЛИЗАЦИИ

---

### ФАЗА 0: Инженерная дисциплина (P0)
**Блокирующий. Сначала это, потом всё остальное.**  
**Оценка: 2 недели | ~40 часов**

Источник: Qwen3.6PlusPreview (его главный инсайт)

#### P0.1 — Definition of Done
```
Файл: Tasks/DEFINITION_OF_DONE.md

Критерии DoD для каждого патча:
  ✅ Фича работает по acceptance criteria
  ✅ Тесты: новые + регрессионные проходят
  ✅ Нет новых security issues
  ✅ ruff check kadima/ → 0 ошибок
  ✅ Нет print(), нет bare except:, нет hardcoded paths
  ✅ Документация обновлена если поведение изменилось
  ✅ Commit message: conventional format type(scope): desc
```

#### P0.2 — Self-check modes (CLI)
```
kadima/cli.py → добавить:
  kadima --self-check import     → проверить импорты всех модулей
  kadima --self-check db_open    → открыть и закрыть DB, вернуть JSON
  kadima --self-check health     → проверить модели, провайдеры
  kadima --self-check migrations → проверить версию схемы

Выход: JSON {"status": "ok"|"error", "details": {...}}
Использование: в CI перед запуском тестов
```

#### P0.3 — Cold-Audit Framework (сокращённый)
```
Документ: Tasks/COLD_AUDIT_FRAMEWORK.md

Методология (из V_book):
  1. Измеряем cold-open время каждого view (первый рендер)
  2. Цель: ≤500ms для первого paint
  3. Измеряем с реальными данными (1000+ документов)
  4. Записываем baseline перед каждой фазой

Первые волны аудита (после P1):
  Wave 1: Dashboard cold-open
  Wave 2: Pipeline view + pipeline run
  Wave 3: Results view (5000 терминов)
  Wave 4: Validation view (226 checks)
  Wave 5: Concordance search (FTS5 query)
```

#### P0.4 — CI Pipeline
```
.github/workflows/ci.yml:
  - pytest tests/ -x --ignore=tests/ui (без PyQt6)
  - ruff check kadima/
  - python -m kadima --self-check import
  - python -m kadima --self-check db_open

Запускается на: push + pull_request в main
```

---

### ФАЗА 1: Фундамент инфраструктуры (F)
**Блокирующий для всего остального.**  
**Оценка: 3 недели | ~80 часов**

#### F1.1 — DB Layer Hardening (~16ч)
```
kadima/infra/db.py (НОВЫЙ, db.py → legacy alias)
  - WAL PRAGMAs: busy_timeout=15000, temp_store=MEMORY, 
                 mmap_size=268435456, cache_size=-65536, synchronous=NORMAL
  - @event.listens_for(engine, "connect") для всех PRAGMAs
  - @event.listens_for(engine, "checkout") для FK=ON reset
  - Отдельный _read_engine: pool_size=4, max_overflow=4

kadima/infra/write_gate.py (НОВЫЙ по V_book паттерну)
  - serialized_db_write(operation) context manager
  - RLock + телеметрия wait_ms / hold_ms
  - Предупреждение если wait_ms > 250ms или hold_ms > 2000ms

kadima/infra/db_retry.py (НОВЫЙ)
  - @db_retry(max_attempts=3, backoff_ms=100) декоратор
  - Перехватывает OperationalError "database is locked"
```

#### F1.2 — SettingsService (~8ч)
```
kadima/infra/settings.py (НОВЫЙ singleton)
  - QSettings INI: "KADIMA"/"KADIMA"
  - Методы: get_string/get_int/get_bool/set_value
  - save_geometry(widget) / restore_geometry(widget)
  - save_table_state(table, key) / restore_table_state(table, key)

kadima/ui/main_window.py:
  - Сохранять geometry при closeEvent
  - Восстанавливать last_view_index при startup
  - Сохранять profile combo state
```

#### F1.3 — FTS5 Manager (~16ч)
```
kadima/data/migrations/005_fts5.sql:
  - sentence_fts USING fts5(text, doc_id, sentence_id, 
                           tokenize='unicode61 remove_diacritics 1')
  - term_fts USING fts5(he_term, translation, project_id UNINDEXED)
  - annotation_fts USING fts5(text, task_id UNINDEXED) -- (MiMo insight)
  - Триггеры: trg_sentence_ai/au/ad, trg_term_ai/au/ad

kadima/infra/fts_manager.py (НОВЫЙ)
  - ensure_fts_tables() — создать если нет
  - repair_fts_parity() — self-healing если расхождение
  - reindex_project(project_id) — полное переиндексирование
```

#### F1.4 — Domain Layer (~20ч)
```
kadima/domain/dto.py (НОВЫЙ)
  - ProjectDTO, LibraryDTO, CorpusDTO, DocumentDTO
  - TermDTO, KWICResult, AudioAsset, StudyCard
  - ProjectStats, CorpusStats, ValidationReport

kadima/domain/hebrew_utils.py (НОВЫЙ)
  - strip_nikud(text), strip_cantillation(text)
  - normalize_whitespace(text)
  - get_article_variants(query) → List[str]  # поиск с/без ה
  - is_pronoun(word) → bool  # для det_surfaces detection

kadima/domain/kwic.py (НОВЫЙ)
  - format_kwic(sentence, match, context_chars=50) → (left, match, right)
  - KWICResult dataclass

kadima/domain/scoring.py (ПЕРЕНЕСТИ из engine/)
  - pmi(), t_score(), llr(), dice() — уже есть, переместить
```

#### F1.5 — Data Hierarchy Migration (~20ч)
```
kadima/data/migrations/006_project_hierarchy.sql:
  CREATE TABLE library (...)
  CREATE TABLE dict_project (library_id, src_lang, tgt_lang, nlp_engine,
    mwe_min_freq, mwe_min_pmi, mwe_max_n, is_reference, ref_db_path)
  CREATE TABLE source_corpus (project_id, name, watch_folder_path)
  -- backward compat: INSERT INTO library DEFAULT; INSERT INTO dict_project FROM corpora

kadima/infra/sa_models.py — расширить существующий:
  - Добавить Library, DictProject, SourceCorpus (+ relationships)
  - Corpora → DictProject (alias/migration)

kadima/services/project_service.py (НОВЫЙ singleton):
  - create_project / open_project / list_projects / delete_project
  - get_project_stats() → ProjectStats DTO
```

---

### ФАЗА 2: Search & KWIC Concordance (S)
**Критично для UX лингвиста.**  
**Оценка: 2 недели | ~48ч**

#### S1 — ConcordanceService + KWIC View (~32ч)
```
kadima/services/concordance_service.py (НОВЫЙ):
  - search(query, project_id, limit=100) → List[KWICResult]
  - normalize_hebrew_search(query) → List[str]  # article variants
  - Использует sentence_fts FTS5 table
  - sanitize_fts5_query(query) перед поиском (security)

kadima/ui/concordance_view.py (НОВЫЙ):
  - Input: RTLTextEdit (поисковая строка)
  - Table: левый контекст | ключевое слово (bold) | правый контекст | источник
  - Кнопка [▶] на каждой строке → аудио воспроизведение контекста (Claude insight)
  - Клик на строку → открывает документ на нужном предложении
  - Filters: по проекту, корпусу, POS
  - Export results → CSV
```

#### S2 — Coverage Panel (~16ч)
```
kadima/services/coverage_service.py (НОВЫЙ):
  - get_term_coverage(project_id) → CoverageStats
  - Термины найдены / всего в корпусе (%)
  - Топ-N терминов по частоте
  - Hapax legomena count
  - Уникальные леммы по документам

kadima/ui/results_view.py — добавить Coverage Panel в правую панель
```

---

### ФАЗА 3: Translation Memory & User Dictionary (T)
**Ключевая фича для терминографов.**  
**Оценка: 3 недели | ~80ч**

#### T1 — Translation Memory (~32ч)
```
kadima/data/migrations/007_tm.sql:
  - tm_entry (project_id, he_term, tgt_lang, translation, source, confidence)
  - tm_global (he_term, tgt_lang, translation, usage_count) -- cross-project
  - user_dictionary (project_id, he_term, translation, notes)

kadima/services/tm_service.py (НОВЫЙ):
  - add_translation(term, translation, source='user') 
  - lookup(term, tgt_lang) → Optional[str]  # TM lookup
  - export_tmx(project_id) → str  # TMX XML
  - import_tmx(file_path, project_id) → int  # count imported
  - sync_global_tm() → int  # push project TM → global TM
```

#### T2 — Batch Translation Worker V2 (~24ч)
```
kadima/services/batch_translate_service.py (НОВЫЙ по V_book паттерну):
  - BatchTranslateEngine: chunked processing (50 терминов/chunk)
  - Chain mode: TM lookup → M14 ML → Google fallback
  - Force mode: только M14
  - Pause/Resume через checkpoint (commit каждого chunk)
  - Emit: progress_signal(int, str), finished_signal(int), failed_signal(str)

kadima/ui/dialogs/batch_translate_dialog.py (НОВЫЙ):
  - QProgressBar + статус "Переведено X/Y"
  - Pause/Resume/Cancel кнопки
  - Chain selection combo
  - Results preview table
```

#### T3 — User Dictionary + SM-2 SRS (~24ч)

Источник: MiMoV2Pro (его уникальный инсайт)

```
kadima/data/migrations/010_study.sql:
  - study_card (ud_entry_id, easiness_factor, interval, repetitions, next_due)

kadima/services/study_service.py (НОВЫЙ):
  - SM-2 algorithm: update_card(card, quality) → updated card
  - get_due_cards(project_id, limit=20) → List[StudyCard]
  - StudyCard = TermDTO + pronunciation + definition + examples

UI: вкладка "Study" в KB view или отдельный StudyView
  - Flashcard режим: ивритский термин → [показать] → перевод + произношение
  - Автоматическое расписание через SM-2
  - Интеграция с M15 TTS для произношения карточки
```

---

### ФАЗА 4: Security & Reliability (SEC)
**Для production-grade.**  
**Оценка: 1.5 недели | ~40ч**

#### SEC1 — Security Infrastructure (~24ч)

```
kadima/infra/security/crypto.py:
  - encrypt_credential(key, value) → bytes  # AES-256-GCM
  - decrypt_credential(key, encrypted) → str
  - Хранение в OS keyring (keyring пакет)

kadima/infra/security/validators.py:
  - sanitize_fts5_query(q) → str  # экранировать " * ( )
  - validate_import_path(path, allowed_base) → Path
  - sanitize_csv_value(v) → str  # защита от macro injection
  - sanitize_log_value(v) → str  # защита от log injection

kadima/infra/security/audit.py:
  - AuditLogger.log(action, entity, entity_id, user, details)
  - Таблица audit_log (из миграции 008)
  - Actions: CREATE/DELETE/EXPORT/IMPORT/TRANSLATE/RUN_PIPELINE
```

#### SEC2 — Reliability Patterns (~16ч)

Источник: MiMoV2Pro (circuit breaker — его инсайт)

```
kadima/infra/reliability/circuit_breaker.py:
  - CircuitBreaker(failure_threshold=5, recovery_timeout=60)
  - Для: Label Studio API, LLM API (Dicta-LM), MT providers
  - States: CLOSED → OPEN → HALF-OPEN

kadima/infra/reliability/rate_limiter.py:
  - RateLimiter(calls_per_minute=60)
  - Для: LLM API calls, Google Translate API

kadima/services/operations_center.py (по Qwen/V_book паттерну):
  - Singleton: максимум 1 тяжёлая операция одновременно
  - Операции: NLP pipeline run, batch translate, model load, import
  - OperationsCenterBusyError если слот занят
```

---

### ФАЗА 5: Document Import & Export (IO)
**Оценка: 2 недели | ~60ч**

#### IO1 — Multi-Format Import (~32ч)
```
kadima/infra/extractors/:
  - txt.py (существующий → перенести)
  - docx.py: python-docx, сохранить структуру параграфов
  - pdf.py: PyPDF2 primary + pytesseract fallback (OCR)
  - pptx.py: python-pptx, текст из слайдов
  - Base: SHA256 dedup (не импортировать дубликаты)
  - Watch folder: inotify/ReadDirectoryChangesW для auto-import

kadima/ui/import_wizard.py (НОВЫЙ QWizard):
  - Шаг 1: drag-n-drop + file picker (multi-select)
  - Шаг 2: выбор проекта + параметры NLP
  - Шаг 3: прогресс (staged, ≤500ms first paint)
  - Шаг 4: результаты (N импортировано, M дублей пропущено)
```

#### IO2 — Excel Export + Project Bundle (~28ч)
```
kadima/services/export_service.py — добавить Excel:
  - export_excel(project_id) с листами:
    Terms: he_term | pos | freq | rank | translation
    TM: he_term | translation | source | confidence
    Stats: corpus statistics
  - RTL formatting: ws.sheet_view.rightToLeft = True

kadima/services/project_exchange/ (НОВЫЙ по V_book):
  - exporter.py: Project → .kadimaproj ZIP
    ├── manifest.json (version, SHA256, schema_version)
    ├── project.sqlite (filtered DB copy)
    ├── raw/ (исходные документы)
    ├── kb/ (KB definitions + embeddings как JSON)
    └── annotations/ (Label Studio tasks + results)
  - importer.py: .kadimaproj → Project (с ID remapping)
  - Integrity check: SHA256 verification при импорте
```

---

### ФАЗА 6: Audio Management (AUD)
**Оценка: 2 недели | ~48ч**

#### AUD1 — AudioService + Cache (~28ч)
```
kadima/infra/audio/cache.py (НОВЫЙ):
  - Ключ: SHA256(term + provider + voice + lang)
  - Хранение: ~/.kadima/audio_cache/<sha256_prefix>/<sha256>.wav
  - get(key) → Optional[Path]
  - store(key, wav_path)
  - max_size_mb настройка (default: 500MB)

kadima/services/audio_service.py (НОВЫЙ singleton):
  - get_audio(term, provider, voice=None) → Path
  - Cache-first: проверяем кэш → если нет, генерируем через M15
  - batch_generate(terms, provider, progress_cb) → List[Path]
  - Playlist: AudioPlaylist(queue, current_index, repeat_mode)

kadima/ui/widgets/audio_player.py — улучшить:
  - Playlist support (следующий/предыдущий трек)
  - Keyboard shortcuts: Space=play/pause, →=next, ←=prev
  - Waveform preview (опционально)
```

#### AUD2 — ML Actions Column в Terms Table (~20ч)

Источник: Claude Code (уникальный ML workflow инсайт)

```
kadima/ui/results_view.py — добавить ML Actions:
  Для каждого термина в таблице:
  [🎵] → произношение через AudioService (M15 TTS)
  [📖] → дикритизация (M13) → показать в popup
  [🌐] → ML перевод (M14) с confidence badge
  [🏷] → NER тип (M17) — автоматически при загрузке
  [➕] → добавить в User Dictionary

Реализация:
  - MLActionsDelegate(QStyledItemDelegate)
  - Клик на иконку → QRunnable через QThreadPool
  - Results появляются инлайн без перезагрузки таблицы
```

---

### ФАЗА 7: T5 + API Completion (APP)
**По текущему ТЗ KADIMA.**  
**Оценка: 2 недели | ~48ч**

#### APP1 — T5 Modules (~24ч)
```
R-5.1: kadima/engine/keyphrase_extractor.py — M24 YAKE!
R-5.2: kadima/engine/grammar_corrector.py   — M23 Dicta-LM
R-5.3: kadima/engine/summarizer.py          — M19 mT5/Dicta-LM
Step 13: nlp_tools_view.py — Grammar/Keyphrase/Summarize
Step 14: llm_view.py       — chat + presets + context selector
Step 15: тесты UI T5
```

#### APP2 — API Stub Routers (~24ч)

Источник: D4 из CLAUDE.md — все три плана пропустили конкретику

```
kadima/api/routers/validation.py (5 endpoints):
  GET  /api/v1/validation/corpora              ← список gold corpus
  POST /api/v1/validation/run                  ← запустить валидацию
  GET  /api/v1/validation/results/{corpus_id}  ← результаты
  GET  /api/v1/validation/checks               ← все проверки
  GET  /api/v1/validation/report               ← экспорт отчёта

kadima/api/routers/kb.py (5 endpoints):
  GET  /api/v1/kb/terms            ← список KB terms
  POST /api/v1/kb/terms            ← добавить term
  GET  /api/v1/kb/search           ← text + embedding search
  GET  /api/v1/kb/similar/{term}   ← similar terms (cosine)
  GET  /api/v1/kb/clusters         ← term clusters

kadima/api/routers/annotation.py + llm.py — аналогично
```

---

### ФАЗА 8: UI Polish & Reference Corpus (UX)
**Оценка: 2 недели | ~40ч**

#### UX1 — First-Run Wizard + Command Palette (~24ч)
```
kadima/ui/first_run_wizard.py (QWizard):
  - Шаг 1: выбор языкового направления (HE→RU | HE→EN | HE→HE)
  - Шаг 2: NLP engine (rules / stanza / dictabert)
  - Шаг 3: пути к моделям (PHONIKUD, HF_HOME)
  - Шаг 4: первый проект

kadima/ui/command_palette.py (Ctrl+K):
  - Fuzzy search по командам
  - История последних команд
  - Команды: run, import, export, search [query], kb [term],
             project [name], settings, translate, validate
```

#### UX2 — Hebrew Wikipedia Reference Corpus (~16ч)
```
kadima/infra/reference/hewiki_connector.py:
  - attach_reference_db(path) → engine (read-only)
  - is_reference_available() → bool
  - get_term_global_freq(term) → int  # из heWiki 387k docs

DictProject.is_reference = True → использует внешнюю DB
  - Нормализует TF-IDF через общий корпус
  - Только READ операции (PERF-SCALE PATCH-A из V_book)
```

---

## ЧАСТЬ V: ДОРОЖНАЯ КАРТА И ПРИОРИТЕТЫ

### Порядок выполнения (критический путь)

```
P0 (DoD, CI, cold-audit framework)    ← 2 нед
   ↓
F1 (DB hardening, WAL, Write Gate)    ← параллельно можно
F2 (SettingsService)                  ← параллельно можно
F3 (FTS5)                             ← нужен для S1
F4 (Domain Layer)                     ← нужен для services/
F5 (Data Hierarchy migration)         ← нужен для Project concept
   ↓
S1 (Concordance/KWIC)                 ← нужна F3 + F4
T1 (Translation Memory)               ← нужна F5
APP2 (API stubs)                      ← независимо, можно параллельно
APP1 (T5: M23/M24/M19)               ← независимо
   ↓
T2 (Batch Translate V2)               ← нужен T1
T3 (User Dictionary + SM-2)           ← нужен T1
SEC1+SEC2 (Security + Reliability)    ← нужен F1 (DB), F3 (FTS5)
   ↓
IO1 (Multi-format Import)             ← нужен F5
IO2 (Excel + Project Bundle)          ← нужен T1
AUD1 (Audio Cache + Service)          ← независимо
AUD2 (ML Actions column)              ← нужен AUD1
   ↓
UX1 (Wizard, Command Palette)         ← нужен F2 (Settings)
UX2 (Reference Corpus)               ← независимо
```

### Итоговый таймлайн

| Фаза | Содержание | Оценка | Зависит от |
|------|-----------|--------|-----------|
| **P0** | DoD, CI, cold-audit методология | 2 нед | — |
| **F** | DB hardening, FTS5, Settings, Domain, Hierarchy | 3 нед | P0 |
| **S** | Concordance/KWIC, Coverage | 2 нед | F |
| **T** | TM, Batch MT, User Dict + SM-2 | 3 нед | F |
| **APP** | T5 modules, API stub routers | 2 нед | F |
| **SEC** | Security, Reliability, Operations Center | 1.5 нед | F |
| **IO** | Document import, Excel, Project Exchange | 2 нед | T |
| **AUD** | Audio cache, ML Actions column | 2 нед | T |
| **UX** | Wizard, Command palette, Reference corpus | 2 нед | F, AUD |
| **TOTAL** | | **~20 недель** | |

---

## ЧАСТЬ VI: МЕТРИКИ УСПЕХА v2.0

| Метрика | Сейчас | Цель v2.0 | Источник |
|---------|--------|-----------|----------|
| Архитектурные слои | 2 (engine+data) | 4 (domain+infra+services+ui) | Все три |
| DB миграции | 4 | 20+ | Все три |
| WAL PRAGMAs | Частично | Полный набор V_book | Claude+Qwen |
| Write Gate | Нет | ✅ RLock+телеметрия | Claude+Qwen |
| FTS5 tables | 0 | 3 (sentence, term, annotation) | Claude+MiMo |
| SettingsService | Нет | ✅ INI, geometry | Claude |
| KWIC Concordance | Нет | ✅ FTS5-powered, RTL | Все три |
| Translation Memory | Нет | ✅ Global+local, TMX | Все три |
| SM-2 SRS | Нет | ✅ Study cards из терминов | MiMo |
| Security hardening | Нет | ✅ AES-256, audit, injection | Все три |
| Circuit breaker | Нет | ✅ LS API, LLM API | MiMo |
| Excel export | Нет | ✅ RTL форматирование | Claude+Qwen |
| DOCX/PDF import | Нет | ✅ +OCR fallback | Все три |
| Project Exchange | Нет | ✅ .kadimaproj + KB/Annotation | Claude+MiMo |
| Audio cache | Нет | ✅ SHA256 content-addressed | Claude |
| ML Actions column | Нет | ✅ TTS/Diacritize/NER/Translate | Claude |
| Cold-audit waves | 0 | 5+ before каждого релиза | Qwen |
| API stub routers | 16 TODO | 0 TODO | Qwen |
| Modules M1-M25 | 22/25 | 25/25 (T5) | Все три |
| Тест/код ratio | ~0.3 | >0.6 | Qwen |
| CI Pipeline | Нет | ✅ GitHub Actions | Qwen |
| First-run wizard | Нет | ✅ | Claude |
| Command palette | Нет | ✅ Ctrl+K | Claude |
| Reference corpus | Нет | ✅ HebWiki | Claude |

---

## ЧАСТЬ VII: ЧТО НЕ ДЕЛАТЬ

```
1. Не трогать engine/ M1-M22 при архитектурном рефакторинге — они работают
2. Не удалять data/repositories.py — UI использует его; переходить постепенно через aliases
3. Не делать Big Bang refactoring — только patch series
4. Не заменять SA ORM — он уже есть; только расширять sa_models.py
5. Не копировать Stanza subprocess паттерн из V_book — KADIMA использует 
   иную архитектуру ML (lazy loading + CUDA); subprocess нужен только при MemoryError
6. Не игнорировать cold-audit — до релиза каждой фазы: измеряем first-paint
7. Не смешивать миграцию иерархии + новые фичи в одном коммите
8. Не вводить новые зависимости без проверки на RTX 3070 8GB VRAM budget
```

---

## ЧАСТЬ VIII: ПЕРВЫЕ ДЕЙСТВИЯ (Sprint 0)

```bash
# Немедленно — до начала фазы F:

1. Создать Tasks/DEFINITION_OF_DONE.md  (P0.1)
2. Создать .github/workflows/ci.yml     (P0.4)
3. kadima/cli.py → --self-check import  (P0.2)
4. Tasks/COLD_AUDIT_FRAMEWORK.md        (P0.3)
5. Зафиксировать baseline: время cold-open Dashboard, Pipeline, Results view

# Затем — начать фазу F с F1.1 (WAL PRAGMAs) — это не ломает ничего,
# только улучшает надёжность DB при конкурентном доступе
```

---

*Этот документ — мастер-план. При начале каждой фазы запускать repo-auditor → task-planner.*  
*Каждый патч: pytest → ruff → self-check → commit с conventional message.*
