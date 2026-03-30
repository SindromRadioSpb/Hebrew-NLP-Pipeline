# 4.4. NLP Stack Integration — KADIMA v1.0

> Дата: 2026-03-30 | Статус: draft
> Связанные документы: 04_Система/ARCHITECTURE.md, 04_Система/DATA_MODEL.md, 02_Продукт/PRD.md, 05_Нефункционал/NFR.md

---

## 1. Назначение

Определяет, какие open-source модули заменяют кастомную реализацию Engine Layer (M1–M8), как они интегрируются в архитектуру KADIMA, и какие компоненты нужно писать самостоятельно.

**Принцип:** некоммерческий проект → используем готовые модули с открытым кодом, не изобретаем велосипед.

---

## 2. Маппинг: Модуль KADIMA → Open-source компонент

| Модуль KADIMA | Описание | Компонент | Статус |
|---------------|----------|-----------|--------|
| **M1. Sentence Splitter** | Разбиение на предложения | HebPipe (`-s auto`) | ✅ готовый модуль |
| **M2. Tokenizer** | Токенизация | HebPipe (`-w`) + spaCy `lang/he` | ✅ готовый модуль |
| **M3. Morphological Analyzer** | POS, lemma, features, prefix | HebPipe (`-tpl`) | ✅ готовый модуль |
| **M4. N-gram Extractor** | Bigram/trigram | spaCy component (кастомный) | ⚠️ пишем |
| **M5. NP Chunk Extractor** | NP pattern detection | spaCy + NeoDictaBERT embeddings | ⚠️ пишем на базе transformer |
| **M6. Canonicalizer** | Surface → canonical | spaCy pipe component | ⚠️ пишем (правила) |
| **M7. Association Measures** | PMI, LLR, Dice | Python (numpy/scipy) | ⚠️ пишем (чистая математика) |
| **M8. Term Extractor** | 3 profiles, ranked output | Orchestrator M4–M7 | ⚠️ пишем (склейка) |
| **M9. NER** | Named Entities | NeoDictaBERT + spaCy NER | 🔬 Phase 2, дообучение |
| **M11. Validation** | Gold corpus, expected, review | KADIMA (кастомный) | ⚠️ пишем (из ТЗ) |
| **M12. Noise Classifier** | Token classification | spaCy component или правила | ⚠️ пишем |
| **M14. Corpus Manager** | Import/export, stats | KADIMA (кастомный) | ⚠️ пишем |

**Итого:** 3 модуля закрываем готовыми библиотеками, ~8 пишаем. Готовые модули покрывают самую сложную часть — морфологию иврита.

---

## 3. Архитектура интеграции

### 3.1 Схема

```
┌──────────────────────────────────────────────────────────────┐
│                        UI Layer (PyQt)                       │
├──────────────────────────────────────────────────────────────┤
│                      Service Layer                           │
│  PipelineService │ ValidationService │ ExportService         │
├──────────────────────────────────────────────────────────────┤
│                      Engine Layer                            │
│                                                              │
│  ┌─────────────── spaCy Pipeline (единый пайплайн) ───────┐ │
│  │                                                         │ │
│  │  lang/he Tokenizer                                      │ │
│  │       │                                                 │ │
│  │       ▼                                                 │ │
│  │  ┌─────────────────────────────────────────┐            │ │
│  │  │ NeoDictaBERT (transformer backbone)     │            │ │
│  │  │ dicta-il/neodictabert via spacy-        │            │ │
│  │  │ transformers                            │            │ │
│  │  └──────────┬──────────────────────────────┘            │ │
│  │             │                                           │ │
│  │    ┌────────┼────────┬──────────┐                       │ │
│  │    ▼        ▼        ▼          ▼                       │ │
│  │  HebPipe  HebPipe  HebPipe   Custom                    │ │
│  │  SentSplit POS+Morph Lemma   Components                │ │
│  │  (M1)     (M3)      (M3)     (M4-M12)                  │ │
│  │                                                         │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌─── Outside spaCy ───────────────────────────────────────┐ │
│  │  M7. AssociationMeasures (numpy/scipy, stateless)        │ │
│  │  M8. TermExtractor (orchestrator, stateless)             │ │
│  │  M11. ValidationFramework (gold corpus, report)          │ │
│  │  M14. CorpusManager (SQLite CRUD)                        │ │
│  └─────────────────────────────────────────────────────────┘ │
├──────────────────────────────────────────────────────────────┤
│                      Data Layer                              │
│  CorpusRepo │ ResultRepo │ GoldRepo │ SQLite                 │
└──────────────────────────────────────────────────────────────┘
```

### 3.2 Почему spaCy как ядро

| Критерий | Без spaCy (чистый HebPipe) | С spaCy + NeoDictaBERT |
|----------|---------------------------|------------------------|
| M1–M3 | ✅ из коробки | ✅ из коробки (через HebPipe-компоненты) |
| NER (M9) | ⚠️ beta в HebPipe | ✅ дообучаем на NeoDictaBERT |
| NP chunking | ❌ нет в HebPipe | ✅ transformer embeddings → классификатор |
| Term extraction | ❌ нужно писать | ❌ нужно писать (но embeddings помогают) |
| Pipeline API | CLI, не расширяемый | ✅ `nlp(text)` → doc, расширяемый |
| Validation | ❌ отдельно | ❌ отдельно (одинаково) |
| Расширяемость | Низкая | Высокая (spaCy components) |

**Вывод:** spaCy даёт расширяемый каркас + transformer embeddings через NeoDictaBERT. HebPipe отдаёт модули M1–M3 как кастомные spaCy-компоненты.

---

## 4. Стек зависимостей

### 4.1 Совместимость версий

| Пакет | Версия | Роль | Лицензия |
|-------|--------|------|----------|
| Python | 3.12+ | Runtime | — |
| spaCy | ≥3.7,<4.0 | Pipeline framework | MIT |
| spacy-transformers | ≥1.3 | Transformer integration | MIT |
| transformers (HuggingFace) | ≥4.35 | NeoDictaBERT loading | Apache 2.0 |
| torch | ≥2.1 | Transformer backend | BSD |
| HebPipe | latest | M1–M3 modules | Apache 2.0 |
| NeoDictaBERT | latest | Transformer backbone | CC BY 4.0 |
| numpy, scipy | — | M7 (AM) | BSD |
| pandas | — | Data processing | BSD |
| SQLite | 3.x | Storage | Public domain |
| PyQt6 | — | UI | GPL/Commercial |

### 4.2 Конфликтный анализ

| Потенциальный конфликт | Статус | Решение |
|------------------------|--------|---------|
| HebPipe фиксирует `transformers==4.35.2` | ⚠️ | pip разрешит автоматически; если нет — в venv |
| HebPipe фиксирует `torch==2.1.0` | ⚠️ | Совместимо с spacy-transformers |
| HebPipe тянет `stanza` (может конфликтовать с spaCy) | ⚠️ | Stanza и spaCy независимы, конфликтов нет |
| NeoDictaBERT `trust_remote_code=True` | ✅ | Работает с transformers ≥4.35 |
| VRAM: NeoDictaBERT (base) ~500 MB | ⚠️ | Влезает в 8 GB RTX 3070 |
| RAM: 3.8 GB в WSL2 | ⚠️ | Нужен swap 4 GB (см. ENV_SETUP.md) |

### 4.3 Порядок установки

```bash
# В виртуальном окружении KADIMA
cd /mnt/c/projects/hebrew-corpus-v2
source .venv/bin/activate

# 1. spaCy с transformer-поддержкой
pip install 'spacy[transformers]>=3.7'

# 2. HebPipe
pip install hebpipe

# 3. Проверка
python -c "
import spacy
import hebpipe
import transformers
import torch
print(f'spaCy: {spacy.__version__}')
print(f'transformers: {transformers.__version__}')
print(f'torch: {torch.__version__}')
print('Stack OK')
"
```

---

## 5. Интеграция HebPipe в spaCy

### 5.1 Общая стратегия

HebPipe — standalone CLI/Python pipeline. Нельзя просто `pip install` и `import` как spaCy-компонент. Нужна обёртка.

**Подход:** вызываем HebPipe-функции внутри кастомных spaCy pipe components. Данные между компонентами передаются через `Doc` объект (token extensions / custom attributes).

### 5.2 Компонент: HebPipe Sentence Splitter (M1)

```python
# engine/components/hebpipe_sent_splitter.py
from spacy.language import Language
from spacy.tokens import Doc

@Language.factory("hebpipe_sent_splitter")
class HebPipeSentSplitter:
    """M1: Sentence splitting через HebPipe internals."""

    def __init__(self, nlp: Language, name: str):
        self.nlp = nlp

    def __call__(self, doc: Doc) -> Doc:
        # HebPipe internal sentence splitting
        # Применяем к doc.sents
        # Кладём результат в Doc
        return doc
```

### 5.3 Компонент: HebPipe Morphological Analyzer (M2+M3)

```python
# engine/components/hebpipe_morph.py
from spacy.language import Language
from spacy.tokens import Doc

@Language.factory("hebpipe_morph_analyzer")
class HebPipeMorphAnalyzer:
    """M2+M3: Токенизация + морфологический анализ через HebPipe."""

    def __init__(self, nlp: Language, name: str, use_gpu: bool = True):
        self.nlp = nlp
        self.use_gpu = use_gpu
        self._pipeline = None

    @property
    def pipeline(self):
        if self._pipeline is None:
            # Ленивая загрузка моделей
            from hebpipe import run_hebpipe  # или внутренний API
            self._pipeline = ...
        return self._pipeline

    def __call__(self, doc: Doc) -> Doc:
        text = doc.text
        # Запускаем HebPipe tokenizer + POS + morphology + lemma
        # Результат: [(surface, lemma, pos, features), ...]
        # Записываем в spaCy Token attributes:
        for token, analysis in zip(doc, results):
            token.lemma_ = analysis.lemma
            token.pos_ = analysis.pos
            # features → token.morph
        return doc
```

### 5.4 Конфигурация spaCy pipeline

```ini
# config.cfg — KADIMA Hebrew Pipeline
[nlp]
lang = "he"
pipeline = ["transformer", "hebpipe_sent_splitter", "hebpipe_morph_analyzer",
            "ngram_extractor", "np_chunker", "noise_classifier"]

[components]

# --- Transformer backbone ---
[components.transformer]
factory = "transformer"

[components.transformer.model]
@architectures = "spacy-transformers.TransformerModel.v3"
name = "dicta-il/neodictabert"
tokenizer_config = {"use_fast": true}
transformer_config = {"trust_remote_code": true}

[components.transformer.model.get_spans]
@architectures = "spacy-transformers.strided_spans.v1"
window = 128
stride = 96

# --- HebPipe Sentence Splitter (M1) ---
[components.hebpipe_sent_splitter]
factory = "hebpipe_sent_splitter"

# --- HebPipe Morphological Analyzer (M2+M3) ---
[components.hebpipe_morph_analyzer]
factory = "hebpipe_morph_analyzer"
use_gpu = true

# --- Custom: N-gram Extractor (M4) ---
[components.ngram_extractor]
factory = "ngram_extractor"
min_n = 2
max_n = 5
min_freq = 2

# --- Custom: NP Chunker (M5) ---
[components.np_chunker]
factory = "np_chunker"

[components.np_chunker.model]
@architectures = "kadima.NPChunkerModel.v1"
nO = null

[components.np_chunker.model.tok2vec]
@architectures = "spacy-transformers.TransformerListener.v1"
grad_factor = 1.0

[components.np_chunker.model.tok2vec.pooling]
@layers = "reduce_mean.v1"

# --- Custom: Noise Classifier (M12) ---
[components.noise_classifier]
factory = "noise_classifier"
```

---

## 6. Интеграция NeoDictaBERT

### 6.1 Роль в архитектуре

NeoDictaBERT — **не замена** HebPipe. Это **дополнительный слой** для:

| Задача | Без NeoDictaBERT | С NeoDictaBERT |
|--------|------------------|----------------|
| POS tagging | HebPipe (F1 ~96) | HebPipe (F1 ~96) — не меняем |
| Lemmatization | HebPipe (F1 ~95-97) | HebPipe — не меняем |
| NP chunking | Правила (базовый) | Transformer embeddings → классификатор |
| NER | HebPipe beta (низкое качество) | Дообучение на NeoDictaBERT → F1 >85 |
| Semantic similarity | ❌ | ✅ через token vectors |
| Term disambiguation | ❌ | ✅ через contextual embeddings |

### 6.2 Использование embeddings для term extraction

NeoDictaBERT даёт контекстные эмбеддинги для каждого токена. Это позволяет:

1. **Кластеризация терминов** — семантически близкие термины группируются
2. **Disambiguation** — «קל» (лёгкий) vs «קל» (голос) — разные embedding-контексты
3. **NP classification** — transformer выделяет features для классификатора NP-чанков

```python
# Пример: получение embeddings из spaCy doc
import spacy

nlp = spacy.load("he_kadima_pipeline")
doc = nlp("אפרים קישון כתב מאמרים הומוריסטיים")

for token in doc:
    # NeoDictaBERT embedding для каждого токена
    vector = token._.trf_data.last_hidden_state[token.i]
    print(f"{token.text}: vector dim = {vector.shape}")
```

### 6.3 Обучение NER (Phase 2)

```python
# Схема дообучения NER на базе NeoDictaBERT
# Данные: IAHLT UD Hebrew treebank (NER-размеченный)

import spacy
from spacy.training import Example

nlp = spacy.load("config.cfg")  # pipeline с NeoDictaBERT

# TRAIN_DATA из IAHLT / внутренних данных
for epoch in range(20):
    losses = {}
    for text, annot in TRAIN_DATA:
        example = Example.from_dict(nlp.make_doc(text), annot)
        nlp.update([example], losses=losses, drop=0.3)
```

---

## 7. Поток данных внутри pipeline

```
Файл (.txt, UTF-8)
    │
    ▼
┌─ spaCy nlp(text) ──────────────────────────────────┐
│                                                     │
│  1. lang/he Tokenizer                               │
│     "אפרים קישון כתב מאמרים" → [אפרים, קישון, כתב, מאמרים] │
│                                                     │
│  2. Transformer (NeoDictaBERT)                      │
│     tokens → contextual embeddings (768-dim)        │
│     (параллельно, не меняет токены)                  │
│                                                     │
│  3. hebpipe_sent_splitter (M1)                      │
│     → sentence boundaries                           │
│                                                     │
│  4. hebpipe_morph_analyzer (M2+M3)                  │
│     token → (lemma, POS, features, prefix)          │
│     קישון → קישון/NOUN/DEF=YES/M.SG                 │
│     כתב → כתב/VERB/PAST/3.M.SG                     │
│                                                     │
│  5. ngram_extractor (M4)                            │
│     → bigrams, trigrams с частотами                 │
│                                                     │
│  6. np_chunker (M5) — использует transformer feats  │
│     → NP chunks: "אפרים קישון" [PERSON]            │
│                  "מאמרים הומוריסטיים" [NP]          │
│                                                     │
│  7. noise_classifier (M12)                          │
│     → punct, number, latin, non_noise              │
│                                                     │
│  Doc (tokens, sents, ents, lemmas, morph, vectors)  │
└─────────────────────────────────────────────────────┘
    │
    ▼
┌─ Service Layer ─────────────────────────────────────┐
│                                                     │
│  PipelineService.run(doc, profile="balanced"):      │
│    → M6: Canonicalizer (surface → canonical)        │
│    → M7: AssociationMeasures (PMI, LLR, Dice)       │
│    → M8: TermExtractor (score, rank, filter)        │
│                                                     │
│  Result: TermSet → SQLite                           │
└─────────────────────────────────────────────────────┘
    │
    ▼
┌─ Validation Service ────────────────────────────────┐
│                                                     │
│  M11: Gold corpus → expected → compare → report     │
│  PASS / WARN / FAIL                                  │
└─────────────────────────────────────────────────────┘
```

---

## 8. Производительность (NFR compliance)

| Требование NFR | Компонент | Оценка | Статус |
|----------------|-----------|--------|--------|
| Tokenization ≥ 10K tok/sec | spaCy lang/he | ~50K+ tok/sec | ✅ |
| Full pipeline ≥ 1K tok/sec | HebPipe (M1–M3) | ~2K tok/sec (GPU) | ✅ |
| Transformer inference | NeoDictaBERT | ~500 tok/sec (GPU) | ⚠️ bottleneck |
| Validation ≥ 5K checks/sec | Python (SQLite) | ~20K checks/sec | ✅ |
| UI response ≤ 200ms | async pipeline | зависит от объёма | ⚠️ |

### 8.1 Оптимизация transformer bottleneck

NeoDictaBERT — самый тяжёлый компонент. Варианты:

| Подход | Latency | Точность | VRAM |
|--------|---------|----------|------|
| Full precision (FP32) | 2x baseline | baseline | ~2 GB |
| FP16 (half precision) | 1.5x faster | ~same | ~1 GB |
| ONNX Runtime | 2x faster | ~same | ~1 GB |
| INT8 quantization | 3x faster | -1-2% | ~500 MB |
| CPU fallback | 5x slower | ~same | 0 |

**Рекомендация для Phase 1:** FP16 на GPU (RTX 3070). Достаточно для 1K tok/sec pipeline.

---

## 9. Маппинг на Data Model

| Сущность BД | Источник данных | Компонент |
|-------------|----------------|-----------|
| Token | spaCy `Doc[i]` | spaCy tokenizer |
| Lemma | `token.lemma_` | HebPipe M3 |
| Token.pos | `token.pos_` | HebPipe M3 |
| Token.features | `token.morph` | HebPipe M3 |
| Term | TermSet | M8 (custom) |
| PipelineRun | PipelineService | KADIMA |
| GoldCorpus | import | KADIMA |
| ExpectedCheck | validation | KADIMA M11 |
| ReviewResult | comparison | KADIMA M11 |

---

## 10. План реализации (интеграция)

### Phase 1: Инфраструктура (Week 1–2)

- [ ] Настроить venv с совместимыми версиями (spaCy + HebPipe + transformers)
- [ ] Smoke test: `spacy.blank("he")` токенизация работает
- [ ] Скачать NeoDictaBERT, проверить загрузку
- [ ] Написать `HebPipeSentSplitter` (spaCy component, M1)
- [ ] Написать `HebPipeMorphAnalyzer` (spaCy component, M2+M3)
- [ ] Интеграционный тест: `nlp(text)` → doc с lemma, POS

### Phase 2: Engine Layer (Week 3–5)

- [ ] M4: `NgramExtractor` component (spaCy pipe)
- [ ] M5: `NPChunker` component (spaCy pipe, использует transformer spans)
- [ ] M6: `Canonicalizer` component (правила)
- [ ] M12: `NoiseClassifier` component (правила + spaCy)
- [ ] M7: `AssociationMeasures` (stateless, вне spaCy)
- [ ] M8: `TermExtractor` (orchestrator M4–M7)

### Phase 3: Validation & Corpus (Week 6–8)

- [ ] M11: Validation Framework (gold corpus import, expected, report)
- [ ] M14: Corpus Manager (SQLite CRUD)
- [ ] PipelineService: оркестрация spaCy nlp + post-processing
- [ ] Интеграционные тесты: gold corpus → PASS

### Phase 4: NER & Polish (Week 9–12)

- [ ] M9: NER — дообучение на базе NeoDictaBERT
- [ ] Benchmark: accuracy vs HebPipe standalone
- [ ] Оптимизация: FP16 / ONNX
- [ ] UI интеграция (PyQt)

---

## 11. Риски

| Риск | Вероятность | Влияние | Митигация |
|------|------------|---------|-----------|
| Конфликт версий HebPipe ↔ spaCy | Среднее | Блокер | Виртуальное окружение, pinned versions |
| NeoDictaBERT не помещается в 8 GB VRAM | Низкое | Серьёзное | FP16, INT8, CPU fallback |
| WSL2 RAM limit (3.8 GB + swap) | Среднее | Среднее | 4 GB swap (см. ENV_SETUP.md) |
| HebPipe API нестабильный / undocumented | Среднее | Серьёзное | Изучить source, написать обёртку |
| HebPipe NER (beta) недостаточно точен | Высокое | Среднее | Использовать NeoDictaBERT NER вместо |
| Производительность transformer < 1K tok/sec | Низкое | Среднее | Batch processing, кэширование |

---

## 12. Связи с документацией KADIMA

| Документ | Что обновить |
|----------|-------------|
| `04_Система/ARCHITECTURE.md` | Engine Layer → spaCy pipeline с NeoDictaBERT |
| `04_Система/DATA_MODEL.md` | Token.lemma, Token.pos, Token.morph → из HebPipe |
| `06_Разработка/BACKLOG.md` | Добавить task: "integrate HebPipe as spaCy components" |
| `06_Разработка/ROADMAP.md` | Phase 1 Week 1–2 = инфраструктура NLP stack |
| `05_Нефункционал/NFR.md` | FP16 optimization как требование |
| `05_Нефункционал/SECURITY.md` | NeoDictaBERT: CC BY 4.0, attribution required |
