# kadima/engine/np_chunker.py
"""M5: NP Chunk Extractor — извлечение именных групп.

Example:
    >>> from kadima.engine.np_chunker import NPChunker
    >>> from kadima.engine.hebpipe_wrappers import MorphAnalysis
    >>> chunker = NPChunker()
    >>> morphs = [[MorphAnalysis("חוזק","חוזק","חוזק","NOUN"), MorphAnalysis("מתיחה","מתיחה","מתיחה","NOUN")]]
    >>> result = chunker.process(morphs, {})
    >>> result.data.chunks[0].pattern
    "NOUN_NOUN"
"""

import time
from typing import Any, Dict, List
from dataclasses import dataclass

import logging

logger = logging.getLogger(__name__)

from kadima.engine.base import Processor, ProcessorResult, ProcessorStatus
from kadima.engine.hebpipe_wrappers import MorphAnalysis


@dataclass
class NPChunk:
    """Именная группа: surface-форма, токены, паттерн, позиция."""

    surface: str
    tokens: List[str]
    pattern: str
    start: int
    end: int
    sentence_idx: int


@dataclass
class NPChunkResult:
    """Результат NP chunking: список именных групп."""

    chunks: List[NPChunk]
    total: int


class NPChunker(Processor):
    """M5: NP pattern detection (N+N, N+ADJ, DET+N+ADJ)."""

    @property
    def name(self) -> str:
        return "np_chunk"

    @property
    def module_id(self) -> str:
        return "M5"

    def validate_input(self, input_data: Any) -> bool:
        return isinstance(input_data, list) and all(
            isinstance(sent, list) and all(isinstance(m, MorphAnalysis) for m in sent)
            for sent in input_data
        )

    def process(self, input_data: List[List[MorphAnalysis]], config: Dict[str, Any]) -> ProcessorResult:
        start = time.time()
        try:
            chunks = []
            for sent_idx, sentence in enumerate(input_data):
                i = 0
                while i < len(sentence):
                    # Pattern: NOUN + NOUN
                    if (i + 1 < len(sentence) and
                        sentence[i].pos == "NOUN" and sentence[i+1].pos == "NOUN"):
                        surface = f"{sentence[i].surface} {sentence[i+1].surface}"
                        chunks.append(NPChunk(
                            surface=surface, tokens=[sentence[i].surface, sentence[i+1].surface],
                            pattern="NOUN_NOUN", start=sentence[i].start if hasattr(sentence[i], 'start') else i,
                            end=sentence[i+1].end if hasattr(sentence[i+1], 'end') else i+1,
                            sentence_idx=sent_idx,
                        ))
                        i += 2
                        continue
                    # Pattern: NOUN + ADJ
                    if (i + 1 < len(sentence) and
                        sentence[i].pos == "NOUN" and sentence[i+1].pos == "ADJ"):
                        surface = f"{sentence[i].surface} {sentence[i+1].surface}"
                        chunks.append(NPChunk(
                            surface=surface, tokens=[sentence[i].surface, sentence[i+1].surface],
                            pattern="NOUN_ADJ", start=i, end=i+1, sentence_idx=sent_idx,
                        ))
                        i += 2
                        continue
                    i += 1

            return ProcessorResult(
                module_name=self.name, status=ProcessorStatus.READY,
                data=NPChunkResult(chunks=chunks, total=len(chunks)),
                processing_time_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            logger.error("NP chunking failed: %s", e, exc_info=True)
            return ProcessorResult(
                module_name=self.name, status=ProcessorStatus.FAILED,
                data=None, errors=[str(e)],
                processing_time_ms=(time.time() - start) * 1000,
            )
