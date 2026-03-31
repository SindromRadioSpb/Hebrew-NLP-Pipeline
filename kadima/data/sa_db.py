# kadima/data/sa_db.py
"""R-2.6: SQLAlchemy engine and session management for KADIMA.

Provides both sync and async session factories.
Coexists with the legacy sqlite3 layer (db.py) for backward compatibility.

Usage (sync):
    from kadima.data.sa_db import get_engine, get_session_factory
    engine = get_engine(db_path)
    Session = get_session_factory(engine)
    with Session() as session:
        ...

Usage (async, R-2.7):
    from kadima.data.sa_db import get_async_engine, get_async_session_factory
    engine = get_async_engine(db_path)
    AsyncSession = get_async_session_factory(engine)
    async with AsyncSession() as session:
        ...
"""

import logging
import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import Engine, event, text
from sqlalchemy import create_engine as sa_create_engine
from sqlalchemy.orm import Session, sessionmaker

logger = logging.getLogger(__name__)

# ── Sync engine ──────────────────────────────────────────────────────────────


def get_engine(db_path: str) -> Engine:
    """Create a SQLAlchemy sync engine for SQLite WAL.

    Applies WAL journal mode and foreign_keys ON at connection time,
    matching the behaviour of the legacy get_connection() in db.py.

    Args:
        db_path: Absolute or relative path to the SQLite database file.

    Returns:
        SQLAlchemy Engine configured for WAL mode.
    """
    db_path = os.path.expanduser(db_path)
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)

    engine = sa_create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
        echo=False,
    )

    @event.listens_for(engine, "connect")
    def _set_pragmas(dbapi_conn: object, _: object) -> None:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    logger.debug("SQLAlchemy sync engine created for: %s", db_path)
    return engine


def get_session_factory(engine: Engine) -> sessionmaker:
    """Return a sessionmaker bound to the given engine.

    Args:
        engine: SQLAlchemy Engine.

    Returns:
        sessionmaker instance for creating Session objects.
    """
    return sessionmaker(bind=engine, expire_on_commit=False)


@contextmanager
def get_session(db_path: str) -> Generator[Session, None, None]:
    """Context manager: create engine + session, commit on exit, rollback on error.

    Args:
        db_path: Path to SQLite database file.

    Yields:
        SQLAlchemy Session.
    """
    engine = get_engine(db_path)
    Session = get_session_factory(engine)
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db(db_path: str) -> None:
    """Create all tables defined in sa_models.Base.metadata.

    Idempotent: uses CREATE TABLE IF NOT EXISTS semantics via checkfirst=True.
    For production use, prefer Alembic migrations.

    Args:
        db_path: Path to SQLite database file.
    """
    from kadima.data.sa_models import Base

    engine = get_engine(db_path)
    Base.metadata.create_all(engine, checkfirst=True)
    logger.info("SQLAlchemy tables initialised at: %s", db_path)


# ── Async engine (R-2.7) ─────────────────────────────────────────────────────


def get_async_engine(db_path: str) -> "AsyncEngine":  # type: ignore[name-defined]
    """Create a SQLAlchemy async engine for SQLite WAL (aiosqlite).

    Args:
        db_path: Absolute or relative path to the SQLite database file.

    Returns:
        AsyncEngine configured for WAL mode.
    """
    from sqlalchemy.ext.asyncio import create_async_engine

    db_path = os.path.expanduser(db_path)
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)

    engine = create_async_engine(
        f"sqlite+aiosqlite:///{db_path}",
        connect_args={"check_same_thread": False},
        echo=False,
    )

    @event.listens_for(engine.sync_engine, "connect")
    def _set_pragmas(dbapi_conn: object, _: object) -> None:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    logger.debug("SQLAlchemy async engine created for: %s", db_path)
    return engine


def get_async_session_factory(engine: "AsyncEngine") -> "async_sessionmaker":  # type: ignore[name-defined]
    """Return an async_sessionmaker bound to the async engine.

    Args:
        engine: AsyncEngine.

    Returns:
        async_sessionmaker for creating AsyncSession objects.
    """
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    return async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
