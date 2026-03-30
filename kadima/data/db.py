# kadima/data/db.py
"""SQLite connection + migration runner."""

import os
import re
import sqlite3
import logging
from pathlib import Path
from typing import Optional, List

logger = logging.getLogger(__name__)

MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "migrations")
MIGRATION_PATTERN = re.compile(r"^(\d{3})_(.+)\.sql$")


def get_connection(db_path: str) -> sqlite3.Connection:
    """Получить соединение с БД. Создаёт директорию если нужно.

    Always applies WAL + foreign_keys. Run migrations before first use.
    """
    db_path = os.path.expanduser(db_path)
    Path(os.path.dirname(db_path)).mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn


def get_applied_migrations(conn: sqlite3.Connection) -> set:
    """Вернуть множество имён применённых миграций."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS _migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL UNIQUE,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    return set(row[0] for row in conn.execute("SELECT filename FROM _migrations").fetchall())


def get_pending_migrations(applied: set) -> List[str]:
    """Вернуть список .sql файлов, которые ещё не применены (sorted)."""
    if not os.path.isdir(MIGRATIONS_DIR):
        return []
    all_files = sorted(f for f in os.listdir(MIGRATIONS_DIR) if f.endswith(".sql"))
    return [f for f in all_files if f not in applied]


def run_migrations(db_path: str) -> int:
    """Выполнить все SQL-миграции по порядку.

    Args:
        db_path: Path to SQLite database.

    Returns:
        Number of migrations applied in this run.

    Raises:
        Exception: If any migration fails (rolled back).
    """
    db_path = os.path.expanduser(db_path)
    conn = get_connection(db_path)

    applied = get_applied_migrations(conn)
    pending = get_pending_migrations(applied)
    count = 0

    for filename in pending:
        filepath = os.path.join(MIGRATIONS_DIR, filename)
        logger.info("Applying migration: %s", filename)

        with open(filepath, "r", encoding="utf-8") as f:
            sql = f.read()

        try:
            conn.executescript(sql)
            conn.execute("INSERT INTO _migrations (filename) VALUES (?)", (filename,))
            conn.commit()
            count += 1
            logger.info("Migration %s applied successfully", filename)
        except Exception as e:
            conn.rollback()
            logger.error("Migration %s failed: %s", filename, e, exc_info=True)
            raise

    if count:
        logger.info("Applied %d migration(s) to %s", count, db_path)
    else:
        logger.debug("No pending migrations for %s", db_path)

    conn.close()
    return count


def ensure_db(db_path: str) -> None:
    """Гарантировать что БД существует и все миграции применены.

    Вызывать при каждом старте (API, GUI, CLI).
    Идемпотентен — повторные вызовы безопасны.
    """
    applied = run_migrations(db_path)
    if applied:
        logger.info("Database ready (%d new migrations applied)", applied)


def get_schema_version(db_path: str) -> str:
    """Вернуть имя последней применённой миграции (или 'empty')."""
    db_path = os.path.expanduser(db_path)
    if not os.path.exists(db_path):
        return "no_db"
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT filename FROM _migrations ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return row[0] if row else "empty"
    except Exception:
        return "unknown"
    finally:
        conn.close()


def generate_migration(name: str) -> str:
    """Создать файл миграции с авто-инкрементным номером.

    Args:
        name: Descriptive name (e.g. 'add_user_table').

    Returns:
        Path to created file.
    """
    if not MIGRATION_PATTERN.match(f"000_{name}.sql"):
        raise ValueError(
            f"Invalid migration name '{name}'. "
            "Use lowercase with underscores (e.g. 'add_user_table')"
        )

    if not os.path.isdir(MIGRATIONS_DIR):
        os.makedirs(MIGRATIONS_DIR, exist_ok=True)

    existing = sorted(f for f in os.listdir(MIGRATIONS_DIR) if f.endswith(".sql"))
    if existing:
        last = existing[-1]
        last_num = int(MIGRATION_PATTERN.match(last).group(1))
        next_num = last_num + 1
    else:
        next_num = 1

    filename = f"{next_num:03d}_{name}.sql"
    filepath = os.path.join(MIGRATIONS_DIR, filename)

    template = f"""-- {filename}
-- Migration: {name.replace('_', ' ')}
-- Created: auto-generated

-- TODO: Add migration SQL here
-- Use CREATE TABLE IF NOT EXISTS / ALTER TABLE / CREATE INDEX IF NOT EXISTS
-- Do NOT use DROP TABLE or destructive operations without backup logic

"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(template)

    logger.info("Created migration: %s", filepath)
    return filepath
