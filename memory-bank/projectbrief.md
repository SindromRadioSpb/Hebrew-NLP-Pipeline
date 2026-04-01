# Project Brief — KADIMA

## Что такое KADIMA
KADIMA — NLP-платформа для терминологической экстракции из ивритских текстов.
Hebrew Dynamic Lexicon Engine. Цель: production-grade инструмент терминографа,
который слышит, говорит, учится и объясняет.

**Версия:** 0.9.x → цель 1.0.0 → цель 2.0 (HDLE-grade)  
**Статус на:** 2026-04-01  
**Package:** `kadima/`  
**Python:** 3.10+

---

## Стек

| Слой | Технологии |
|------|-----------|
| NLP pipeline | spaCy 3.7+, spacy-transformers, hebpipe (опционально) |
| ML / GPU | PyTorch 2.10+cu128, HuggingFace Transformers, ONNX Runtime |
| API | FastAPI 0.110+, uvicorn, Pydantic v2 |
| Desktop UI | PyQt6 (GPL v3 — ⚠️ коммерческая лицензия нужна!) |
| DB | SQLite WAL + raw sqlite3 + SQLAlchemy ORM (sync+async) |
| Annotation | Label Studio Community (Docker, Apache 2.0) |
| LLM | llama.cpp server (Docker), Dicta-LM 3.0 (dictalm-3.0-1.7b-instruct.gguf) |
| Infrastructure | Docker Compose, GitHub Actions CI |

## Hardware (целевое)
- **Dev:** RTX 3060 12GB VRAM (CUDA 12.8)
- **CI/prod:** RTX 3070 8GB VRAM (CUDA 12.8)
- **VRAM budget:** 2-3 small (<1GB) + 1 medium (2-3GB) одновременно

## Ключевые пути
```
E:\projects\Project_Vibe\Kadima\   ← корень проекта
F:\datasets_models\                ← HF_HOME, TORCH_HOME, TRANSFORMERS_CACHE
D:\virtualenvs\                    ← virtualenvs
```

## Entry Points
```bash
kadima api --host 0.0.0.0 --port 8501   # REST API
kadima gui                               # Desktop UI
kadima migrate                           # Apply DB migrations
kadima --self-check import|db_open|health|migrations  # CI gate
make up       # Docker: API + Label Studio
make up-llm   # + llama.cpp GPU
```

## Два режима pipeline

```
PipelineService.run_on_text(text)
  → NLP pipeline: M1→M2→M3→M4→M5→M6→M7→M8→M12 (sequential)

PipelineService.run_module(id, input)
  → Generative modules M13-M25 (on-demand, independent)
```

## Processor Protocol (все модули обязаны реализовать)
```python
# kadima/engine/contracts.py
@runtime_checkable
class ProcessorProtocol(Protocol):
    @property
    def name(self) -> str: ...
    @property
    def module_id(self) -> str: ...
    def process(self, input_data: Any, config: Dict[str, Any]) -> ProcessorResult: ...
    def validate_input(self, input_data: Any) -> bool: ...
```
Базовый класс: `kadima/engine/base.py::Processor` (ABC)
