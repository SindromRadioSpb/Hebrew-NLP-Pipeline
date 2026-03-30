# 10.2. Interface Contracts — KADIMA

> Версия: 1.0 (2026-03-30)
> Связанные: PROJECT_STRUCTURE.md (kadima/engine/base.py), DATA_MODEL.md, ARCHITECTURE.md

---

## Базовый интерфейс: Processor ABC

Все модули Engine Layer наследуют `Processor`. Это контракт, по которому PipelineService оркестрирует модули.

```python
# kadima/engine/base.py

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum


class ProcessorStatus(str, Enum):
    READY = "ready"
    RUNNING = "running"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ProcessorResult:
    """Результат работы одного Processor."""
    module_name: str                    # "M1", "M2", ...
    status: ProcessorStatus
    data: Any                           # Результат (тип зависит от модуля)
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    processing_time_ms: float = 0.0


@dataclass
class PipelineResult:
    """Результат полного pipeline run."""
    corpus_id: int
    profile: str                        # "precise" / "balanced" / "recall"
    module_results: Dict[str, ProcessorResult] = field(default_factory=dict)
    terms: List["Term"] = field(default_factory=list)
    ngrams: List["Ngram"] = field(default_factory=list)
    np_chunks: List["NPChunk"] = field(default_factory=list)
    total_time_ms: float = 0.0
    status: ProcessorStatus = ProcessorStatus.READY


class Processor(ABC):
    """
    Базовый интерфейс для всех модулей Engine Layer.
    Каждый модуль M1–M12 реализует этот интерфейс.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Имя модуля: 'sent_split', 'tokenizer', 'morph_analyzer', и т.д."""
        ...

    @property
    @abstractmethod
    def module_id(self) -> str:
        """Номер модуля: 'M1', 'M2', 'M3', ..."""
        ...

    @abstractmethod
    def process(self, input_data: Any, config: Dict[str, Any]) -> ProcessorResult:
        """
        Основной метод обработки.

        Args:
            input_data: Входные данные (тип зависит от модуля)
            config: Конфигурация модуля из PipelineConfig

        Returns:
            ProcessorResult с data соответствующего типа
        """
        ...

    def validate_input(self, input_data: Any) -> bool:
        """Опциональная валидация входных данных."""
        return True

    def get_status(self) -> ProcessorStatus:
        """Текущий статус модуля."""
        return ProcessorStatus.READY
```

---

## Сигнатуры модулей: вход → выход

### M1: Sentence Splitter

```python
# kadima/engine/hebpipe_wrappers.py

from dataclasses import dataclass
from typing import List

@dataclass
class Sentence:
    index: int
    text: str
    start: int        # char offset в исходном тексте
    end: int

@dataclass
class SentenceSplitResult:
    sentences: List[Sentence]
    count: int

# Вход: str (raw text)
# Выход: SentenceSplitResult
# Processor.process(text: str) → ProcessorResult(data=SentenceSplitResult)
```

### M2: Tokenizer

```python
@dataclass
class Token:
    index: int
    surface: str        # "הפלדה"
    start: int
    end: int
    is_punct: bool = False

@dataclass
class TokenizeResult:
    tokens: List[Token]
    count: int

# Вход: str (предложение)
# Выход: TokenizeResult
```

### M3: Morphological Analyzer

```python
@dataclass
class MorphAnalysis:
    surface: str        # "הפלדה"
    base: str           # "פלדה" (без префиксов)
    lemma: str          # "פלדה"
    pos: str            # "NOUN" / "VERB" / "ADJ" / ...
    features: Dict[str, str]  # {"gender": "fem", "number": "sg", "definiteness": "def"}
    is_det: bool
    prefix_chain: List[str]   # ["ה"] или ["ב", "ה"]

@dataclass
class MorphResult:
    analyses: List[MorphAnalysis]  # один на каждый токен
    count: int

# Вход: List[Token] (из M2)
# Выход: MorphResult
```

### M4: N-gram Extractor

```python
@dataclass
class Ngram:
    tokens: List[str]   # ["חוזק", "מתיחה"]
    n: int              # 2
    freq: int           # 8
    doc_freq: int       # 4 (в скольких документах встречается)

@dataclass
class NgramResult:
    ngrams: List[Ngram]
    total_candidates: int
    filtered: int       # после min_freq

# Вход: List[List[Token]] (список предложений, каждое = список токенов)
# Выход: NgramResult
# Конфиг: min_n=2, max_n=5, min_freq=2
```

### M5: NP Chunk Extractor

```python
@dataclass
class NPChunk:
    surface: str        # "חוזק מתיחה"
    tokens: List[str]
    pattern: str        # "NOUN_NOUN" / "NOUN_ADJ" / "DET_NOUN_ADJ"
    start: int
    end: int
    sentence_idx: int

@dataclass
class NPChunkResult:
    chunks: List[NPChunk]
    total: int

# Вход: List[List[MorphAnalysis]] (морфологически разобранные предложения)
# Выход: NPChunkResult
```

### M6: Canonicalizer

```python
@dataclass
class CanonicalMapping:
    surface: str        # "הפלדה"
    canonical: str      # "פלדה"
    rules_applied: List[str]  # ["det_removal"]

@dataclass
class CanonicalResult:
    mappings: List[CanonicalMapping]

# Вход: List[str] (surface forms)
# Выход: CanonicalResult
```

### M7: Association Measures

```python
@dataclass
class AssociationScore:
    pair: tuple[str, str]   # ("חוזק", "מתיחה")
    pmi: float
    llr: float
    dice: float

@dataclass
class AMResult:
    scores: List[AssociationScore]

# Вход: List[Ngram] (из M4) + corpus statistics
# Выход: AMResult
```

### M8: Term Extractor

```python
@dataclass
class Term:
    surface: str
    canonical: str
    kind: str           # "NOUN_NOUN" / "NOUN_ADJ" / ...
    freq: int
    doc_freq: int
    pmi: float
    llr: float
    dice: float
    rank: int
    profile: str        # "precise" / "balanced" / "recall"

@dataclass
class TermResult:
    terms: List[Term]
    profile: str
    total_candidates: int
    filtered: int

# Вход: NgramResult + AMResult + NPChunkResult + profile config
# Выход: TermResult
# Профили:
#   precise:   min_freq=3, hapax=False, pmi_high
#   balanced:  min_freq=2, hapax=False, pmi_medium
#   recall:    min_freq=1, hapax=True,  pmi_low
```

### M11: Validation Framework

```python
@dataclass
class CheckResult:
    check_type: str     # "sentence_count" / "token_count" / "lemma_freq" / "term_present"
    file_id: str
    item: str
    expected: str
    actual: str
    result: str         # "PASS" / "WARN" / "FAIL"
    expectation_type: str  # "exact" / "approx" / "present_only" / "absent"
    discrepancy_type: Optional[str]  # "bug" / "stale_gold" / ...

@dataclass
class ValidationReport:
    corpus_id: int
    status: str         # "PASS" / "WARN" / "FAIL"
    checks: List[CheckResult]
    summary: Dict[str, int]  # {"pass": 45, "warn": 2, "fail": 0}

# Вход: GoldCorpus + PipelineResult
# Выход: ValidationReport
```

### M12: Noise Classifier

```python
@dataclass
class NoiseLabel:
    surface: str
    noise_type: str     # "punct" / "number" / "latin" / "chemical" / "quantity" / "math" / "non_noise"

@dataclass
class NoiseResult:
    labels: List[NoiseLabel]

# Вход: List[Token]
# Выход: NoiseResult
```

---

## Pipeline Orchestrator Interface

```python
# kadima/pipeline/orchestrator.py

from kadima.engine.base import Processor, PipelineResult
from kadima.pipeline.config import PipelineConfig

class PipelineService:
    """Оркестрирует выполнение M1→M2→...→M8."""

    def __init__(self, config: PipelineConfig):
        self.config = config
        self.modules: Dict[str, Processor] = {}
        self._register_modules()

    def _register_modules(self):
        """Регистрирует модули в порядке выполнения."""
        # M1 SentSplit → M2 Tokenizer → M3 MorphAnalyzer → M4 NgramExtractor →
        # M5 NPChunker → M6 Canonicalizer → M7 AMEngine → M8 TermExtractor
        ...

    def run(self, corpus_id: int) -> PipelineResult:
        """
        Запускает pipeline на корпусе.

        Args:
            corpus_id: ID корпуса в БД

        Returns:
            PipelineResult с terms, ngrams, np_chunks
        """
        ...

    def run_on_text(self, text: str) -> PipelineResult:
        """Запускает pipeline на одном тексте (без БД)."""
        ...
```

---

## Label Studio Client Interface

```python
# kadima/annotation/ls_client.py

class LabelStudioClient:
    """REST API клиент для Label Studio."""

    def __init__(self, url: str = "http://localhost:8080", api_key: Optional[str] = None):
        ...

    def create_project(self, name: str, label_config: str) -> int:
        """Создать проект. Возвращает project ID."""
        ...

    def import_tasks(self, project_id: int, tasks: List[Dict]) -> List[int]:
        """Импортировать задачи. Возвращает task IDs."""
        ...

    def import_predictions(self, project_id: int, predictions: List[Dict]) -> None:
        """Импортировать pre-annotations."""
        ...

    def export_annotations(self, project_id: int, export_type: str = "JSON") -> List[Dict]:
        """Экспортировать аннотации."""
        ...

    def get_project_stats(self, project_id: int) -> Dict:
        """Статистика: total, completed, skipped."""
        ...
```

---

## LLM Client Interface (v1.x)

```python
# kadima/llm/client.py

class LlamaCppClient:
    """HTTP клиент для llama.cpp server."""

    def __init__(self, server_url: str = "http://localhost:8081", timeout: int = 30):
        ...

    def is_loaded(self) -> bool:
        """Проверить, загружена ли модель."""
        ...

    def generate(self, prompt: str, max_tokens: int = 512, temperature: float = 0.7) -> str:
        """Генерация текста."""
        ...

    def chat(self, messages: List[Dict[str, str]], max_tokens: int = 512) -> str:
        """Chat completion (messages: [{"role": "user", "content": "..."}])."""
        ...
```

---

## Data Repository Interface

```python
# kadima/data/repositories.py

class CorpusRepository:
    def create(self, name: str, language: str = "he") -> int: ...
    def get(self, corpus_id: int) -> Optional[Corpus]: ...
    def list_all(self) -> List[Corpus]: ...
    def delete(self, corpus_id: int) -> None: ...

class PipelineRunRepository:
    def create(self, corpus_id: int, profile: str) -> int: ...
    def update_status(self, run_id: int, status: str) -> None: ...
    def save_terms(self, run_id: int, terms: List[Term]) -> None: ...
    def get_results(self, run_id: int) -> PipelineResult: ...

class KBRepository:  # v1.x
    def create_term(self, term: KBTerm) -> int: ...
    def search(self, query: str, limit: int = 20) -> List[KBTerm]: ...
    def get_related(self, term_id: int, top_n: int = 10) -> List[KBRelation]: ...
    def update_definition(self, term_id: int, definition: str, source: str) -> None: ...
```

---

## Типы данных: вход/выход каждого модуля (сводка)

| Модуль | Класс | Вход (process data=) | Выход (result.data=) |
|--------|-------|---------------------|---------------------|
| M1 | `HebPipeSentSplitter` | `str` | `SentenceSplitResult` |
| M2 | `HebPipeTokenizer` | `str` | `TokenizeResult` |
| M3 | `HebPipeMorphAnalyzer` | `List[Token]` | `MorphResult` |
| M4 | `NgramExtractor` | `List[List[Token]]` | `NgramResult` |
| M5 | `NPChunker` | `List[List[MorphAnalysis]]` | `NPChunkResult` |
| M6 | `Canonicalizer` | `List[str]` | `CanonicalResult` |
| M7 | `AMEngine` | `List[Ngram] + stats` | `AMResult` |
| M8 | `TermExtractor` | `NgramResult + AMResult + NPChunkResult` | `TermResult` |
| M11 | `ValidationFramework` | `GoldCorpus + PipelineResult` | `ValidationReport` |
| M12 | `NoiseClassifier` | `List[Token]` | `NoiseResult` |
| M14 | `CorpusManager` | corpus_id | Corpus statistics |
| M15 | `AnnotationManager` | project config | LS project ID |
| M18 | `LLMService` (v1.x) | prompt | `str` (generated text) |
| M19 | `KBService` (v1.x) | term/query | `KBTerm / List[KBTerm]` |
