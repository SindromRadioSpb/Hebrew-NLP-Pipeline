# 5.1. Non-Functional Requirements — KADIMA

> Версия: 2.0 (2026-03-30)

---

## Производительность

### Core Pipeline (v1.0)
| Операция | Требование | Компонент |
|----------|-----------|-----------|
| Tokenization | ≥ 10,000 tokens/sec | spaCy lang/he |
| Full pipeline (M1–M8) | ≥ 1,000 tokens/sec | HebPipe + spaCy |
| Transformer inference | ≥ 500 tokens/sec (FP16 GPU) | NeoDictaBERT |
| Validation | ≥ 5,000 checks/sec | SQLite |
| UI response | ≤ 200ms | PyQt |

### Annotation (v1.0)
| Операция | Требование | Компонент |
|----------|-----------|-----------|
| Label Studio page load | ≤ 3 сек | LS web UI |
| Pre-annotation export (KADIMA → LS) | ≤ 30 сек за 100 документов | ML backend |
| Annotation export (LS → KADIMA) | ≤ 10 сек за 100 задач | LS API |

### Knowledge Base (v1.x)
| Операция | Требование | Компонент |
|----------|-----------|-----------|
| KB term search | ≤ 200ms | SQLite + index |
| Embedding similarity (top-10) | ≤ 500ms | NeoDictaBERT + SQLite |
| Bulk definition generation | ≤ 5 сек/term | Dicta-LM 1.7B |

### LLM Service (v1.x)
| Операция | Требование | Компонент |
|----------|-----------|-----------|
| Term definition generation | ≤ 3 сек | Dicta-LM 1.7B (GGUF Q4) |
| Grammar explanation | ≤ 5 сек | Dicta-LM 1.7B |
| QA over corpus (RAG) | ≤ 10 сек | Dicta-LM 1.7B + retrieval |
| Model load time | ≤ 30 сек | llama.cpp |

---

## Масштабируемость
- Max corpus size: 1M tokens per corpus
- Max documents per corpus: 10,000
- Max concurrent pipeline runs: 1 (v1.0), 4 (v2.0)
- Max KB terms: 500,000
- Max annotation tasks per project: 100,000

---

## Отказоустойчивость
- Pipeline crash → auto-save partial results
- DB corruption → auto-backup every run
- UI freeze → async processing with progress bar
- Label Studio down → show status, suggest `docker-compose up`
- Dicta-LM not loaded → fallback to pipeline-only (no LLM features)
- llama.cpp timeout → show error, suggest reduce max_tokens or use smaller model

---

## Совместимость
- OS: Windows 10/11 (v1.0), macOS/Linux (v1.x)
- Python: 3.12+
- Encoding: UTF-8 mandatory
- Docker: для Label Studio (v1.0) + llama.cpp server (v1.x)
- Browser: Chrome/Firefox/Edge (для Label Studio UI)

---

## Логирование
- Pipeline: INFO level by default, DEBUG configurable
- Errors: full stack trace + input context
- Audit: user actions logged
- LLM: latency, tokens, model version logged per request
- Label Studio: annotation events synced via webhook

---

## Безопасность
- Local storage only (v1.0) — no cloud
- No user auth (single-user desktop)
- Secrets: N/A (v1.0)
- Label Studio: local instance, no external access (v1.0)
- Dicta-LM: local inference, no data sent externally
- Model attribution: Apache 2.0 (HebPipe, Label Studio, Dicta-LM), CC BY 4.0 (NeoDictaBERT — attribution required)

---

## Железо (минимальные требования)

| Компонент | v1.0 | v1.x (с LLM) | v2.0 |
|-----------|------|--------------|------|
| CPU | x86_64, 4 cores | x86_64, 4 cores | x86_64, 8 cores |
| RAM | 16 GB | 32 GB | 32 GB |
| GPU (VRAM) | 4 GB (NeoDictaBERT FP16) | 8 GB (NeoDictaBERT + Dicta-LM 1.7B) | 16+ GB (12B model) |
| Disk | 10 GB | 30 GB (модели) | 50 GB |
| Docker | Опционален | Обязателен (LS) | Обязателен |
