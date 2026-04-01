---
name: premium-operation-progress-ux
description: Use this skill when Kadima progress UX feels hung or shows only a bottom bar. Implements or reuses a premium OperationProgressDialog with stage label, done/total/percent, elapsed, speed, ETA, counters, bounded activity log, cancel, and optional pause/resume. No modal spam — one final summary dialog only.
---

# Premium Operation Progress UX

## When to use
- Progress UX is "a bottom bar" and feels hung
- User trust depends on visibility of what's happening
- Adding new long operations (TTS batch, STT transcription, corpus import)
- Any generative module batch operation

## Target dialog spec

```
┌─────────────────────────────────────────────────────┐
│ Processing corpus: "Example"                [Stage 2/3] │
├─────────────────────────────────────────────────────┤
│ ████████████████░░░░░░░░  1 247 / 3 000  (41%)      │
│ Elapsed: 00:01:23   Speed: 15 items/s   ETA: ~02:10 │
├─────────────────────────────────────────────────────┤
│ OK: 1 240  SKIP: 7  FAILED: 0                       │
├─────────────────────────────────────────────────────┤
│ [Activity log — last 8 lines, auto-scroll]          │
│ > M3 morphology: "מחשב" → NOUN                      │
│ > M4 n-gram: 3-gram extracted                       │
├─────────────────────────────────────────────────────┤
│           [Pause]           [Cancel]                │
└─────────────────────────────────────────────────────┘
```

## Implementation guidelines

### Reuse before creating
Check `kadima/ui/` for existing progress components before creating new ones.
Prefer generalizing `PipelineWorker`'s existing progress signals.

### Signal contract (worker side)
```python
progress = pyqtSignal(int, str)     # (percent_0_100, stage_label)
activity = pyqtSignal(str)          # single log line
counters = pyqtSignal(dict)         # {"ok": N, "skip": N, "failed": N}
```

### Dialog responsibilities
- Bounded activity log: keep last 50–100 lines max (use `collections.deque`)
- Speed: rolling average over last 10 progress updates
- ETA: `remaining_items / avg_speed` — show "—" if < 3 data points
- Determinate mode: show progress bar
- Indeterminate mode: pulse bar (for initial load, unknown total)
- Final summary: show once on `finished` signal (not during run)

### Timing format
```python
def format_duration(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h: return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"
```

## Non-negotiables
- No UI freeze: dialog lives in main thread, worker in QThreadPool
- No modal spam: aggregate warnings in log, single summary at end
- Cancel button wired to `worker.cancel()` flag
- objectName format: `<operation>_progress_<widget>` e.g. `pipeline_progress_cancel_button`

## Tests
- Unit test for speed/ETA calculation logic
- Unit test for bounded log (deque overflow)
- Smoke: worker emits 100 progress signals, dialog updates without crash

```bash
pytest tests/ui/ -v -k progress
```
