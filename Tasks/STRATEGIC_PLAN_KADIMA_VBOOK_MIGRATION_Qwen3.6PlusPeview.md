# STRATEGIC PLAN: KADIMA → HDLE-Grade Hebraic Dynamic Lexicon Engine

> **Date:** 2026-04-01
> **Source:** Analysis of V_book HDLE Premium (mature product) vs. KADIMA (growing prototype)
> **Goal:** Scale KADIMA to production-grade Hebraic Dynamic Lexicon Engine using V_book's best practices while retaining KADIMA's unique capabilities

---

## 1. Executive Summary

### V_book HDLE Premium — What It Has Achieved

| Dimension | Status | Details |
|-----------|--------|---------|
| **Milestones** | M1–M11 complete | Core NLP, UI, TM, batch translation, export, project exchange |
| **Database** | Schema v42+ | WAL mode, FTS5, schema versioning, reference DB attachment, migration framework |
| **UI** | Full PyQt6 desktop | 30+ dialogs/views, Project Dashboard, cold-audit optimized |
| **Performance** | Cold-audit framework | 32+ cold-audit waves, bounded UI latency, staged first-paint contracts |
| **Security** | FTS5/CSV/log injection, credential encryption, audit logging | Complete security hardening |
| **Testing** | Multi-wave smoke, P1/P2/P3 verification tiers, CI gates | 200+ targeted regression tests |
| **Engineering Discipline** | Definition of Done, evidence-first, decision-gate framework | Production-ready release gates |
| **Architecture** | Clean domain/services/infra/domain layers | Pluggable NLP engines (Stanza), subprocess workers |

### KADIMA — What We Have

| Dimension | Status | Details |
|-----------|--------|---------|
| **Modules** | 25 modules (M1-M25) | M1-M8, M12 NLP pipeline + M13-M25 generative modules |
| **Architecture** | Layered: engine/pipeline/data/api/ui/annotation/kb/llm | Processor Protocol, VRAM management |
| **UI** | Desktop PyQt6 (T3-T4 done, T5 pending) | 6 views + widgets, dark theme, cross-view wiring |
| **Testing** | 822 test functions, gold corpus (26 sets) | Engine, config, corpus, validation, E2E, UI smoke |
| **Data** | SQLite + SQLAlchemy 2.x + 4 migrations | WAL mode, FK, FTS5 |
| **Unique** | Dicta-LM integration, NER training, KB embedding search, term clustering | More AI/ML capabilities than V_book |

### Key Gap Analysis

| Area | V_book | KADIMA | Gap Severity |
|------|--------|--------|--------------|
| **Database** | Schema v42, reference DBs, FTS5 mastery, migration discipline | 4 migrations, basic SQLite | 🔴 HIGH |
| **Cold-start Performance** | 32 cold-audit waves, staged first-paint, bounded latency | No cold-audit, blocking UI | 🔴 HIGH |
| **Production Readiness** | Release gates, prebuild validation, installer, frozen builds | Docker, CLI — not production-hardened | 🔴 HIGH |
| **Security** | Injection prevention, credential encryption, audit logging | Basic input validation | 🟡 MEDIUM |
| **Engineering Process** | DoD, cold-audit framework, evidence-first patches, decision gates | Roadmap, phases, no rigorous QA gates | 🟡 MEDIUM |
| **NLP Engine** | Stanza subprocess isolation, subprocess-based heavy ops | In-process Stanza, hebpipe | 🟡 MEDIUM |
| **Reference Corpus** | Hebrew Wikipedia baseline (387k docs), processed DB | No reference corpus | 🟡 MEDIUM |
| **Batch Translation** | Multi-provider chain, force mode, progress tracking | Single provider + rules fallback | 🟢 LOW |
| **Project Management** | Project exchange (.hdleproj), project dashboard | Basic corpus management | 🟢 LOW |
| **Unique Capabilities** | TM/translation focus | Diacritize/TTS/STT/NER/QA/Grammar/Keyphrase | ✅ KADIMA LEADS |

---

## 2. Strategic Architecture — Future State

### 2.1 Layered Architecture (V_book-inspired, KADIMA-enhanced)

```
┌─────────────────────────────────────────────────────────────────┐
│                     UI Layer (PyQt6)                              │
│  ├── Dialog/View system (V_book dialog patterns)                  │
│  ├── Cold-audit staged first-paint contracts                     │
│  ├── Project Dashboard + 8+ views                               │
│  └── Worker threads (QRunnable) with heavy-slot governance       │
├─────────────────────────────────────────────────────────────────┤
│                     Services Layer                               │
│  ├── NLP Service (pluggable engines: Stanza + HebPipe)          │
│  ├── Term Extraction Service (profiles: precise/balanced/recall) │
│  ├── Concordance Service (FTS5-optimized)                       │
│  ├── Translation Memory Service (V_book M7 + P2 contracts)       │
│  ├── Dictionary Service + User Dictionaries                      │
│  ├── Export Service (Excel, CSV, JSONL, TBX, TMX, CoNLL-U)       │
│  ├── Audio/TTS/STT Service                                     │
│  ├── Project Exchange Service (.kadimaproc bundles)              │
│  ├── Backup & Recovery Service                                 │
│  └── Health Check Service                                       │
├─────────────────────────────────────────────────────────────────┤
│                     Domain Layer                                 │
│  ├── Hebrew preprocessing (maqaf, geresh, prefix stripping)     │
│  ├── KWIK/KWIC domain models                                    │
│  ├── Term extraction DTOs                                       │
│  ├── TM normalization contracts                                 │
│  └── Hebrew Utils (niqqud, homograph support)                   │
├─────────────────────────────────────────────────────────────────┤
│                     Infrastructure Layer                          │
│  ├── Database: SQLite WAL + FTS5 + SQLAlchemy 2.x               │
│  ├── NLP Engines: Stanza subprocess + HebPipe + rules fallback  │
│  ├── FTS5 Manager (auto-health, parity repair)                  │
│  ├── Settings (encrypted credentials, QSettings)                 │
│  ├── Resource paths (cross-platform)                             │
│  ├── Write Gate (runtime heavy-operation slot)                   │
│  ├── DB Retry (SQLITE_BUSY handling)                           │
│  ├── Reference DB Guard (attach read-only reference DBs)        │
│  └── Migrations (schema versioning, idempotent)                 │
├─────────────────────────────────────────────────────────────────┤
│                     Data Layer                                    │
│  ├── Schema v10+ (evolution from current 4)                     │
│  ├── 18+ SA models (expanded from 18)                           │
│  ├── Async + Sync sessions                                     │
│  └── Repository pattern                                        │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 What Stays, What Goes, What Changes

| Component | Decision | Rationale |
|-----------|----------|-----------|
| `kadima/engine/` (M1-M25) | **KEEP + ENHANCE** | KADIMA's 25 modules are more extensive than V_book's — use this strength |
| `kadima/pipeline/orchestrator.py` | **KEEP + ADD** throttler, heavy-slot | Add V_book's operations_center pattern |
| `kadima/data/` migrations | **EXPAND** from 4 → 10+ | V_book has 42 migrations; match their discipline |
| `kadima/ui/` views | **ADOPT** V_book dialog patterns | Staged first-paint, cold-audit compliance |
| `kadima/llm/` (Dicta-LM) | **KEEP + ELEVATE** | V_book has no LLM integration — unique advantage |
| `kadima/kb/` embedding search | **KEEP + ELEVATE** | V_book lacks KB — unique advantage |
| `kadima/annotation/` (Label Studio) | **KEEP** | V_book lacks annotation pipeline |
| Engine module stubs | **ELIMINATE** — implement real backends | No more stubs: all 25 modules must be production-ready |
| `kadima/api/` (FastAPI) | **FILL** stub routers | 16 TODO endpoints must be implemented |

---

## 3. phased Implementation Plan

### PHASE P0: Foundation & Engineering Discipline (Weeks 1-3)

#### P0.1 Adopt V_book's Quality Gates
| Item | Source V_book | Implementation Effort |
|------|---------------|----------------------|
| Definition of Done document | DEFINITION_OF_DONE.md | Copy + adapt to KADIMA |
| Release ship gate script | `scripts/prebuild_validate.py` | Create `scripts/prebuild_validate.py` for KADIMA |
| P1 verification framework | `app/tools/p1_verify.py` | Create `kadima/tools/p1_verify.py` |
| CI scripts (PowerShell/Bash) | V_book CI | Create `scripts/ci_run_tests.ps1/sh` |
| Self-check modes | `--self-check import/db_open/health` | Add to `kadima/cli.py` |
| **Effort:** | | **40 hours** |

#### P0.2 Database Schema Expansion
| Item | Source V_book | Implementation Effort |
|------|---------------|----------------------|
| Schema versioning (upgrade 4→10+) | schema v42 pattern | Write migrations 005-010 |
| FTS5 manager with auto-health | `infra/fts_manager.py` | Create `kadima/infra/fts_manager.py` |
| Write gate / heavy-operation slot | `infra/write_gate.py` | Create `kadima/infra/write_gate.py` |
| DB retry discipline | `infra/db_retry.py` | Create `kadima/infra/db_retry.py` |
| Reference DB guard | `infra/reference_guard.py` | Create `kadima/infra/reference_guard.py` |
| **Effort:** | | **60 hours** |

#### P0.3 Cold-Audit Framework Adoption
| Item | Source V_book | Implementation Effort |
|------|---------------|----------------------|
| Cold-audit framework doc | COLD_AUDIT_FRAMEWORK.md | Copy + adapt methodology |
| Staged first-paint UI contract | Multiple V_book repair docs | Adopt for KADIMA views |
| Decision-gate triage process | Engineering control roadmap | Document in KADIMA context |
| **Effort:** | | **16 hours** |

**Phase P0 Total: ~116 hours (~3 weeks, 1 engineer)**

---

### PHASE P1: NLP Engine Hardening (Weeks 4-7)

#### P1.1 Stanza Subprocess Isolation (V_book Pattern)
| Item | Source V_book | Implementation Effort |
|------|---------------|----------------------|
| Stanza subprocess worker | `stanza_subprocess_worker.py` | Create `kadima/engine/stanza_worker.py` |
| Managed probe subprocess | `stanza_probe_worker.py` | Create `kadima/engine/stanza_probe.py` |
| Runtime torch bootstrap | `infra/runtime_torch_bootstrap.py` | Create `kadima/infra/torch_bootstrap.py` |
| **Effort:** | | **40 hours** |

#### P1.2 M3 Morphological Analyzer Upgrade
| Current KADIMA | V_book Approach | Target |
|----------------|-----------------|--------|
| Rule-based prefix stripping | Stanza Hebrew model | Stanza primary → rules fallback |
| Partial prefix chains | Full Hebrew NLP | Complete morphological analysis |
| **Effort:** | | **24 hours** |

#### P1.3 Hebrew-Specific Domain Layer
| Item | Description | Effort |
|------|-------------|--------|
| `domain/hebrew_utils.py` | Maqaf handling, geresh/gershayim, prefix chains, abbreviations | 16 h |
| `domain/kwic.py` | KWIC display for concordance | 8 h |
| `domain/normalize_rules.py` | Deterministic normalization for Hebrew | 12 h |
| `domain/scoring.py` | Term scoring PMI/LLR/Dice | 8 h |
| `domain/sentence_splitter.py` | Hebrew-aware sentence splitting | 8 h |
| **Effort:** | | **52 hours** |

#### P1.4 M5 NP Chunker Transformer Embeddings
| Item | Description | Effort |
|------|-------------|--------|
| NeoDictaBERT integration | Already built — verify + harden | 8 h |
| Transformer embeddings mode | Validate + test | 8 h |
| **Effort:** | | **16 hours** |

**Phase P1 Total: ~132 hours (~4 weeks, 1 engineer)**

---

### PHASE P2: UI Performance & Cold-Audit Compliance (Weeks 8-11)

#### P2.1 Staged First-Paint for All Views
| View | Source V_book | Effort |
|------|---------------|--------|
| DashboardView | `project_dashboard.py` staged loading | 12 h |
| PipelineView | Lazy engine checks | 8 h |
| ResultsView | Terms table staged loading | 8 h |
| ValidationView | Validation results staged | 6 h |
| KBView | KB search staged | 8 h |
| CorporaView | Corpus import staged | 6 h |
| GenerativeView | 6 tabs lazy loading | 12 h |
| AnnotationView | LS project loading staged | 10 h |
| **Effort:** | | **70 hours** |

#### P2.2 Cold-Audit Initial Waves (First 8 Subsystems)
| Wave | Target | V_book Baseline | Effort |
|------|--------|-----------------|--------|
| 1 | Startup DB open | 82 ms probe | 4 h |
| 2 | Document picker / corpus list | 0.152 s p95 | 6 h |
| 3 | Sentences / terms view | staged repair | 8 h |
| 4 | Dictionary view | 0.003 s first page | 6 h |
| 5 | Terms view | 0.003 s first page | 4 h |
| 6 | Concordance (FTS health) | sentence_fts dependency | 8 h |
| 7 | TM / Translation Memory | 0.050 s page | 8 h |
| 8 | Coverage panel | 0.391 s partial | 8 h |
| **Effort:** | | | **52 hours** |

#### P2.3 NLP Engine Readiness — Lazy + Background
| Item | Description | Effort |
|------|-------------|--------|
| Async engine checks | Non-blocking NLP readiness check | 6 h |
| Lazy model loading | VRAM budget compliance | 8 h |
| Engine status UI | "Checking NLP engine readiness..." pattern from V_book | 4 h |
| **Effort:** | | **18 hours** |

**Phase P2 Total: ~140 hours (~4 weeks, 1 engineer)**

---

### PHASE P3: Data Layer & Services (Weeks 12-16)

#### P3.1 Database Schema Migrations (005-010)
| Migration | Contents | Effort |
|-----------|----------|--------|
| 005: TM schema | `tm_entry`, `tm_entry_history`, `dict_source`, `dict_entry`, `mt_cache` (V_book M7) | 12 h |
| 006: Audio | `audio_asset` table with content-addressed identity (V_book) | 8 h |
| 007: Process tracking | `processor_run`, `run_error` + retention contract (V_book P1-03) | 8 h |
| 008: Snapshot | `sentence_nlp_snapshot` with per-doc stats (V_book schema 42) | 10 h |
| 009: Lemma stats | `lemma_doc_stat`, `lemma_project_stat` | 8 h |
| 010: Generative results | Results from M13-M25 modules | 8 h |
| **Effort:** | | **54 hours** |

#### P3.2 Core Services (V_book Pattern)
| Service | Source V_book | Effort |
|---------|---------------|--------|
| `DBService` | Session management, reference attach | 10 h |
| `TermExtractionService` | 3-profile extraction + PMIs | 12 h |
| `ConcordanceService` | FTS5-optimized KWIC | 10 h |
| `TranslationMemoryService` | M7+P2 contracts, normalization, revert origin | 16 h |
| `DictionaryService` | User dictionary + FTS search | 10 h |
| `ExportService` | Excel, CSV, JSONL, TBX, TMX | 8 h |
| `ProjectService` | Create/open/switch/bundles | 12 h |
| `BackupService` | SHA256 integrity, backup/restore | 8 h |
| `HealthCheckService` | Resource/pronunciation/MT/provider checks | 8 h |
| `StatsService` | Corpus/document/term statistics | 6 h |
| **Effort:** | | **100 hours** |

#### P3.3 Pipeline Throttler + Operations Center
| Item | Source V_book | Effort |
|------|---------------|--------|
| `OperationsCenter` | Global heavy-operation slot | 8 h |
| `PipelineThrottler` | Advisory + runtime slot agreement | 6 h |
| Worker slot claims | NLP, extract, ingest, delete, import | 8 h |
| **Effort:** | | **22 hours** |

**Phase P3 Total: ~176 hours (~5 weeks, 1 engineer)**

---

### PHASE P4: Feature Integration (Weeks 17-22)

#### P4.1 V_book Features NOT in KADIMA (Must Port)
| Feature | Description | Effort |
|---------|-------------|--------|
| Hebrew Wikipedia Baseline | Reference corpus (387k docs) for comparison | 12 h |
| Batch Translation (M11) | Multi-provider chain, force mode, progress | 16 h |
| Project Exchange (.hdleproj) | ZIP bundles with ID remapping | 20 h |
| Import Wizard | Multi-format (TXT, DOCX, PDF with OCR) | 16 h |
| Pronunciation Bootstrap | Phonikud ONNX + sentence niqqud | 16 h |
| Audio Asset Service | TTS generation, playback, queue, cache | 16 h |
| User Dictionary Review | Per-item add/reject workflow | 8 h |
| Command Palette | Fuzzy action search | 6 h |
| Resources Manager | Model/resource download management | 8 h |
| Project Dashboard | Health, metrics, growth governance | 12 h |
| **Effort:** | | **130 hours** |

#### P4.2 KADIMA Unique Features — Production Hardening
| Module | Current Status | Production Target | Effort |
|--------|---------------|-------------------|--------|
| M15 TTS (XTTS→MMS) | Working stub | Full XTTS v2 production deployment | 16 h |
| M16 STT (Whisper) | Working stub | Full Whisper deployment + WER metric | 16 h |
| M18 Sentiment (heBERT) | Working stub | Full heBERT deployment + accuracy metric | 12 h |
| M20 QA (AlephBERT) | Working stub | Full AlephBERT + uncertainty sampling | 12 h |
| M23 Grammar (Dicta-LM) | Not created | Rules + Dicta-LM backend | 16 h |
| M24 Keyphrase (YAKE) | Not created | YAKE! backend + UI | 12 h |
| M19 Summarizer | Not created | Dicta-LM / mT5 backend | 16 h |
| M25 Paraphraser | Not created | mT5 / Dicta-LM backend | 16 h |
| **Effort:** | | **116 hours** |

#### P4.3 LLM View & NLP Tools View (T5)
| Item | Description | Effort |
|------|-------------|--------|
| `nlp_tools_view.py` | Grammar/Keyphrase/Summarize tabs | 12 h |
| `llm_view.py` | Chat + presets + context selector | 12 h |
| `chat_widget.py` | Chat interface for LLM | 8 h |
| T5 UI tests | pytest-qt for new views | 6 h |
| **Effort:** | | **38 hours** |

**Phase P4 Total: ~284 hours (~7 weeks, 2 engineers)**

---

### PHASE P5: Security, Testing & Release (Weeks 23-26)

#### P5.1 Security Hardening (V_book Pattern)
| Item | Source V_book | Effort |
|------|---------------|--------|
| FTS5 injection prevention | Injection tests | 6 h |
| CSV injection prevention | Macro/formula sanitization | 4 h |
| Log injection prevention | Newline sanitization | 4 h |
| SQL injection prevention | Parameterized queries verification | 6 h |
| Credential encryption | Windows DPAPI / macOS Keychain | 8 h |
| Audit logging | Security event logger | 8 h |
| Input validation | File paths, text, user input | 8 h |
| **Effort:** | | **44 hours** |

#### P5.2 Test Expansion
| Test Category | Current | Target | Effort |
|---------------|---------|--------|--------|
| Engine unit tests | Good | Expand to 25 modules | 20 h |
| Service integration tests | Limited | V_book P1/P2/P3 pattern | 32 h |
| UI integration tests | 62 smoke | Full view + worker testing | 24 h |
| Cold-latency tests | None | V_book cold-audit pattern | 16 h |
| E2E pipeline tests | 28 | Expand with new modules | 12 h |
| Security tests | None | Injection, input validation | 16 h |
| Performance benchmarks | None | Baseline + regression | 12 h |
| **Effort:** | | | **132 hours** |

#### P5.3 Release Infrastructure
| Item | Description | Effort |
|------|-------------|--------|
| Prebuild validation script | DB corruption detection, freeze check | 8 h |
| Self-check modes | import, db_open, health, cloud_tests | 8 h |
| CI pipeline | GitHub Actions: lint + typecheck + tests | 6 h |
| Docker Compose production-ready | Multi-service, GPU, volumes | 4 h |
| Installer packaging | PyInstaller / InnoSetup | 12 h |
| Release documentation | CHANGELOG, known issues, troubleshooting | 6 h |
| **Effort:** | | **44 hours** |

**Phase P5 Total: ~220 hours (~6 weeks, 2 engineers)**

---

## 4. Summary Timeline & Resource Planning

| Phase | Duration | Engineer-Weeks | Risk | Key Deliverable |
|-------|----------|---------------|------|-----------------|
| **P0** Foundation | Weeks 1-3 | 3 EW | Low | Quality gates, schema expansion, cold-audit framework |
| **P1** NLP Engines | Weeks 4-7 | 4 EW | Medium | Stanza subprocess, Hebrew domain, M3 upgrade |
| **P2** UI Performance | Weeks 8-11 | 4 EW | Medium | Staged first-paint, initial 8 cold-audit waves |
| **P3** Data + Services | Weeks 12-16 | 5 EW | High | 6 migrations, 10 services, operations center |
| **P4** Feature Integration | Weeks 17-22 | 14 EW | High | 10 V_book features, 4 new modules, T5 views |
| **P5** Security + Release | Weeks 23-26 | 6 EW | Medium | Security hardening, 200+ tests, release pipeline |
| **TOTAL** | **26 weeks** | **~36 EW** | — | **Production-grade HDLE** |

### Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| DB migration complexity | High | High | Incremental migrations, each tested on copy |
| Stanza subprocess stability | Medium | High | Mock engine fallback, comprehensive tests |
| UI performance regressions | Medium | Medium | Cold-audit after every change, evidence-first |
| VRAM budget exceeded | Medium | Medium | Strict lazy loading, LRU eviction |
| Test flakiness | Low | Medium | Deterministic fixtures, no live data in tests |

---

## 5. V_book Practices to Adopt Immediately

### 5.1 Engineering Discipline
| Practice | V_book Source | How to Adopt |
|----------|---------------|--------------|
| **Cold-Audit Framework** | `COLD_AUDIT_FRAMEWORK.md` | Copy methodology, start with first 3 waves |
| **Evidence-First Patches** | All V_book repair docs | Every fix must have before/after metrics |
| **Decision-Gate Triage** | Engineering roadmap | No automatic follow-ups — evidence must gate |
| **Bounded Phases** | Import chunking | No monolithic long-running operations |
| **Definition of Done** | `DEFINITION_OF_DONE.md` | Adopt verbatim + adapt to KADIMA |

### 5.2 Database Discipline
| Practice | V_book Source | How to Adopt |
|----------|---------------|--------------|
| Schema versioning | 42 migrations, monotonic | Never create tables in code |
| FTS5 health monitoring | `fts_manager.py` | Auto-detect parity drift |
| Write gate | Global heavy-operation slot | Single-writer for high-contention |
| DB retry | `db_retry.py` | SQLITE_BUSY retry with backoff |
| Reference DB attachment | `attach_reference()` | Read-only reference corpora |

### 5.3 UI Performance Contracts
| Practice | V_book Source | How to Adopt |
|----------|---------------|--------------|
| Staged first-paint | Rows → count → overlays | Every view must render within 0.5s |
| Lazy loading | Background workers | Heavy work never on cold-open path |
| Anti-stale requests | Worker cancel | Cancel superseded requests |
| Cold-audit waves | 32 waves completed | Measure every dialog/view before release |

### 5.4 Testing Rigor
| Practice | V_book Source | How to Adopt |
|----------|---------------|--------------|
| P1 verification | `p1_verify.py` | Automated proof of data integrity |
| P2 service tests | Service contracts | Query count ceilings, revert origin |
| P3 scenario tests | Gate tests | Critical user journey verification |
| Controlled benchmarks | JSON artifacts | Measure on same DB, same conditions |
| Regression suites | Every patch tested | No merge without full regression pass |

---

## 6. Execution Priorities — Order Matters

### Critical Path (Do Not Reorder)
```
P0: Quality gates + DB schema + Cold-audit methodology
   ↓
P1: Stanza subprocess + Hebrew domain + M3 upgrade
   ↓
P2: Staged first-paint + Initial cold-audit waves (UI must be responsive first)
   ↓
P3: Migrations + Services + Operations center (data layer before features)
   ↓
P4: V_book features port + KADIMA module production + T5 views
   ↓
P5: Security + Tests + Release pipeline
```

### Why This Order?
1. **Quality gates first** — Without DoD, you'll introduce regressions during changes
2. **DB schema next** — Services depend on tables, features depend on services
3. **UI performance early** — If UI is slow later, rework is massive
4. **Data layer before features** — Services must be stable before UI uses them
5. **Security and testing last** — After functionality is stable, harden it

---

## 7. What KADIMA Does Better (Preserve)

| Strength | Description | How to Maintain |
|----------|-------------|-----------------|
| **25-Module Coverage** | M1-M25 full NLP + generative pipeline | Keep Processor Protocol, validate all modules |
| **Dicta-LM Integration** | Israeli AI for Hebrew | Keep llm/ module, expand to Grammar/Summarize |
| **KB Embedding Search** | Cosine similarity on float32 BLOB | Keep kb/ module, optimize search |
| **Term Clustering** | k-means/HDBSCAN on NeoDictaBERT | Keep engine/clusterer, verify metrics |
| **NER Training Pipeline** | LS → CoNLL-U → spaCy Examples | Keep annotation/ + NER training |
| **API-First Design** | FastAPI with 10+ endpoints | Complete stub routers, add generative endpoints |
| **Docker Deployment** | Multi-service, GPU support | Keep docker-compose, enhance for production |

---

## 8. Immediate Next Steps

### Week 1 — Sprint 1 Goals
- [ ] Copy + adapt `DEFINITION_OF_DONE.md` → `Tasks/DEFINITION_OF_DONE.md`
- [ ] Create `kadima/tools/p1_verify.py` — P1 verification framework
- [ ] Create `scripts/ci_run_tests.ps1` — CI test runner
- [ ] Self-check modes in `kadima/cli.py` — `--self-check import`
- [ ] Review `config/config.default.yaml` — ensure all module configs complete
- [ ] Set up schema migration 005 (TM tables)

### Week 1 — Acceptance Criteria
- [ ] All existing tests pass (822+)
- [ ] `pytest tests/ -v` → 100% PASS
- [ ] `ruff check kadima/` → 0 errors
- [ ] Definition of Done documented
- [ ] Self-check `import` mode returns JSON
- [ ] Migration 005 created and reversible

---

## 9. Architectural Contracts (Non-Negotiable)

### 9.1 Module Registration (Orchestrator)
```python
# Pattern from KADIMA + V_book operations_center
_optional = {
    "sent_split": ("kadima.engine.sent_splitter", "SentSplitter"),
    "tokenizer": ("kadima.engine.tokenizer", "Tokenizer"),
    "morph_analyzer": ("kadima.engine.morphology", "MorphAnalyzer"),
    ...  # All 25 modules
}
```

### 9.2 VRAM Budget (From KADIMA, Enhanced)
| Budget | Max Simultaneous | V_book Equivalent |
|--------|-----------------|-------------------|
| Small (<1GB) | 2-3 modules | Stanza + Phonikud + heBERT |
| Medium (2-3GB) | 1 module | Translator / Whisper |
| Large (4-6GB) | 1 module | XTTS (only when requested) |

### 9.3 Processor Protocol
Every module must implement:
```python
@runtime_checkable
class ProcessorProtocol(Protocol):
    @property
    def name(self) -> str: ...
    @property
    def module_id(self) -> str: ...
    def process(self, input_data: Any, config: Dict[str, Any]) -> ProcessorResult: ...
    def validate_input(self, input_data: Any) -> bool: ...
```

### 9.4 DB Migration Discipline
- Tables created ONLY via migrations
- Migrations are idempotent
- Schema version incremented
- Rollback script provided
- No tables in code

### 9.5 Security Contracts
- All SQL parameterized (`?` placeholders)
- No SQL string interpolation of user input
- All CSV fields sanitized
- All log fields newline-sanitized
- All ML imports wrapped in `try/except ImportError`

---

## 10. Success Metrics — v2.0.0 Target

| Metric | Current | Target | How Measured |
|--------|---------|--------|-------------|
| Tests | 822 functions | 1200+ functions | `pytest tests/ -v` |
| Migrations | 4 | 10+ | `sqlite3 kadima.db "SELECT count(*) FROM schema_version"` |
| Services | ~10 (partial) | 18+ (full) | Count of service classes |
| Modules working | ~18/25 | 25/25 | Gold corpus per module |
| Cold-open startup | No measurement | <0.5 s first view | Cold-audit wave 1 |
| UI first-paint | 2-3 s (blocking) | <0.5 s staged | Cold-audit waves 2-8 |
| Security findings | Unknown | 0 critical | `security-auditor` |
| DB schema | v4 | v10+ | `schema_version` table |
| Release gates | None | Prebuild + self-check | `scripts/prebuild_validate.py` |
| CI | Partial | Green on main | GitHub Actions |
| VRAM peak | Unmeasured | <=8GB with 3 modules | `nvidia-smi` under load |
| Module coverage | ~75% | 100% | Files in `kadima/engine/` |
| API endpoints | 10 working, 16 TODO | 26+ working | `GET /api/v1/health` + all routers |

---

## 11. Risk Assessment

### Critical Risks
| Risk | Likelihood | Impact | Mitigation Strategy |
|------|-----------|--------|-------------------|
| Database migration failure | Medium | HIGH | Test on copy, rollback script, backup before each migration |
| Stanza subprocess instability | Medium | MEDIUM | Mock engine fallback, comprehensive subprocess tests |
| UI performance regression | Low | MEDIUM | Cold-audit after every change, evidence-first |
| VRAM budget exceeded | Medium | MEDIUM | Strict lazy loading, LRU eviction, monitoring |
| Module regression | Low | HIGH | Gold corpus validation, 25 module tests |

### Dependencies
- `stanza` (Hebrew NLP model)
- `transformers` (NeoDictaBERT, HeBERT, mBART-50)
- `PyQt6` (UI framework)
- `fastapi` + `uvicorn` (API)
- `sqlalchemy` (ORM)
- `phonikud` (Diacritization ONNX)
- `openai-whisper` (STT)
- `TTS` (Coqui TTS)
- `Label Studio` (Annotation)
- `yake` (Keyphrase extraction)

---

## 12. Appendices

### A. Glossary

| Term | Definition |
|------|-----------|
| **Cold-Audit** | Measured performance of system under cold-start conditions |
| **Staged First-Paint** | UI pattern: render rows first, count/overlays later |
| **Decision Gate** | Evidence-based checkpoint — no automatic follow-up |
| **Heavy-Operation Slot** | Single-writer discipline for high-contention DB operations |
| **P1/P2/P3** | Verification tiers: P1=critical, P2=quality, P3=extended |
| **Processor Protocol** | Contract for all 25 modules |
| **Cold Path** | Code path executed on first run or after idle period |
| **Warm Path** | Code path with cached data or repeated execution |

### B. File Mapping (V_book → KADIMA)

| V_book Path | KADIMA Path | Notes |
|-------------|-------------|-------|
| `app/infra/db.py` | `kadima/infra/db.py` | DB engine, session management |
| `app/infra/fts_manager.py` | `kadima/infra/fts_manager.py` | New file |
| `app/infra/write_gate.py` | `kadima/infra/write_gate.py` | New file |
| `app/infra/db_retry.py` | `kadima/infra/db_retry.py` | New file |
| `app/infra/reference_guard.py` | `kadima/infra/reference_guard.py` | New file |
| `app/services/db_service.py` | `kadima/infra/db_service.py` | New file |
| `app/services/operations_center.py` | `kadima/services/operations_center.py` | Copy pattern |
| `app/services/pipeline_throttler.py` | `kadima/services/pipeline_throttler.py` | Copy pattern |
| `app/services/term_extraction_service.py` | `kadima/engine/term_extractor.py` | Enhance existing |
| `app/services/concordance_service.py` | `kadima/corpus/search.py` | Enhance existing |
| `app/services/project_service.py` | `kadima/corpus/manager.py` | New file |
| `app/services/translation_service.py` | `kadima/engine/translator.py` | Enhance existing |
| `app/services/health_check_service.py` | `kadima/services/health_check.py` | New file |
| `app/services/backup_service.py` | `kadima/services/backup.py` | New file |
| `app/services/stats_service.py` | `kadima/corpus/statistics.py` | Enhance existing |
| `app/tools/p1_verify.py` | `kadima/tools/p1_verify.py` | New file |
| `app/infra/nlp_engines/stanza_subprocess_worker.py` | `kadima/engine/stanza_worker.py` | New file |
| `tools/smoke_export_center.py` | `kadima/tools/smoke_tests.py` | New file |

### C. Recommended Commit Sequence

```
feat(infra): add Definition of Done and quality gates
feat(cli): add --self-check import mode
feat(infra): add p1_verify.py tool
test: add CI scripts for automated testing
feat(data): add migration 005 TM schema
feat(infra): add FTS5 manager with parity health
feat(infra): add write gate for heavy operations
feat(infra): add DB retry with SQLITE_BUSY backoff
feat(engine): Stanza subprocess worker isolation
feat(engine): upgrade M3 morphological analyzer
feat(domain): add Hebrew utilities (maqaf, geresh, prefix chains)
feat(ui): staged first-paint for DashboardView
feat(ui): staged first-paint for PipelineView
... (continue per phase)
```

---

## Conclusion

This plan transforms KADIMA from a capable prototype into a production-grade
Hebraic Dynamic Lexicon Engine by adopting V_book's proven engineering practices
while preserving and elevating KADIMA's unique capabilities (25 modules, LLM
integration, KB search, NER training).

**Key Principles:**
1. **Evidence over assumptions** — every change measured, documented
2. **Bounded phases** — no monolithic long-running operations
3. **Quality gates** — nothing merges without passing tests
4. **Cold-audit disciplined** — UI responsiveness is non-negotiable
5. **Preserve unique strengths** — Dicta-LM, KB embedding, NER training stay

**Expected Outcome (26 weeks):**
- V_book-grade production readiness
- KADIMA's 25 modules all production-ready
- 1200+ test functions, 100% pass rate
- Release pipeline with prebuild validation
- Cold-start performance <0.5 s for all views
- Security hardened, 0 critical findings
- Documentation at V_book level