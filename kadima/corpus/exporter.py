# kadima/corpus/exporter.py
"""M14: Export CSV, JSON, TBX, TMX, CoNLL-U.

Example:
    >>> from kadima.corpus.exporter import export_csv, export_json
    >>> terms = [{"surface": "חוזק מתיחה", "freq": 8, "rank": 1}]
    >>> csv_str = export_csv(terms)
    >>> "חוזק מתיחה" in csv_str
    True
    >>> json_str = export_json(terms)
    >>> import json; json.loads(json_str)["count"]
    1
"""

import csv
import json
import io
import logging
from typing import List, Dict, Any
from xml.etree import ElementTree as ET

logger = logging.getLogger(__name__)


def export_csv(terms: List[Dict[str, Any]]) -> str:
    """Экспорт терминов в CSV."""
    if not terms:
        logger.warning("No terms to export as CSV")
        return ""
    output = io.StringIO()
    fieldnames = terms[0].keys()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(terms)
    logger.info("Exported %d terms to CSV", len(terms))
    return output.getvalue()


def export_json(terms: List[Dict[str, Any]], indent: int = 2) -> str:
    """Экспорт терминов в JSON."""
    logger.info("Exported %d terms to JSON", len(terms))
    return json.dumps({"terms": terms, "count": len(terms)}, ensure_ascii=False, indent=indent)


def export_tbx(terms: List[Dict[str, Any]]) -> str:
    """Экспорт терминов в TBX (TermBase eXchange)."""
    try:
        root = ET.Element("tbx", type="TBX-Basic", style="dca")
        body = ET.SubElement(root, "body")
        termlist = ET.SubElement(body, "termEntry")

        for term in terms:
            entry = ET.SubElement(termlist, "termEntry")
            lang_set = ET.SubElement(entry, "langSet", xml="he")
            tig = ET.SubElement(lang_set, "tig")

            term_elem = ET.SubElement(tig, "term")
            term_elem.text = term.get("surface", "")

            if term.get("canonical"):
                note = ET.SubElement(tig, "note", type="canonical")
                note.text = term["canonical"]

            if term.get("kind"):
                note_kind = ET.SubElement(tig, "note", type="termType")
                note_kind.text = term["kind"]

        result = ET.tostring(root, encoding="unicode", xml_declaration=True)
        logger.info("Exported %d terms to TBX", len(terms))
        return result
    except Exception:
        logger.error("Failed to export TBX", exc_info=True)
        return ""


def export_tmx(terms: List[Dict[str, Any]]) -> str:
    """Экспорт терминов в TMX (Translation Memory eXchange)."""
    try:
        root = ET.Element("tmx", version="1.4")
        header = ET.SubElement(root, "header", creationtool="KADIMA", creationtoolversion="1.0",
                               datatype="plaintext", segtype="sentence", adminlang="he")
        body = ET.SubElement(root, "body")

        for term in terms:
            tu = ET.SubElement(body, "tuv", xml="he")
            seg = ET.SubElement(tu, "seg")
            seg.text = term.get("surface", "")

        result = ET.tostring(root, encoding="unicode", xml_declaration=True)
        logger.info("Exported %d terms to TMX", len(terms))
        return result
    except Exception:
        logger.error("Failed to export TMX", exc_info=True)
        return ""


def export_conllu(sentences: List[List[Dict[str, Any]]]) -> str:
    """Экспорт в CoNLL-U формат."""
    try:
        lines = []
        for sent_idx, sentence in enumerate(sentences):
            lines.append(f"# sent_id = {sent_idx + 1}")
            for token_idx, token in enumerate(sentence):
                cols = [
                    str(token_idx + 1),
                    token.get("surface", "_"),
                    token.get("lemma", "_"),
                    token.get("pos", "_"),
                    token.get("xpos", "_"),
                    token.get("feats", "_"),
                    token.get("head", "_"),
                    token.get("deprel", "_"),
                    token.get("deps", "_"),
                    token.get("misc", "_"),
                ]
                lines.append("\t".join(cols))
            lines.append("")
        result = "\n".join(lines)
        logger.info("Exported %d sentences to CoNLL-U", len(sentences))
        return result
    except Exception:
        logger.error("Failed to export CoNLL-U", exc_info=True)
        return ""


EXPORT_FORMATS = {
    "csv": export_csv,
    "json": export_json,
    "tbx": export_tbx,
    "tmx": export_tmx,
    "conllu": export_conllu,
}
