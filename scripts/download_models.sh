#!/usr/bin/env bash
# scripts/download_models.sh — Download required models for Kadima
#
# Usage:
#   bash scripts/download_models.sh [--all] [--neodictabert] [--dictalm] [--heq-ner]
#
# Environment variables:
#   HF_HOME         HuggingFace cache dir (default: ~/.cache/huggingface)
#   MODELS_DIR      Override base model dir (default: $HF_HOME/hub)
#   KADIMA_LLM_DIR  Directory for GGUF llama.cpp models (default: ~/.kadima/models/llm)
#
# Requirements:
#   - huggingface_hub Python package (pip install huggingface-hub)
#   - wget or curl (for GGUF download)
#   - HF_TOKEN env var if downloading gated models
set -euo pipefail

# ── Colours ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()    { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; }

# ── Defaults ─────────────────────────────────────────────────────────────────
HF_HOME="${HF_HOME:-$HOME/.cache/huggingface}"
MODELS_DIR="${MODELS_DIR:-$HF_HOME/hub}"
KADIMA_LLM_DIR="${KADIMA_LLM_DIR:-${KADIMA_HOME:-$HOME/.kadima}/models/llm}"

mkdir -p "$MODELS_DIR" "$KADIMA_LLM_DIR"

# ── Argument parsing ──────────────────────────────────────────────────────────
DOWNLOAD_ALL=false
DOWNLOAD_NEODICTABERT=false
DOWNLOAD_DICTALM=false
DOWNLOAD_HEQ_NER=false

if [[ $# -eq 0 ]]; then
    DOWNLOAD_ALL=true
fi

for arg in "$@"; do
    case "$arg" in
        --all)           DOWNLOAD_ALL=true ;;
        --neodictabert)  DOWNLOAD_NEODICTABERT=true ;;
        --dictalm)       DOWNLOAD_DICTALM=true ;;
        --heq-ner)       DOWNLOAD_HEQ_NER=true ;;
        --help|-h)
            echo "Usage: $0 [--all] [--neodictabert] [--dictalm] [--heq-ner]"
            exit 0 ;;
        *)
            error "Unknown argument: $arg"; exit 1 ;;
    esac
done

if $DOWNLOAD_ALL; then
    DOWNLOAD_NEODICTABERT=true
    DOWNLOAD_DICTALM=true
    DOWNLOAD_HEQ_NER=true
fi

# ── Helper: download HF model via huggingface-cli ────────────────────────────
hf_download() {
    local repo_id="$1"
    local description="$2"
    info "Downloading $description ($repo_id)…"
    if python -c "import huggingface_hub" 2>/dev/null; then
        python -c "
from huggingface_hub import snapshot_download
import os
token = os.environ.get('HF_TOKEN')
path = snapshot_download('$repo_id', token=token, local_files_only=False)
print(f'  → cached at: {path}')
"
    elif command -v huggingface-cli &>/dev/null; then
        huggingface-cli download "$repo_id" --local-dir "$MODELS_DIR/$repo_id"
    else
        error "huggingface_hub Python package not found. Install: pip install huggingface-hub"
        return 1
    fi
    info "Done: $description"
}

# ── Helper: download GGUF file ────────────────────────────────────────────────
gguf_download() {
    local url="$1"
    local filename="$2"
    local dest="$KADIMA_LLM_DIR/$filename"

    if [[ -f "$dest" ]]; then
        info "Already downloaded: $filename ($(du -h "$dest" | cut -f1))"
        return 0
    fi

    info "Downloading GGUF: $filename → $KADIMA_LLM_DIR"
    if command -v wget &>/dev/null; then
        wget -q --show-progress -O "$dest" "$url"
    elif command -v curl &>/dev/null; then
        curl -L --progress-bar -o "$dest" "$url"
    else
        error "Neither wget nor curl found. Install one to download GGUF files."
        return 1
    fi
    info "Done: $filename ($(du -h "$dest" | cut -f1))"
}

# ── Model definitions ─────────────────────────────────────────────────────────

download_neodictabert() {
    # NeoDictaBERT: Hebrew transformer backbone (768-dim, ~500MB)
    # Used by: KadimaTransformer (R-1.2), NP chunker (R-2.1), NER (R-2.2),
    #          term clusterer (R-2.5), KB embedding search (R-2.4)
    hf_download "dicta-il/neodictabert" "NeoDictaBERT (Hebrew BERT backbone)"
}

download_heq_ner() {
    # HeQ-NER: Hebrew NER token-classification model (<500MB)
    # Used by: NERExtractor (M17) heq_ner backend
    hf_download "dicta-il/HeQ-NER" "HeQ-NER (Hebrew NER)"
}

download_dictalm() {
    # DictaLM 3.0 1.7B Instruct GGUF — quantized for llama.cpp
    # GGUF Q4_K_M: ~1.1GB, runs on CPU or GPU
    # Source: dicta-il/dictalm3.0-instruct-GGUF on HuggingFace
    local gguf_url
    gguf_url="https://huggingface.co/dicta-il/dictalm3.0-instruct-GGUF/resolve/main/dictalm3.0-instruct.Q4_K_M.gguf"
    gguf_download "$gguf_url" "dictalm3.0-instruct.Q4_K_M.gguf"

    # Also snapshot the tokenizer / config (needed for chat template)
    hf_download "dicta-il/dictalm3.0-instruct-GGUF" "DictaLM 3.0 Instruct GGUF (metadata)"
}

# ── Main ──────────────────────────────────────────────────────────────────────

echo ""
info "Kadima model download script"
info "HF cache:    $MODELS_DIR"
info "LLM dir:     $KADIMA_LLM_DIR"
if [[ -n "${HF_TOKEN:-}" ]]; then
    info "HF_TOKEN:    set (${#HF_TOKEN} chars)"
else
    warn "HF_TOKEN:    not set (set it for gated models)"
fi
echo ""

SUCCESS=()
FAILED=()

run_step() {
    local name="$1"
    local fn="$2"
    if $fn; then
        SUCCESS+=("$name")
    else
        FAILED+=("$name")
        warn "Failed to download $name — continuing"
    fi
}

$DOWNLOAD_NEODICTABERT && run_step "NeoDictaBERT" download_neodictabert
$DOWNLOAD_HEQ_NER      && run_step "HeQ-NER"      download_heq_ner
$DOWNLOAD_DICTALM      && run_step "DictaLM 3.0"  download_dictalm

echo ""
info "Summary:"
for m in "${SUCCESS[@]:-}"; do [[ -n "$m" ]] && echo -e "  ${GREEN}✓${NC} $m"; done
for m in "${FAILED[@]:-}";  do [[ -n "$m" ]] && echo -e "  ${RED}✗${NC} $m"; done

if [[ ${#FAILED[@]} -gt 0 ]] && [[ -n "${FAILED[0]:-}" ]]; then
    error "Some downloads failed. Check logs above."
    exit 1
fi
info "All downloads complete."
