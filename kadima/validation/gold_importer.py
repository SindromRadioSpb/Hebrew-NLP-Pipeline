# kadima/validation/gold_importer.py
"""M11: Импорт gold corpus (manifest + expected CSV).

Example:
    >>> from kadima.validation.gold_importer import load_gold_corpus
    >>> corpus = load_gold_corpus("tests/data/he_01_sentence_token_lemma_basics")
    >>> len(corpus.checks) >= 0
    True
"""

import json
import csv
import os
import yaml
import logging
from typing import List, Dict
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Top-level YAML sections that are NOT per-document file IDs
_SPECIAL_YAML_SECTIONS = {"corpus_total", "cross_doc_lemma_freq"}


def _serialize_value(value: object) -> tuple[str, str]:
    """Serialize a YAML value to (canonical_string, expectation_type).

    Returns:
        (serialized_value, expectation_type) — list values use "list_exact".
    """
    if isinstance(value, list):
        return json.dumps(sorted(str(v) for v in value), ensure_ascii=False), "list_exact"
    return str(value), "exact"


@dataclass
class ExpectedCheck:
    """Одна проверка из gold corpus."""
    check_type: str       # sentence_count | token_count | lemma_freq | term_present
    file_id: str
    item: str
    expected_value: str
    expectation_type: str # exact | approx | present_only | absent | relational | manual_review


@dataclass
class GoldCorpus:
    """Полный gold corpus."""
    corpus_id: int
    version: str
    description: str
    checks: List[ExpectedCheck] = field(default_factory=list)
    raw_files: Dict[str, str] = field(default_factory=dict)  # filename → text


def load_gold_corpus(corpus_dir: str) -> GoldCorpus:
    """
    Загрузить gold corpus из директории.

    Ожидаемая структура:
        corpus_dir/
            corpus_manifest.json
            expected_counts.yaml
            expected_lemmas.csv
            expected_terms.csv
            review_sheet.csv
            raw/
                doc_01.txt
                doc_02.txt
    """
    checks = []
    raw_files = {}

    # 1. Manifest
    manifest_path = os.path.join(corpus_dir, "corpus_manifest.json")
    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        version = manifest.get("version", "1.0")
        description = manifest.get("description", "")
    else:
        version = "1.0"
        description = os.path.basename(corpus_dir)

    # 2. Expected counts (YAML)
    counts_path = os.path.join(corpus_dir, "expected_counts.yaml")
    if os.path.exists(counts_path):
        with open(counts_path, "r", encoding="utf-8") as f:
            counts = yaml.safe_load(f) or {}

        for section_key, section_val in counts.items():
            if not isinstance(section_val, dict):
                continue
            # Skip YAML comment keys
            if str(section_key).startswith("#"):
                continue

            if section_key == "corpus_total":
                # Aggregate corpus-level checks: file_id = "corpus_total"
                for check_type, value in section_val.items():
                    if str(check_type).startswith("#"):
                        continue
                    if isinstance(value, dict):
                        raw_val = value.get("value", "")
                        serialized, inferred_type = _serialize_value(raw_val)
                        # list_exact takes precedence — the YAML "type: exact" is for scalar intent
                        expectation_type = inferred_type if inferred_type == "list_exact" else str(value.get("type", "exact"))
                    else:
                        serialized, expectation_type = _serialize_value(value)
                    checks.append(ExpectedCheck(
                        check_type=check_type, file_id="corpus_total",
                        item=check_type, expected_value=serialized,
                        expectation_type=expectation_type,
                    ))

            elif section_key == "cross_doc_lemma_freq":
                # Cross-document lemma frequency checks: file_id = "cross_doc"
                for lemma, value in section_val.items():
                    if str(lemma).startswith("#"):
                        continue
                    if isinstance(value, dict):
                        expected_value = str(value.get("total_freq", value.get("value", "")))
                        expectation_type = str(value.get("type", "exact"))
                    else:
                        expected_value = str(value)
                        expectation_type = "exact"
                    checks.append(ExpectedCheck(
                        check_type="cross_doc_lemma_freq", file_id="cross_doc",
                        item=str(lemma), expected_value=expected_value,
                        expectation_type=expectation_type,
                    ))

            else:
                # Regular per-document section: section_key is file_id
                file_id = str(section_key)
                for check_type, value in section_val.items():
                    if str(check_type).startswith("#"):
                        continue
                    if isinstance(value, dict):
                        raw_val = value.get("value", "")
                        serialized, inferred_type = _serialize_value(raw_val)
                        # list_exact takes precedence over the YAML "type: exact" scalar hint
                        expectation_type = inferred_type if inferred_type == "list_exact" else str(value.get("type", "exact"))
                    else:
                        serialized, expectation_type = _serialize_value(value)
                    checks.append(ExpectedCheck(
                        check_type=check_type, file_id=file_id,
                        item=check_type, expected_value=serialized,
                        expectation_type=expectation_type,
                    ))

    # 3. Expected lemmas (CSV)
    lemmas_path = os.path.join(corpus_dir, "expected_lemmas.csv")
    if os.path.exists(lemmas_path):
        with open(lemmas_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                checks.append(ExpectedCheck(
                    check_type="lemma_freq", file_id=row.get("file", ""),
                    item=row.get("lemma", ""), expected_value=row.get("count", "0"),
                    expectation_type=row.get("expectation_type", "exact"),
                ))

    # 4. Expected terms (CSV)
    terms_path = os.path.join(corpus_dir, "expected_terms.csv")
    if os.path.exists(terms_path):
        with open(terms_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                checks.append(ExpectedCheck(
                    check_type="term_present", file_id=row.get("file", ""),
                    item=row.get("term", ""), expected_value=row.get("expected", "present"),
                    expectation_type=row.get("expectation_type", "present_only"),
                ))

    # 5. Raw files
    raw_dir = os.path.join(corpus_dir, "raw")
    if os.path.isdir(raw_dir):
        for fname in sorted(os.listdir(raw_dir)):
            if fname.endswith(".txt"):
                with open(os.path.join(raw_dir, fname), "r", encoding="utf-8") as f:
                    raw_files[fname] = f.read()

    logger.info("Loaded gold corpus from %s: %d checks, %d raw files", corpus_dir, len(checks), len(raw_files))

    return GoldCorpus(
        corpus_id=0, version=version, description=description,
        checks=checks, raw_files=raw_files,
    )
