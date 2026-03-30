"""Tests for kadima.validation.gold_importer."""

import os
import tempfile
import pytest
from kadima.validation.gold_importer import load_gold_corpus


class TestGoldImporter:
    def test_load_gold_corpus_structure(self, tmp_path):
        """Verify gold corpus directory can be loaded."""
        corpus_dir = tmp_path / "he_01_test"
        corpus_dir.mkdir()
        (corpus_dir / "corpus_manifest.json").write_text(
            '{"version": "1.0", "description": "test"}',
            encoding="utf-8",
        )
        (corpus_dir / "expected_counts.yaml").write_text(
            "doc1:\n  sentence_count: 1\n",
            encoding="utf-8",
        )
        raw_dir = corpus_dir / "raw"
        raw_dir.mkdir()
        (raw_dir / "doc1.txt").write_text("טקסט לבדיקה.", encoding="utf-8")

        result = load_gold_corpus(str(corpus_dir))
        assert result is not None
        assert result.version == "1.0"
        assert result.description == "test"
        assert len(result.raw_files) == 1
        assert len(result.checks) == 1
        assert result.checks[0].check_type == "sentence_count"

    def test_empty_directory(self, tmp_path):
        """Empty corpus dir should return empty GoldCorpus."""
        corpus_dir = tmp_path / "empty"
        corpus_dir.mkdir()
        result = load_gold_corpus(str(corpus_dir))
        assert result is not None
        assert len(result.checks) == 0
        assert len(result.raw_files) == 0

    def test_with_lemmas_csv(self, tmp_path):
        """Expected lemmas CSV should be loaded."""
        corpus_dir = tmp_path / "with_lemmas"
        corpus_dir.mkdir()
        (corpus_dir / "expected_lemmas.csv").write_text(
            "file,lemma,count,expectation_type\ndoc1,פלדה,3,exact\n",
            encoding="utf-8",
        )
        result = load_gold_corpus(str(corpus_dir))
        assert len(result.checks) == 1
        assert result.checks[0].check_type == "lemma_freq"
        assert result.checks[0].item == "פלדה"
