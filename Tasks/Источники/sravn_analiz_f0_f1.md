# Сравнительный анализ: hebrew-corpus-v2 (референс) vs Kadima (Project_Vibe)

**Дата:** 2026-03-31
**Статус Фаз:** Фаза 0 (стабилизация) + Фаза 1 (генеративные модули Tier 1) — завершены

---

## 1. Краткое описание обоих репозиториев

### hebrew-corpus-v2 (референс)
- **Путь:** `/mnt/c/projects/hebrew-corpus-v2/`
- **Версия:** v0.9.0
- **Состояние:** Базовый NLP pipeline (M1-M8, M12) работает. M3 MorphAnalyzer — STUB (lemma=surface, POS="NOUN"). run(corpus_id) — заглушка. E2E тесты пусты. VALID_MODULES содержит только 9 NLP модулей. Генеративные модули (M13-M25) описаны в CLAUDE.md но не реализованы.
- **Тестов:** ~298

### Kadima (Project_Vibe)
- **Путь:** `/mnt/c/projects/Project_Vibe/Kadima/`
- **Версия:** v0.9.1
- **Состояние:** Полностью реализованы Фаза 0 + Фаза 1. Все 4 блокера Фазы 0 (B1-B4) закрыты. Реализованы 5 генеративных модулей Tier 1 (M22, M21, M13, M17, M14). Generative API router работает. Orchestrator с lazy-load генеративных модулей.
- **Тестов:** ~500

---

## 2. Модульное сравнение

### 2.1 Общие модули (идентичные или с минимальными отличиями)

| Модуль | Референс | Kadima | Статус |
|--------|----------|--------|--------|
| `engine/base.py` | Processor ABC, ProcessorResult, PipelineResult | Идентичен | ✅ Совпадает |
| `engine/contracts.py` | ProcessorProtocol, TypedDict | Идентичен | ✅ Совпадает |
| `engine/ngram_extractor.py` | M4 NgramExtractor | Идентичен | ✅ Совпадает |
| `engine/np_chunker.py` | M5 NPChunker | Идентичен | ✅ Совпадает |
| `engine/canonicalizer.py` | M6 Canonicalizer | Идентичен | ✅ Совпадает |
| `engine/association_measures.py` | M7 AMEngine | Идентичен | ✅ Совпадает |
| `engine/term_extractor.py` | M8 TermExtractor | Идентичен | ✅ Совпадает |
| `engine/noise_classifier.py` | M12 NoiseClassifier | Идентичен | ✅ Совпадает |
| `corpus/` | importer, exporter, statistics | Идентичен | ✅ Совпадает |
| `data/` | db, models, repositories, миграции | Идентичен | ✅ Совпадает |
| `annotation/` | ls_client, exporter, sync, ml_backend, project_manager | Идентичен | ✅ Совпадает |
| `kb/` | generator, models, repository, search | Идентичен | ✅ Совпадает |
| `llm/` | client, prompts, service | Идентичен | ✅ Совпадает |
| `nlp/components/` | 5 spaCy компонентов | Идентичен | ✅ Совпадает |
| `validation/` | check_engine, gold_importer, report | Идентичен | ✅ Совпадает |
| `ui/` | 7 виджетов-заглушек | Идентичен | ✅ Совпадает (stub) |
| `utils/` | hebrew, logging | Идентичен | ✅ Совпадает |
| `cli.py` | CLI entrypoint | Идентичен | ✅ Совпадает |

### 2.2 Модули с существенными отличиями

| Модуль | Референс | Kadima | Статус |
|--------|----------|--------|--------|
| `engine/hebpipe_wrappers.py` M3 | **STUB**: lemma=surface, POS="NOUN" всегда, только is_det | **Реализован**: rule-based fallback (7 prefixes, 16 chains, ~70 function words, POS heuristics) + hebpipe integration | ✅ Kadima расширен |
| `pipeline/config.py` | VALID_MODULES = 9 NLP модулей | NLP_MODULES=9 + GENERATIVE_MODULES=13 = 22 | ✅ Kadima расширен |
| `pipeline/orchestrator.py` | run(corpus_id) = STUB (TODO) | **Реализован**: загрузка из БД, pipeline_runs, сохранение terms, rollback | ✅ Kadima расширен |
| `api/app.py` | 3 core routers + 3 extended | + generative router (5 endpoints) | ✅ Kadima расширен |
| `pyproject.toml` | v0.9.0, только [gui,hebpipe,dev] | v0.9.1, + [ml], [gpu] groups | ✅ Kadima расширен |

### 2.3 Модули, отсутствующие в референсе, но present в Kadima

| Модуль | Файл | Назначение | Статус |
|--------|------|------------|--------|
| M13 Diacritizer | `engine/diacritizer.py` | Огласовка текста (phonikud/dicta/rules) | ✅ Реализован |
| M14 Translator | `engine/translator.py` | Перевод (mBART/OPUS/dict) | ✅ Реализован |
| M17 NER Extractor | `engine/ner_extractor.py` | NER (HeQ-NER/rules) | ✅ Реализован |
| M21 MorphGenerator | `engine/morph_generator.py` | Морфогенерация (7 биньянов, rules) | ✅ Реализован |
| M22 Transliterator | `engine/transliterator.py` | Транслитерация (latin/phonetic/hebrew) | ✅ Реализован |
| `api/routers/generative.py` | API router | 5 endpoints: transliterate, morph-gen, diacritize, ner, translate | ✅ Реализован |

---

## 3. Отклонения от Фаз 0-1

### Фаза 0 (стабилизация) — КРИТЕРИИ ВЫХОДА

| Критерий | Референс | Kadima | Комментарий |
|----------|----------|--------|-------------|
| Все существующие тесты проходят | 298 тестов | ~500 тестов | ✅ Kadima превышает |
| E2E pipeline тест | **ПУСТОЙ** (stub) | 21 тестов в 4 классах | ✅ Kadima реализован (B3) |
| `pip install -e ".[ml,dev]"` работает | Нет [ml] group | Есть [ml] + [gpu] groups | ✅ Kadima реализован |
| Config принимает M13-M25 | VALID_MODULES = 9 | VALID_MODULES = 22 | ✅ Kadima реализован (B4) |
| CI зелёный | .github/workflows/test.yml | .github/workflows/test.yml | ✅ Оба имеют |
| Нет захардкоженных секретов | .env.example | .env.example | ✅ Оба имеют |

### Фаза 1 (генеративные модули Tier 1) — ПЛАН

| Порядок | Модуль | План | Реализовано в Kadima |
|---------|--------|------|---------------------|
| 1 | M22 Transliterator | rules-only | ✅ 3 режима (latin/phonetic/hebrew), 35 тестов |
| 2 | M21 MorphGenerator | rules-only | ✅ 7 биньянов, noun/adj inflections, 33 теста |
| 3 | M13 Diacritizer | phonikud/dicta/rules | ✅ 3 backend, метрики, 28 тестов |
| 4 | M17 NER Extractor | HeQ-NER/rules | ✅ gazetteer + patterns, метрики, 29 тестов |
| 5 | M14 Translator | mBART/OPUS/dict | ✅ 3 backend, BLEU metric, 25 тестов |

**Все 5 модулей Фазы 1 реализованы в Kadima.**

### Блокеры Фазы 0 (B1-B4)

| Блокер | Референс | Kadima |
|--------|----------|--------|
| B1: M3 MorphAnalyzer STUB | НЕ РЕШЕН | ✅ РЕШЕН: rule-based fallback + hebpipe |
| B2: run(corpus_id) STUB | НЕ РЕШЕН | ✅ РЕШЕН: полная реализация с БД |
| B3: E2E тесты пустые | НЕ РЕШЕН | ✅ РЕШЕН: 21 E2E тест |
| B4: VALID_MODULES = 9 | НЕ РЕШЕН | ✅ РЕШЕН: 22 модуля + Pydantic sub-configs |

---

## 4. Недостающий функционал для Фаз 2+

### Фаза 2 — ML-тяжёлые модули (НЕ РЕАЛИЗОВАНЫ в обоих)

| Модуль | Назначение | VRAM | Статус |
|--------|------------|------|--------|
| M18 Sentiment Analyzer | Анализ тональности | <1GB | ❌ Не реализован |
| M20 QA Extractor | Вопросно-ответная система | <1GB | ❌ Не реализован |
| M19 Summarizer | Суммаризация | 2GB | ❌ Не реализован |
| M15 TTS Synthesizer | Синтез речи | 4GB | ❌ Не реализован |
| M16 STT Transcriber | Распознавание речи | 3-6GB | ❌ Не реализован |

### Фаза 3 — Оставшиеся модули (НЕ РЕАЛИЗОВАНЫ)

| Модуль | Назначение | Статус |
|--------|------------|--------|
| M24 Keyphrase Extractor | Извлечение ключевых фраз | ❌ Не реализован |
| M23 Grammar Corrector | Грамматическая коррекция | ❌ Не реализован |
| M25 Paraphraser | Парафраз текста | ❌ Не реализован |

### Фаза 4 — Стабилизация релиза (НЕ РЕАЛИЗОВАНЫ)

- Regression testing
- Load testing
- Security audit
- Documentation finalization
- UI реализация (все виджеты — stubs в обоих репозиториях)

---

## 5. Архитектурные различия

### 5.1 Config Architecture
| Аспект | Референс | Kadima |
|--------|----------|--------|
| VALID_MODULES | `frozenset([...])` — 9 NLP | `NLP_MODULES | GENERATIVE_MODULES` = 22 |
| Generative configs | Нет | 13 Pydantic sub-configs (DiacritizerConfig, TranslatorConfig, и т.д.) |
| DeviceEnum | Нет | `DeviceEnum(cpu/cuda)` |
| get_module_config() | Только NLP модули | NLP + generative (model_dump) |
| load_config() | Только NLP секции | + generative секции из YAML |
| JSON Schema | Только NLP модели | + все 13 generative моделей |

### 5.2 Orchestrator Architecture
| Аспект | Референс | Kadima |
|--------|----------|--------|
| _register_modules() | 9 модулей (синхронно) | 9 NLP + 5 generative (lazy-load через importlib) |
| run(corpus_id) | STUB (return empty) | Полная реализация: БД, pipeline_runs, terms, rollback |
| Generative support | Нет | lazy-import с fallback при ImportError |

### 5.3 API Architecture
| Аспект | Референс | Kadima |
|--------|----------|--------|
| Core routers | corpora, pipeline, validation | corpora, pipeline, validation, **generative** |
| Generative endpoints | Нет | /generative/transliterate, /morph-gen, /diacritize, /ner, /translate |

### 5.4 Dependencies
| Группа | Референс | Kadima |
|--------|----------|--------|
| [ml] | Нет | phonikud-onnx, onnxruntime, transformers, sentencepiece, yake |
| [gpu] | Нет | torch, TTS, openai-whisper |
| pyproject.toml | v0.9.0 | v0.9.1 |

### 5.5 M3 MorphAnalyzer Architecture
| Аспект | Референс | Kadima |
|--------|----------|--------|
| Implementation | STUB: lemma=surface, POS="NOUN" | Rule-based + hebpipe |
| Prefix stripping | Нет | 7 single-char + 16 multi-char chains |
| POS detection | Только "NOUN" | PUNCT, NUM, ADP, CCONJ, SCONJ, ADV, PRON, VERB, DET, ADJ, NOUN |
| Function words | Нет | ~70 words с correct POS |
| hebpipe integration | Нет (только try/except) | _process_hebpipe() с fallback |

---

## 6. Рекомендации по возврату в продуктовое русло

### Для референса (hebrew-corpus-v2)

Если референс должен догнать Kadima:

1. **B1 — M3 MorphAnalyzer**: Скопировать rule-based fallback из Kadima (`_strip_prefixes()`, `_detect_pos()`, `_FUNCTION_WORDS`, `_process_rules()`, `_process_hebpipe()`)
2. **B2 — run(corpus_id)**: Скопировать реализацию из Kadima (БД загрузка, pipeline_runs, terms запись, rollback)
3. **B3 — E2E тесты**: Скопировать `test_pipeline_e2e.py` из Kadima (21 тест)
4. **B4 — VALID_MODULES**: Расширить config.py как в Kadima (NLP_MODULES + GENERATIVE_MODULES + 13 sub-configs)
5. **pyproject.toml**: Добавить [ml] и [gpu] optional dependency groups
6. **Generative router**: Создать `api/routers/generative.py` как в Kadima

### Для Kadima

1. **Документация**: Синхронизировать CLAUDE.md — убрать устаревшие пометки "STUB" для M3 и B2
2. **Фаза 2**: Реализовать M22 Transliterator и M21 MorphGenerator уже готовы → следующие M18 Sentiment, M20 QA
3. **UI**: Все виджеты остаются stubs — нужна реализация хотя бы базовых views
4. **Генеративные модули в orchestrator**: Сейчас они lazy-load и не участвуют в NLP pipeline — это правильно по архитектуре, но on-demand вызовы нужно тестировать отдельно

---

## 7. Риски

### Риск 1: M3 MorphAnalyzer в референсе — критический
- **Вероятность:** Высокая (в референсе не исправлен)
- **Влияние:** Все downstream модули (M4-M8) работают на искажённой морфологической базе
- **Митигация:** Kadima уже решил это; референс должен скопировать решение

### Риск 2: Документация отстаёт от кода в Kadima
- **Вероятность:** Средняя
- **Влияние:** CLAUDE.md содержит устаревшие пометки (M3=STUB, B2=stub) которые не соответствуют реальному коду
- **Митигация:** Обновить CLAUDE.md

### Риск 3: Нет ML-зависимостей в референсе
- **Вероятность:** Высокая
- **Влияление:** `pip install -e ".[ml]"` не работает в референсе
- **Митигация:** Kadima уже имеет [ml] и [gpu] groups

### Риск 4: Generative модули не тестированы в реальном pipeline
- **Вероятность:** Средняя
- **Влияние:** M13-M17 реализованы как отдельные модули с API endpoints, но не интегрированы в основной NLP pipeline (и это правильно по архитектуре)
- **Митигация:** Generative модули — on-demand, не sequential pipeline. Нужны отдельные интеграционные тесты

### Риск 5: UI остаётся stub в обоих репозиториях
- **Вероятность:** Высокая
- **Влияние:** Нет desktop интерфейса для конечного пользователя
- **Митигация:** API + CLI работают; UI — это отдельная фаза

### Риск 6: Диблю между репозиториями
- **Вероятность:** Высокая
- **Влияние:** hebrew-corpus-v2 и Kadima — два отдельных репозитория с почти идентичной структурой. Любое исправление нужно делать в двух местах
- **Митигация:** Определить canonical repo (Kadima) и архивировать/удалить референс, либо сделать submodule

---

## Сводная таблица: модуль → статус

| Модуль | Референс | Kadima | Фаза |
|--------|----------|--------|------|
| M1 SentSplit | ✅ | ✅ | 0 |
| M2 Tokenizer | ✅ | ✅ | 0 |
| M3 MorphAnalyzer | ❌ STUB | ✅ Rule-based + hebpipe | 0 (B1) |
| M4 NgramExtractor | ✅ | ✅ | 0 |
| M5 NPChunker | ✅ | ✅ | 0 |
| M6 Canonicalizer | ✅ | ✅ | 0 |
| M7 AMEngine | ✅ | ✅ | 0 |
| M8 TermExtractor | ✅ | ✅ | 0 |
| M12 NoiseClassifier | ✅ | ✅ | 0 |
| M13 Diacritizer | ❌ | ✅ | 1 |
| M14 Translator | ❌ | ✅ | 1 |
| M17 NER Extractor | ❌ | ✅ | 1 |
| M21 MorphGenerator | ❌ | ✅ | 1 |
| M22 Transliterator | ❌ | ✅ | 1 |
| M15 TTS | ❌ | ❌ | 2 |
| M16 STT | ❌ | ❌ | 2 |
| M18 Sentiment | ❌ | ❌ | 2 |
| M19 Summarizer | ❌ | ❌ | 2 |
| M20 QA | ❌ | ❌ | 2 |
| M23 Grammar | ❌ | ❌ | 3 |
| M24 Keyphrase | ❌ | ❌ | 3 |
| M25 Paraphrase | ❌ | ❌ | 3 |
| Config (VALID_MODULES) | 9 модулей | 22 модуля | 0 (B4) |
| Orchestrator run() | STUB | ✅ | 0 (B2) |
| Generative router | ❌ | ✅ | 1 |
| E2E тесты | ❌ пустой | ✅ 21 тест | 0 (B3) |
| Tests total | ~298 | ~500 | — |
