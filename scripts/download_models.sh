#!/usr/bin/env bash
# scripts/download_models.sh — Download required models
set -euo pipefail

MODELS_DIR="${KADIMA_HOME:-$HOME/.kadima}/models"
mkdir -p "$MODELS_DIR"

echo "Models to download:"
echo "  - DictaLM 3.0 1.7B Instruct (GGUF)"
echo "  - NeoDictaBERT embeddings"
echo ""
echo "TODO: Implement download URLs (check doc/ for model sources)"
