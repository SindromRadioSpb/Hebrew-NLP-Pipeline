# Conventions — KADIMA

## Code Style

| Rule | Value |
|------|-------|
| Language | Python 3.10+ |
| Formatter | black (line length 88) |
| Linter | ruff (isort-compatible) |
| Type checker | mypy --ignore-missing-imports |
| Naming | snake_case files/functions, PascalCase classes, UPPER_SNAKE constants |

```bash
ruff check kadima/          # lint
mypy kadima/ --ignore-missing-imports  # types
pytest tests/ -v            # tests (must pass before AND after any change)
```

---

## Typing Rules
- Type annotations on **all** public functions (parameters + return type)
- `X | None` — nullable types (Python 3.10+ syntax, NOT `Optional[X]`)
- `list[X]`, `dict[K, V]` — lowercase (Python 3.10+)
- `@dataclass` for engine data, `pydantic.BaseModel` for API schemas
- Config models: `pydantic.BaseModel` with `extra="forbid"`

---

## Processor Pattern (engine modules)

```python
# Every kadima/engine/*.py MUST follow this pattern:
from kadima.engine.base import Processor, ProcessorResult, ProcessorStatus

class MyModule(Processor):
    @property
    def name(self) -> str: return "my_module"
    
    @property
    def module_id(self) -> str: return "M99"
    
    def process(self, input_data: Any, config: dict[str, Any]) -> ProcessorResult:
        if not self.validate_input(input_data):
            return ProcessorResult(status=ProcessorStatus.FAILED, errors=["Invalid input"])
        try:
            # ... logic ...
            return ProcessorResult(status=ProcessorStatus.READY, data=result)
        except Exception as exc:
            logger.error("Module failed: %s", exc)
            return ProcessorResult(status=ProcessorStatus.FAILED, errors=[str(exc)])
    
    def validate_input(self, input_data: Any) -> bool:
        return isinstance(input_data, str) and bool(input_data.strip())
    
    # Optional but recommended:
    def process_batch(self, inputs: list, config: dict) -> list[ProcessorResult]:
        return [self.process(inp, config) for inp in inputs]
```

**Non-negotiable:** Processors NEVER raise — always return `FAILED` with errors list.

---

## ML Import Pattern

```python
logger = logging.getLogger(__name__)

_model = None  # lazy singleton

def _load_model():
    global _model
    if _model is not None:
        return _model
    try:
        from some_ml_lib import Model
        device = "cuda" if torch.cuda.is_available() else "cpu"
        _model = Model.from_pretrained("model/name").to(device)
        return _model
    except ImportError:
        raise ImportError(
            "ML dependency not installed. Run: pip install -e '.[ml]'"
        )
```

---

## FastAPI Router Pattern

```python
# kadima/api/routers/example.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from kadima.engine.base import ProcessorStatus

router = APIRouter(prefix="/example", tags=["example"])

class MyRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Hebrew text")
    backend: str = Field(default="rules", pattern=r"^(rules|ml)$")

class MyResponse(BaseModel):
    result: str
    backend: str

@router.post("/run", response_model=MyResponse)
async def run(req: MyRequest) -> MyResponse:
    """One-line docstring."""
    from kadima.engine.my_module import MyModule
    proc = MyModule()
    result = proc.process(req.text, {"backend": req.backend})
    if result.status != ProcessorStatus.READY:
        raise HTTPException(status_code=500, detail=result.errors)
    return MyResponse(result=result.data.result, backend=result.data.backend)
```

**Rules:**
- `response_model=` always declared
- Never return SQLAlchemy ORM objects directly — map to Pydantic first
- No NLP logic inline — call `engine/` only
- Blocking calls in `asyncio.to_thread()`

---

## SQLite Rules

```python
# ALWAYS parameterized:
conn.execute("SELECT * FROM terms WHERE lemma = ?", (lemma,))

# NEVER:
conn.execute(f"SELECT * FROM terms WHERE lemma = '{lemma}'")  # ❌

# Sort columns — whitelist only:
ALLOWED_SORT = {"lemma", "freq", "created_at"}
if sort_col not in ALLOWED_SORT:
    raise ValueError(f"Invalid sort: {sort_col!r}")

# Connection setup:
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA busy_timeout=5000")
conn.execute("PRAGMA foreign_keys=ON")
```

**Tables created ONLY via migrations** in `kadima/data/migrations/00N_name.sql`

---

## PyQt6 Threading Rules

```python
# Workers use QRunnable + QThreadPool:
class MyWorker(QRunnable):
    def run(self) -> None:
        # DO: use signals only to update UI
        # DO: self._cancel flag at safe boundaries
        # DON'T: touch any UI widget directly
        # DON'T: call engine modules from main thread

# Wiring in view:
worker = MyWorker(...)
worker.signals.finished.connect(self._on_done)
QThreadPool.globalInstance().start(worker)
```

---

## Error Handling

```python
# Specific exceptions, never bare:
try:
    result = do_something()
except sqlite3.OperationalError as exc:
    logger.warning("DB error: %s", exc)
    raise

# Never:
try:
    ...
except:       # ❌ bare except
    pass      # ❌ silent swallow
```

---

## Logging

```python
# In every module:
logger = logging.getLogger(__name__)

# Never print() outside CLI:
logger.info("Processing corpus %d", corpus_id)   # ✅
print(f"Processing {corpus_id}")                  # ❌
```

---

## Commit Format

```
type(scope): short description (imperative, max 72 chars)

Types: feat | fix | refactor | test | docs | chore | perf | security
Scopes: engine | pipeline | api | ui | data | config | docker | ci | kb | llm | annotation | validation
```

Examples:
```
feat(engine): add M25 Paraphraser with mT5 + LLM fallback
fix(data): fix off-by-one in kb_terms column index (r[9] vs r[10])
test(api): add 19 integration tests for validation router
docs(claude): update CLAUDE.md — T6 D4 done, 29 endpoints
```

---

## Adding a New Generative Module

```
1. Create kadima/engine/<module>.py
   - Inherit from Processor (kadima/engine/base.py)
   - Implement: process(), process_batch(), validate_input()
   - Add static metric methods
   - Wrap ML imports: try/except ImportError
   - Check CUDA: torch.cuda.is_available() before .to("cuda")
   - Register in lazy loading pattern

2. Create tests/engine/test_<module>.py
   - Metric unit tests (no model needed)
   - process() with mock/rules fallback
   - validate_input() edge cases
   - Empty input → FAILED status, no crash

3. Register in kadima/pipeline/orchestrator.py
   - Add to _optional_modules dict
   - try/except ImportError on load

4. Add config section to config/config.default.yaml

5. Add API endpoint to kadima/api/routers/generative.py

6. pytest tests/ -v — ALL PASS

7. Commit: feat(engine): add M<XX> <ModuleName>
```
