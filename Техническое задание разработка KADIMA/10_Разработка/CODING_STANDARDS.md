# 10.3. Coding Standards — KADIMA

> Версия: 1.0 (2026-03-30)
> Связанные: PROJECT_STRUCTURE.md, INTERFACE_CONTRACTS.md

---

## Python Version

**3.12+** (используем новые features: type statement, f-strings improvements)

---

## Typing

**Обязательно** для всех публичных функций, методов и классов.

```python
# ✅ Правильно
def extract_terms(ngrams: List[Ngram], config: TermConfig) -> TermResult:
    ...

# ❌ Неправильно
def extract_terms(ngrams, config):
    ...
```

### Dataclass vs Pydantic
- **Engine Layer** (Processor, результаты): `@dataclass` (быстро, без валидации)
- **API Layer** (request/response): `pydantic.BaseModel` (валидация, сериализация)
- **Config**: `@dataclass` + YAML loader

```python
# Engine: dataclass
@dataclass
class Term:
    surface: str
    freq: int

# API: pydantic
class TermResponse(BaseModel):
    surface: str
    freq: int
    pmi: float

# Config: dataclass
@dataclass
class PipelineConfig:
    profile: str = "balanced"
    min_freq: int = 2
```

---

## Docstrings

Google style, обязательны для публичных классов и методов.

```python
class TermExtractor(Processor):
    """M8: Извлечение терминов с ранжированием по association measures.

    Принимает n-grams, association scores и NP chunks.
    Фильтрует по профилю (precise/balanced/recall) и ранжирует.
    """

    def process(self, input_data: TermExtractorInput, config: Dict[str, Any]) -> ProcessorResult:
        """Извлечь и ранжировать термины.

        Args:
            input_data: NgramResult + AMResult + NPChunkResult
            config: {"profile": "balanced", "min_freq": 2, ...}

        Returns:
            ProcessorResult с data=TermResult
        """
        ...
```

---

## Error Handling

### Принципы
1. **Не глотаем ошибки** — всегда логируем
2. **Processor не падает** — возвращает `ProcessorResult(status=FAILED, errors=[...])`
3. **Pipeline продолжает** — если модуль M4 упал, M5–M8 пропускаются, но pipeline не crash
4. **Пользователю — понятное сообщение**, в лог — traceback

### Исключения

```python
# Кастомные исключения
class KadimaError(Exception):
    """Базовое исключение KADIMA."""
    pass

class PipelineError(KadimaError):
    """Ошибка в pipeline."""
    pass

class ConfigError(KadimaError):
    """Ошибка конфигурации."""
    pass

class GoldCorpusError(KadimaError):
    """Ошибка импорта/валидации gold corpus."""
    pass

class AnnotationError(KadimaError):
    """Ошибка Label Studio интеграции."""
    pass

class LLMError(KadimaError):  # v1.x
    """Ошибка LLM inference."""
    pass
```

### Pattern: Processor error handling

```python
def process(self, input_data: Any, config: Dict[str, Any]) -> ProcessorResult:
    start = time.time()
    try:
        if not self.validate_input(input_data):
            return ProcessorResult(
                module_name=self.name,
                status=ProcessorStatus.FAILED,
                data=None,
                errors=[f"Invalid input for {self.name}"]
            )
        result_data = self._do_work(input_data, config)
        return ProcessorResult(
            module_name=self.name,
            status=ProcessorStatus.READY,
            data=result_data,
            processing_time_ms=(time.time() - start) * 1000
        )
    except Exception as e:
        logger.error(f"{self.name} failed: {e}", exc_info=True)
        return ProcessorResult(
            module_name=self.name,
            status=ProcessorStatus.FAILED,
            data=None,
            errors=[str(e)],
            processing_time_ms=(time.time() - start) * 1000
        )
```

---

## Logging

### Setup
```python
# kadima/utils/logging.py
import logging
import sys

def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(os.path.expanduser("~/.kadima/logs/kadima.log")),
        ]
    )
```

### Usage
```python
import logging
logger = logging.getLogger(__name__)

# INFO: нормальные операции
logger.info("Pipeline started: corpus=%s, profile=%s", corpus_id, profile)

# WARNING: не критичные проблемы
logger.warning("Hapax term filtered: %s", term.surface)

# ERROR: ошибки с traceback
logger.error("Pipeline failed on file %s", filename, exc_info=True)

# DEBUG: детали (только при KADIMA_LOG_LEVEL=DEBUG)
logger.debug("Tokenizer output: %s", tokens)
```

---

## Форматирование

- **Black** (line length 100)
- **isort** (profile: black)
- **Ruff** для linting

```toml
# pyproject.toml
[tool.black]
line-length = 100

[tool.ruff]
line-length = 100
select = ["E", "F", "I", "W", "UP"]

[tool.isort]
profile = "black"
```

---

## File Headers

```python
# kadima/engine/term_extractor.py
"""M8: Term Extractor — извлечение и ранжирование терминов.

Принимает n-grams (M4), association measures (M7) и NP chunks (M5).
Фильтрует по профилю (precise/balanced/recall), применяет AM scores
для ранжирования, возвращает ranked TermResult.
"""
```

---

## Тестовые конвенции

### Именование
```python
# test_<module>.py
# test_<function>_<scenario>

def test_extract_terms_balanced_profile():
    ...

def test_extract_terms_empty_corpus():
    ...

def test_extract_terms_min_freq_filter():
    ...
```

### Fixtures
```python
# tests/conftest.py

@pytest.fixture
def sample_corpus_text():
    """Один документ на иврите для smoke test."""
    return "פלדה חזקה משמשת בבניין. חוזק מתיחה גבוה."

@pytest.fixture
def gold_corpus_he_01():
    """Gold corpus he_01 для acceptance test."""
    return load_gold_corpus("tests/data/he_01_sentence_token_lemma_basics")

@pytest.fixture
def pipeline_config():
    """Дефолтная конфигурация pipeline."""
    return PipelineConfig(profile="balanced", min_freq=2)
```

### Моки для внешних сервисов
```python
@pytest.fixture
def mock_llm_client(monkeypatch):
    """Мок llama.cpp сервера для тестов без GPU."""
    def mock_generate(*args, **kwargs):
        return "זהו מבחן."
    monkeypatch.setattr("kadima.llm.client.LlamaCppClient.generate", mock_generate)

@pytest.fixture
def mock_ls_client(monkeypatch):
    """Мок Label Studio для тестов без Docker."""
    ...
```

---

## Git Conventions

### Commits
```
<type>: <description>

Types: feat, fix, docs, refactor, test, chore, perf

Examples:
feat: add M4 ngram extractor
fix: handle empty corpus in M8
docs: update DATA_MODEL with KB tables
test: add he_01 acceptance test
```

### Branches
```
main              — стабильный
develop           — интеграция
feat/M4-ngram     — feature
fix/empty-corpus  — bugfix
```
