---
name: idempotent-backfill-script
description: Use this skill when introducing new canonical layers, linking columns, or derived data in Kadima that requires backfilling existing DB rows. Creates a CLI backfill script with --dry-run, chunked processing, deterministic ordering, and safe re-run guarantees.
---

# Idempotent Backfill Script

## When to use
When introducing new canonical layers, linking columns, or new derived data that requires
populating existing rows. Common in Kadima: backfilling KB embeddings, linking terms to
corpora, populating new derived columns after a migration.

## Objective
Idempotent backfill with:
- `--dry-run` mode (print what would change, touch nothing)
- chunked processing (default 500 rows)
- deterministic ordering (stable ORDER BY)
- final summary: created/updated/linked/skipped/errors
- safe re-runs (no duplication, no corruption)

## Script template structure

```python
#!/usr/bin/env python3
"""Backfill <description>.

Usage:
  python scripts/backfill_<name>.py [--dry-run] [--db-path PATH] [--chunk-size N]
"""
import argparse
import sqlite3

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--db-path", default="~/.kadima/kadima.db")
    p.add_argument("--chunk-size", type=int, default=500)
    return p.parse_args()

def backfill(conn, dry_run: bool, chunk_size: int) -> dict:
    stats = {"created": 0, "updated": 0, "skipped": 0, "errors": 0}
    offset = 0
    while True:
        rows = conn.execute(
            "SELECT id, ... FROM ... ORDER BY id LIMIT ? OFFSET ?",
            (chunk_size, offset)
        ).fetchall()
        if not rows:
            break
        for row in rows:
            try:
                # deterministic logic here
                if <already_done>(row):
                    stats["skipped"] += 1
                    continue
                if not dry_run:
                    conn.execute("UPDATE ...", (..., row["id"]))
                stats["updated"] += 1
            except Exception as e:
                stats["errors"] += 1
                print(f"ERROR row {row['id']}: {e}")
        if not dry_run:
            conn.commit()
        offset += chunk_size
    return stats

def main():
    args = parse_args()
    db_path = os.path.expanduser(args.db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    stats = backfill(conn, args.dry_run, args.chunk_size)
    conn.close()
    print(f"Done: {stats}")
    if args.dry_run:
        print("[DRY RUN — no changes written]")

if __name__ == "__main__":
    main()
```

## Tests to add
- backfill is idempotent: run twice → same results, stats["created"] == 0 on second run
- partial backfill then resume → correct final state
- `--dry-run` touches nothing in DB

## Output format
- script file content
- test file
- commands to run
- DoD evidence:
  ```bash
  python scripts/backfill_<name>.py --dry-run
  python scripts/backfill_<name>.py
  python scripts/backfill_<name>.py  # second run — must show 0 created
  ```
