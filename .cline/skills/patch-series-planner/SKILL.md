---
name: patch-series-planner
description: Use this skill for any Kadima feature beyond a 10-30 line fix. Turns a request into a disciplined PATCH-01..N plan where each patch is independently buildable and testable. Produces exact file lists, step-by-step edits, tests, DoD items, and commit messages per patch.
---

# Patch Series Planner — anti-regression

## When to use
Any feature beyond a 10–30 line fix, or any change touching more than 3 files.

## Objective
Turn the request into a disciplined PATCH-01..N plan:
- each patch independently buildable + testable
- minimal diffs, minimal scope per patch
- tests and DoD evidence attached to each patch

## Standard 3-patch structure

```
PATCH-01: Foundations
  - interfaces, contracts, migrations, utilities
  - no behavioral change to existing code
  - passes existing tests unchanged

PATCH-02: Primary integration
  - engine module, service, API wiring, UI wiring
  - new behavior introduced here

PATCH-03: Tests + docs + hardening
  - full test suite for new code
  - DoD evidence
  - follow-up fixes if any
```

## For each patch, produce

1. **Exact file list** (CREATE / MODIFY)
2. **Step-by-step edits** (what/where)
3. **Tests to run** (new + regression)
4. **DoD items covered**
5. **Exact commit message** in format: `type(scope): description`

## Kadima commit scopes
`engine | pipeline | api | ui | data | config | docker | ci | kb | llm | annotation | validation`

## Non-negotiables
- Do not merge patches. Keep them small and testable.
- PATCH-01 must not break existing `pytest tests/ -v`
- Each patch must be independently reviewable
- ML imports always in `try/except ImportError`
- No hardcoded secrets, paths, or CUDA calls without capability check

## Output format

```
### PATCH-01 — <title>

**Files:**
- MODIFY `kadima/...`
- CREATE `kadima/...`

**Edits:**
1. In `file.py`, add/change ...

**Tests:**
```bash
pytest tests/engine/test_<module>.py -v
pytest tests/ -v  # regression
```

**DoD:**
- [ ] ...

**Commit:** `feat(engine): ...`
```
