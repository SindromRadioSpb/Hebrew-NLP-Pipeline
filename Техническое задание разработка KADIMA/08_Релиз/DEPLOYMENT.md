# 8.1. Deployment Guide — KADIMA

## Desktop (Windows)
1. Python 3.11+ installed
2. `pip install kadima` (from PyPI)
3. `kadima --init` — creates config + DB
4. `kadima gui` — launches UI

## From source
1. `git clone https://github.com/SindromRadioSpb/Hebrew-NLP-Pipeline`
2. `cd Hebrew-NLP-Pipeline && pip install -e .`
3. `python -m kadima gui`

## Configuration
- `~/.kadima/config.yaml` — pipeline settings
- `~/.kadima/kadima.db` — SQLite database
- `~/.kadima/logs/` — log files

## Environment Variables
- `KADIMA_HOME` — override default config directory
- `KADIMA_LOG_LEVEL` — DEBUG/INFO/WARNING/ERROR
- `KADIMA_DB_PATH` — override SQLite path

## Rollback
- Config: restore `config.yaml` from backup
- DB: restore `kadima.db` from backup
- Data: re-import corpora from export files
