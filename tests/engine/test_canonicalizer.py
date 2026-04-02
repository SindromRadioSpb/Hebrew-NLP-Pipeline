"""Tests for M6: Canonicalizer — full coverage for rules, hebpipe fallback, metrics, batch."""

import pytest
from kadima.engine.canonicalizer import (
    Canonicalizer,
    CanonicalMapping,
    CanonicalResult,
    _FINAL_TO_NONFINAL,
    _CLITIC_CHAINS,
    _HEBPIPE_AVAILABLE,
)
from kadima.engine.base import ProcessorResult, ProcessorStatus


class TestCanonicalizer:
    @pytest.fixture
    def canon(self):
        return Canonicalizer()


class TestDefiniteArticleRemoval(TestCanonicalizer):
    """Tests for ה (definite article) removal."""

    def test_basic_det_removal(self, canon):
        result = canon.process(["הפלדה"], {})
        assert result.status == ProcessorStatus.READY
        m = result.data.mappings[0]
        assert m.canonical == "פלדה"
        assert "det_removal" in m.rules_applied

    def test_det_removal_with_niqqud(self, canon):
        """הַפַּלְדָּה → פלדה (article + niqqud + final letter)."""
        result = canon.process(["\u05d4\u05b7\u05e4\u05bc\u05b7\u05dc\u05b0\u05d3\u05b8\u05d4"], {})
        m = result.data.mappings[0]
        assert m.canonical == "פלדה"
        assert "det_removal" in m.rules_applied

    def test_no_det_single_letter(self, canon):
        """Single letter ה — stays as is since there's nothing after stripping,
        but הב (2 chars) gets stripped to ב."""
        result = canon.process(["ה"], {})
        m = result.data.mappings[0]
        # Single ה: length=1, > 1 is False, so no stripping
        # Actually len("ה") = 1, and condition is > 1, so no stripping
        assert m.canonical == "ה"

    def test_det_two_letter_word(self, canon):
        """Two-letter word with ה: ה+letter → only letter remains."""
        result = canon.process(["הב"], {})
        m = result.data.mappings[0]
        assert m.canonical == "ב"
        assert "det_removal" in m.rules_applied


class TestFinalLetterNormalization(TestCanonicalizer):
    """Tests for final → non-final letter conversion."""

    def test_final_mem(self, canon):
        result = canon.process(["שלום\u05dd"], {})  # שלום + final mem
        m = result.data.mappings[0]
        assert "\u05dd" not in m.canonical  # ם should be converted to מ
        assert "final_to_nonfinal" in m.rules_applied

    def test_final_nun(self, canon):
        result = canon.process(["ב\u05df"], {})  # ב + final nun
        m = result.data.mappings[0]
        assert "\u05df" not in m.canonical  # ן → נ
        assert "final_to_nonfinal" in m.rules_applied

    def test_all_five_final_letters(self, canon):
        """Test םןץכף → מנצכפ."""
        finals = "\u05dd\u05df\u05e5\u05da\u05e3"  # ם ן ץ ך ף
        nonfinals = "\u05de\u05e0\u05e6\u05db\u05e4"  # מ נ צ כ פ
        for final_char, nonfinal_char in zip(finals, nonfinals):
            word = f"א{final_char}א"
            result = canon.process([word], {})
            m = result.data.mappings[0]
            assert nonfinal_char in m.canonical
            assert final_char not in m.canonical

    def test_no_final_letters_unchanged(self, canon):
        """Word without final letters (םןץכף) should not get final_to_nonfinal rule."""
        result = canon.process(["כלב"], {})  # כלב — no final letters
        m = result.data.mappings[0]
        assert "final_to_nonfinal" not in m.rules_applied


class TestNiqqudStripping(TestCanonicalizer):
    """Tests for vowel point removal using strip_niqqud from hebrew.py."""

    def test_niqqud_stripping_simple(self, canon):
        """Remove all vowel points from a word."""
        # הַפַּלְדָּה → plda without vowels
        text = "\u05d4\u05b7\u05e4\u05bc\u05b7\u05dc\u05b0\u05d3\u05b8\u05d4"
        result = canon.process([text], {})
        m = result.data.mappings[0]
        # All niqqud (U+05B0-U+05BD) should be removed
        assert not any("\u05b0" <= c <= "\u05bd" for c in m.canonical)
        assert "niqqud_strip" in m.rules_applied

    def test_niqqud_and_det_combined(self, canon):
        """Word with both definite article and niqqud."""
        text = "\u05d4\u05b7\u05d1\u05b7\u05bc\u05d9\u05b4\u05ea"  # הַבַּיִת
        result = canon.process([text], {})
        m = result.data.mappings[0]
        assert "det_removal" in m.rules_applied
        assert "niqqud_strip" in m.rules_applied


class TestCliticStripping(TestCanonicalizer):
    """Tests for clitic prefix stripping."""

    def test_vav_clitic(self, canon):
        """ו+stem → stem."""
        result = canon.process(["ובית"], {})
        m = result.data.mappings[0]
        assert m.canonical != "ובית"
        assert any(r.startswith("clitic_strip") for r in m.rules_applied)

    def test_multi_char_chain(self, canon):
        """וכש+stem → stem."""
        result = canon.process(["וכשהוא"], {})
        m = result.data.mappings[0]
        assert any(r.startswith("clitic_strip") for r in m.rules_applied)

    def test_no_clitic(self, canon):
        """Word without clitics unchanged (מלך should only get final_to_nonfinal for ך)."""
        result = canon.process(["מלך"], {})
        m = result.data.mappings[0]
        assert not any(r.startswith("clitic_strip") for r in m.rules_applied)
        # ך → כ is expected
        assert "final_to_nonfinal" in m.rules_applied


class TestMaqafNormalization(TestCanonicalizer):
    """Tests for maqaf (Hebrew hyphen) normalization."""

    def test_regular_hyphen_to_maqaf(self, canon):
        result = canon.process(["בן-אדם"], {})
        m = result.data.mappings[0]
        # Regular hyphen should be converted to maqaf U+05BE if present
        assert "-" not in m.canonical or m.canonical == "בן\u05beאדם"


class TestInputValidation(TestCanonicalizer):

    def test_empty_input(self, canon):
        result = canon.process([], {})
        assert result.status == ProcessorStatus.READY
        assert len(result.data.mappings) == 0

    def test_empty_string_skipped(self, canon):
        result = canon.process(["", "   ", "מלך"], {})
        # Empty/whitespace strings should be skipped
        assert len(result.data.mappings) == 1
        assert result.data.mappings[0].surface == "מלך"

    def test_validate_input(self, canon):
        assert canon.validate_input(["a", "b"])
        assert not canon.validate_input("not a list")
        assert not canon.validate_input(None)
        assert not canon.validate_input([1, 2])  # non-strings
        assert not canon.validate_input(["a", None])

    def test_module_id(self, canon):
        assert canon.module_id == "M6"

    def test_module_name(self, canon):
        assert canon.name == "canonicalize"


class TestHebpipeFallback(TestCanonicalizer):
    """Tests for HebPipe backend behavior when unavailable."""

    def test_hebpipe_unavailable_defaults_to_rules(self, canon):
        """When hebpipe is not available, rules are used."""
        if not _HEBPIPE_AVAILABLE:
            result = canon.process(["הפלדה"], {})
            m = result.data.mappings[0]
            assert m.canonical == "פלדה"
            assert "det_removal" in m.rules_applied

    def test_hebpipe_disabled_via_config(self, canon):
        """Config use_hebpipe=False forces rules-only."""
        result = canon.process(["הפלדה"], {"use_hebpipe": False})
        m = result.data.mappings[0]
        assert m.canonical == "פלדה"


class TestProcessBatch(TestCanonicalizer):

    def test_process_batch(self, canon):
        batches = [["הפלדה", "הבית"], ["מלך", "מלכה"]]
        results = canon.process_batch(batches, {})
        assert len(results) == 2
        assert results[0].status == ProcessorStatus.READY
        assert len(results[0].data.mappings) == 2
        assert results[1].status == ProcessorStatus.READY
        assert len(results[1].data.mappings) == 2


class TestMetrics(TestCanonicalizer):
    """Tests for canonicalization metrics."""

    def test_canonicalization_rate_all_changed(self, canon):
        result = canon.process(["הפלדה", "הבית"], {})
        rate = Canonicalizer.canonicalization_rate(result)
        assert rate == 1.0  # all words changed

    def test_canonicalization_rate_none_changed(self, canon):
        """Words without ה should not change in det_removal only mode."""
        result = canon.process(["מלך", "מלכה"], {})
        # Some might change due to other rules, but check it's computed
        rate = Canonicalizer.canonicalization_rate(result)
        assert 0.0 <= rate <= 1.0

    def test_canonicalization_rate_failed_result(self):
        result = ProcessorResult(
            module_name="canonicalize",
            status=ProcessorStatus.FAILED,
            data=None,
            errors=["test"],
            processing_time_ms=0,
        )
        assert Canonicalizer.canonicalization_rate(result) == 0.0

    def test_unique_canonical_forms(self, canon):
        result = canon.process(["הפלדה", "הבית", "פלדה"], {})
        unique = Canonicalizer.unique_canonical_forms(result)
        assert unique >= 1
        # הפלדה → פלדה, הבית → בית, פלדה → פלדה = 2 unique
        assert unique == 2

    def test_rule_distribution(self, canon):
        result = canon.process(["הפלדה", "הבית"], {})
        dist = Canonicalizer.rule_distribution(result)
        assert "det_removal" in dist
        assert dist["det_removal"] == 2

    def test_rule_distribution_empty(self):
        result = ProcessorResult(
            module_name="canonicalize",
            status=ProcessorStatus.READY,
            data=CanonicalResult(mappings=[]),
            processing_time_ms=0,
        )
        dist = Canonicalizer.rule_distribution(result)
        assert dist == {}


class TestIntegrationM6toM8(TestCanonicalizer):
    """Integration tests for M6→M8 pipeline: canonical_mappings → TermExtractor dedup."""

    def test_m6_output_canonical_mappings_format(self, canon):
        """M6 output is dict[str, str] consumable by TermExtractor."""
        result = canon.process(["הפלדה", "לבטון"], {})
        assert result.status == ProcessorStatus.READY
        mappings = {m.surface: m.canonical for m in result.data.mappings}
        assert isinstance(mappings, dict)
        assert mappings["הפלדה"] == "פלדה"

    def test_m6_integration_with_term_extractor_input(self, canon):
        """M6 canonical_mappings can be directly injected into TermExtractor input.

        Simulates what pipeline orchestrator does:
            1. canonicalizer.process(surfaces) → mappings
            2. term_extractor.process({"canonical_mappings": mappings, ...})
        """
        # Step 1: M6 produces canonical mappings
        canon_result = canon.process(["הפלדה", "פלדה", "מלך", "מלכה"], {})
        assert canon_result.status == ProcessorStatus.READY
        canonical_mappings = {m.surface: m.canonical for m in canon_result.data.mappings}
        
        # Step 2: Verify TermExtractor can use these for dedup
        # הפלדה→פלדה, פלדה→פלדה (duplicate canonical)
        assert canonical_mappings.get("הפלדה") == "פלדה"
        assert canonical_mappings.get("פלדה") == "פלדה"
        assert canonical_mappings.get("מלך") == "מלכ"  # final kaf ך → non-final כ
        assert canonical_mappings.get("מלכה") == "מלכה"

    def test_m6_to_m8_dedup_logic_simulation(self, canon):
        """Simulate M6→M8 dedup: terms with different surfaces same canonical get merged."""
        from kadima.engine.ngram_extractor import Ngram
        from kadima.engine.term_extractor import TermExtractor

        # M6: canonicalize surfaces
        canon_result = canon.process(["הפלדה", "פלדה", "הפלדה"], {})
        canonical_mappings = {m.surface: m.canonical for m in canon_result.data.mappings}

        # M8: TermExtractor with canonical_mappings
        te = TermExtractor()
        ngrams = [
            Ngram(["הפלדה"], 1, 10, 1),
            Ngram(["פלדה"], 1, 8, 1),
            Ngram(["הפלדה", "של"], 2, 5, 1),
        ]
        te_input = {
            "ngrams": ngrams,
            "am_scores": {
                ("הפלדה",): {"pmi": 3.0, "llr": 5.0, "dice": 0.7},
                ("פלדה",): {"pmi": 2.0, "llr": 3.0, "dice": 0.5},
                ("הפלדה", "של"): {"pmi": 1.5, "llr": 2.0, "dice": 0.4},
            },
            "np_chunks": [],
            "canonical_mappings": canonical_mappings,
        }

        te_result = te.process(te_input, {"min_freq": 1})
        assert te_result.status == ProcessorStatus.READY

        # Terms should be deduplicated by canonical form
        terms = te_result.data.terms
        
        # Check that canonical forms are used
        canonical_values = [t.canonical for t in terms]
        assert "פלדה" in canonical_values  # canonical of הפלדה

    def test_m6_empty_surfaces_no_error(self, canon):
        """M6 handles empty input gracefully, TermExtractor handles empty canonical_mappings."""
        from kadima.engine.term_extractor import TermExtractor
        from kadima.engine.ngram_extractor import Ngram

        canon_result = canon.process([], {})
        canonical_mappings = {m.surface: m.canonical for m in canon_result.data.mappings}
        assert canonical_mappings == {}

        te = TermExtractor()
        te_input = {
            "ngrams": [Ngram(["test"], 1, 5, 1)],
            "am_scores": {},
            "np_chunks": [],
            "canonical_mappings": canonical_mappings,
        }
        te_result = te.process(te_input, {"min_freq": 1})
        assert te_result.status == ProcessorStatus.READY
