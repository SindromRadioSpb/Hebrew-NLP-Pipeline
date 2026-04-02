"""M8 Term Extractor backends — abstract interface + statistical + AlephBERT ML.

Architecture:
    M8Backend (ABC)
    ├── StatisticalBackend  — текущий Ngram+AM+NP pipeline
    └── AlephBERTBackend    — fine-tuned Token Classification

Usage:
    >>> from kadima.engine.term_extractor_backends import get_backend
    >>> backend = get_backend("statistical")
    >>> result = backend.extract(text, config)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional
import logging
import time

logger = logging.getLogger(__name__)


@dataclass
class ExtractedTerm:
    """Единый формат термина для всех бэкендов."""

    surface: str
    canonical: str
    kind: str = "UNKNOWN"
    freq: int = 1
    doc_freq: int = 1
    pmi: float = 0.0
    llr: float = 0.0
    dice: float = 0.0
    t_score: float = 0.0
    chi_square: float = 0.0
    phi: float = 0.0
    rank: int = 0
    profile: str = "balanced"
    cluster_id: int = -1
    variant_count: int = 1
    variants: list[str] = field(default_factory=list)
    # ML-specific
    confidence: float = 0.0
    start_offset: int = 0
    end_offset: int = 0


@dataclass
class ExtractionResult:
    """Результат извлечения терминов."""

    terms: list[ExtractedTerm] = field(default_factory=list)
    total_candidates: int = 0
    filtered: int = 0
    term_mode: str = "canonical"
    total_clusters: int = 0
    backend: str = "statistical"
    processing_time_ms: float = 0.0
    model_version: str = ""


class M8Backend(ABC):
    """Abstract base для всех M8 бэкендов."""

    @property
    @abstractmethod
    def backend_name(self) -> str:
        """Уникальное имя бэкенда (statistical, alephbert, ...)."""
        ...

    @abstractmethod
    def extract(self, text: str, config: dict[str, Any]) -> ExtractionResult:
        """Извлечь термины из текста.

        Args:
            text: Raw Hebrew text.
            config: Pipeline config (min_freq, term_mode, pos_filter_enabled, ...).

        Returns:
            ExtractionResult с извлечёнными терминами.
        """
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Проверить доступность бэкенда (модель загружена, зависимости установлены)."""
        ...

    def get_info(self) -> dict[str, Any]:
        """Метаинформация о бэкенде."""
        return {
            "name": self.backend_name,
            "available": self.is_available(),
        }


class StatisticalBackend(M8Backend):
    """Statistical backend — обёртка над текущим TermExtractor.

    Использует NgramExtractor + AssociationMeasures + NPChunker + Canonicalizer.
    """

    @property
    def backend_name(self) -> str:
        return "statistical"

    def is_available(self) -> bool:
        return True  # всегда доступен, zero ML dependencies

    def extract(self, text: str, config: dict[str, Any]) -> ExtractionResult:
        """Извлечь термины через статистический pipeline.

        Этот метод вызывается из orchestrator — он уже передаёт
        ngrams, am_scores, np_chunks, canonical_mappings.
        Для standalone использования нужен полный pipeline.
        """
        start = time.time()
        # Statistical backend требует pre-computed данные из pipeline.
        # orchestrator вызывает TermExtractor.process() напрямую.
        # Этот метод — заглушка для совместимости с backend interface.
        logger.debug("StatisticalBackend.extract() called — use TermExtractor.process() instead")
        return ExtractionResult(
            backend=self.backend_name,
            processing_time_ms=(time.time() - start) * 1000,
            model_version="rule-based",
        )

    def get_info(self) -> dict[str, Any]:
        return {
            "name": self.backend_name,
            "available": True,
            "description": "Ngram + AM + NP + Canonical rule-based extraction",
            "model_version": "rule-based",
        }


class AlephBERTBackend(M8Backend):
    """AlephBERT Token Classification backend для term extraction.

    Fine-tuned alephbert-base для распознавания терминов в Hebrew text.
    Output: BIO tagging (B-TERM, I-TERM, O).
    """

    MODEL_NAME = "onlplab/alephbert-base"
    DEFAULT_MAX_LENGTH = 512

    def __init__(self, model_path: Optional[str] = None, device: str = "cpu"):
        self._model_path = model_path
        self._device = device
        self._model = None
        self._tokenizer = None
        self._label2id: dict[str, int] = {}
        self._id2label: dict[int, str] = {}
        self._model_version = ""

    @property
    def backend_name(self) -> str:
        return "alephbert"

    def is_available(self) -> bool:
        """Проверить доступность AlephBERT."""
        try:
            from transformers import AutoModelForTokenClassification, AutoTokenizer
            return True
        except ImportError:
            return False

    def load(self) -> bool:
        """Загрузить модель и токенизатор.

        Returns:
            True если загрузка успешна.
        """
        if self._model is not None:
            return True

        try:
            from transformers import AutoModelForTokenClassification, AutoTokenizer
            import torch

            model_path = self._model_path or self.MODEL_NAME

            logger.info("Loading AlephBERT term extractor from %s", model_path)
            self._tokenizer = AutoTokenizer.from_pretrained(model_path)
            self._model = AutoModelForTokenClassification.from_pretrained(model_path)

            # Get label mappings
            self._label2id = self._model.config.label2id
            self._id2label = self._model.config.id2label
            self._model_version = model_path.split("/")[-1]

            # Move to device
            if self._device == "cuda" and torch.cuda.is_available():
                self._model = self._model.to("cuda")
                logger.info("AlephBERT term extractor loaded on GPU")
            else:
                logger.info("AlephBERT term extractor loaded on CPU")

            return True

        except Exception as e:
            logger.error("Failed to load AlephBERT term extractor: %s", e)
            return False

    def extract(self, text: str, config: dict[str, Any]) -> ExtractionResult:
        """Извлечь термины через AlephBERT Token Classification.

        Args:
            text: Raw Hebrew text.
            config: min_freq, term_mode, confidence_threshold, ...

        Returns:
            ExtractionResult с извлечёнными терминами.
        """
        start = time.time()

        if not self.load():
            logger.warning("AlephBERT backend unavailable, returning empty result")
            return ExtractionResult(
                backend=self.backend_name,
                processing_time_ms=(time.time() - start) * 1000,
            )

        confidence_threshold = config.get("confidence_threshold", 0.5)
        min_freq = config.get("min_freq", 1)

        # Tokenize
        inputs = self._tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=self.DEFAULT_MAX_LENGTH,
            padding=True,
        )

        # Inference
        import torch
        with torch.no_grad():
            if self._device == "cuda":
                inputs = {k: v.to("cuda") for k, v in inputs.items()}
            outputs = self._model(**inputs)
            logits = outputs.logits

        # Decode predictions
        predictions = torch.argmax(logits, dim=2)
        tokens = self._tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])

        # BIO → terms
        terms = self._bio_to_terms(
            tokens, predictions[0].cpu().numpy(), text, confidence_threshold
        )

        # Apply min_freq filter
        freq_map: dict[str, ExtractedTerm] = {}
        for term in terms:
            if term.surface in freq_map:
                freq_map[term.surface].freq += 1
            else:
                freq_map[term.surface] = term

        filtered = [t for t in freq_map.values() if t.freq >= min_freq]

        # Rank by freq + confidence
        filtered.sort(key=lambda t: t.freq + t.confidence, reverse=True)
        for rank, term in enumerate(filtered, 1):
            term.rank = rank

        return ExtractionResult(
            terms=filtered,
            total_candidates=len(terms),
            filtered=len(filtered),
            backend=self.backend_name,
            processing_time_ms=(time.time() - start) * 1000,
            model_version=self._model_version,
        )

    def _bio_to_terms(
        self,
        tokens: list[str],
        predictions: Any,
        original_text: str,
        confidence_threshold: float,
    ) -> list[ExtractedTerm]:
        """Конвертировать BIO predictions в термины."""
        terms = []
        current_term_tokens = []
        current_start = 0

        for i, (token, pred_id) in enumerate(zip(tokens, predictions)):
            label = self._id2label.get(int(pred_id), "O")

            if label.startswith("B-TERM"):
                # Save previous term
                if current_term_tokens:
                    surface = self._tokenizer.convert_tokens_to_string(current_term_tokens).strip()
                    if surface:
                        terms.append(ExtractedTerm(
                            surface=surface,
                            canonical=surface,
                            kind="ML_TERM",
                            freq=1,
                            confidence=0.8,  # placeholder
                            start_offset=current_start,
                        ))
                # Start new term
                current_term_tokens = [token]
                current_start = i
            elif label.startswith("I-TERM") and current_term_tokens:
                current_term_tokens.append(token)
            else:
                # O tag — save current term if any
                if current_term_tokens:
                    surface = self._tokenizer.convert_tokens_to_string(current_term_tokens).strip()
                    if surface:
                        terms.append(ExtractedTerm(
                            surface=surface,
                            canonical=surface,
                            kind="ML_TERM",
                            freq=1,
                            confidence=0.8,
                            start_offset=current_start,
                        ))
                current_term_tokens = []

        # Don't forget last term
        if current_term_tokens:
            surface = self._tokenizer.convert_tokens_to_string(current_term_tokens).strip()
            if surface:
                terms.append(ExtractedTerm(
                    surface=surface,
                    canonical=surface,
                    kind="ML_TERM",
                    freq=1,
                    confidence=0.8,
                    start_offset=current_start,
                ))

        return terms

    def get_info(self) -> dict[str, Any]:
        return {
            "name": self.backend_name,
            "available": self.is_available(),
            "model_path": self._model_path or self.MODEL_NAME,
            "device": self._device,
            "model_version": self._model_version or "not loaded",
        }


# ── Registry ────────────────────────────────────────────────────────────────

_BACKENDS: dict[str, M8Backend] = {}


def register_backend(backend: M8Backend) -> None:
    """Зарегистрировать бэкенд."""
    _BACKENDS[backend.backend_name] = backend


def get_backend(name: str = "statistical") -> M8Backend:
    """Получить бэкенд по имени.

    Args:
        name: statistical | alephbert

    Returns:
        M8Backend instance.

    Raises:
        ValueError: если бэкенд не найден.
    """
    if name not in _BACKENDS:
        # Auto-register on first access
        _register_defaults()

    if name not in _BACKENDS:
        raise ValueError(f"Unknown term extractor backend: {name}. Available: {list(_BACKENDS.keys())}")

    return _BACKENDS[name]


def _register_defaults() -> None:
    """Зарегистрировать стандартные бэкенды."""
    if "statistical" not in _BACKENDS:
        _BACKENDS["statistical"] = StatisticalBackend()
    if "alephbert" not in _BACKENDS:
        _BACKENDS["alephbert"] = AlephBERTBackend()


def list_backends() -> list[dict[str, Any]]:
    """Список всех зарегистрированных бэкендов."""
    _register_defaults()
    return [b.get_info() for b in _BACKENDS.values()]