# Kadima Skills Pack — Premium Python/PyQt6/SQLite

Skills for disciplined development of the Kadima Hebrew NLP platform.
Ported from `V_book/.claude/skills/premium_desktop_pyqt_sqlite/`.

## Workflow

```
1. repo-audit-map          → mandatory first step for any change
2. patch-series-planner    → plan PATCH-01..N for features > 30 lines
3. <specialized skill>     → apply as needed
4. docs-dod-evidence-runbook → always for non-trivial features
```

## Skill Index

| Skill | When to use |
|-------|-------------|
| `repo-audit-map` | Before any change — map entry points, risks, tests |
| `patch-series-planner` | Feature > 30 lines — PATCH-01..N plan with DoD |
| `sqlite-migration-wal-safe` | Any schema change in `kadima/data/migrations/` |
| `idempotent-backfill-script` | New canonical layers, derived data, linking columns |
| `db-lock-mitigation` | OperationalError: database is locked; frequent writes |
| `qt-worker-signal-contract` | Any long UI operation (pipeline, export, TTS, STT) |
| `premium-operation-progress-ux` | Progress UX upgrade; new long operations |
| `pause-resume-checkpoint` | Large corpus runs, TTS/STT batch — must be pausable |
| `deterministic-scoring-canonical-layer` | KB dedup, TM global layer, term normalization |
| `large-export-atomic-cancel` | CSV/TBX/TMX/CoNLL-U exports > 1000 rows |
| `security-hardening-guardrails` | File paths, SQL, user inputs, API keys |
| `release-packaging-smoke` | New modules/migrations/deps → Docker build + smoke |
| `docs-dod-evidence-runbook` | Any premium feature — design doc + runbook + DoD |

## Non-negotiables (all skills)
- No guessing: confirm invariants in code before proposing changes
- Minimal diffs: each patch independently buildable + testable
- SQLite WAL: short writes, no long exclusive locks
- No modal spam: aggregate warnings, single final summary
- ML imports: always `try/except ImportError` with actionable message
- CUDA: always `torch.cuda.is_available()` before `.to("cuda")`
