# tests/fixture_loader.py
"""Загрузчик gold-корпусных фикстур из validation_text_test/."""

import os
import csv
import yaml
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple


FIXTURES_ROOT = os.path.join(os.path.dirname(__file__), "data")


@dataclass
class ExpectedCounts:
    """Ожидаемые количественные значения для одного документа."""
    doc_id: str
    sentence_count: Optional[int] = None
    token_count: Optional[int] = None
    unique_lemma_count: Optional[int] = None
    det_surface_count: Optional[int] = None
    det_surfaces: List[str] = field(default_factory=list)


@dataclass
class CorpusTotals:
    """Суммарные ожидания по корпусу."""
    total_sentences: Optional[int] = None
    total_tokens: Optional[int] = None
    total_unique_lemmas: Optional[int] = None
    total_det_surfaces: Optional[int] = None


@dataclass
class ExpectedLemma:
    """Одна строка из expected_lemmas.csv."""
    file_id: str
    lemma: str
    expected_freq: int
    expected_doc_freq: int
    expected_pos_primary: str
    is_det_surface: bool
    expectation_type: str  # exact | approx | present_only | absent
    comment: str = ""


@dataclass
class ExpectedTerm:
    """Одна строка из expected_terms.csv."""
    corpus_id: str
    term_surface: str
    expected_kind: str
    expected_members: List[str]
    expected_freq: int
    expected_doc_freq: int
    expected_noise: str  # non_noise | noise | edge_case
    expected_rank_bucket: str  # top_10 | top_20 | top_30 | absent
    expectation_type: str  # exact | present_only | absent | relational
    comment: str = ""


@dataclass
class CorpusManifest:
    """Метаданные gold-корпуса из corpus_manifest.json."""
    corpus_id: str
    version: str
    title: str
    purpose: str
    language: str
    domain: str
    difficulty: str
    recommended_profile: str
    text_count: int
    files: List[Dict]
    assertion_policy: Dict
    known_limitations: List[str]


def load_corpus_dir(corpus_id: str) -> str:
    """Вернуть путь к директории корпуса. Бросает ValueError если не найден."""
    root = os.path.abspath(FIXTURES_ROOT)
    for name in os.listdir(root):
        if name.startswith(corpus_id) and os.path.isdir(os.path.join(root, name)):
            return os.path.join(root, name)
    raise ValueError(f"Corpus {corpus_id} not found in {root}")


def load_raw_texts(corpus_dir: str) -> Dict[str, str]:
    """Загрузить все .txt файлы из raw/."""
    raw_dir = os.path.join(corpus_dir, "raw")
    texts = {}
    for fname in sorted(os.listdir(raw_dir)):
        if fname.endswith(".txt"):
            with open(os.path.join(raw_dir, fname), "r", encoding="utf-8") as f:
                texts[fname.replace(".txt", "")] = f.read()
    return texts


def load_expected_counts(corpus_dir: str) -> Tuple[Dict[str, ExpectedCounts], CorpusTotals]:
    """Загрузить expected_counts.yaml."""
    path = os.path.join(corpus_dir, "expected_counts.yaml")
    with open(path, "r", encoding="utf-8-sig") as f:
        data = yaml.safe_load(f)

    docs = {}
    totals = CorpusTotals()

    for key, val in data.items():
        if key == "corpus_total":
            tc = val.get("total_sentences", {})
            totals.total_sentences = tc.get("value") if isinstance(tc, dict) else tc
            tc2 = val.get("total_tokens", {})
            totals.total_tokens = tc2.get("value") if isinstance(tc2, dict) else tc2
            tc3 = val.get("total_unique_lemmas", {})
            totals.total_unique_lemmas = tc3.get("value") if isinstance(tc3, dict) else tc3
            tc4 = val.get("total_det_surfaces", {})
            totals.total_det_surfaces = tc4.get("value") if isinstance(tc4, dict) else tc4
        elif key.startswith("cross_doc"):
            continue
        elif isinstance(val, dict):
            ec = ExpectedCounts(doc_id=key)
            sc = val.get("sentence_count", {})
            ec.sentence_count = sc.get("value") if isinstance(sc, dict) else sc
            tc = val.get("token_count", {})
            ec.token_count = tc.get("value") if isinstance(tc, dict) else tc
            ulc = val.get("unique_lemma_count", {})
            ec.unique_lemma_count = ulc.get("value") if isinstance(ulc, dict) else ulc
            dsc = val.get("det_surface_count", {})
            ec.det_surface_count = dsc.get("value") if isinstance(dsc, dict) else dsc
            ds = val.get("det_surfaces", {})
            ec.det_surfaces = ds.get("value", []) if isinstance(ds, dict) else (ds or [])
            docs[key] = ec

    return docs, totals


def load_expected_lemmas(corpus_dir: str) -> List[ExpectedLemma]:
    """Загрузить expected_lemmas.csv."""
    path = os.path.join(corpus_dir, "expected_lemmas.csv")
    lemmas = []
    with open(path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            lemmas.append(ExpectedLemma(
                file_id=row["file_id"],
                lemma=row["lemma"],
                expected_freq=int(row["expected_freq"]),
                expected_doc_freq=int(row.get("expected_doc_freq", 1)),
                expected_pos_primary=row.get("expected_pos_primary", ""),
                is_det_surface=row.get("is_det_surface", "False") == "True",
                expectation_type=row.get("expectation_type", "exact"),
                comment=row.get("comment", ""),
            ))
    return lemmas


def load_expected_terms(corpus_dir: str) -> List[ExpectedTerm]:
    """Загрузить expected_terms.csv."""
    path = os.path.join(corpus_dir, "expected_terms.csv")
    terms = []
    with open(path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            members_str = row.get("expected_members", "")
            members = [m.strip() for m in members_str.strip('"').split(",") if m.strip()] if members_str else []
            freq = row.get("expected_freq", "0")
            doc_freq = row.get("expected_doc_freq", "0")
            terms.append(ExpectedTerm(
                corpus_id=row["corpus_id"],
                term_surface=row["term_surface"],
                expected_kind=row.get("expected_kind", ""),
                expected_members=members,
                expected_freq=int(freq) if freq.isdigit() else 0,
                expected_doc_freq=int(doc_freq) if doc_freq.isdigit() else 0,
                expected_noise=row.get("expected_noise", ""),
                expected_rank_bucket=row.get("expected_rank_bucket", ""),
                expectation_type=row.get("expectation_type", "exact"),
                comment=row.get("comment", ""),
            ))
    return terms


def load_manifest(corpus_dir: str) -> CorpusManifest:
    """Загрузить corpus_manifest.json."""
    import json
    path = os.path.join(corpus_dir, "corpus_manifest.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return CorpusManifest(
        corpus_id=data["corpus_id"],
        version=data.get("version", "1.0.0"),
        title=data.get("title", ""),
        purpose=data.get("purpose", ""),
        language=data.get("language", "he"),
        domain=data.get("domain", ""),
        difficulty=data.get("difficulty", ""),
        recommended_profile=data.get("recommended_profile", "any"),
        text_count=data.get("text_count", 0),
        files=data.get("files", []),
        assertion_policy=data.get("assertion_policy", {}),
        known_limitations=data.get("known_limitations", []),
    )


def discover_corpora() -> List[str]:
    """Вернуть список corpus_id (имена директорий he_XX_...)."""
    root = os.path.abspath(FIXTURES_ROOT)
    return sorted(
        name for name in os.listdir(root)
        if name.startswith("he_") and os.path.isdir(os.path.join(root, name))
    )


def load_corpus(corpus_id: str) -> Dict:
    """Загрузить всё для данного корпуса в один dict."""
    corpus_dir = load_corpus_dir(corpus_id)
    docs, totals = load_expected_counts(corpus_dir)
    return {
        "corpus_id": corpus_id,
        "corpus_dir": corpus_dir,
        "manifest": load_manifest(corpus_dir),
        "raw_texts": load_raw_texts(corpus_dir),
        "expected_counts": docs,
        "corpus_totals": totals,
        "expected_lemmas": load_expected_lemmas(corpus_dir),
        "expected_terms": load_expected_terms(corpus_dir),
    }
