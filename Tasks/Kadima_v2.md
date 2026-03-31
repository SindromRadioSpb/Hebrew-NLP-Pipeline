# KADIMA Development Prompt v2.0

> **Дата:** 2026-03-31 | **Версия проекта:** v0.9.x → v1.0.0
> **Целевое железо:** RTX 3060 12GB VRAM (dev), RTX 3070 8GB (CI/prod)

---

## 0. Контекст и философия

KADIMA — NLP-платформа для терминологической экстракции из ивритских текстов.
Проект находится на стадии v0.9.x: базовый pipeline (M1-M8, M12) работает,
но содержит технический долг и заглушки. Цель — довести до v1.0.0 с
генеративными модулями (M13-M25), стабильной инфраструктурой и CI/CD.

**Принцип:** Не строить новое на шатком фундаменте. Сначала стабилизировать,
потом расширять.

---

## 1. Аудит текущего состояния (обязательный шаг перед любой работой)

### 1.1 Критические проблемы (блокеры)

| # | Проблема | Файл:строка | Влияние |
|---|----------|-------------|---------|
| B1 | M3 MorphAnalyzer — заглушка: `lemma = surface`, POS всегда `"NOUN"` | `kadima/engine/hebpipe_wrappers.py:251-258` | M4-M8 работают на неправильных леммах. Вся терминологическая экстракция даёт искажённые результаты |
| B2 | `PipelineService.run(corpus_id)` — пустая заглушка | `kadima/pipeline/orchestrator.py:78-81` | `POST /pipeline/run/{corpus_id}` не работает. Невозможно обработать корпус через API |
| B3 | `test_pipeline_e2e.py` содержит 0 тестовых функций | `tests/integration/test_pipeline_e2e.py` | Нет E2E-верификации pipeline. Регрессии не ловятся |
| B4 | ML-зависимости не объявлены в `pyproject.toml` | `pyproject.toml` | Невозможно `pip install kadima[ml]`. M13-M25 нельзя установить штатно |
| B5 | `VALID_MODULES` в config.py захардкожен на 9 модулей | `kadima/pipeline/config.py:54-57` | Новые модули M13-M25 не пройдут валидацию конфига |

### 1.2 Средние проблемы (техдолг)

| # | Проблема | Файл | Влияние |
|---|----------|------|---------|
| D1 | `LABEL_STUDIO_PASSWORD=kadima2024` захардкожен | `docker-compose.yml:44` | Нарушение security policy |
| D2 | Docker-образы без версий (`:latest`, `:server`) | `docker-compose.yml` | Непредсказуемые сломы при обновлении |
| D3 | `depends_on: service_started` вместо `service_healthy` | `docker-compose.yml` | API стартует до готовности Label Studio |
| D4 | `setuptools.backends._legacy:_Backend` | `pyproject.toml:3` | Private API, сломается при обновлении setuptools |
| D5 | Нет CI/CD (GitHub Actions) | `.github/` отсутствует | Тесты не проверяются автоматически |
| D6 | Нет `.env.example` | корень проекта | Новый разработчик не знает какие переменные нужны |
| D7 | `Token` dataclass объявлен в 2 местах с разными полями | `data/models.py:39` и `engine/hebpipe_wrappers.py:64` | Путаница при импорте |
| D8 | GPU reservation только для `llm` сервиса, не для `api` | `docker-compose.yml:86` | M13-M25 не получат GPU |
| D9 | API routers (validation, annotation, kb, llm) — пустые заглушки | `kadima/api/routers/` | 4 из 6 роутеров не работают |
| D10 | UI — все 7 виджетов пустые заглушки (~10 строк каждый) | `kadima/ui/` | Desktop UI не функционален |

### 1.3 Что работает хорошо

- Engine Layer (M1-M8, M12): код чистый, следует ProcessorProtocol, тесты есть
- Pipeline config: строгая Pydantic v2 валидация, профили, JSON Schema экспорт
- Data Layer: WAL mode, параметризованные запросы, миграции
- Validation: gold corpus (26 наборов), check_engine, gold_importer
- Документация: 25+ документов ТЗ — покрывают всё от UX до deployment
- Annotation (Label Studio): клиент, sync, project_manager реализованы

---

## 2. RoadMap v0.9.x → v1.0.0

### Фаза 0: Стабилизация фундамента (1-2 недели)

**Цель:** Устранить блокеры и критический техдолг. Ничего нового не добавляем.

```
PATCH-01: Fix conftest.py + test_pipeline_e2e.py
  - Исправить PipelineConfig сигнатуру в tests/conftest.py
  - Добавить реальные тестовые функции в test_pipeline_e2e.py
  - DoD: pytest tests/ -v — 100% PASS

PATCH-02: pyproject.toml modernization
  - build-backend → setuptools.build_meta
  - Добавить optional groups: [ml], [gpu], [dev], [all]
  - [ml]: transformers, sentencepiece, phonikud-onnx, onnxruntime
  - [gpu]: torch (cu128), openai-whisper, TTS
  - DoD: pip install -e ".[dev]" и pip install -e ".[ml]" работают

PATCH-03: Config extensibility for M13-M25
  - Расширить VALID_MODULES для M13-M25 module names
  - Добавить Pydantic sub-configs (DiacritizerConfig, TranslatorConfig, ...)
  - Добавить get_module_config() для каждого нового модуля
  - Обновить config/config.default.yaml
  - Обновить config/config.schema.json
  - DoD: load_config() парсит конфиг с M13-M25 секциями, валидация работает

PATCH-04: Docker & Security hardening
  - Вынести секреты в .env, создать .env.example
  - Пиннинг образов (label-studio:X.Y.Z, llama.cpp:bXXXX)
  - depends_on: service_healthy
  - GPU reservation для api сервиса
  - DoD: docker compose config --quiet без ошибок, .env.example в репо

PATCH-05: CI/CD baseline
  - .github/workflows/test.yml: pytest + ruff + mypy
  - .github/workflows/docker.yml: build check
  - DoD: CI зелёный на main
```

**Критерий выхода из Фазы 0:**
- [ ] Все существующие тесты проходят
- [ ] E2E тест pipeline запускается и проходит
- [ ] `pip install -e ".[ml,dev]"` работает
- [ ] Config принимает M13-M25 модули
- [ ] CI зелёный
- [ ] Нет захардкоженных секретов

---

### Фаза 1: Генеративные модули — Tier 1 (3-4 недели)

**Цель:** Реализовать 5 модулей с наивысшим приоритетом (M13, M14, M17, M22, M21).
Выбраны по принципу: минимальный VRAM + максимальная интеграция с существующим pipeline.

#### Порядок и зависимости

```
M22 Transliterator (0 VRAM, rules only) ─┐
M21 MorphGenerator (0 VRAM, rules only) ──┤── Независимы от ML
                                          │
M13 Diacritizer (<1GB VRAM) ──────────────┤── Первый ML-модуль
M17 NER Extractor (<1GB VRAM) ────────────┤── Интеграция с M8
M14 Translator (3GB VRAM) ────────────────┘── Самый тяжёлый в Tier 1
```

#### Для КАЖДОГО модуля — строгий порядок:

```
1. kadima/engine/<module>.py
   - Наследование от Processor (kadima/engine/base.py)
   - process(), process_batch(), validate_input()
   - Static metric methods
   - try/except ImportError для ML-зависимостей
   - torch.cuda.is_available() перед .to("cuda")
   - logging, Google-style docstrings

2. tests/engine/test_<module>.py
   - Unit-тесты метрик (без ML-модели)
   - Тест с мок-моделью или lightweight fallback
   - Тест validate_input() с невалидными данными
   - Тест process() с пустым вводом

3. Регистрация в orchestrator.py _register_modules()
   - try/except ImportError — если модуль недоступен, skip

4. API endpoint в kadima/api/routers/generative.py
   - POST /generative/<action>
   - Pydantic request/response schemas

5. pytest tests/ -v — 100% PASS

6. Коммит: feat(engine): add M<XX> <ModuleName>
```

#### Детали по модулям Tier 1

**M22 — Transliterator** (самый простой, для разогрева)
- Вход: `str` → Выход: `str`
- Rules-only: таблицы маппинга, без ML
- 3 режима: `to_latin`, `to_male`, `to_haser`
- Метрика: char_accuracy
- VRAM: 0

**M21 — MorphGenerator** (rules-only)
- Вход: `{lemma, pos, features}` → Выход: `List[MorphForm]`
- 7 биньянов: paal, piel, pual, hifil, hufal, hitpael, nifal
- Падежи: singular/plural, absolute/construct, definite/indefinite
- Метрика: form_accuracy
- VRAM: 0

**M13 — Diacritizer** (первый ML)
- Вход: `str` → Выход: `str` (с никудом)
- Backend: `phonikud-onnx` (ONNX Runtime, <1GB)
- Fallback: dicta-il/dictabert-large-char-menaked (transformers)
- Метрики: char_accuracy, word_accuracy
- Интеграция: огласованный текст улучшает M3 MorphAnalyzer
- VRAM: <1GB

**M17 — NER Extractor**
- Вход: `str` → Выход: `List[Entity]`
- Backend: dicta-il/HeQ-NER (transformers pipeline)
- Метрики: precision, recall, F1
- Интеграция: NER entities → M8 TermExtractor (кандидаты терминов)
- VRAM: <1GB

**M14 — Translator**
- Вход: `{text, src_lang, tgt_lang}` → Выход: `str`
- Backend: facebook/mbart-large-50-many-to-many-mmt
- Альтернатива: Helsinki-NLP/opus-mt-tc-big-he-en (быстрее, меньше VRAM)
- Метрика: BLEU
- VRAM: 3GB

**Критерий выхода из Фазы 1:**
- [ ] 5 модулей реализованы, тесты проходят
- [ ] API /generative/* endpoints работают
- [ ] Gold corpus расширен: expected_diacritics.csv, expected_ner.csv, expected_translation_he_en.csv
- [ ] VRAM budget при одновременной загрузке M13+M17+M14: ≤5GB (влезает в 8GB RTX 3070)

---

### Фаза 2: Генеративные модули — Tier 2 (3-4 недели)

**Цель:** Добавить ML-тяжёлые модули (M15, M16, M18, M19, M20).
Требуют управления VRAM — не все могут быть загружены одновременно.

```
M18 Sentiment Analyzer (<1GB) ────── heBERT
M20 QA Extractor (<1GB) ──────────── AlephBERT
M19 Summarizer (2GB) ─────────────── mT5-base
M15 TTS Synthesizer (4GB) ────────── XTTS v2
M16 STT Transcriber (3-6GB) ──────── Whisper large-v3
```

**VRAM Management Strategy:**
```python
# kadima/engine/model_manager.py (новый файл)
class ModelManager:
    """Lazy loading + LRU eviction для ML-моделей.

    Загружает модель в VRAM только при первом вызове.
    Если VRAM заканчивается — выгружает LRU модель.
    RTX 3060 (12GB): максимум 2-3 модели одновременно.
    RTX 3070 (8GB): максимум 1-2 модели.
    """
    def load(self, module_id: str) -> Any: ...
    def unload(self, module_id: str) -> None: ...
    def get_vram_usage(self) -> dict: ...
```

**Миграции БД (PATCH-06):**
```sql
-- 005_generative_results.sql
CREATE TABLE results_nikud (id, document_id, original, diacritized, accuracy, created_at);
CREATE TABLE results_translation (id, document_id, src_lang, tgt_lang, original, translated, bleu, created_at);
CREATE TABLE results_tts (id, document_id, text, audio_path, duration_sec, created_at);
CREATE TABLE results_ner (id, document_id, text, entity_text, entity_type, start, end, score, created_at);
CREATE TABLE results_sentiment (id, document_id, text, label, score, created_at);
CREATE TABLE results_summary (id, document_id, original, summary, rouge_l, created_at);
CREATE TABLE results_qa (id, document_id, context, question, answer, score, created_at);
```

**TTS/STT цикл (M15+M16):**
- Специальный integration test: text → M15 TTS → WAV → M16 STT → text'
- Метрика: WER(text, text') < 0.15

**Критерий выхода из Фазы 2:**
- [ ] 5 модулей реализованы, тесты проходят
- [ ] ModelManager управляет VRAM, нет OOM при последовательном вызове всех модулей
- [ ] TTS→STT round-trip WER < 0.15
- [ ] Миграция 005 применяется, результаты сохраняются в БД

---

### Фаза 3: Генеративные модули — Tier 3 + Инфраструктура (2-3 недели)

**Цель:** Оставшиеся модули (M23, M24, M25) + полировка.

```
M24 Keyphrase Extractor (<1GB) ──── YAKE! (без ML) или KeyBERT
M23 Grammar Corrector (2-4GB) ───── T5-hebrew или LLM
M25 Paraphraser (2-4GB) ─────────── mT5 или LLM
```

**M23 и M25** могут использовать LLM-сервис (llama.cpp) вместо отдельной модели:
```python
class GrammarCorrector(Processor):
    def __init__(self, backend="llm"):
        # backend: "llm" → используем kadima/llm/client.py
        # backend: "mt5" → отдельная модель
```

**Дополнительные задачи Фазы 3:**

```
PATCH-07: PipelineService.run(corpus_id) — полная реализация
  - Загрузка документов из БД
  - Итерация по документам с run_on_text()
  - Сохранение результатов
  - Progress callback для UI

PATCH-08: API routers — дореализовать заглушки
  - validation, annotation, kb, llm роутеры
  - OpenAPI docs актуальны

PATCH-09: M3 MorphAnalyzer — интеграция с реальным HebPipe
  - Optional dependency: hebpipe
  - Fallback на текущую regex-заглушку если hebpipe не установлен
  - Тест с реальным HebPipe (если доступен)

PATCH-10: Generative view UI (kadima/ui/generative_view.py)
  - Таб с 13 модулями
  - Input/output text areas
  - Backend/device selector
  - Progress bar
```

**Критерий выхода из Фазы 3:**
- [ ] Все 25 модулей реализованы
- [ ] PipelineService.run(corpus_id) работает end-to-end
- [ ] API полностью функционален (0 заглушек)
- [ ] M3 использует реальный HebPipe (если установлен)

---

### Фаза 4: Стабилизация v1.0.0 (1-2 недели)

```
- Полный regression suite: pytest tests/ -v --tb=short
- Load testing: 100 документов через pipeline, нет утечек памяти
- VRAM stress test: все ML-модули поочерёдно, нет OOM
- Security audit: security-auditor на всех новых файлах
- Docker production compose: resource limits, healthchecks, pinned images
- Documentation: обновить README, CHANGELOG, API docs
- Tag: v1.0.0
```

---

## 3. VRAM Budget (RTX 3060 12GB / RTX 3070 8GB)

| Модуль | VRAM | Одновременная загрузка? |
|--------|------|------------------------|
| M13 Diacritizer | <1GB | Да (всегда в памяти) |
| M17 NER | <1GB | Да |
| M18 Sentiment | <1GB | Да |
| M20 QA | <1GB | Да |
| M14 Translator | 3GB | По требованию |
| M19 Summarizer | 2GB | По требованию |
| M15 TTS | 4GB | Эксклюзивно (выгружает другие) |
| M16 STT | 3-6GB | Эксклюзивно |
| M23 Grammar | 2-4GB | По требованию / через LLM |
| M25 Paraphrase | 2-4GB | По требованию / через LLM |
| M24 Keyphrase | <1GB | Да (YAKE! — CPU only) |
| M21 MorphGen | 0 | Да (rules) |
| M22 Transliterator | 0 | Да (rules) |

**Правило:** Суммарно в VRAM не более 8GB (RTX 3070 target).
ModelManager обеспечивает LRU eviction.

---

## 4. Архитектурные решения

### 4.1 Регистрация модулей в Orchestrator

```python
# kadima/pipeline/orchestrator.py — расширенный _register_modules()
def _register_modules(self) -> None:
    # ... existing M1-M8, M12 ...

    # Генеративные модули — lazy load, не падаем если нет зависимостей
    _optional_modules = {
        "diacritizer":    ("kadima.engine.diacritizer", "Diacritizer"),
        "translator":     ("kadima.engine.translator", "Translator"),
        "tts":            ("kadima.engine.tts_synthesizer", "TTSSynthesizer"),
        "stt":            ("kadima.engine.stt_transcriber", "STTTranscriber"),
        "ner":            ("kadima.engine.ner_extractor", "NERExtractor"),
        "sentiment":      ("kadima.engine.sentiment_analyzer", "SentimentAnalyzer"),
        "summarizer":     ("kadima.engine.summarizer", "Summarizer"),
        "qa":             ("kadima.engine.qa_extractor", "QAExtractor"),
        "morph_gen":      ("kadima.engine.morph_generator", "MorphGenerator"),
        "transliterator": ("kadima.engine.transliterator", "Transliterator"),
        "grammar":        ("kadima.engine.grammar_corrector", "GrammarCorrector"),
        "keyphrase":      ("kadima.engine.keyphrase_extractor", "KeyphraseExtractor"),
        "paraphrase":     ("kadima.engine.paraphraser", "Paraphraser"),
    }

    for name, (module_path, class_name) in _optional_modules.items():
        if name not in self.config.modules:
            continue
        try:
            mod = importlib.import_module(module_path)
            cls = getattr(mod, class_name)
            self.modules[name] = cls(self.config.get_module_config(name))
            logger.info("Loaded optional module: %s", name)
        except ImportError as e:
            logger.warning("Module %s unavailable: %s", name, e)
```

### 4.2 Generative Pipeline vs NLP Pipeline

Генеративные модули НЕ являются последовательной цепочкой (в отличие от M1→M8).
Каждый вызывается **независимо** по запросу пользователя:

```
NLP Pipeline (sequential):  M1 → M2 → M3 → M4 → M5 → M6 → M7 → M8 → M12
                                                                      ↓
Generative (on-demand):     M13, M14, M15, M16, M17, M18, M19, M20, M21, M22, M23, M24, M25
```

Оркестратор должен поддерживать оба режима:
- `run_on_text(text)` — NLP pipeline (как сейчас)
- `run_module(module_id, input_data)` — одиночный генеративный вызов (новый метод)

### 4.3 Config расширение

```python
# Добавить в PipelineConfig:
VALID_MODULES = frozenset([
    # NLP pipeline (sequential)
    "sent_split", "tokenizer", "morph_analyzer", "ngram", "np_chunk",
    "canonicalize", "am", "term_extract", "noise",
    # Generative (on-demand)
    "diacritizer", "translator", "tts", "stt", "ner",
    "sentiment", "summarizer", "qa", "morph_gen",
    "transliterator", "grammar", "keyphrase", "paraphrase",
])

# Sub-configs для каждого генеративного модуля:
class DiacritizerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    backend: str = "phonikud"  # phonikud | dicta
    device: str = "cuda"

class TranslatorConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    backend: str = "mbart"  # mbart | opus | nllb
    device: str = "cuda"
    default_tgt_lang: str = "en"

# ... и т.д. для каждого модуля
```

---

## 5. Constraints & Non-Negotiables

### Для каждого коммита:
1. `pytest tests/ -v` — 100% PASS (включая существующие тесты)
2. `ruff check kadima/` — 0 ошибок
3. Нет захардкоженных секретов
4. Все SQL — параметризованные
5. ML-импорты обёрнуты в `try/except ImportError`
6. CUDA: всегда `torch.cuda.is_available()` перед `.to("cuda")`
7. Logging через `logging.getLogger(__name__)`, не `print()`
8. Google-style docstrings на публичных методах
9. Аннотации типов на публичных функциях

### Формат коммитов:
```
feat(engine): add M13 Diacritizer with phonikud backend
fix(pipeline): fix PipelineConfig signature in conftest
chore(deps): add [ml] optional dependency group
test(engine): add unit tests for M22 Transliterator
refactor(config): extend VALID_MODULES for M13-M25
```

### Что НЕ делать:
- Не начинать M13-M25 пока Фаза 0 не завершена
- Не загружать все ML-модели одновременно — ModelManager
- Не класть NLP-логику в API routers — только вызовы engine/pipeline
- Не хардкодить пути — `KADIMA_HOME` env
- Не создавать таблицы в коде — только миграции SQL
- Не мержить fixture с реальными данными
- Не ломать существующий pipeline ради новых модулей

---

## 6. Инструкция для Claude Code

### Первый запуск (при каждой новой сессии):

```
1. Прочитай этот файл (Tasks/Kadima_v2.md)
2. Прочитай CLAUDE.md — полная карта модулей
3. Определи текущую фазу по состоянию кода:
   - Есть ли M13+ в kadima/engine/? → Фаза 1+ начата
   - Есть ли .github/workflows/? → Фаза 0 (CI) завершена
   - Есть ли [ml] в pyproject.toml? → Фаза 0 (deps) завершена
4. Запусти: pytest tests/ -v — убедись что всё проходит
5. Продолжи с текущего PATCH в текущей фазе
```

### Workflow для каждого модуля:

```
1. repo-auditor → проверить зависимости и конфликты
2. Создать engine/<module>.py (наследование от Processor)
3. Создать tests/engine/test_<module>.py
4. Обновить orchestrator.py _register_modules()
5. Обновить config/config.default.yaml
6. pytest tests/ -v — ALL PASS
7. code-reviewer → ревью диффа
8. security-auditor → если модуль принимает user input
9. Коммит: feat(engine): add M<XX> <Name>
```

### Переключение между фазами:

Не переходи к следующей фазе пока не выполнены ВСЕ критерии выхода текущей.
Если критерий не выполняется — разберись почему, исправь, и только потом двигайся дальше.

---

## 7. Приоритеты при конфликтах

1. **Не сломать существующее** > добавить новое
2. **Тесты проходят** > красивый код
3. **Безопасность** > удобство разработки
4. **Простое решение** > архитектурно "правильное"
5. **Работающий M13** > начатые M13+M14+M17

---

## 8. Метрики успеха v1.0.0

| Метрика | Target | Как измерять |
|---------|--------|-------------|
| Тесты | 100% PASS, >150 test functions | `pytest tests/ -v --tb=short` |
| Покрытие модулей | 25/25 реализованы | Наличие файлов в engine/ |
| API endpoints | 0 заглушек | Все роутеры возвращают данные |
| VRAM budget | ≤8GB при 3 моделях | `nvidia-smi` при нагрузке |
| Nikud accuracy | >0.95 char accuracy | Gold corpus expected_diacritics.csv |
| NER F1 | >0.85 | Gold corpus expected_ner.csv |
| Translation BLEU | >30.0 (HE→EN) | Gold corpus expected_translation.csv |
| TTS→STT WER | <0.15 | Round-trip integration test |
| CI | Зелёный на main | GitHub Actions |
| Security | 0 critical findings | security-auditor |
