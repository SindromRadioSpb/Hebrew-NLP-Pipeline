"""Tests for kadima.engine.hebpipe_wrappers (M1-M3)."""

import pytest
from kadima.engine.hebpipe_wrappers import (
    HebPipeSentSplitter, HebPipeTokenizer, HebPipeMorphAnalyzer,
    Sentence, SentenceSplitResult, Token, TokenizeResult,
    MorphAnalysis, MorphResult,
)
from kadima.engine.base import ProcessorStatus


class TestHebPipeSentSplitter:
    @pytest.fixture
    def splitter(self):
        return HebPipeSentSplitter()

    def test_basic_split(self, splitter):
        text = "פלדה חזקה משמשת בבניין. חוזק מתיחה גבוה מאד."
        result = splitter.process(text, {})
        assert result.status == ProcessorStatus.READY
        assert result.data.count >= 1

    def test_single_sentence(self, splitter):
        text = "פלדה חזקה"
        result = splitter.process(text, {})
        assert result.status == ProcessorStatus.READY
        assert result.data.count == 1

    def test_empty_input(self, splitter):
        result = splitter.process("", {})
        assert result.status == ProcessorStatus.FAILED

    def test_module_metadata(self, splitter):
        assert splitter.name == "sent_split"
        assert splitter.module_id == "M1"

    def test_validate_input(self, splitter):
        assert splitter.validate_input("טקסט")
        assert not splitter.validate_input("")
        assert not splitter.validate_input(123)


class TestHebPipeTokenizer:
    @pytest.fixture
    def tokenizer(self):
        return HebPipeTokenizer()

    def test_basic_tokenize(self, tokenizer):
        result = tokenizer.process("חוזק מתיחה של הפלדה", {})
        assert result.status == ProcessorStatus.READY
        assert result.data.count == 4
        assert result.data.tokens[0].surface == "חוזק"

    def test_punct_detection(self, tokenizer):
        result = tokenizer.process("test.", {})
        assert result.status == ProcessorStatus.READY
        assert result.data.tokens[0].is_punct is False  # "test." is not pure punct

    def test_empty_string(self, tokenizer):
        result = tokenizer.process("", {})
        assert result.status == ProcessorStatus.READY
        assert result.data.count == 0

    def test_module_metadata(self, tokenizer):
        assert tokenizer.name == "tokenizer"
        assert tokenizer.module_id == "M2"


class TestHebPipeMorphAnalyzer:
    @pytest.fixture
    def analyzer(self):
        return HebPipeMorphAnalyzer()

    def test_basic_morph(self, analyzer):
        tokens = [
            Token(index=0, surface="פלדה", start=0, end=4),
            Token(index=1, surface="חזקה", start=5, end=9),
        ]
        result = analyzer.process(tokens, {})
        assert result.status == ProcessorStatus.READY
        assert result.data.count == 2

    def test_det_detection(self, analyzer):
        tokens = [Token(index=0, surface="הפלדה", start=0, end=5)]
        result = analyzer.process(tokens, {})
        analysis = result.data.analyses[0]
        assert analysis.is_det is True
        assert analysis.prefix_chain == ["ה"]

    def test_non_det(self, analyzer):
        tokens = [Token(index=0, surface="פלדה", start=0, end=4)]
        result = analyzer.process(tokens, {})
        analysis = result.data.analyses[0]
        assert analysis.is_det is False
        assert analysis.prefix_chain == []

    def test_empty_input(self, analyzer):
        result = analyzer.process([], {})
        assert result.status == ProcessorStatus.READY
        assert result.data.count == 0

    def test_module_metadata(self, analyzer):
        assert analyzer.name == "morph_analyzer"
        assert analyzer.module_id == "M3"
