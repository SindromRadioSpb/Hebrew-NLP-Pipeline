# Database Migrations

## How It Works

KADIMA uses **forward-only SQL migrations** tracked in a `_migrations` table.

```
kadima/data/migrations/
├── 001_initial.sql      ← Core tables (corpora, documents, tokens, terms, ...)
├── 002_annotation.sql   ← Label Studio integration
├── 003_kb.sql           ← Knowledge Base
├── 004_llm.sql          ← LLM conversations
├── 005_<your_name>.sql  ← Next migration
```

## Creating a Migration

### Option A: Generator (recommended)

```bash
kadima migrate --new add_user_table
# → kadima/data/migrations/005_add_user_table.sql
```

Edit the generated file, then apply:

```bash
kadima migrate
```

### Option B: Manual

1. Find the next number: `ls kadima/data/migrations/`
2. Create `XXX_descriptive_name.sql`

## Writing Migrations

### Rules

1. **Idempotent** — use `IF NOT EXISTS` / `IF EXISTS`
2. **Forward-only** — no rollback support; plan accordingly
3. **Non-destructive** — never `DROP TABLE` without backup logic
4. **Single concern** — one logical change per file
5. **No data migration in SQL** — use Python for complex data transforms

### Template

```sql
-- 005_add_user_table.sql
-- Migration: Add user table for auth
-- Issue: #42

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
```

### Adding a Column

```sql
-- 006_add_embedding_version.sql
-- Add version tracking for embeddings

-- SQLite: no ALTER COLUMN, only ADD COLUMN
ALTER TABLE kb_terms ADD COLUMN embedding_model TEXT DEFAULT 'neodictabert';
ALTER TABLE kb_terms ADD COLUMN embedding_dim INTEGER DEFAULT 768;
```

### Adding an Index

```sql
-- 007_perf_indexes.sql
-- Performance: add missing indexes

CREATE INDEX IF NOT EXISTS idx_terms_canonical_freq ON terms(canonical, freq DESC);
CREATE INDEX IF NOT EXISTS idx_lemmas_pos ON lemmas(pos);
```

## Applying Migrations

Migrations run automatically at every startup:

- `kadima run` → applies pending migrations
- `kadima gui` → applies pending migrations
- `kadima api` → applies pending migrations
- `kadima init` → applies all migrations (first-time setup)

Manual apply:

```bash
kadima migrate
```

Check status:

```bash
kadima migrate --status
# Schema version: 004_llm.sql
```

## What NOT To Do

| ❌ Don't | ✅ Do instead |
|----------|--------------|
| `DROP TABLE` | Keep old tables; clean up in a later migration |
| Edit an applied migration | Create a new migration to fix |
| Skip numbers | Always use next sequential number |
| Mix concerns | One table/index/alter per file |
| Use `DELETE FROM` | Use Python for data migrations |
| Forget `IF NOT EXISTS` | Always guard DDL |

## Troubleshooting

**Migration failed:**
```
ERROR - Migration 005_foo.sql failed: duplicate column name
```
→ The migration was partially applied. Check `_migrations` table:
```sql
SELECT * FROM _migrations;
```
If it's NOT listed, the migration was rolled back — fix the SQL and retry.
If it IS listed, the SQL needs to be idempotent (`ALTER TABLE ... ADD COLUMN IF NOT EXISTS`).

**Schema version stuck:**
```bash
kadima migrate --status
# → Shows latest applied migration
```

**Need to rebuild from scratch:**
```bash
rm ~/.kadima/kadima.db
kadima init
```
