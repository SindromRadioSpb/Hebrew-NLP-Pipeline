"""Tests for kadima/corpus.exporter."""

import json
import pytest
from kadima.corpus.exporter import export_csv, export_json


class TestExportCSV:
    def test_basic_csv_export(self):
        terms = [
            {"surface": "חוזק מתיחה", "canonical": "חוזק מתיחה", "freq": 8, "rank": 1},
            {"surface": "בטון קל", "canonical": "בטון קל", "freq": 5, "rank": 2},
        ]
        csv_str = export_csv(terms)
        assert "חוזק מתיחה" in csv_str
        assert csv_str.count("\n") >= 3  # header + 2 rows

    def test_empty_export(self):
        csv_str = export_csv([])
        assert csv_str == ""


class TestExportJSON:
    def test_basic_json_export(self):
        terms = [{"surface": "חוזק", "freq": 10}]
        json_str = export_json(terms)
        data = json.loads(json_str)
        assert data["count"] == 1
        assert data["terms"][0]["surface"] == "חוזק"
