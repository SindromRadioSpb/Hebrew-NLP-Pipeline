---
name: deterministic-scoring-canonical-layer
description: Use this skill when implementing single-source-of-truth tables in Kadima (KB canonical terms, translation memory global layer, term deduplication). Implements deterministic scoring tuple for candidate selection, upsert that only overwrites if new candidate wins, propagation to linked rows, and idempotent backfill.
---

# Canonical Layer Scoring + Propagation

## When to use
Implementing "single source of truth" tables:
- KB canonical terms (`kb_terms` deduplication)
- Translation Memory global layer (Phase S: `tm_global`)
- Term clustering results propagation
- Cross-corpus term normalization

## Deterministic scoring tuple

Candidates are compared by this tuple (higher wins):

```python
from dataclasses import dataclass
from datetime import datetime

@dataclass(order=True)
class CandidateScore:
    has_definition: bool        # 1 wins over 0
    status_rank: int            # approved=3 > reviewed=2 > pending=1 > rejected=0
    origin_rank: int            # manual=3 > ml=2 > auto=1
    updated_at: datetime        # more recent wins
    id: int                     # lowest id wins (stable tie-breaker, reversed: negate)

    def __lt__(self, other):    # implement if not using dataclass order
        ...
```

## Upsert pattern

```python
def upsert_canonical(conn, key: str, candidate: dict) -> bool:
    """Insert or update only if candidate wins over existing. Returns True if updated."""
    existing = conn.execute(
        "SELECT * FROM canonical WHERE key = ?", (key,)
    ).fetchone()

    if existing is None:
        conn.execute("INSERT INTO canonical (...) VALUES (?,...)", (...,))
        return True

    existing_score = score_from_row(existing)
    candidate_score = score_from_row(candidate)

    if candidate_score > existing_score:
        conn.execute("UPDATE canonical SET ... WHERE key = ?", (..., key))
        _propagate(conn, key, candidate)
        return True

    return False
```

## Propagation

After canonical row is updated, propagate required fields to all linked rows:

```python
def _propagate(conn, canonical_key: str, new_values: dict) -> None:
    conn.execute(
        "UPDATE linked_table SET field = ? WHERE canonical_key = ?",
        (new_values["field"], canonical_key)
    )
```

## Backfill

```python
def backfill_canonical(conn, chunk_size: int = 500, dry_run: bool = False):
    """Group by canonical key, create canonical rows, link all, propagate initial values."""
    offset = 0
    while True:
        rows = conn.execute(
            "SELECT * FROM source ORDER BY id LIMIT ? OFFSET ?",
            (chunk_size, offset)
        ).fetchall()
        if not rows:
            break
        for row in rows:
            upsert_canonical(conn, row["key"], row)
        if not dry_run:
            conn.commit()
        offset += chunk_size
```

## Tests (required)

```python
def test_higher_score_wins():
    # candidate with status=approved beats existing with status=pending

def test_lower_score_loses():
    # candidate with status=pending does not overwrite existing approved

def test_propagation_updates_linked_rows():
    # after upsert, all rows with canonical_key have updated field

def test_backfill_idempotent():
    # run twice → same state, no duplication
```

```bash
pytest tests/kb/ -v
pytest tests/ -v
```
