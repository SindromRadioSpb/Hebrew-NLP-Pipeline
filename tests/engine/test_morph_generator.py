"""Tests for kadima.engine.morph_generator (M21)."""

import pytest
from kadima.engine.morph_generator import (
    MorphGenerator, MorphForm, MorphGenResult,
    form_accuracy, _extract_root, _apply_pattern,
)
from kadima.engine.base import ProcessorStatus


class TestMetadata:
    def test_name(self):
        assert MorphGenerator().name == "morph_gen"

    def test_module_id(self):
        assert MorphGenerator().module_id == "M21"


class TestValidateInput:
    def test_valid_input(self):
        g = MorphGenerator()
        assert g.validate_input({"lemma": "כתב", "pos": "VERB"}) is True

    def test_missing_lemma(self):
        g = MorphGenerator()
        assert g.validate_input({"pos": "VERB"}) is False

    def test_missing_pos(self):
        g = MorphGenerator()
        assert g.validate_input({"lemma": "כתב"}) is False

    def test_non_dict(self):
        g = MorphGenerator()
        assert g.validate_input("כתב") is False
        assert g.validate_input(None) is False


class TestFormAccuracy:
    def test_perfect(self):
        assert form_accuracy(["a", "b", "c"], ["a", "b", "c"]) == 1.0

    def test_partial(self):
        assert form_accuracy(["a", "b"], ["a", "b", "c"]) == pytest.approx(2 / 3)

    def test_none_found(self):
        assert form_accuracy(["x", "y"], ["a", "b"]) == 0.0

    def test_empty_expected(self):
        assert form_accuracy([], []) == 1.0

    def test_empty_expected_nonempty_predicted(self):
        assert form_accuracy(["a"], []) == 0.0


class TestExtractRoot:
    def test_three_letter_root(self):
        root = _extract_root("כתב")
        assert root == ["כ", "ת", "ב"]

    def test_four_letter_word_takes_three(self):
        root = _extract_root("שלום")
        assert root == ["ש", "ל", "ו"]

    def test_two_letter_word(self):
        root = _extract_root("בן")
        assert root == ["ב", "ן"]

    def test_mixed_text_extracts_hebrew(self):
        root = _extract_root("כתב1")
        assert root == ["כ", "ת", "ב"]


class TestApplyPattern:
    def test_basic_pattern(self):
        result = _apply_pattern(["כ", "ת", "ב"], "{0}{1}{2}")
        assert result == "כתב"

    def test_prefix_pattern(self):
        result = _apply_pattern(["כ", "ת", "ב"], "ל{0}{1}ו{2}")
        assert result == "לכתוב"

    def test_suffix_pattern(self):
        result = _apply_pattern(["כ", "ת", "ב"], "{0}{1}{2}תי")
        assert result == "כתבתי"


class TestVerbGeneration:
    @pytest.fixture
    def g(self):
        return MorphGenerator()

    def test_paal_generates_forms(self, g):
        r = g.process({"lemma": "כתב", "pos": "VERB"}, {"binyan": "paal"})
        assert r.status == ProcessorStatus.READY
        assert r.data.count > 0
        forms_text = [f.form for f in r.data.forms]
        assert "כתב" in forms_text        # past 3ms
        assert "לכתוב" in forms_text       # infinitive

    def test_paal_past_1s(self, g):
        r = g.process({"lemma": "כתב", "pos": "VERB"}, {"binyan": "paal"})
        forms_text = [f.form for f in r.data.forms]
        assert "כתבתי" in forms_text

    def test_nifal(self, g):
        r = g.process({"lemma": "כתב", "pos": "VERB"}, {"binyan": "nifal"})
        assert r.status == ProcessorStatus.READY
        forms_text = [f.form for f in r.data.forms]
        assert "נכתב" in forms_text

    def test_hifil(self, g):
        r = g.process({"lemma": "כתב", "pos": "VERB"}, {"binyan": "hifil"})
        assert r.status == ProcessorStatus.READY
        forms_text = [f.form for f in r.data.forms]
        assert "הכתיב" in forms_text

    def test_hitpael(self, g):
        r = g.process({"lemma": "כתב", "pos": "VERB"}, {"binyan": "hitpael"})
        assert r.status == ProcessorStatus.READY
        forms_text = [f.form for f in r.data.forms]
        assert "התכתב" in forms_text

    def test_all_binyanim_produce_forms(self, g):
        for b in ("paal", "nifal", "piel", "pual", "hifil", "hufal", "hitpael"):
            r = g.process({"lemma": "כתב", "pos": "VERB"}, {"binyan": b})
            assert r.status == ProcessorStatus.READY
            assert r.data.count > 0, f"No forms for binyan {b}"

    def test_unknown_binyan(self, g):
        r = g.process({"lemma": "כתב", "pos": "VERB"}, {"binyan": "nonexistent"})
        assert r.status == ProcessorStatus.READY
        assert r.data.count == 0

    def test_short_root_fallback(self, g):
        r = g.process({"lemma": "בן", "pos": "VERB"}, {"binyan": "paal"})
        assert r.status == ProcessorStatus.READY
        assert r.data.count == 1  # single fallback form

    def test_form_features_populated(self, g):
        r = g.process({"lemma": "כתב", "pos": "VERB"}, {"binyan": "paal"})
        for f in r.data.forms:
            assert "binyan" in f.features
            assert f.features["binyan"] == "paal"
            assert "tense" in f.features


class TestNounGeneration:
    @pytest.fixture
    def g(self):
        return MorphGenerator()

    def test_masculine_noun(self, g):
        r = g.process({"lemma": "ספר", "pos": "NOUN"}, {"gender": "masculine"})
        assert r.status == ProcessorStatus.READY
        forms_text = [f.form for f in r.data.forms]
        assert "ספר" in forms_text       # singular
        assert "ספרים" in forms_text     # plural m
        assert "הספר" in forms_text      # definite

    def test_feminine_noun(self, g):
        r = g.process({"lemma": "ספר", "pos": "NOUN"}, {"gender": "feminine"})
        forms_text = [f.form for f in r.data.forms]
        assert "ספרות" in forms_text     # plural f

    def test_default_gender_masculine(self, g):
        r = g.process({"lemma": "ספר", "pos": "NOUN"}, {})
        forms_text = [f.form for f in r.data.forms]
        assert "ספרים" in forms_text     # masculine plural


class TestAdjGeneration:
    def test_adjective_forms(self):
        g = MorphGenerator()
        r = g.process({"lemma": "גדול", "pos": "ADJ"}, {})
        assert r.status == ProcessorStatus.READY
        forms_text = [f.form for f in r.data.forms]
        assert "גדול" in forms_text      # ms
        assert "גדולה" in forms_text     # fs
        assert "גדולים" in forms_text    # mp
        assert "גדולות" in forms_text    # fp
        assert r.data.count == 4


class TestProcessBatch:
    def test_batch(self):
        g = MorphGenerator()
        inputs = [
            {"lemma": "כתב", "pos": "VERB"},
            {"lemma": "ספר", "pos": "NOUN"},
        ]
        results = g.process_batch(inputs, {"binyan": "paal"})
        assert len(results) == 2
        assert all(r.status == ProcessorStatus.READY for r in results)

    def test_empty_batch(self):
        g = MorphGenerator()
        assert g.process_batch([], {}) == []
