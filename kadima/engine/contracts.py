# kadima/engine/contracts.py
"""Typed contracts for engine module inputs/outputs.

Defines Protocol classes and TypedDicts for each Processor's
input and output types. These contracts let Claude Code (and any
type checker) understand data flow between modules without reading
implementation details.

Actual data types are defined in their respective engine modules.
This file only defines:
  - TypedDict contracts for module inputs
  - ProcessorProtocol for structural typing
"""

from typing import Protocol, TypedDict, List, Dict, Tuple, Any, runtime_checkable


# ── TypedDict contracts (module inputs) ──────────────────────────────────────


class AMScoreDict(TypedDict):
    """Association scores for a bigram pair."""
    pmi: float
    llr: float
    dice: float


class TermExtractInput(TypedDict):
    """M8 input: aggregated n-grams + AM scores + NP chunks.

    Keys:
        ngrams: List[Ngram] from M4
        am_scores: Dict[Tuple[str,str], AMScoreDict] from M7
        np_chunks: List[NPChunk] from M5
    """
    ngrams: List[Any]       # List[engine.ngram_extractor.Ngram]
    am_scores: Dict[Tuple[str, str], AMScoreDict]
    np_chunks: List[Any]    # List[engine.np_chunker.NPChunk]


# ── Processor protocol ───────────────────────────────────────────────────────


@runtime_checkable
class ProcessorProtocol(Protocol):
    """Protocol that all Engine Layer processors must satisfy.

    This is the structural contract — any class with these methods
    qualifies as a Processor, regardless of inheritance.

    Module I/O contracts (input → output):
        M1 (HebPipeSentSplitter):  str → SentenceSplitResult
        M2 (HebPipeTokenizer):     str → TokenizeResult
        M3 (HebPipeMorphAnalyzer): List[Token] → MorphResult
        M4 (NgramExtractor):       List[List[Token]] → NgramResult
        M5 (NPChunker):            List[List[MorphAnalysis]] → NPChunkResult
        M6 (Canonicalizer):        List[str] → CanonicalResult
        M7 (AMEngine):             List[Ngram] → AMResult
        M8 (TermExtractor):        TermExtractInput → TermResult
        M12 (NoiseClassifier):     List[Token] → NoiseResult
    """

    @property
    def name(self) -> str:
        """Human-readable module name (e.g. 'ngram')."""
        ...

    @property
    def module_id(self) -> str:
        """Module ID (e.g. 'M4')."""
        ...

    def process(self, input_data: Any, config: Dict[str, Any]) -> Any:
        """Process input data and return ProcessorResult.

        Args:
            input_data: Module-specific input (see contracts above).
            config: Module configuration dict.

        Returns:
            ProcessorResult with .data containing the typed result.
        """
        ...

    def validate_input(self, input_data: Any) -> bool:
        """Validate input data type and structure."""
        ...
