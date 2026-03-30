# kadima/validation/report.py
"""M11: PASS/WARN/FAIL report generation."""

import json
import csv
import io
import logging
from typing import List, Dict
from dataclasses import dataclass, field

from kadima.validation.check_engine import CheckResult

logger = logging.getLogger(__name__)


@dataclass
class ValidationReport:
    corpus_id: int
    status: str             # PASS | WARN | FAIL
    checks: List[CheckResult]
    summary: Dict[str, int] = field(default_factory=dict)


def generate_report(corpus_id: int, check_results: List[CheckResult]) -> ValidationReport:
    """Сгенерировать отчёт из результатов проверок."""
    summary = {"pass": 0, "warn": 0, "fail": 0}
    for cr in check_results:
        if cr.result == "PASS":
            summary["pass"] += 1
        elif cr.result == "WARN":
            summary["warn"] += 1
        else:
            summary["fail"] += 1

    if summary["fail"] > 0:
        status = "FAIL"
    elif summary["warn"] > 0:
        status = "WARN"
    else:
        status = "PASS"

    return ValidationReport(
        corpus_id=corpus_id, status=status,
        checks=check_results, summary=summary,
    )


def report_to_csv(report: ValidationReport) -> str:
    """Экспорт отчёта в CSV."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["check_type", "file", "item", "expected", "actual", "result", "expectation_type", "discrepancy_type"])
    for cr in report.checks:
        writer.writerow([cr.check_type, cr.file_id, cr.item, cr.expected, cr.actual, cr.result, cr.expectation_type, cr.discrepancy_type])
    return output.getvalue()


def report_to_json(report: ValidationReport) -> str:
    """Экспорт отчёта в JSON."""
    return json.dumps({
        "corpus_id": report.corpus_id,
        "status": report.status,
        "summary": report.summary,
        "checks": [
            {
                "check_type": cr.check_type, "file": cr.file_id,
                "item": cr.item, "expected": cr.expected,
                "actual": cr.actual, "result": cr.result,
                "discrepancy_type": cr.discrepancy_type,
            }
            for cr in report.checks
        ],
    }, ensure_ascii=False, indent=2)
