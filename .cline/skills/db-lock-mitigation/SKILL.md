---
name: db-lock-mitigation
description: Use this skill when a Kadima operation writes frequently to SQLite, or when OperationalError 'database is locked' is observed. Implements three-layer defense: busy_timeout, retry decorator with exponential backoff, and write batching with chunked commits. No modal spam — log transient locks only.
---

# SQLite "database is locked" Defenses

## When to use
- Any long operation writing frequently to SQLite
- Any worker updating many rows (corpus processing, pipeline runs)
- Observed `OperationalError: database is locked`
- Adding new workers that share the DB with UI

## Three-layer defense

### Layer 1 — Connection-level busy_timeout
```python
# In kadima/data/db.py (or wherever connections are created)
conn.execute("PRAGMA busy_timeout = 5000")  # 5 seconds
```
Apply to **all** connections: main thread, workers, test fixtures.

### Layer 2 — retry_on_db_locked decorator
```python
import functools
import time
import sqlite3

def retry_on_db_locked(max_retries: int = 3, base_delay: float = 0.1):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except sqlite3.OperationalError as e:
                    if "database is locked" not in str(e):
                        raise
                    if attempt == max_retries - 1:
                        raise
                    delay = base_delay * (2 ** attempt)
                    logger.warning("DB locked, retry %d/%d in %.2fs", attempt+1, max_retries, delay)
                    time.sleep(delay)
        return wrapper
    return decorator
```

### Layer 3 — Write batching + chunked commits
```python
# Instead of: for row in rows: conn.execute(UPDATE...); conn.commit()
# Do:
CHUNK = 200
for i in range(0, len(rows), CHUNK):
    chunk = rows[i:i+CHUNK]
    for row in chunk:
        conn.execute("UPDATE ...", (...,))
    conn.commit()  # commit per chunk, not per row
```

## UI policy (no modal spam)
- Transient lock warnings → activity log only (`logger.warning`)
- Show one final summary error only if unrecoverable after all retries

## Tests to add
- Unit test: `retry_on_db_locked` retries N times then raises
- Unit test: retries on "database is locked", not on other OperationalErrors
- Integration test (optional): second connection holding lock while first retries

## Output format
- Changes to `kadima/data/db.py` or relevant connection factory
- `retry_on_db_locked` decorator (new utility or inline)
- Worker changes (chunked writes)
- Test commands:
  ```bash
  pytest tests/data/ -v
  pytest tests/ -v
  ```
