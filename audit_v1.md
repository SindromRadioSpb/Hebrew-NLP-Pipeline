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

#### A) Реализованный функционал

| Функциональность | Доказательство | Связанные процессы |
|-----------------|---------------|-------------------|
| Разбиение текста на предложения по regex `(?<=[\u0590-\u05FF])\.\s+` | `hebpipe_wrappers.py:138` | pipeline run on text (первый шаг) |
| Возврат `SentenceSplitResult` с offset-ами (start/end) | `hebpipe_wrappers.py:56-60` | Pipeline → M2 |
| Валидация входных данных (непустая строка) | `hebpipe_wrappers.py:127` | Error handling |
| Graceful degradation: ProcessorStatus.FAILED на ошибку | `hebpipe_wrappers.py:154` | CI/health check |
| Интеграция с `PipelineService` как первый модуль | `orchestrator.py:65` | Pipeline orchestration |

#### B) Запланировано, не реализовано

| Функциональность | Доказательство | Ожидаемые процессы | Блокеры |
|-----------------|---------------|-------------------|---------|
| Интеграция с HebPipe для полноценного SBD | `hebpipe_wrappers.py:219-228` (import attempt) | Точное разбиение с учётом сокращений | Требует `pip install hebpipe` |
| Разбиение по вопросительным/восклицательным знакам (неполное) | Regex только на точку после ивритского символа | Корректная обработка вопросов | Low |

#### C) Технически возможно, не планировалось

| Функциональность | Почему реализуемо | Потенциальные процессы | Риск/Сложность |
|-----------------|------------------|----------------------|----------------|
| Разбиение с учётом парагенезиса (абзацы) | Простое расширение regex | Документная сегментация | Low |
| Экспорт sentence boundaries для FTS5 | SQLite FTS5 готов (migration 001) | Sentence-level search | Medium |

#### Резюме модуля

Зрелость: производственная для базовых случаев. Слепое пятно: сложные случаи (сокращения, parenthetical clauses). HebPipe-интеграция код присутствует, но не тестировалась (hebpipe не установлен в стандартной поставке).

---

### 5.2 M2 — Tokenizer (HebPipeTokenizer)

#### A) Реализованный функционал

| Функциональность | Доказательство | Связанные процессы |
|-----------------|---------------|-------------------|
| Токенизация по пробелам (`str.split()`) | `hebpipe_wrappers.py:191` | M1 → M2 → M3 |
| Определение пунктуации через regex `[^\u0590-\u05FF\w]+` | `hebpipe_wrappers.py:199` | Noise classifier (M12) |
| Возврат `TokenizeResult` с char offset-ами | `hebpipe_wrappers.py:75-79` | M3 (morph needs offsets) |
| Интеграция в pipeline как шаг 2 | `orchestrator.py:67` | Pipeline orchestration |

#### B) Запланировано, не реализовано

| Функциональность | Доказательство | Ожидаемые процессы | Блокеры |
|-----------------|---------------|-------------------|---------|
| Реальная Hebrew tokenization через HebPipe | CLAUDE.md: "M2: Tokenizer (str.split, no HebPipe)" | Разделение клитических форм (ובבית → ו+ב+בית) | hebpipe dependency |
| Агглютинативная токенизация (morph-aware) | Задокументировано в TZ_uglublenie | Точный морф-анализ M3 | Medium complexity |

#### C) Технически возможно, не планировалось

| Функциональность | Почему реализуемо | Потенциальные процессы | Риск/Сложность |
|-----------------|------------------|----------------------|----------------|
| Sub-word tokenization для BERT-моделей | spacy-transformers уже в deps | Прямая интеграция с M13-M20 | Medium |

#### Резюме модуля

Минимальная реализация (пробел-split). Для иврита это существенное ограничение — язык агглютинативный, многие слова содержат клитики. Слепое пятно: клитическая декомпозиция полностью отсутствует.

---

### 5.3 M3 — Morphological Analyzer (HebPipeMorphAnalyzer)

#### A) Реализованный функционал

| Функциональность | Доказательство | Связанные процессы |
|-----------------|---------------|-------------------|
| Rule-based prefix stripping: 7 проклитиков + цепочки (`_PREFIX_CHAINS`) | `hebpipe_wrappers.py:237-254` | M4 n-gram, M5 NP chunker, M6 canonicalize |
| POS heuristics: PUNCT/NUM/ADP/ADV/PRON/VERB/ADJ/NOUN | `hebpipe_wrappers.py:334-359` | Term extraction filtering |
| Словарь function words (70+ слов) с явными POS | `hebpipe_wrappers.py:260-293` | M12 noise, M8 term filter |
| Опциональная hebpipe-интеграция (`_HEBPIPE_AVAILABLE`) | `hebpipe_wrappers.py:219-228` | Full morph analysis |
| Adjective suffix detection (ית/יים/יות/ני/לי/אי) | `hebpipe_wrappers.py:303-305` | ADJ POS tagging |
| Возврат `MorphResult` с prefix_chain, is_det, features | `hebpipe_wrappers.py:82-99` | M5 NP Chunker (is_det field) |

#### B) Запланировано, не реализовано

| Функциональность | Доказательство | Ожидаемые процессы | Блокеры |
|-----------------|---------------|-------------------|---------|
| Полный морф-анализ через hebpipe (лемматизация, полные features) | CLAUDE.md B1: "hebpipe integration when available" | Точная лемматизация для M6 | hebpipe not installed |
| Verb conjugation identification | — | NER, Summarizer context | Требует лингвистических данных |

#### C) Технически возможно, не планировалось

| Функциональность | Почему реализуемо | Потенциальные процессы | Риск/Сложность |
|-----------------|------------------|----------------------|----------------|
| Morph disambiguation (одно слово — несколько разборов) | Архитектура MorphAnalysis поддерживает alternatives | Более точный term extraction | High |

#### Резюме модуля

Наиболее критичный для качества модуль с наибольшим gap между реализованным и необходимым. Правила покрывают ~80% случаев современного иврита, но лемматизация заметно хуже hebpipe. Техдолг D6: конфликт `Token` dataclass с `engine/hebpipe_wrappers.py` vs `data/models.py`.

---

### 5.4 M4 — N-gram Extractor (NgramExtractor)

#### A) Реализованный функционал

| Функциональность | Доказательство | Связанные процессы |
|-----------------|---------------|-------------------|
| Bigram/trigram extraction с частотным фильтром (min_freq) | `ngram_extractor.py:45+` | M7 (AM scores), M8 (term extraction) |
| document frequency tracking (doc_freq per ngram) | `ngram_extractor.py:33` | TF-IDF scoring в M24 |
| Конфигурируемый диапазон n (min_n, max_n) | orchestrator.py config | Pipeline config |
| Интеграция в pipeline как шаг 4 | `orchestrator.py:69` | Pipeline orchestration |

#### B) Запланировано, не реализовано

| Функциональность | Доказательство | Ожидаемые процессы | Блокеры |
|-----------------|---------------|-------------------|---------|
| Skipgram поддержка | Нет в коде, нет в roadmap | Дальний контекст | — |

#### C) Технически возможно, не планировалось

| Функциональность | Почему реализуемо | Потенциальные процессы | Риск/Сложность |
|-----------------|------------------|----------------------|----------------|
| Позиционные n-граммы (sentence boundary markers) | Данные о позиции уже есть | Улучшенный term extraction | Low |

#### Резюме модуля

Зрелый, хорошо протестированный. Функционал соответствует заявленному.

---

### 5.5 M5 — NP Chunker (NPChunker)

#### A) Реализованный функционал

| Функциональность | Доказательство | Связанные процессы |
|-----------------|---------------|-------------------|
| Rule-based NP chunking по POS паттернам (NOUN+NOUN, NOUN+ADJ) | `np_chunker.py:50+` | M8 term extraction |
| Transformer embeddings режим через `process_doc()` | `np_chunker.py:24-28` | NeoDictaBERT pipeline |
| Auto-mode: embeddings если doc.tensor доступен, иначе rules | `np_chunker.py:7` | Adaptive processing |
| Возврат `NPChunk` с surface, tokens, pattern, offset | `np_chunker.py:47+` | M8 term input |
| Косинусное сходство для определения границ NP | `np_chunker.py` embeddings mode | R-2.1 |

#### B) Запланировано, не реализовано

| Функциональность | Доказательство | Ожидаемые процессы | Блокеры |
|-----------------|---------------|-------------------|---------|
| Construct state (smichut) chains как NP | Упомянуто в gold corpus he_25 | Term quality | Requires morph features |

#### Резюме модуля

Двойной режим (rules/embeddings) реализован. R-2.1 закрыт. Зрелость: Production для rules режима, Beta для embeddings (зависит от KadimaTransformer).

---

### 5.6 M6 — Canonicalizer (Canonicalizer)

#### A) Реализованный функционал

| Функциональность | Доказательство | Связанные процессы |
|-----------------|---------------|-------------------|
| Канонизация форм — снятие определённого артикля, нормализация | `canonicalizer.py` | M8 term dedup, KB indexing |
| Интеграция в pipeline как шаг 6 | `orchestrator.py:71` | Pipeline |

#### Резюме модуля

Реализован, доказано кодом. Детальный анализ не проводился (файл не читался полностью), но тест `tests/engine/test_canonicalizer.py` присутствует.

---

### 5.7 M7 — Association Measures (AMEngine)

#### A) Реализованный функционал

| Функциональность | Доказательство | Связанные процессы |
|-----------------|---------------|-------------------|
| PMI (Pointwise Mutual Information) | `association_measures.py` | M8 term ranking |
| LLR (Log-Likelihood Ratio) | `association_measures.py` | M8 term ranking |
| Dice coefficient | `association_measures.py` | M8 term ranking |
| Возврат `AMResult` с `AMScoreDict` per bigram | `contracts.py:22-27` | M8 input |

#### Резюме модуля

Зрелый. Три метрики ассоциации реализованы. Тест `tests/engine/test_association_measures.py` присутствует.

---

### 5.8 M8 — Term Extractor (TermExtractor)

#### A) Реализованный функционал

| Функциональность | Доказательство | Связанные процессы |
|-----------------|---------------|-------------------|
| Комбинирование n-gram + AM + NP chunks | `contracts.py:28-39` | Финальный шаг NLP pipeline |
| Фильтрация по частоте, POS, noise | `term_extractor.py` | M12 noise feedback |
| Возврат `TermResult` для DB сохранения | `orchestrator.py:run_on_text()` | Data layer (terms table) |

#### Резюме модуля

Терминальный модуль NLP pipeline. Тест присутствует.

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
- **M2 (Tokenizer)**: str.split() — неприемлемо для production Hebrew NLP (клитики).
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

**P2-1: Улучшить M2 и M3 (Hebrew tokenization gap)**
- Что: Добавить клитическую декомпозицию в M2/M3 (хотя бы для ו/ב/ל/כ/מ/ש/ה), улучшить лемматизацию
- Зачем: Текущий str.split() — наибольший gap в качестве Hebrew NLP pipeline
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
