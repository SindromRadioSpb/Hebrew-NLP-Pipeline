# kadima/engine/hebpipe_wrappers.py
"""M1–M3: Обёртки над HebPipe для интеграции в pipeline.

Data flow:
  M1 HebPipeSentSplitter:  str → SentenceSplitResult
  M2 HebPipeTokenizer:     str → TokenizeResult
  M3 HebPipeMorphAnalyzer: List[Token] → MorphResult
"""

import time
import logging
import re
from typing import Any, Dict, List
from dataclasses import dataclass, field

from kadima.engine.base import Processor, ProcessorResult, ProcessorStatus

logger = logging.getLogger(__name__)


# ── Data types ───────────────────────────────────────────────────────────────


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


@dataclass
class Token:
    index: int
    surface: str      # "הפלדה"
    start: int
    end: int
    is_punct: bool = False


@dataclass
class TokenizeResult:
    tokens: List[Token]
    count: int


@dataclass
class MorphAnalysis:
    surface: str
    base: str           # "פלדה" (без префиксов)
    lemma: str
    pos: str            # "NOUN" / "VERB" / "ADJ" / ...
    features: Dict[str, str] = field(default_factory=dict)
    is_det: bool = False
    prefix_chain: List[str] = field(default_factory=list)


@dataclass
class MorphResult:
    analyses: List[MorphAnalysis]
    count: int


# ── M1: Sentence Splitter ────────────────────────────────────────────────────


class HebPipeSentSplitter(Processor):
    """M1: Разбиение текста на предложения."""

    @property
    def name(self) -> str:
        return "sent_split"

    @property
    def module_id(self) -> str:
        return "M1"

    def validate_input(self, input_data: Any) -> bool:
        return isinstance(input_data, str) and len(input_data.strip()) > 0

    def process(self, input_data: str, config: Dict[str, Any]) -> ProcessorResult:
        start = time.time()
        if not self.validate_input(input_data):
            return ProcessorResult(
                module_name=self.name, status=ProcessorStatus.FAILED,
                data=None, errors=["Expected non-empty str"],
                processing_time_ms=(time.time() - start) * 1000,
            )
        try:
            parts = re.split(r'(?<=[\u0590-\u05FF])\.\s+', input_data)
            sentences = []
            offset = 0
            for i, part in enumerate(parts):
                part = part.strip()
                if not part:
                    continue
                s = input_data.find(part, offset)
                sentences.append(Sentence(index=i, text=part, start=s, end=s + len(part)))
                offset = s + len(part)
            return ProcessorResult(
                module_name=self.name, status=ProcessorStatus.READY,
                data=SentenceSplitResult(sentences=sentences, count=len(sentences)),
                processing_time_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            logger.error("Sentence splitting failed: %s", e, exc_info=True)
            return ProcessorResult(
                module_name=self.name, status=ProcessorStatus.FAILED,
                data=None, errors=[str(e)],
                processing_time_ms=(time.time() - start) * 1000,
            )


# ── M2: Tokenizer ────────────────────────────────────────────────────────────


class HebPipeTokenizer(Processor):
    """M2: Токенизация предложения по пробелам."""

    @property
    def name(self) -> str:
        return "tokenizer"

    @property
    def module_id(self) -> str:
        return "M2"

    def validate_input(self, input_data: Any) -> bool:
        return isinstance(input_data, str)

    def process(self, input_data: str, config: Dict[str, Any]) -> ProcessorResult:
        start = time.time()
        try:
            raw_tokens = input_data.split()
            tokens = []
            offset = 0
            for i, raw in enumerate(raw_tokens):
                pos = input_data.find(raw, offset)
                tokens.append(Token(
                    index=i, surface=raw,
                    start=pos, end=pos + len(raw),
                    is_punct=bool(re.match(r'^[^\u0590-\u05FF\w]+$', raw)),
                ))
                offset = pos + len(raw)
            return ProcessorResult(
                module_name=self.name, status=ProcessorStatus.READY,
                data=TokenizeResult(tokens=tokens, count=len(tokens)),
                processing_time_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            logger.error("Tokenization failed: %s", e, exc_info=True)
            return ProcessorResult(
                module_name=self.name, status=ProcessorStatus.FAILED,
                data=None, errors=[str(e)],
                processing_time_ms=(time.time() - start) * 1000,
            )


# ── M3: Morphological Analyzer ───────────────────────────────────────────────


class HebPipeMorphAnalyzer(Processor):
    """M3: Морфологический анализ токенов."""

    @property
    def name(self) -> str:
        return "morph_analyzer"

    @property
    def module_id(self) -> str:
        return "M3"

    def validate_input(self, input_data: Any) -> bool:
        return isinstance(input_data, list) and all(isinstance(t, Token) for t in input_data)

    def process(self, input_data: List[Token], config: Dict[str, Any]) -> ProcessorResult:
        start = time.time()
        try:
            analyses = []
            for token in input_data:
                is_det = token.surface.startswith("\u05d4")  # ה
                analysis = MorphAnalysis(
                    surface=token.surface,
                    base=token.surface,
                    lemma=token.surface,
                    pos="NOUN",
                    features={},
                    is_det=is_det,
                    prefix_chain=["ה"] if is_det else [],
                )
                analyses.append(analysis)
            return ProcessorResult(
                module_name=self.name, status=ProcessorStatus.READY,
                data=MorphResult(analyses=analyses, count=len(analyses)),
                processing_time_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            logger.error("Morph analysis failed: %s", e, exc_info=True)
            return ProcessorResult(
                module_name=self.name, status=ProcessorStatus.FAILED,
                data=None, errors=[str(e)],
                processing_time_ms=(time.time() - start) * 1000,
            )
