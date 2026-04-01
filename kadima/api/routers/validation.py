# kadima/api/routers/validation.py
"""REST API: Validation framework — vertical slice (T6).

Endpoints:
  GET  /validation/corpora            — list available gold corpora
  POST /validation/run                — run pipeline + checks against gold corpus
  GET  /validation/report/{run_id}    — get a stored validation run
  POST /validation/review/{run_id}/{check_index} — override check verdict
  GET  /validation/export/{run_id}    — export as JSON or CSV (?format=json|csv)
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse

from kadima.api.schemas import (
    CheckResultItem,
    GoldCorpusInfo,
    ReviewUpdateRequest,
    ValidationRunRequest,
    ValidationRunResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Gold corpus discovery path (override via KADIMA_GOLD_DATA env var)
# ---------------------------------------------------------------------------

_HERE = os.path.dirname(os.path.abspath(__file__))
_GOLD_DATA_PATH = os.environ.get(
    "KADIMA_GOLD_DATA",
    os.path.normpath(os.path.join(_HERE, "..", "..", "..", "tests", "data")),
)

# In-process store for validation runs: run_id → ValidationRunResponse dict
_store: dict[int, dict[str, Any]] = {}
_run_counter = 0


def _next_run_id() -> int:
    global _run_counter
    _run_counter += 1
    return _run_counter


def _checks_to_items(check_results: list) -> list[CheckResultItem]:
    """Convert CheckResult objects to CheckResultItem schemas."""
    return [
        CheckResultItem(
            index=i,
            check_type=cr.check_type,
            file_id=cr.file_id,
            item=cr.item,
            expected=cr.expected,
            actual=cr.actual,
            result=cr.result,
            expectation_type=cr.expectation_type,
            discrepancy_type=cr.discrepancy_type,
        )
        for i, cr in enumerate(check_results)
    ]


def _discover_gold_corpora() -> list[GoldCorpusInfo]:
    """Scan GOLD_DATA_PATH for corpus directories with a manifest."""
    result = []
    if not os.path.isdir(_GOLD_DATA_PATH):
        return result
    for name in sorted(os.listdir(_GOLD_DATA_PATH)):
        d = os.path.join(_GOLD_DATA_PATH, name)
        if not os.path.isdir(d):
            continue
        manifest = os.path.join(d, "corpus_manifest.json")
        if not os.path.exists(manifest):
            continue
        import json
        try:
            with open(manifest, encoding="utf-8") as f:
                m = json.load(f)
        except Exception:
            continue
        text_count = m.get("text_count", 0)
        lang = m.get("language", "he")
        # Count check files as a rough estimate
        check_count = sum(
            1 for fn in os.listdir(d) if fn.endswith(".yaml") or fn.endswith(".csv")
        )
        result.append(GoldCorpusInfo(
            corpus_name=name, language=lang,
            text_count=text_count, check_count=check_count,
        ))
    return result


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/validation/corpora", response_model=list[GoldCorpusInfo])
async def list_gold_corpora() -> list[GoldCorpusInfo]:
    """List all discovered gold corpora available for validation."""
    corpora = await asyncio.to_thread(_discover_gold_corpora)
    logger.info("Discovered %d gold corpora at %s", len(corpora), _GOLD_DATA_PATH)
    return corpora


@router.post("/validation/run", response_model=ValidationRunResponse, status_code=201)
async def run_validation(body: ValidationRunRequest) -> ValidationRunResponse:
    """Run pipeline on all raw files of a gold corpus and return check results.

    The result is stored under a new run_id and can be retrieved via
    GET /validation/report/{run_id}.
    """
    gold_dir = os.path.join(_GOLD_DATA_PATH, body.gold_corpus)
    if not os.path.isdir(gold_dir):
        raise HTTPException(
            status_code=404,
            detail=f"Gold corpus not found: {body.gold_corpus!r}",
        )

    t0 = time.time()
    try:
        from kadima.validation.service import run_validation_on_gold

        check_results, report = await asyncio.to_thread(
            run_validation_on_gold, gold_dir, body.db_path
        )
    except Exception as exc:
        logger.error("Validation run failed for %s: %s", body.gold_corpus, exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    run_id = _next_run_id()
    items = _checks_to_items(check_results)
    summary = {
        "PASS": sum(1 for c in items if c.result == "PASS"),
        "WARN": sum(1 for c in items if c.result == "WARN"),
        "FAIL": sum(1 for c in items if c.result == "FAIL"),
    }

    response = ValidationRunResponse(
        run_id=run_id,
        gold_corpus=body.gold_corpus,
        status=report.status,
        checks=items,
        summary=summary,
        total_checks=len(items),
    )
    _store[run_id] = response.model_dump()
    logger.info(
        "Validation run %d finished in %.0fms: %s %s",
        run_id, (time.time() - t0) * 1000, body.gold_corpus, report.status,
    )
    return response


@router.get("/validation/report/{run_id}", response_model=ValidationRunResponse)
async def get_validation_report(run_id: int) -> ValidationRunResponse:
    """Get a previously stored validation run by run_id."""
    data = _store.get(run_id)
    if data is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return ValidationRunResponse(**data)


@router.post("/validation/review/{run_id}/{check_index}")
async def update_review(
    run_id: int, check_index: int, body: ReviewUpdateRequest
) -> dict[str, Any]:
    """Override the verdict of a single check in a stored run.

    Args:
        run_id: ID returned by POST /validation/run.
        check_index: Zero-based index of the check to update.
        body: New verdict and optional discrepancy type.
    """
    data = _store.get(run_id)
    if data is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    checks = data.get("checks", [])
    if check_index < 0 or check_index >= len(checks):
        raise HTTPException(
            status_code=400,
            detail=f"check_index {check_index} out of range (0–{len(checks) - 1})",
        )
    checks[check_index]["result"] = body.pass_fail
    checks[check_index]["discrepancy_type"] = body.discrepancy_type
    # Recompute summary
    data["summary"] = {
        "PASS": sum(1 for c in checks if c["result"] == "PASS"),
        "WARN": sum(1 for c in checks if c["result"] == "WARN"),
        "FAIL": sum(1 for c in checks if c["result"] == "FAIL"),
    }
    fail = data["summary"]["FAIL"]
    warn = data["summary"]["WARN"]
    data["status"] = "FAIL" if fail > 0 else ("WARN" if warn > 0 else "PASS")
    logger.info("Review updated: run=%d check=%d → %s", run_id, check_index, body.pass_fail)
    return {"run_id": run_id, "check_index": check_index, "result": body.pass_fail}


@router.get("/validation/export/{run_id}")
async def export_report(
    run_id: int,
    format: str = Query(default="json", pattern="^(json|csv)$"),
) -> Any:
    """Export a validation run report.

    Args:
        run_id: Run ID from POST /validation/run.
        format: Output format — 'json' (default) or 'csv'.
    """
    data = _store.get(run_id)
    if data is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    if format == "csv":
        from kadima.validation.report import CheckResult, ValidationReport, report_to_csv

        check_results = [
            CheckResult(
                check_type=c["check_type"], file_id=c["file_id"],
                item=c["item"], expected=c["expected"],
                actual=c["actual"], result=c["result"],
                expectation_type=c["expectation_type"],
                discrepancy_type=c.get("discrepancy_type"),
            )
            for c in data.get("checks", [])
        ]
        report = ValidationReport(
            corpus_id=0, status=data["status"],
            checks=check_results, summary=data["summary"],
        )
        csv_text = report_to_csv(report)
        return PlainTextResponse(
            content=csv_text,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="run_{run_id}.csv"'},
        )

    import json
    return PlainTextResponse(
        content=json.dumps(data, ensure_ascii=False, indent=2),
        media_type="application/json",
    )
