# kadima/annotation/exporter.py
"""Export annotations to various formats (gold corpus, CoNLL-U, training JSON).

For LS-side export, use ls_client.py.export_annotations().
This module converts local DB annotation_results into output files.
"""

import csv
import json
import logging
from typing import List, Dict, Optional

from kadima.data.db import get_connection

logger = logging.getLogger(__name__)


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


def export_to_conllu(db_path: str, project_id: int, output_path: str) -> int:
    """Export NER annotations to CoNLL-U format. Stub."""
    raise NotImplementedError("CoNLL-U export not yet implemented")
