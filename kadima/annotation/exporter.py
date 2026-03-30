# kadima/annotation/exporter.py
"""Export annotations to various formats (gold corpus, CoNLL-U, training JSON).

For LS-side export, use ls_client.py.export_annotations().
This module converts local DB annotation_results into output files.
"""

import csv
import json
import logging
from typing import List, Dict

from kadima.data.db import get_connection

logger = logging.getLogger(__name__)


# ── CSV Export ───────────────────────────────────────────────────────────────


def export_to_csv(db_path: str, project_id: int, output_path: str) -> int:
    """Export annotation_results to CSV.

    Returns number of rows written.
    """
    conn = get_connection(db_path)
    try:
        rows = conn.execute("""
            SELECT t.document_id, r.label, r.start_char, r.end_char,
                   r.text_span, r.annotator, r.created_at
            FROM annotation_results r
            JOIN annotation_tasks t ON r.task_id = t.id
            WHERE t.project_id = ?
            ORDER BY t.document_id, r.start_char
        """, (project_id,)).fetchall()
    finally:
        conn.close()

    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["document_id", "label", "start_char", "end_char", "text_span", "annotator", "created_at"])
        for row in rows:
            writer.writerow(row)

    logger.info("Exported %d annotations to %s", len(rows), output_path)
    return len(rows)


# ── CoNLL-U Export ───────────────────────────────────────────────────────────


def _assign_iob2_tags(
    tokens: List[Dict],
    spans: List[Dict],
) -> List[str]:
    """Assign IOB2 NER tags to tokens based on character spans.

    Args:
        tokens: List of {"text": str, "start": int, "end": int}.
        spans: List of {"label": str, "start_char": int, "end_char": int}.

    Returns:
        List of IOB2 tags (O, B-LABEL, I-LABEL) per token.
    """
    tags = ["O"] * len(tokens)

    for span in spans:
        label = span["label"]
        s_start = span["start_char"]
        s_end = span["end_char"]

        first = True
        for i, tok in enumerate(tokens):
            tok_start = tok["start"]
            tok_end = tok["end"]

            # Token overlaps with span
            if tok_end > s_start and tok_start < s_end:
                if first:
                    tags[i] = f"B-{label}"
                    first = False
                else:
                    tags[i] = f"I-{label}"

    return tags


def _tokenize_for_conllu(text: str) -> List[Dict]:
    """Simple whitespace tokenizer for CoNLL-U export.

    Returns list of {"text": str, "start": int, "end": int}.
    """
    tokens = []
    pos = 0
    for part in text.split():
        start = text.index(part, pos)
        end = start + len(part)
        tokens.append({"text": part, "start": start, "end": end})
        pos = end
    return tokens


def export_to_conllu(db_path: str, project_id: int, output_path: str) -> int:
    """Export NER annotations to CoNLL-U format.

    Format per token (10 tab-separated columns):
        ID FORM LEMMA UPOS XPOS FEATS HEAD DEPREL DEPS MISC

    NER tags are stored in MISC column as `NER=B-PER`, `NER=I-LOC`, etc.

    Args:
        db_path: Path to SQLite database.
        project_id: Label Studio project ID.
        output_path: Output file path.

    Returns:
        Number of sentences written.
    """
    conn = get_connection(db_path)

    try:
        # Get all annotated tasks for this project
        tasks = conn.execute("""
            SELECT t.id, t.document_id, t.data
            FROM annotation_tasks t
            WHERE t.project_id = ?
            ORDER BY t.document_id
        """, (project_id,)).fetchall()

        if not tasks:
            logger.warning("No tasks found for project %d", project_id)
            return 0

        sentence_count = 0
        with open(output_path, "w", encoding="utf-8") as f:
            for task_row in tasks:
                task_id = task_row["id"]
                doc_id = task_row["document_id"]
                task_data = json.loads(task_row["data"])
                text = task_data.get("text", "")

                if not text.strip():
                    continue

                # Get annotations for this task
                annotations = conn.execute("""
                    SELECT label, start_char, end_char, text_span
                    FROM annotation_results
                    WHERE task_id = ?
                    ORDER BY start_char
                """, (task_id,)).fetchall()

                spans = [
                    {"label": a["label"], "start_char": a["start_char"], "end_char": a["end_char"]}
                    for a in annotations
                ]

                # Tokenize and assign IOB2 tags
                tokens = _tokenize_for_conllu(text)
                if not tokens:
                    continue

                ner_tags = _assign_iob2_tags(tokens, spans)

                # Write CoNLL-U sentence
                f.write(f"# sent_id = {doc_id}-{task_id}\n")
                f.write(f"# text = {text}\n")

                for i, tok in enumerate(tokens):
                    # CoNLL-U columns:
                    # ID FORM LEMMA UPOS XPOS FEATS HEAD DEPREL DEPS MISC
                    col_id = str(i + 1)
                    col_form = tok["text"]
                    col_lemma = tok["text"]  # placeholder — real lemmatization needs M3
                    col_upos = "_"  # placeholder — needs morph analysis
                    col_xpos = "_"
                    col_feats = "_"
                    col_head = "_"
                    col_deprel = "_"
                    col_deps = "_"
                    col_misc = f"NER={ner_tags[i]}" if ner_tags[i] != "O" else "_"

                    f.write(f"{col_id}\t{col_form}\t{col_lemma}\t{col_upos}\t{col_xpos}\t{col_feats}\t{col_head}\t{col_deprel}\t{col_deps}\t{col_misc}\n")

                f.write("\n")
                sentence_count += 1

        logger.info("Exported %d sentences to CoNLL-U: %s", sentence_count, output_path)
        return sentence_count

    finally:
        conn.close()


# ── Training JSON Export ─────────────────────────────────────────────────────


def export_to_training_json(db_path: str, project_id: int, output_path: str) -> int:
    """Export annotations to training JSON (spacy-style).

    Format:
    [
      {
        "text": "...",
        "entities": [{"start": 0, "end": 5, "label": "TERM"}, ...]
      },
      ...
    ]

    Returns number of examples written.
    """
    conn = get_connection(db_path)
    try:
        tasks = conn.execute("""
            SELECT t.id, t.data
            FROM annotation_tasks t
            WHERE t.project_id = ?
            ORDER BY t.id
        """, (project_id,)).fetchall()

        examples = []
        for task_row in tasks:
            task_id = task_row["id"]
            task_data = json.loads(task_row["data"])
            text = task_data.get("text", "")

            if not text.strip():
                continue

            annotations = conn.execute("""
                SELECT label, start_char, end_char
                FROM annotation_results
                WHERE task_id = ?
                ORDER BY start_char
            """, (task_id,)).fetchall()

            entities = [
                {"start": a["start_char"], "end": a["end_char"], "label": a["label"]}
                for a in annotations
            ]

            if entities:
                examples.append({"text": text, "entities": entities})

    finally:
        conn.close()

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(examples, f, ensure_ascii=False, indent=2)

    logger.info("Exported %d training examples to %s", len(examples), output_path)
    return len(examples)
