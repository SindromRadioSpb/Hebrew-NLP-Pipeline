# CLAUDE.md — Kadima Project Map

> **Python 3.10+** | **Package:** `kadima/` | **DB:** SQLite WAL + migrations
> **Conventions:** snake_case files/functions, PascalCase classes, UPPER_SNAKE constants
> **Target HW:** RTX 3060 12GB (dev) / RTX 3070 8GB (CI)
> **Version:** 0.9.x (NLP pipeline) -> 1.0.0 (+ generative modules)

---

## Quick Start

```bash
# Install (core only)
pip install -e ".[dev]"

# Install with ML modules
pip install -e ".[ml,dev]"

# Install with GPU-accelerated ML
pip install -e ".[gpu,dev]"

# Run tests (MUST pass before any change)
pytest tests/ -v

# Lint + typecheck
ruff check kadima/
mypy kadima/ --ignore-missing-imports

# Run API
kadima api --host 0.0.0.0 --port 8501

# Docker
make up                     # API + Label Studio
make up-llm                 # + llama.cpp (GPU)
```

---

## Current Status (2026-03-31)

### What works

| Component | Status | Notes |
|-----------|--------|-------|
| Engine M1-M8, M12 | Working | M3 rule-based fallback + hebpipe integration |
| Pipeline `run_on_text()` | Working | Sequential M1->M8->M12 |
| Pipeline `run(corpus_id)` | Working | DB load + process + save pipeline_runs/terms |
| Pipeline config | Working | Pydantic v2, profiles, JSON Schema, M13-M25 sub-configs |
| Data layer | Working | WAL, FK, 4 migrations, parameterized queries |
| Validation | Working | 26 gold corpus sets, check_engine |
| Annotation client | Working | Label Studio REST client, sync, project manager |
| API (corpora, pipeline) | Working | FastAPI, 2 of 6 routers functional |
| Tests | 350+ functions | Engine, config, corpus, data, validation, E2E covered |

### Resolved blockers (Phase 0)

| ID | Resolution | Commit scope |
|----|-----------|--------------|
| B1 | M3 rule-based: prefix stripping (7 proclitics + chains), POS heuristics (PUNCT/NUM/ADP/ADV/PRON/VERB/ADJ/X/NOUN), hebpipe integration when available | `engine/hebpipe_wrappers.py` |
| B2 | `PipelineService.run(corpus_id)`: loads docs from DB, runs pipeline, saves pipeline_runs + terms | `pipeline/orchestrator.py` |
| B3 | 28 E2E tests: direct wiring, orchestrator, edge cases, DB integration | `tests/integration/test_pipeline_e2e.py` |
| B4 | `VALID_MODULES` = 9 NLP + 13 generative (22 total), 13 Pydantic sub-configs with validation | `pipeline/config.py` |

### Tech debt

| ID | Problem | Location |
|----|---------|----------|
| D1 | Docker: `LABEL_STUDIO_PASSWORD` hardcoded | `docker-compose.yml` |
| D2 | Docker: images unpinned (`:latest`) | `docker-compose.yml` |
| D3 | Docker: `service_started` instead of `service_healthy` | `docker-compose.yml` |
| D4 | API routers: validation, annotation, kb, llm are empty stubs | `api/routers/` |
| D5 | UI: all 7 widget files are 10-line stubs | `kadima/ui/` |
| D6 | `Token` dataclass declared in 2 places with different fields | `data/models.py` and `engine/hebpipe_wrappers.py` |

---

## File Layout

| What | Where | Example |
|------|-------|---------|
| NLP processors (M1-M8, M12) | `kadima/engine/<name>.py` | `term_extractor.py` |
| **Generative modules (M13-M25)** | `kadima/engine/<name>.py` | `diacritizer.py` |
| VRAM/model management | `kadima/engine/model_manager.py` | Lazy load + LRU eviction |
| Pipeline orchestration | `kadima/pipeline/` | `orchestrator.py`, `config.py` |
| Validation / gold corpus | `kadima/validation/` | `check_engine.py` |
| Corpus manager | `kadima/corpus/` | `importer.py`, `exporter.py` |
| Label Studio integration | `kadima/annotation/` | `ls_client.py`, `sync.py` |
| Knowledge Base | `kadima/kb/` | `repository.py`, `search.py` |
| LLM service | `kadima/llm/` | `client.py`, `prompts.py` |
| spaCy components | `kadima/nlp/components/` | `hebpipe_*.py` |
| DB / migrations | `kadima/data/` | `db.py`, `models.py`, `migrations/XXX.sql` |
| REST API | `kadima/api/routers/` | `corpora.py`, `generative.py` |
| API schemas | `kadima/api/schemas.py` | Pydantic models |
| PyQt UI | `kadima/ui/` | `main_window.py`, `widgets/` |
| Utils | `kadima/utils/` | `hebrew.py`, `logging.py` |
| Unit tests | `tests/<module>/test_<name>.py` | `tests/engine/test_term_extractor.py` |
| Integration tests | `tests/integration/` | `test_pipeline_e2e.py` |
| Gold corpus fixtures | `tests/data/he_XX_*/` | `expected_counts.yaml`, `raw/*.txt` |
| Label Studio templates | `templates/` | `hebrew_ner.xml` |
| Dev prompt / roadmap | `Tasks/Kadima_v2.md` | Phased implementation plan |

---

## Module Map (25 modules)

### NLP Pipeline (sequential: M1 -> M2 -> M3 -> M4 -> M5 -> M6 -> M7 -> M8 -> M12)

| ID | Module | File | I/O | Status |
|----|--------|------|-----|--------|
| M1 | Sentence Splitter | `hebpipe_wrappers.py` | `str -> SentenceSplitResult` | Working (regex, no HebPipe) |
| M2 | Tokenizer | `hebpipe_wrappers.py` | `str -> TokenizeResult` | Working (str.split, no HebPipe) |
| M3 | Morph Analyzer | `hebpipe_wrappers.py` | `List[Token] -> MorphResult` | **STUB**: lemma=surface, POS="NOUN" |
| M4 | N-gram Extractor | `ngram_extractor.py` | `List[List[Token]] -> NgramResult` | Working |
| M5 | NP Chunker | `np_chunker.py` | `List[MorphAnalysis] -> NPChunkResult` | Working |
| M6 | Canonicalizer | `canonicalizer.py` | `List[str] -> CanonicalResult` | Working |
| M7 | Association Measures | `association_measures.py` | `List[Ngram] -> AMResult` | Working |
| M8 | Term Extractor | `term_extractor.py` | `TermExtractInput -> TermResult` | Working |
| M12 | Noise Classifier | `noise_classifier.py` | `List[Token] -> NoiseResult` | Working |

### Generative Modules (on-demand, NOT sequential)

| ID | Module | File | Model | VRAM | I/O | Tier |
|----|--------|------|-------|------|-----|------|
| M13 | Diacritizer | `diacritizer.py` | phonikud-onnx / DictaBERT | <1GB | `str -> str` | 1 |
| M14 | Translator | `translator.py` | mBART-50 / OPUS-MT | 3GB | `str,lang -> str` | 1 |
| M15 | TTS Synthesizer | `tts_synthesizer.py` | XTTS v2 (Coqui) | 4GB | `str -> Path(WAV)` | 2 |
| M16 | STT Transcriber | `stt_transcriber.py` | Whisper large-v3 | 3-6GB | `Path(WAV) -> str` | 2 |
| M17 | NER Extractor | `ner_extractor.py` | HeQ-NER (dicta-il) | <1GB | `str -> List[Entity]` | 1 |
| M18 | Sentiment Analyzer | `sentiment_analyzer.py` | heBERT | <1GB | `str -> {label,score}` | 2 |
| M19 | Summarizer | `summarizer.py` | mT5-base | 2GB | `str -> str` | 2 |
| M20 | QA Extractor | `qa_extractor.py` | AlephBERT | <1GB | `{q,ctx} -> {answer,score}` | 2 |
| M21 | Morph Generator | `morph_generator.py` | Rules (no ML) | 0 | `lemma,pos -> List[MorphForm]` | 1 |
| M22 | Transliterator | `transliterator.py` | Rules + lookup | 0 | `str <-> str` | 1 |
| M23 | Grammar Corrector | `grammar_corrector.py` | T5-hebrew / LLM | 2-4GB | `str -> str` | 3 |
| M24 | Keyphrase Extractor | `keyphrase_extractor.py` | YAKE! / KeyBERT | <1GB | `str -> List[str]` | 3 |
| M25 | Paraphraser | `paraphraser.py` | mT5 / LLM | 2-4GB | `str -> List[str]` | 3 |

**All M13-M25 are NOT YET IMPLEMENTED.** See `Tasks/Kadima_v2.md` for phased plan.

**Tier meaning:** 1 = first to implement (rules-only or <1GB), 2 = ML-heavy, 3 = LLM-dependent.

---

## Architecture

### Two Pipeline Modes

```
CLI / API / GUI
      |
      v
PipelineService (pipeline/orchestrator.py)
      |
      +--- run_on_text(text) ---- NLP Pipeline (sequential) ----+
      |    M1 -> M2 -> M3 -> M4 -> M5 -> M6 -> M7 -> M8 -> M12 |
      |                                                          |
      +--- run_module(id, input) - Generative (on-demand) ------+
      |    M13..M25: each called independently by user request   |
      |                                                          |
      v                                                          v
Data Layer (data/)              Validation (validation/)
SQLite WAL + migrations         Gold corpus (26 sets)
```

**Key distinction:** NLP pipeline is a fixed chain. Generative modules are independent
services invoked on demand — they do NOT form a sequential pipeline.

### Processor Protocol

Every module implements `ProcessorProtocol` from `kadima/engine/contracts.py`:

```python
@runtime_checkable
class ProcessorProtocol(Protocol):
    @property
    def name(self) -> str: ...       # "diacritizer"
    @property
    def module_id(self) -> str: ...  # "M13"
    def process(self, input_data: Any, config: Dict[str, Any]) -> ProcessorResult: ...
    def validate_input(self, input_data: Any) -> bool: ...
```

Concrete base class: `kadima/engine/base.py::Processor` (ABC).

New generative modules additionally implement:
- `process_batch(inputs, config)` — batch processing
- Static metric methods specific to the module

### VRAM Management

ML modules use lazy loading. Not all models fit in VRAM simultaneously.

| Budget | Max simultaneous |
|--------|-----------------|
| RTX 3070 (8GB) | 2-3 small (<1GB) + 1 medium (2-3GB) |
| RTX 3060 (12GB) | 2-3 small + 1 large (4-6GB) |

**Rule:** Always check `torch.cuda.is_available()` before `.to("cuda")`.
**Rule:** ML imports wrapped in `try/except ImportError` with clear message.

### Module Registration (orchestrator)

```python
# NLP modules: imported directly (always available)
self.modules = {
    "sent_split": HebPipeSentSplitter(),
    "tokenizer": HebPipeTokenizer(),
    ...
}

# Generative modules: lazy-loaded, skip if unavailable
_optional = {
    "diacritizer": ("kadima.engine.diacritizer", "Diacritizer"),
    "translator":  ("kadima.engine.translator", "Translator"),
    ...
}
for name, (mod_path, cls_name) in _optional.items():
    if name not in self.config.modules:
        continue
    try:
        mod = importlib.import_module(mod_path)
        cls = getattr(mod, cls_name)
        self.modules[name] = cls(self.config.get_module_config(name))
    except ImportError as e:
        logger.warning("Module %s unavailable: %s", name, e)
```

---

## Configuration

| File | Purpose |
|------|---------|
| `pyproject.toml` | Dependencies (ranges), tool config, optional groups [ml]/[gpu]/[gui]/[dev] |
| `requirements.txt` | Pinned deps for Docker (core only) |
| `requirements-dev.txt` | Pinned dev deps |
| `config/config.default.yaml` | Default pipeline + module config |
| `config/config.schema.json` | JSON Schema (auto-generated from Pydantic) |
| `.env.example` | Required env vars template |
| `.env` | Actual secrets (gitignored) |

### Config structure (config.default.yaml)

```yaml
pipeline:
  language: he
  profile: balanced          # precise | balanced | recall
  modules: [sent_split, tokenizer, morph_analyzer, ...]
  thresholds: {min_freq: 2, pmi_threshold: 3.0, hapax_filter: true}

# Generative module configs (added as modules are implemented)
diacritizer:  {backend: phonikud, device: cuda}
translator:   {backend: mbart, device: cuda, default_tgt_lang: en}
tts:          {backend: xtts, device: cuda}
stt:          {backend: whisper, device: cuda}
ner:          {backend: heq_ner, device: cuda}
sentiment:    {backend: hebert, device: cuda}
summarizer:   {backend: mt5, device: cuda, max_length: 150}
qa:           {backend: alephbert, device: cuda}
morph_gen:    {gender: masculine, binyan: paal}
transliterator: {mode: latin}
grammar:      {backend: llm, device: cuda}
keyphrase:    {backend: yake, top_n: 10}
paraphrase:   {backend: mt5, device: cuda, num_variants: 1}

annotation:   {label_studio_url: ..., ml_backend_url: ...}
llm:          {enabled: false, server_url: ..., model: dictalm-3.0}
kb:           {enabled: false, embedding_model: neodictabert}
logging:      {level: INFO, file: ~/.kadima/logs/kadima.log}
storage:      {db_path: ~/.kadima/kadima.db, auto_backup: true}
```

---

## Database

### Current schema (4 migrations)

| Migration | Tables |
|-----------|--------|
| `001_initial.sql` | corpora, documents, tokens, lemmas, pipeline_runs, terms |
| `002_annotation.sql` | gold_corpora, expected_checks, review_results, annotation_* |
| `003_kb.sql` | kb_terms, kb_relations, kb_definitions |
| `004_llm.sql` | llm_conversations, llm_messages |

### Planned migration for M13-M25

```sql
-- 005_generative_results.sql (create when first generative module lands)
-- Tables: results_nikud, results_translation, results_tts,
--         results_ner, results_sentiment, results_summary, results_qa
```

### Migration commands

```bash
kadima migrate                     # Apply pending
kadima migrate --new add_foo       # Create XXX_name.sql
```

**Rule:** Never create tables in code. Only SQL migrations in `kadima/data/migrations/`.

---

## Dependencies

### Core (always installed)

| Package | Range | Purpose |
|---------|-------|---------|
| PyYAML | `>=6.0,<7` | Config loader |
| pydantic | `>=2.6,<3` | Validation, API schemas |
| spacy | `>=3.7,<4` | NLP pipeline |
| httpx | `>=0.27,<1` | HTTP client |
| fastapi | `>=0.110,<1` | REST API |
| uvicorn | `>=0.29,<1` | ASGI server |

### Optional groups

| Group | Packages | Purpose |
|-------|----------|---------|
| `[ml]` | transformers, sentencepiece, phonikud-onnx, onnxruntime, yake | M13-M25 CPU inference |
| `[gpu]` | torch (cu128), openai-whisper, TTS | GPU-accelerated M13-M25 |
| `[gui]` | PyQt6 | Desktop UI |
| `[hebpipe]` | hebpipe | Real morphological analysis for M3 |
| `[dev]` | pytest, pytest-cov, ruff, mypy | Development tools |

```bash
pip install -e ".[dev]"          # Dev without ML
pip install -e ".[ml,dev]"       # Dev with ML (CPU)
pip install -e ".[gpu,ml,dev]"   # Dev with ML (GPU)
```

---

## Testing

```bash
pytest tests/ -v                          # All tests
pytest tests/engine/ -v                   # Engine only
pytest tests/integration/ -v              # E2E pipeline
pytest tests/engine/test_diacritizer.py   # Specific module
make test                                 # Shortcut
make ci                                   # Full CI: lint + typecheck + tests
```

### Test structure per module

Each `tests/engine/test_<module>.py` must include:
1. **Unit tests for metrics** (no ML model needed, fast)
2. **`process()` with mock/lightweight model** or rules fallback
3. **`validate_input()` with invalid data** (returns False, no crash)
4. **`process()` with empty input** (returns FAILED status, no crash)
5. **Gold corpus validation** where applicable (via `tests/data/`)

### Gold corpus (26 sets)

Located in `tests/data/he_01_*` through `he_26_*`.
Each set: `expected_counts.yaml` + `raw/*.txt` + optional `expected_*.csv`.

Loaded via `conftest.py` fixtures: `gold_corpus_he_01`, `all_gold_corpora`.

---

## Docker

```bash
make build    # Build API image
make up       # API (8501) + Label Studio (8080)
make up-llm   # + llama.cpp (8081, GPU)
make down     # Stop all
```

### Environment

All secrets via `.env` file (gitignored). Copy `.env.example` to `.env` and fill in:

```bash
# .env.example
LS_API_KEY=                          # Label Studio API key
LABEL_STUDIO_PASSWORD=               # Label Studio admin password
HF_HOME=/path/to/huggingface/cache   # HuggingFace model cache
```

### GPU for generative modules

When M13-M25 are active, the `api` service needs GPU reservation:
```yaml
deploy:
  resources:
    reservations:
      devices:
        - capabilities: [gpu]
```

---

## API Endpoints

### Implemented

| Method | Path | Status |
|--------|------|--------|
| `GET` | `/health` | Working |
| `GET` | `/api/v1/corpora` | Working |
| `POST` | `/api/v1/corpora` | Working |
| `POST` | `/api/v1/pipeline/run-text` | Working |
| `POST` | `/api/v1/pipeline/run/{corpus_id}` | **Stub** (B2) |

### Planned (generative router)

`kadima/api/routers/generative.py`:

```
POST /api/v1/generative/diacritize    {text} -> {result}
POST /api/v1/generative/translate     {text, tgt_lang} -> {result}
POST /api/v1/generative/tts           {text} -> {audio_url}
POST /api/v1/generative/stt           {audio_url} -> {text}
POST /api/v1/generative/ner           {text} -> {entities}
POST /api/v1/generative/sentiment     {text} -> {label, score}
POST /api/v1/generative/summarize     {text} -> {summary}
POST /api/v1/generative/qa            {question, context} -> {answer}
POST /api/v1/generative/morph-gen     {lemma, pos} -> {forms}
POST /api/v1/generative/transliterate {text, mode} -> {result}
POST /api/v1/generative/grammar       {text} -> {corrected}
POST /api/v1/generative/keyphrase     {text} -> {keyphrases}
POST /api/v1/generative/paraphrase    {text} -> {paraphrases}
```

### Stub routers (need implementation)

- `api/routers/validation.py` — 5 TODO methods
- `api/routers/annotation.py` — 4 TODO methods
- `api/routers/kb.py` — 5 TODO methods
- `api/routers/llm.py` — 5 TODO methods

---

## Development Workflow

### Adding a new generative module

```
1. Create kadima/engine/<module>.py
   - Inherit from Processor (kadima/engine/base.py)
   - Implement: process(), process_batch(), validate_input()
   - Add static metric methods
   - Wrap ML imports: try/except ImportError
   - Check CUDA: torch.cuda.is_available() before .to("cuda")
   - Use: logger = logging.getLogger(__name__)
   - Add: Google-style docstrings on public methods

2. Create tests/engine/test_<module>.py
   - Metric unit tests (no model)
   - process() with mock model
   - validate_input() edge cases
   - Empty input handling

3. Register in pipeline/orchestrator.py
   - Add to _optional_modules dict
   - try/except ImportError on load

4. Add config section to config/config.default.yaml

5. Add API endpoint to api/routers/generative.py

6. Verify: pytest tests/ -v — ALL PASS

7. Commit: feat(engine): add M<XX> <ModuleName>
```

### Commit format

```
type(scope): short description (imperative, max 72 chars)

Types: feat | fix | refactor | test | docs | chore | perf | security
Scope: engine | pipeline | api | ui | data | config | docker | ci
```

### Before any change

1. `pytest tests/ -v` — must pass BEFORE your change
2. Read the code you are changing
3. Identify which tests cover the area

### After any change

1. `pytest tests/ -v` — must still pass
2. `ruff check kadima/` — 0 errors
3. No hardcoded secrets, no `print()`, no bare `except:`

---

## Code Conventions

### Typing
- Type annotations required on all public functions
- Engine layer: `@dataclass` for data. API layer: `pydantic.BaseModel`
- Config models: `pydantic.BaseModel` with `extra="forbid"`

### Error handling
- **Processors never crash** — return `ProcessorResult(status=FAILED, errors=[...])`
- ML dependencies: `try/except ImportError` with actionable message
- CUDA: always `torch.cuda.is_available()` before `.to("cuda")`
- Catch specific exceptions, never bare `except:`

### Logging
- `logger = logging.getLogger(__name__)` in every module
- Never `print()` outside CLI

### SQL
- All queries parameterized (`?` placeholders)
- Tables created only via migrations
- Never interpolate user input into SQL

### Paths
- Use `KADIMA_HOME` env var, never hardcoded absolute paths
- `os.path.expanduser()` for `~` paths

---

## What NOT to do

- Do not put NLP logic in `api/routers/` — routers call `engine/` or `pipeline/`
- Do not hardcode paths — use `KADIMA_HOME` env
- Do not create tables in code — only migrations
- Do not import ML modules without `try/except ImportError`
- Do not use CUDA without checking `torch.cuda.is_available()`
- Do not mix fixtures with real data
- Do not load all ML models simultaneously — respect VRAM budget
- Do not start M13-M25 work until blockers B1-B4 are resolved
- Do not break existing tests to add new features

---

## Quality Targets (v1.0.0)

| Metric | Target | How to measure |
|--------|--------|----------------|
| Tests | 100% PASS, >200 functions | `pytest tests/ -v` |
| Module coverage | 25/25 implemented | Files in `kadima/engine/` |
| API endpoints | 0 stubs | All routers return data |
| VRAM peak | <=8GB with 3 models | `nvidia-smi` under load |
| Nikud char accuracy | >0.95 | Gold corpus `expected_diacritics.csv` |
| NER F1 | >0.85 | Gold corpus `expected_ner.csv` |
| Translation BLEU | >30.0 (HE->EN) | Gold corpus `expected_translation.csv` |
| TTS->STT WER | <0.15 | Round-trip integration test |
| CI | Green on main | GitHub Actions |
| Security | 0 critical findings | `security-auditor` agent |

---

## Phased Roadmap

Detailed plan with patch series, VRAM budgets, and exit criteria:
**`Tasks/Kadima_v2.md`**

| Phase | Scope | Key deliverables |
|-------|-------|-----------------|
| 0 | Stabilization | Fix B1-B4, add CI, harden Docker, add [ml] deps |
| 1 | Tier 1 modules | M22, M21, M13, M17, M14 (rules + small ML) |
| 2 | Tier 2 modules | M18, M20, M19, M15, M16 (heavy ML + VRAM mgmt) |
| 3 | Tier 3 + infra | M24, M23, M25, full API, UI, PipelineService.run() |
| 4 | v1.0.0 release | Regression suite, load testing, security audit, docs |

---

## Reference

- Full technical spec: `doc/Техническое задание разработка KADIMA/`
- Gold corpus methodology: `tests/data/README.md`
- Validation strategy: `tests/data/VALIDATION_STRATEGY.md`
