#!/bin/bash
# scripts/run_label_studio.sh
# Start Label Studio in Docker for KADIMA annotation workflow

set -e

LS_PORT="${LABEL_STUDIO_PORT:-8080}"
LS_DATA_DIR="${LABEL_STUDIO_DATA_DIR:-./label_studio_data}"

echo "Starting Label Studio on port ${LS_PORT}..."
echo "Data directory: ${LS_DATA_DIR}"

mkdir -p "${LS_DATA_DIR}"

docker run -d \
    --name kadima-label-studio \
    -p "${LS_PORT}:8080" \
    -v "$(pwd)/${LS_DATA_DIR}:/label-studio/files" \
    -e LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED=true \
    -e LABEL_STUDIO_DISABLE_SIGNUP_WITHOUT_LINK=true \
    heartexlabs/label-studio:latest

echo ""
echo "Label Studio running at: http://localhost:${LS_PORT}"
echo "Default credentials: create at first visit"
echo ""
echo "To stop: docker stop kadima-label-studio && docker rm kadima-label-studio"
