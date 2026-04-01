# Стратегический план KADIMA v2.0
## Hebraic Dynamic Lexicon Engine — Production-Grade NLP Platform

> **Составлен:** 2026-04-01  
> **Основа анализа:** V_book (HDLE Premium) — 70k LOC, 284 тестов, 28+ миграций  
> **Цель:** KADIMA приобретает production-качество V_book, сохраняя превосходство по ML-модулям

---

## 1. Сравнительный анализ: V_book vs KADIMA

### 1.1 Что V_book делает лучше KADIMA

| Область | V_book | KADIMA (сейчас) | Критичность |
|---------|--------|-----------------|-------------|
| Архитектура | 3-слойная: Domain→Services→UI | Смешанная: нет явных слоёв | 🔴 Критично |
| DB: WAL PRAGMAs | busy_timeout=15s, temp_store=MEMORY, mmap=256MB, cache=64MB | Минимум | 🔴 Критично |
| DB: Write Gate | RLock-сериализатор записей с телеметрией | Нет | 🔴 Критично |
| DB: FTS5 | Full-text search по предложениям и терминам | Нет | 🔴 Критично |
| DB: Read/Write engines | Отдельные пулы для read/write | Один коннект | 🟠 Важно |
| Иерархия данных | Library→Project→Corpus→Document | Corpus→Document | 🔴 Критично |
| Settings persistence | QSettings INI, geometry, layout state | Нет (теряется при перезапуске) | 🔴 Критично |
| Миграции | 28+ SQL файлов | 4 файла | 🟠 Важно |
| Security | AES-256-GCM credentials, audit log, injection prevention | Нет | 🟠 Важно |
| KWIC Concordance | FTS5-powered, с context highlight | Нет | 🟠 Важно |
| Translation Memory | Cross-project TM, user dictionary | Нет | 🟡 Желательно |
| Batch MT с прогрессом | Google Translate free + Cloud API | Только через pipeline | 🟡 Желательно |
| Excel export | openpyxl XLSX | Нет (CSV/JSON/TBX/TMX) | 🟡 Желательно |
| Project Exchange | .hdleproj ZIP + SHA256 | Нет | 🟡 Желательно |
| Reference corpus | Hebrew Wikipedia 387k docs, внешний DB mount | Нет | 🟡 Желательно |
| Audio management | Content-addressed cache, playlist, 3 провайдера | TTS есть, UI базовый | 🟡 Желательно |
| Command palette | Ctrl+K с fuzzy search | Нет | 🟢 Nice-to-have |
| First-run wizard | Setup wizard при первом запуске | Нет | 🟢 Nice-to-have |
| Document import | TXT/DOCX/PDF/OCR/PPTX + drag-n-drop | TXT/CSV/CoNLL-U/JSON | 🟡 Желательно |
| Тесты | 284 файла, 1:1 ratio к коду | 822 функций (хорошо!) | ✅ KADIMA лучше |

### 1.2 Что KADIMA делает лучше V_book (уникальные преимущества)

| Область | KADIMA | V_book |
|---------|--------|--------|
| **ML-стек (M13-M25)** | TTS (XTTS/MMS), STT (Whisper), NER, Sentiment (heBERT), QA (AlephBERT), Diacritizer (phonikud-onnx), Translator (mBART), Morph Gen, Transliterator | Только Stanza (лемматизация+POS) |
| **Transformer backbone** | NeoDictaBERT, KadimaTransformer | Нет |
| **KB с эмбеддингами** | Cosine similarity, term clustering (k-means/HDBSCAN) | Нет |
| **Gold corpus validation** | 26 корпусов, check_engine | Нет |
| **Label Studio** | Active learning, NER training pipeline, sync | Нет |
| **REST API** | FastAPI с 10+ endpoints | Нет |
| **GPU acceleration** | CUDA 12.8, VRAM management | Нет |
| **CoNLL-U export** | Да | Нет |
| **NLP pipeline** | M1-M12 последовательный | Базовый (Stanza-based) |
| **Active Learning** | uncertainty sampling → LS export | Нет |

### 1.3 Главный вывод

> **V_book = production-grade lexicography tool (infrastructure + UX)**  
> **KADIMA = research NLP platform with powerful ML (content + AI)**  
> **KADIMA v2.0 = V_book infrastructure + KADIMA ML superpowers**

---

## 2. Стратегическая цель

**KADIMA v2.0: Hebraic Dynamic Lexicon Engine**  
Профессиональная desktop-платформа для ивритской лексикографии, терминографии и NLP исследований.

**Целевая аудитория:**
- Лингвисты и терминографы (как V_book)
- NLP исследователи (уникально для KADIMA)
- Переводчики (TM + ML translation)
- Редакторы и учёные (KB + annotation)

**Ключевое отличие от V_book:**
> V_book — это "умный словник". KADIMA v2.0 — это "говорящий, понимающий, обучаемый словник" с нейросетевым ядром.

---

## 3. Целевая архитектура (v2.0)

```
┌─────────────────────────────────────────────────────────┐
│                    KADIMA Desktop UI                     │
│  (PyQt6, 10+ views, command palette, wizards, settings)  │
└────────────────────┬────────────────────────────────────┘
                     │  signals only (never direct calls)
┌────────────────────▼────────────────────────────────────┐
│                  Services Layer (40+ services)           │
│  project_service | corpus_service | pipeline_service    │
│  tms_service | concordance_service | audio_service      │
│  export_service | annotation_service | kb_service       │
│  settings_service | security_service | batch_service    │
└──────────┬─────────────────────────┬────────────────────┘
           │                         │
┌──────────▼───────────┐  ┌──────────▼───────────────────┐
│   Domain Layer       │  │    ML Engine Layer           │
│  (pure logic, DTOs)  │  │  (M1-M25 processors)         │
│  scoring.py          │  │  model_manager.py            │
│  kwic.py             │  │  orchestrator.py             │
│  normalization/      │  │  HebPipe | Stanza | DictaBERT│
│  term_extraction/    │  │  XTTS | Whisper | heBERT     │
│  hebrew_utils.py     │  │  AlephBERT | YAKE | Dicta-LM │
└──────────┬───────────┘  └──────────────────────────────┘
           │
┌──────────▼───────────────────────────────────────────────┐
│                  Infrastructure Layer                     │
│  db.py (DatabaseManager, WAL, FTS5, Write Gate)          │
│  sa_models.py (Library→Project→Corpus→Document)          │
│  repositories/ (typed, SA-based, parameterized)          │
│  settings.py (QSettings INI, cross-platform)             │
│  security/ (AES-256, keyring, audit log, injection prev) │
│  migrations/ (005-028: new tables)                       │
│  providers/ (NLP engines, TTS, MT — pluggable)          │
└──────────────────────────────────────────────────────────┘
           │
┌──────────▼──────────────────────────────────────┐
│           FastAPI REST API (optional)            │
│  /api/v1/corpora | /pipeline | /generative       │
│  /api/v1/kb | /annotation | /validation          │
└─────────────────────────────────────────────────┘
```

**Ключевые архитектурные принципы (от V_book):**
1. **Чистые слои**: UI не знает о DB; Domain не знает о UI
2. **Singleton services**: `ProjectService.get_instance()`, `SettingsService.get_instance()`
3. **Write Gate**: все DB-записи через `serialized_db_write(operation)`
4. **WAL PRAGMAs**: `busy_timeout=15000`, `temp_store=MEMORY`, `mmap=256MB`
5. **Workers emit signals**: QRunnable → сигналы → UI (никогда напрямую)
6. **FTS5 triggers**: авто-индексация при INSERT/DELETE документов

---

## 4. Иерархия данных v2.0

```
Library (1 default)
  └── Project (= нынешний Corpus + настройки)
        ├── src_lang / tgt_lang
        ├── nlp_engine (stanza | hebpipe | dictabert)
        ├── mwe_min_freq / mwe_min_pmi / mwe_min_tscore
        ├── is_reference (для Hebrew Wikipedia)
        └── SourceCorpus (= группа документов)
              └── SourceDocument
                    └── DocumentSentence (FTS5-indexed)
                          └── Token → Lemma → NgramCandidate → Term
```

**Новые таблицы (миграции 005–020):**

| # | Таблица | Назначение |
|---|---------|-----------|
| 005 | `library` | Верхний уровень иерархии |
| 005 | `dict_project` | Проект с NLP-настройками |
| 005 | `source_corpus` | Группа документов |
| 006 | `sentence_fts` | FTS5 virtual table |
| 006 | `term_fts` | FTS5 для терминов |
| 007 | `tm_entry` | Translation Memory |
| 007 | `user_dictionary` | Личный словарь |
| 008 | `audit_log` | Журнал действий |
| 009 | `credentials` | Зашифрованные ключи API |
| 010 | `audio_cache` | Content-addressed аудио |
| 011 | `kwic_index` | KWIC статистика |
| 012 | `term_curation_state` | Статус ревью терминов |
| 013 | `project_export_log` | История экспортов |

---

## 5. Фазовый план реализации

### Фаза 1: Foundation Layer (Фундамент)
**Приоритет: 🔴 Блокирующий | Оценка: 3–4 недели**

Без этого всё остальное строится на песке. Делать в первую очередь.

#### PATCH-F1: DB Layer Hardening

**R-F1.1 — WAL PRAGMAs + Write Gate + Dual Engine**
```
Файлы:
  kadima/data/db.py              ← добавить PRAGMAs + @event.listens_for
  kadima/data/write_gate.py      ← НОВЫЙ файл (скопировать паттерн V_book)
  kadima/data/db_retry.py        ← НОВЫЙ: retry декоратор для "database is locked"

Изменения db.py:
  - journal_mode=WAL (уже есть, проверить)
  - busy_timeout=15000
  - temp_store=MEMORY
  - mmap_size=268435456
  - cache_size=-65536
  - synchronous=NORMAL
  - Отдельный read_engine (pool_size=4)

Изменения repositories.py:
  - Все UPDATE/INSERT/DELETE обернуть в serialized_db_write()
  - Chunked commits для bulk операций (commit каждые 500 строк)
```

**R-F1.2 — FTS5 Full-Text Search**
```
Файлы:
  kadima/data/migrations/005_fts5.sql   ← НОВАЯ миграция
  kadima/data/fts_manager.py            ← НОВЫЙ (FTS5 DDL + triggers)
  kadima/data/repositories.py           ← добавить fts_search()

Таблицы:
  sentence_fts USING fts5(text, doc_id, sentence_id, tokenize='unicode61 remove_diacritics 1')
  term_fts USING fts5(he_term, ru_translation, notes, project_id UNINDEXED)

Триггеры:
  trg_sentence_ai / trg_sentence_au / trg_sentence_ad
```

**R-F1.3 — SettingsService**
```
Файлы:
  kadima/infra/settings.py    ← НОВЫЙ singleton QSettings wrapper
  kadima/ui/main_window.py    ← сохранение geometry, last_view, profile

Сохраняет:
  - Window geometry / splitter state
  - Last active view index
  - Profile (balanced/precise/recall)
  - Last opened corpus
  - Table column widths per view
```

---

#### PATCH-F2: Data Hierarchy (Иерархия данных)

**R-F2.1 — Library → Project → Corpus (Миграция схемы)**
```
Файлы:
  kadima/data/migrations/006_project_hierarchy.sql  ← НОВАЯ
  kadima/data/sa_models.py   ← добавить Library, DictProject, SourceCorpus, SourceDocument
  kadima/data/repositories.py ← ProjectRepository, LibraryRepository

Стратегия миграции:
  - Создать дефолтную Library "Default"
  - Каждый существующий corpus → DictProject + SourceCorpus (1:1)
  - Существующие documents → SourceDocument
  - Backward compatible: старые API продолжают работать
```

**R-F2.2 — ProjectService**
```
Файлы:
  kadima/services/project_service.py  ← НОВЫЙ singleton

Методы:
  create_project(name, src_lang, tgt_lang, nlp_engine)
  open_project(project_id) → ProjectContext
  list_projects() → List[ProjectDTO]
  delete_project(project_id)
  get_project_stats(project_id) → ProjectStats
  update_project_settings(project_id, **kwargs)
```

---

#### PATCH-F3: Clean Architecture Refactoring

**R-F3.1 — Domain Layer**
```
Создать kadima/domain/:
  kadima/domain/dto.py          ← все DataTransferObjects
  kadima/domain/exceptions.py   ← кастомные исключения
  kadima/domain/hebrew_utils.py ← утилиты для иврита (никуд, ударения, статья)
  kadima/domain/scoring.py      ← PMI/T-score (перенести из engine/)
  kadima/domain/kwic.py         ← KWIC структуры
  kadima/domain/normalization/  ← нормализация текста
```

**R-F3.2 — Services Layer**
```
Создать kadima/services/:
  kadima/services/corpus_service.py    ← CRUD для корпусов (из repositories)
  kadima/services/document_service.py  ← импорт, парсинг документов
  kadima/services/pipeline_service.py  ← перенести из pipeline/orchestrator
  kadima/services/export_service.py    ← перенести из corpus/exporter
  kadima/services/ingest_service.py    ← новый: импорт DOCX/PDF
  kadima/services/settings_service.py  ← обёртка QSettings
```

**R-F3.3 — Remove circular imports**
```
Текущие проблемы:
  - ui/ импортирует из data/ напрямую
  - engine/ импортирует из pipeline/
  - validation/ не изолирован от ui/

Правило: ui/ → services/ → domain/ + data/
Никогда: data/ → ui/
```

---

### Фаза 2: Search & Discovery
**Приоритет: 🔴 Критично для UX | Оценка: 2–3 недели**

#### PATCH-S1: KWIC Concordance View

```
Файлы:
  kadima/domain/kwic.py                  ← format_kwic(), KWICResult DTO
  kadima/services/concordance_service.py ← FTS5 поиск + нормализация запроса
  kadima/ui/concordance_view.py          ← НОВЫЙ view (замена текущего search в kb_view)

Функционал:
  - Поиск по всем документам корпуса (FTS5)
  - Нормализация запроса на иврите (with/without ה prefix)
  - KWIC отображение: [левый контекст | ключевое слово | правый контекст]
  - Клик на результат → открывает документ в нужном предложении
  - RTL-safe отображение

UI Spec (по V_book):
  ┌─────────────────────────────────┐
  │ [🔍 Search input RTL]  [Search] │
  ├─────────────────────────────────┤
  │ Left context | Match | Right    │
  │ ...          |  שגיאה  | ...    │
  │ Source: doc_01.txt, sentence 3  │
  └─────────────────────────────────┘
```

#### PATCH-S2: Advanced Term Search + Coverage

```
Файлы:
  kadima/services/coverage_service.py  ← НОВЫЙ
  kadima/ui/results_view.py            ← добавить coverage panel

Метрики покрытия (по V_book):
  - Термины найдены / всего в корпусе (%)
  - Документы с хотя бы 1 термином
  - Топ-N терминов по частоте
  - Hapax legomena count
```

---

### Фаза 3: Translation Memory & Dictionary
**Приоритет: 🟠 Важно | Оценка: 2–3 недели**

#### PATCH-T1: Translation Memory (TM)

```
Файлы:
  kadima/data/migrations/007_tm.sql          ← tm_entry, user_dictionary
  kadima/services/tm_service.py              ← НОВЫЙ
  kadima/services/batch_translate_service.py ← НОВЫЙ (V_book паттерн)
  kadima/ui/tm_view.py                       ← НОВЫЙ view (или вкладка в Results)

Схема (tm_entry):
  id, project_id, he_term, tgt_lang, translation,
  source (user|mt|import), confidence, created_at, updated_at

Функционал:
  - Сохранение переводов пользователя
  - Batch translation через Translator (M14 mBART/OPUS)
  - Экспорт TM → TMX формат (уже есть в exporter.py)
  - Импорт TMX из других проектов
  - Cross-project TM sharing (global TM)
```

#### PATCH-T2: Batch Translation Worker V2

```
Файлы:
  kadima/services/batch_translate_engine_v2.py  ← НОВЫЙ (по V_book паттерну)
  kadima/ui/dialogs/batch_translate_dialog.py   ← НОВЫЙ диалог с прогрессом

Особенности (от V_book):
  - Chunked processing (50 терминов за раз)
  - Real-time progress bar
  - Pause/Resume поддержка
  - Force mode: только M14 (ML)
  - Chain mode: user dict → TM → MT fallback
  - Отмена с rollback (uncommitted транзакция)
```

---

### Фаза 4: Document Import & Export
**Приоритет: 🟠 Важно | Оценка: 1–2 недели**

#### PATCH-E1: Excel Export + Import Wizard

```
Файлы:
  kadima/services/export_service.py     ← добавить Excel формат (openpyxl)
  kadima/ui/import_wizard.py            ← НОВЫЙ wizard (по V_book паттерну)
  kadima/infra/extractors/              ← НОВАЯ директория
    kadima/infra/extractors/txt.py
    kadima/infra/extractors/docx.py     ← python-docx
    kadima/infra/extractors/pdf.py      ← PyPDF2 + pytesseract fallback
    kadima/infra/extractors/pptx.py     ← python-pptx

Excel export (openpyxl):
  - Лист "Terms": term, lemma, freq, pos, translations
  - Лист "TM": he_term, translation, source, confidence
  - Лист "Stats": corpus statistics
  - Форматирование: RTL направление, иврит шрифт

Import wizard (QWizard):
  - Шаг 1: выбор файлов (drag-n-drop + dialog)
  - Шаг 2: параметры обработки (язык, NLP engine)
  - Шаг 3: прогресс + результаты
```

#### PATCH-E2: Project Exchange (.kadimaproj)

```
Файлы:
  kadima/services/project_exchange/  ← НОВАЯ директория
    exporter.py   ← Project → ZIP bundle
    importer.py   ← ZIP bundle → Project (с ID remapping)
    manifest.py   ← ManifestSchema + SHA256 verification

Bundle содержит:
  - manifest.json (version, created_at, schema_version, SHA256)
  - project.sqlite (filtered копия DB)
  - raw/ (исходные документы)
  - models/ (gold corpus checks если есть)
```

---

### Фаза 5: Security & Audit
**Приоритет: 🟠 Важно для production | Оценка: 1–2 недели**

#### PATCH-SEC: Security Hardening

```
Файлы:
  kadima/infra/security/              ← НОВАЯ директория
    kadima/infra/security/crypto.py    ← AES-256-GCM для API ключей (keyring)
    kadima/infra/security/validators.py ← sanitize_fts5_query, validate_path
    kadima/infra/security/audit.py     ← AuditLogger (audit_log table)
  kadima/data/migrations/008_audit.sql ← audit_log + credentials tables

Конкретные уязвимости KADIMA сейчас:
  1. FTS5 query injection (после добавления FTS5)
  2. Path traversal в импорте файлов
  3. API ключи (LS_API_KEY, HF_TOKEN) хранятся в .env в открытом виде
  4. Нет аудита действий пользователя

Патч:
  - sanitize_fts5_query(): экранировать " + * ( ) в FTS5 запросах
  - validate_import_path(): проверить что путь внутри allowed dir
  - API ключи → OS keyring через keyring пакет
  - audit_log: INSERT для каждого Create/Delete/Export
```

---

### Фаза 6: Audio & Reference Corpus
**Приоритет: 🟡 Желательно | Оценка: 2–3 недели**

#### PATCH-A1: Audio Management Service

```
Файлы:
  kadima/services/audio_service.py         ← НОВЫЙ singleton
  kadima/infra/audio/                      ← НОВАЯ директория
    base_provider.py   ← AudioProvider ABC
    providers/
      mms.py           ← уже есть (M15 MMS-TTS), обернуть
      xtts.py          ← уже есть (M15 XTTS), обернуть
      mock.py          ← для тестов
  kadima/services/audio_cache_service.py   ← content-addressed cache (SHA256 ключ)
  kadima/ui/widgets/audio_player.py        ← улучшить текущий AudioPlayer

AudioService:
  - get_audio(term, provider, voice) → Path(WAV)
  - cache-first: SHA256(term+provider+voice) → cached WAV
  - batch_generate(terms, provider) → прогресс-диалог
  - playlist: очередь воспроизведения
```

#### PATCH-A2: Hebrew Wikipedia Reference Corpus

```
Файлы:
  kadima/infra/reference/          ← НОВАЯ директория
    hewiki_connector.py   ← подключение внешней DB
    hewiki_search.py      ← поиск в 387k документах

Концепция (от V_book PERF-SCALE PATCH-A):
  - is_reference=True для проекта → открывает внешнюю DB read-only
  - Используется для подсчёта term frequency в общем корпусе
  - Нормализует TF-IDF значения терминов
  - Отдельный read engine (не конкурирует с основным)

Требования:
  - Файл heWiki.db (~17 GB) на внешнем диске M:\
  - Схема совместима с SourceDocument модели KADIMA
  - Read-only mount (нет записи, только SELECT)
```

---

### Фаза 7: ML Integration in V_book-Style UI
**Приоритет: 🟡 Высокая ценность | Оценка: 2–3 недели**

Это уникальный вклад KADIMA — V_book не имеет этого вообще.

#### PATCH-ML1: ML-Enhanced Term Workflow

```
Интеграция ML в стандартный рабочий процесс:

1. Terms Table → ML Actions column:
   - [🎵] Произношение (M15 TTS)
   - [📖] Дикритизация (M13)
   - [🌐] ML-перевод (M14 с confidence score)
   - [🏷] NER тип (M17 — автоматически)
   - [❤] Sentiment context (M18)

2. Sentence view → ML Panel:
   - Автоматическая дикритизация предложения
   - QA extraction при выборе вопроса
   - Суммаризация абзаца (M19 когда будет)

3. KWIC → Audio column:
   - Каждый результат concordance → [▶] для воспроизведения контекста
```

#### PATCH-ML2: NLP Engine Pluggable Architecture

```
По V_book паттерну (infra/nlp_engines/):

kadima/infra/nlp_engines/
  base_engine.py      ← NLPEngine ABC
  providers/
    rules_engine.py   ← текущий HebPipe (rule-based)
    stanza_engine.py  ← Stanza (как в V_book)
    dictabert.py      ← NeoDictaBERT (наш уникальный)
    mock_engine.py    ← для тестов

DictProject.nlp_engine → str (rules | stanza | dictabert)
На лету переключается в Project Settings
```

---

### Фаза 8: UI Polish & Command Palette
**Приоритет: 🟢 UX quality | Оценка: 1–2 недели**

#### PATCH-UX1: Settings Persistence + Wizards

```
kadima/ui/first_run_wizard.py  ← НОВЫЙ QWizard
  - Шаг 1: выбор языкового направления (HE→RU | HE→EN | ...)
  - Шаг 2: выбор NLP engine (rules / stanza / dictabert)
  - Шаг 3: пути к моделям (PHONIKUD, HF_HOME)
  - Шаг 4: создание первого проекта

kadima/ui/project_settings_dialog.py  ← НОВЫЙ
  - NLP engine / threshold settings
  - Пути к моделям
  - Audio providers
  - API keys (через SecurityService)
```

#### PATCH-UX2: Command Palette (Ctrl+K)

```
kadima/ui/command_palette.py  ← НОВЫЙ QDialog

Команды:
  > "run pipeline" → F5
  > "import corpus" → Ctrl+I
  > "export terms" → Ctrl+E
  > "search [query]" → открыть Concordance с запросом
  > "kb [term]" → открыть KB для термина
  > "project [name]" → открыть проект
  > "settings" → открыть настройки

Архитектура:
  - QDialog с QLineEdit + QListView
  - Fuzzy matching по названиям команд
  - История последних команд
```

---

### Фаза 9: T5 + API (параллельно с основными фазами)
**Приоритет: 🟡 По ТЗ | Оценка: 2–3 недели**

Завершение текущего ТЗ по KADIMA (независимо от архитектурных изменений):

```
R-5.1 keyphrase_extractor.py — M24 YAKE! backend
R-5.2 grammar_corrector.py   — M23 Dicta-LM
R-5.3 summarizer.py          — M19 mT5/Dicta-LM
Step 13: nlp_tools_view.py    — Grammar/Keyphrase/Summarize
Step 14: llm_view.py          — chat + presets
Step 15: tests/ui/            — smoke tests T5

API стабы заполнить:
  validation.py   ← 5 endpoints
  annotation.py   ← 4 endpoints
  kb.py           ← 5 endpoints
  llm.py          ← 5 endpoints
```

---

## 6. Порядок реализации (Priority Matrix)

```
Немедленно (до любого нового функционала):
  ├── R-F1.1 WAL PRAGMAs + Write Gate  [риск data loss]
  ├── R-F1.3 SettingsService           [UX критично]
  └── R-F3.1 Domain Layer DTOs         [долг архитектуры]

Квартал 1 (Апрель–Май 2026):
  ├── R-F1.2 FTS5                      [блокирует Concordance]
  ├── R-F2.1 Hierarchy migration       [блокирует Projects UI]
  ├── R-F2.2 ProjectService            [блокирует Projects UI]
  ├── PATCH-S1 Concordance/KWIC        [высокая ценность]
  ├── PATCH-T5 T5 modules (R-5.1–5.3) [по ТЗ]
  └── PATCH-UX1 First-run wizard       [onboarding]

Квартал 2 (Июнь–Июль 2026):
  ├── PATCH-T1 Translation Memory      [ключевая фича]
  ├── PATCH-T2 Batch translate V2      [ключевая фича]
  ├── PATCH-E1 Excel export + DOCX/PDF [import quality]
  ├── PATCH-SEC Security hardening     [production ready]
  └── PATCH-ML1 ML в Terms workflow    [уникальность]

Квартал 3 (Август–Сентябрь 2026):
  ├── PATCH-E2 Project Exchange        [collaboration]
  ├── PATCH-A1 Audio management        [TTS UX]
  ├── PATCH-ML2 NLP Engine pluggable   [architecture]
  ├── PATCH-A2 Hebrew Wikipedia        [reference scale]
  └── PATCH-UX2 Command palette        [power users]
```

---

## 7. Риски и митигация

| Риск | Вероятность | Влияние | Митигация |
|------|-------------|---------|-----------|
| Миграция иерархии сломает текущие 4 миграции | Средняя | Высокое | Создать migration 006 как additive — не удалять старые таблицы, добавлять новые + compatibility views |
| Clean Architecture refactoring = большой diff | Высокая | Среднее | Делать по слоям: сначала только domain/, потом services/, потом ui/ — каждый шаг отдельный коммит |
| FTS5 triggers дублируют данные → inconsistency | Средняя | Высокое | FTS Manager с self-healing (re-create если inconsistent) + тест: INSERT doc → verify FTS has entry |
| Write Gate дедлоки между потоками | Низкая | Высокое | RLock (re-entrant) + timeout в QThread.wait() + busy_timeout в SQLite |
| Settings file corruption (QSettings INI) | Низкая | Среднее | Try-except в get_*, fallback to defaults, QSettings.sync() при exit |
| Batch translate API rate limits | Высокая | Низкое | Chunked (50/batch), exponential backoff, Chain mode (ML fallback) |
| ML модели не влезают в VRAM при новом workflow | Средняя | Среднее | ModelManager LRU eviction + VRAM budget check перед load |
| Стаз "database is locked" в UI | Средняя | Высокое | Write Gate + busy_timeout=15000 + DB retry decorator |

---

## 8. Метрики успеха v2.0

| Метрика | Сейчас | Цель v2.0 |
|---------|--------|-----------|
| Модули (M1–M25) | 22/25 реализованы | 25/25 |
| API endpoints | 10/26 | 26/26 |
| Тесты | 822 функций | >1000 |
| Тест/код ratio | ~0.3 | >0.8 (как V_book) |
| Миграции DB | 4 | 20+ |
| Settings persistence | Нет | ✅ |
| FTS5 search | Нет | ✅ |
| KWIC Concordance | Нет | ✅ |
| Translation Memory | Нет | ✅ |
| Excel export | Нет | ✅ |
| DOCX/PDF import | Нет | ✅ |
| Security hardening | Нет | ✅ AES-256 + audit |
| Write Gate | Нет | ✅ |
| WAL PRAGMAs | Частично | ✅ Полный набор |
| Reference corpus | Нет | ✅ HebWiki |

---

## 9. Что НЕ делать

1. **Не копировать V_book** — это интеграция паттернов, не clone
2. **Не делать Big Bang refactoring** — только patch series, каждый независимо buildable
3. **Не трогать ML движки (M1-M25)** при архитектурном рефакторинге — они работают
4. **Не менять pipeline/orchestrator.py** до завершения Domain/Services слоёв
5. **Не удалять legacy data/repositories.py** сразу — UI использует его, переходить постепенно
6. **Не добавлять V_book зависимости** которые уже покрыты нашими ML модулями
   (Stanza лематизация → заменить на NeoDictaBERT; Google Translate free → M14 mBART)

---

## 10. Первый шаг (Next Action)

Перед началом любой реализации — запустить `repo-auditor` агента на изменённых файлах.

**Немедленные действия:**

```bash
# 1. Создать ветку для архитектурных изменений
git checkout -b feat/v2-foundation

# 2. Первый патч: WAL PRAGMAs + Write Gate (не ломает ничего, только улучшает надёжность)
# Файлы: kadima/data/db.py, новый kadima/data/write_gate.py

# 3. Второй патч: SettingsService (независим от всего остального)
# Файлы: новый kadima/infra/settings.py + kadima/ui/main_window.py

# 4. Третий патч: Domain layer DTOs (только добавление, ничего не ломает)
# Файлы: новая директория kadima/domain/

# Каждый патч: pytest tests/ → ruff check → commit
```

---

*Документ предназначен для ориентации при разработке. При начале каждой фазы — запускать `repo-auditor` + `task-planner` агентов для детального patch series.*
