# kadima/corpus/exporter.py
"""M14: Export CSV, JSON, TBX, TMX, CoNLL-U."""

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
        return ""
    output = io.StringIO()
    fieldnames = terms[0].keys()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(terms)
    return output.getvalue()


def export_json(terms: List[Dict[str, Any]], indent: int = 2) -> str:
    """Экспорт терминов в JSON."""
    return json.dumps({"terms": terms, "count": len(terms)}, ensure_ascii=False, indent=indent)


def export_tbx(terms: List[Dict[str, Any]]) -> str:
    """Экспорт терминов в TBX (TermBase eXchange)."""
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

    return ET.tostring(root, encoding="unicode", xml_declaration=True)


def export_tmx(terms: List[Dict[str, Any]]) -> str:
    """Экспорт терминов в TMX (Translation Memory eXchange)."""
    root = ET.Element("tmx", version="1.4")
    header = ET.SubElement(root, "header", creationtool="KADIMA", creationtoolversion="1.0",
                           datatype="plaintext", segtype="sentence", adminlang="he")
    body = ET.SubElement(root, "body")

    for term in terms:
        tu = ET.SubElement(body, "tuv", xml="he")
        seg = ET.SubElement(tu, "seg")
        seg.text = term.get("surface", "")

    return ET.tostring(root, encoding="unicode", xml_declaration=True)


def export_conllu(sentences: List[List[Dict[str, Any]]]) -> str:
    """Экспорт в CoNLL-U формат."""
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
    return "\n".join(lines)


EXPORT_FORMATS = {
    "csv": export_csv,
    "json": export_json,
    "tbx": export_tbx,
    "tmx": export_tmx,
    "conllu": export_conllu,
}
