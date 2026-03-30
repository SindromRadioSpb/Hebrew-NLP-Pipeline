"""Tests for M5: NP Chunker."""

import pytest
from kadima.engine.np_chunker import NPChunker, NPChunk
from kadima.engine.hebpipe_wrappers import MorphAnalysis
from kadima.engine.base import ProcessorStatus


def _make_morph(surface: str, base: str, lemma: str, pos: str) -> MorphAnalysis:
    return MorphAnalysis(surface=surface, base=base, lemma=lemma, pos=pos)


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
