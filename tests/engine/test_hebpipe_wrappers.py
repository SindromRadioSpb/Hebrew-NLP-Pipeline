"""Tests for kadima.engine.hebpipe_wrappers (M1-M3)."""

import pytest
from kadima.engine.hebpipe_wrappers import (
    HebPipeSentSplitter, HebPipeTokenizer, HebPipeMorphAnalyzer,
    Sentence, SentenceSplitResult, Token, TokenizeResult,
    MorphAnalysis, MorphResult,
    _strip_prefixes, _detect_pos,
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

    def test_function_word_pos(self, analyzer):
        """Function words get correct POS, not NOUN."""
        tokens = [
            Token(0, "של", 0, 2),
            Token(1, "על", 3, 5),
            Token(2, "או", 6, 8),
            Token(3, "כי", 9, 11),
            Token(4, "מאד", 12, 15),
        ]
        result = analyzer.process(tokens, {})
        analyses = result.data.analyses
        assert analyses[0].pos == "ADP"   # של
        assert analyses[1].pos == "ADP"   # על
        assert analyses[2].pos == "CCONJ" # או
        assert analyses[3].pos == "SCONJ" # כי
        assert analyses[4].pos == "ADV"   # מאד

    def test_function_word_no_prefix_strip(self, analyzer):
        """Function words keep their surface as base/lemma."""
        tokens = [Token(0, "מאד", 0, 3)]
        result = analyzer.process(tokens, {})
        a = result.data.analyses[0]
        assert a.base == "מאד"
        assert a.lemma == "מאד"
        assert a.prefix_chain == []

    def test_prefix_stripping_bet(self, analyzer):
        """ב prefix stripped correctly."""
        tokens = [Token(0, "בבניין", 0, 6)]
        result = analyzer.process(tokens, {})
        a = result.data.analyses[0]
        assert a.base == "בניין"
        assert a.prefix_chain == ["ב"]
        assert a.is_det is False

    def test_prefix_stripping_vav_he(self, analyzer):
        """וה (and+the) chain detected."""
        tokens = [Token(0, "והפלדה", 0, 6)]
        result = analyzer.process(tokens, {})
        a = result.data.analyses[0]
        assert "ו" in a.prefix_chain
        assert "ה" in a.prefix_chain
        assert a.is_det is True

    def test_prefix_stripping_shel(self, analyzer):
        """של (of) chain detected."""
        tokens = [Token(0, "שלבטון", 0, 6)]
        result = analyzer.process(tokens, {})
        a = result.data.analyses[0]
        assert a.prefix_chain == ["של"]

    def test_short_word_no_strip(self, analyzer):
        """Short words (<=2 chars) are not stripped."""
        tokens = [Token(0, "בן", 0, 2)]  # "בן" = son, not ב+ן
        result = analyzer.process(tokens, {})
        a = result.data.analyses[0]
        assert a.base == "בן"
        assert a.prefix_chain == []

    def test_punct_pos(self, analyzer):
        """Punctuation tokens get PUNCT POS."""
        tokens = [Token(0, ".", 0, 1), Token(1, "!!!", 2, 5)]
        result = analyzer.process(tokens, {})
        assert result.data.analyses[0].pos == "PUNCT"
        assert result.data.analyses[1].pos == "PUNCT"

    def test_number_pos(self, analyzer):
        """Numeric tokens get NUM POS."""
        tokens = [Token(0, "7.5", 0, 3), Token(1, "100", 4, 7)]
        result = analyzer.process(tokens, {})
        assert result.data.analyses[0].pos == "NUM"
        assert result.data.analyses[1].pos == "NUM"

    def test_latin_pos(self, analyzer):
        """Latin tokens get X POS."""
        tokens = [Token(0, "MPa", 0, 3)]
        result = analyzer.process(tokens, {})
        assert result.data.analyses[0].pos == "X"

    def test_adjective_detection(self, analyzer):
        """Adjective suffixes detected (nisba/relational)."""
        tokens = [
            Token(0, "טכנולוגית", 0, 9),   # -ית suffix
            Token(1, "ישראלי", 10, 16),     # -י suffix (not matched, too short pattern)
        ]
        result = analyzer.process(tokens, {})
        assert result.data.analyses[0].pos == "ADJ"

    def test_pronoun_pos(self, analyzer):
        """Pronouns get PRON POS."""
        tokens = [Token(0, "הוא", 0, 3), Token(1, "זה", 4, 6)]
        result = analyzer.process(tokens, {})
        assert result.data.analyses[0].pos == "PRON"
        assert result.data.analyses[1].pos == "PRON"

    def test_copula_pos(self, analyzer):
        """Copula/existential words get VERB POS."""
        tokens = [Token(0, "יש", 0, 2), Token(1, "אין", 3, 6)]
        result = analyzer.process(tokens, {})
        assert result.data.analyses[0].pos == "VERB"
        assert result.data.analyses[1].pos == "VERB"


class TestStripPrefixes:
    """Unit tests for _strip_prefixes helper."""

    def test_no_prefix(self):
        base, chain, det = _strip_prefixes("פלדה")
        assert base == "פלדה"
        assert chain == []
        assert det is False

    def test_he_prefix(self):
        base, chain, det = _strip_prefixes("הפלדה")
        assert base == "פלדה"
        assert chain == ["ה"]
        assert det is True

    def test_bet_prefix(self):
        base, chain, det = _strip_prefixes("בבניין")
        assert base == "בניין"
        assert chain == ["ב"]
        assert det is False

    def test_vav_bet_chain(self):
        base, chain, det = _strip_prefixes("ובפלדה")
        assert base == "פלדה"
        assert chain == ["ו", "ב"]
        assert det is False

    def test_lamed_he_chain(self):
        base, chain, det = _strip_prefixes("להפלדה")
        assert base == "פלדה"
        assert chain == ["ל", "ה"]
        assert det is True

    def test_short_word_preserved(self):
        """Words <=2 chars after strip are not stripped."""
        base, chain, det = _strip_prefixes("בן")
        assert base == "בן"
        assert chain == []

    def test_non_hebrew_unchanged(self):
        base, chain, det = _strip_prefixes("hello")
        assert base == "hello"
        assert chain == []


class TestDetectPos:
    """Unit tests for _detect_pos helper."""

    def test_punct(self):
        assert _detect_pos(".", ".") == "PUNCT"
        assert _detect_pos("...", "...") == "PUNCT"

    def test_num(self):
        assert _detect_pos("42", "42") == "NUM"
        assert _detect_pos("3.14", "3.14") == "NUM"

    def test_function_word(self):
        assert _detect_pos("של", "של") == "ADP"
        assert _detect_pos("או", "או") == "CCONJ"

    def test_non_hebrew(self):
        assert _detect_pos("test", "test") == "X"

    def test_default_noun(self):
        assert _detect_pos("פלדה", "פלדה") == "NOUN"
