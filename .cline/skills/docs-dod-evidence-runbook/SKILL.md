---
name: docs-dod-evidence-runbook
description: Use this skill for any Kadima premium feature, complex UX, pause/resume, or new migration. Writes design doc with architecture and failure modes, runbook with how to run/resume/recover, troubleshooting guide, and DoD evidence checklist with manual smoke steps and expected outputs.
---

# Docs + DoD Evidence + Runbook

## When to use
- Any new engine module (M13-M25)
- Complex UI features (pause/resume, multi-step operations)
- New migrations or schema changes
- New API vertical slices
- Before marking any feature as "done"

## Artifacts to produce

### 1. Design doc (inline in CLAUDE.md or separate `docs/<feature>.md`)

Structure:
```markdown
## Design: <Feature Name>

### Architecture
- What components are involved
- Data flow: input → processing → output
- Storage: what goes in DB, what is transient

### Invariants
- What must always be true
- What is guaranteed by the implementation

### Failure modes
- What can go wrong and how it's handled
- Graceful degradation behavior
- What is logged vs what raises
```

### 2. Runbook

```markdown
## Runbook: <Feature Name>

### How to run
```bash
# example commands
```

### How to resume / recover
- If interrupted: ...
- If checkpoint exists: ...
- If params changed: ...

### How to diagnose
```bash
kadima --self-check health
# check logs at: ~/.kadima/logs/kadima.log
```
```

### 3. Troubleshooting

```markdown
## Troubleshooting

### "database is locked"
- Cause: long write overlapping with UI read
- Fix: increase PRAGMA busy_timeout; check for uncommitted transactions

### "Module X unavailable"
- Cause: optional ML dependency not installed
- Fix: pip install -e ".[ml]" or pip install -e ".[gpu]"

### "No CUDA device"
- Cause: torch not built with CUDA or no GPU
- Fix: works on CPU with fallback; install GPU extras for acceleration
```

### 4. DoD evidence checklist

```markdown
## DoD Evidence: <Feature Name>

### P1 — Functional
- [ ] Feature works per acceptance criteria (describe test)
- [ ] `pytest tests/<path> -v` — all PASS
- [ ] Empty input returns FAILED status, no crash
- [ ] Invalid input returns False from validate_input, no crash

### P2 — Regression
- [ ] `pytest tests/ -v` — no regressions
- [ ] `ruff check kadima/` — 0 errors
- [ ] `kadima --self-check import` — passes

### P3 — Docs/Security
- [ ] CLAUDE.md updated (module map / endpoint table / migration table)
- [ ] No hardcoded secrets or paths
- [ ] ML imports wrapped in try/except ImportError
- [ ] CUDA check: torch.cuda.is_available() before .to("cuda")
```

## Output format
Return:
- List of doc files created/updated with content summary
- Full DoD checklist (filled in, not template)
- Manual smoke steps with expected log lines/outputs
- Diagnostic commands:
  ```bash
  kadima --self-check health
  pytest tests/<specific>/ -v
  python -c "from kadima.engine.<module> import <Class>; print('OK')"
  ```
