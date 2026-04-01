---
name: security-hardening-guardrails
description: Use this skill for any Kadima code touching file paths, user-provided strings, SQL queries, logs, audio file paths, imports, or zip bundles. Identifies attacker-controlled inputs, applies validation/whitelists/sanitizers, ensures parameterized SQL, validates file paths against allowed base dirs, and adds security tests.
---

# Security Guardrails (Kadima)

## When to use
Any code touching:
- File paths (audio_path in STT, corpus import, export output)
- User-provided strings (API request bodies, UI inputs)
- SQL queries (any new query in data layer)
- Log output (avoid log injection)
- ZIP/archive extraction (corpus import)
- API key / secret storage (`.env`, config)

## Checklist

### 1. Attacker-controlled inputs — identify first
```
API request body fields → validate at router level (Pydantic min_length/pattern)
UI file dialogs         → validate path, extension, size before opening
audio_path in STT API   → must be server-side path, validate with os.path.isfile
corpus text imports     → validate file size, encoding before reading
```

### 2. SQL — all queries parameterized
```python
# ❌ NEVER
conn.execute(f"SELECT * FROM terms WHERE lemma = '{user_input}'")

# ✅ ALWAYS
conn.execute("SELECT * FROM terms WHERE lemma = ?", (user_input,))
```

Sort columns must be whitelisted:
```python
ALLOWED_SORT_COLS = {"lemma", "freq", "created_at"}
if sort_col not in ALLOWED_SORT_COLS:
    raise ValueError(f"Invalid sort column: {sort_col!r}")
```

### 3. File path validation
```python
import os

def validate_path(user_path: str, base_dir: str) -> str:
    """Resolve and verify path stays within base_dir."""
    abs_path = os.path.realpath(os.path.abspath(user_path))
    base = os.path.realpath(os.path.abspath(base_dir))
    if not abs_path.startswith(base + os.sep) and abs_path != base:
        raise ValueError(f"Path traversal detected: {user_path!r}")
    return abs_path
```

### 4. Subprocess — never shell=True with user input
```python
# ❌
subprocess.run(f"ffmpeg -i {user_path}", shell=True)

# ✅
subprocess.run(["ffmpeg", "-i", validated_path], capture_output=True)
```

### 5. YAML loading
```python
# ❌
yaml.load(f)

# ✅
yaml.safe_load(f)
```

### 6. Secrets
- Never hardcode in code or config files
- Always from `.env` / env vars
- `.env` must be in `.gitignore` (verify)
- `.env.example` must have placeholder values only

### 7. Pydantic input validation (FastAPI routers)
```python
# Already required in kadima/api/routers/ — verify new endpoints have:
field: str = Field(..., min_length=1, max_length=10000)
backend: str = Field(..., pattern=r"^(option1|option2)$")
audio_path: str = Field(..., description="Server-side absolute path")
```

## Tests to add/extend
```python
def test_sql_injection_rejected():
    # "'; DROP TABLE terms; --" as input → treated as literal string, no error

def test_path_traversal_rejected():
    # audio_path = "../../etc/passwd" → 422 or ValueError

def test_sort_column_whitelist():
    # unknown sort column → 422

def test_env_example_has_no_real_secrets():
    # assert all values in .env.example are placeholders
```

```bash
pytest tests/ -v -k security
# or if security_auditor agent available — run it
```
