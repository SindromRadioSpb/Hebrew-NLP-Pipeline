# CLAUDE.md — Project Map for Claude Code

> **Язык проекта:** Python 3.10+ | **Пакет:** `kadima/` | **БД:** SQLite + миграции
> **Конвенции:** snake_case файлы/функции, PascalCase классы, UPPER_SNAKE константы
> **Таргет:** RTX 3060 (12GB VRAM) | **v0.9.0** → **v1.0.0** (генеративные модули)

---

## Куда класть код

| Что | Куда | Пример |
|-----|------|--------|
| NLP-процессор (M1–M8, M12) | `kadima/engine/<name>.py` | `term_extractor.py` |
| **Новые модули (M13–M25)** | `kadima/engine/<name>.py` | `diacritizer.py` |
| Pipeline оркестрация | `kadima/pipeline/` | `orchestrator.py`, `config.py` |
| Валидация / gold corpus | `kadima/validation/` | `check_engine.py` |
| Корпусный менеджер | `kadima/corpus/` | `importer.py`, `exporter.py` |
| Label Studio интеграция | `kadima/annotation/` | `ls_client.py`, `sync.py`, `ml_backend.py` |
| Knowledge Base | `kadima/kb/` | `repository.py`, `search.py` |
| LLM сервис | `kadima/llm/` | `client.py`, `prompts.py`, `service.py` |
| spaCy компоненты | `kadima/nlp/components/` | `hebpipe_*.py`, `*_component.py` |
| DB / миграции | `kadima/data/` | `db.py`, `models.py`, `migrations/XXX.sql` |
| REST API endpoints | `kadima/api/routers/` | `corpora.py`, `annotation.py` |
| Pydantic схемы API | `kadima/api/schemas.py` | — |
| PyQt UI виджеты | `kadima/ui/` + `kadima/ui/widgets/` | `dashboard.py`, `term_table.py` |
| Утилиты | `kadima/utils/` | `hebrew.py`, `logging.py` |
| Unit-тесты | `tests/<module>/test_<name>.py` | `tests/engine/test_term_extractor.py` |
| Integration тесты | `tests/integration/` | `test_pipeline_e2e.py` |
| Gold corpus fixtures | `tests/data/he_XX_*/` | `expected_counts.yaml`, `raw/*.txt` |
| Label Studio шаблоны | `templates/` | `hebrew_ner.xml` |

---

## Полная карта модулей (25 модулей)

### Engine Layer — существующие (M1–M8, M12)

| ID | Модуль | Файл | Вход → Выход | Статус |
|----|--------|------|--------------|--------|
| M1 | Sentence Splitter | `hebpipe_wrappers.py` | `str → SentenceSplitResult` | ✅ |
| M2 | Tokenizer | `hebpipe_wrappers.py` | `str → TokenizeResult` | ✅ |
| M3 | Morph Analyzer | `hebpipe_wrappers.py` | `List[Token] → MorphResult` | ✅ |
| M4 | N-gram Extractor | `ngram_extractor.py` | `List[List[Token]] → NgramResult` | ✅ |
| M5 | NP Chunker | `np_chunker.py` | `List[MorphAnalysis] → NPChunkResult` | ✅ |
| M6 | Canonicalizer | `canonicalizer.py` | `List[str] → CanonicalResult` | ✅ |
| M7 | Association Measures | `association_measures.py` | `List[Ngram] → AMResult` | ✅ |
| M8 | Term Extractor | `term_extractor.py` | `TermExtractInput → TermResult` | ✅ |
| M12 | Noise Classifier | `noise_classifier.py` | `List[Token] → NoiseResult` | ✅ |

### Engine Layer — новые модули (M13–M25)

| ID | Модуль | Файл | Модель | VRAM | Вход → Выход | Приоритет |
|----|--------|------|--------|------|--------------|-----------|
| M13 | Diacritizer | `diacritizer.py` | DictaBERT (phonikud-onnx) | <1GB | `str → str` (с никудом) | 🔴 |
| M14 | Translator | `translator.py` | mBART-50 (facebook/mbart-large-50-many-to-many-mmt) | 3GB | `str,lang,lang → str` | 🔴 |
| M15 | TTS Synthesizer | `tts_synthesizer.py` | XTTS v2 (Coqui) | 4GB | `str,lang → Path(WAV)` | 🔴 |
| M16 | STT Transcriber | `stt_transcriber.py` | Whisper large-v3 (openai-whisper) | 3-6GB | `Path(WAV) → str` | 🔴 |
| M17 | NER Extractor | `ner_extractor.py` | HeQ-NER (dicta-il) | <1GB | `str → List[Entity]` | 🔴 |
| M18 | Sentiment Analyzer | `sentiment_analyzer.py` | heBERT (avichr/heBERT_sentiment_analysis) | <1GB | `str → Dict{label,score}` | 🟡 |
| M19 | Summarizer | `summarizer.py` | mT5-base (google/mt5-base) | 2GB | `str → str` (summary) | 🟡 |
| M20 | QA Extractor | `qa_extractor.py` | AlephBERT (onlplab/alephbert-base) | <1GB | `str,str → Dict{answer,score}` | 🟡 |
| M21 | Morph Generator | `morph_generator.py` | Rules (без ML) | <100MB | `lemma,pos → List[MorphForm]` | 🟡 |
| M22 | Transliterator | `transliterator.py` | Rules + lookup | <100MB | `str ↔ str` (ktiv male↔haser) | 🟢 |
| M23 | Grammar Corrector | `grammar_corrector.py` | T5-hebrew / LLM | 2-4GB | `str → str` (исправленный) | 🟢 |
| M24 | Keyphrase Extractor | `keyphrase_extractor.py` | YAKE! / KeyBERT | <1GB | `str → List[str]` | 🟢 |
| M25 | Paraphraser | `paraphraser.py` | mT5 / LLM | 2-4GB | `str → List[str]` | ⚪ |

### Архитектура Processor Protocol

Каждый новый модуль должен реализовывать `ProcessorProtocol` из `kadima/engine/contracts.py`:

```python
@runtime_checkable
class ProcessorProtocol(Protocol):
    @property
    def name(self) -> str: ...          # "diacritizer"
    @property
    def module_id(self) -> str: ...     # "M13"
    def process(self, input_data: Any, config: Dict[str, Any]) -> Any: ...
```

**Дополнительно** для новых модулей — каждый должен иметь:

```python
class XxxProcessor(Processor):
    # Наследуется от kadima/engine/base.py::Processor

    def process(self, input_data, config): ...       # Обработка одного элемента
    def process_batch(self, inputs, config): ...     # Batch обработка
    def process_corpus(self, corpus_path, config): ... # Обработка корпуса
    def generate_expected(self, corpus_path): ...    # Генерация ground truth

    # Metrics (static methods)
    @staticmethod
    def metric_xxx(reference, actual) -> float: ...  # Метрика качества
```

---

## Pipeline Orchestrator — расширенный Data Flow

```
CLI/API/GUI
    ↓
Pipeline Orchestrator (pipeline/orchestrator.py)
    ↓
┌─── NLP Pipeline (существующий) ────────────────────────────┐
│ M1 SentSplit → M2 Token → M3 Morph →                     │
│ M4 Ngram → M5 NP → M6 Canonicalize →                     │
│ M7 AM → M8 TermExtract → M12 Noise                        │
└───────────────────────────────────────────────────────────┘
    ↓
┌─── Generative Pipeline (новый) ────────────────────────────┐
│ M13 Diacritize → огласованный текст                       │
│ M14 Translate → перевод (HE→EN/RU)                        │
│ M15 TTS → аудио (WAV)                                     │
│ M16 STT ← аудио (WAV) → текст (обратно к M1)             │
│ M17 NER → сущности (PER, LOC, ORG, ...)                   │
│ M18 Sentiment → тональность (pos/neg/neutral)             │
│ M19 Summarize → краткое содержание                        │
│ M20 QA → ответ на вопрос из контекста                     │
│ M21 MorphGen → парадигмы словоформ                        │
│ M22 Transliterate → ktiv male↔haser                       │
│ M23 GrammarCorrect → исправленный текст                   │
│ M24 Keyphrase → ключевые фразы                            │
│ M25 Paraphrase → переформулированный текст                 │
└───────────────────────────────────────────────────────────┘
    ↓
Data Layer (data/) ← SQLite + миграции
    ↑
Validation (validation/) ← gold corpus проверка
```

---

## Детализация новых модулей

### M13 — Diacritizer (ניקוד)
```python
# kadima/engine/diacritizer.py
from kadima.engine.base import Processor

class Diacritizer(Processor):
    """Добавляет огласовку (никуд) к неогласованному ивриту."""
    module_id = "M13"
    name = "diacritizer"

    def __init__(self, backend="phonikud", device="cuda"):
        # backend: "phonikud" (ONNX) | "dicta" (transformers)
        ...

    def process(self, text: str, config: dict) -> str:
        """Огласовать текст."""
        ...

    @staticmethod
    def char_accuracy(ref: str, hyp: str) -> float: ...
    @staticmethod
    def word_accuracy(ref: str, hyp: str) -> float: ...
    @staticmethod
    def strip_nikud(text: str) -> str: ...
```

**Зависимости:** `phonikud-onnx>=1.0.0` + `onnxruntime>=1.15.0`
**Модель:** `dicta-il/dictabert-large-char-menaked` (SOTA 2025-03, CC BY 4.0)
**Интеграция с M3:** Morph Analyzer может использовать огласованный текст для улучшения морфологического анализа

### M14 — Translator
```python
class Translator(Processor):
    """Перевод иврита на целевые языки."""
    module_id = "M14"

    def __init__(self, backend="mbart", device="cuda"):
        # backend: "mbart" (mBART-50, 50 langs) | "opus" (Helsinki-NLP, fast) | "nllb" (200 langs)
        ...

    def process(self, text: str, config: dict) -> str:
        # config: {"src_lang": "he", "tgt_lang": "en"}
        ...

    @staticmethod
    def bleu_score(ref: str, hyp: str) -> float: ...
```

**Зависимости:** `transformers>=4.35.0`, `torch>=2.0.0`, `sentencepiece>=0.1.99`
**Интеграция с API:** endpoint `POST /pipeline/translate`

### M15 — TTS Synthesizer
```python
class TTSSynthesizer(Processor):
    """Синтез речи из ивритского текста."""
    module_id = "M15"

    def __init__(self, backend="xtts", device="cuda", speaker_wav=None):
        # backend: "xtts" (XTTS v2, voice cloning) | "mms" (MMS-TTS-heb, fast) | "piper"
        ...

    def process(self, text: str, config: dict) -> Path:
        """Синтезировать WAV."""
        ...

    @staticmethod
    def estimate_duration(text: str, lang: str) -> float: ...
```

**Зависимости:** `TTS>=0.22.0` (Coqui) — ~1.5GB модель
**Интеграция с UI:** кнопка "Озвучить" в pipeline_view

### M16 — STT Transcriber
```python
class STTTranscriber(Processor):
    """Транскрибация аудио в текст."""
    module_id = "M16"

    def __init__(self, backend="whisper", device="cuda"):
        ...

    def process(self, audio_path: Path, config: dict) -> str:
        ...

    @staticmethod
    def wer(ref: str, hyp: str) -> float: ...
    @staticmethod
    def cer(ref: str, hyp: str) -> float: ...
```

**Зависимости:** `openai-whisper>=20231117`
**Замыкает цикл:** TTS → аудио → STT → текст → сравнение с исходным

### M17 — NER Extractor
```python
class NERExtractor(Processor):
    """Извлечение именованных сущностей."""
    module_id = "M17"

    def __init__(self, backend="heq_ner", device="cuda"):
        # backend: "heq_ner" (dicta-il, рекомендуется) | "alephbert" | "hebert"
        ...

    def process(self, text: str, config: dict) -> List[Entity]:
        ...

    @staticmethod
    def precision_recall_f1(expected, actual) -> dict: ...
```

**Зависимости:** `transformers>=4.35.0`
**Интеграция с M8:** NER результаты → Term Extractor (сущности как кандидаты терминов)
**Интеграция с Label Studio:** NER → annotation export

### M18 — Sentiment Analyzer
```python
class SentimentAnalyzer(Processor):
    """Анализ тональности ивритского текста."""
    module_id = "M18"

    def process(self, text: str, config: dict) -> dict:
        # → {"label": "positive|negative|neutral", "score": 0.87}
        ...
```

### M19 — Summarizer
```python
class Summarizer(Processor):
    """Суммаризация ивритских документов."""
    module_id = "M19"

    def process(self, text: str, config: dict) -> str:
        # config: {"max_length": 150, "min_length": 30}
        ...

    @staticmethod
    def rouge_l(ref: str, hyp: str) -> float: ...
```

### M20 — QA Extractor
```python
class QAExtractor(Processor):
    """Вопросно-ответная система (extractive)."""
    module_id = "M20"

    def process(self, qa_pair: dict, config: dict) -> dict:
        # input: {"question": "...", "context": "..."}
        # output: {"answer": "...", "score": 0.95, "start": 10, "end": 25}
        ...
```

### M21 — Morphological Generator
```python
class MorphGenerator(Processor):
    """Генерация всех словоформ из леммы + грамматических параметров."""
    module_id = "M21"

    def generate_noun_forms(self, lemma, gender="masculine") -> List[MorphForm]: ...
    def generate_verb_paradigm(self, root, binyan="paal", tense="present") -> List[MorphForm]: ...

    # Биньяны: paal, piel, pual, hifil, hufal, hitpael, nifal
    # Падежи: singular/plural, absolute/construct, definite/indefinite
```

**Зависимости:** Нет (только правила). **Интеграция с M3:** расширение морфологического анализа

### M22 — Transliterator
```python
class Transliterator(Processor):
    """Конвертация между ktiv male и ktiv haser."""
    module_id = "M22"

    def to_male(self, text: str) -> str: ...     # הַשָּׁנָה → השנה
    def to_haser(self, text: str) -> str: ...    # השנה → הַשָּׁנָה
    def to_phonetic(self, text: str) -> str: ... # IPA транскрипция
```

### M23 — Grammar Corrector
```python
class GrammarCorrector(Processor):
    """Грамматическая коррекция иврита."""
    module_id = "M23"
    # Требует fine-tuned модель или LLM
```

### M24 — Keyphrase Extractor
```python
class KeyphraseExtractor(Processor):
    """Извлечение ключевых фраз (дополняет M8)."""
    module_id = "M24"
    # YAKE! (language-independent) или KeyBERT
```

### M25 — Paraphraser
```python
class Paraphraser(Processor):
    """Переформулировка текста."""
    module_id = "M25"
    # Требует LLM или fine-tuned seq2seq
```

---

## Gold Corpus Schema — расширенный

### existing_file_counts (добавить)
```json
{
  "expected_diacritics_csv": {"type": "boolean", "default": false},
  "expected_translation_csv": {"type": "boolean", "default": false},
  "expected_tts_csv": {"type": "boolean", "default": false},
  "expected_stt_csv": {"type": "boolean", "default": false},
  "expected_ner_csv": {"type": "boolean", "default": false},
  "expected_sentiment_csv": {"type": "boolean", "default": false},
  "expected_summary_csv": {"type": "boolean", "default": false},
  "expected_qa_csv": {"type": "boolean", "default": false},
  "expected_morph_gen_csv": {"type": "boolean", "default": false},
  "expected_transliteration_csv": {"type": "boolean", "default": false}
}
```

### focus_areas (добавить)
```
diacritization, nikud_male, nikud_haser, matres_lectionis,
translation_he_en, translation_he_ru, translation_he_multi,
tts_synthesis, tts_voice_cloning, tts_prosody,
stt_transcription, stt_alignment,
ner_extraction, ner_coreference,
sentiment_analysis,
summarization, summarization_extractive, summarization_abstractive,
question_answering, qa_reading_comprehension,
morphological_generation, verb_paradigm, noun_declension_gen,
transliteration, grammar_correction, keyphrase_extraction, paraphrase
```

### quality_metrics (добавить)
```json
{
  "nikud_accuracy_target": 0.95,
  "bleu_target": 30.0,
  "tts_mos_target": 3.5,
  "tts_wer_target": 0.15,
  "stt_wer_target": 0.10,
  "ner_f1_target": 0.85,
  "sentiment_accuracy_target": 0.85,
  "summary_rouge_l_target": 0.40,
  "qa_f1_target": 0.80,
  "morph_gen_accuracy_target": 0.90
}
```

### Expected CSV Formats

| Модуль | Файл | Обязательные колонки |
|--------|------|---------------------|
| M13 | expected_diacritics.csv | `surface, expected_nikud, expectation_type, tolerance` |
| M14 | expected_translation_*.csv | `surface, src_lang, tgt_lang, expected_translation, expectation_type` |
| M15 | expected_tts.csv | `surface, lang, expected_duration_sec, format, expectation_type` |
| M16 | expected_stt.csv | `audio_file, expected_text, lang, expectation_type` |
| M17 | expected_ner.csv | `surface, entity_text, entity_type, expectation_type` |
| M18 | expected_sentiment.csv | `surface, expected_sentiment, expectation_type` |
| M19 | expected_summary.csv | `surface, expected_summary, expectation_type` |
| M20 | expected_qa.csv | `context, question, answer, expectation_type` |
| M21 | expected_morph_gen.csv | `lemma, pos, surface, features, expectation_type` |

---

## Конвенции кода

### Typing
- **Обязательны** аннотации типов для всех публичных функций и методов
- `List[Dict[str, Any]]`, не `List[Dict]`
- Engine Layer: `@dataclass`. API Layer: `pydantic.BaseModel`
- Config: `pydantic.BaseModel` с `extra="forbid"`

### Docstrings
- Google style, обязательны для публичных классов и методов

### Error Handling
- **Processor не падает** — возвращает `ProcessorResult(status=FAILED, errors=[...])`
- ML-зависимости обёрнуты в `try/except ImportError` с понятным сообщением
- Устройство: всегда проверять `torch.cuda.is_available()` перед `.to("cuda")`

### Logging
- `logger = logging.getLogger(__name__)` в каждом модуле
- Не использовать `print()` вне CLI

---

## Конфигурация

| Файл | Назначение |
|------|-----------|
| `pyproject.toml` | Зависимости (ranges) + tool config |
| `requirements.txt` | Pinned deps для Docker |
| `requirements-dev.txt` | Dev deps |
| `config/config.default.yaml` | Дефолтная конфигурация pipeline |
| `config/config.schema.json` | JSON Schema |

```bash
pip install -e ".[dev]"
kadima migrate
```

---

## Миграции БД

```bash
kadima migrate                     # Применить pending
kadima migrate --new add_foo       # Создать XXX_name.sql
```

Новые модули (M13–M25) могут потребовать миграции для хранения результатов:
- `results_nikud` — огласованные тексты
- `results_translation` — переводы
- `results_tts` — аудиофайлы (пути)
- `results_ner` — извлечённые сущности
- `results_sentiment` — тональность
- `results_summary` — суммаризации
- `results_qa` — QA пары

---

## Docker

```bash
make build && make up              # API (8501) + Label Studio (8080)
make up-llm                        # + llama.cpp (8081, GPU)
```

Новые модули (M13–M21) требуют GPU. Docker-compose должен монтировать GPU:
```yaml
deploy:
  resources:
    reservations:
      devices:
        - capabilities: [gpu]
```

---

## Зависимости

| Пакет | Range | Для чего |
|-------|-------|----------|
| PyYAML | `>=6.0,<7` | Config |
| pydantic | `>=2.6,<3` | Validation, API |
| spacy | `>=3.7,<4` | NLP pipeline |
| httpx | `>=0.27,<1` | HTTP client |
| fastapi | `>=0.110,<1` | REST API |
| transformers | `>=4.35,<5` | **M14, M17, M18, M19, M20** |
| torch | `>=2.0,<3` | **M13–M20** (ML inference) |
| sentencepiece | `>=0.1.99` | **M14** (translation) |
| phonikud-onnx | `>=1.0.0` | **M13** (diacritization) |
| onnxruntime | `>=1.15.0` | **M13** |
| openai-whisper | `>=20231117` | **M16** (STT) |
| TTS (coqui) | `>=0.22.0` | **M15** (XTTS v2) |

Optional: `PyQt6` (gui), `hebpipe` (hebpipe), `pytest`+`ruff`+`mypy` (dev)

---

## Тестирование

```bash
# All tests
pytest tests/ -v

# Engine tests only
pytest tests/engine/ -v

# Integration (pipeline E2E)
pytest tests/integration/ -v

# Specific module
pytest tests/engine/test_diacritizer.py -v
```

Для новых модулей — каждый получает свой `tests/engine/test_<module>.py` с:
- Unit-тестами метрик (без ML-модели)
- Integration-тестами (с заглушкой или small моделью)
- Gold corpus валидацией через `tests/data/`

---

## Что НЕ делать

- Не класть NLP-логику в `api/routers/` — только вызовы из `engine/`/`pipeline/`
- Не хардкодить пути — использовать `KADIMA_HOME` env
- Не создавать таблицы в коде — только миграции
- Не импортировать ML-модули без try/except ImportError
- Не использовать CUDA без проверки `torch.cuda.is_available()`
- Не мержить fixture с реальными данными

---

*Смотри также: `doc/Техническое задание разработка KADIMA/` — полная документация*
*Workspace prototype: `/home/lletp/.openclaw/workspace/hebrew-corpus-v2/` — прототип модулей M13–M21*

---

## Интеграционные точки для Claude Code

### Pipeline Orchestrator (M13–M25)

Новые модули должны регистрироваться в `kadima/pipeline/orchestrator.py`:

```python
# В _register_modules() добавить:
from kadima.engine.diacritizer import Diacritizer
from kadima.engine.translator import Translator
from kadima.engine.tts_synthesizer import TTSSynthesizer
from kadima.engine.stt_transcriber import STTTranscriber
from kadima.engine.ner_extractor import NERExtractor
from kadima.engine.sentiment_analyzer import SentimentAnalyzer
from kadima.engine.summarizer import Summarizer
from kadima.engine.qa_extractor import QAExtractor
from kadima.engine.morph_generator import MorphGenerator
from kadima.engine.transliterator import Transliterator
from kadima.engine.grammar_corrector import GrammarCorrector
from kadima.engine.keyphrase_extractor import KeyphraseExtractor
from kadima.engine.paraphraser import Paraphraser

self.modules = {
    ...existing...,
    "M13": Diacritizer(config.get("diacritizer", {})),
    "M14": Translator(config.get("translator", {})),
    "M15": TTSSynthesizer(config.get("tts", {})),
    "M16": STTTranscriber(config.get("stt", {})),
    "M17": NERExtractor(config.get("ner", {})),
    "M18": SentimentAnalyzer(config.get("sentiment", {})),
    "M19": Summarizer(config.get("summarizer", {})),
    "M20": QAExtractor(config.get("qa", {})),
    "M21": MorphGenerator(config.get("morph_gen", {})),
    "M22": Transliterator(config.get("transliterator", {})),
    "M23": GrammarCorrector(config.get("grammar", {})),
    "M24": KeyphraseExtractor(config.get("keyphrase", {})),
    "M25": Paraphraser(config.get("paraphrase", {})),
}
```

### Config (config/config.default.yaml)

Добавить секции для новых модулей:
```yaml
diacritizer:
  backend: phonikud
  device: cuda

translator:
  backend: mbart
  device: cuda
  tgt_lang: en

tts:
  backend: xtts
  device: cuda

stt:
  backend: whisper
  device: cuda

ner:
  backend: heq_ner
  device: cuda

sentiment:
  backend: hebert
  device: cuda

summarizer:
  backend: mt5
  device: cuda
  max_length: 150

qa:
  backend: alephbert
  device: cuda

morph_gen:
  gender: masculine
  binyan: paal

transliterator:
  mode: latin

grammar:
  backend: mt5
  device: cuda

keyphrase:
  backend: yake
  top_n: 10

paraphrase:
  backend: mt5
  device: cuda
  num_variants: 1
```

### API Endpoints (kadima/api/routers/)

Нужно создать `kadima/api/routers/generative.py`:

```python
# POST /generative/diacritize   {"text": "..."} → {"result": "..."}
# POST /generative/translate    {"text": "...", "tgt_lang": "en"} → {"result": "..."}
# POST /generative/tts          {"text": "..."} → {"audio_url": "..."}
# POST /generative/stt          {"audio_url": "..."} → {"text": "..."}
# POST /generative/ner          {"text": "..."} → {"entities": [...]}
# POST /generative/sentiment    {"text": "..."} → {"label": "...", "score": 0.87}
# POST /generative/summarize    {"text": "..."} → {"summary": "..."}
# POST /generative/qa           {"question": "...", "context": "..."} → {"answer": "..."}
# POST /generative/morph-gen    {"lemma": "...", "pos": "NOUN"} → {"forms": [...]}
# POST /generative/transliterate {"text": "...", "mode": "latin"} → {"result": "..."}
# POST /generative/grammar      {"text": "..."} → {"corrected": "..."}
# POST /generative/keyphrase    {"text": "..."} → {"keyphrases": [...]}
# POST /generative/paraphrase   {"text": "..."} → {"paraphrases": [...]}
```

### UI Views (kadima/ui/)

Нужно создать `kadima/ui/generative_view.py`:
- Таб "Генеративные модули" с 13 кнопками (по одной на модуль)
- Входное поле для текста
- Выходное поле для результата
- Настройки (backend, device, язык)

### Validation (kadima/validation/)

`check_engine.py` должен проверять новые модули через gold corpus:
```python
# Добавить проверку expected_diacritics.csv, expected_translation_*.csv и т.д.
# Использовать NikudMetrics, TranslationMetrics и т.д. из workspace prototype
```

### Рабочий прототип

Прототипы всех модулей лежат в workspace:
```
/home/lletp/.openclaw/workspace/hebrew-corpus-v2/tools/
```

Эти файлы содержат:
- Готовые метрики (static methods)
- CLI-интерфейсы
- Логику загрузки моделей
- Форматы expected CSV

**Класть в настоящий проект нужно ПО КОМПОНЕНТНО:**
1. Метрики → `kadima/engine/<module>_metrics.py`
2. Процессор → `kadima/engine/<module>.py` (с наследованием от Processor)
3. CLI → расширить `kadima/cli.py`
4. API → `kadima/api/routers/generative.py`
5. UI → `kadima/ui/generative_view.py`

