# Dockerfile — KADIMA API server (multi-stage)
# Build: docker build -t kadima-api .
# Run:   docker run -p 8501:8501 -v kadima-data:/data kadima-api

# ── Stage 1: install dependencies ────────────────────────────────────────────
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /build

COPY pyproject.toml ./
COPY kadima/ ./kadima/
COPY config/ ./config/
COPY templates/ ./templates/

RUN pip install --no-cache-dir --prefix=/install .

# ── Stage 2: minimal runtime ─────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# curl for healthchecks
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY config/ ./config/
COPY templates/ ./templates/
COPY kadima/ ./kadima/

# Non-root user
RUN useradd --no-create-home --uid 1000 appuser
USER appuser

# Data volume: /data holds kadima.db, logs, models, backups
ENV KADIMA_HOME=/data
VOLUME /data

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8501/health || exit 1

ENTRYPOINT ["kadima"]
CMD ["api", "--host", "0.0.0.0", "--port", "8501"]
