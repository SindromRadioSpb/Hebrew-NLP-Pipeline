# kadima/pipeline/orchestrator.py
"""Pipeline Orchestrator: M1→M2→M3→M4→M5→M6→M7→M8.

Data flow:
  str → M1 sent_split → SentenceSplitResult
  SentenceSplitResult → M2 tokenizer (per sentence) → List[Token]
  List[Token] → M3 morph_analyzer → MorphResult
  MorphResult → M4 ngram → NgramResult
  MorphResult → M5 np_chunk → NPChunkResult
  NgramResult + NPChunkResult → M6 canonicalize → CanonicalResult
  NgramResult → M7 am → AMResult
  ngrams + am_scores + np_chunks → M8 term_extract → TermResult
"""

import time
import logging
from typing import Dict, Any, Optional, List

from kadima.engine.base import Processor, PipelineResult, ProcessorStatus
from kadima.engine.hebpipe_wrappers import (
    SentenceSplitResult, TokenizeResult, MorphResult, Token,
)
from kadima.engine.ngram_extractor import NgramResult
from kadima.engine.np_chunker import NPChunkResult
from kadima.engine.association_measures import AMResult
from kadima.pipeline.config import PipelineConfig

logger = logging.getLogger(__name__)


class PipelineService:
    """Оркестрирует выполнение модулей Engine Layer.

    Ключевая ответственность: трансформация данных между модулями.
    Каждый модуль принимает конкретный тип, оркестратор обеспечивает
    правильный маппинг выхода предыдущего модуля на вход следующего.
    """

    def __init__(self, config: PipelineConfig, db_path: str = "~/.kadima/kadima.db"):
        self.config = config
        self.db_path = db_path
        self.modules: Dict[str, Processor] = {}
        self._register_modules()

    def _register_modules(self) -> None:
        from kadima.engine.hebpipe_wrappers import HebPipeSentSplitter, HebPipeTokenizer, HebPipeMorphAnalyzer
        from kadima.engine.ngram_extractor import NgramExtractor
        from kadima.engine.np_chunker import NPChunker
        from kadima.engine.canonicalizer import Canonicalizer
        from kadima.engine.association_measures import AMEngine
        from kadima.engine.term_extractor import TermExtractor
        from kadima.engine.noise_classifier import NoiseClassifier

        self.modules = {
            "sent_split": HebPipeSentSplitter(),
            "tokenizer": HebPipeTokenizer(),
            "morph_analyzer": HebPipeMorphAnalyzer(),
            "ngram": NgramExtractor(),
            "np_chunk": NPChunker(),
            "canonicalize": Canonicalizer(),
            "am": AMEngine(),
            "term_extract": TermExtractor(),
            "noise": NoiseClassifier(),
        }

    def _get_module_config(self, module_name: str) -> Dict[str, Any]:
        """Получить конфигурацию модуля с учётом профиля."""
        base = self.config.get_module_config(module_name)
        base["profile"] = self.config.profile.value
        return base

    def run(self, corpus_id: int) -> PipelineResult:
        """Запускает pipeline на корпусе (из БД)."""
        # TODO: загрузить документы из БД, запустить run_on_text на каждом
        return PipelineResult(corpus_id=corpus_id, profile=self.config.profile.value)

    def run_on_text(self, text: str) -> PipelineResult:
        """Запускает pipeline на одном тексте (без БД).

        Модули выполняются последовательно, каждый получает данные
        от предыдущего в правильном формате.
        """
        start = time.time()
        result = PipelineResult(corpus_id=0, profile=self.config.profile.value)

        # Промежуточные данные между модулями
        sentences_data: Optional[SentenceSplitResult] = None
        all_tokens: List[Token] = []           # flat list для noise
        tokens_per_sentence: List[List[Token]] = []  # для ngram
        morph_per_sentence: List[List] = []    # для np_chunk
        ngram_result: Optional[NgramResult] = None
        np_chunk_result: Optional[NPChunkResult] = None
        am_result: Optional[AMResult] = None
        canonical_mappings: Dict[str, str] = {}

        enabled = self.config.modules

        # ── M1: Sentence Split ───────────────────────────────────────────
        if "sent_split" in enabled and "sent_split" in self.modules:
            proc = self.modules["sent_split"]
            proc_result = proc.process(text, self._get_module_config("sent_split"))
            result.module_results["sent_split"] = proc_result

            if proc_result.status == ProcessorStatus.FAILED:
                logger.error("sent_split failed, aborting")
                result.status = ProcessorStatus.FAILED
                return result

            sentences_data = proc_result.data  # SentenceSplitResult
            logger.debug("M1: %d sentences", sentences_data.count)

        # ── M2: Tokenize (per sentence) ──────────────────────────────────
        if "tokenizer" in enabled and "tokenizer" in self.modules:
            proc = self.modules["tokenizer"]
            tokens_per_sentence = []
            all_tokens = []

            sentences = sentences_data.sentences if sentences_data else [type('S', (), {'text': text, 'index': 0})()]
            for sent in sentences:
                proc_result = proc.process(sent.text, self._get_module_config("tokenizer"))
                if proc_result.status == ProcessorStatus.READY:
                    tok_result: TokenizeResult = proc_result.data
                    tokens_per_sentence.append(tok_result.tokens)
                    all_tokens.extend(tok_result.tokens)

            result.module_results["tokenizer"] = proc_result
            logger.debug("M2: %d tokens in %d sentences", len(all_tokens), len(tokens_per_sentence))

        # ── M3: Morphological Analysis (per sentence) ────────────────────
        if "morph_analyzer" in enabled and "morph_analyzer" in self.modules:
            proc = self.modules["morph_analyzer"]
            morph_per_sentence = []

            for sent_tokens in tokens_per_sentence:
                proc_result = proc.process(sent_tokens, self._get_module_config("morph_analyzer"))
                if proc_result.status == ProcessorStatus.READY:
                    morph_result: MorphResult = proc_result.data
                    morph_per_sentence.append(morph_result.analyses)

            result.module_results["morph_analyzer"] = proc_result
            logger.debug("M3: %d sentences morphed", len(morph_per_sentence))

        # ── M4: N-gram Extraction ────────────────────────────────────────
        if "ngram" in enabled and "ngram" in self.modules:
            proc = self.modules["ngram"]
            proc_result = proc.process(tokens_per_sentence, self._get_module_config("ngram"))
            result.module_results["ngram"] = proc_result

            if proc_result.status == ProcessorStatus.READY:
                ngram_result = proc_result.data  # NgramResult
                result.ngrams = ngram_result.ngrams
                logger.debug("M4: %d ngrams", ngram_result.filtered)

        # ── M5: NP Chunking ──────────────────────────────────────────────
        if "np_chunk" in enabled and "np_chunk" in self.modules:
            proc = self.modules["np_chunk"]
            proc_result = proc.process(morph_per_sentence, self._get_module_config("np_chunk"))
            result.module_results["np_chunk"] = proc_result

            if proc_result.status == ProcessorStatus.READY:
                np_chunk_result = proc_result.data  # NPChunkResult
                result.np_chunks = np_chunk_result.chunks
                logger.debug("M5: %d NP chunks", np_chunk_result.total)

        # ── M6: Canonicalization ─────────────────────────────────────────
        if "canonicalize" in enabled and "canonicalize" in self.modules:
            proc = self.modules["canonicalize"]
            surfaces = list(set(t.surface for t in all_tokens))
            proc_result = proc.process(surfaces, self._get_module_config("canonicalize"))
            result.module_results["canonicalize"] = proc_result

            if proc_result.status == ProcessorStatus.READY:
                from kadima.engine.canonicalizer import CanonicalResult
                canon: CanonicalResult = proc_result.data
                canonical_mappings = {m.surface: m.canonical for m in canon.mappings}
                logger.debug("M6: %d canonical mappings", len(canonical_mappings))

        # ── M7: Association Measures ─────────────────────────────────────
        if "am" in enabled and "am" in self.modules and ngram_result:
            proc = self.modules["am"]
            proc_result = proc.process(ngram_result.ngrams, self._get_module_config("am"))
            result.module_results["am"] = proc_result

            if proc_result.status == ProcessorStatus.READY:
                am_result = proc_result.data  # AMResult
                logger.debug("M7: %d AM scores", len(am_result.scores))

        # ── M8: Term Extraction ──────────────────────────────────────────
        if "term_extract" in enabled and "term_extract" in self.modules:
            proc = self.modules["term_extract"]

            # Собираем AM scores в dict для TermExtractor
            am_scores = {}
            if am_result:
                for score in am_result.scores:
                    am_scores[score.pair] = {"pmi": score.pmi, "llr": score.llr, "dice": score.dice}

            term_input = {
                "ngrams": ngram_result.ngrams if ngram_result else [],
                "am_scores": am_scores,
                "np_chunks": np_chunk_result.chunks if np_chunk_result else [],
            }
            proc_result = proc.process(term_input, self._get_module_config("term_extract"))
            result.module_results["term_extract"] = proc_result

            if proc_result.status == ProcessorStatus.READY:
                from kadima.engine.term_extractor import TermResult
                term_result: TermResult = proc_result.data
                result.terms = term_result.terms
                logger.debug("M8: %d terms", len(term_result.terms))

        # ── M12: Noise Classification ────────────────────────────────────
        if "noise" in enabled and "noise" in self.modules:
            proc = self.modules["noise"]
            proc_result = proc.process(all_tokens, self._get_module_config("noise"))
            result.module_results["noise"] = proc_result
            logger.debug("M12: noise classified %d tokens", len(all_tokens))

        result.total_time_ms = (time.time() - start) * 1000
        result.status = ProcessorStatus.READY
        return result
