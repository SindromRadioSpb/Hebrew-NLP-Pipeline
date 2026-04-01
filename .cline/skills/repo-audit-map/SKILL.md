---
name: repo-audit-map
description: Use this skill before planning or coding any change in Kadima. Performs a mandatory repo audit: maps entry points (UI handlers, workers, services), DB tables/queries touched, existing progress UI, retry/busy_timeout policy, and relevant tests. Returns file map, risks, constraints, and a minimal patch series outline.
---

# Repo Audit Map — mandatory first step

## When to use
Before planning or coding ANY change. Do not propose implementation before the audit.

## Objective
Produce a precise map of:
- entry points (UI handlers, workers, services, API routers)
- DB tables/queries touched by the change
- existing progress UI / dialogs / signals
- retry/busy_timeout policy
- tests and smoke commands relevant to the touched area
- risk register for the change

## Steps

1. Locate code entry points for the requested feature:
   - UI handler(s) in `kadima/ui/*_view.py`
   - background worker(s) (`QRunnable`) and signal contracts
   - service/engine layer functions in `kadima/engine/` or `kadima/pipeline/`
   - API routers in `kadima/api/routers/`
   - DB models + migrations in `kadima/data/`

2. Locate existing reusable components:
   - progress dialogs, retry decorators, DB helpers
   - existing similar endpoints or engine modules

3. Identify invariants and constraints from code/docs:
   - ProcessorProtocol contract (`kadima/engine/contracts.py`)
   - CLAUDE.md architecture rules (no NLP logic in routers, migrations only in SQL files)
   - SQLite WAL constraints

4. Return:
   - **A) File map** with exact paths and key functions/classes
   - **B) Risks + mitigations**
   - **C) Minimal patch strategy** (PATCH-01..N outline)
   - **D) Tests to run** (exact commands)

## Output format

```
### Repo Audit Findings

#### File Map
| File | Symbols | Role |
|------|---------|------|

#### Constraints / Invariants

#### Risks + Mitigations

#### Recommended Patch Series Outline
- PATCH-01: ...
- PATCH-02: ...

#### Tests to Run Now
```bash
pytest tests/ -v
pytest tests/<specific_module>/ -v
```
```

## Kadima-specific checks
- Confirm engine module implements `ProcessorProtocol` (`process`, `validate_input`, `process_batch`)
- Confirm no ML imports outside `try/except ImportError`
- Confirm no CUDA calls without `torch.cuda.is_available()`
- Confirm API router only calls engine/pipeline, no NLP logic inline
- Confirm DB changes go through migration files, not `CREATE TABLE` in code
