"""Tests for R-2.3: NER training pipeline — Label Studio → spaCy."""

import pytest
from kadima.annotation.ner_training import (
    AnnotatedSentence,
    NERSpan,
    _assign_bio_tags,
    _deduplicate_ents,
    ls_annotations_to_spans,
    ls_to_spacy_examples,
    spans_to_conllu,
    spans_to_spacy_examples,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────

def _ls_task(task_id: int, text: str, spans: list) -> dict:
    """Build a Label Studio task dict."""
    results = [
        {
            "type": "labels",
            "value": {
                "start": s["start"],
                "end": s["end"],
                "text": text[s["start"]:s["end"]],
                "labels": [s["label"]],
            },
        }
        for s in spans
    ]
    return {
        "id": task_id,
        "data": {"text": text},
        "annotations": [{"result": results}],
    }


# ── ls_annotations_to_spans ───────────────────────────────────────────────────

class TestLSAnnotationsToSpans:
    def test_basic_task(self):
        tasks = [_ls_task(1, "דוד בן גוריון חי בישראל", [{"start": 0, "end": 13, "label": "PER"}])]
        sentences = ls_annotations_to_spans(tasks)
        assert len(sentences) == 1
        assert sentences[0].text == "דוד בן גוריון חי בישראל"
        assert len(sentences[0].spans) == 1
        assert sentences[0].spans[0].label == "PER"

    def test_multiple_spans(self):
        text = "ישראל היא בתל אביב"
        tasks = [_ls_task(1, text, [
            {"start": 0, "end": 6, "label": "GPE"},
            {"start": 10, "end": 18, "label": "GPE"},
        ])]
        sentences = ls_annotations_to_spans(tasks)
        assert len(sentences[0].spans) == 2

    def test_no_annotations(self):
        tasks = [{"id": 1, "data": {"text": "שלום עולם"}, "annotations": []}]
        sentences = ls_annotations_to_spans(tasks)
        assert len(sentences) == 1
        assert len(sentences[0].spans) == 0

    def test_empty_text_skipped(self):
        tasks = [{"id": 1, "data": {"text": ""}, "annotations": []}]
        sentences = ls_annotations_to_spans(tasks)
        assert len(sentences) == 0

    def test_invalid_offsets_skipped(self):
        text = "שלום"
        tasks = [_ls_task(1, text, [{"start": -1, "end": 100, "label": "PER"}])]
        sentences = ls_annotations_to_spans(tasks)
        assert len(sentences[0].spans) == 0

    def test_task_id_preserved(self):
        tasks = [_ls_task(42, "טקסט", [])]
        sentences = ls_annotations_to_spans(tasks)
        assert sentences[0].task_id == 42

    def test_multiple_tasks(self):
        tasks = [
            _ls_task(1, "ישראל מדינה", [{"start": 0, "end": 6, "label": "GPE"}]),
            _ls_task(2, "שלום עולם", []),
        ]
        sentences = ls_annotations_to_spans(tasks)
        assert len(sentences) == 2


# ── _assign_bio_tags ──────────────────────────────────────────────────────────

class TestAssignBIOTags:
    def test_single_token_span(self):
        text = "ישראל היא מדינה"
        tokens = text.split()
        spans = [NERSpan(text="ישראל", label="GPE", start=0, end=6)]
        tags = _assign_bio_tags(text, tokens, spans)
        assert tags[0] == "B-GPE"
        assert tags[1] == "O"
        assert tags[2] == "O"

    def test_multi_token_span(self):
        text = "דוד בן גוריון"
        tokens = text.split()
        spans = [NERSpan(text="דוד בן גוריון", label="PER", start=0, end=13)]
        tags = _assign_bio_tags(text, tokens, spans)
        assert tags[0] == "B-PER"
        assert tags[1] == "I-PER"
        assert tags[2] == "I-PER"

    def test_no_spans_all_outside(self):
        tokens = ["שלום", "עולם"]
        tags = _assign_bio_tags("שלום עולם", tokens, [])
        assert all(t == "O" for t in tags)

    def test_two_separate_spans(self):
        text = "ישראל ו ירדן"
        tokens = text.split()
        spans = [
            NERSpan(text="ישראל", label="GPE", start=0, end=6),
            NERSpan(text="ירדן", label="GPE", start=9, end=13),
        ]
        tags = _assign_bio_tags(text, tokens, spans)
        assert tags[0] == "B-GPE"
        assert tags[1] == "O"
        assert tags[2] == "B-GPE"


# ── spans_to_conllu ───────────────────────────────────────────────────────────

class TestSpansToCoNLLU:
    def test_basic_output(self):
        sentences = [
            AnnotatedSentence(
                text="ישראל מדינה",
                spans=[NERSpan(text="ישראל", label="GPE", start=0, end=6)],
            )
        ]
        conllu = spans_to_conllu(sentences)
        assert "# text = ישראל מדינה" in conllu
        assert "B-GPE" in conllu
        assert "O" in conllu

    def test_tab_separated_columns(self):
        sentences = [AnnotatedSentence(text="שלום עולם", spans=[])]
        conllu = spans_to_conllu(sentences)
        for line in conllu.split("\n"):
            if line and not line.startswith("#"):
                parts = line.split("\t")
                assert len(parts) == 10  # 10 CoNLL-U columns

    def test_multiple_sentences(self):
        sentences = [
            AnnotatedSentence(text="ישראל", spans=[]),
            AnnotatedSentence(text="ירדן", spans=[]),
        ]
        conllu = spans_to_conllu(sentences)
        # Two sentences → two text comment lines
        assert conllu.count("# text =") == 2

    def test_empty_sentences_skipped(self):
        sentences = [AnnotatedSentence(text="", spans=[])]
        conllu = spans_to_conllu(sentences)
        assert conllu.strip() == ""


# ── spans_to_spacy_examples ───────────────────────────────────────────────────

class TestSpansToSpacyExamples:
    def test_basic_conversion(self):
        sentences = [
            AnnotatedSentence(
                text="ישראל מדינה",
                spans=[NERSpan(text="ישראל", label="GPE", start=0, end=6)],
            )
        ]
        examples = spans_to_spacy_examples(sentences)
        assert len(examples) == 1

    def test_example_has_ents(self):
        import spacy
        # "ישראל" = 5 Hebrew chars (0-4), end=5; space at 5; "מדינה" starts at 6
        sentences = [
            AnnotatedSentence(
                text="ישראל מדינה",
                spans=[NERSpan(text="ישראל", label="GPE", start=0, end=5)],
            )
        ]
        examples = spans_to_spacy_examples(sentences, nlp=spacy.blank("he"))
        assert len(examples[0].reference.ents) == 1
        assert examples[0].reference.ents[0].label_ == "GPE"

    def test_empty_text_skipped(self):
        sentences = [AnnotatedSentence(text="", spans=[])]
        examples = spans_to_spacy_examples(sentences)
        assert len(examples) == 0

    def test_overlapping_spans_deduplicated(self):
        sentences = [
            AnnotatedSentence(
                text="דוד בן גוריון",
                spans=[
                    NERSpan(text="דוד בן גוריון", label="PER", start=0, end=13),
                    NERSpan(text="דוד", label="PER", start=0, end=3),  # overlapping
                ],
            )
        ]
        examples = spans_to_spacy_examples(sentences)
        # Should succeed (no ValueError from overlapping)
        assert len(examples) <= 1


# ── _deduplicate_ents ─────────────────────────────────────────────────────────

class TestDeduplicateEnts:
    def test_no_overlap(self):
        ents = [(0, 5, "GPE"), (10, 15, "PER")]
        result = _deduplicate_ents(ents)
        assert len(result) == 2

    def test_overlapping_keeps_longest(self):
        ents = [(0, 10, "PER"), (0, 3, "PER")]  # first is longer
        result = _deduplicate_ents(ents)
        assert len(result) == 1
        assert result[0] == (0, 10, "PER")

    def test_empty(self):
        assert _deduplicate_ents([]) == []

    def test_single(self):
        ents = [(5, 10, "ORG")]
        assert _deduplicate_ents(ents) == [(5, 10, "ORG")]


# ── ls_to_spacy_examples (round-trip) ────────────────────────────────────────

class TestRoundTrip:
    def test_full_pipeline(self):
        tasks = [
            _ls_task(1, "דוד בן גוריון ביקר בישראל", [
                {"start": 0, "end": 13, "label": "PER"},
                {"start": 19, "end": 25, "label": "GPE"},
            ])
        ]
        examples = ls_to_spacy_examples(tasks)
        assert len(examples) == 1
        assert len(examples[0].reference.ents) == 2

    def test_empty_input(self):
        examples = ls_to_spacy_examples([])
        assert examples == []
