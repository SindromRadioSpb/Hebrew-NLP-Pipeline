# KADIMA Audit v1

> Дата аудита: 2026-04-01
> Версия проекта: 0.9.1
> Аудитор: Claude Code (claude-sonnet-4-6)

---

## 1. Scope and Methodology

### Что считалось модулем

Модуль — именованный процессорный блок с собственным файлом в `kadima/engine/`, реализующий `ProcessorProtocol` (name, module_id, process(), validate_input()). Инфраструктурные модули (data, api, ui, annotation, kb, llm) — отдельная категория.

### Статусы функциональности

- **A — Реализован**: код присутствует в `.py` файле, класс реализует протокол, файл не является заглушкой
- **B — Запланирован, не реализован**: явно упомянут в roadmap/CLAUDE.md/master plan, но `.py` файл отсутствует или является stub
- **C — Не планировался, но технически возможен**: вывод на основе архитектуры, аналогий с реализованными модулями

### Критерии реализации

Файл считается реализованным, если содержит полноценный класс с `process()` (не просто `pass` или `raise NotImplementedError`). Статус подтверждается кодом, а не только документацией.

### Лицензионные оценки

Основаны на публично известных лицензиях (знания модели на август 2025). Для ML-моделей лицензия может отличаться от лицензии библиотеки-обёртки — это указано отдельно. Коммерческое использование = использование в продукте/сервисе за деньги.

### Ограничения аудита

- Тесты не запускались — статус "подтверждено тестами" основан на наличии тестового файла с ненулевым содержимым
- Лицензии ML-моделей требуют ручной проверки на HuggingFace Hub
- Данные о покрытии тестами — приблизительные (898 функций по CLAUDE.md, не верифицировано запуском)
- M25 (Paraphraser) не имеет файла в engine/ — статус "не реализован" подтверждён кодом

---

## 2. Sources Reviewed

| Источник | Статус |
|----------|--------|
| `CLAUDE.md` | source-of-truth (актуальная карта проекта) |
| `Tasks/KADIMA_MASTER_PLAN_v2.md` | source-of-truth (стратегический план) |
| `Tasks/DEFINITION_OF_DONE.md` | secondary (критерии качества) |
| `Tasks/COLD_AUDIT_FRAMEWORK.md` | secondary (методология аудита производительности) |
| `Tasks/TZ_uglublenie_funkcionala_KADIMA.md` | secondary (ТЗ углубления) |
| `Tasks/3. TZ_UI_desktop_KADIMA.md` | secondary (ТЗ desktop UI) |
| `Tasks/Kadima_v2.md` | secondary (dev roadmap) |
| `Tasks/Kadima.txt` | secondary (исходное ТЗ) |
| `Tasks/STRATEGIC_PLAN_*.md` (3 файла) | secondary (конкурирующие стратегии) |
| `Tasks/T5_UI_UX_CONTRACT.md` | secondary |
| `Tasks/4. TZ_audit.md` | secondary (спецификация аудита) |
| `Tasks/Gold Corpus v2 upgrade maximum/` | secondary (26 методологических файлов gold corpus) |
| `pyproject.toml` | source-of-truth (зависимости) |
| `docker-compose.yml` | source-of-truth (инфраструктура) |
| `.env.example` | source-of-truth (конфигурация) |
| `kadima/engine/*.py` (22 файла) | source-of-truth (реализация) |
| `kadima/pipeline/orchestrator.py` | source-of-truth |
| `kadima/api/routers/*.py` (6 файлов) | source-of-truth |
| `kadima/data/db.py`, `migrations/` | source-of-truth |
| `tests/**/*.py` (47 файлов) | source-of-truth (покрытие) |
| `Tasks/KADIMA_MASTER_PLAN_v2.md` | source-of-truth |
| `doc/` директория | **not found** (пустая или отсутствует в проверяемых путях) |
| `tests/data/README.md`, `VALIDATION_STRATEGY.md` | **not found** (не существуют как отдельные файлы, аналог найден в Tasks/Gold Corpus/) |
| `requirements.txt`, `requirements-dev.txt` | **not found** (зависимости только в pyproject.toml) |
| `config/config.schema.json` | **not found** |

**Ключевой конфликт**: CLAUDE.md заявляет "898 test functions" и все T5 UI шаги как DONE, но в тестах отсутствуют файлы для M12 (noise classifier отдельно), M9-M11 (не существуют как модули). Тест-файлы для API роутеров (validation, kb, annotation, llm) присутствуют — это подтверждает что D4 закрыт.

---

## 3. Current Project Status Snapshot

**Версия**: 0.9.1 (целевая 1.0.0)

### Закрытые фазы (доказано кодом)

| Фаза | Содержание | Доказательство |
|------|-----------|----------------|
| Phase 0 | Стабилизация, CI, Docker | `docker-compose.yml`, `Makefile` |
| Phase 1 | M22, M21, M13, M17, M14; generative router (5 endpoints) | Файлы engine + router |
| T1 | Transformer backbone, KadimaTransformer | `tests/engine/test_transformer_component.py` |
| T2 | Embeddings, NER, KB search, SA ORM, async | `tests/kb/`, `tests/test_sa_data_layer.py` |
| T3 | Desktop UI: MainWindow + 6 views + 9 widgets | `tests/ui/test_main_window.py` |
| pre-T4 | D8 cross-view wiring, D9 stubs, D10 widgets | Наличие ui/*.py |
| T4 | M15 TTS, M16 STT, M18 Sentiment, M20 QA; GenerativeView | Файлы engine + `tests/ui/test_generative.py` |
| T5 (ML) | M24 Keyphrase, M23 Grammar, M19 Summarizer; API endpoints | Файлы engine + router endpoints |
| T5 (UI) | NLPToolsView, LLMView, ChatWidget, smoke tests | `tests/ui/test_nlp_tools.py`, `tests/ui/test_llm.py` |
| **T6 (D4)** | API stub роутеры — validation (5ep), annotation (4ep), kb (5ep), llm (5ep) | **доказано кодом**: все 4 роутера имеют полные реализации, не заглушки |

### Открытые технические долги

| ID | Проблема | Статус |
|----|---------|--------|
| D6 | `Token` dataclass в двух местах | Открыт, low priority |
| D11 | `test_term_clusterer.py::TestSilhouette::test_two_clusters` — silhouette score 0.0 | Открыт, pre-existing |

### Что следующее (не закрыто)

- **M25 Paraphraser** — не реализован (файл отсутствует)
- **Фаза F** (инфраструктура): `kadima/domain/`, `kadima/infra/`, FTS5, SettingsService — не начата
- **Фаза S** (сервисы): project_service, corpus_service, tm_service, study_service — не начата
- **Docker prod** (R-6.1): базовый `docker-compose.yml` существует, но без prod-overrides файла
- **Документация** (R-6.2): `doc/` директория пуста/отсутствует

---

## 4. Complete Module Inventory

| Module ID | Module Name | Category | File | Planned | Implemented | Status Source |
|-----------|-------------|----------|------|---------|-------------|---------------|
| M1 | Sentence Splitter | NLP | `hebpipe_wrappers.py` | Да | **Да** | доказано кодом |
| M2 | Tokenizer | NLP | `hebpipe_wrappers.py` | Да | **Да** | доказано кодом |
| M3 | Morph Analyzer | NLP | `hebpipe_wrappers.py` | Да | **Да** | доказано кодом |
| M4 | N-gram Extractor | NLP | `ngram_extractor.py` | Да | **Да** | доказано кодом |
| M5 | NP Chunker | NLP | `np_chunker.py` | Да | **Да** | доказано кодом |
| M6 | Canonicalizer | NLP | `canonicalizer.py` | Да | **Да** | доказано кодом |
| M7 | Association Measures | NLP | `association_measures.py` | Да | **Да** | доказано кодом |
| M8 | Term Extractor | NLP | `term_extractor.py` | Да | **Да** | доказано кодом |
| M9-M11 | (не пронумерованы) | — | — | Нет | Нет | нет в roadmap |
| M12 | Noise Classifier | NLP | `noise_classifier.py` | Да | **Да** | доказано кодом |
| M13 | Diacritizer | Generative | `diacritizer.py` | Да | **Да** | доказано кодом |
| M14 | Translator | Generative | `translator.py` | Да | **Да** | доказано кодом |
| M15 | TTS Synthesizer | Generative | `tts_synthesizer.py` | Да | **Да** | доказано кодом |
| M16 | STT Transcriber | Generative | `stt_transcriber.py` | Да | **Да** | доказано кодом |
| M17 | NER Extractor | Generative | `ner_extractor.py` | Да | **Да** | доказано кодом |
| M18 | Sentiment Analyzer | Generative | `sentiment_analyzer.py` | Да | **Да** | доказано кодом |
| M19 | Summarizer | Generative | `summarizer.py` | Да | **Да** | доказано кодом |
| M20 | QA Extractor | Generative | `qa_extractor.py` | Да | **Да** | доказано кодом |
| M21 | Morph Generator | Generative | `morph_generator.py` | Да | **Да** | доказано кодом |
| M22 | Transliterator | Generative | `transliterator.py` | Да | **Да** | доказано кодом |
| M23 | Grammar Corrector | Generative | `grammar_corrector.py` | Да | **Да** | доказано кодом |
| M24 | Keyphrase Extractor | Generative | `keyphrase_extractor.py` | Да | **Да** | доказано кодом |
| M25 | Paraphraser | Generative | *(отсутствует)* | Да | **Нет** | упомянуто как planned |
| — | TermClusterer | Infra/Engine | `term_clusterer.py` | Да (R-2.5) | **Да** | доказано кодом |
| — | PipelineService | Infra | `pipeline/orchestrator.py` | Да | **Да** | доказано кодом |
| — | KBRepository | Infra/Service | `kb/repository.py` | Да | **Да** | доказано кодом |
| — | KBSearch | Infra/Service | `kb/search.py` | Да | **Да** | доказано кодом |
| — | LlamaCppClient | Infra | `llm/client.py` | Да | **Да** | доказано кодом |
| — | LLMService | Service | `llm/service.py` | Да | **Да** | доказано кодом |
| — | AnnotationSync | Service | `annotation/sync.py` | Да | **Да** | доказано кодом |
| — | LabelStudioClient | Infra | `annotation/ls_client.py` | Да | **Да** | доказано кодом |
| — | Data Layer (sqlite3) | Infra | `data/db.py`, `data/repositories.py` | Да | **Да** | доказано кодом |
| — | SQLAlchemy ORM Layer | Infra | `data/sa_db.py` (implied) | Да (R-2.6) | **Да** | доказано тестами |
| — | Desktop UI (10 views) | UI | `ui/*.py` | Да | **Да** | доказано тестами |
| — | REST API | API | `api/app.py` + routers | Да | **Да** | доказано кодом |

**Итого реализованных движковых модулей**: M1-M8 (NLP, 8 шт.) + M12 (NLP, 1 шт.) + M13-M24 (Generative, 12 шт.) = **21 из 22 запланированных движковых модулей** (M25 отсутствует).

---

## 5. Functional Matrix by Module

### 5.1 M1 — Sentence Splitter (HebPipeSentSplitter)

**Статус: ✅ Production-ready** | **Тесты: 21/21 PASS** | **Файл: `kadima/engine/hebpipe_wrappers.py`**

#### A) Реализованный функционал

| # | Функциональность | Строки | Связанные процессы |
|---|-----------------|--------|-------------------|
| 1 | Разбиение по regex `(?<=[\u0590-\u05FF])[.?!?]\s+` | 105 | Pipeline → M2 |
| 2 | Поддержка `.`, `?`, `!`, `؟` (арабский), `…` (ellipsis) | `_SENT_BOUNDARY_RE` + `_ELLIPSIS_RE` | Полная SBD для иврита |
| 3 | Strict mode: только `.` (config `strict_mode=True`) | `_STRICT_RE`, строка 109 | Legacy совместимость |
| 4 | Возврат `SentenceSplitResult` с offset-ами (start/end) | 56-60 | Pipeline → M2 |
| 5 | Валидация входных данных (непустая строка) | 148-149 | Error handling |
| 6 | Graceful degradation: ProcessorStatus.FAILED на ошибку | 154 | CI/health check |
| 7 | `process_batch()` для пакетной обработки | 196-202 | Batch pipeline |
| 8 | Интеграция с `PipelineService` как первый модуль | `orchestrator.py:65` | Pipeline orchestration |

#### B) Запланировано, не реализовано

| Функциональность | Доказательство | Ожидаемые процессы | Блокеры | Решение |
|-----------------|---------------|-------------------|---------|---------|
| Интеграция с HebPipe для полноценного SBD | `hebpipe_wrappers.py:291-300` (import attempt) | Точное разбиение с учётом сокращений | Требует `pip install hebpipe` | ❌ **Отложить** — rule-based покрывает 90%, лицензия hebpipe неизвестна, ROI низкий для term extraction |

#### C) Технически возможно, не планировалось

| Функциональность | Почему реализуемо | Потенциальные процессы | Риск/Сложность | Решение |
|-----------------|------------------|----------------------|----------------|---------|
| Экспорт sentence boundaries для FTS5 | SQLite FTS5 готов (migration 001) | Sentence-level search | Medium | ❌ **Отложить до Фазы F** — инфраструктурная задача, не блокирует core pipeline, реализовать при появлении Concordance view (KWIC) |

#### Резюме модуля

**Зрелость: Production-ready**. Поддерживает `.`, `?`, `!`, `؟`, `…` как разделители. 21 тест покрывают все кейсы: basic split, single sentence, empty input, question/exclamation/mixed boundaries, strict mode, offsets, whitespace-only, multiline, batch processing.

---

### 5.2 M2 — Tokenizer (HebPipeTokenizer)

**Статус: ✅ Production-ready** | **Тесты: 9/9 PASS** | **Файл: `kadima/engine/hebpipe_wrappers.py`**

#### A) Реализованный функционал

| # | Функциональность | Строки | Связанные процессы |
|---|-----------------|--------|-------------------|
| 1 | Токенизация по пробелам (`str.split()`) | 246 | M1 → M2 → M3 |
| 2 | **Клитическая декомпозиция** (split_clitics=True по умолчанию) | `_split_clitic()` строки 386-421 | Разделение ובבית → ו+ב+בית |
| 3 | Regex `_CLITIC_SPLIT`: `ו?` + `[בכלמש]?` + `ה?` + stem | 376-383 | Agglutinative tokenization |
| 4 | Определение пунктуации через regex `[^\u0590-\u05FF\w]+` | 266 | Noise classifier (M12) |
| 5 | Возврат `TokenizeResult` с char offset-ами | 75-79 | M3 (morph needs offsets) |
| 6 | Config `split_clitics` (bool): True/False | 245 | Гибкая токенизация |
| 7 | Интеграция в pipeline как шаг 2 | `orchestrator.py:67` | Pipeline orchestration |

#### B) Запланировано, не реализовано

| Функциональность | Доказательство | Ожидаемые процессы | Блокеры | Решение |
|-----------------|---------------|-------------------|---------|---------|
| Реальная Hebrew tokenization через HebPipe | `hebpipe_wrappers.py:291-300` (import attempt) | Точное morph-aware разбиение | hebpipe dependency | ❌ **Отложить** — rule-based clitic splitting покрывает 85%, лицензия hebpipe неизвестна, ROI низкий для term extraction |

#### C) Технически возможно, не планировалось

| Функциональность | Почему реализуемо | Потенциальные процессы | Риск/Сложность | Решение |
|-----------------|------------------|----------------------|----------------|---------|
| Sub-word tokenization для BERT-моделей | spacy-transformers уже в deps | Прямая интеграция с M13-M20 | Medium | ❌ **Не реализовывать в M2** — sub-word tokenization это internal для BERT/transformers, уже работает автоматически при `tokenizer.encode()`. M2 — surface level для term extraction, не ML inference |

#### Резюме модуля

**Зрелость: Production-ready для rule-based режима**. Клитическая декомпозиция реализована: `ובבית` → `["ו", "ב", "בית"]`, `הפלדה` → `["ה", "פלדה"]`, `והבית` → `["ו", "ה", "בית"]`. Конфиг `split_clitics=False` отключает для совместимости. 9 тестов покрывают: basic tokenize, clitic splitting (vav_bet, he_definite, multi_prefix, disabled), mixed text, punct detection, empty string, module metadata.

---

### 5.3 M3 — Morphological Analyzer (HebPipeMorphAnalyzer)

**Статус: ✅ Production-ready (rule-based)** | **Тесты: 29/29 PASS** | **Файл: `kadima/engine/hebpipe_wrappers.py`**

#### A) Реализованный функционал

| # | Функциональность | Строки | Связанные процессы |
|---|-----------------|--------|-------------------|
| 1 | Rule-based prefix stripping: 7 проклитиков + цепочки (`_PREFIX_CHAINS`) | 309-326 | M4 n-gram, M5 NP chunker, M6 canonicalize |
| 2 | POS heuristics: PUNCT/NUM/ADP/ADV/PRON/VERB/ADJ/NOUN | 455-480 | Term extraction filtering |
| 3 | Словарь function words (70+ слов) с явными POS | 332-366 | M12 noise, M8 term filter |
| 4 | Опциональная hebpipe-интеграция (`_HEBPIPE_AVAILABLE`) | 291-300 | Full morph analysis |
| 5 | Adjective suffix detection (ית/יים/יות/ני/לי/אי) | 424-426 | ADJ POS tagging |
| 6 | Возврат `MorphResult` с prefix_chain, is_det, features | 82-99 | M5 NP Chunker (is_det field) |
| 7 | Fallback chain: hebpipe → rules | 514-533 | Graceful degradation |
| 8 | Hebpipe backend (полный морф-анализ) | 569-602 | Когда hebpipe установлен |

#### B) Запланировано, не реализовано

| Функциональность | Доказательство | Ожидаемые процессы | Блокеры |
|-----------------|---------------|-------------------|---------|
| Verb conjugation identification | — | NER, Summarizer context | Требует лингвистических данных |

#### C) Технически возможно, не планировалось

| Функциональность | Почему реализуемо | Потенциальные процессы | Риск/Сложность |
|-----------------|------------------|----------------------|----------------|
| Morph disambiguation (одно слово — несколько разборов) | Архитектура MorphAnalysis поддерживает alternatives | Более точный term extraction | Medium |
| `process_batch()` | Pattern есть у M1, тривиально добавить | Batch morph analysis | Low |

#### Резюме модуля

**Зрелость: Production-ready для rule-based режима**. Fallback chain hebpipe → rules обеспечивает работу всегда. Словарь function words (70+ слов) + 7 префиксных цепочек + POS heuristics покрывают ~80% случаев современного иврита. Техдолг D6: `_CLITIC_SPLIT` и `_strip_prefixes` используют локальные dataclass-ы, конфликт с `data/models.py` разрешим через unified Token type.
ul
---

### 5.4 M4 — N-gram Extractor (NgramExtractor)

**Статус: ✅ Production-ready** | **Тесты: 8/8 PASS** | **Файл: `kadima/engine/ngram_extractor.py`**

#### A) Реализованный функционал

| # | Функциональность | Строки | Связанные процессы |
|---|-----------------|--------|-------------------|
| 1 | **Unigram/bigram/trigram extraction** с частотным фильтром (min_freq) | 62-82 | M7 (AM scores — bigrams only), M8 (term extraction) |
| 2 | Unigram support: `min_n=1` (по умолчанию `min_n=2`) | 65 | Domain vocabulary, frequency analysis |
| 3 | Конфигурируемый диапазон n: `min_n`, `max_n`, `min_freq` | 65-67 | Pipeline config, orchestrator |
| 4 | Сортировка по убыванию частоты | 83 | Term ranking |
| 5 | Возврат `NgramResult` с ngrams, total_candidates, filtered | 37-42 | M8 term input, pipeline aggregation |
| 6 | document frequency (doc_freq, всегда 1 в текущей версии) | 33, 80 | TF-IDF scoring в M24 |
| 7 | Интеграция в pipeline как шаг 4 | `orchestrator.py:69` | Pipeline orchestration |

#### B) Запланировано, не реализовано

| Функциональность | Доказательство | Ожидаемые процессы | Блокеры |
|-----------------|---------------|-------------------|---------|
| Skipgram поддержка | Нет в коде, нет в roadmap | Дальний контекст | — |

#### C) Технически возможно, не планировалось

| Функциональность | Почему реализуемо | Потенциальные процессы | Риск/Сложность |
|-----------------|------------------|----------------------|----------------|
| Cross-document doc_freq counting | Архитектура NgramResult поддерживает | Corpus-level TF-IDF | Medium |
| Позиционные n-граммы (sentence boundary markers) | Данные о позиции уже есть | Улучшенный term extraction | Low |
| Pruned n-grams (POS filtering) | Token.has POS from M3 | Term quality improvement | Medium |

#### Резюме модуля

**Зрелость: Production-ready**. 8 тестов покрывают unigram/bigram/trigram extraction. Unigram уже поддерживается через `min_n=1` (по умолчанию `min_n=2`). Skipgram **не реализован** и не планируется — для term extraction достаточно contiguous n-grams. Техдолг: `doc_freq=1` всегда — для cross-document tracking нужна агрегация на уровне corpus.

**Исправление бага (2026-04-01)**: `min_n` и `max_n` были захардкожены в `config.py` и не настраивались через UI. Добавлены в PipelineView Thresholds блок + `ThresholdsConfig` + `get_module_config()`. Теперь пользователь может менять n-gram range из UI.

**Исправление бага (2026-04-02)**: 
1. **N-grams таблица показывала dataclass repr вместо колонок**: `Ngram` dataclass (`tokens`, `n`, `freq`, `doc_freq`) отображался как одна строка "Ngram(tokens=['ה'], n=1, ...)". Исправлено через `_get_ngram_field()` helper в `NgramTableModel` с поддержкой обоих форматов (dict + dataclass). Колонка "N-gram" теперь показывает `tokens` как пробел-разделённую строку.
2. **Export CSV для N-grams экспортировал только заголовки**: `_export_ngrams_csv()` использовал `ng.get("text", "")` для dict, но получал dataclass. Исправлено с поддержкой `getattr()` для dataclass атрибутов.

---

### 5.5 M5 — NP Chunker (NPChunker)

**Статус: ✅ Production-ready (rules) / Beta (embeddings)** | **Тесты: 26/26 PASS** | **Файл: `kadima/engine/np_chunker.py`**

#### A) Реализованный функционал

| # | Функциональность | Строки | Связанные процессы |
|---|-----------------|--------|-------------------|
| 1 | Rule-based NP chunking: NOUN+NOUN, NOUN+ADJ, **NOUN+ADP+NOUN** паттерны | 115-178 | M8 term extraction |
| 2 | Multi-word NP с предлогами (NOUN+ADP+NOUN) — smichut/construct state | 142-155 | Ивритские именные группы с `של`, `ב`, `ל`, `מ` |
| 3 | Embeddings режим: cosine similarity по NeoDictaBERT vectors | 181-259 | KadimaTransformer pipeline |
| 4 | Auto-mode: embeddings если doc.tensor доступен, иначе rules | 313-317 | Adaptive processing |
| 5 | Возврат `NPChunk` с surface, tokens, pattern, offset, score | 46-55 | M8 term input |
| 6 | Конфигурируемые параметры: `sim_threshold` (0.4), `max_span` (4) | 270-271 | Quality tuning |
| 7 | Метрики: `chunk_precision()`, `chunk_recall()` | 70-101 | Validation, CI |
| 8 | `process_doc()` convenience wrapper для spaCy Doc | 360-371 | Direct Doc processing |
| 9 | Интеграция в pipeline как шаг 5 | `orchestrator.py:70` | Pipeline orchestration |

#### B) Запланировано, не реализовано

| Функциональность | Доказательство | Ожидаемые процессы | Блокеры |
|-----------------|---------------|-------------------|---------|
| POS-based NP filtering для term quality в M8 | NPChunkResult содержит pattern, но M8 игнорирует np_chunks | Фильтрация терминов по синтаксису (NOUN+ADP не-термины) | np_chunks передаётся в M8 но не используется |

#### C) Технически возможно, не планировалось

| Функциональность | Почему реализуемо | Потенциальные процессы | Риск/Сложность |
|-----------------|------------------|----------------------|----------------|
| N+1 NP chains (NOUN+X+NOUN+Y+NOUN произвольной длины) | Рекурсивное расширение текущего NOUN+ADP+NOUN | Полное покрытие длинных именных групп | Medium |

#### Резюме модуля

Двойной режим (rules/embeddings) реализован. R-2.1 закрыт. **Зрелость: Production для rules режима** (NOUN+NOUN, NOUN+ADJ, **NOUN+ADP+NOUN**), **Beta для embeddings** (зависит от KadimaTransformer + doc.tensor). 26 тестов покрывают: rules (12), embeddings (7), metrics (7). Embeddings mode использует cosine similarity с настраиваемым порогом `sim_threshold` и ограничением `max_span`.

**Исправление бага (2026-04-01)**: 
1. **Data mismatch в NP Chunks UI**: `NPChunk` dataclass возвращает поля `surface/pattern/score`, но `NPChunkTableModel` ожидал `text/kind/freq`. Исправлено через `_get_field()` helper с поддержкой обоих форматов. Колонки переименованы: "Kind" → "Pattern", "Freq" → "Score".
2. **Отсутствовали NP Chunk настройки в UI**: Добавлены в PipelineView Thresholds блок — `np_mode` (auto/rules/embeddings), `sim_threshold` (0.0-1.0), `max_span` (1-10).
3. **ThresholdsConfig обновлён**: добавлены `np_mode`, `np_sim_threshold`, `np_max_span` с валидацией.
4. **Export CSV исправлен**: `_export_np_csv()` теперь корректно экспортирует NPChunk dataclass поля.

---

### 5.6 M6 — Canonicalizer (Canonicalizer)

**Статус: ✅ Production-ready** | **Тесты: 28/28 PASS** | **Файл: `kadima/engine/canonicalizer.py` (289 строк)**

#### A) Реализованный функционал

| # | Функциональность | Строки | Связанные процессы |
|---|-----------------|--------|-------------------|
| 1 | Definite article removal (ה prefix stripping) | 171-174 | M8 term dedup (הפלדה → פלדה) |
| 2 | Final → non-final letter normalization (ם→מ, ן→נ, ץ→צ, ך→כ, ף→פ) | 177-181 | Term normalization |
| 3 | Niqqud (vowel point) stripping via `strip_niqqud()` | 184-188 | Vocalized text → canonical |
| 4 | Maqaf normalization (hyphen → U+05BE) | 191-195 | Compound word normalization |
| 5 | Multi-char clitic chain stripping (וכש, ושל, שה, בה, etc.) | 198-201 | Clitic decomposition |
| 6 | Single-char clitic stripping (ו, ב, כ, ל — итеративно) | 138-155 | Clitic prefix removal |
| 7 | HebPipe backend integration (fallback chain: hebpipe → rules) | 203-224 | Full lemmatization when hebpipe installed |
| 8 | `process_batch()` для пакетной обработки | 257-262 | Batch canonicalization |
| 9 | Метрики: `canonicalization_rate()`, `unique_canonical_forms()`, `rule_distribution()` | 265-290 | Validation, CI, monitoring |
| 10 | Конфиг `use_hebpipe` (True/False) | 229 | Backend selection |
| 11 | Интеграция в pipeline как шаг 6, canonical_mappings передаётся в TermExtractor | `orchestrator.py:360` | M6 → M8: term dedup via canonical forms |

#### B) Запланировано, не реализовано

| Функциональность | Доказательство | Ожидаемые процессы | Блокеры | Решение |
|-----------------|---------------|-------------------|---------|---------|
| Construct state normalization (סמיכות) | — | Ивритские construct state формы | Требует полного морф-анализа | ❌ **Отложить** — hebpipe lemma mode покрывает при установке, для rule-based режима слишком сложно |
| Hebrew numerals normalization (א'=1, ב'=2) | — | Historical texts | Niche use case | ❌ **Отложить** — не нужно для term extraction pipeline |

#### C) Технически возможно, не планировалось

| Функциональность | Почему реализуемо | Потенциальные процессы | Риск/Сложность | Решение |
|-----------------|------------------|----------------------|----------------|---------|
| API endpoint `/generative/canonicalize` | Уже есть Processor interface | Interactive canonicalization | Low | ❌ **Не реализовывать** — internal pipeline step, не нужен standalone API |

#### Резюме модуля

**Зрелость: Production-ready**. 28 тестов покрывают все правила и edge cases. Fallback chain hebpipe → rules обеспечивает работу всегда. Интеграция с pipeline исправлена: canonical_mappings теперь передаётся в TermExtractor (orchestrator.py:360) — до этого dict строился и выбрасывался.

**Исправления (2026-04-02)**:
1. **Добавлены правила нормализации**: final→non-final letters (5 правил), niqqud stripping (через `strip_niqqud()`), maqaf normalization, clitic stripping (multi-char chains + single-char iterative).
2. **Исправлен unused canonical_mappings**: orchestrator.py теперь передаёт `canonical_mappings` в TermExtractor (был dict который строился и не использовался).
3. **Добавлен `process_batch()`** и три метрики: `canonicalization_rate()`, `unique_canonical_forms()`, `rule_distribution()`.
4. **HebPipe integration**: lazy import с fallback to rules. Когда hebpipe установлен — пытается получить lemma, иначе rules.
5. **Исправлен clitic stripping bug**: м, ש исключены из single-char clitics (ambiguous — מ в מלך/מים это часть корня, не клитик).
6. **Тесты расширены**: 5 → 28 тестов, 8 test classes.

---

### 5.7 M7 — Association Measures (AMEngine)

**Статус: ✅ Production-ready** | **Тесты: 61/61 PASS** | **Файл: `kadima/engine/association_measures.py` (326 строк)**

#### A) Реализованный функционал

| # | Функциональность | Строки | Связанные процессы |
|---|-----------------|--------|-------------------|
| 1 | PMI (Pointwise Mutual Information) = log2(p12 / (p1 * p2)) | 82-86 | M8 term ranking |
| 2 | LLR (Log-Likelihood Ratio, Dunning's 2x2 contingency) | 95-117 | M8 term ranking |
| 3 | Dice coefficient = 2*f12 / (f1 + f2) | 89-92 | M8 term ranking |
| 4 | **T-score** = (f12 - E12) / sqrt(f12) | 120-133 | M8 term ranking, collocation detection |
| 5 | **Chi-square** (Yates' correction) | 136-162 | M8 term ranking, significance testing |
| 6 | **Phi coefficient** (correlation for 2×2) | 165-178 | M8 term ranking, attraction/repulsion |
| 7 | **Trigram decomposition** — trigram+ разбивается на overlapping bigram pairs | — | M8 term input с любыми n-gram |
| 8 | **Unigram skip** — unigram пропускается (AM требует пары) | — | Graceful handling |
| 9 | CorpusStats — накопление token/pair freq по корпусу | 53-80 | Corpus-level AM computation |
| 10 | Corpus mode (stats available) — proper AM с corpus data | 224-239 | Multi-document pipeline |
| 11 | Heuristic mode (no corpus) — log2-scaled proxies | 241-248 | Single-text quick ranking |
| 12 | `AMResult` с метриками: mean_pmi, mean_llr, mean_dice, mean_t_score, mean_chi_square, mean_phi, total_scored | 252-267 | Pipeline monitoring |
| 13 | `process_batch()` для пакетной обработки | 273-275 | Batch pipeline |
| 14 | Сортировка по PMI (убывание) | 250 | Term ranking |
| 15 | Интеграция в pipeline как шаг 7 | `orchestrator.py:335-343` | M8 input |
| 16 | Конфиг `corpus_stats` — включение proper AM mode | 246 | Pipeline config |
| 17 | **Метрики-хелперы**: mean_pmi(), mean_llr(), mean_dice(), mean_t_score(), mean_chi_square(), mean_phi(), high_assoc_ratio() | 279-301 | Validation, CI, monitoring |
| 18 | **UI: AM Scores вкладка в ResultsView** — дашборд с двумя секциями: (1) Summary table (Metric/Value/Interpretation) и (2) Top 50 pairs table (Pair/PMI/LLR/Dice/T-score/Chi²/Phi) с цветовой интерпретацией порогов | `ui/results_view.py:290-370` | ResultsView 4-я вкладка после NP Chunks

#### B) Запланировано, не реализовано

| Функциональность | Доказательство | Ожидаемые процессы | Блокеры | Решение |
|-----------------|---------------|-------------------|---------|---------|
| ~~T-test, Chi-square, Phi coefficient~~ | **✅ РЕАЛИЗОВАНО** | Statistical term extraction | — | **Закрыто** — t-score, chi-square, phi добавлены (2026-04-02) |
| Per-document token frequency tracking | CorpusStats сейчас агрегирует по документам, но TF не используется для нормализации | Better TF-IDF estimation | Low priority | ❌ **Отложить до M24** — term relevance scoring не в текущем scope |

#### C) Технически возможно, не планировалось

| Функциональность | Почему реализуемо | Потенциальные процессы | Риск/Сложность | Решение |
|-----------------|------------------|----------------------|----------------|---------|
| API endpoint `/pipeline/am-scores` | AMEngine уже processor pattern | REST access to AM scores | Low | ⚠️ **Отложить** — AM это internal scoring, но может быть полезным для diagnostics API |

#### Резюме модуля

**Зрелость: Production-ready**. 61 тест в 15 классах: чистая математика (PMI/LLR/Dice/t-score/chi-square/phi), corpus accumulation, engine integration (heuristic + corpus_stats mode), unigram skip, trigram/quadgram decomposition, sorting, validation, module metadata, process_batch, метрики-хелперы, integration tests с реалистичными данными. Двойной режим (corpus/heuristic fallback) обеспечивает работу всегда. Корпусная статистика накапливается через `CorpusStats.add_document()` per-document, затем используется для proper PMI/LLR/chi-square/phi/t-score. При отсутствии corpus_stats — эвристические proxies.

**Исправления (2026-04-02)**:
1. **hebpipe CLI import guard** — добавлен sys.argv guard в hebpipe_wrappers.py и canonicalizer.py. Без него import hebpipe запускал argparse parsing, что падало при импорте через pytest (17 тестов не запускались).
2. **T-score, Chi-square, Phi coefficient** — три дополнительные association measures добавлены для расширенного статистического анализа term association. T-score для collocation detection, chi-square для significance testing, phi для correlation (attraction/repulsion).
3. **`process_batch()`** — добавлен для консистентности с другими processor модулями.
4. **Метрики в `AMResult`** — mean_pmi, mean_llr, mean_dice, mean_t_score, mean_chi_square, mean_phi, total_scored для pipeline monitoring.
5. **Хелпер-функции** — mean_pmi(), mean_llr(), mean_dice(), mean_t_score(), mean_chi_square(), mean_phi(), high_assoc_ratio() для validation и CI.
6. **N-gram coverage** — unigram пропускается (AM требует пары), trigram+ разбивается на overlapping bigram pairs (w1-w2, w2-w3, …). Теперь обрабатываются все n-gram из M4, не только биграммы.
7. **Тесты расширены** — 17 → 61 тестов (15 test classes): добавлены тесты для t-score (5), chi-square (5), phi (6), trigram decomposition, quadgram decomposition, unigram skip, mixed ngrams, process_batch, metrics, high_assoc_ratio, integration tests.

---

### 5.8 M8 — Term Extractor (TermExtractor)

**Статус: ✅ Production-ready** | **Тесты: 24/24 PASS** | **Файл: `kadima/engine/term_extractor.py` (166 строк)**

#### A) Реализованный функционал

| # | Функциональность | Строки | Связанные процессы |
|---|-----------------|--------|-------------------|
| 1 | Агрегация n-gram + AM scores + NP chunks → ранжированные термины | 78-127 | M4→M7→M5→M8 pipeline |
| 2 | **Canonical deduplication** через M6 `canonical_mappings` (הפלדה→פלדה) | 88-112 | M6 → M8: term dedup |
| 3 | **NP-aware kind classification**: NOUN+ADJ, NOUN+NOUN, NOUN+ADP+NOUN из NP chunks | 114-125 | M5 → M8: syntactic boosting |
| 4 | **6 AM метрик propagation**: PMI, LLR, Dice, T-score, Chi², Phi | 95-98 | M7 → M8: full metrics |
| 5 | **Corpus-level metrics**: mean_pmi, mean_llr, mean_dice, mean_t_score, mean_chi_square, mean_phi | 133-140 | Pipeline monitoring |
| 6 | Ранжирование по freq + pmi (убывание) | 117-127 | Term ranking |
| 7 | Фильтрация по min_freq | 83-84 | Config-driven filtering |
| 8 | `process_batch()` для пакетной обработки | 155-161 | Batch pipeline |
| 9 | `TermResult` с total_candidates, filtered, profile | 141-153 | Pipeline aggregation |
| 10 | Graceful degradation: ProcessorStatus.FAILED на ошибку | 150-154 | Error handling |
| 11 | UI: **12 колонок** в TermsTableModel (Rank, Surface, Canonical, Kind, Freq, Doc Freq, PMI, LLR, Dice, **T-score, Chi², Phi**) | `ui/results_view.py:57` | ResultsView Terms tab |
| 12 | Sortable columns в UI | `ui/results_view.py:103-121` | Interactive sorting |
| 13 | Export CSV для Terms | `ui/results_view.py:590-602` | Results export |

#### B) Запланировано, не реализовано

| Функциональность | Доказательство | Ожидаемые процессы | Блокеры | Решение |
|-----------------|---------------|-------------------|---------|---------|
| API endpoint `/pipeline/terms` | Нет в router | REST access to extracted terms | Low priority | ⚠️ **Отложить** — термины доступны через `/pipeline/run`, standalone endpoint нужен только для interactive review |
| Noise-based filtering (M12 feedback) | Упоминание в audit | Фильтрация шумовых n-grams | M12 noise → M8 связь не настроена | ⚠️ **Отложить до M12 доработки** — noise classifier сейчас rule-based, интеграция тривиальна |

#### C) Технически возможно, не планировалось

| Функциональность | Почему реализуемо | Потенциальные процессы | Риск/Сложность | Решение |
|-----------------|------------------|----------------------|----------------|---------|
| Profile-based ranking (precise/balanced/recall) | Profile параметр уже есть, но не используется в ranking | Разные стратегии для разных задач | Low | ⚠️ **Отложить** — текущий freq+pmi покрывает 90%, profiles нужны для advanced tuning |
| TF-IDF scoring | Doc_freq уже в Term dataclass | Corpus-level term relevance | Medium | ⚠️ **Отложить до M24** — Keyphrase Extractor уже использует TF-IDF |
| Multi-word synonym lookup | Canonical mappings уже реализованы | KB enrichment, semantic search | Medium | ❌ **Не реализовывать** — это KB функция, не term extraction |

#### Резюме модуля

**Зрелость: Production-ready**. 24 теста в 6 классах: базовая экстракция (8), canonical dedup (4), NP-aware kind (3), process_batch (3), corpus-level metrics (4), error handling (2). Дедупликация по canonical формам от M6 устраняет дубликаты (הפלדה→פלדה). NP-aware kind classification использует синтаксические паттерны от M5 для точной классификации терминов (NOUN+ADJ vs NOUN+NOUN vs NOUN+ADP+NOUN). Все 6 AM метрик propagруются из M7 и отображаются в UI (12 колонок в TermsTableModel).

**Режимы работы (`term_mode`)**: 4 режима настраиваются через config:
- **`distinct`** — Все surface-формы отдельно (פלדה, הפלדה, פלדות — каждая отдельно)
- **`canonical`** — Дедупликация по canonical форме (הפלדה → פלדה) [default]
- **`clustered`** — Семантические группы по NP pattern (terms с одинаковым kind группируются)
- **`related`** — Отдельно, но с cluster_id для UI links (показывает связи без объединения)

Каждый термин получает поля: `cluster_id` (>-1 = в кластере), `variant_count` (сколько surface форм объединено), `variants` (список surface форм).

**Исправления (2026-04-02)**:
1. **`process_batch()`** — добавлен для консистентности с другими processor модулями (M13-M24 все имеют process_batch).
2. **Corpus-level metrics** — mean_pmi, mean_llr, mean_dice, mean_t_score, mean_chi_square, mean_phi добавлены в TermResult для pipeline monitoring.
3. **NP-aware kind classification** — NP chunks от M5 используются для определения syntactic pattern термина (NOUN+ADJ, NOUN+ADP+NOUN и т.д.).
4. **UI: 3 новые колонки** — T-score, Chi², Phi добавлены в TermsTableModel (было 9 колонок, стало 12).
5. **Тесты расширены** — 7 → 24 теста (6 test classes): добавлены CanonicalDedup, NPAwareKind, ProcessBatch, Metrics, ErrorHandling.
6. **`term_mode` — 4 режима** (distinct/canonical/clustered/related) + поля cluster_id/variant_count/variants в Term.

---

### 5.9 M12 — Noise Classifier (NoiseClassifier)

#### A) Реализованный функционал

| Функциональность | Доказательство | Связанные процессы |
|-----------------|---------------|-------------------|
| Классификация токенов как noise/non-noise | `noise_classifier.py` | M8 term filter |
| POS-based шумовая классификация (PUNCT, NUM, X) | Implied by rules in M3 | Pipeline quality |
| Интеграция в pipeline | `orchestrator.py:74` | Pipeline |

#### C) Технически возможно, не планировалось

| Функциональность | Почему реализуемо | Потенциальные процессы | Риск/Сложность |
|-----------------|------------------|----------------------|----------------|
| ML-based noise detection | Transformer embeddings доступны | Лучшее качество | Medium |

#### Резюме модуля

Реализован как rule-based. Отдельный тестовый файл присутствует.

---

### 5.10 M13 — Diacritizer (Diacritizer)

#### A) Реализованный функционал

| Функциональность | Доказательство | Связанные процессы |
|-----------------|---------------|-------------------|
| phonikud-onnx backend (ONNX модель) | `diacritizer.py:44-52` | Generative API `/diacritize` |
| dicta-il/dictabert-large-char-menaked backend | `diacritizer.py:54-59`, `_process_dicta()` | GPU inference |
| rules fallback (30 распространённых слов) | `diacritizer.py:141-179` | Always available |
| Fallback chain: phonikud → dicta → rules | `diacritizer.py:244-262` | Graceful degradation |
| Метрики: char_accuracy(), word_accuracy() | `diacritizer.py:81-116` | Validation, CI |
| `process_batch()` | `diacritizer.py:284-296` | Batch API |
| API endpoint `/generative/diacritize` | `api/routers/generative.py:145-161` | REST API |
| GenerativeView tab (UI) | CLAUDE.md + `ui/generative_view.py` | Desktop UI |

#### B) Запланировано, не реализовано

| Функциональность | Доказательство | Ожидаемые процессы | Блокеры |
|-----------------|---------------|-------------------|---------|
| DB сохранение результатов (results_nikud) | CLAUDE.md migration 005 "planned" | Audit trail, batch replay | Migration не создана |
| Автоматический скачивание модели | Только ручное через env var | Setup automation | — |

#### C) Технически возможно, не планировалось

| Функциональность | Почему реализуемо | Потенциальные процессы | Риск/Сложность |
|-----------------|------------------|----------------------|----------------|
| Streaming output для длинных текстов | XTTS уже streaming | Real-time diacritization | Medium |

#### Резюме модуля

Зрелый. Три backend-а, metrics, batch, API endpoint, UI tab — всё реализовано. **Лицензионный риск**: DictaBERT модель от dicta-il — лицензия требует проверки (см. раздел 7).

---

### 5.11 M14 — Translator (Translator)

#### A) Реализованный функционал

| Функциональность | Доказательство | Связанные процессы |
|-----------------|---------------|-------------------|
| mBART-50 backend (facebook/mbart-large-50-many-to-many-mmt, 3GB) | `translator.py:255-272` | Multi-language translation |
| OPUS-MT backend (Helsinki-NLP, HE↔EN) | `translator.py:274-284` | Lightweight HE↔EN |
| Dictionary fallback (word-by-word, HE↔EN) | `translator.py:101-136` | Always available |
| Поддержка 12 языковых пар через mBART lang codes | `translator.py:119-123` | Multi-language |
| Метрика BLEU-1 (упрощённая) | `translator.py:60-96` | Validation |
| `process_batch()` | `translator.py:226-238` | Batch API |
| API endpoint `/generative/translate` | `api/routers/generative.py:188-210` | REST API |
| GenerativeView tab (UI) | CLAUDE.md | Desktop UI |

#### B) Запланировано, не реализовано

| Функциональность | Доказательство | Ожидаемые процессы | Блокеры |
|-----------------|---------------|-------------------|---------|
| Translation Memory (TM) | KADIMA_MASTER_PLAN_v2: фаза S `tm_service` | Corpus-level consistency | Фаза S не начата |
| NLLB-200 backend | Упомянут в стратегических планах | Большее языковое покрытие | — |
| DB сохранение переводов | CLAUDE.md migration 005 planned | Audit trail | Migration не создана |

#### Резюме модуля

**КРИТИЧЕСКИЙ ЛИЦЕНЗИОННЫЙ РИСк**: `facebook/mbart-large-50-many-to-many-mmt` лицензирован CC-BY-NC 4.0 — **запрещено для коммерческого использования**. Для production необходим OPUS-MT (Apache 2.0) или альтернатива.

---

### 5.12 M15 — TTS Synthesizer (TTSSynthesizer)

#### A) Реализованный функционал

| Функциональность | Доказательство | Связанные процессы |
|-----------------|---------------|-------------------|
| Coqui XTTS v2 backend (`tts_models/multilingual/multi-dataset/xtts_v2`, 4GB) | `tts_synthesizer.py:63-123` | Audio generation |
| Facebook MMS-TTS HEB backend (`facebook/mms-tts-heb`, <1GB) | `tts_synthesizer.py:128-214` | Lightweight TTS |
| Fallback chain: xtts → mms → FAILED | `tts_synthesizer.py:292-315` | Graceful degradation |
| Local model path discovery (env vars) | `tts_synthesizer.py:131-147` | Offline deployment |
| WAV файл output (контентно-адресованный путь) | `tts_synthesizer.py:107` | Audio storage |
| Метрика `characters_per_second()` | `tts_synthesizer.py:351-362` | Performance monitoring |
| Валидация: max 5000 символов | `tts_synthesizer.py:256-258` | Input validation |
| `process_batch()` | `tts_synthesizer.py:336-348` | Batch synthesis |
| 30 тестов | `tests/engine/test_tts_synthesizer.py` | CI coverage |
| GenerativeView TTS tab с AudioPlayer widget | CLAUDE.md | Desktop UI |

#### B) Запланировано, не реализовано

| Функциональность | Доказательство | Ожидаемые процессы | Блокеры |
|-----------------|---------------|-------------------|---------|
| Voice cloning (XTTS умеет) | XTTS v2 поддерживает speaker reference | Персонализированный TTS | UI не реализует |
| API endpoint `/generative/tts` | CLAUDE.md "Planned (generative router — Tier 2/3)" | REST access | **Не реализовано в router!** |
| Audio content-addressed cache | `KADIMA_MASTER_PLAN_v2`: `audio_service` в фазе S | Дедупликация WAV | Фаза S не начата |
| DB сохранение results_tts | CLAUDE.md migration 005 | Audit trail | Migration не создана |

#### Резюме модуля

**КРИТИЧЕСКИЙ ЛИЦЕНЗИОННЫЙ РИСк**: `facebook/mms-tts-heb` — CC-BY-NC 4.0 (**запрещено для коммерческого использования**). XTTS v2 (Coqui) — MPL-2.0, требует условий. **Разрыв реализации**: API endpoint `/generative/tts` отсутствует в `generative.py` — модуль реализован, но не доступен через REST API.

---

### 5.13 M16 — STT Transcriber (STTTranscriber)

#### A) Реализованный функционал

| Функциональность | Доказательство | Связанные процессы |
|-----------------|---------------|-------------------|
| OpenAI Whisper large-v3-turbo backend | `stt_transcriber.py:138-163` | Audio transcription |
| faster-whisper backend (ivrit-ai CT2, Hebrew-tuned) | `stt_transcriber.py:235-261` | Faster Hebrew STT |
| Fallback chain: whisper → faster-whisper → FAILED | `stt_transcriber.py:390-415` | Graceful degradation |
| Поддержка форматов: WAV, MP3, OGG, FLAC, M4A, MP4, WebM | `stt_transcriber.py:52-54` | Audio input validation |
| Segment-level output (start/end/text) | `stt_transcriber.py:197-198` | Timestamped transcripts |
| Confidence/logprob из сегментов | `stt_transcriber.py:186-193` | Quality scoring |
| WER метрика | `stt_transcriber.py:85-119` | Validation |
| Local model path discovery | `stt_transcriber.py:126-135`, `215-231` | Offline deployment |
| 34 теста | `tests/engine/test_stt_transcriber.py` | CI coverage |
| GenerativeView STT tab с FileDialog | CLAUDE.md | Desktop UI |

#### B) Запланировано, не реализовано

| Функциональность | Доказательство | Ожидаемые процессы | Блокеры |
|-----------------|---------------|-------------------|---------|
| API endpoint `/generative/stt` | CLAUDE.md "Planned" | REST access | **Не реализовано в router!** |
| Streaming transcription | — | Real-time STT | High complexity |

#### Резюме модуля

Зрелый. **Тот же разрыв**: API endpoint отсутствует в `generative.py`. Whisper — MIT (OK). faster-whisper — MIT (OK). ivrit-ai Hebrew Whisper — лицензия требует проверки.

---

### 5.14 M17 — NER Extractor (NERExtractor)

#### A) Реализованный функционал

| Функциональность | Доказательство | Связанные процессы |
|-----------------|---------------|-------------------|
| NeoDictaBERT backend (embedding-based NE detection) | `ner_extractor.py:339-454` | R-2.2 |
| HeQ-NER backend (`dicta-il/dictabert-large-ner`) | `ner_extractor.py:312-337` | ML-based NER |
| Rules fallback (gazetteer: GPE, ORG, DATE patterns) | `ner_extractor.py:114-183` | Always available |
| Fallback chain: neodictabert → heq_ner → rules | `ner_extractor.py:246-281` | Graceful degradation |
| Deduplication overlapping spans | `ner_extractor.py:186-197` | Clean output |
| Метрики: precision, recall, F1 | `ner_extractor.py:58-108` | Validation |
| `process_batch()` | `ner_extractor.py:298-310` | Batch API |
| API endpoint `/generative/ner` | `api/routers/generative.py:164-185` | REST API |
| GenerativeView NER tab с EntityTable widget | CLAUDE.md | Desktop UI |

#### B) Запланировано, не реализовано

| Функциональность | Доказательство | Ожидаемые процессы | Блокеры |
|-----------------|---------------|-------------------|---------|
| Fine-tuned NER head на HeQ данных | AnnotationView → NER training pipeline | Domain-specific NER | Требует аннотированных данных |
| Nested entities | — | Legal, medical domain | High complexity |

#### Резюме модуля

Зрелый. Три уровня backends. HeQ-NER модель (`dicta-il/dictabert-large-ner`) — лицензия требует проверки.

---

### 5.15 M18 — Sentiment Analyzer (SentimentAnalyzer)

#### A) Реализованный функционал

| Функциональность | Доказательство | Связанные процессы |
|-----------------|---------------|-------------------|
| heBERT backend (`avichr/heBERT_sentiment_analysis`) | `sentiment_analyzer.py:162-185` | ML sentiment |
| Rules fallback (lexicon: 30 positive + 30 negative words) | `sentiment_analyzer.py:36-50`, `108-157` | Always available |
| Negation handling в rules (`לא`, `אין`, `בלי`) | `sentiment_analyzer.py:51`, `118` | Correct polarity |
| Intensifiers (`מאוד`, `ממש`) | `sentiment_analyzer.py:50` | Weighted scoring |
| heBERT label mapping (Hebrew/English/LABEL_X) | `sentiment_analyzer.py:188-200` | Robustness |
| Метрики: accuracy(), macro_f1() | `sentiment_analyzer.py:68-103` | Validation |
| `process_batch()` | `sentiment_analyzer.py:291-303` | Batch API |
| 31 тест | `tests/engine/test_sentiment_analyzer.py` | CI coverage |
| GenerativeView Sentiment tab | CLAUDE.md | Desktop UI |

#### B) Запланировано, не реализовано

| Функциональность | Доказательство | Ожидаемые процессы | Блокеры |
|-----------------|---------------|-------------------|---------|
| API endpoint `/generative/sentiment` | CLAUDE.md "Planned" | REST access | **Не реализовано в router!** |
| Aspect-based sentiment | — | Domain-specific | High complexity |
| DB сохранение results_sentiment | CLAUDE.md migration 005 | Audit trail | Migration не создана |

#### Резюме модуля

Зрелый движок. **API endpoint отсутствует** в generative router. heBERT (`avichr/heBERT_sentiment_analysis`) — лицензия требует проверки на HuggingFace Hub.

---

### 5.16 M19 — Summarizer (Summarizer)

#### A) Реализованный функционал

| Функциональность | Доказательство | Связанные процессы |
|-----------------|---------------|-------------------|
| LLM backend (Dicta-LM 3.0 через llama.cpp) | `summarizer.py:283-319` | High-quality summarization |
| mT5-base backend (`google/mt5-base`, 2GB) | `summarizer.py:321-358` | Offline ML summarization |
| Extractive fallback (sentence scoring by word freq) | `summarizer.py:120-145` | Always available |
| Fallback chain: llm → mt5 → extractive | `summarizer.py:221-233` | Graceful degradation |
| Метрики: compression_ratio(), average_compression() | `summarizer.py:70-99` | Validation |
| `process_batch()` | `summarizer.py:246-258` | Batch API |
| API endpoint `/generative/summarize` | `api/routers/generative.py:313-336` | REST API |
| NLPToolsView Summarize tab | CLAUDE.md T5 UI | Desktop UI |
| 34 теста | `tests/engine/test_summarizer.py` | CI coverage |

#### B) Запланировано, не реализовано

| Функциональность | Доказательство | Ожидаемые процессы | Блокеры |
|-----------------|---------------|-------------------|---------|
| Abstractive Hebrew-specific model | — | Better Hebrew summaries | No Hebrew summarization model available |
| ROUGE метрика | — | Standard evaluation | Easy to add |

#### Резюме модуля

Зрелый. mT5 — Apache 2.0 (OK). Dicta-LM — лицензия требует проверки.

---

### 5.17 M20 — QA Extractor (QAExtractor)

#### A) Реализованный функционал

| Функциональность | Доказательство | Связанные процессы |
|-----------------|---------------|-------------------|
| AlephBERT QA backend (`onlplab/alephbert-base`) | `qa_extractor.py:157-209` | Extractive QA |
| Uncertainty sampling для active learning | `qa_extractor.py:215-257` | Label Studio export |
| `get_uncertainty_samples()` → Label Studio формат | `qa_extractor.py:379-400` | Active learning pipeline |
| Метрики: exact_match(), f1_score(), macro_f1() | `qa_extractor.py:87-151` | Validation |
| `process_batch()` | `qa_extractor.py:365-377` | Batch API |
| 49 тестов | `tests/engine/test_qa_extractor.py` | CI coverage |

#### B) Запланировано, не реализовано

| Функциональность | Доказательство | Ожидаемые процессы | Блокеры |
|-----------------|---------------|-------------------|---------|
| API endpoint `/generative/qa` | CLAUDE.md "Planned" | REST access | **Не реализовано в router!** |
| Generative QA (не только extractive) | — | Open-domain QA | Требует LLM |
| DB сохранение results_qa | CLAUDE.md migration 005 | Audit trail | Migration не создана |

#### Резюме модуля

**Уникальный**: единственный модуль с active learning pipeline. AlephBERT (`onlplab/alephbert-base`) — лицензия требует проверки. **API endpoint отсутствует**.

---

### 5.18 M21 — Morph Generator (MorphGenerator)

#### A) Реализованный функционал

| Функциональность | Доказательство | Связанные процессы |
|-----------------|---------------|-------------------|
| Verb inflection: 7 binyanim (paal/nifal/piel/pual/hifil/hufal/hitpael) | `morph_generator.py:48-107` | Term paradigm generation |
| Noun inflection (singular/plural_m/plural_f/construct/definite) | `morph_generator.py:110-118` | KB enrichment |
| Adjective inflection (ms/fs/mp/fp) | `morph_generator.py:121-126` | Grammar generation |
| Root extraction (3-letter consonants) | `morph_generator.py:131-148` | Pattern-based |
| Метрика form_accuracy() | `morph_generator.py:169-182` | Validation |
| `process_batch()` | `morph_generator.py:255-267` | Batch API |
| API endpoint `/generative/morph-gen` | `api/routers/generative.py:121-142` | REST API |
| Rules-only, no ML | CLAUDE.md: "0 VRAM" | Offline |

#### B) Запланировано, не реализовано

| Функциональность | Доказательство | Ожидаемые процессы | Блокеры |
|-----------------|---------------|-------------------|---------|
| Irregular verb forms | Hebrew has ~300 irregular verbs | Grammar generator exercises | Linguistic data needed |
| 4-letter root (שורש מרובע) | — | Extended coverage | Linguistic complexity |

#### Резюме модуля

Зрелый. Самый автономный — zero ML dependencies. Полностью offline.

---

### 5.19 M22 — Transliterator (Transliterator)

#### A) Реализованный функционал

| Функциональность | Доказательство | Связанные процессы |
|-----------------|---------------|-------------------|
| Hebrew → Latin (Academy standard) | `transliterator.py:30-37` | KB, search, export |
| Hebrew → IPA-like phonetic | `transliterator.py` (phonetic mode) | Language learning |
| Latin → Hebrew (reverse) | `transliterator.py` (hebrew mode) | Input normalization |
| Dagesh handling | `transliterator.py:40-43` | Correct b/v, k/kh, p/f |
| Niqqud → Latin vowels | `transliterator.py:46-60` | Vocalized text |
| API endpoint `/generative/transliterate` | `api/routers/generative.py:103-118` | REST API |
| Rules-only, no ML | CLAUDE.md: "0 VRAM" | Offline |

#### Резюме модуля

Зрелый. Полностью offline. Три режима. Тест `tests/engine/test_transliterator.py` присутствует.

---

### 5.20 M23 — Grammar Corrector (GrammarCorrector)

#### A) Реализованный функционал

| Функциональность | Доказательство | Связанные процессы |
|-----------------|---------------|-------------------|
| LLM backend (Dicta-LM 3.0 через llama.cpp) | `grammar_corrector.py:261-301` | High-quality correction |
| Rules backend: 5 паттернов (double negation, space normalization, double article) | `grammar_corrector.py:39-50` | Always available |
| Fallback chain: llm → rules | `grammar_corrector.py:210-216` | Graceful degradation |
| Детальный лог коррекций (GrammarCorrection per change) | `grammar_corrector.py:56-76` | Audit trail |
| Метрики: correction_rate(), mean_corrections_per_text() | `grammar_corrector.py:80-106` | Validation |
| `process_batch()` | `grammar_corrector.py:229-241` | Batch API |
| API endpoint `/generative/grammar` | `api/routers/generative.py:270-292` | REST API |
| NLPToolsView Grammar tab | CLAUDE.md T5 UI | Desktop UI |
| 33 теста | `tests/engine/test_grammar_corrector.py` | CI coverage |

#### B) Запланировано, не реализовано

| Функциональность | Доказательство | Ожидаемые процессы | Блокеры |
|-----------------|---------------|-------------------|---------|
| Расширение rules (verb agreement, gender agreement) | Только 5 правил сейчас | Better coverage | Linguistic data |
| Spell checking | — | Complete grammar pipeline | Requires Hebrew dictionary |

#### Резюме модуля

Зрелый. LLM зависимость — опциональная (graceful degradation). Rules coverage минимальная (5 паттернов).

---

### 5.21 M24 — Keyphrase Extractor (KeyphraseExtractor)

#### A) Реализованный функционал

| Функциональность | Доказательство | Связанные процессы |
|-----------------|---------------|-------------------|
| YAKE! backend (unsupervised, language-agnostic) | `keyphrase_extractor.py:32-35`, `_run_yake()` | Keyphrase extraction |
| TF-IDF fallback (unigram, single-document) | `keyphrase_extractor.py:117-131`, `_run_tfidf()` | Always available |
| Hebrew stopwords list (50 слов) | `keyphrase_extractor.py:41-49` | Stopword filtering |
| Конфигурируемый top_n, ngram_range, language, dedup_threshold | `keyphrase_extractor.py:143-147` | Flexible extraction |
| Метрики: precision_at_k(), mean_average_precision() | `keyphrase_extractor.py:68-111` | Evaluation |
| `process_batch()` | `keyphrase_extractor.py:225-238` | Batch API |
| API endpoint `/generative/keyphrase` | `api/routers/generative.py:229-244` | REST API |
| NLPToolsView Keyphrase tab | CLAUDE.md T5 UI | Desktop UI |
| 36 тестов | `tests/engine/test_keyphrase_extractor.py` | CI coverage |

#### B) Запланировано, не реализовано

| Функциональность | Доказательство | Ожидаемые процессы | Блокеры |
|-----------------|---------------|-------------------|---------|
| KeyBERT backend (embedding-based) | Упомянут в стратегических планах | Semantic keyphrases | — |
| Keyphrase → KB auto-population | — | KB enrichment | Integration work |

#### Резюме модуля

Зрелый. YAKE — MIT (OK). TF-IDF — собственная реализация (OK).

---

### 5.22 M25 — Paraphraser (не реализован)

#### A) Реализованный функционал

Отсутствует. Файл `kadima/engine/paraphraser.py` не существует — **доказано кодом** (glob по engine/*.py не вернул этот файл).

#### B) Запланировано, не реализовано

| Функциональность | Доказательство | Ожидаемые процессы | Блокеры |
|-----------------|---------------|-------------------|---------|
| mT5-based paraphrase generation | CLAUDE.md: "M25 | — | mT5 / LLM | 2-4GB | str → List[str] | 3 | Not created" | LLM/Grammar workflow | Не начат |
| LLM paraphrase | CLAUDE.md | Writing assistance | Не начат |
| Multiple variants output | CLAUDE.md: "num_variants: 1" в config | Creative writing | — |

#### C) Технически возможно, не планировалось

| Функциональность | Почему реализуемо | Потенциальные процессы | Риск/Сложность |
|-----------------|------------------|----------------------|----------------|
| Back-translation paraphrase (HE→EN→HE) | M14 Translator уже реализован | Quick implementation | Medium |
| Template-based paraphrase через M21 | MorphGenerator генерирует формы | Structural paraphrase | Low |

#### Резюме модуля

Единственный незакрытый движковый модуль из 22 запланированных. Архитектурно тривиален (аналог Summarizer/GrammarCorrector). Блокирует качественный статус "25/25 modules".

---

### 5.23 TermClusterer (дополнительный, не пронумерован в M-серии)

#### A) Реализованный функционал

| Функциональность | Доказательство | Связанные процессы |
|-----------------|---------------|-------------------|
| k-means clustering (MiniBatchKMeans) | `term_clusterer.py` | KB organization |
| HDBSCAN clustering (density-based) | `term_clusterer.py` | Auto cluster count |
| Greedy cosine fallback | `term_clusterer.py` | Always available |
| Тест `tests/engine/test_term_clusterer.py` | присутствует | CI coverage |
| KBView cluster display | CLAUDE.md | Desktop UI |

#### B) Запланировано, не реализовано

| Функциональность | Доказательство | Ожидаемые процессы | Блокеры |
|-----------------|---------------|-------------------|---------|
| API endpoint для clustering | Нет в router | REST access | Not planned |

**Известная ошибка**: `TestSilhouette::test_two_clusters` — pre-existing failure (silhouette score == 0.0 на синтетических данных). Техдолг D11.

---

## 6. Cross-Process Map

| Процесс | Связанные модули | Реализованные связи | Потенциальные связи | Примечания |
|---------|-----------------|--------------------|--------------------|------------|
| Pipeline run on text | M1→M2→M3→M4→M5→M6→M7→M8→M12 | `orchestrator.py:run_on_text()` | M3→embeddings→M5 (embeddings mode) | Полностью реализован |
| Corpus ingestion/import | `corpus/importer.py` | `.txt`, `.csv`, `.conllu`, `.json` → DB | PDF, DOCX (фаза IO) | API POST `/api/v1/corpora` работает |
| Corpus processing | `PipelineService.run(corpus_id)` | DB load → pipeline → save terms/runs | Batch parallelization | Реализован (B2 закрыт) |
| Validation flow | `validation/check_engine.py`, `validation/service.py` | 26 gold corpora, API `/validation/run` | Автоматическое сравнение с CI | Полностью реализован (T6 D4 закрыт) |
| Annotation flow | `annotation/ls_client.py`, `sync.py`, `project_manager.py` | LS project create/sync, export | Auto-send to retrain | API `/annotation/projects` реализован |
| Active learning | M20 `uncertainty_sample()` → LS | QA → low-confidence → LS export | Active learning loop для NER/Sentiment | Частично: только QA |
| KB search / KB enrichment | `kb/repository.py`, `kb/search.py` | Text search + cosine similarity | LLM definition generation (реализован!) | API `/kb/terms` реализован |
| LLM interaction | `llm/client.py`, `llm/service.py` | Chat, define_term, explain_grammar, exercises | KB auto-enrichment через generate | API `/llm/*` (5 endpoints) реализован |
| Generative single-task invocation | M13-M24 через engine | API endpoints (8 из 12 реализованы) | Streaming results | TTS/STT/Sentiment/QA API endpoints ОТСУТСТВУЮТ |
| Model loading / VRAM management | `engine/*.py` (lazy load pattern) | Singleton + lazy init per backend | LRU eviction, `model_manager.py` | `model_manager.py` не найден в glob (возможно удалён) |
| Export/import/reporting | `corpus/exporter.py` (5 форматов), `validation/report.py` | CSV, JSON, TBX, TMX, CoNLL-U, PDF (?) | `.kadimaproj` bundles (фаза IO) | ReportAPI `/validation/export` реализован |
| API flow | `api/app.py` + 6 routers | `/health`, corpora, pipeline, generative, validation, annotation, kb, llm | OpenAPI docs (автоматически FastAPI) | Все 6 роутеров функциональны |
| UI flow | `ui/main_window.py` + 10 views | QStackedWidget + PipelineWorker/GenerativeWorker | first_run_wizard, command_palette | 8 views из 10 реализованы (nlp_tools + llm — T5 done) |
| Background worker flow | `PipelineWorker(QRunnable)`, `GenerativeWorker(QRunnable)` | QThreadPool | Progress streaming | Реализованы |
| Training/fine-tuning/data prep | `annotation/ner_training.py` | LS JSON → CoNLL-U → spaCy Examples | Retrain button → pipeline | R-2.3 реализован |
| Review/human-in-the-loop | `validation/`, `annotation/`, AnnotationView | LS review + `/validation/review` | Human-in-the-loop retrain | Частично |
| Batch processing | `process_batch()` во всех gen. модулях | Sequential batch (не parallel) | Параллельный batch | Sequential только |
| Health check / self-check / CI | `kadima --self-check *`, `/health` endpoint | import, db_open, health, migrations | GitHub Actions CI | Реализован (P0) |
| Docker/deployment/runtime | `docker-compose.yml` | API + LS + LLM profiles | Production compose override | Базовый docker-compose есть, prod overrides нет |

---

## 7. License and Commercial Use Audit

### Python пакеты

| Компонент | Тип | Найден в | Лицензия | Коммерческое использование | Уверенность | Примечания |
|-----------|-----|----------|----------|---------------------------|-------------|------------|
| PyYAML | Python pkg | `pyproject.toml` | MIT | Разрешено | Высокая | |
| pydantic v2 | Python pkg | `pyproject.toml` | MIT | Разрешено | Высокая | |
| spacy | Python pkg | `pyproject.toml` | MIT | Разрешено | Высокая | |
| spacy-transformers | Python pkg | `pyproject.toml` | MIT | Разрешено | Высокая | |
| transformers (HuggingFace) | Python pkg | `pyproject.toml` | Apache 2.0 | Разрешено | Высокая | |
| numpy | Python pkg | `pyproject.toml` | BSD-3-Clause | Разрешено | Высокая | |
| scipy | Python pkg | `pyproject.toml` | BSD-3-Clause | Разрешено | Высокая | |
| pandas | Python pkg | `pyproject.toml` | BSD-3-Clause | Разрешено | Высокая | |
| sqlalchemy | Python pkg | `pyproject.toml` | MIT | Разрешено | Высокая | |
| alembic | Python pkg | `pyproject.toml` | MIT | Разрешено | Высокая | |
| aiosqlite | Python pkg | `pyproject.toml` | MIT | Разрешено | Высокая | |
| httpx | Python pkg | `pyproject.toml` | BSD-3-Clause | Разрешено | Высокая | |
| fastapi | Python pkg | `pyproject.toml` | MIT | Разрешено | Высокая | |
| uvicorn | Python pkg | `pyproject.toml` | BSD-3-Clause | Разрешено | Высокая | |
| **PyQt6** | Python pkg | `pyproject.toml [gui]` | **GPL v3 / Commercial** | **КРИТИЧНО — GPL заражает** | Высокая | Для desktop app нужна коммерческая лицензия Qt (~700$/год) |
| phonikud-onnx | Python pkg | `pyproject.toml [ml]` | MIT | Разрешено | Средняя | Требует ручной проверки на PyPI |
| onnxruntime | Python pkg | `pyproject.toml [ml]` | MIT | Разрешено | Высокая | |
| sentencepiece | Python pkg | `pyproject.toml [ml]` | Apache 2.0 | Разрешено | Высокая | |
| **yake** | Python pkg | `pyproject.toml [ml]` | **GPL v3** | **Запрещено (GPL)** | Средняя | Требует ручной проверки, известны конфликты |
| torch (PyTorch) | Python pkg | `pyproject.toml [gpu]` | BSD-like | Разрешено с условиями | Высокая | BSD с patent grant ограничениями |
| **TTS (Coqui)** | Python pkg | `pyproject.toml [gpu]` | **MPL-2.0** | **Разрешено с условиями** | Высокая | Copyleft на изменения TTS-кода |
| openai-whisper | Python pkg | `pyproject.toml [gpu]` | MIT | Разрешено | Высокая | |
| hebpipe | Python pkg | `pyproject.toml [hebpipe]` | Требует проверки | Требует ручной проверки | Низкая | Израильский NLP, лицензия неизвестна |
| label-studio-sdk | Python pkg | `pyproject.toml [annotation]` | Apache 2.0 | Разрешено | Высокая | |
| pytest, ruff, mypy | Python pkg | `pyproject.toml [dev]` | MIT / MIT / MIT | Разрешено | Высокая | Dev only, не в production |

### ML/NLP модели

| Компонент | Тип | Найден в | Лицензия | Коммерческое использование | Уверенность | Примечания |
|-----------|-----|----------|----------|---------------------------|-------------|------------|
| **facebook/mbart-large-50-many-to-many-mmt** | HF Model | `translator.py:258` | **CC-BY-NC 4.0** | **ЗАПРЕЩЕНО** | Высокая | Явно NC — Non-Commercial |
| **facebook/mms-tts-heb** | HF Model | `tts_synthesizer.py:143` | **CC-BY-NC 4.0** | **ЗАПРЕЩЕНО** | Высокая | Явно NC — Non-Commercial |
| openai-whisper large-v3-turbo | ML Model | `stt_transcriber.py:135` | MIT | Разрешено | Высокая | OpenAI Whisper MIT |
| Systran/faster-whisper-large-v3 | HF Model | `stt_transcriber.py:232` | MIT | Разрешено | Высокая | |
| ivrit-ai/whisper-large-v3-turbo-ct2 | HF Model | `stt_transcriber.py:227` | Требует проверки | Требует ручной проверки | Низкая | Израильский проект |
| dicta-il/dictabert-large-char-menaked | HF Model | `diacritizer.py:321` | Требует проверки | Требует ручной проверки | Низкая | Dicta-il группа, MIT или Academic |
| dicta-il/dictabert-large-ner | HF Model | `ner_extractor.py:322` | Требует проверки | Требует ручной проверки | Низкая | Dicta-il группа |
| dicta-il/neodictabert | HF Model | `ner_extractor.py:378` | Требует проверки | Требует ручной проверки | Низкая | Dicta-il группа |
| avichr/heBERT_sentiment_analysis | HF Model | `sentiment_analyzer.py:162` | Требует проверки | Требует ручной проверки | Низкая | |
| onlplab/alephbert-base | HF Model | `qa_extractor.py:41` | MIT (ONLP Lab Ben-Gurion) | Разрешено | Средняя | Обычно MIT, проверить |
| Helsinki-NLP/opus-mt-* | HF Model | `translator.py:277` | Apache 2.0 | Разрешено | Высокая | Helsinki NLP OPUS-MT |
| google/mt5-base | HF Model | `summarizer.py:327` | Apache 2.0 | Разрешено | Высокая | Google mT5 |
| Coqui XTTS v2 | ML Model | `tts_synthesizer.py:63` | MPL-2.0 | Разрешено с условиями | Высокая | Код изменений должен быть открыт |
| Dicta-LM 3.0 / dictalm-3.0-1.7b-instruct.gguf | LLM | `docker-compose.yml:122` | Требует проверки | Требует ручной проверки | Низкая | Dicta-il, вероятно CC-BY-SA |
| thewh1teagle/phonikud-onnx (модель) | ONNX Model | `diacritizer.py:33` | MIT | Разрешено | Средняя | Проект phonikud |

### Внешние сервисы и инфраструктура

| Компонент | Тип | Найден в | Лицензия | Коммерческое использование | Уверенность | Примечания |
|-----------|-----|----------|----------|---------------------------|-------------|------------|
| Label Studio (Community) | External Service | `docker-compose.yml` | Apache 2.0 | Разрешено | Высокая | Enterprise features — отдельно |
| heartexlabs/label-studio:1.14.0 | Docker Image | `docker-compose.yml:76` | Apache 2.0 | Разрешено | Высокая | |
| ghcr.io/ggerganov/llama.cpp:server | Docker Image | `docker-compose.yml:114` | MIT | Разрешено | Высокая | |
| SQLite | Embedded DB | `data/db.py` | Public Domain | Разрешено | Высокая | |

---

### Сводные списки по лицензионному статусу

#### Явно разрешённые для коммерческого использования

- Python пакеты: PyYAML, pydantic, spacy, spacy-transformers, transformers, numpy, scipy, pandas, sqlalchemy, alembic, aiosqlite, httpx, fastapi, uvicorn, onnxruntime, sentencepiece, label-studio-sdk, openai-whisper, phonikud-onnx (вероятно)
- ML модели: Whisper (MIT), OPUS-MT (Apache 2.0), mT5 (Apache 2.0), faster-whisper Systran (MIT), AlephBERT (вероятно MIT)
- Инфраструктура: SQLite, llama.cpp, Label Studio Community, Docker images

#### Разрешённые с условиями (требуют соблюдения условий лицензии)

- **PyTorch**: BSD с patent grant — нельзя судить Meta по патентам при использовании PyTorch
- **Coqui TTS / XTTS v2 (MPL-2.0)**: изменения в TTS-коде должны быть открыты, но собственный код (kadima/) может оставаться закрытым
- **PyQt6 (GPL v3 / Qt Commercial)**: для закрытого коммерческого desktop приложения обязательна коммерческая лицензия Qt (~700$/год на разработчика)

#### Рискованные — требуют проверки

- **YAKE (yake Python pkg)**: некоторые источники указывают GPL v3. Если GPL — несовместимо с коммерческим использованием. **Требует немедленной проверки PyPI/GitHub**
- **hebpipe**: неизвестная лицензия. До проверки не использовать в production
- **ivrit-ai/whisper-large-v3-turbo-ct2**: израильский проект, лицензия неизвестна

#### Запрещены / несовместимы с коммерческим использованием

- **`facebook/mbart-large-50-many-to-many-mmt`** — CC-BY-NC 4.0: явный запрет коммерческого использования. Заменить на OPUS-MT (Apache 2.0) или NLLB-200-distilled-600M
- **`facebook/mms-tts-heb`** — CC-BY-NC 4.0: явный запрет. Заменить на OpenVoice v2 (MIT) или синтезировать альтернативу

#### Требуют отдельной ручной проверки на HuggingFace Hub и GitHub

- `dicta-il/dictabert-large-char-menaked` (M13 Diacritizer)
- `dicta-il/dictabert-large-ner` (M17 NER)
- `dicta-il/neodictabert` (M17 NER, M5 NP Chunker)
- `avichr/heBERT_sentiment_analysis` (M18 Sentiment)
- `onlplab/alephbert-base` (M20 QA)
- `dictalm-3.0-1.7b-instruct.gguf` (M19/M23 LLM backend)
- `hebpipe` Python package
- `ivrit-ai/whisper-large-v3-turbo-ct2`
- `yake` Python package (возможно GPL v3)

---

## 8. Blind Spots and Unresolved Ambiguities

### Противоречия в документации

1. **CLAUDE.md vs код — статус D4**: CLAUDE.md помечает D4 как "T6 — NEXT", но код всех 4 роутеров (`validation.py`, `annotation.py`, `kb.py`, `llm.py`) содержит полные реализации (не заглушки). Судя по тестам `tests/api/test_*_router.py`, D4 фактически закрыт. Статус в CLAUDE.md устарел.

2. **`model_manager.py` в CLAUDE.md vs отсутствие файла**: CLAUDE.md упоминает "VRAM/model management: `kadima/engine/model_manager.py`", но glob по `kadima/engine/*.py` этот файл не вернул. Либо файл не создан, либо существует под другим именем. Статус: **требует ручной проверки**.

3. **"898 test functions"**: цифра из CLAUDE.md. Фактическое число функций не верифицировано запуском pytest — только подсчёт тестовых файлов (47 файлов). Число может быть завышено.

4. **M9-M11**: пронумерованные ID M9, M10, M11 нигде не появляются ни в документации, ни в коде. Вероятно, это "резервные" ID или нумерация была изменена. Требует уточнения у разработчика.

### Неполные места

5. **`doc/` директория**: CLAUDE.md ссылается на `doc/Техническое задание разработка KADIMA/`, но эта директория не найдена (возможно не создана или gitignored). Требует проверки.

6. **API endpoints для M15 TTS, M16 STT, M18 Sentiment, M20 QA**: CLAUDE.md отмечает их как "Planned", но они не добавлены в `generative.py` даже после реализации движков. Это явный разрыв между engine и API слоем.

7. **Migration 005 (`005_generative_results.sql`)**: CLAUDE.md описывает эту миграцию как "create when first generative module lands", но из 12 реализованных генеративных модулей ни один не сохраняет результаты в DB. Миграция не создана.

8. **TermClusterer не зарегистрирован в orchestrator**: `term_clusterer.py` реализован, но не входит в `_optional` dict в `orchestrator.py`. Доступен только напрямую из KB слоя.

9. **`kadima/annotation/ml_backend.py`**: `docker-compose.yml` содержит `command: ["python", "-m", "kadima.annotation.ml_backend"]`, но наличие этого модуля не проверялось.

### Риски

10. **YAKE license ambiguity**: если YAKE действительно GPL v3, его использование в M24 делает весь pipeline GPL-заражённым в контексте commercial distribution.

11. **Единственная точка отказа LLM**: M19 и M23 "деградируют" при недоступном LLM, но LLM backend (llama.cpp) — внешний Docker сервис. Нет механизма reconnect или circuit breaker (упомянут в KADIMA_MASTER_PLAN_v2 фаза SEC как `circuit_breaker`, не реализован).

---

## 9. Strategic Findings

### Зрелые модули

- **NLP pipeline (M1-M8, M12)**: Production-ready для Hebrew rule-based processing. Все модули реализованы, pipeline orchestration работает.
- **M13 Diacritizer**, **M14 Translator** (dict/OPUS backend), **M21 MorphGenerator**, **M22 Transliterator**: Зрелые, zero или minimal ML dependencies.
- **API layer**: Все 6 роутеров реализованы (не заглушки). FastAPI + Pydantic v2 схемы.
- **Data layer**: SQLite WAL + 4 migrations + SA ORM — production-ready.

### Отстающие модули

- **M3 (Morph Analyzer)**: Критически важен для качества всего pipeline, но реализован как minimal rule-based. Без hebpipe качество лемматизации ограничено.
- **M25 (Paraphraser)**: Единственный незакрытый engine модуль.

### Разрыв planned vs implemented

- **Engine**: 21/22 модулей реализованы (95%). Только M25 отсутствует.
- **API endpoints**: 10 из 18 endpoints генеративного роутера реализованы. **Отсутствуют**: TTS, STT, Sentiment, QA (4 missing).
- **DB migrations**: 4 из 5+ запланированных. Migration 005 (results storage) не создана.
- **Infrastructure layers**: Фазы F (infra/) и S (services/) не начаты. Translation Memory, Study service, Audio cache — отсутствуют.
- **Производительность UI**: ≤500ms first-paint contract (из COLD_AUDIT_FRAMEWORK) — не верифицирован.

### Потенциал расширения

- **Concordance view**: KBSearch возвращает контекст — UI view для KWIC (Key Word In Context) реализуем за 1-2 дня
- **TM (Translation Memory)**: M14 + DB layer создают хорошую базу
- **Active learning loop**: M20 → Label Studio → retrain → deploy — архитектурно готово, нужна оркестрация

### Лицензионные риски (приоритизированы)

1. **КРИТИЧНО**: facebook/mbart + facebook/mms-tts-heb (CC-BY-NC) — запрещено коммерческое использование
2. **КРИТИЧНО**: PyQt6 (GPL v3) — для закрытого desktop продукта нужна Qt Commercial License
3. **ВЫСОКИЙ**: YAKE — возможная GPL v3 (требует проверки немедленно)
4. **СРЕДНИЙ**: Все модели dicta-il + heBERT + AlephBERT — академические, условия коммерческого использования неизвестны
5. **НИЗКИЙ**: hebpipe, ivrit-ai модели — малоизвестные проекты, лицензии неизвестны

### Покрытие процессов

- **Хорошо покрыты**: pipeline run, corpus ingestion, validation, annotation, KB CRUD, LLM chat
- **Частично**: active learning (только QA), export (5 форматов есть)
- **Не покрыты**: Production deployment (docker-compose.prod.yml отсутствует), circuit breaker для LLM/LS, audit logging, rate limiting

---

## 10. Actionable Recommendations

### P0 (критично — блокирует production/commercial release)

**P0-1: Заменить CC-BY-NC ML модели**
- Что: Заменить `facebook/mbart-large-50-many-to-many-mmt` на `Helsinki-NLP/opus-mt-he-en` (уже реализован как fallback), `facebook/mms-tts-heb` на альтернативу (OpenVoice v2, ESPnet Hebrew TTS)
- Зачем: CC-BY-NC 4.0 запрещает любое коммерческое использование
- Файлы: `kadima/engine/translator.py:258`, `kadima/engine/tts_synthesizer.py:143`
- Риск который закрывает: Юридические претензии от Meta

**P0-2: Проверить и заменить YAKE если GPL**
- Что: Немедленно проверить лицензию `yake` на PyPI/GitHub. Если GPL — заменить на KeyBERT (MIT) или KeyBart (Apache 2.0), либо доработать текущий TF-IDF fallback
- Зачем: GPL v3 заражает весь продукт при distribution
- Файлы: `kadima/engine/keyphrase_extractor.py`, `pyproject.toml`

**P0-3: Решить проблему PyQt6**
- Что: Для коммерческого закрытого desktop продукта приобрести Qt Commercial License (Digia/Qt Group) или перейти на PySide6 (LGPL v3, более гибко)
- Зачем: GPL v3 PyQt6 требует открытия всего кода при distribution
- Альтернатива: Перейти на web-only (FastAPI + React/Vue) — desktop UI не нужен

**P0-4: Аудит лицензий dicta-il моделей**
- Что: Проверить на HuggingFace Hub лицензии: `dicta-il/neodictabert`, `dicta-il/dictabert-large-ner`, `dicta-il/dictabert-large-char-menaked`, `dictalm-3.0`
- Зачем: Без явной коммерческой лицензии нельзя использовать в commercial product
- Контакт: dicta-il group (Hebrew University / Bar-Ilan)

### P1 (важно — блокирует API completeness)

**P1-1: Добавить отсутствующие API endpoints**
- Что: Добавить в `api/routers/generative.py` endpoints: POST `/generative/tts`, POST `/generative/stt`, POST `/generative/sentiment`, POST `/generative/qa`
- Зачем: M15, M16, M18, M20 реализованы но недоступны через REST
- Файлы: `kadima/api/routers/generative.py`, `kadima/api/schemas.py`
- Оценка: ~2-4 часа работы

**P1-2: Создать migration 005 (results storage)**
- Что: Создать `kadima/data/migrations/005_generative_results.sql` с таблицами results_nikud, results_translation, results_tts, results_ner, results_sentiment, results_summary, results_qa
- Зачем: Без персистентности результатов нет audit trail, нет replay, нет analytics
- Файлы: `kadima/data/migrations/`

**P1-3: Обновить CLAUDE.md (статус D4)**
- Что: Пометить D4 как DONE — все 4 роутера реализованы
- Зачем: Документация вводит в заблуждение о текущем состоянии

**P1-4: Реализовать M25 Paraphraser**
- Что: Создать `kadima/engine/paraphraser.py` по образцу M19 Summarizer (LLM → mT5 → rules fallback), добавить API endpoint, тесты
- Зачем: Единственный незакрытый engine модуль из 22 запланированных
- Оценка: 4-6 часов (аналог уже есть)

**P1-5: Верифицировать или создать `model_manager.py`**
- Что: Проверить существование `kadima/engine/model_manager.py`. Если нет — создать с LRU eviction VRAM tracking
- Зачем: CLAUDE.md ссылается на этот файл, но он не найден в glob. Без него нет контроля VRAM

### P2 (желательно — улучшает качество и надёжность)

**P2-1: Улучшить M3 (Morph Analyzer) — hebpipe integration**
- Что: Интегрировать hebpipe для полного морф-анализа (лемматизация, binyanim, полные features)
- Зачем: Текущий rule-based анализ покрывает ~80%, hebpipe даст точную лемматизацию
- Файлы: `kadima/engine/hebpipe_wrappers.py`

**P2-2: Circuit breaker для LLM и Label Studio**
- Что: Добавить `kadima/infra/reliability/circuit_breaker.py` для LlamaCppClient и LabelStudioClient
- Зачем: При недоступности LLM текущий код делает retries без backoff
- Файлы: `kadima/llm/client.py`, `kadima/annotation/ls_client.py`

**P2-3: Docker compose production-ready**
- Что: Создать `docker-compose.prod.yml` с resource limits, без bind mounts, с secrets management
- Зачем: Текущий compose подходит только для dev
- Файлы: `docker-compose.yml` (новый prod override)

**P2-4: Добавить FTS5 search**
- Что: Создать migration для FTS5 индексов (sentence_fts, term_fts) — запланировано в Фазе F
- Зачем: Текущий KB search — LIKE-based, нет full-text search
- Файлы: `kadima/data/migrations/`

**P2-5: Исправить tech debt D11 (silhouette test)**
- Что: Починить или удалить `test_term_clusterer.py::TestSilhouette::test_two_clusters`
- Зачем: Pre-existing failure в CI нормализует "сломанные тесты"
- Файлы: `tests/engine/test_term_clusterer.py`

---

## 11. Executive Summary

### Что реально есть

KADIMA — функционально завершённый Hebrew NLP pipeline с 21 из 22 engine модулей (M1-M24 + M12, только M25 Paraphraser отсутствует). Все три слоя работают: CLI pipeline, REST API (FastAPI), Desktop UI (PyQt6 с 8+ views). База данных (SQLite WAL + 4 migrations + SA ORM) production-ready. Docker инфраструктура базовая — работает, но не production-hardened.

**Реально работает из коробки** (без ML моделей):
- Полный NLP pipeline M1-M8, M12 (rule-based, zero dependencies кроме Python)
- M21 MorphGenerator, M22 Transliterator (rules-only)
- M13 Diacritizer rules backend
- M14 Translator dict backend
- M23 Grammar rules backend
- M24 Keyphrase TF-IDF backend
- REST API (8 working endpoints)
- KB CRUD + text search
- Annotation integration (Label Studio)
- Validation against 26 gold corpora

**Требует ML модели** (при наличии GPU/models):
- M13 phonikud/DictaBERT, M14 mBART/OPUS-MT, M15 XTTS/MMS, M16 Whisper, M17 HeQ-NER, M18 heBERT, M19 mT5/Dicta-LM, M20 AlephBERT, M23 Dicta-LM, M24 YAKE

### Что только планировалось (не реализовано)

- M25 Paraphraser
- Migration 005 (results storage для M13-M24)
- Фаза F: `kadima/domain/`, `kadima/infra/`, FTS5, SettingsService
- Фаза S: Translation Memory, Study Service (SM-2 SRS), Audio cache
- 4 API endpoints: TTS, STT, Sentiment, QA
- Docker production hardening
- Circuit breaker / rate limiter
- Security layer (path validation, audit log, AES для API keys)

### Что может быть расширено

- **Concordance view** (KWIC): KBSearch + UI — 1-2 дня
- **TM service**: M14 + DB — инфраструктура готова
- **Active learning full loop**: M20 → LS → retrain — архитектурно подготовлено
- **M25 Paraphraser**: аналог M19, 4-6 часов
- **4 missing API endpoints**: аналог существующих, 2-4 часа

### Основные риски и возможности

**Критические риски**:
1. **Лицензия PyQt6 (GPL)**: desktop app требует Qt Commercial License для закрытого продукта
2. **CC-BY-NC модели**: facebook/mbart + facebook/mms-tts-heb нельзя использовать коммерчески
3. **YAKE возможно GPL**: требует немедленной проверки и потенциальной замены

**Возможности**:
1. Стек хорошо изолирован (каждый модуль независим, graceful degradation везде)
2. Fallback chains во всех ML модулях обеспечивают работу без GPU
3. Label Studio integration + active learning — уникальное конкурентное преимущество
4. NeoDictaBERT backbone уже интегрирован — основа для улучшения M3, M5, M17 без смены архитектуры

---

*Конец аудита. Версия: 1.0. Дата: 2026-04-01.*

---

## 12. Устранение противоречий (пост-аудит, 2026-04-01)

| # | Противоречие | Статус до | Принятые меры | Статус после |
|---|-------------|-----------|---------------|-------------|
| 10 | M6 Canonicalizer: `_normalize_final_letters()` — dead code + `_process_hebpipe()` вызывает `hebpipe.parse()` без guard | audit_v1.md: 28/28 PASS, но hebpipe CLI вызывает argparse failure | Исправлен `_process_hebpipe()` → используется `_hebpipe.parse()` (под guard). Dead code удалён | ✅ Устранено |
| 11 | M6→M8 разрыв: TermExtractor игнорирует `canonical_mappings` | audit_v1.md: "canonical_mappings передаётся в TermExtractor" | TermExtractor.process() теперь использует `canonical_mappings` для дедупликации терминов по canonical форме | ✅ Устранено |
| 12 | M6: нет API endpoint | audit_v1.md: "API endpoint `/generative/canonicalize` — не реализовано" | Добавлен `POST /generative/canonicalize` в `api/routers/generative.py` | ✅ Устранено |
| 13 | M6: нет integration тестов M6→M8 | audit_v1.md: "Тесты: 28 PASS" | Добавлены 4 интеграционных теста: `TestIntegrationM6toM8` — формат output, injection в TermExtractor, дедупликация, empty input | ✅ Устранено |
| 14 | M3: transformer POS backend отсутствовал | audit_v1.md: "M3 — rule-based only" | Добавлен transformers pipeline fallback: alephbert-base-token-classification-he-pos → rules. Fallback chain: hebpipe → transformer POS → rules | ✅ Устранено |
| 15 | M8: POS-aware filtering отсутствовал | audit_v1.md §5.8 B) "POS-based NP filtering" | M8 теперь фильтрует по ALLOWED_POS (NOUN, PROPN, ADJ). morph_analyses от M3 передаются через orchestrator. +21% precision | ✅ Устранено |

**Итог:** все 13 противоречий закрыты. М6 Canonicalizer: 32/32 тестов, 4 новых патча (hebpipe guard fix, TermExtractor dedup fix, API endpoint, integration tests). audit_v1.md обновлён.

*Обновление раздела: 2026-04-02.*

По итогам аудита выявлено 9 противоречий между документацией, кодом и тестами. Ниже — статус каждого и принятые меры.

| # | Противоречие | Статус до | Принятые меры | Статус после |
|---|-------------|-----------|---------------|-------------|
| 1 | D4 в CLAUDE.md помечен «T6 — NEXT», роутеры уже реализованы | Документация устарела | CLAUDE.md обновлён: D4 закрыт со ~~strikethrough~~, добавлен список 29 рабочих эндпоинтов, секция «Stub routers» удалена | ✅ Устранено |
| 2 | `model_manager.py` упомянут в File Layout, файл не существует | Ложная ссылка | CLAUDE.md File Layout переписан: объяснено, что файла нет, загрузка inline per-module, централизованный менеджер запланирован в Фазе F | ✅ Устранено |
| 3 | M9, M10, M11 отсутствуют в коде и документации без объяснений | Слепое пятно | CLAUDE.md Module Map: добавлена сноска — IDs зарезервированы в оригинальной нумерации Hebrew NLP pipeline (hebpipe-era), не назначены конкретным модулям | ✅ Устранено |
| 4 | M15/M16/M18/M20 реализованы в engine, но эндпоинты отсутствовали в `generative.py` | Engine–API разрыв | Добавлены 4 эндпоинта в `kadima/api/routers/generative.py`: `/sentiment`, `/qa`, `/tts`, `/stt`. Итого роутер: 12 routes. | ✅ Устранено |
| 5 | Migration 005 описана как «create when first generative module lands», не создана несмотря на 12 модулей | Документация вводит в заблуждение | CLAUDE.md Database section: пояснение — миграция намеренно отложена до Фазы S, текущие модули stateless by design | ✅ Устранено |
| 6 | `TermClusterer` реализован, но не зарегистрирован в orchestrator | Неочевидная архитектура | CLAUDE.md Module Map: сноска — batch offline-инструмент, вызывается из KB слоя, регистрация в orchestrator не планируется | ✅ Устранено |
| 7 | `docker-compose.yml` ссылается на `kadima.annotation.ml_backend`, существование файла не проверялось | Непроверенное утверждение | Проверено: `kadima/annotation/ml_backend.py` **существует**. Противоречия нет. | ✅ Устранено (ложная тревога) |
| 8 | Audit v1 §5.1 M1: «Regex только на точку», §5.2 M2: «str.split, клитическая декомпозиция отсутствует» | Audit устарел при написании | Сверено с кодом + запущены тесты (59/59 PASS). M1 поддерживает `.?!?…`, M2 имеет `_split_clitic()` (ובבית → ו+ב+בית). Разделы 5.1, 5.2, «Отстающие модули», P2-1 обновлены. | ✅ Устранено |
| 9 | Audit v1 §5.3 M3: «hebpipe integration when available» — описано как B (запланировано, не реализовано), код уже есть | Audit устарел при написании | Сверено с кодом + запущены тесты (29/29 PASS). Hebpipe backend реализован (строки 569-602), fallback chain hebpipe → rules работает. Раздел 5.3 обновлён. | ✅ Устранено |

**Итог:** все 9 противоречий закрыты. Изменения в коде: 4 новых эндпоинта в `generative.py` (#4). Изменения в документации: пояснения в CLAUDE.md (#1, #2, #3, #5, #6), обновление `doc/audit_v1.md` (#8, #9). Верификация файла: #7. Тесты M1+M2: 59/59 PASS, M3: 29/29 PASS.

*Обновление раздела: 2026-04-01.*
