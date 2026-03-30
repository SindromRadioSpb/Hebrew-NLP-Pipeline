"""Tests for kadima.validation.check_engine."""

import pytest
from kadima.validation.check_engine import run_checks, compare_exact, compare_approx
from kadima.validation.gold_importer import ExpectedCheck


class TestComparators:
    def test_exact_pass(self):
        assert compare_exact("5", "5") == "PASS"

    def test_exact_fail(self):
        assert compare_exact("5", "3") == "FAIL"

    def test_approx_pass(self):
        assert compare_approx("10", "10.5", tolerance=0.1) == "PASS"

    def test_approx_warn(self):
        assert compare_approx("10", "11.5", tolerance=0.1) == "WARN"

    def test_approx_fail(self):
        assert compare_approx("10", "20", tolerance=0.1) == "FAIL"


class TestRunChecks:
    def test_empty_checks(self):
        result = run_checks([], {})
        assert result == []

    def test_exact_pass(self):
        checks = [ExpectedCheck(
            check_type="sentence_count", file_id="doc1",
            item="sentence_count", expected_value="2",
            expectation_type="exact",
        )]
        actuals = {"sentence_count:doc1:sentence_count": "2"}
        result = run_checks(checks, actuals)
        assert result[0].result == "PASS"

    def test_exact_fail(self):
        checks = [ExpectedCheck(
            check_type="sentence_count", file_id="doc1",
            item="sentence_count", expected_value="5",
            expectation_type="exact",
        )]
        actuals = {"sentence_count:doc1:sentence_count": "2"}
        result = run_checks(checks, actuals)
        assert result[0].result == "FAIL"

    def test_missing_actual(self):
        checks = [ExpectedCheck(
            check_type="term_present", file_id="doc1",
            item="חוזק", expected_value="present",
            expectation_type="present_only",
        )]
        result = run_checks(checks, {})
        assert result[0].actual == "N/A"
