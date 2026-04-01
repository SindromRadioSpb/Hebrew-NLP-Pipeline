---
name: large-export-atomic-cancel
description: Use this skill for large data exports from Kadima (terms to CSV/TBX/TMX/CoNLL-U, corpus export, validation results). Implements chunked DB fetch, incremental write, atomic temp-file-replace, cancel between chunks, progress dialog with stage/speed/ETA, no UI freeze.
---

# Large Export with Atomic Write + Cancel

## When to use
Exporting large filtered datasets from SQLite:
- Terms export (CSV / JSON / TBX / TMX / CoNLL-U) from `corpus/exporter.py`
- Validation results export from `validation/report.py`
- KB terms export
- Any export > 1000 rows

## Design

```
UI thread                          Worker thread (QThreadPool)
─────────────────────────────────────────────────────────
ExportButton.clicked                MyExportWorker.run()
  → ExportWorker(filter, format)      → chunked SELECT (1000 rows)
  → worker.signals.progress.connect     → write to temp file
  → pool.start(worker)                  → cancel check between chunks
                                        → atomic replace on finish
                                        → emit finished(output_path)
```

## Worker template

```python
import os
import tempfile

class ExportWorker(QRunnable):
    def run(self):
        self.signals.started.emit()
        # Atomic write: temp file first
        tmp_fd, tmp_path = tempfile.mkstemp(
            suffix=f".{self._format}",
            dir=os.path.dirname(self._output_path)
        )
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as fh:
                self._write_header(fh)
                offset = 0
                total = self._count_rows()
                while True:
                    if self._cancel:
                        self.signals.activity.emit("Export cancelled.")
                        return  # temp file abandoned (cleaned in finally)
                    rows = self._fetch_chunk(offset, CHUNK=1000)
                    if not rows:
                        break
                    self._write_rows(fh, rows)
                    offset += len(rows)
                    pct = min(100, int(offset * 100 / total)) if total else 0
                    self.signals.progress.emit(pct, f"Exported {offset}/{total}")
            # Atomic replace: only if fully written
            os.replace(tmp_path, self._output_path)
            self.signals.finished.emit(self._output_path)
        except Exception as exc:
            self.signals.failed.emit(str(exc))
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)  # clean temp on cancel or error
                except OSError:
                    pass
```

## Format handlers in Kadima
- `corpus/exporter.py` already handles CSV / JSON / TBX / TMX / CoNLL-U
- Reuse `Exporter.export(corpus_id, format, output_path)` — do not duplicate

## Tests (required)

```python
def test_export_small_fixture_creates_file():
    # export 10 rows → file exists, headers present

def test_cancel_mid_run_cleans_temp_file():
    # cancel after first chunk → output file absent, temp file absent

def test_export_is_atomic():
    # output_path absent until export fully complete
```

```bash
pytest tests/corpus/ -v -k export
pytest tests/ -v
```
