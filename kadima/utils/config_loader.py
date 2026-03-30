# kadima/utils/config_loader.py
"""Load and validate YAML configuration.

Usage:
    from kadima.utils.config_loader import load_config
    config = load_config("~/.kadima/config.yaml")
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = os.path.expanduser("~/.kadima/config.yaml")
FALLBACK_CONFIG = os.path.join(os.path.dirname(__file__), "..", "..", "config", "config.default.yaml")


def load_config(path: Optional[str] = None) -> Dict[str, Any]:
    """Load YAML config with fallback to defaults.

    Args:
        path: Config file path. Defaults to ~/.kadima/config.yaml.

    Returns:
        Config dict.
    """
    path = path or DEFAULT_CONFIG_PATH

    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        logger.info("Loaded config from %s", path)
    elif os.path.exists(FALLBACK_CONFIG):
        with open(FALLBACK_CONFIG, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        logger.warning("Config not found at %s, using defaults", path)
    else:
        config = {"pipeline": {"language": "he", "profile": "balanced"}}
        logger.warning("No config found, using minimal defaults")

    return config or {}
