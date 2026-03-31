# kadima/engine/hebpipe_wrappers.py
"""M1–M3: Обёртки над HebPipe для интеграции в pipeline.

Data flow:
  M1 HebPipeSentSplitter:  str → SentenceSplitResult
  M2 HebPipeTokenizer:     str → TokenizeResult
  M3 HebPipeMorphAnalyzer: List[Token] → MorphResult

Example (full M1→M2→M3 chain):
    >>> from kadima.engine.hebpipe_wrappers import (
    ...     HebPipeSentSplitter, HebPipeTokenizer, HebPipeMorphAnalyzer,
    ... )
    >>> text = "פלדה חזקה משמשת בבניין. חוזק מתיחה גבוה."
    >>> # M1: sentence split
    >>> m1 = HebPipeSentSplitter()
    >>> r1 = m1.process(text, {})
    >>> sentences = [s.text for s in r1.data.sentences]
    >>> # M2: tokenize each sentence
    >>> m2 = HebPipeTokenizer()
    >>> tokens_per_sent = []
    >>> for sent in r1.data.sentences:
    ...     r2 = m2.process(sent.text, {})
    ...     tokens_per_sent.append(r2.data.tokens)
    >>> # M3: morphological analysis
    >>> m3 = HebPipeMorphAnalyzer()
    >>> r3 = m3.process(tokens_per_sent[0], {})
    >>> r3.data.analyses[0].lemma  # "פלדה"
    'פלדה'
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
    """Предложение с позицией в исходном тексте."""

    index: int
    text: str
    start: int        # char offset в исходном тексте
    end: int


@dataclass
class SentenceSplitResult:
    """Результат разбиения на предложения."""

    sentences: List[Sentence]
    count: int


@dataclass
class Token:
    """Токен с surface-формой и позицией."""

    index: int
    surface: str      # "הפלדה"
    start: int
    end: int
    is_punct: bool = False


@dataclass
class TokenizeResult:
    """Результат токенизации предложения."""

    tokens: List[Token]
    count: int


@dataclass
class MorphAnalysis:
    """Морфологический анализ одного токена."""

    surface: str
    base: str           # "פלדה" (без префиксов)
    lemma: str
    pos: str            # "NOUN" / "VERB" / "ADJ" / ...
    features: Dict[str, str] = field(default_factory=dict)
    is_det: bool = False
    prefix_chain: List[str] = field(default_factory=list)


@dataclass
class MorphResult:
    """Результат морфологического анализа предложения."""

    analyses: List[MorphAnalysis]
    count: int


# ── M1: Sentence Splitter ────────────────────────────────────────────────────


class HebPipeSentSplitter(Processor):
    """M1: Разбиение текста на предложения.

    Example:
        >>> splitter = HebPipeSentSplitter()
        >>> result = splitter.process("פלדה חזקה. בטון קל.", {})
        >>> result.data.count
        2
        >>> result.data.sentences[0].text
        'פלדה חזקה'
    """

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
    """M2: Токенизация предложения по пробелам.

    Example:
        >>> tok = HebPipeTokenizer()
        >>> result = tok.process("חוזק מתיחה של הפלדה", {})
        >>> result.data.count
        4
        >>> result.data.tokens[0].surface
        'חוזק'
    """

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

# Try to import hebpipe for real morphological analysis
_HEBPIPE_AVAILABLE = False
try:
    import hebpipe
    _HEBPIPE_AVAILABLE = True
    logger.info("hebpipe available — using full morphological analysis")
except ImportError:
    logger.info(
        "hebpipe not installed — using rule-based fallback. "
        "Install with: pip install -e '.[hebpipe]'"
    )


# ── Hebrew prefix/POS rules ────────────────────────────────────────────────

# Single-char proclitics: ב(in) ה(the) ו(and) ל(to) כ(like) מ(from) ש(that)
_PREFIXES_SINGLE = "בהולכמש"

# Common multi-char prefix chains (ordered longest-first for greedy match)
_PREFIX_CHAINS = [
    ("וכש", ["ו", "כש"]),    # and+when
    ("וב", ["ו", "ב"]),      # and+in
    ("ול", ["ו", "ל"]),      # and+to
    ("וה", ["ו", "ה"]),      # and+the
    ("וכ", ["ו", "כ"]),      # and+like
    ("ומ", ["ו", "מ"]),      # and+from
    ("וש", ["ו", "ש"]),      # and+that
    ("של", ["של"]),           # of (genitive)
    ("בה", ["ב", "ה"]),      # in+the
    ("לה", ["ל", "ה"]),      # to+the
    ("כה", ["כ", "ה"]),      # like+the
    ("מה", ["מ", "ה"]),      # from+the
    ("שה", ["ש", "ה"]),      # that+the
    ("שב", ["ש", "ב"]),      # that+in
    ("שמ", ["ש", "מ"]),      # that+from
    ("כש", ["כש"]),           # when
]

# Minimum remaining stem length after prefix stripping
_MIN_STEM_LEN = 2

# Function words: prepositions, conjunctions, particles
_FUNCTION_WORDS: Dict[str, str] = {
    # Prepositions → ADP
    "של": "ADP", "על": "ADP", "אל": "ADP", "עם": "ADP",
    "את": "ADP", "מן": "ADP", "בין": "ADP", "אצל": "ADP",
    "לפני": "ADP", "אחרי": "ADP", "תחת": "ADP", "בלי": "ADP",
    "בגלל": "ADP", "למען": "ADP", "כלפי": "ADP", "מול": "ADP",
    "ליד": "ADP", "סביב": "ADP", "דרך": "ADP", "עד": "ADP",
    "מעל": "ADP", "מתחת": "ADP",
    # Conjunctions → CCONJ / SCONJ
    "או": "CCONJ", "אבל": "CCONJ", "אך": "CCONJ",
    "גם": "CCONJ", "אלא": "CCONJ", "אולם": "CCONJ",
    "כי": "SCONJ", "אם": "SCONJ", "כאשר": "SCONJ",
    "כשם": "SCONJ", "למרות": "SCONJ", "משום": "SCONJ",
    "שכן": "SCONJ", "לכן": "SCONJ",
    # Adverbs → ADV
    "מאד": "ADV", "מאוד": "ADV", "גם": "ADV", "רק": "ADV",
    "כבר": "ADV", "עוד": "ADV", "כאן": "ADV", "שם": "ADV",
    "היום": "ADV", "אתמול": "ADV", "מחר": "ADV", "עכשיו": "ADV",
    "תמיד": "ADV", "לעולם": "ADV", "הרבה": "ADV", "קצת": "ADV",
    "יותר": "ADV", "פחות": "ADV", "ביותר": "ADV",
    # Pronouns → PRON
    "הוא": "PRON", "היא": "PRON", "הם": "PRON", "הן": "PRON",
    "אני": "PRON", "אנחנו": "PRON", "אתה": "PRON", "את": "PRON",
    "אתם": "PRON", "אתן": "PRON", "זה": "PRON", "זאת": "PRON",
    "זו": "PRON", "אלה": "PRON", "אלו": "PRON",
    # Existential / copula → VERB
    "יש": "VERB", "אין": "VERB", "היה": "VERB", "היתה": "VERB",
    "היו": "VERB", "יהיה": "VERB", "תהיה": "VERB",
    # Determiners → DET
    "כל": "DET", "כמה": "DET", "הרבה": "DET", "כמעט": "ADV",
    # Quantifiers / Numerals → NUM
    "אחד": "NUM", "שני": "NUM", "שתי": "NUM", "שלוש": "NUM",
    "ארבע": "NUM", "חמש": "NUM", "שש": "NUM", "שבע": "NUM",
    "שמונה": "NUM", "תשע": "NUM", "עשר": "NUM",
}

# Hebrew char range for checking if token is Hebrew
_HE_RANGE = re.compile(r'[\u0590-\u05FF]')
_ALL_HE = re.compile(r'^[\u0590-\u05FF]+$')
_PUNCT_RE = re.compile(r'^[^\w\u0590-\u05FF]+$')
_NUM_RE = re.compile(r'^[\d.,/%+-]+$')

# Common adjective suffixes (feminine ה-, plural ים-/ות-)
_ADJ_PATTERNS = re.compile(
    r'^[\u0590-\u05FF]{2,}(ית|יים|יות|ני|נית|לי|לית|אי|אית)$'
)


def _strip_prefixes(surface: str) -> tuple:
    """Strip Hebrew proclitics from surface form.

    Returns:
        (base, prefix_chain, has_det)
    """
    if not _ALL_HE.match(surface) or len(surface) < _MIN_STEM_LEN + 1:
        return surface, [], False

    # Try multi-char chains first (longest match)
    for chain_str, chain_parts in _PREFIX_CHAINS:
        if surface.startswith(chain_str) and len(surface) - len(chain_str) >= _MIN_STEM_LEN:
            base = surface[len(chain_str):]
            has_det = "ה" in chain_parts
            return base, chain_parts, has_det

    # Try single-char prefix
    first = surface[0]
    if first in _PREFIXES_SINGLE and len(surface) - 1 >= _MIN_STEM_LEN:
        base = surface[1:]
        has_det = first == "ה"
        return base, [first], has_det

    return surface, [], False


def _detect_pos(surface: str, base: str) -> str:
    """Heuristic POS detection for Hebrew token."""
    # Punctuation
    if _PUNCT_RE.match(surface):
        return "PUNCT"

    # Numbers
    if _NUM_RE.match(surface):
        return "NUM"

    # Function words (check both surface and base)
    if surface in _FUNCTION_WORDS:
        return _FUNCTION_WORDS[surface]
    if base != surface and base in _FUNCTION_WORDS:
        return _FUNCTION_WORDS[base]

    # Non-Hebrew tokens (Latin, mixed)
    if not _HE_RANGE.search(surface):
        return "X"

    # Adjective patterns (nisba/relational suffixes)
    if _ADJ_PATTERNS.match(base):
        return "ADJ"

    # Default: NOUN (most common POS in Hebrew text)
    return "NOUN"


class HebPipeMorphAnalyzer(Processor):
    """M3: Морфологический анализ токенов.

    Использует hebpipe когда доступен, иначе rule-based fallback
    с prefix stripping и POS heuristics.

    Example:
        >>> from kadima.engine.hebpipe_wrappers import Token
        >>> m3 = HebPipeMorphAnalyzer()
        >>> tokens = [Token(0, "הפלדה", 0, 5)]
        >>> result = m3.process(tokens, {})
        >>> a = result.data.analyses[0]
        >>> a.is_det
        True
        >>> a.prefix_chain
        ['ה']
        >>> a.base
        'פלדה'
    """

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
            if _HEBPIPE_AVAILABLE:
                analyses = self._process_hebpipe(input_data, config)
            else:
                analyses = self._process_rules(input_data)

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

    def _process_rules(self, tokens: List[Token]) -> List[MorphAnalysis]:
        """Rule-based morphological analysis (fallback)."""
        analyses = []
        for token in tokens:
            surface = token.surface

            # Function words recognized as-is (no prefix stripping)
            if surface in _FUNCTION_WORDS:
                analyses.append(MorphAnalysis(
                    surface=surface,
                    base=surface,
                    lemma=surface,
                    pos=_FUNCTION_WORDS[surface],
                    features={},
                    is_det=False,
                    prefix_chain=[],
                ))
                continue

            base, prefix_chain, has_det = _strip_prefixes(surface)
            pos = _detect_pos(surface, base)
            lemma = base

            analyses.append(MorphAnalysis(
                surface=surface,
                base=base,
                lemma=lemma,
                pos=pos,
                features={},
                is_det=has_det,
                prefix_chain=prefix_chain,
            ))
        return analyses

    def _process_hebpipe(self, tokens: List[Token], config: Dict[str, Any]) -> List[MorphAnalysis]:
        """Full morphological analysis via hebpipe."""
        # Reconstruct sentence text for hebpipe
        text = " ".join(t.surface for t in tokens)
        try:
            result = hebpipe.parse(text)
            analyses = []
            for i, token in enumerate(tokens):
                if i < len(result):
                    parsed = result[i]
                    analyses.append(MorphAnalysis(
                        surface=token.surface,
                        base=getattr(parsed, "lemma", token.surface),
                        lemma=getattr(parsed, "lemma", token.surface),
                        pos=getattr(parsed, "pos", "NOUN"),
                        features=getattr(parsed, "features", {}),
                        is_det=getattr(parsed, "is_det", False),
                        prefix_chain=getattr(parsed, "prefixes", []),
                    ))
                else:
                    # Fallback for alignment mismatch
                    base, prefix_chain, has_det = _strip_prefixes(token.surface)
                    analyses.append(MorphAnalysis(
                        surface=token.surface,
                        base=base,
                        lemma=base,
                        pos=_detect_pos(token.surface, base),
                        features={},
                        is_det=has_det,
                        prefix_chain=prefix_chain,
                    ))
            return analyses
        except Exception as e:
            logger.warning("hebpipe failed, falling back to rules: %s", e)
            return self._process_rules(tokens)
