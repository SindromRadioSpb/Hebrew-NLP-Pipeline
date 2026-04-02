# Roadmap — KADIMA
# Источник: doc/KADIMA_MASTER_PLAN_v2.md (синтез Claude Code + Qwen3.6Plus + MiMoV2Pro)
# Утверждён: 2026-04-01

---

## Критический путь

```
P0 ✅ → T5 UI ✅ → T6 D4 ✅ → R-6.1 Docker ← СЕЙЧАС
   ↓
Фаза F (инфраструктура)  ← блокирует S, SEC
   ↓
Фаза S (сервисы) + APP параллельно
   ↓
T (TM + User Dict) + SEC (безопасность) параллельно
   ↓
IO (импорт/экспорт) + AUD (audio cache) параллельно
   ↓
UX (polish: wizard, command palette, reference corpus)
```

---

## Завершённые фазы

| Фаза | Что закрыто | Доказательство |
|------|-------------|----------------|
| Phase 0 | Стабилизация B1-B4, CI, Docker | docker-compose.yml, .github/workflows/ |
| Phase 1 | M22, M21, M13, M17, M14; generative router 5ep | engine/*.py, api/routers/generative.py |
| T1 | KadimaTransformer, NeoDictaBERT backbone, spaCy pipeline builder | tests/engine/test_transformer_component.py |
| T2 | M5 embeddings, M17 NER neodictabert, NER training, KB embeddings, TermClusterer, SA ORM, async SA | tests/kb/, tests/test_sa_data_layer.py |
| T3 | Desktop UI: MainWindow + 6 views + 9 widgets + dark QSS | tests/ui/test_main_window.py |
| pre-T4 | D8 cross-view wiring, D9 engine stubs, D10 T4 widgets | ui/*.py |
| P0 | DoD checklist, Cold-Audit Framework, self-check CLI, CI gate | Tasks/DEFINITION_OF_DONE.md, .github/ |
| T4 | M15 TTS, M16 STT, M18 Sentiment, M20 QA; GenerativeView + AnnotationView | tests/ui/test_generative.py |
| T5 ML | M24 Keyphrase, M23 Grammar, M19 Summarizer; API endpoints | engine/*.py |
| T5 UI | NLPToolsView, LLMView, ChatWidget, 60 smoke tests | tests/ui/test_nlp_tools.py |
| T6 D4 | 19 API endpoints: validation 5ep, kb 5ep, annotation 4ep, llm 5ep; 80 тестов | api/routers/*.py |
| — | 4 missing generative endpoints: sentiment, qa, tts, stt | api/routers/generative.py |

---

## Текущий следующий шаг: R-6.1 Docker Production

**Цель**: `docker-compose.prod.yml` — production-ready конфигурация

```
Что сделать:
  - docker-compose.prod.yml с resource limits, GPU reservation, non-root user
  - Healthchecks для всех сервисов (api, label-studio, llama-cpp)
  - .env.example актуализировать
  - Без bind mounts source code (только named volumes)
  - PRAGMA WAL + busy_timeout в connection string

Файлы: docker-compose.prod.yml (новый), docker-compose.yml (ref), .env.example
Оценка: 3-5 часов
```

---

## Фаза F: Инфраструктурный Фундамент
**Блокирует Фазы S, T, SEC. Оценка: 3 недели / ~80ч**

### F1.1 — DB Layer Hardening (~16ч)
```
kadima/infra/db.py         — WAL PRAGMAs полный набор + dual read/write engines
kadima/infra/write_gate.py — RLock сериализатор, телеметрия wait_ms/hold_ms
kadima/infra/db_retry.py   — @db_retry(max_attempts=3) для OperationalError "locked"
```

### F1.2 — SettingsService (~8ч)
```
kadima/infra/settings.py   — QSettings INI singleton ("KADIMA"/"KADIMA")
  save_geometry(widget) / restore_geometry(widget)
  save_table_state(table, key)
```

### F1.3 — FTS5 Manager (~16ч)
```
kadima/data/migrations/005_fts5.sql:
  sentence_fts USING fts5(text, doc_id, sentence_id, tokenize='unicode61 remove_diacritics 1')
  term_fts USING fts5(he_term, translation, project_id UNINDEXED)
  annotation_fts USING fts5(text, task_id UNINDEXED)
  Триггеры: trg_sentence_ai/au/ad, trg_term_ai/au/ad

kadima/infra/fts_manager.py — ensure_fts_tables(), repair_fts_parity(), reindex_project()
```

### F1.4 — Domain Layer (~20ч)
```
kadima/domain/dto.py         — ProjectDTO, TermDTO, KWICResult, AudioAsset, StudyCard
kadima/domain/hebrew_utils.py — strip_nikud(), normalize_whitespace(), get_article_variants()
kadima/domain/kwic.py         — format_kwic(), KWICResult dataclass
kadima/domain/scoring.py      — pmi(), t_score(), llr(), dice() (перенести из engine/)
```

### F1.5 — Data Hierarchy Migration (~20ч)
```
kadima/data/migrations/006_project_hierarchy.sql:
  library, dict_project (library_id, src_lang, tgt_lang, nlp_engine, is_reference),
  source_corpus (project_id, watch_folder_path)
  -- backward compat: INSERT INTO library DEFAULT; INSERT INTO dict_project FROM corpora

kadima/infra/sa_models.py    — добавить Library, DictProject, SourceCorpus
kadima/services/project_service.py — CRUD проектов, singleton
```

---

## Фаза S: Search & KWIC Concordance
**Нужна Фаза F. Оценка: 2 недели / ~48ч**

```
kadima/services/concordance_service.py — FTS5-powered KWIC с Hebrew normalization
  search(query, project_id) → List[KWICResult]
  sanitize_fts5_query(query) — безопасность перед FTS5

kadima/ui/concordance_view.py — левый контекст | ключевое слово | правый | источник
  Кнопка [▶] на каждой строке → audio из AudioService
  Клик → открыть документ на нужном предложении
  Фильтры: по проекту, корпусу, POS

kadima/services/coverage_service.py — term coverage %, hapax count, freq top-N
  + Coverage Panel в results_view.py
```

---

## Фаза T: Translation Memory & User Dictionary
**Нужна Фаза F. Оценка: 3 недели / ~80ч**

### T1 — Translation Memory (~32ч)
```
kadima/data/migrations/007_tm.sql:
  tm_entry (project_id, he_term, tgt_lang, translation, source, confidence)
  tm_global (he_term, tgt_lang, translation, usage_count)
  user_dictionary (project_id, he_term, translation, notes)

kadima/services/tm_service.py:
  lookup(term, tgt_lang) → Optional[str]
  export_tmx(project_id) → str
  import_tmx(file_path, project_id) → int
```

### T2 — Batch Translation Worker V2 (~24ч)
```
kadima/services/batch_translate_service.py — chunked (50/chunk), pause/resume,
  chain: TM → M14 ML → Google fallback
kadima/ui/dialogs/batch_translate_dialog.py — QProgressBar + Pause/Resume/Cancel
```

### T3 — User Dictionary + SM-2 SRS (~24ч) [инсайт MiMoV2Pro]
```
kadima/data/migrations/010_study.sql — study_card (easiness_factor, interval, next_due)
kadima/services/study_service.py — SM-2 algorithm, get_due_cards(project_id)
UI: flashcard режим + M15 TTS для произношения карточки
```

---

## Фаза SEC: Security & Reliability
**Нужна Фаза F. Оценка: 1.5 недели / ~40ч**

```
kadima/infra/security/crypto.py      — AES-256-GCM для API ключей, OS keyring
kadima/infra/security/validators.py  — sanitize_fts5_query(), validate_import_path(),
                                        sanitize_csv_value(), sanitize_log_value()
kadima/infra/security/audit.py       — AuditLogger → таблица audit_log (migration 008)
  Actions: CREATE/DELETE/EXPORT/IMPORT/TRANSLATE/RUN_PIPELINE

kadima/infra/reliability/circuit_breaker.py — для LS API, LLM API, MT providers
  CircuitBreaker(failure_threshold=5, recovery_timeout=60s)
  States: CLOSED → OPEN → HALF-OPEN

kadima/infra/reliability/rate_limiter.py — RateLimiter(calls_per_minute=60)
kadima/services/operations_center.py — singleton: max 1 тяжёлая операция одновременно
```

---

## Фаза IO: Document Import & Export
**Нужна T. Оценка: 2 недели / ~60ч**

```
kadima/infra/extractors/: txt.py, docx.py, pdf.py (PyPDF2+OCR), pptx.py
  SHA256 dedup (не импортировать дубликаты)
  Watch folder: inotify/ReadDirectoryChangesW

kadima/ui/import_wizard.py — QWizard 4 шага: drag-n-drop → проект → прогресс → результат

kadima/services/export_service.py — добавить Excel:
  Листы: Terms, TM, Stats | RTL: ws.sheet_view.rightToLeft = True

kadima/services/project_exchange/ — .kadimaproj ZIP bundle:
  manifest.json + project.sqlite + raw/ + kb/ + annotations/
  SHA256 integrity check при импорте
```

---

## Фаза AUD: Audio Management
**Нужна T. Оценка: 2 недели / ~48ч**

```
kadima/infra/audio/cache.py — SHA256(term+provider+voice) как ключ
  Хранение: ~/.kadima/audio_cache/, max_size_mb=500

kadima/services/audio_service.py — cache-first, batch_generate(), AudioPlaylist

kadima/ui/widgets/audio_player.py — улучшить: playlist, Space/→/← shortcuts

kadima/ui/results_view.py — ML Actions колонка:
  [🎵] TTS, [📖] Diacritize, [🌐] Translate, [🏷] NER, [➕] User Dict
  MLActionsDelegate(QStyledItemDelegate) + QRunnable per action
```

---

## Фаза UX: Polish
**Нужна F, AUD. Оценка: 2 недели / ~40ч**

```
kadima/ui/first_run_wizard.py — QWizard: язык → NLP engine → пути к моделям → первый проект

kadima/ui/command_palette.py — Ctrl+K: fuzzy search команд
  команды: run, import, export, search [q], kb [term], project [name], settings

kadima/infra/reference/hewiki_connector.py — Hebrew Wikipedia как reference corpus
  DictProject.is_reference=True → нормализует TF-IDF через 387k docs
```

---

## Миграции: план 005-017

| Миграция | Таблицы | Фаза | Приоритет |
|----------|---------|------|-----------|
| 005_fts5.sql | sentence_fts, term_fts, annotation_fts (FTS5) | F | 🔴 |
| 006_project_hierarchy.sql | library, dict_project, source_corpus | F | 🔴 |
| 007_tm.sql | tm_entry, tm_global, user_dictionary | T | 🟠 |
| 008_audit.sql | audit_log, credentials | SEC | 🟠 |
| 009_audio.sql | audio_asset (content-addressed cache) | AUD | 🟡 |
| 010_study.sql | study_progress (SM-2 SRS) | T | 🟡 |
| 011_nlp_cache.sql | sentence_nlp_snapshot | S | 🟡 |
| 012_curation.sql | term_curation_state | AUD | 🟡 |

---

## Итоговый таймлайн

| Фаза | Оценка | Зависит от |
|------|--------|-----------|
| R-6.1 Docker prod | 3-5ч | — |
| F (фундамент) | 3 нед | — |
| S (concordance) | 2 нед | F |
| T (TM + dict) | 3 нед | F |
| APP (API completion, M25) | 2 нед | F |
| SEC (security + reliability) | 1.5 нед | F |
| IO (import/export) | 2 нед | T |
| AUD (audio cache) | 2 нед | T |
| UX (wizard, palette) | 2 нед | F, AUD |
| **TOTAL** | **~20 нед** | |

---

## Метрики успеха v2.0

| Метрика | Сейчас | Цель |
|---------|--------|------|
| Engine модули | 21/22 | 22/22 (M25) |
| API endpoints | 29 | 40+ |
| UI views | 10 | 13 (+ concordance, wizard, palette) |
| DB migrations | 4 | 12+ |
| Test functions | ~980 | 800+ верифицировано |
| VRAM peak (3 модели) | — | ≤8GB |
| UI first-paint | — | ≤500ms (cold-audit) |
| Security issues | не проверено | 0 critical |
| CI | green | green + self-check |

---

## Фаза T7: Term Extractor ML Enhancement
**Параллельна Фазе S. Оценка: 1.5 недели / ~40ч**

### T7-1 — POS-aware Filtering (✅ DONE)
```
Реализовано: 2026-04-02
- M3: transformer POS fallback chain
- M8: POS-aware filtering (ALLOWED_POS: NOUN, PROPN, ADJ)
- Orchestrator: M3 → M8 data flow
- term_mode: 4 режима (distinct/canonical/clustered/related)
- UI: PipelineView selector + ResultsView help panel
- Тесты: 30/30 PASS
```

### T7-2 — NeoDictaBERT Clustering (~16ч)
```
kadima/engine/term_clusterer.py — уже есть, доработать:
- NeoDictaBERT embeddings для терминов
- HDBSCAN clustering (density-based)
- Semantic synonym merging
- variant_count, variants list в Term

UI: ResultsView — expandable cluster groups
```

### T7-3 — AlephBERT Fine-Tuning (~24ч)
```
kadima/engine/term_extractor_ml.py — новый ML backend:
- AlephBERT Token Classification (fine-tuned)
- Active learning loop: UI → Label Studio → retrain
- export_training_data() → CoNLL-U формат
- train_m8_model() скрипт

UI: PipelineView — "Extraction Method" selector (statistical | ml)
     ResultsView — кнопка "Retrain Term Model"
     Status bar: 🤖 ML: v3 (trained 2 days ago)
```

---

## Философские принципы (из мастер-плана, обязательны)

```
1. НЕ ПЕРЕПИСЫВАТЬ — АДАПТИРОВАТЬ (MiMo)
   engine/ нетронут, добавляем слои вокруг

2. PIPELINE-FIRST (MiMo)
   Все фичи доступны через API, CLI и UI одновременно

3. EVIDENCE-FIRST (Qwen)
   Каждый фикс производительности: before/after метрики

4. ИНКРЕМЕНТАЛЬНО (все три)
   Каждый патч: независимо buildable + testable

5. ML КАК СУПЕРСИЛА (Claude)
   ML модули интегрированы в каждый workflow
```
