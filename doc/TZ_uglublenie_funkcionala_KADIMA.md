# Техническое задание: Углубление функционала KADIMA

> Версия: 1.0
> Дата: 2026-03-31
> Репозиторий: `E:\projects\Project_Vibe\Kadima`
> Режим: Непрерывная разработка — каждый шаг реализуется, тестируется, коммитится перед переходом к следующему.

---

## 1. Контекст и основание

### 1.1 Что произошло

Проект KADIMA прошёл две фазы разработки:

- **Фаза 0 (стабилизация):** Закрыты 4 блокера — B1 (M3 MorphAnalyzer STUB → rule-based + hebpipe), B2 (run(corpus_id) STUB → полная реализация), B3 (E2E тесты пустые → 21 тест), B4 (VALID_MODULES = 9 → 22 модуля + Pydantic sub-configs).
- **Фаза 1 (генеративные модули Tier 1):** Реализованы M22 Transliterator, M21 MorphGenerator, M13 Diacritizer, M17 NER Extractor, M14 Translator. Generative API router — 5 эндпоинтов. Тестов: ~500.

### 1.2 Что документация описывает, а код не реализует

Проведён аудит документации (`Техническое задание разработка KADIMA/`) vs текущего состояния кода. Выявлены отклонения:

| Отклонение | Критичность | Суть |
|---|---|---|
| NeoDictaBERT не интегрирован | 🔴 Критическое | Документация: transformer backbone. Код: `spacy.blank("xx")` без embeddings |
| spacy-transformers отсутствует | 🔴 Критическое | Нет в pyproject.toml, pipeline работает без transformer |
| M5 NPChunker — правила | 🟡 Среднее | Документация: transformer-based. Код: pattern matching |
| NER — HeQ-NER, не NeoDictaBERT | 🟡 Среднее | Документация: дообучение на NeoDictaBERT. Код: внешняя модель |
| KB search — точное совпадение | 🟡 Среднее | Документация: embedding similarity. Код: string matching |
| pyproject.toml — optional vs core | 🟡 Среднее | Документация: torch/transformers в core. Код: в [ml] |
| UI — стабы | 🟡 Среднее | Документация: полноценный PyQt Dashboard. Код: заглушки |
| SQLAlchemy — документация vs sqlite3 | 🟡 Среднее | Документация: SQLAlchemy. Код: прямой sqlite3 |

### 1.3 Цель ТЗ

Привести реализацию к архитектурному уровню, описанному в документации. Система должна получить:
1. Семантическое понимание текста (transformer embeddings)
2. Качественный NP chunking, NER, KB search на embeddings
3. Type-safe data layer (SQLAlchemy)
4. Desktop UI для лингвистов
5. Полный набор генеративных модулей Phase 2–3

### 1.4 Источники

| Файл | Что содержит |
|---|---|
| `E:\projects\Project_Vibe\Kadima\Tasks\Источники\revizia.md` | Аудит референсного репозитория (модули, функционал, проблемы) |
| `E:\projects\Project_Vibe\Kadima\Tasks\Источники\sravn_analiz_f0_f1.md` | Сравнительный анализ: референс vs Kadima |
| `E:\projects\Project_Vibe\Kadima\Tasks\Источники\analiz_dokumentacii_vs_realizacii.md` | Отклонения документации от реализации |
| `E:\projects\Project_Vibe\Kadima\Tasks\Источники\trebovaniya_k_uglubleniyu_funkcionala.md` | Требования к углублению (30 пунктов) |
| `E:\projects\Project_Vibe\Kadima\Tasks\Источники\summary - what each block brings to the system.txt` | Сводка что каждый блок даёт системе |
| `E:\projects\Project_Vibe\Kadima\Техническое задание разработка KADIMA\` | Полная документация ТЗ (архитектура, NLP stack, API, roadmap) |
---

## 2. Текущее состояние системы

### 2.1 Что работает (реализовано)

**NLP Pipeline (M1–M8, M12):**
- M1 SentSplit — spaCy component (HebPipe wrapper)
- M2 Tokenizer — встроен в M3
- M3 MorphAnalyzer — rule-based fallback + hebpipe integration (482 строки)
- M4 NgramExtractor — spaCy component (96 строк)
- M5 NPChunker — rule-based (105 строк)
- M6 Canonicalizer — правила (77 строк)
- M7 AM Engine — PMI, LLR, Dice (187 строк)
- M8 TermExtractor — 3 профиля (102 строки)
- M12 NoiseClassifier — правила (92 строки)

**Генеративные модули (Phase 1):**
- M13 Diacritizer — phonikud/dicta/rules backends (295 строк)
- M14 Translator — mBART/OPUS-MT/dict backends (284 строки)
- M17 NER Extractor — HeQ-NER/rules backends (314 строк)
- M21 MorphGenerator — rules, 7 binyanim (323 строки)
- M22 Transliterator — latin/phonetic/hebrew (287 строки)

**Инфраструктура:**
- Pipeline Orchestrator — run_on_text() + run(corpus_id) с БД
- Config — Pydantic v2, 22 модуля, 13 generative sub-configs
- Data Layer — SQLite WAL, миграции, repository pattern
- API — FastAPI, 7 роутеров (corpora, pipeline, validation, annotation, kb, llm, generative)
- Annotation — Label Studio integration (5 файлов)
- KB — repository, search, generator, models
- LLM — llama.cpp client, prompts, service
- Validation — gold corpus, check engine, report
- Corpus — importer, exporter, statistics
- CLI — gui, run, api, migrate, init
- Tests — ~500 тестов, 22 файла, E2E покрытие

### 2.2 Что НЕ работает (стабы / отсутствует)

- UI — все 7 виджетов-заглушек (dashboard, pipeline_view, и т.д.)
- NeoDictaBERT — не интегрирован
- spacy-transformers — не в dependencies
- M18 Sentiment, M15 TTS, M16 STT, M20 Active Learning — не реализованы
- M24 Keyphrase, M23 Grammar, M25 Summarizer — не реализованы
- SQLAlchemy — не используется (прямой sqlite3)
- KB embedding search — нет

---

## 3. Требования

### Общие правила реализации

1. **Каждый шаг** реализуется → тестируется → коммитится перед переходом к следующему.
2. **Backward compatibility:** Все существующие тесты должны проходить после каждого шага.
3. **Graceful degradation:** Если зависимость недоступна (нет GPU, нет модели) — fallback, не crash.
4. **Конфигурируемость:** Новые возможности включаются/выключаются через config.
5. **Тесты:** Каждый новый модуль/изменение — минимум 5 unit-тестов + 1 интеграционный.

---

### Tier 1: Базовое качество (v1.0) — ~25–35 часов

#### R-1.1 spacy-transformers в core dependencies

**Что:** Добавить `spacy-transformers>=1.3,<2.0` и `transformers>=4.35,<5.0` в `dependencies` (не optional) в `pyproject.toml`.

**Файлы:** `pyproject.toml`

**Критерий:** `pip install kadima` ставит spacy-transformers. `python -c "import spacy_transformers"` работает.

**Тест:** `tests/test_config.py` — проверка что все NLP-зависимости importable.

**Коммит:** `feat(deps): add spacy-transformers and transformers to core dependencies`

---

#### R-1.2 NeoDictaBERT transformer component

**Что:** Создать `kadima/nlp/components/transformer_component.py`:

```python
@Language.factory("kadima_transformer")
class KadimaTransformer:
    """NeoDictaBERT transformer backbone для spaCy pipeline.
    
    Загружает dicta-il/neodictabert через spacy-transformers.
    Кладёт контекстные embeddings (768-dim) в doc[i].vector.
    """
    
    def __init__(self, nlp: Language, name: str, 
                 model_name: str = "dicta-il/neodictabert",
                 max_length: int = 512):
        # Загрузка через spacy-transformers.TransformerModel
        # При ошибке — fallback (см. R-1.4)
    
    def __call__(self, doc: Doc) -> Doc:
        # NeoDictaBERT inference → doc[i].vector для каждого токена
```

**Зависимости:** R-1.1

**Конфигурация:** Секция в `config/default.yaml`:
```yaml
transformer:
  model_name: "dicta-il/neodictabert"
  max_length: 512
  device: "cpu"  # или "cuda"
  fp16: true
```

**Критерий:** `nlp(text)` → каждый токен имеет `.vector` размерности 768.

**Тесты:**
- `tests/engine/test_transformer_component.py` — загрузка модели, vector dimension, fallback при ошибке
- Интеграционный: pipeline с transformer → doc с vectors

**Коммит:** `feat(nlp): add NeoDictaBERT transformer component (R-1.2)`

---

#### R-1.3 Pipeline builder с transformer

**Что:** Изменить `kadima/nlp/pipeline.py` — `build_pipeline()` принимает параметр `use_transformer: bool = True`.

```python
def build_pipeline(use_transformer: bool = True, **kwargs) -> Language:
    nlp = spacy.blank("he")
    
    if use_transformer:
        try:
            nlp.add_pipe("kadima_transformer", first=True)
        except Exception as e:
            logger.warning(f"Transformer unavailable: {e}, falling back to rule-based")
    
    nlp.add_pipe("kadima_sent_split")
    nlp.add_pipe("kadima_morph")
    # ...
    return nlp
```

**Зависимости:** R-1.2

**Критерий:**
- `build_pipeline(use_transformer=True)` → pipeline с transformer, doc[i].vector существует
- `build_pipeline(use_transformer=False)` → pipeline без transformer, backward compatible

**Тесты:**
- Тест с transformer=True → проверка vectors
- Тест с transformer=False → проверка что pipeline работает без vectors
- Тест что все существующие тесты проходят в обоих режимах

**Коммит:** `feat(nlp): add use_transformer flag to pipeline builder (R-1.3)`

---

#### R-1.4 Graceful degradation

**Что:** В `KadimaTransformer.__init__()` — при невозможности загрузить модель (нет VRAM, нет модели, ImportError) → warning в лог → fallback на заглушку (doc без vectors, но не crash).

```python
def __init__(self, ...):
    try:
        self._load_model(model_name)
    except Exception as e:
        logger.warning(
            f"NeoDictaBERT unavailable ({e}). "
            f"Pipeline will work without transformer embeddings."
        )
        self._model = None
    
    def __call__(self, doc):
        if self._model is None:
            return doc  # no-op, graceful degradation
        # ... normal processing
```

**Зависимости:** R-1.2

**Критерий:** На машине без GPU pipeline стартует с warning, работает rule-based. Не crash.

**Тест:** Мокать `transformers.AutoModel.from_pretrained` → raise Exception → pipeline работает без crash.

**Коммит:** `feat(nlp): graceful degradation when NeoDictaBERT unavailable (R-1.4)`

---

#### R-1.5 Обновить pyproject.toml — NLP в core

**Что:** Перенести из optional в core:
- `hebpipe>=0.2`
- `numpy>=1.26,<2.0`
- `scipy>=1.12,<2.0`
- `pandas>=2.1,<3.0`

Оставить в optional:
- `[gui]` — PyQt6
- `[annotation]` — label-studio-sdk (новая группа)
- `[llm]` — llama-cpp-python
- `[gpu]` — torch, TTS, openai-whisper
- `[ml]` — phonikud-onnx, onnxruntime, yake

**Зависимости:** R-1.1

**Критерий:** `pip install kadima` → `kadima pipeline "שלום"` работает без `[ml]` флага.

**Коммит:** `fix(deps): move NLP dependencies to core, add annotation group (R-1.5)`

---

#### R-1.6 spaCy config.cfg

**Что:** Создать `config/config.cfg` — формальный spaCy config с полной pipeline конфигурацией:

```ini
[nlp]
lang = "he"
pipeline = ["kadima_transformer", "kadima_sent_split", "kadima_morph",
            "ngram_extractor", "np_chunker", "noise_classifier"]

[components.kadima_transformer]
factory = "kadima_transformer"

[components.kadima_transformer.model]
@architectures = "spacy-transformers.TransformerModel.v3"
name = "dicta-il/neodictabert"

[components.kadima_sent_split]
factory = "kadima_sent_split"

[components.kadima_morph]
factory = "kadima_morph"

[components.ngram_extractor]
factory = "ngram_extractor"
min_n = 2
max_n = 5

[components.np_chunker]
factory = "np_chunker"

[components.noise_classifier]
factory = "noise_classifier"
```

**Зависимости:** R-1.2

**Критерий:** `spacy debug data config.cfg` не падает на валидации.

**Коммит:** `feat(config): add spaCy config.cfg with transformer backbone (R-1.6)`

---

### Tier 2: Расширенное качество (v1.x) — ~45–60 часов

#### R-2.1 M5 NP Chunker — transformer-based

**Что:** Переписать `kadima/engine/np_chunker.py` (105 строк) — добавить режим `embeddings`:

- Вход: `Doc` с `.vector` (из NeoDictaBERT)
- Классификация: Tok2Vec → reduce_mean pooling → линейный классификатор → NP-boundary
- Fallback: если `.vector` нет → текущие правила (backward compatible)

**Зависимости:** R-1.2

**Конфигурация:**
```yaml
np_chunker:
  mode: "embeddings"  # "embeddings" | "rules" | "auto"
```

**Критерий:** NP chunking на тестовом корпусе показывает улучшение recall vs rule-based версия.

**Тесты:**
- `tests/engine/test_np_chunker.py` — дополнить тестами с embeddings
- Сравнение: rules vs embeddings на gold corpus

**Коммит:** `feat(engine): M5 NP Chunker with transformer embeddings (R-2.1)`

---

#### R-2.2 NER — NeoDictaBERT backend

**Что:** Расширить `kadima/engine/ner_extractor.py` (314 строк) — добавить backend `"neodictabert"`:

- spaCy NER component на базе NeoDictaBERT transformer
- Config: `backend: "neodictabert"`
- Fallback: если модель недоступна → HeQ-NER → rules

**Зависимости:** R-1.2

**Критерий:** `backend="neodictabert"` возвращает NER-результаты. Fallback chain: neodictabert → heq_ner → rules.

**Тесты:**
- Тест с neodictabert backend → проверка entity labels
- Тест fallback chain при недоступности модели

**Коммит:** `feat(engine): M17 NER with NeoDictaBERT backend (R-2.2)`

---

#### R-2.3 NER training pipeline (Label Studio → spaCy)

**Что:** Реализовать в `kadima/annotation/ml_backend.py`:

1. Экспорт аннотаций из Label Studio (через LS API)
2. Конвертация LS JSON → CoNLL-U формат
3. Конвертация CoNLL-U → spaCy training data (`Example` objects)
4. Запуск `spacy train` на NeoDictaBERT backbone

**Зависимости:** R-2.2

**Критерий:** Экспорт NER-аннотаций из LS → формат пригодный для `spacy train config.cfg`.

**Тест:** Фикстура LS-annotations → CoNLL-U → spaCy Examples. Проверка round-trip.

**Коммит:** `feat(annotation): NER training pipeline — LS export to spaCy format (R-2.3)`

---

#### R-2.4 KB embedding search

**Что:** Расширить `kadima/kb/search.py`:

```python
class KBSearch:
    def search_by_embedding(self, query_vector: np.ndarray, 
                            top_k: int = 5) -> List[KBTerm]:
        """Поиск по cosine similarity между NeoDictaBERT vectors."""
        similarities = cosine_similarity(query_vector, self._all_vectors)
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        return [self._terms[i] for i in top_indices]
```

**Зависимости:** R-1.2

**Конфигурация:**
```yaml
kb:
  embedding_search: true
  top_k: 5
  similarity_threshold: 0.7
```

**Критерий:** Поиск «פלדה» находит связанные термины (סגסוגת, מתכת) по semantic similarity.

**Тест:** Фикстура KB с embedding vectors → search → проверка что найдены связанные термины.

**Коммит:** `feat(kb): embedding-based search via NeoDictaBERT vectors (R-2.4)`

---

#### R-2.5 Term clustering

**Что:** Создать `kadima/engine/term_clusterer.py`:

- Вход: список Term с embedding vectors
- Алгоритм: k-means или HDBSCAN
- Выход: List[Cluster] — группы семантически близких терминов

**Зависимости:** R-2.4

**Критерий:** Термины группируются в тематические кластеры (металлургия, механика, и т.д.).

**Тест:** Фикстура терминов с vectors → clustering → проверка что related terms в одном кластере.

**Коммит:** `feat(engine): term clustering via embedding similarity (R-2.5)`

---

#### R-2.6 SQLAlchemy migration

**Что:** Переписать `kadima/data/`:

- `db.py` — SQLAlchemy Engine + Session вместо `sqlite3.connect()`
- `models.py` — SQLAlchemy declarative models (Base, Corpus, Document, Token, и т.д.)
- `repositories.py` — SQLAlchemy queries вместо raw SQL
- Миграции — Alembic вместо ручных `.sql` файлов

**Зависимости:** нет (независимый блок)

**Критерий:**
- `pip install kadima` + `kadima --init` создаёт БД через SQLAlchemy
- Все существующие тесты проходят
- `alembic revision --autogenerate` работает

**Тесты:** Все существующие `test_data_layer.py`, `test_config.py` — должны пройти без изменений.

**Коммит:** `refactor(data): migrate from sqlite3 to SQLAlchemy (R-2.6)`

---

#### R-2.7 Async data layer

**Что:** После R-2.6 — добавить `aiosqlite` + SQLAlchemy async sessions в FastAPI endpoints.

**Зависимости:** R-2.6

**Критерий:** API endpoints работают через `async def`, не блокируют event loop.

**Тест:** `tests/integration/test_api_async.py` — параллельные запросы не блокируют друг друга.

**Коммит:** `feat(api): async data layer with aiosqlite (R-2.7)`

---

#### R-2.8 Model download script

**Что:** Обновить `scripts/download_models.sh` — скачивание всех моделей:

1. NeoDictaBERT (`dicta-il/neodictabert`) → через `transformers` cache
2. Dicta-LM 3.0 1.7B GGUF → `~/.kadima/models/`
3. (опционально) Dicta-LM 3.0 12B GGUF

**Критерий:** `./scripts/download_models.sh` — все модели скачаны, pipeline работает.

**Коммит:** `feat(scripts): complete model download script for all backends (R-2.8)`

---

### Tier 3: UI (v1.x–v2.0) — ~36–54 часа

#### R-3.1 Dashboard

**Что:** Реализовать `kadima/ui/dashboard.py` — главное окно приложения (PyQt6).

**Структура:**
```
QMainWindow
├── QMenuBar (File, Pipeline, View, Help)
├── QStackedWidget
│   ├── DashboardView (status cards, recent runs)
│   ├── PipelineView (config, run, progress)
│   ├── ResultsView (terms table, ngrams table, NP table)
│   ├── ValidationView (PASS/WARN/FAIL report)
│   ├── KBView (search, browse, clustering)
│   └── AnnotationView (Label Studio integration)
├── QStatusBar (pipeline status, model info)
```

**Зависимости:** R-2.6

**Критерий:** `kadima gui` открывает окно, отображает статус pipeline.

**Коммит:** `feat(ui): implement main dashboard with navigation (R-3.1)`

---

#### R-3.2 Pipeline Configuration UI

**Что:** `kadima/ui/pipeline_view.py` — форма:
- Выбор профиля (precise/balanced/recall) — QComboBox
- Включение/отключение модулей — QCheckBox
- Пороговые значения (min_freq, pmi_threshold) — QSpinBox
- Кнопка "Запустить" — запускает pipeline

**Зависимости:** R-3.1

**Критерий:** Можно выбрать профиль, запустить pipeline, увидеть прогресс.

**Коммит:** `feat(ui): pipeline configuration and run controls (R-3.2)`

---

#### R-3.3 Results View

**Что:** `kadima/ui/results_view.py` — табличное представление:
- Terms table (surface, freq, PMI, LLR, rank) — QTableWidget
- N-grams table
- NP chunks table
- Сортировка по колонкам
- Экспорт в CSV

**Зависимости:** R-3.1

**Критерий:** Результаты pipeline отображаются в таблице, сортируются, экспортируются.

**Коммит:** `feat(ui): results view with sortable tables and CSV export (R-3.3)`

---

#### R-3.4 Validation Report UI

**Что:** Отображение PASS/WARN/FAIL отчётов: зелёные/жёлтые/красные строки, summary, drill-down.

**Зависимости:** R-3.1

**Коммит:** `feat(ui): validation report view with PASS/WARN/FAIL indicators (R-3.4)`

---

### Tier 4: Phase 2 модули (v1.x) — ~22–30 часов

#### R-4.1 M18 Sentiment Classifier

**Что:** Создать `kadima/engine/sentiment.py`:

- Backend: `hebrew-sentiment` (transformer-based) или rules
- Вход: текст → Выход: polarity (positive/negative/neutral) + confidence
- API endpoint: `POST /api/v1/generative/sentiment`

**Критерий:** API возвращает polarity для ивритского текста.

**Тесты:** Фикстуры positive/negative/neutral текстов → проверка polarity.

**Коммит:** `feat(engine): M18 Sentiment Classifier (R-4.1)`

---

#### R-4.2 M15 TTS

**Что:** Создать `kadima/engine/tts.py`:

- Backend: `TTS` library (Coqui / OpenTTS)
- Вход: текст на иврите → Выход: аудио-файл (WAV)
- API endpoint: `POST /api/v1/generative/tts` → returns audio

**Критерий:** API возвращает аудио-файл для ивритского текста.

**Коммит:** `feat(engine): M15 Text-to-Speech (R-4.2)`

---

#### R-4.3 M16 STT

**Что:** Создать `kadima/engine/stt.py`:

- Backend: `openai-whisper` (medium model, Hebrew)
- Вход: аудио-файл → Выход: транскрипция
- API endpoint: `POST /api/v1/generative/stt`

**Критерий:** API принимает аудио, возвращает транскрипцию на иврите.

**Коммит:** `feat(engine): M16 Speech-to-Text with Whisper (R-4.3)`

---

#### R-4.4 M20 Active Learning

**Что:** Создать `kadima/engine/active_learning.py`:

- Confidence scores из NER/term extraction
- Uncertainty sampling: выбор lowest-confidence predictions
- Экспорт выбранных примеров в Label Studio (JSON import)
- API endpoint: `POST /api/v1/annotation/active-learning`

**Зависимости:** R-2.2 (NER с confidence)

**Критерий:** Система предлагает аннотатору наиболее информативные примеры.

**Коммит:** `feat(engine): M20 Active Learning with uncertainty sampling (R-4.4)`

---

### Tier 5: Phase 3 модули (v2.0) — ~11–16 часов

#### R-5.1 M24 Keyphrase Extractor

**Что:** Создать `kadima/engine/keyphrase.py`:

- Backend: YAKE (unsupervised)
- Вход: текст → Выход: ranked keyphrases
- API endpoint: `POST /api/v1/generative/keyphrase`

**Критерий:** API возвращает ranked keyphrases для ивритского текста.

**Коммит:** `feat(engine): M24 Keyphrase Extractor with YAKE (R-5.1)`

---

#### R-5.2 M23 Grammar Checker

**Что:** Создать `kadima/engine/grammar.py`:

- Backend: LLM (Dicta-LM 3.0) через `llm/service.py`
- Вход: текст → Выход: grammar issues с исправлениями
- API endpoint: `POST /api/v1/generative/grammar`

**Зависимости:** LLM service (уже реализован)

**Критерий:** API принимает текст, возвращает grammar issues.

**Коммит:** `feat(engine): M23 Grammar Checker via Dicta-LM (R-5.2)`

---

#### R-5.3 M25 Summarizer

**Что:** Создать `kadima/engine/summarizer.py`:

- Backend: LLM (Dicta-LM 3.0) через `llm/service.py`
- Вход: длинный текст → Выход: summary
- API endpoint: `POST /api/v1/generative/summarize`

**Зависимости:** LLM service

**Критерий:** API принимает текст, возвращает summary.

**Коммит:** `feat(engine): M25 Summarizer via Dicta-LM (R-5.3)`

---

### Tier 6: Infrastructure & Docs — ~6–10 часов

#### R-6.1 Обновить документацию

**Что:** Синхронизировать `CLAUDE.md` и `doc/` с текущим состоянием кода:
- M3 — убрать пометку STUB
- B1–B4 — пометить как resolved
- Phase 1 — пометить как completed
- Добавить описание Tier 1–5 требований

**Коммит:** `docs: sync documentation with current codebase state (R-6.1)`

---

#### R-6.2 Docker Compose — production-ready

**Что:** Проверить и доработать `docker-compose.yml`:
- KADIMA API + Label Studio + llama.cpp + GPU profile
- Healthchecks, volumes, environment variables
- Model download при первом запуске

**Коммит:** `fix(docker): production-ready Docker Compose with all profiles (R-6.2)`

---

## 4. Порядок реализации

```
Tier 1 (база):
  R-1.1 → R-1.2 → R-1.3 → R-1.4 → R-1.5 → R-1.6
        ↓
Tier 2 (качество):
  R-2.1 → R-2.2 → R-2.3 → R-2.4 → R-2.5
  R-2.6 → R-2.7 (параллельно с R-2.x)
  R-2.8 (параллельно)
        ↓
Tier 3 (UI):
  R-3.1 → R-3.2 → R-3.3 → R-3.4
        ↓
Tier 4 (Phase 2):
  R-4.1 → R-4.2 → R-4.3 → R-4.4
        ↓
Tier 5 (Phase 3):
  R-5.1 → R-5.2 → R-5.3
        ↓
Tier 6 (Infrastructure):
  R-6.1 → R-6.2
```

**Зависимости между tier:**
- Tier 2 (R-2.1–R-2.5) зависит от Tier 1 (R-1.2)
- Tier 2 (R-2.6–R-2.7) независим от Tier 1
- Tier 3 зависит от Tier 2 (R-2.6)
- Tier 4–5 независимы от Tier 1–3 (кроме R-4.4, который зависит от R-2.2)
- Tier 6 независим

---

## 5. Критерии приёмки

### По Tier

| Tier | Критерий готовности |
|---|---|
| Tier 1 | `nlp(text)` возвращает doc с transformer vectors (768-dim). `pip install kadima` работает без флагов. Все 500+ тестов проходят. |
| Tier 2 | M5 работает на embeddings. NER имеет neodictabert backend. KB search — embedding-based. SQLAlchemy заменяет sqlite3. |
| Tier 3 | `kadima gui` открывает окно с Dashboard, Pipeline, Results, Validation views. |
| Tier 4 | API endpoints для Sentiment, TTS, STT, Active Learning работают. |
| Tier 5 | API endpoints для Keyphrase, Grammar, Summarizer работают. |
| Tier 6 | Документация актуальна. Docker Compose поднимает полный стек. |

### Общие

- Все существующие тесты проходят после каждого шага
- Каждый шаг — отдельный git commit
- Нет регрессий в NLP pipeline (M1–M8, M12)
- Graceful degradation при отсутствии GPU/моделей

---

## 6. Оценка

| Tier | Набор | Часы |
|---|---|---|
| Tier 1 | Transformer backbone (база) | 25–35 |
| Tier 2 | Embeddings + SQLAlchemy | 45–60 |
| Tier 3 | UI (PyQt Desktop) | 36–54 |
| Tier 4 | Phase 2 модули | 22–30 |
| Tier 5 | Phase 3 модули | 11–16 |
| Tier 6 | Infrastructure + Docs | 6–10 |
| **Всего** | | **145–205 часов** |

---

## 7. Риски

| Риск | Вероятность | Влияние | Митигация |
|---|---|---|---|
| NeoDictaBERT не влезает в VRAM | Низкое | Блокер для Tier 1–2 | FP16, graceful degradation (R-1.4) |
| HebPipe API нестабилен | Среднее | M3 деградирует | Rule-based fallback (уже есть) |
| SQLAlchemy migration ломает тесты | Среднее | Блокер | Пошаговая миграция, backward compat |
| PyQt6 не установлен | Среднее | Tier 3 невозможен | Optional dependency, fallback на CLI/API |
| LLM server не запущен | Среднее | Phase 3 невозможен | Graceful degradation, fallback на rules |
| Сроки Tier 3 (UI) | Высокое | Задержка релиза | UI — отдельная фаза, может быть отложена |
