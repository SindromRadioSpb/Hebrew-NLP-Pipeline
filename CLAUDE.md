# CLAUDE.md — Kadima Project Map

> **Python 3.10+** | **Package:** `kadima/` | **DB:** SQLite WAL + migrations
> **Conventions:** snake_case files/functions, PascalCase classes, UPPER_SNAKE constants
> **Target HW:** RTX 3060 12GB (dev) / RTX 3070 8GB (CI)
> **Version:** 0.9.x → 1.0.0 | **Current phase:** T5 (Phase 3: Keyphrase/Grammar/Summarizer + NLP Tools UI)

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

## Current Status (2026-04-01)

### What works

| Component | Status | Notes |
|-----------|--------|-------|
| Engine M1-M8, M12 | Working | M3 rule-based fallback + hebpipe integration |
| NP Chunker M5 | Working | Rules + transformer embeddings mode (R-2.1) |
| Pipeline `run_on_text()` | Working | Sequential M1->M8->M12 |
| Pipeline `run(corpus_id)` | Working | DB load + process + save pipeline_runs/terms |
| Pipeline config | Working | Pydantic v2, profiles, JSON Schema, M13-M25 sub-configs |
| Data layer | Working | WAL, FK, 4 migrations, parameterized queries |
| SQLAlchemy ORM | Working | 18 models, sync+async sessions, SA 2.x (R-2.6, R-2.7) |
| Validation | Working | 26 gold corpus sets, check_engine |
| Annotation client | Working | Label Studio REST client, sync, project manager |
| NER training pipeline | Working | LS JSON → CoNLL-U → spaCy Examples (R-2.3) |
| KB embedding search | Working | Cosine similarity over float32 BLOB vectors (R-2.4) |
| Term clusterer | Working | k-means / HDBSCAN / greedy on NeoDictaBERT vectors (R-2.5) |
| API (corpora, pipeline, generative) | Working | FastAPI, 3 of 6 routers functional |
| Generative M13, M14, M17, M21, M22 | Working | Rules + ML fallback, API endpoints live |
| NER M17 | Working | neodictabert → heq_ner → rules fallback chain (R-2.2) |
| Transformer backbone | Working | KadimaTransformer, doc.tensor, spaCy pipeline builder (T1) |
| Desktop UI (T3) | Working | MainWindow + 6 full views + 9 widgets + dark QSS theme + cross-view wiring |
| M15 TTSSynthesizer | **Working** (R-4.2) | XTTS v2 (Coqui) → MMS-TTS (facebook/mms-tts-heb) fallback; 30 tests |
| M16 STTTranscriber | **Working** (R-4.3) | openai-whisper → faster-whisper fallback; WER metric; 34 tests |
| M18 SentimentAnalyzer | **Working** (R-4.1) | heBERT → rules fallback; accuracy+macro_f1; 31 tests |
| M20 QAExtractor | **Working** (R-4.4) | AlephBERT QA; uncertainty_sample() → Label Studio; exact_match+F1; 49 tests |
| T4 widgets | Done | D10: BackendSelector, ExportButton, EntityTable, AudioPlayer created in `ui/widgets/` |
| GenerativeView (T4 Step 10) | **Working** | 6 tabs: Sentiment/TTS/STT/Translate/Diacritize/NER + GenerativeWorker |
| AnnotationView (T4 Step 11) | **Working** | Projects table + Tasks + AL Queue + Sync/Pre-annotate/Retrain buttons |
| Tests | 822 functions | Engine, config, corpus, data, validation, KB, E2E + 62 UI smoke tests |

### Resolved blockers (Phase 0)

| ID | Resolution | Commit scope |
|----|-----------|--------------|
| B1 | M3 rule-based: prefix stripping (7 proclitics + chains), POS heuristics (PUNCT/NUM/ADP/ADV/PRON/VERB/ADJ/X/NOUN), hebpipe integration when available | `engine/hebpipe_wrappers.py` |
| B2 | `PipelineService.run(corpus_id)`: loads docs from DB, runs pipeline, saves pipeline_runs + terms | `pipeline/orchestrator.py` |
| B3 | 28 E2E tests: direct wiring, orchestrator, edge cases, DB integration | `tests/integration/test_pipeline_e2e.py` |
| B4 | `VALID_MODULES` = 9 NLP + 13 generative (22 total), 13 Pydantic sub-configs with validation | `pipeline/config.py` |

### Tech debt

| ID | Problem | Location | Priority |
|----|---------|----------|----------|
| D4 | API routers: validation, annotation, kb, llm are empty stubs (16 TODO endpoints) | `api/routers/` | T5 |
| D5 | ~~UI: main_window + 7 view files are 10-line stubs~~ **CLOSED in T3** | `kadima/ui/` | — |
| D6 | `Token` dataclass declared in 2 places with different fields (different layers, no conflict) | `data/models.py` + `engine/hebpipe_wrappers.py` | Low |
| D7 | SQLAlchemy ORM added alongside legacy sqlite3 — UI uses legacy layer by design | `data/repositories.py` | Won't fix |
| D8 | ~~T3 connective tissue: 7 view signals unwired~~ **CLOSED** — `_wire_all()` + `_wired:set` + 6 cross-view connections + `trigger_run_for_corpus()` | `kadima/ui/main_window.py` | — |
| D9 | ~~Engine stubs M15/M16/M18/M20 missing~~ **CLOSED** — 4 stub files created, registered in orchestrator | `kadima/engine/` | — |
| D10 | ~~T4 widgets missing~~ **CLOSED** — BackendSelector, ExportButton, EntityTable, AudioPlayer created | `kadima/ui/widgets/` | — |
| D11 | `test_term_clusterer.py::TestSilhouette::test_two_clusters` pre-existing failure — silhouette score == 0.0 on synthetic data | `tests/engine/test_term_clusterer.py` | Low |

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
| PyQt UI views (T3) | `kadima/ui/*_view.py` | `dashboard_view.py`, `pipeline_view.py` |
| PyQt UI widgets | `kadima/ui/widgets/` | `status_card.py`, `rtl_text_edit.py` |
| UI entry point | `kadima/ui/main_window.py`, `kadima/app.py` | `kadima gui` → `app.main()` |
| UI styles | `kadima/ui/styles/` | `app.qss`, `dark.qss` |
| Utils | `kadima/utils/` | `hebrew.py`, `logging.py` |
| Unit tests | `tests/<module>/test_<name>.py` | `tests/engine/test_term_extractor.py` |
| UI tests | `tests/ui/test_*.py` | `test_dashboard_view.py` (pytest-qt) |
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
| M3 | Morph Analyzer | `hebpipe_wrappers.py` | `List[Token] -> MorphResult` | Working (rule-based: prefix strip + POS heuristics; hebpipe fallback) |
| M4 | N-gram Extractor | `ngram_extractor.py` | `List[List[Token]] -> NgramResult` | Working |
| M5 | NP Chunker | `np_chunker.py` | `List[MorphAnalysis] -> NPChunkResult` | Working |
| M6 | Canonicalizer | `canonicalizer.py` | `List[str] -> CanonicalResult` | Working |
| M7 | Association Measures | `association_measures.py` | `List[Ngram] -> AMResult` | Working |
| M8 | Term Extractor | `term_extractor.py` | `TermExtractInput -> TermResult` | Working |
| M12 | Noise Classifier | `noise_classifier.py` | `List[Token] -> NoiseResult` | Working |

### Generative Modules (on-demand, NOT sequential)

| ID | Module | File | Model | VRAM | I/O | Tier | Status |
|----|--------|------|-------|------|-----|------|--------|
| M13 | Diacritizer | `diacritizer.py` | phonikud-onnx / DictaBERT | <1GB | `str -> str` | 1 | **Working** (rules + ML fallback) |
| M14 | Translator | `translator.py` | mBART-50 / OPUS-MT | 3GB | `str,lang -> str` | 1 | **Working** (dict + ML fallback) |
| M15 | TTS Synthesizer | `tts_synthesizer.py` | XTTS v2 (Coqui) | 4GB | `str -> Path(WAV)` | 2 | **Working** (xtts → mms fallback, R-4.2) |
| M16 | STT Transcriber | `stt_transcriber.py` | Whisper large-v3 | 3-6GB | `Path(WAV) -> str` | 2 | **Working** (whisper → faster-whisper fallback, R-4.3) |
| M17 | NER Extractor | `ner_extractor.py` | HeQ-NER (dicta-il) | <1GB | `str -> List[Entity]` | 1 | **Working** (gazetteer + ML fallback) |
| M18 | Sentiment Analyzer | `sentiment_analyzer.py` | heBERT | <1GB | `str -> {label,score}` | 2 | **Working** (hebert → rules fallback, R-4.1) |
| M19 | Summarizer | — | mT5-base | 2GB | `str -> str` | 2 | Not created (R-5.3) |
| M20 | QA Extractor | `qa_extractor.py` | AlephBERT | <1GB | `{q,ctx} -> {answer,score}` | 2 | **Working** (alephbert + uncertainty sampling, R-4.4) |
| M21 | Morph Generator | `morph_generator.py` | Rules (no ML) | 0 | `lemma,pos -> List[MorphForm]` | 1 | **Working** (7 binyanim, noun/adj inflection) |
| M22 | Transliterator | `transliterator.py` | Rules + lookup | 0 | `str <-> str` | 1 | **Working** (Academy + IPA + reverse) |
| M23 | Grammar Corrector | — | T5-hebrew / LLM | 2-4GB | `str -> str` | 3 | Not created (R-5.2) |
| M24 | Keyphrase Extractor | — | YAKE! / KeyBERT | <1GB | `str -> List[str]` | 3 | Not created (R-5.1) |
| M25 | Paraphraser | — | mT5 / LLM | 2-4GB | `str -> List[str]` | 3 | Not created |

**Phase 1 (Tier 1) complete:** M13, M14, M17, M21, M22 implemented with rules + ML fallback.
**Phase 2 (Tier 2) DONE:** M15 TTS (XTTS→MMS), M16 STT (Whisper→faster-whisper), M18 Sentiment (heBERT→rules), M20 QA (AlephBERT + uncertainty sampling).
**T5 next (Tier 3):** M24 Keyphrase (YAKE), M23 Grammar (Dicta-LM), M19/M25 Summarizer/Paraphraser (Dicta-LM).

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
| `POST` | `/api/v1/pipeline/run/{corpus_id}` | Working |
| `POST` | `/api/v1/generative/transliterate` | Working (M22) |
| `POST` | `/api/v1/generative/morph-gen` | Working (M21) |
| `POST` | `/api/v1/generative/diacritize` | Working (M13) |
| `POST` | `/api/v1/generative/ner` | Working (M17) |
| `POST` | `/api/v1/generative/translate` | Working (M14) |

### Planned (generative router — Tier 2/3)

```
POST /api/v1/generative/tts           {text} -> {audio_url}      (M15, Tier 2)
POST /api/v1/generative/stt           {audio_url} -> {text}      (M16, Tier 2)
POST /api/v1/generative/sentiment     {text} -> {label, score}   (M18, Tier 2)
POST /api/v1/generative/summarize     {text} -> {summary}        (M19, Tier 2)
POST /api/v1/generative/qa            {question, context} -> {answer} (M20, Tier 2)
POST /api/v1/generative/grammar       {text} -> {corrected}      (M23, Tier 3)
POST /api/v1/generative/keyphrase     {text} -> {keyphrases}     (M24, Tier 3)
POST /api/v1/generative/paraphrase    {text} -> {paraphrases}    (M25, Tier 3)
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
- Do not break existing tests to add new features

---

## Desktop UI (T3–T5)

Full TZ: `Tasks/3. TZ_UI_desktop_KADIMA.md`

### Entry Point

```
kadima gui  →  cli.py::run_gui()  →  app.py::main()  →  MainWindow (QStackedWidget)
```

`kadima/app.py` and `main_window.py` fully implemented (T3 complete). Cross-view wiring via `_wire_all()` (D8 closed).

### View Map

| # | View file | Phase | Key data sources |
|---|-----------|-------|-----------------|
| 1 | `dashboard_view.py` | **T3** | `data/repositories.py` (runs), `corpus/statistics.py`, pipeline status |
| 2 | `pipeline_view.py` | **T3** | `pipeline/orchestrator.py`, `pipeline/config.py`, `PipelineWorker(QRunnable)` |
| 3 | `results_view.py` | **T3** | `PipelineResult` → `TermsTableModel(QAbstractTableModel)`, `corpus/exporter.py` (5 formats) |
| 4 | `validation_view.py` | **T3** | `validation/check_engine.py`, `validation/report.py`, `ResultColorDelegate` |
| 5 | `kb_view.py` | **T3** | `kb/repository.py`, `kb/search.py` (text + embedding + similar), `kb/generator.py` |
| 6 | `corpora_view.py` | **T3** | `corpus/importer.py` (`.txt .csv .conllu .json`), `corpus/statistics.py` |
| 7 | `generative_view.py` | T4 | M13/M14/M17/M18/M15/M16 via engine modules, `GenerativeWorker(QRunnable)` |
| 8 | `annotation_view.py` | T4 | `annotation/project_manager.py`, `annotation/sync.py`, `annotation/ner_training.py` |
| 9 | `nlp_tools_view.py` | T5 | M23/M24/M25 (Grammar/Keyphrase/Summarize) via engine modules |
| 10 | `llm_view.py` | T5 | `llm/service.py` (define_term, explain_grammar, chat), `llm/client.py` (is_loaded) |

### Widget Map

| Widget file | New/Existing | Used by |
|-------------|-------------|---------|
| `widgets/error_dialog.py` | Exists | All views |
| `widgets/progress_bar.py` | Exists | Pipeline view |
| `widgets/term_table.py` | Exists | Results view |
| `widgets/status_card.py` | **NEW T3** | Dashboard |
| `widgets/rtl_text_edit.py` | **NEW T3** | Pipeline, KB, Generative, LLM |
| `widgets/ngram_table.py` | **NEW T3** | Results |
| `widgets/np_chunk_table.py` | **NEW T3** | Results |
| `widgets/check_table.py` | **NEW T3** | Validation |
| `widgets/backend_selector.py` | **Done pre-T4** | Pipeline, Generative |
| `widgets/export_button.py` | **Done pre-T4** | Results, Validation, KB |
| `widgets/entity_table.py` | **Done pre-T4** | Generative (NER tab) |
| `widgets/audio_player.py` | **Done pre-T4** | Generative (TTS tab) |
| `widgets/chat_widget.py` | NEW T5 | LLM view |

### T3 Steps (all DONE)

```
Step 1:  main_window.py — QMainWindow + QStackedWidget + MenuBar + ToolBar + StatusBar + lazy view loading  ✅
Step 2:  widgets/status_card.py + dashboard_view.py — 3 status cards + recent runs + quick actions          ✅
Step 3:  widgets/rtl_text_edit.py + pipeline_view.py — module toggles + PipelineWorker(QRunnable)           ✅
Step 4:  widgets/ngram_table.py + widgets/np_chunk_table.py + results_view.py — TermsTableModel + export     ✅
Step 5:  widgets/check_table.py + validation_view.py — PASS/WARN/FAIL + ResultColorDelegate                  ✅
Step 6:  kb_view.py — text/embedding/similar search + definition editor + cluster view                       ✅
Step 7:  corpora_view.py — import + corpus table + statistics + pipeline trigger                             ✅
Step 8:  styles/app.qss — design tokens, dark theme                                                          ✅
Step 9:  tests/ui/test_main_window.py — 28 pytest-qt smoke tests                                            ✅
pre-T4: D8 _wire_all() cross-view signals | D9 stubs M15/M16/M18/M20 | D10 T4 widgets                       ✅
```

### T4 Steps (NOW — active)

```
R-4.1:  sentiment_analyzer.py — implement heBERT backend + rules fallback  ← NEXT
R-4.2:  tts_synthesizer.py — implement Coqui XTTS v2 backend
R-4.3:  stt_transcriber.py — implement Whisper large-v3 backend
R-4.4:  active_learning.py — uncertainty sampling → Label Studio export
Step 10: generative_view.py — 6 tabs: Sentiment/TTS/STT/Translate/Diacritize/NER
         + GenerativeWorker(QRunnable) + model lazy loading
Step 11: annotation_view.py — LS projects + pre-annotate + AL queue
Step 12: tests/ui/test_generative.py + test_annotation.py
```

### T5 Steps (pending)

```
R-5.1:  keyphrase_extractor.py — YAKE! backend
R-5.2:  grammar_corrector.py — Dicta-LM backend via llm/service.py
R-5.3:  summarizer.py — Dicta-LM / mT5 backend
Step 13: widgets/chat_widget.py + nlp_tools_view.py — Grammar/Keyphrase/Summarize tabs
Step 14: llm_view.py — chat + presets + context selector
Step 15: tests/ui/test_nlp_tools.py + test_llm.py
```

### T4 GenerativeView Layout Spec (Step 10)

```
GenerativeView — QTabWidget with 6 tabs, each tab pattern:
┌────────────────────────────────────┐
│ BackendSelector (backend + device) │
├────────────────────────────────────┤
│ Input RTLTextEdit                  │
│ [▶ Run]  [🔄 Clear]                │
├────────────────────────────────────┤
│ Result QTextEdit (read-only, RTL)  │
│ [📋 Copy]  [📥 Export]             │
├────────────────────────────────────┤
│ Status: "Ready"  VRAM: N MB        │
└────────────────────────────────────┘

Tab-specific:
  Sentiment  → hebert/rules  → colored QLabel "Positive (0.92)"
  TTS        → xtts/mms      → AudioPlayer widget + voice selector
  STT        → whisper       → QFileDialog + editable transcript
  Translate  → mbart/opus    → lang selector HE↔EN toggle
  Diacritize → phonikud/dicta/rules → RTLTextEdit with nikud
  NER        → neodictabert/heq_ner/rules → EntityTable widget

GenerativeWorker(QRunnable) — one per tab, uses QThreadPool.
objectName format: "generative_{tab}_{zone}" e.g. "generative_sentiment_input"
Signal: generative_finished_signal = pyqtSignal(str, object)  # (tab_name, result)
```

### UI Architecture Rules

**Cross-view wiring (MainWindow responsibility)**:
All inter-view signal connections live in `MainWindow._wire_views()`, called lazily after both views are created via `_get_or_create_view()`. Pattern:
```python
# pipeline → results (auto-switch on finish)
pipe_view.run_finished_signal.connect(lambda r: (self._switch_view(2), results_view.load_results(r)))
# corpora → pipeline (run by corpus_id)
corpora_view.pipeline_run_requested.connect(lambda cid: (self._switch_view(1), pipe_view.set_corpus(cid), pipe_view.trigger_run()))
# results → KB (open term)
results_view.kb_open_requested.connect(lambda t: (self._switch_view(4), kb_view.search(t)))
# validation run → ValidationWorker
validation_view.run_validation_requested.connect(self._run_validation)
# dashboard quick actions → switch_to
dashboard_view.quick_run_clicked.connect(lambda: self._switch_view(1))
dashboard_view.results_clicked.connect(lambda: self._switch_view(2))
dashboard_view.kb_clicked.connect(lambda: self._switch_view(4))
```

**Threading** (non-negotiable):
- Pipeline runs in `PipelineWorker(QRunnable)` → `QThreadPool`
- Generative calls in `GenerativeWorker(QRunnable)` → `QThreadPool`
- Never call `orchestrator.run*()` or engine modules from main thread

**Data layer** (UI uses legacy layer):
- UI reads/writes via `data/repositories.py` (sqlite3) + `pipeline/orchestrator.py`
- SA ORM (`sa_db.py`) only for new queries needing type safety
- Never mix two layers in one view

**Layout** — layout managers only (QVBoxLayout/QHBoxLayout/QGridLayout/QSplitter):
- No absolute positioning (`move()`, `setGeometry()`)
- Min window: 1280×720
- RTL: `setLayoutDirection(Qt.LayoutDirection.RightToLeft)` for Hebrew text inputs
- All tables: `QHeaderView.Stretch` on main column

**Naming** — `objectName` required for pytest-qt + QSS:
- Format: `<view>_<zone>_<widget>_<purpose>`
- Examples: `pipeline_run_button`, `results_terms_table`, `kb_search_input`

**Signals** — format: `<noun>_<verb>_signal`:
```python
run_finished_signal = pyqtSignal(object)        # PipelineResult
run_progress_signal = pyqtSignal(int, str)       # (percent, module_name)
corpus_selected_signal = pyqtSignal(int)         # corpus_id
term_selected_signal = pyqtSignal(object)        # KBTerm
```

**States** — every view must handle all 4:
- Empty: explanatory message + icon
- Loading: spinner + "Processing..."
- Ready: data displayed
- Error: `ErrorDialog` + red warning label

**PyQt6 imports** — lazy, always wrapped:
```python
try:
    from PyQt6.QtWidgets import ...
except ImportError:
    raise ImportError("PyQt6 required. Install with: pip install -e '.[gui]'")
```

**Export** — Results: 5 formats (CSV/JSON/TBX/TMX/CoNLL-U) via `corpus/exporter.py`; Validation: 2 formats (CSV/JSON) via `validation/report.py`

**Hotkeys** (global):
| Key | Action |
|-----|--------|
| F5 | Run pipeline |
| Esc | Stop pipeline |
| Ctrl+E | Export current table |
| Ctrl+F | Focus filter/search |
| Ctrl+1–6 | Switch view |
| Ctrl+I | Import corpus |

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

## Roadmap (TZ: углубление функционала)

Полный план — `Tasks/TZ_uglublenie_funkcionala_KADIMA.md`.
Источники аудита — `Tasks/Источники/`.

### Завершённые фазы

| Фаза | Содержание | Статус |
|------|-----------|--------|
| Phase 0 | Стабилизация: B1–B4, CI, Docker, deps | **DONE** |
| Phase 1 | Tier 1 генеративные: M22, M21, M13, M17, M14; generative router (5 endpoints) | **DONE** |
| T1 | Transformer backbone: spacy-transformers, KadimaTransformer, pipeline builder, config.cfg | **DONE** |
| T2 | Embeddings+data: NP chunker emb mode, NER neodictabert, NER training pipeline, KB emb search, term clusterer, SA ORM, async SA, model download script | **DONE** |
| T3 | Desktop UI: MainWindow + 6 full views + 9 widgets + app.qss dark theme + 28 smoke tests | **DONE** |
| pre-T4 | D8 cross-view wiring, D9 engine stubs M15/M16/M18/M20, D10 T4 widgets | **DONE** |

### Текущий план (по ТЗ углубления)

| Tier | Набор | Требования | Статус | Часов |
|------|-------|-----------|--------|-------|
| **T1** | Transformer backbone | R-1.1 spacy-transformers в core deps | **DONE** | 1 |
| | | R-1.2 NeoDictaBERT component (`nlp/components/transformer_component.py`) | **DONE** | 8–12 |
| | | R-1.3 Pipeline builder с `use_transformer` flag | **DONE** | 4–6 |
| | | R-1.4 Graceful degradation (no VRAM / no model) | **DONE** | 2–3 |
| | | R-1.5 pyproject.toml — hebpipe/numpy/scipy/pandas в core | **DONE** | 2 |
| | | R-1.6 spaCy `config/config.cfg` с transformer backbone | **DONE** | 3–4 |
| **T2** | Embeddings + data | R-2.1 M5 NP Chunker — transformer embeddings mode | **DONE** | 6–8 |
| | | R-2.2 M17 NER — NeoDictaBERT backend + fallback chain | **DONE** | 8–10 |
| | | R-2.3 NER training pipeline (Label Studio → spaCy) | **DONE** | 4–6 |
| | | R-2.4 KB embedding search (cosine similarity) | **DONE** | 4–6 |
| | | R-2.5 Term clustering (k-means / HDBSCAN) | **DONE** | 3–4 |
| | | R-2.6 SQLAlchemy migration (sqlite3 → SA 2.x + Alembic) | **DONE** | 8–12 |
| | | R-2.7 Async data layer (aiosqlite + SA async sessions) | **DONE** | 4–6 |
| | | R-2.8 Model download script (`scripts/download_models.sh`) | **DONE** | 2–3 |
| **T3** | Desktop UI | Step 1: `main_window.py` — QMainWindow + QStackedWidget + MenuBar + lazy views | **DONE** | 4–6 |
| | | Step 2: `widgets/status_card.py` + `dashboard_view.py` | **DONE** | 3–4 |
| | | Step 3: `widgets/rtl_text_edit.py` + `pipeline_view.py` + PipelineWorker | **DONE** | 4–6 |
| | | Step 4: `widgets/ngram_table.py` + `widgets/np_chunk_table.py` + `results_view.py` | **DONE** | 4–6 |
| | | Step 5: `widgets/check_table.py` + `validation_view.py` + ResultColorDelegate | **DONE** | 3–4 |
| | | Step 6: `kb_view.py` — text/embedding/similar search + definition editor | **DONE** | 4–6 |
| | | Step 7: `corpora_view.py` — import + statistics + pipeline trigger | **DONE** | 3–4 |
| | | Step 8: `styles/app.qss` — design tokens, dark theme | **DONE** | 2–3 |
| | | Step 9: `tests/ui/test_main_window.py` — 29 pytest-qt smoke tests (skip if no PyQt6) | **DONE** | 4–6 |
| **pre-T4** | T3 wiring + stubs | D8/D9/D10 — все закрыты | **DONE** | — |
| **T4** | Phase 2 + UI | R-4.1 M18 Sentiment Classifier (heBERT + rules fallback) | **DONE** | 4–6 |
| | | R-4.2 M15 TTS (Coqui XTTS v2 + MMS fallback) | **DONE** | 6–8 |
| | | R-4.3 M16 STT (Whisper large-v3 + faster-whisper fallback) | **DONE** | 6–8 |
| | | R-4.4 M20 Active Learning (uncertainty sampling → LS export) | **DONE** | 6–8 |
| | | Step 10: `generative_view.py` — 6 tabs: Sentiment/TTS/STT/Translate/Diacritize/NER + GenerativeWorker | **DONE** | 6–8 |
| | | Step 11: `annotation_view.py` — LS projects + pre-annotate + AL queue | **DONE** | 4–6 |
| | | Step 12: `tests/ui/test_generative.py` + `tests/ui/test_annotation.py` | **DONE** | 2–3 |
| **T5** | Phase 3 + UI | R-5.1 M24 Keyphrase (YAKE) | Pending | 3–4 |
| | | R-5.2 M23 Grammar Checker (Dicta-LM) | Pending | 4–6 |
| | | R-5.3 M25 Summarizer (Dicta-LM) | Pending | 4–6 |
| | | Step 13: `widgets/chat_widget.py` + `nlp_tools_view.py` — Grammar/Keyphrase/Summarize | Pending | 3–4 |
| | | Step 14: `llm_view.py` — chat + presets + context selector | Pending | 3–4 |
| | | Step 15: `tests/ui/test_nlp_tools.py` + `test_llm.py` | Pending | 2–3 |
| **T6** | Infrastructure | R-6.1 Docker Compose production-ready | Pending | 3–5 |
| | | R-6.2 Документация синхронизация | Pending | 2–3 |

**Порядок выполнения:**
```
T1 (R-1.1→R-1.6) → T2-embeddings (R-2.1→R-2.5) → T2-data (R-2.6→R-2.8) [параллельно с T2-emb]
→ T3 (R-3.1→R-3.4) → T4 (R-4.1→R-4.4) → T5 (R-5.1→R-5.3) → T6
```

**Зависимости:**
- T2 embeddings (R-2.1–R-2.5) требует R-1.2 (NeoDictaBERT)
- T2 data (R-2.6–R-2.7) независим от T1
- T3 требует R-2.6 (SQLAlchemy)
- T4/T5 независимы от T1–T3 (кроме R-4.4 → R-2.2)

---

## Reference

- Full technical spec: `doc/Техническое задание разработка KADIMA/`
- Gold corpus methodology: `tests/data/README.md`
- Validation strategy: `tests/data/VALIDATION_STRATEGY.md`
