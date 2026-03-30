"""Tests for kadima/corpus/importer."""

import os
import csv
import pytest
from kadima.corpus.importer import import_files, import_directory, SUPPORTED_FORMATS


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

    def test_import_nonexistent(self):
        docs = import_files(["/nonexistent/file.txt"])
        assert len(docs) == 0

    def test_supported_formats(self):
        assert ".txt" in SUPPORTED_FORMATS
        assert ".csv" in SUPPORTED_FORMATS


class TestImportDirectory:
    def test_import_directory_txt(self, tmp_path):
        (tmp_path / "a.txt").write_text("טקסט א", encoding="utf-8")
        (tmp_path / "b.txt").write_text("טקסט ב", encoding="utf-8")
        docs = import_directory(str(tmp_path))
        assert len(docs) == 2
