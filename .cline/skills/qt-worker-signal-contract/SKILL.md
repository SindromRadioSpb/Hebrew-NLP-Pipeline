---
name: qt-worker-signal-contract
description: Use this skill for any long Kadima operation invoked from UI: NLP pipeline processing, corpus import, export, generative module calls, annotation sync. Standardizes QRunnable worker behavior — non-blocking UI, typed signals, cancellation flag, DB session per worker, throttled progress updates.
---

# QThread/Worker Signal Contract (non-blocking UI)

## When to use
Any long operation invoked from UI:
- NLP pipeline runs (`PipelineWorker`)
- Generative module calls (`GenerativeWorker`)
- Corpus import/export
- Annotation sync, Label Studio operations
- KB embedding search or clustering

## Standard worker pattern in Kadima

```python
from PyQt6.QtCore import QRunnable, QObject, pyqtSignal, QThreadPool

class _WorkerSignals(QObject):
    started = pyqtSignal()
    progress = pyqtSignal(int, str)   # (percent, stage_name)
    activity = pyqtSignal(str)        # log line
    finished = pyqtSignal(object)     # result payload
    failed = pyqtSignal(str)          # error message

class MyWorker(QRunnable):
    def __init__(self, ...):
        super().__init__()
        self.signals = _WorkerSignals()
        self._cancel = False           # thread-safe flag (simple bool for single-writer)

    def cancel(self) -> None:
        self._cancel = True

    def run(self) -> None:
        self.signals.started.emit()
        try:
            for i, item in enumerate(items):
                if self._cancel:
                    self.signals.activity.emit("Cancelled.")
                    return
                # do work
                if i % THROTTLE == 0:  # emit every N items, not every item
                    self.signals.progress.emit(pct, f"Processing {i}/{total}")
            self.signals.finished.emit(result)
        except Exception as exc:
            logger.error("Worker failed: %s", exc, exc_info=True)
            self.signals.failed.emit(str(exc))
```

## Non-negotiables
- **Never** touch UI widgets from `run()` — signals only
- Cancellation flag polled at safe boundaries (end of chunk, not mid-operation)
- DB: one `sqlite3.connect()` per worker run, `conn.close()` in `finally`
- Throttle progress signals: emit every 50–200 items, not every row
- `QThreadPool.globalInstance().start(worker)` — never `worker.run()` directly

## VRAM-aware workers (generative modules)
- Check `torch.cuda.is_available()` before `.to("cuda")`
- Wrap ML imports in `try/except ImportError` with actionable message
- Emit `activity` signal with backend being used: `"Using XTTS (cuda)"`

## Output format
- Worker class (signals + run + cancel)
- UI wiring in view: `worker.signals.finished.connect(...)` etc.
- Test or smoke: verify worker completes without blocking event loop
  ```bash
  pytest tests/ui/test_<view>.py -v -k worker
  pytest tests/ -v
  ```
