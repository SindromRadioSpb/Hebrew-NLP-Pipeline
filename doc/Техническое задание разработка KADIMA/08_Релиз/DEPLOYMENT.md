# 8.1. Deployment Guide — KADIMA

> Версия: 2.0 (2026-03-30)

---

## Desktop (Windows)

### Step 1: Python & Docker
```powershell
# Python 3.12+ (из python.org)
python --version  # 3.12+

# Docker Desktop (для Label Studio)
docker --version
```

### Step 2: Install KADIMA
```powershell
pip install kadima
kadima --init
```

### Step 3: Start Label Studio
```powershell
# В директории проекта
docker-compose -f docker-compose.kadima-ls.yml up -d

# Проверка: http://localhost:8080
```

### Step 4: Start LLM (v1.x)
```powershell
# Скачать модель (один раз)
# DictaLM-3.0-1.7B-Instruct-GGUF Q4_K_M
# ~1 GB

# Запуск inference server
llama-server -m DictaLM-3.0-1.7B-Instruct-Q4_K_M.gguf -ngl 35 --port 8081

# Проверка: http://localhost:8081/health
```

### Step 5: Launch UI
```powershell
kadima gui
```

---

## From Source
```bash
git clone https://github.com/SindromRadioSpb/Hebrew-NLP-Pipeline
cd Hebrew-NLP-Pipeline
pip install -e .

# Label Studio
docker-compose -f docker-compose.kadima-ls.yml up -d

# LLM (v1.x)
llama-server -m models/DictaLM-3.0-1.7B-Instruct-Q4_K_M.gguf -ngl 35 --port 8081

# UI
python -m kadima gui
```

---

## Docker Compose: Full Stack

```yaml
# docker-compose.kadima-ls.yml
version: '3.8'

services:
  label-studio:
    image: heartexlabs/label-studio:latest
    ports:
      - "8080:8080"
    volumes:
      - ./ls_data:/label-studio/data
    environment:
      - LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED=true

  kadima-ml-backend:
    build:
      context: ./ml_backends
      dockerfile: Dockerfile
    ports:
      - "9090:9090"
    environment:
      - LABEL_STUDIO_URL=http://label-studio:8080
      - SPACY_MODEL=he_kadima_pipeline
    depends_on:
      - label-studio

  # v1.x: LLM inference server
  # kadima-llm:
  #   image: ghcr.io/ggerganov/llama.cpp:server
  #   ports:
  #     - "8081:8081"
  #   volumes:
  #     - ./models:/models
  #   command: -m /models/DictaLM-3.0-1.7B-Instruct-Q4_K_M.gguf -ngl 35 --port 8081
```

---

## Configuration

```
~/.kadima/
├── config.yaml          # Pipeline settings, profiles, thresholds
├── kadima.db            # SQLite database
├── models/
│   ├── neodictabert/    # NeoDictaBERT (auto-download)
│   └── dictalm-1.7b.gguf  # Dicta-LM (v1.x, manual download)
├── logs/
│   ├── pipeline.log
│   ├── annotation.log
│   └── llm.log
└── backups/
```

### config.yaml
```yaml
pipeline:
  language: he
  modules: [sent_split, tokenize, morph, ngram, np_chunk, canonicalize, am, term_extract]
  profile: balanced
  thresholds:
    min_freq: 2
    pmi_threshold: 3.0
    hapax_filter: true

annotation:
  label_studio_url: http://localhost:8080
  label_studio_api_key: ${LS_API_KEY}
  ml_backend_url: http://localhost:9090

llm:  # v1.x
  enabled: false
  server_url: http://localhost:8081
  model: dictalm-3.0-1.7b-instruct
  max_tokens: 512
  temperature: 0.7

kb:  # v1.x
  enabled: false
  embedding_model: neodictabert
  auto_generate_definitions: false
```

---

## Environment Variables
- `KADIMA_HOME` — override default config directory
- `KADIMA_LOG_LEVEL` — DEBUG/INFO/WARNING/ERROR
- `KADIMA_DB_PATH` — override SQLite path
- `KADIMA_LS_URL` — Label Studio URL (default: http://localhost:8080)
- `KADIMA_LLM_URL` — LLM server URL (default: http://localhost:8081)

---

## Rollback
- Config: restore `config.yaml` from `backups/`
- DB: restore `kadima.db` from `backups/`
- Data: re-import corpora from export files
- Label Studio: `docker-compose down && docker-compose up -d`
- LLM: restart `llama-server`
