---
name: pause-resume-checkpoint
description: Use this skill when a long Kadima operation (e.g., pipeline run on large corpus, TTS batch synthesis, STT transcription batch) must be safely pausable and resumable. Implements checkpoint persistence in DB, deterministic ordering, params compatibility check, and tests proving pause+resume equals uninterrupted run.
---

# Pause/Resume with Deterministic Checkpointing

## When to use
Long operations that must be pausable/resumable safely:
- Pipeline run on large corpus (`pipeline/orchestrator.py`)
- TTS batch synthesis (M15)
- STT transcription batch (M16)
- NER training pipeline

## Design principles

1. **Safe boundary**: pause at end of chunk, never mid-document
2. **Persistent checkpoint**: store in DB (not in memory)
3. **Params compatibility**: resume only if same config hash
4. **Deterministic equivalence**: pause+resume produces identical results to uninterrupted run

## Checkpoint DB table (add via migration)

```sql
CREATE TABLE IF NOT EXISTS operation_checkpoints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operation_key TEXT NOT NULL UNIQUE,   -- e.g. "pipeline:corpus_id:42"
    cursor INTEGER NOT NULL DEFAULT 0,    -- last processed item ID or offset
    total INTEGER,
    params_hash TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'paused', -- paused | completed | cancelled
    counters TEXT,                         -- JSON: {"ok": N, "skip": N, "failed": N}
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Worker logic

```python
def run(self):
    checkpoint = self._load_checkpoint()
    if checkpoint:
        if checkpoint["params_hash"] != self._params_hash():
            self.signals.activity.emit("Params changed — cannot resume. Start fresh.")
            self._clear_checkpoint()
            return
        cursor = checkpoint["cursor"]
        self.signals.activity.emit(f"Resuming from item {cursor}")
    else:
        cursor = 0

    items = self._get_items_from(cursor)  # ORDER BY id, deterministic
    for item in items:
        if self._pause_requested:
            self._save_checkpoint(cursor=item.id, status="paused")
            self.signals.activity.emit(f"Paused at item {item.id}")
            return
        if self._cancel:
            self._clear_checkpoint()
            return
        self._process(item)
        cursor = item.id
        # save checkpoint after each chunk
        if self._chunk_counter % CHUNK_SIZE == 0:
            self._save_checkpoint(cursor=cursor, status="paused")
            conn.commit()

    self._save_checkpoint(cursor=cursor, status="completed")
    self.signals.finished.emit(self._result)
```

## params_hash
```python
import hashlib, json

def _params_hash(self) -> str:
    config = {"corpus_id": self.corpus_id, "modules": sorted(self.modules), ...}
    return hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()[:16]
```

## Incompatibility handling
- Offer "Start new run" button (never reuse silently)
- Archive old checkpoint before clearing (log to activity)

## Tests (required)
```python
def test_pause_resume_equals_uninterrupted():
    # Run on N items, pause at N/2, resume → same final result as one full run

def test_params_mismatch_blocks_resume():
    # Save checkpoint with params_hash A, attempt resume with hash B → rejected

def test_checkpoint_idempotent():
    # Resume twice from same checkpoint → no duplication
```

```bash
pytest tests/integration/ -v -k checkpoint
pytest tests/ -v
```
