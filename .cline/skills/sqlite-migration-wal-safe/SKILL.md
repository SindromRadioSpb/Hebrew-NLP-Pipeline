---
name: sqlite-migration-wal-safe
description: Use this skill for any Kadima schema change: new tables, columns, indexes, triggers. Creates additive WAL-safe migrations in kadima/data/migrations/ with correct naming, safe defaults, indexes, and a migration test. Never creates tables in code.
---

# WAL-safe SQLite Migrations

## When to use
Any schema change: new tables, columns, indexes, triggers, constraints.

## Kadima migration rules
- Files go in `kadima/data/migrations/` named `00N_description.sql`
- Current migrations: 001_initial, 002_annotation, 003_kb, 004_llm
- Next migration number: `005_<name>.sql`
- **Never** `CREATE TABLE` in Python code — migrations only
- Applied via `kadima migrate` CLI command

## Objective
Create additive, idempotent migrations with low risk:
- `CREATE TABLE IF NOT EXISTS`
- `ALTER TABLE ADD COLUMN` (SQLite: one column per statement)
- indexes for FK columns and expected query patterns
- safe defaults and CHECK constraints
- WAL-compatible (no long exclusive locks)

## Steps

1. Create migration SQL file:
   ```sql
   -- kadima/data/migrations/005_example.sql
   CREATE TABLE IF NOT EXISTS example (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
       ...
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );
   CREATE INDEX IF NOT EXISTS idx_example_field ON example(field);
   ```

2. Update SQLAlchemy models if ORM is used (`kadima/data/sa_models.py` or equivalent)

3. Update DTOs / dataclasses if relevant

4. Add migration smoke test:
   - confirms table exists
   - confirms columns exist
   - confirms basic insert/select works

5. Update `CLAUDE.md` Database section with new migration entry

## Output format
- Migration SQL file content (complete)
- Model/DTO changes (if any)
- Test commands
- DoD evidence steps:
  ```bash
  kadima migrate
  kadima --self-check db_open
  kadima --self-check migrations
  pytest tests/ -v
  ```

## WAL-specific constraints
- No `BEGIN EXCLUSIVE` in migration
- Keep migrations short — no bulk data operations
- `PRAGMA journal_mode=WAL` already set by `kadima/data/db.py`
- `PRAGMA foreign_keys=ON` — FK references must be valid at migration time
