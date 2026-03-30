# Dockerfile — KADIMA API server
# Build: docker build -t kadima-api .
# Run:   docker run -p 8501:8501 -v kadima-data:/data kadima-api

FROM python:3.12-slim AS base

# Prevent Python from writing .pyc and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System deps
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── Copy project files ──────────────────────────────────────────────────────
COPY pyproject.toml ./
COPY config/ ./config/
COPY templates/ ./templates/
COPY kadima/ ./kadima/

# ── Install ──────────────────────────────────────────────────────────────────
RUN pip install --no-cache-dir .

# ── Runtime ──────────────────────────────────────────────────────────────────
# Data volume: /data holds kadima.db, logs, models, backups
ENV KADIMA_HOME=/data
VOLUME /data

EXPOSE 8501

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8501/health || exit 1

ENTRYPOINT ["kadima"]
CMD ["api", "--host", "0.0.0.0", "--port", "8501"]
