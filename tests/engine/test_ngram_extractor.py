"""Tests for M4: NgramExtractor."""

import pytest
from kadima.engine.ngram_extractor import NgramExtractor, Ngram
from kadima.engine.hebpipe_wrappers import Token
from kadima.engine.base import ProcessorStatus


def _make_token(surface: str, index: int = 0) -> Token:
    return Token(index=index, surface=surface, start=0, end=len(surface))


class TestNgramExtractor:
    @pytest.fixture
    def extractor(self):
        return NgramExtractor()

    def test_basic_bigrams(self, extractor):
        tokens = [
            [_make_token("חוזק", 0), _make_token("מתיחה", 1), _make_token("של", 2), _make_token("הפלדה", 3)],
            [_make_token("חוזק", 0), _make_token("מתיחה", 1), _make_token("של", 2), _make_token("בטון", 3)],
        ]
        result = extractor.process(tokens, {"min_n": 2, "max_n": 3, "min_freq": 2})
        assert result.status == ProcessorStatus.READY
        assert len(result.data.ngrams) > 0
        bigram = next((n for n in result.data.ngrams if n.tokens == ["חוזק", "מתיחה"]), None)
        assert bigram is not None
        assert bigram.freq == 2

    def test_trigrams(self, extractor):
        tokens = [
            [_make_token("חוזק"), _make_token("מתיחה"), _make_token("של")],
            [_make_token("חוזק"), _make_token("מתיחה"), _make_token("של")],
        ]
        result = extractor.process(tokens, {"min_n": 3, "max_n": 3, "min_freq": 2})
        assert result.status == ProcessorStatus.READY
        trigrams = [n for n in result.data.ngrams if n.n == 3]
        assert any(n.tokens == ["חוזק", "מתיחה", "של"] for n in trigrams)

    def test_min_freq_filter(self, extractor):
        tokens = [[_make_token("aaa")], [_make_token("bbb")]]
        result = extractor.process(tokens, {"min_n": 2, "max_n": 2, "min_freq": 2})
        assert result.status == ProcessorStatus.READY
        # each doc has only 1 token → no bigrams at all
        assert len(result.data.ngrams) == 0

    def test_single_doc(self, extractor):
        tokens = [[_make_token("word1"), _make_token("word2"), _make_token("word3")]]
        result = extractor.process(tokens, {"min_n": 2, "max_n": 2, "min_freq": 1})
        assert result.status == ProcessorStatus.READY
        assert len(result.data.ngrams) == 2  # (w1,w2) and (w2,w3)

    def test_empty_input(self, extractor):
        result = extractor.process([], {"min_n": 2, "max_n": 2, "min_freq": 1})
        assert result.status == ProcessorStatus.READY
        assert len(result.data.ngrams) == 0

    def test_validate_input(self, extractor):
        assert extractor.validate_input([])
        assert extractor.validate_input([[_make_token("a"), _make_token("b")]])
        assert not extractor.validate_input("not a list")
        assert not extractor.validate_input(None)

    def test_module_id(self, extractor):
        assert extractor.module_id == "M4"
        assert extractor.name == "ngram"

    def test_ngram_attributes(self, extractor):
        tokens = [[_make_token("חוזק"), _make_token("מתיחה")]]
        result = extractor.process(tokens, {"min_n": 2, "max_n": 2, "min_freq": 1})
        ng = result.data.ngrams[0]
        assert ng.n == 2
        assert ng.tokens == ["חוזק", "מתיחה"]
        assert ng.freq == 1
        assert ng.doc_freq == 1
