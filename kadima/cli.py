# kadima/cli.py
"""CLI entrypoint для KADIMA.

Использование:
    kadima gui                    — запустить PyQt UI
    kadima run --corpus ID        — запустить pipeline на корпусе
    kadima run --text "טקסט"      — запустить pipeline на одном тексте
    kadima api                    — запустить FastAPI сервер
    kadima --init                 — инициализация (~/.kadima/ с config и DB)
    kadima --version              — версия
"""

import os
import sys
import logging
import argparse
from pathlib import Path

import yaml

KADIMA_HOME = os.environ.get("KADIMA_HOME", os.path.expanduser("~/.kadima"))
CONFIG_PATH = os.path.join(KADIMA_HOME, "config.yaml")
DB_PATH = os.path.join(KADIMA_HOME, "kadima.db")
LOG_PATH = os.path.join(KADIMA_HOME, "logs", "kadima.log")


def init_kadima():
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


def run_pipeline(args):
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


def run_gui():
    """Запуск PyQt UI."""
    from kadima.data.db import ensure_db as _ensure_db
    _ensure_db(DB_PATH)
    from kadima.app import main as gui_main
    gui_main()


def run_api(args):
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


def run_migrate(args):
    """Управление миграциями."""
    from kadima.data.db import run_migrations, get_schema_version, generate_migration

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


def main():
    parser = argparse.ArgumentParser(prog="kadima", description="KADIMA — Hebrew NLP Platform")
    parser.add_argument("--version", action="version", version="%(prog)s " + __import__("kadima").__version__)
    parser.add_argument("--init", action="store_true", help="Initialize KADIMA")
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
