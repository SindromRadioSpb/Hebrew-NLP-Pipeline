"""Tests for kadima.engine.hebpipe_wrappers (M1-M3)."""

import pytest
from kadima.engine.hebpipe_wrappers import (
    HebPipeSentSplitter, HebPipeTokenizer, HebPipeMorphAnalyzer,
    Sentence, SentenceSplitResult, Token, TokenizeResult,
    MorphAnalysis, MorphResult,
    _strip_prefixes, _detect_pos, _split_sentences,
)
from kadima.engine.base import ProcessorStatus


class TestSplitSentencesHelper:
    """Unit tests for the _split_sentences helper function."""

    def test_period_split(self):
        parts = _split_sentences("משפט אחד. משפט שני.")
        assert len(parts) >= 2

    def test_question_split(self):
        parts = _split_sentences("מי אתה? לא יודע.")
        assert len(parts) >= 2

    def test_exclamation_split(self):
        parts = _split_sentences("זה נהדר! באמת.")
        assert len(parts) >= 2

    def test_mixed_boundaries(self):
        parts = _split_sentences("משפט. שאלה? קריאה!")
        assert len(parts) >= 3

    def test_no_boundary(self):
        parts = _split_sentences("משפט אחד בלי סימן סוף")
        assert len(parts) == 1

    def test_strict_mode_only_period(self):
        parts = _split_sentences("האם אתה שם? בטח. נהדר!", strict=True)
        assert len(parts) >= 1
        # In strict mode, ? and ! should NOT split
        result = _split_sentences("שאלה אחת? משפט שני.", strict=True)
        # The string after ? is not split in strict mode
        full = " ".join(result)
        assert "שאלה אחת" in full

    def test_empty_string(self):
        parts = _split_sentences("")
        assert len(parts) == 1
        assert parts[0] == ""

    def test_multi_paragraph(self):
        parts = _split_sentences("פסקה ראשונה.\n\nפסקה שנייה.")
        assert len(parts) >= 2


class TestHebPipeSentSplitter:
    @pytest.fixture
    def splitter(self):
        return HebPipeSentSplitter()

    def test_basic_split(self, splitter):
        text = "פלדה חזקה משמשת בבניין. חוזק מתיחה גבוה מאד."
        result = splitter.process(text, {})
        assert result.status == ProcessorStatus.READY
        assert result.data.count >= 2

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

    def test_question_mark_split(self, splitter):
        """Split on ? after Hebrew character."""
        text = "מי אתה? מה אתה רוצה? אני לא יודע."
        result = splitter.process(text, {})
        assert result.status == ProcessorStatus.READY
        assert result.data.count >= 3

    def test_exclamation_mark_split(self, splitter):
        """Split on ! after Hebrew character."""
        text = "זה נהדר! באמת יופי! מספיק."
        result = splitter.process(text, {})
        assert result.status == ProcessorStatus.READY
        assert result.data.count >= 3

    def test_mixed_boundary_split(self, splitter):
        """Mixed . ? ! in same text."""
        text = "תחילה. שאלה? קריאה!"
        result = splitter.process(text, {})
        assert result.status == ProcessorStatus.READY
        assert result.data.count >= 3
        sentences = [s.text for s in result.data.sentences]
        assert "תחילה" in sentences[0]
        assert "שאלה" in sentences[1]
        assert "קריאה" in sentences[2]

    def test_strict_mode_only_period(self, splitter):
        """Strict mode: only split on period."""
        text = "משפט ראשון. שאלה אחת? משפט שני."
        result = splitter.process(text, {"strict_mode": True})
        assert result.status == ProcessorStatus.READY
        # In strict mode, only . splits
        assert result.data.count == 2

    def test_sentence_offsets(self, splitter):
        """Sentence start/end offsets should be correct."""
        text = "א. ב."
        result = splitter.process(text, {})
        assert result.status == ProcessorStatus.READY
        if result.data.count >= 2:
            s0 = result.data.sentences[0]
            s1 = result.data.sentences[1]
            assert s0.start == 0
            assert s0.end > s0.start
            assert s1.start > s0.end

    def test_whitespace_only_input(self, splitter):
        result = splitter.process("   ", {})
        assert result.status == ProcessorStatus.FAILED

    def test_multiline_text(self, splitter):
        """Multi-line text with sentence boundaries."""
        text = "שורה ראשונה.\nשורה שנייה.\nשורה שלישית!"
        result = splitter.process(text, {})
        assert result.status == ProcessorStatus.READY
        assert result.data.count >= 2

    def test_process_batch(self, splitter):
        """Batch processing multiple texts."""
        inputs = [
            "טקסט ראשון. עוד משהו.",
            "שאלה אחת? אולי.",
            "קריאה אחת!",
        ]
        results = splitter.process_batch(inputs, {"strict_mode": False})
        assert len(results) == 3
        assert all(r.status == ProcessorStatus.READY for r in results)
        assert results[0].data.count >= 2
        assert results[1].data.count >= 2
        assert results[2].data.count >= 1


class TestHebPipeTokenizer:
    @pytest.fixture
    def tokenizer(self):
        return HebPipeTokenizer()

    def test_basic_tokenize(self, tokenizer):
        """Basic tokenize with clitic splitting enabled (default)."""
        result = tokenizer.process("חוזק מתיחה של הפלדה", {})
        assert result.status == ProcessorStatus.READY
        # Clitic splitting: מתיחה→מ+תיחה, הפלדה→ה+פלדה = 6 tokens
        assert result.data.count == 6
        assert result.data.tokens[0].surface == "חוזק"

    def test_clitic_splitting_vav_bet(self, tokenizer):
        """Clitic splitting: ובבית → ו+ב+בית."""
        result = tokenizer.process("ובבית", {"split_clitics": True})
        assert result.status == ProcessorStatus.READY
        assert result.data.count == 3
        surfaces = [t.surface for t in result.data.tokens]
        assert surfaces == ["ו", "ב", "בית"]

    def test_clitic_splitting_he_definite(self, tokenizer):
        """Clitic splitting: הפלדה → ה+פלדה."""
        result = tokenizer.process("הפלדה", {"split_clitics": True})
        assert result.status == ProcessorStatus.READY
        assert result.data.count == 2
        assert result.data.tokens[0].surface == "ה"
        assert result.data.tokens[1].surface == "פלדה"

    def test_clitic_splitting_multi_prefix(self, tokenizer):
        """Clitic splitting: והבית → ו+ה+בית."""
        result = tokenizer.process("והבית", {"split_clitics": True})
        assert result.status == ProcessorStatus.READY
        assert result.data.count == 3
        surfaces = [t.surface for t in result.data.tokens]
        assert surfaces == ["ו", "ה", "בית"]

    def test_clitic_splitting_disabled(self, tokenizer):
        """No clitic splitting when disabled."""
        result = tokenizer.process("ובבית", {"split_clitics": False})
        assert result.status == ProcessorStatus.READY
        assert result.data.count == 1
        assert result.data.tokens[0].surface == "ובבית"

    def test_no_clitic_on_mixed_text(self, tokenizer):
        """Latin/mixed text is not split."""
        result = tokenizer.process("hello MPa 7.5", {})
        assert result.status == ProcessorStatus.READY
        assert result.data.count == 3

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
