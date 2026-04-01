# kadima/cli.py
"""CLI entrypoint для KADIMA.

Использование:
    kadima gui                    — запустить PyQt UI
    kadima run --corpus ID        — запустить pipeline на корпусе
    kadima run --text "טקסט"      — запустить pipeline на одном тексте
    kadima api                    — запустить FastAPI сервер
    kadima --init                 — инициализация (~/.kadima/ с config и DB)
    kadima --version              — версия
    kadima --self-check import    — проверить импорты всех модулей → JSON
    kadima --self-check db_open   — открыть/закрыть DB → JSON
    kadima --self-check health    — проверить модели и провайдеры → JSON
    kadima --self-check migrations — проверить версию схемы → JSON
"""

import argparse
import logging
import os
import sys
from pathlib import Path

import yaml

KADIMA_HOME = os.environ.get("KADIMA_HOME", os.path.expanduser("~/.kadima"))
CONFIG_PATH = os.path.join(KADIMA_HOME, "config.yaml")
DB_PATH = os.path.join(KADIMA_HOME, "kadima.db")
LOG_PATH = os.path.join(KADIMA_HOME, "logs", "kadima.log")


def init_kadima() -> None:
    """Инициализация: создать директории, config, DB."""
    dirs = [
        KADIMA_HOME,
        os.path.join(KADIMA_HOME, "logs"),
        os.path.join(KADIMA_HOME, "models"),
        os.path.join(KADIMA_HOME, "backups"),
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

    # Config
    if not os.path.exists(CONFIG_PATH):
        default_config = os.path.join(os.path.dirname(__file__), "../config/config.default.yaml")
        if os.path.exists(default_config):
            import shutil
            shutil.copy(default_config, CONFIG_PATH)
            print(f"Config created: {CONFIG_PATH}")
        else:
            # Fallback: create minimal config
            with open(CONFIG_PATH, "w") as f:
                yaml.dump({"pipeline": {"language": "he", "profile": "balanced"}}, f)
            print(f"Config created (minimal): {CONFIG_PATH}")

    # Database: run migrations
    from kadima.data.db import run_migrations
    run_migrations(DB_PATH)
    print(f"Database initialized: {DB_PATH}")

    print(f"\nKADIMA initialized at {KADIMA_HOME}")
    print("Run 'kadima gui' to start the UI")


def run_pipeline(args: argparse.Namespace) -> None:
    """Запуск pipeline из CLI."""
    from kadima.data.db import ensure_db as _ensure_db
    from kadima.pipeline.config import load_config
    from kadima.pipeline.orchestrator import PipelineService

    db_path = args.db or DB_PATH
    _ensure_db(db_path)
    config = load_config(args.config or CONFIG_PATH)
    service = PipelineService(config, db_path=db_path)

    if args.text:
        result = service.run_on_text(args.text)
        print(f"\nProfile: {result.profile}")
        print(f"Terms found: {len(result.terms)}")
        for term in result.terms[:20]:
            print(f"  {term.surface:30} freq={term.freq:4}  PMI={term.pmi:.2f}  rank={term.rank}")
    elif args.corpus:
        result = service.run(int(args.corpus))
        print(f"\nPipeline completed: {len(result.terms)} terms in {result.total_time_ms:.0f}ms")
    else:
        print("Error: specify --corpus ID or --text '...'")
        sys.exit(1)


def run_gui() -> None:
    """Запуск PyQt UI."""
    from kadima.data.db import ensure_db as _ensure_db
    _ensure_db(DB_PATH)
    from kadima.app import main as gui_main
    gui_main()


def run_api(args: argparse.Namespace) -> None:
    """Запуск FastAPI сервера."""
    from kadima.data.db import ensure_db as _ensure_db
    _ensure_db(args.db or DB_PATH)
    import uvicorn
    uvicorn.run(
        "kadima.api.app:app",
        host=args.host or "127.0.0.1",
        port=args.port or 8501,
        reload=args.reload or False,
    )


_SELF_CHECK_MODULES = [
    "kadima.engine.hebpipe_wrappers",
    "kadima.engine.ngram_extractor",
    "kadima.engine.np_chunker",
    "kadima.engine.canonicalizer",
    "kadima.engine.association_measures",
    "kadima.engine.term_extractor",
    "kadima.engine.noise_classifier",
    "kadima.pipeline.orchestrator",
    "kadima.pipeline.config",
    "kadima.data.db",
    "kadima.data.repositories",
    "kadima.validation.check_engine",
    "kadima.validation.gold_importer",
    "kadima.kb.repository",
    "kadima.llm.client",
    "kadima.annotation.ls_client",
]


def _sc_import() -> dict[str, object]:
    """Check all core module imports."""
    failed: list[str] = []
    imported: list[str] = []
    for mod in _SELF_CHECK_MODULES:
        try:
            __import__(mod)
            imported.append(mod)
        except ImportError as exc:
            failed.append(f"{mod}: {exc}")
        except Exception as exc:  # noqa: BLE001
            failed.append(f"{mod}: unexpected {type(exc).__name__}: {exc}")
    status = "error" if failed else "ok"
    return {"status": status, "details": {"imported": len(imported), "failed": failed}}


def _sc_db_open() -> dict[str, object]:
    """Open a temporary DB, run migrations, return result."""
    import tempfile

    from kadima.data.db import run_migrations

    with tempfile.TemporaryDirectory() as tmpdir:
        test_db = os.path.join(tmpdir, "self_check.db")
        try:
            count = run_migrations(test_db)
            return {"status": "ok", "details": {"migrations_applied": count}}
        except Exception as exc:  # noqa: BLE001
            return {"status": "error", "details": {"error": str(exc)}}


def _sc_health() -> dict[str, object]:
    """Check DB reachability, config load, CUDA availability."""
    checks: dict[str, str] = {}
    status = "ok"
    try:
        from kadima.data.db import get_schema_version

        checks["db"] = f"ok (schema v{get_schema_version(DB_PATH)})"
    except Exception as exc:  # noqa: BLE001
        checks["db"] = f"error: {exc}"
        status = "error"
    try:
        from kadima.pipeline.config import load_config

        load_config(CONFIG_PATH if os.path.exists(CONFIG_PATH) else None)
        checks["config"] = "ok"
    except Exception as exc:  # noqa: BLE001
        checks["config"] = f"error: {exc}"
        status = "error"
    try:
        import torch

        checks["cuda"] = f"available (devices={torch.cuda.device_count()})"
    except ImportError:
        checks["cuda"] = "torch not installed"
    return {"status": status, "details": checks}


def _sc_migrations() -> dict[str, object]:
    """Report current schema version."""
    try:
        from kadima.data.db import get_schema_version

        version = get_schema_version(DB_PATH)
        return {"status": "ok", "details": {"schema_version": version, "db_path": DB_PATH}}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "details": {"error": str(exc)}}


_SC_HANDLERS = {
    "import": _sc_import,
    "db_open": _sc_db_open,
    "health": _sc_health,
    "migrations": _sc_migrations,
}


def run_self_check(mode: str) -> None:
    """Self-check для CI: проверяет состояние системы и выводит JSON результат."""
    import json

    handler = _SC_HANDLERS.get(mode)
    if handler is None:
        res: dict[str, object] = {"mode": mode, "status": "error",
                                  "details": {"error": f"Unknown mode: {mode!r}"}}
    else:
        res = {"mode": mode, **handler()}  # type: ignore[arg-type]

    print(json.dumps(res, ensure_ascii=False, indent=2))
    if res.get("status") != "ok":
        sys.exit(1)


def run_migrate(args: argparse.Namespace) -> None:
    """Управление миграциями."""
    from kadima.data.db import generate_migration, get_schema_version, run_migrations

    if args.new:
        path = generate_migration(args.new)
        print(f"Created: {path}")
        print("Edit the file, then run `kadima migrate` to apply.")
    elif args.status:
        version = get_schema_version(args.db or DB_PATH)
        print(f"Schema version: {version}")
    else:
        count = run_migrations(args.db or DB_PATH)
        print(f"Applied {count} migration(s).")


def main() -> None:
    """Точка входа CLI: парсит аргументы и запускает команду."""
    parser = argparse.ArgumentParser(prog="kadima", description="KADIMA — Hebrew NLP Platform")
    parser.add_argument("--version", action="version", version="%(prog)s " + __import__("kadima").__version__)
    parser.add_argument("--init", action="store_true", help="Initialize KADIMA")
    parser.add_argument(
        "--self-check",
        metavar="MODE",
        choices=["import", "db_open", "health", "migrations"],
        help="Run self-check: import | db_open | health | migrations",
    )
    parser.add_argument("--config", type=str, help="Config file path")
    parser.add_argument("--db", type=str, help="Database path")
    parser.add_argument("--log-level", type=str, default="INFO", help="Log level")

    subparsers = parser.add_subparsers(dest="command")

    # gui
    subparsers.add_parser("gui", help="Launch PyQt UI")

    # run
    run_parser = subparsers.add_parser("run", help="Run pipeline")
    run_parser.add_argument("--corpus", type=str, help="Corpus ID")
    run_parser.add_argument("--text", type=str, help="Run on single text")
    run_parser.add_argument("--profile", type=str, default="balanced", help="Extraction profile")
    run_parser.add_argument("--export", type=str, help="Export results to file")

    # api
    api_parser = subparsers.add_parser("api", help="Start REST API server")
    api_parser.add_argument("--host", type=str, default="127.0.0.1")
    api_parser.add_argument("--port", type=int, default=8501)
    api_parser.add_argument("--reload", action="store_true")

    # migrate
    migrate_parser = subparsers.add_parser("migrate", help="Database migrations")
    migrate_parser.add_argument("--new", type=str, help="Generate new migration (e.g. --new add_users)")
    migrate_parser.add_argument("--status", action="store_true", help="Show current schema version")

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    if args.init:
        init_kadima()
        return

    if args.self_check:
        run_self_check(args.self_check)
        return

    if args.command == "gui":
        run_gui()
    elif args.command == "run":
        run_pipeline(args)
    elif args.command == "api":
        run_api(args)
    elif args.command == "migrate":
        run_migrate(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
