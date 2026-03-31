"""Tests for kadima.engine.ner_extractor (M17)."""

import pytest
from kadima.engine.ner_extractor import (
    NERExtractor, Entity, NERResult,
    precision, recall, f1_score,
    _ner_rules, _deduplicate_spans,
)
from kadima.engine.base import ProcessorStatus


class TestMetadata:
    def test_name(self):
        assert NERExtractor().name == "ner"

    def test_module_id(self):
        assert NERExtractor().module_id == "M17"


class TestValidateInput:
    def test_valid(self):
        assert NERExtractor().validate_input("שלום") is True

    def test_empty(self):
        assert NERExtractor().validate_input("") is False

    def test_non_string(self):
        assert NERExtractor().validate_input(42) is False


class TestPrecision:
    def test_perfect(self):
        ents = [Entity("ישראל", "GPE", 0, 5)]
        assert precision(ents, ents) == 1.0

    def test_no_predictions(self):
        assert precision([], [Entity("ישראל", "GPE", 0, 5)]) == 0.0

    def test_false_positive(self):
        pred = [Entity("ישראל", "GPE", 0, 5), Entity("fake", "PER", 6, 10)]
        gold = [Entity("ישראל", "GPE", 0, 5)]
        assert precision(pred, gold) == 0.5

    def test_empty_both(self):
        assert precision([], []) == 1.0


class TestRecall:
    def test_perfect(self):
        ents = [Entity("ישראל", "GPE", 0, 5)]
        assert recall(ents, ents) == 1.0

    def test_missed_entity(self):
        pred = [Entity("ישראל", "GPE", 0, 5)]
        gold = [Entity("ישראל", "GPE", 0, 5), Entity("חיפה", "GPE", 6, 10)]
        assert recall(pred, gold) == 0.5

    def test_no_gold(self):
        assert recall([Entity("x", "Y", 0, 1)], []) == 0.0


class TestF1:
    def test_perfect(self):
        ents = [Entity("ישראל", "GPE", 0, 5)]
        assert f1_score(ents, ents) == 1.0

    def test_zero(self):
        pred = [Entity("fake", "PER", 0, 4)]
        gold = [Entity("ישראל", "GPE", 0, 5)]
        assert f1_score(pred, gold) == 0.0

    def test_partial(self):
        pred = [Entity("ישראל", "GPE", 0, 5), Entity("fake", "PER", 6, 10)]
        gold = [Entity("ישראל", "GPE", 0, 5), Entity("חיפה", "GPE", 11, 15)]
        score = f1_score(pred, gold)
        assert 0.0 < score < 1.0


class TestDeduplicateSpans:
    def test_no_overlap(self):
        ents = [
            Entity("a", "X", 0, 2),
            Entity("b", "Y", 5, 8),
        ]
        assert len(_deduplicate_spans(ents)) == 2

    def test_overlap_keeps_longest(self):
        ents = [
            Entity("תל אביב", "GPE", 0, 7),
            Entity("אביב", "GPE", 3, 7),
        ]
        result = _deduplicate_spans(ents)
        assert len(result) == 1
        assert result[0].text == "תל אביב"

    def test_empty(self):
        assert _deduplicate_spans([]) == []


class TestNERRules:
    def test_detect_location(self):
        ents = _ner_rules("אני גר בישראל")
        gpe = [e for e in ents if e.label == "GPE"]
        assert len(gpe) >= 1
        assert any(e.text == "ישראל" for e in gpe)

    def test_detect_org(self):
        ents = _ner_rules("חיילי צהל שמרו")
        orgs = [e for e in ents if e.label == "ORG"]
        assert any(e.text == "צהל" for e in orgs)

    def test_detect_date_pattern(self):
        ents = _ner_rules("הפגישה ב-15/03/2026")
        dates = [e for e in ents if e.label == "DATE"]
        assert len(dates) >= 1

    def test_no_entities_in_plain_text(self):
        ents = _ner_rules("פלדה חזקה משמשת בבניין")
        assert len(ents) == 0

    def test_multiple_locations(self):
        ents = _ner_rules("טיסה מירושלים לחיפה")
        gpe = [e for e in ents if e.label == "GPE"]
        texts = {e.text for e in gpe}
        assert "ירושלים" in texts
        assert "חיפה" in texts


class TestNERExtractorProcess:
    @pytest.fixture
    def n(self):
        return NERExtractor()

    def test_rules_backend(self, n):
        r = n.process("אני גר בישראל", {"backend": "rules"})
        assert r.status == ProcessorStatus.READY
        assert isinstance(r.data, NERResult)
        assert r.data.backend == "rules"
        assert r.data.count >= 1

    def test_heq_ner_fallback(self, n):
        """If transformers not available, falls back to rules."""
        r = n.process("אני גר בישראל", {"backend": "heq_ner"})
        assert r.status == ProcessorStatus.READY
        assert r.data.backend in ("heq_ner", "rules")

    def test_entities_have_required_fields(self, n):
        r = n.process("חיילי צהל בירושלים", {"backend": "rules"})
        for ent in r.data.entities:
            assert isinstance(ent.text, str)
            assert isinstance(ent.label, str)
            assert isinstance(ent.start, int)
            assert isinstance(ent.end, int)
            assert isinstance(ent.score, float)

    def test_processing_time(self, n):
        r = n.process("שלום", {"backend": "rules"})
        assert r.processing_time_ms >= 0


class TestNERBatch:
    def test_batch(self):
        n = NERExtractor()
        results = n.process_batch(
            ["אני בישראל", "צהל הודיע"],
            {"backend": "rules"},
        )
        assert len(results) == 2
        assert all(r.status == ProcessorStatus.READY for r in results)

    def test_empty_batch(self):
        n = NERExtractor()
        assert n.process_batch([], {"backend": "rules"}) == []
