# kadima/validation/check_engine.py
"""M11: ExpectedCheck → actual → comparison.

Example:
    >>> from kadima.validation.gold_importer import ExpectedCheck
    >>> from kadima.validation.check_engine import run_checks
    >>> checks = [ExpectedCheck("sentence_count", "doc1", "sentences", "2", "exact")]
    >>> actuals = {"sentence_count:doc1:sentences": "2"}
    >>> results = run_checks(checks, actuals)
    >>> results[0].result
    'PASS'
"""

import logging
from typing import List, Dict, Optional
from dataclasses import dataclass

from kadima.validation.gold_importer import ExpectedCheck

logger = logging.getLogger(__name__)


@dataclass
class CheckResult:
    """Результат одной проверки."""
    check_type: str
    file_id: str
    item: str
    expected: str
    actual: str
    result: str             # PASS | WARN | FAIL
    expectation_type: str
    discrepancy_type: Optional[str] = None  # bug | stale_gold | pipeline_variant | known_limitation


def compare_exact(expected: str, actual: str) -> str:
    """Точное совпадение."""
    return "PASS" if str(expected) == str(actual) else "FAIL"


def compare_approx(expected: str, actual: str, tolerance: float = 0.1) -> str:
    """Приблизительное совпадение (±tolerance)."""
    try:
        exp_val = float(expected)
        act_val = float(actual)
        if exp_val == 0:
            return "PASS" if act_val == 0 else "FAIL"
        diff = abs(exp_val - act_val) / abs(exp_val)
        if diff <= tolerance:
            return "PASS"
        elif diff <= tolerance * 2:
            return "WARN"
        else:
            return "FAIL"
    except ValueError:
        return compare_exact(expected, actual)


def compare_present_only(expected: str, actual: str) -> str:
    """Элемент должен присутствовать (actual не пустой)."""
    return "PASS" if actual and actual != "0" and actual != "None" else "FAIL"


def compare_absent(expected: str, actual: str) -> str:
    """Элемент должен отсутствовать."""
    return "PASS" if not actual or actual == "0" or actual == "None" else "FAIL"


COMPARATORS = {
    "exact": compare_exact,
    "approx": compare_approx,
    "present_only": compare_present_only,
    "absent": compare_absent,
}


def run_checks(checks: List[ExpectedCheck], actuals: Dict[str, str]) -> List[CheckResult]:
    """
    Запустить все проверки.

    Args:
        checks: список ExpectedCheck из gold corpus
        actuals: словарь "check_type:file_id:item" → actual value
    """
    results = []
    for check in checks:
        key = f"{check.check_type}:{check.file_id}:{check.item}"
        actual = actuals.get(key, "N/A")

        comparator = COMPARATORS.get(check.expectation_type, compare_exact)
        verdict = comparator(check.expected_value, actual)

        discrepancy = None
        if verdict == "FAIL":
            discrepancy = "bug"  # default, может быть обновлено в review

        results.append(CheckResult(
            check_type=check.check_type, file_id=check.file_id,
            item=check.item, expected=check.expected_value,
            actual=actual, result=verdict,
            expectation_type=check.expectation_type,
            discrepancy_type=discrepancy,
        ))

    return results
