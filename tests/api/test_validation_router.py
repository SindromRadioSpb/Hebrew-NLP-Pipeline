# tests/api/test_validation_router.py
"""Integration tests for the validation router vertical slice (T6).

Uses FastAPI TestClient. The he_test_sample corpus (2 docs, fast pipeline)
is used for integration tests. Schema and error-path tests use mocks.
"""
from __future__ import annotations

import json
import os
import sys
from typing import Any

import pytest

# Ensure the project root is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fastapi.testclient import TestClient

from kadima.api.app import create_app

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_HE_TEST_SAMPLE = "he_test_sample"


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Shared TestClient for all tests in this module."""
    app = create_app()
    return TestClient(app)


# ---------------------------------------------------------------------------
# GET /validation/corpora
# ---------------------------------------------------------------------------


def test_list_corpora_returns_list(client: TestClient) -> None:
    resp = client.get("/api/v1/validation/corpora")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


def test_list_corpora_contains_he_test_sample(client: TestClient) -> None:
    resp = client.get("/api/v1/validation/corpora")
    assert resp.status_code == 200
    names = [c["corpus_name"] for c in resp.json()]
    assert _HE_TEST_SAMPLE in names


def test_list_corpora_items_have_required_fields(client: TestClient) -> None:
    resp = client.get("/api/v1/validation/corpora")
    assert resp.status_code == 200
    for item in resp.json():
        assert "corpus_name" in item
        assert "language" in item
        assert "text_count" in item
        assert "check_count" in item


def test_list_corpora_not_empty(client: TestClient) -> None:
    resp = client.get("/api/v1/validation/corpora")
    assert len(resp.json()) >= 1


# ---------------------------------------------------------------------------
# POST /validation/run — error paths (fast, no pipeline)
# ---------------------------------------------------------------------------


def test_run_unknown_corpus_returns_404(client: TestClient) -> None:
    resp = client.post("/api/v1/validation/run", json={"gold_corpus": "he_nonexistent"})
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


def test_run_missing_body_returns_422(client: TestClient) -> None:
    resp = client.post("/api/v1/validation/run", json={})
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /validation/run — integration (he_test_sample, real pipeline)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def run_result(client: TestClient) -> dict[str, Any]:
    """Run validation on he_test_sample once and share the result."""
    resp = client.post(
        "/api/v1/validation/run",
        json={"gold_corpus": _HE_TEST_SAMPLE},
    )
    assert resp.status_code == 201, f"Run failed: {resp.text}"
    return resp.json()


def test_run_returns_run_id(run_result: dict) -> None:
    assert "run_id" in run_result
    assert isinstance(run_result["run_id"], int)
    assert run_result["run_id"] >= 1


def test_run_returns_gold_corpus_name(run_result: dict) -> None:
    assert run_result["gold_corpus"] == _HE_TEST_SAMPLE


def test_run_status_is_valid(run_result: dict) -> None:
    assert run_result["status"] in ("PASS", "WARN", "FAIL")


def test_run_checks_is_list(run_result: dict) -> None:
    assert isinstance(run_result["checks"], list)


def test_run_total_checks_matches_checks_len(run_result: dict) -> None:
    assert run_result["total_checks"] == len(run_result["checks"])


def test_run_summary_has_three_keys(run_result: dict) -> None:
    s = run_result["summary"]
    assert set(s.keys()) >= {"PASS", "WARN", "FAIL"}


def test_run_summary_totals_match_checks(run_result: dict) -> None:
    s = run_result["summary"]
    checks = run_result["checks"]
    assert s["PASS"] == sum(1 for c in checks if c["result"] == "PASS")
    assert s["FAIL"] == sum(1 for c in checks if c["result"] == "FAIL")


def test_run_check_items_have_required_fields(run_result: dict) -> None:
    for c in run_result["checks"]:
        for field in ("index", "check_type", "file_id", "item",
                      "expected", "actual", "result", "expectation_type"):
            assert field in c, f"Missing field {field!r} in check {c}"


def test_run_check_results_are_valid_verdicts(run_result: dict) -> None:
    valid = {"PASS", "WARN", "FAIL"}
    for c in run_result["checks"]:
        assert c["result"] in valid, f"Invalid verdict: {c['result']}"


# ---------------------------------------------------------------------------
# GET /validation/report/{run_id}
# ---------------------------------------------------------------------------


def test_get_report_returns_same_run(client: TestClient, run_result: dict) -> None:
    run_id = run_result["run_id"]
    resp = client.get(f"/api/v1/validation/report/{run_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["run_id"] == run_id
    assert data["gold_corpus"] == _HE_TEST_SAMPLE


def test_get_report_missing_run_returns_404(client: TestClient) -> None:
    resp = client.get("/api/v1/validation/report/99999")
    assert resp.status_code == 404


def test_get_report_total_checks_preserved(client: TestClient, run_result: dict) -> None:
    run_id = run_result["run_id"]
    resp = client.get(f"/api/v1/validation/report/{run_id}")
    assert resp.json()["total_checks"] == run_result["total_checks"]


# ---------------------------------------------------------------------------
# POST /validation/review/{run_id}/{check_index}
# ---------------------------------------------------------------------------


def test_review_override_changes_verdict(client: TestClient, run_result: dict) -> None:
    run_id = run_result["run_id"]
    # Find any check and flip its result
    checks = run_result["checks"]
    if not checks:
        pytest.skip("no checks in run_result")
    idx = 0
    original = checks[idx]["result"]
    new_verdict = "PASS" if original == "FAIL" else "FAIL"
    resp = client.post(
        f"/api/v1/validation/review/{run_id}/{idx}",
        json={"actual_value": "override", "pass_fail": new_verdict},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["result"] == new_verdict


def test_review_persists_in_report(client: TestClient, run_result: dict) -> None:
    run_id = run_result["run_id"]
    checks = run_result["checks"]
    if not checks:
        pytest.skip("no checks in run_result")
    idx = 0
    resp = client.post(
        f"/api/v1/validation/review/{run_id}/{idx}",
        json={"actual_value": "forced", "pass_fail": "PASS", "discrepancy_type": "stale_gold"},
    )
    assert resp.status_code == 200
    # Verify the report reflects the override
    report_resp = client.get(f"/api/v1/validation/report/{run_id}")
    assert report_resp.status_code == 200
    updated_check = report_resp.json()["checks"][idx]
    assert updated_check["result"] == "PASS"
    assert updated_check["discrepancy_type"] == "stale_gold"


def test_review_invalid_run_returns_404(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/validation/review/99999/0",
        json={"actual_value": "x", "pass_fail": "PASS"},
    )
    assert resp.status_code == 404


def test_review_out_of_range_index_returns_400(client: TestClient, run_result: dict) -> None:
    run_id = run_result["run_id"]
    idx = run_result["total_checks"] + 100  # definitely out of range
    resp = client.post(
        f"/api/v1/validation/review/{run_id}/{idx}",
        json={"actual_value": "x", "pass_fail": "PASS"},
    )
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# GET /validation/export/{run_id}
# ---------------------------------------------------------------------------


def test_export_json_returns_json_content_type(client: TestClient, run_result: dict) -> None:
    run_id = run_result["run_id"]
    resp = client.get(f"/api/v1/validation/export/{run_id}?format=json")
    assert resp.status_code == 200
    assert "application/json" in resp.headers.get("content-type", "")


def test_export_json_is_valid_json(client: TestClient, run_result: dict) -> None:
    run_id = run_result["run_id"]
    resp = client.get(f"/api/v1/validation/export/{run_id}?format=json")
    data = json.loads(resp.text)
    assert "status" in data
    assert "checks" in data


def test_export_csv_returns_csv_content_type(client: TestClient, run_result: dict) -> None:
    run_id = run_result["run_id"]
    resp = client.get(f"/api/v1/validation/export/{run_id}?format=csv")
    assert resp.status_code == 200
    assert "text/csv" in resp.headers.get("content-type", "")


def test_export_csv_has_header_row(client: TestClient, run_result: dict) -> None:
    run_id = run_result["run_id"]
    resp = client.get(f"/api/v1/validation/export/{run_id}?format=csv")
    first_line = resp.text.splitlines()[0]
    assert "check_type" in first_line
    assert "result" in first_line


def test_export_invalid_format_returns_422(client: TestClient, run_result: dict) -> None:
    run_id = run_result["run_id"]
    resp = client.get(f"/api/v1/validation/export/{run_id}?format=xml")
    assert resp.status_code == 422


def test_export_missing_run_returns_404(client: TestClient) -> None:
    resp = client.get("/api/v1/validation/export/99999")
    assert resp.status_code == 404
