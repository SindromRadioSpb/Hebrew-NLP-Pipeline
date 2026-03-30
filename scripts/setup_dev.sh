#!/usr/bin/env bash
# scripts/setup_dev.sh — Dev environment setup
set -euo pipefail

echo "=== KADIMA Dev Setup ==="

# Python venv
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[all]"

# Download models (placeholder)
# bash scripts/download_models.sh

echo "Done. Activate: source .venv/bin/activate"
