# kadima/annotation/ner_training.py
"""R-2.3: NER training pipeline — Label Studio annotations → spaCy training data.

Pipeline:
  Label Studio JSON annotations
        ↓ ls_annotations_to_spans()
  List of (text, spans) pairs
        ↓ spans_to_conllu()
  CoNLL-U format string
        ↓ spans_to_spacy_examples()
  List[spacy.training.Example]
        ↓ spacy.train config.cfg
  Fine-tuned NER model

Usage:
    from kadima.annotation.ner_training import ls_annotations_to_spans, spans_to_spacy_examples
    spans = ls_annotations_to_spans(ls_json)
    examples = spans_to_spacy_examples(spans)
    # → pass to spacy.train or nlp.update()

Label Studio NER annotation format (input):
    [
        {
            "id": 1,
            "data": {"text": "דוד בן גוריון חי בישראל"},
            "annotations": [{
                "result": [{
                    "type": "labels",
                    "value": {
                        "start": 0, "end": 16,
                        "text": "דוד בן גוריון",
                        "labels": ["PER"]
                    }
                }]
            }]
        }
    ]
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ── Data classes ─────────────────────────────────────────────────────────────


@dataclass
class NERSpan:
    """A single named entity span."""

    text: str
    label: str
    start: int   # char offset in source text
    end: int     # char offset in source text


@dataclass
class AnnotatedSentence:
    """A text with its NER span annotations."""

    text: str
    spans: List[NERSpan] = field(default_factory=list)
    task_id: Optional[int] = None


# ── Step 1: Label Studio JSON → AnnotatedSentence ────────────────────────────


def ls_annotations_to_spans(
    ls_tasks: List[Dict[str, Any]],
    label_field: str = "labels",
) -> List[AnnotatedSentence]:
    """Convert Label Studio NER export JSON to AnnotatedSentence list.

    Handles both single-annotator and multi-annotator formats.
    On conflicting annotations for the same task, the first annotation is used.

    Args:
        ls_tasks: List of task dicts from Label Studio export JSON.
        label_field: Name of the labeling field (default "labels").

    Returns:
        List of AnnotatedSentence with parsed spans.
    """
    sentences: List[AnnotatedSentence] = []

    for task in ls_tasks:
        task_id = task.get("id")
        text = task.get("data", {}).get("text", "")
        if not text:
            logger.debug("Task %s has no text — skipping", task_id)
            continue

        annotations = task.get("annotations", [])
        if not annotations:
            # Include text-only tasks for training (useful for negative examples)
            sentences.append(AnnotatedSentence(text=text, task_id=task_id))
            continue

        # Use first annotation (skip rejected/draft)
        ann = annotations[0]
        results = ann.get("result", [])

        spans: List[NERSpan] = []
        for item in results:
            if item.get("type") != "labels":
                continue
            value = item.get("value", {})
            labels = value.get(label_field, value.get("labels", []))
            if not labels:
                continue
            start = value.get("start", 0)
            end = value.get("end", 0)
            span_text = value.get("text", text[start:end])
            label = labels[0] if isinstance(labels, list) else labels

            # Validate offsets
            if start < 0 or end > len(text) or start >= end:
                logger.warning(
                    "Task %s: invalid span offsets [%d, %d) for text len %d — skipping",
                    task_id, start, end, len(text),
                )
                continue

            spans.append(NERSpan(text=span_text, label=label, start=start, end=end))

        sentences.append(AnnotatedSentence(text=text, spans=spans, task_id=task_id))

    logger.info(
        "Parsed %d annotated sentences (%d total spans)",
        len(sentences),
        sum(len(s.spans) for s in sentences),
    )
    return sentences


# ── Step 2: AnnotatedSentence → CoNLL-U ──────────────────────────────────────


def spans_to_conllu(sentences: List[AnnotatedSentence]) -> str:
    """Convert annotated sentences to CoNLL-U format string.

    Uses BIO (Begin-Inside-Outside) tagging scheme.
    Token boundaries are whitespace-split (suitable for Hebrew).

    Args:
        sentences: List of AnnotatedSentence.

    Returns:
        CoNLL-U formatted string.
    """
    lines: List[str] = []

    for sent in sentences:
        text = sent.text
        tokens = text.split()
        if not tokens:
            continue

        # Map char offsets to BIO tags
        tags = _assign_bio_tags(text, tokens, sent.spans)

        lines.append(f"# text = {text}")
        for i, (tok, tag) in enumerate(zip(tokens, tags), start=1):
            # CoNLL-U columns: ID FORM LEMMA UPOS XPOS FEATS HEAD DEPREL DEPS MISC
            lines.append(f"{i}\t{tok}\t_\t_\t_\t_\t_\t_\t_\tNE={tag}")
        lines.append("")  # blank line between sentences

    return "\n".join(lines)


def _assign_bio_tags(
    text: str,
    tokens: List[str],
    spans: List[NERSpan],
) -> List[str]:
    """Assign BIO NER tags to whitespace-tokenized text.

    Args:
        text: Original text.
        tokens: Whitespace-split tokens.
        spans: NER spans with char offsets.

    Returns:
        List of BIO tags, same length as tokens.
    """
    tags = ["O"] * len(tokens)

    # Build (token_start_char, token_end_char) for each token
    token_offsets: List[Tuple[int, int]] = []
    pos = 0
    for tok in tokens:
        start = text.find(tok, pos)
        if start == -1:
            start = pos
        end = start + len(tok)
        token_offsets.append((start, end))
        pos = end

    for span in spans:
        label = span.label
        in_span = False
        for i, (tok_s, tok_e) in enumerate(token_offsets):
            # Token overlaps with span
            if tok_s < span.end and tok_e > span.start:
                if not in_span:
                    tags[i] = f"B-{label}"
                    in_span = True
                else:
                    tags[i] = f"I-{label}"
            elif in_span:
                in_span = False

    return tags


# ── Step 3: AnnotatedSentence → spaCy Examples ───────────────────────────────


def spans_to_spacy_examples(
    sentences: List[AnnotatedSentence],
    nlp: Any = None,
) -> List[Any]:  # List[spacy.training.Example]
    """Convert annotated sentences to spaCy training Example objects.

    Args:
        sentences: List of AnnotatedSentence with NER spans.
        nlp: spaCy Language object. If None, creates spacy.blank("he").

    Returns:
        List of spacy.training.Example for use with nlp.update() or spacy train.
    """
    try:
        import spacy
        from spacy.tokens import Doc
        from spacy.training import Example
    except ImportError as e:
        raise ImportError(
            "spaCy is required for span conversion. "
            "Install with: pip install spacy"
        ) from e

    if nlp is None:
        nlp = spacy.blank("he")

    examples: List[Any] = []

    for sent in sentences:
        text = sent.text
        if not text.strip():
            continue

        # Build ents in spaCy format: List[(start, end, label)]
        ents = []
        for span in sent.spans:
            # Validate that the span text matches
            actual = text[span.start:span.end]
            if not actual:
                continue
            ents.append((span.start, span.end, span.label))

        # Sort and deduplicate overlapping ents (spaCy requires non-overlapping)
        ents = _deduplicate_ents(ents)

        doc = nlp.make_doc(text)
        try:
            reference = Example.from_dict(doc, {"entities": ents})
            examples.append(reference)
        except Exception as e:
            logger.warning("Could not create Example for task: %s — %s", sent.task_id, e)

    logger.info("Created %d spaCy training examples", len(examples))
    return examples


def _deduplicate_ents(
    ents: List[Tuple[int, int, str]],
) -> List[Tuple[int, int, str]]:
    """Remove overlapping entity spans, keeping the longest.

    Args:
        ents: List of (start, end, label) tuples.

    Returns:
        Non-overlapping list sorted by start offset.
    """
    if not ents:
        return []
    # Sort by start, then by length descending
    sorted_ents = sorted(ents, key=lambda e: (e[0], -(e[1] - e[0])))
    result = [sorted_ents[0]]
    for ent in sorted_ents[1:]:
        last = result[-1]
        if ent[0] >= last[1]:  # no overlap
            result.append(ent)
    return result


# ── Round-trip helper ─────────────────────────────────────────────────────────


def ls_to_spacy_examples(
    ls_tasks: List[Dict[str, Any]],
    nlp: Any = None,
) -> List[Any]:
    """Full pipeline: LS JSON → spaCy Examples.

    Convenience wrapper for ls_annotations_to_spans → spans_to_spacy_examples.

    Args:
        ls_tasks: Label Studio export JSON (list of tasks).
        nlp: Optional spaCy Language. Created as spacy.blank("he") if None.

    Returns:
        List of spacy.training.Example.
    """
    sentences = ls_annotations_to_spans(ls_tasks)
    return spans_to_spacy_examples(sentences, nlp)
