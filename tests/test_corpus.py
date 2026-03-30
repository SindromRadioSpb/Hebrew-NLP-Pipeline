"""Tests for kadima/corpus/ — importer, statistics, exporter."""

import os
import json
import csv
import tempfile
import pytest
from kadima.corpus.importer import import_files, import_directory, SUPPORTED_FORMATS
from kadima.corpus.statistics import compute_statistics
from kadima.corpus.exporter import export_csv, export_json


# ── Importer ─────────────────────────────────────────────────

class TestImportFiles:
    def test_import_txt(self, tmp_path):
        p = tmp_path / "test.txt"
        p.write_text("חוזק מתיחה של הפלדה.\nבטון קל.", encoding="utf-8")
        docs = import_files([str(p)])
        assert len(docs) == 1
        assert "חוזק" in docs[0]["raw_text"]
        assert docs[0]["format"] == "txt"

    def test_import_csv(self, tmp_path):
        p = tmp_path / "test.csv"
        with open(p, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["filename", "raw_text"])
            writer.writerow(["doc_01", "חוזק מתיחה"])
            writer.writerow(["doc_02", "בטון קל"])
        docs = import_files([str(p)])
        assert len(docs) == 2

    def test_import_json_list_of_dicts(self, tmp_path):
        p = tmp_path / "test.json"
        data = [{"filename": "doc_01", "raw_text": "חוזק מתיחה"}]
        p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        docs = import_files([str(p)])
        assert len(docs) == 1
        assert docs[0]["raw_text"] == "חוזק מתיחה"
        assert docs[0]["filename"] == "doc_01"

    def test_import_json_string(self, tmp_path):
        p = tmp_path / "test.json"
        p.write_text(json.dumps("חוזק מתיחה", ensure_ascii=False), encoding="utf-8")
        docs = import_files([str(p)])
        assert len(docs) == 1
        assert docs[0]["raw_text"] == "חוזק מתיחה"

    def test_import_json_dict(self, tmp_path):
        p = tmp_path / "test.json"
        data = {"text": "חוזק מתיחה"}
        p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        docs = import_files([str(p)])
        assert len(docs) == 1
        assert docs[0]["raw_text"] == "חוזק מתיחה"

    def test_unsupported_format_skipped(self, tmp_path):
        p = tmp_path / "test.xml"
        p.write_text("<doc>test</doc>")
        docs = import_files([str(p)])
        assert len(docs) == 0

    def test_import_multiple_files(self, tmp_path):
        for i in range(3):
            p = tmp_path / f"doc_{i}.txt"
            p.write_text(f"מסמך {i}", encoding="utf-8")
        docs = import_files([str(tmp_path / f"doc_{i}.txt") for i in range(3)])
        assert len(docs) == 3


class TestImportDirectory:
    def test_recursive(self, tmp_path):
        sub = tmp_path / "sub"
        sub.mkdir()
        (tmp_path / "a.txt").write_text("מסמך א", encoding="utf-8")
        (sub / "b.txt").write_text("מסמך ב", encoding="utf-8")
        docs = import_directory(str(tmp_path), recursive=True)
        assert len(docs) == 2

    def test_non_recursive(self, tmp_path):
        sub = tmp_path / "sub"
        sub.mkdir()
        (tmp_path / "a.txt").write_text("מסמך א", encoding="utf-8")
        (sub / "b.txt").write_text("מסמך ב", encoding="utf-8")
        docs = import_directory(str(tmp_path), recursive=False)
        assert len(docs) == 1


# ── Statistics ───────────────────────────────────────────────

class TestStatistics:
    def test_basic_stats(self):
        docs = [
            {"filename": "a.txt", "raw_text": "חוזק מתיחה של הפלדה."},
            {"filename": "b.txt", "raw_text": "בטון קל."},
        ]
        stats = compute_statistics(docs)
        assert stats["document_count"] == 2
        assert stats["total_words"] > 0
        assert stats["total_sentences"] >= 2

    def test_empty_corpus(self):
        stats = compute_statistics([])
        assert stats["document_count"] == 0
        assert stats["total_words"] == 0

    def test_empty_document(self):
        docs = [{"filename": "empty.txt", "raw_text": ""}]
        stats = compute_statistics(docs)
        assert stats["document_count"] == 1
        assert stats["total_words"] == 0


# ── Exporter ─────────────────────────────────────────────────

class TestExporter:
    def test_export_csv(self):
        terms = [
            {"surface": "חוזק מתיחה", "freq": 10, "pmi": 5.2},
            {"surface": "בטון קל", "freq": 5, "pmi": 3.1},
        ]
        result = export_csv(terms)
        assert "חוזק מתיחה" in result
        assert "בטון קל" in result

    def test_export_json(self):
        terms = [{"surface": "חוזק מתיחה", "freq": 10}]
        result = export_json(terms)
        parsed = json.loads(result)
        assert parsed["count"] == 1
        assert parsed["terms"][0]["surface"] == "חוזק מתיחה"

    def test_export_json_empty(self):
        result = export_json([])
        parsed = json.loads(result)
        assert parsed["count"] == 0
        assert parsed["terms"] == []


# ── Supported formats ────────────────────────────────────────

class TestSupportedFormats:
    def test_txt(self):
        assert ".txt" in SUPPORTED_FORMATS

    def test_csv(self):
        assert ".csv" in SUPPORTED_FORMATS

    def test_json(self):
        assert ".json" in SUPPORTED_FORMATS

    def test_conllu(self):
        assert ".conllu" in SUPPORTED_FORMATS
