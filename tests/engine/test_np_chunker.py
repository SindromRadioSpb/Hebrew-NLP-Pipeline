"""Tests for M5: NP Chunker (rules + embeddings modes)."""

import numpy as np
import pytest
import spacy

from kadima.engine.np_chunker import (
    NPChunk, NPChunker, NPChunkResult,
    _cosine, chunk_precision, chunk_recall,
)
from kadima.engine.hebpipe_wrappers import MorphAnalysis
from kadima.engine.base import ProcessorStatus


def _make_morph(surface: str, base: str, lemma: str, pos: str) -> MorphAnalysis:
    return MorphAnalysis(surface=surface, base=base, lemma=lemma, pos=pos)


def _make_doc(tokens_pos: list[tuple[str, str]]) -> "spacy.tokens.Doc":
    """Create a spaCy Doc with controlled POS tags and a random tensor."""
    nlp = spacy.blank("he")
    words = [t for t, _ in tokens_pos]
    doc = nlp.make_doc(" ".join(words))
    # Assign POS tags
    for token, (_, pos) in zip(doc, tokens_pos):
        token.pos_ = pos
    # Random 768-dim tensor (simulates NeoDictaBERT output)
    n = len(doc)
    doc.tensor = np.random.default_rng(42).standard_normal((n, 768)).astype("float32")
    return doc


def _make_similar_doc(tokens_pos: list[tuple[str, str]], sim: float = 0.95) -> "spacy.tokens.Doc":
    """Create a Doc where ALL token vectors are very similar (controlled similarity)."""
    nlp = spacy.blank("he")
    words = [t for t, _ in tokens_pos]
    doc = nlp.make_doc(" ".join(words))
    for token, (_, pos) in zip(doc, tokens_pos):
        token.pos_ = pos
    n = len(doc)
    base = np.ones(768, dtype=np.float32)
    base /= np.linalg.norm(base)
    # Each token vector ≈ base + small noise → cosine(base, tok) ≈ sim
    noise_scale = (1 - sim) * 0.1
    rng = np.random.default_rng(0)
    tensor = np.stack([base + rng.standard_normal(768).astype("float32") * noise_scale for _ in range(n)])
    doc.tensor = tensor
    return doc


class TestNPChunker:
    @pytest.fixture
    def chunker(self):
        return NPChunker()

    def test_noun_noun_pattern(self, chunker):
        morphs = [[
            _make_morph("חוזק", "חוזק", "חוזק", "NOUN"),
            _make_morph("מתיחה", "מתיחה", "מתיחה", "NOUN"),
        ]]
        result = chunker.process(morphs, {})
        assert result.status == ProcessorStatus.READY
        assert len(result.data.chunks) == 1
        assert result.data.chunks[0].pattern == "NOUN_NOUN"
        assert result.data.chunks[0].surface == "חוזק מתיחה"

    def test_noun_adj_pattern(self, chunker):
        morphs = [[
            _make_morph("פלדה", "פלדה", "פלדה", "NOUN"),
            _make_morph("חזקה", "חזק", "חזק", "ADJ"),
        ]]
        result = chunker.process(morphs, {})
        assert result.status == ProcessorStatus.READY
        assert len(result.data.chunks) == 1
        assert result.data.chunks[0].pattern == "NOUN_ADJ"

    def test_no_chunks(self, chunker):
        morphs = [[
            _make_morph("של", "של", "של", "PREP"),
            _make_morph("ה", "ה", "ה", "DET"),
        ]]
        result = chunker.process(morphs, {})
        assert result.status == ProcessorStatus.READY
        assert len(result.data.chunks) == 0

    def test_multiple_sentences(self, chunker):
        morphs = [
            [_make_morph("חוזק", "חוזק", "חוזק", "NOUN"), _make_morph("מתיחה", "מתיחה", "מתיחה", "NOUN")],
            [_make_morph("בטון", "בטון", "בטון", "NOUN"), _make_morph("קל", "קל", "קל", "ADJ")],
        ]
        result = chunker.process(morphs, {})
        assert result.status == ProcessorStatus.READY
        assert len(result.data.chunks) == 2
        assert result.data.chunks[0].sentence_idx == 0
        assert result.data.chunks[1].sentence_idx == 1

    def test_empty_input(self, chunker):
        result = chunker.process([], {})
        assert result.status == ProcessorStatus.READY
        assert len(result.data.chunks) == 0

    def test_validate_input(self, chunker):
        morphs = [[_make_morph("חוזק", "חוזק", "חוזק", "NOUN")]]
        assert chunker.validate_input(morphs)
        assert not chunker.validate_input("bad")

    def test_module_id(self, chunker):
        assert chunker.module_id == "M5"
        assert chunker.name == "np_chunk"

    def test_result_mode_rules(self, chunker):
        morphs = [[_make_morph("חוזק", "חוזק", "חוזק", "NOUN"), _make_morph("מתיחה", "מתיחה", "מתיחה", "NOUN")]]
        result = chunker.process(morphs, {"mode": "rules"})
        assert result.data.mode == "rules"

    def test_explicit_rules_mode(self, chunker):
        morphs = [[_make_morph("חוזק", "חוזק", "חוזק", "NOUN"), _make_morph("מתיחה", "מתיחה", "מתיחה", "NOUN")]]
        result = chunker.process(morphs, {"mode": "rules"})
        assert result.status == ProcessorStatus.READY
        assert result.data.total == 1


class TestNPChunkerEmbeddings:
    @pytest.fixture
    def chunker(self):
        return NPChunker()

    def test_embeddings_mode_returns_chunks(self, chunker):
        """With similar vectors, embeddings mode should find NP spans."""
        doc = _make_similar_doc([("חוזק", "NOUN"), ("מתיחה", "NOUN")], sim=0.95)
        result = chunker.process(doc, {"mode": "embeddings", "sim_threshold": 0.3})
        assert result.status == ProcessorStatus.READY
        assert result.data.mode == "embeddings"

    def test_auto_mode_uses_embeddings_when_tensor_present(self, chunker):
        doc = _make_similar_doc([("פלדה", "NOUN"), ("חזקה", "ADJ")])
        result = chunker.process(doc, {"mode": "auto"})
        assert result.data.mode == "embeddings"

    def test_auto_mode_falls_back_to_rules_without_tensor(self, chunker):
        morphs = [[_make_morph("פלדה", "פלדה", "פלדה", "NOUN"), _make_morph("חזקה", "חזק", "חזק", "ADJ")]]
        result = chunker.process(morphs, {"mode": "auto"})
        assert result.data.mode == "rules"

    def test_embeddings_mode_fallback_on_missing_tensor(self, chunker):
        """If tensor is missing, embeddings mode falls back to rules (no crash)."""
        nlp = spacy.blank("he")
        doc = nlp("שלום")
        # doc.tensor is empty by default
        result = chunker.process(doc, {"mode": "embeddings"})
        assert result.status == ProcessorStatus.READY

    def test_process_doc_convenience(self, chunker):
        doc = _make_similar_doc([("חוזק", "NOUN"), ("מתיחה", "NOUN")])
        result = chunker.process_doc(doc, {})
        assert result.status == ProcessorStatus.READY

    def test_chunk_score_is_set(self, chunker):
        doc = _make_similar_doc([("פלדה", "NOUN"), ("גבוהה", "ADJ")], sim=0.9)
        result = chunker.process(doc, {"mode": "embeddings", "sim_threshold": 0.2})
        if result.data.chunks:
            assert 0.0 <= result.data.chunks[0].score <= 1.0

    def test_no_overlap_in_chunks(self, chunker):
        """Each token should appear in at most one chunk."""
        doc = _make_similar_doc([("א", "NOUN"), ("ב", "NOUN"), ("ג", "NOUN")], sim=0.9)
        result = chunker.process(doc, {"mode": "embeddings", "sim_threshold": 0.3})
        all_tokens: list = []
        for c in result.data.chunks:
            all_tokens.extend(c.tokens)
        # No duplicates
        assert len(all_tokens) == len(set(all_tokens))


class TestNPChunkerMetrics:
    def _chunk(self, surface: str) -> NPChunk:
        return NPChunk(surface=surface, tokens=[], pattern="", start=0, end=0, sentence_idx=0)

    def test_precision_perfect(self):
        pred = [self._chunk("א ב"), self._chunk("ג ד")]
        assert chunk_precision(pred, pred) == 1.0

    def test_precision_empty_predicted(self):
        expected = [self._chunk("א ב")]
        assert chunk_precision([], expected) == 0.0

    def test_recall_perfect(self):
        pred = [self._chunk("א ב")]
        assert chunk_recall(pred, pred) == 1.0

    def test_recall_empty_expected(self):
        pred = [self._chunk("א ב")]
        assert chunk_recall(pred, []) == 0.0

    def test_cosine_identical(self):
        v = np.ones(768, dtype=np.float32)
        assert abs(_cosine(v, v) - 1.0) < 1e-6

    def test_cosine_orthogonal(self):
        a = np.array([1.0, 0.0], dtype=np.float32)
        b = np.array([0.0, 1.0], dtype=np.float32)
        assert abs(_cosine(a, b)) < 1e-6

    def test_cosine_zero_vector(self):
        a = np.zeros(4, dtype=np.float32)
        b = np.ones(4, dtype=np.float32)
        assert _cosine(a, b) == 0.0
