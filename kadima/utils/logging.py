# kadima/utils/logging.py
"""Logging configuration for KADIMA.

Usage:
    from kadima.utils.logging import setup_logging
    setup_logging(level="INFO")
"""

import logging
import os
import sys
from pathlib import Path


def setup_logging(level: str = "INFO", log_file: str = None) -> None:
    """Configure logging for KADIMA.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR).
        log_file: Optional path to log file. Defaults to ~/.kadima/logs/kadima.log.
    """
    if log_file is None:
        kadima_home = os.environ.get("KADIMA_HOME", os.path.expanduser("~/.kadima"))
        log_dir = os.path.join(kadima_home, "logs")
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        log_file = os.path.join(log_dir, "kadima.log")

    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=fmt,
        handlers=[
            logging.StreamHandler(sys.stderr),
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
    )
