# 10.4. Dependency Manifest — KADIMA

> Версия: 1.0 (2026-03-30)
> Связанные: PROJECT_STRUCTURE.md, NLP_STACK_INTEGRATION.md, DEPLOYMENT.md

---

## pyproject.toml

```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "kadima"
version = "1.0.0"
description = "KADIMA — Hebrew NLP Platform: term extraction, validation, annotation, knowledge base"
readme = "README.md"
license = {text = "Apache-2.0"}
requires-python = ">=3.12"
authors = [
    {name = "KADIMA Team"},
]
classifiers = [
    "Programming Language :: Python :: 3.12",
    "License :: OSI Approved :: Apache Software License",
    "Operating System :: OS Independent",
    "Topic :: Text Processing :: Linguistic",
    "Natural Language :: Hebrew",
]

# === CORE DEPENDENCIES (v1.0) ===
dependencies = [
    # NLP Stack
    "spacy>=3.7,<4.0",
    "spacy-transformers>=1.3,<2.0",
    "transformers>=4.35,<5.0",
    "torch>=2.1,<3.0",
    "hebpipe>=0.4.0",

    # Data
    "pandas>=2.1,<3.0",
    "numpy>=1.26,<2.0",
    "scipy>=1.12,<2.0",
    "pyyaml>=6.0",
    "conllu>=4.5",

    # Database
    "sqlalchemy>=2.0,<3.0",

    # API
    "fastapi>=0.110,<1.0",
    "uvicorn>=0.27,<1.0",
    "pydantic>=2.0,<3.0",
    "httpx>=0.27,<1.0",

    # UI
    "pyqt6>=6.6",

    # Annotation
    "label-studio-sdk>=1.0",

    # Utils
    "rich>=13.0",          # CLI output
    "click>=8.0",          # CLI framework
    "tqdm>=4.60",          # Progress bars
]

[project.optional-dependencies]
# v1.x: LLM support
llm = [
    "llama-cpp-python>=0.2",  # Optional: для программного запуска llama.cpp
]

# Development
dev = [
    "pytest>=8.0",
    "pytest-cov>=4.0",
    "pytest-qt>=4.0",
    "pytest-asyncio>=0.23",
    "black>=24.0",
    "ruff>=0.3",
    "isort>=5.0",
    "mypy>=1.8",
]

[project.scripts]
kadima = "kadima.cli:main"

[project.urls]
Homepage = "https://github.com/SindromRadioSpb/Hebrew-NLP-Pipeline"
Repository = "https://github.com/SindromRadioSpb/Hebrew-NLP-Pipeline"
Documentation = "https://github.com/SindromRadioSpb/Hebrew-NLP-Pipeline/tree/main/docs"

[tool.setuptools.packages.find]
include = ["kadima*"]

[tool.setuptools.package-data]
kadima = ["py.typed"]
```

---

## Версии: совместимость

| Пакет | Минимум | Максимум | Почему |
|-------|---------|----------|--------|
| Python | 3.12 | — | type features, performance |
| spaCy | 3.7 | <4.0 | transformer support, stable API |
| spacy-transformers | 1.3 | <2.0 | NeoDictaBERT integration |
| transformers | 4.35 | <5.0 | trust_remote_code для NeoDictaBERT |
| torch | 2.1 | <3.0 | CUDA 11.8+ support |
| hebpipe | 0.4.0 | — | M1–M3 modules |
| pandas | 2.1 | <3.0 | stable API |
| numpy | 1.26 | <2.0 | compat с scipy/torch |
| scipy | 1.12 | <2.0 | AM calculations |
| pyyaml | 6.0 | — | config loading |
| sqlalchemy | 2.0 | <3.0 | async support |
| fastapi | 0.110 | <1.0 | stable |
| pyqt6 | 6.6 | — | UI |
| label-studio-sdk | 1.0 | — | annotation integration |

---

## Установка: development

```bash
# Клонировать
git clone https://github.com/SindromRadioSpb/Hebrew-NLP-Pipeline
cd Hebrew-NLP-Pipeline

# Виртуальное окружение
python3.12 -m venv .venv
source .venv/bin/activate  # Linux/WSL
# .venv\Scripts\activate   # Windows

# Установить с dev-зависимостями
pip install -e ".[dev,llm]"

# Проверить
python -c "import kadima; print(kadima.__version__)"
python -c "import spacy; import hebpipe; print('NLP stack OK')"

# Инициализировать
kadima --init
```

---

## Установка: production

```bash
pip install kadima
kadima --init
kadima gui
```

---

## Модели: download scripts

### NeoDictaBERT (автоскачивание через transformers)
```python
# models/download_neodictabert.py
from transformers import AutoModel, AutoTokenizer

def download():
    AutoTokenizer.from_pretrained("dicta-il/neodictabert")
    AutoModel.from_pretrained("dicta-il/neodictabert", trust_remote_code=True)
    print("NeoDictaBERT downloaded to HF cache")

if __name__ == "__main__":
    download()
```

### Dicta-LM 3.0 (ручная загрузка GGUF)
```bash
# models/download_dictalm.sh
#!/bin/bash
MODEL_DIR="$HOME/.kadima/models"
mkdir -p "$MODEL_DIR"

# 1.7B Instruct — для v1.x (лёгкая, ~1 GB)
wget -P "$MODEL_DIR" \
  "https://huggingface.co/dicta-il/DictaLM-3.0-1.7B-Instruct-GGUF/resolve/main/DictaLM-3.0-1.7B-Instruct-Q4_K_M.gguf"

echo "Dicta-LM 1.7B Q4 downloaded to $MODEL_DIR"
```

---

## Docker: Label Studio + ML Backend

### docker-compose.kadima-ls.yml
```yaml
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
    volumes:
      - ./kadima_models:/app/models
```

### ml_backends/Dockerfile
```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY kadima_ner_backend.py .

EXPOSE 9090
CMD ["python", "kadima_ner_backend.py"]
```

### ml_backends/requirements.txt
```
label-studio-ml>=1.0
spacy>=3.7
transformers>=4.35
torch>=2.1
hebpipe>=0.4.0
flask>=3.0
```

---

## Порядок установки (конфликт-анализ)

```bash
# 1. Сначала spaCy с transformers (тянет torch)
pip install 'spacy[transformers]>=3.7'

# 2. HebPipe (может обновить torch/transformers)
pip install hebpipe

# 3. Остальные
pip install -e ".[dev,llm]"

# 4. Проверка конфликтов
pip check

# 5. Smoke test
python -c "
import spacy, hebpipe, transformers, torch, pandas, scipy
print(f'spaCy: {spacy.__version__}')
print(f'torch: {torch.__version__}')
print(f'transformers: {transformers.__version__}')
print('All OK')
"
```

---

## .gitignore (релевантные правила)

```gitignore
# Python
__pycache__/
*.pyc
.venv/
dist/
build/
*.egg-info/

# Models (太大 для git)
models/*.gguf
models/*.bin
models/*.safetensors

# Data
~/.kadima/
ls_data/

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db
```
