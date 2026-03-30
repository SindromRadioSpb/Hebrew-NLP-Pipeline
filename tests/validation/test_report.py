"""Tests for kadima.validation.report."""

import pytest
from kadima.validation.report import generate_report
from kadima.validation.check_engine import CheckResult


def _make_check(result: str = "PASS") -> CheckResult:
    return CheckResult(
        check_type="sentence_count", file_id="doc1",
        item="sentence_count", expected="1", actual="1",
        result=result, expectation_type="exact",
    )


class TestReport:
    def test_empty_report(self):
        report = generate_report(0, [])
        assert report.status == "PASS"
        assert report.summary["pass"] == 0

    def test_all_pass(self):
        checks = [_make_check("PASS"), _make_check("PASS")]
        report = generate_report(1, checks)
        assert report.status == "PASS"
        assert report.summary["pass"] == 2

    def test_fail_takes_priority(self):
        checks = [_make_check("PASS"), _make_check("FAIL"), _make_check("WARN")]
        report = generate_report(1, checks)
        assert report.status == "FAIL"
        assert report.summary["pass"] == 1
        assert report.summary["fail"] == 1
        assert report.summary["warn"] == 1

    def test_warn_without_fail(self):
        checks = [_make_check("PASS"), _make_check("WARN")]
        report = generate_report(1, checks)
        assert report.status == "WARN"
