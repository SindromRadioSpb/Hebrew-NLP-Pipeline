# 10.5. Implementation Recipes — KADIMA

> Версия: 1.0 (2026-03-30)
> Связанные: INTERFACE_CONTRACTS.md, PROJECT_STRUCTURE.md, CODING_STANDARDS.md, NLP_STACK_INTEGRATION.md

---

## Recipe 1: HebPipe Wrappers (M1–M3)

```python
# kadima/engine/hebpipe_wrappers.py
"""M1–M3: Обёртки над HebPipe для интеграции в spaCy pipeline."""

import time
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from kadima.engine.base import Processor, ProcessorResult, ProcessorStatus

logger = logging.getLogger(__name__)


@dataclass
class Sentence:
    index: int
    text: str
    start: int
    end: int


@dataclass
class SentenceSplitResult:
    sentences: List[Sentence]
    count: int


@dataclass
class Token:
    index: int
    surface: str
    start: int
    end: int
    is_punct: bool = False


@dataclass
class TokenizeResult:
    tokens: List[Token]
    count: int


@dataclass
class MorphAnalysis:
    surface: str
    base: str
    lemma: str
    pos: str
    features: Dict[str, str] = field(default_factory=dict)
    is_det: bool = False
    prefix_chain: List[str] = field(default_factory=list)


@dataclass
class MorphResult:
    analyses: List[MorphAnalysis]
    count: int


class HebPipeSentSplitter(Processor):
    """M1: Sentence splitting через HebPipe internals."""

    _pipeline = None  # Lazy-loaded singleton

    @property
    def name(self) -> str:
        return "sent_split"

    @property
    def module_id(self) -> str:
        return "M1"

    def _ensure_pipeline(self):
        if HebPipeSentSplitter._pipeline is None:
            logger.info("Loading HebPipe sentence splitter...")
            # from hebpipe import ... (lazy import)
            HebPipeSentSplitter._pipeline = True  # placeholder
            logger.info("HebPipe sentence splitter loaded")

    def process(self, input_data: str, config: Dict[str, Any]) -> ProcessorResult:
        start = time.time()
        self._ensure_pipeline()

        try:
            text = input_data
            # HebPipe sentence splitting logic
            # Placeholder: split by period + Hebrew rules
            sentences = self._split_sentences(text)

            return ProcessorResult(
                module_name=self.name,
                status=ProcessorStatus.READY,
                data=SentenceSplitResult(sentences=sentences, count=len(sentences)),
                processing_time_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            logger.error("Sentence splitting failed: %s", e, exc_info=True)
            return ProcessorResult(
                module_name=self.name,
                status=ProcessorStatus.FAILED,
                data=None,
                errors=[str(e)],
                processing_time_ms=(time.time() - start) * 1000,
            )

    def _split_sentences(self, text: str) -> List[Sentence]:
        """
        Правила (см. PRD FR-01):
        - Boundary: точка после Hebrew буквы/цифры
        - Non-boundary: аббревиатуры (פרופ׳, ד״ר), десятичные (3.14)
        - Empty fragments: не предложения
        """
        # Implementation: integrate with HebPipe internals
        # For now, simple split by period
        import re
        parts = re.split(r'(?<=[א-ת])\.\s+', text)
        sentences = []
        offset = 0
        for i, part in enumerate(parts):
            part = part.strip()
            if not part:
                continue
            start = text.find(part, offset)
            sentences.append(Sentence(index=i, text=part, start=start, end=start + len(part)))
            offset = start + len(part)
        return sentences


class HebPipeMorphAnalyzer(Processor):
    """M2+M3: Токенизация + морфологический анализ через HebPipe."""

    _pipeline = None

    @property
    def name(self) -> str:
        return "morph_analyzer"

    @property
    def module_id(self) -> str:
        return "M3"

    def process(self, input_data: List[Token], config: Dict[str, Any]) -> ProcessorResult:
        start = time.time()
        try:
            analyses = []
            for token in input_data:
                # HebPipe morphological analysis
                analysis = MorphAnalysis(
                    surface=token.surface,
                    base=token.surface,  # placeholder
                    lemma=token.surface,  # placeholder
                    pos="NOUN",           # placeholder
                    features={},
                    is_det=token.surface.startswith("ה"),
                    prefix_chain=[],
                )
                analyses.append(analysis)

            return ProcessorResult(
                module_name=self.name,
                status=ProcessorStatus.READY,
                data=MorphResult(analyses=analyses, count=len(analyses)),
                processing_time_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            logger.error("Morph analysis failed: %s", e, exc_info=True)
            return ProcessorResult(
                module_name=self.name,
                status=ProcessorStatus.FAILED,
                data=None,
                errors=[str(e)],
                processing_time_ms=(time.time() - start) * 1000,
            )
```

---

## Recipe 2: Pipeline Orchestrator

```python
# kadima/pipeline/orchestrator.py
"""Pipeline Orchestrator: M1→M2→M3→M4→M5→M6→M7→M8."""

import time
import logging
from typing import Dict, List, Optional

from kadima.engine.base import Processor, PipelineResult, ProcessorStatus
from kadima.pipeline.config import PipelineConfig
from kadima.data.repositories import PipelineRunRepository, CorpusRepository

logger = logging.getLogger(__name__)


class PipelineService:
    """Оркестрирует выполнение модулей Engine Layer."""

    def __init__(self, config: PipelineConfig, db_path: str = "~/.kadima/kadima.db"):
        self.config = config
        self.modules: Dict[str, Processor] = {}
        self.run_repo = PipelineRunRepository(db_path)
        self.corpus_repo = CorpusRepository(db_path)
        self._register_modules()

    def _register_modules(self):
        """Регистрирует модули в порядке выполнения."""
        from kadima.engine.hebpipe_wrappers import HebPipeSentSplitter, HebPipeMorphAnalyzer
        from kadima.engine.ngram_extractor import NgramExtractor
        from kadima.engine.np_chunker import NPChunker
        from kadima.engine.canonicalizer import Canonicalizer
        from kadima.engine.association_measures import AMEngine
        from kadima.engine.term_extractor import TermExtractor
        from kadima.engine.noise_classifier import NoiseClassifier

        self.modules = {
            "sent_split": HebPipeSentSplitter(),
            "morph_analyzer": HebPipeMorphAnalyzer(),
            "ngram": NgramExtractor(),
            "np_chunk": NPChunker(),
            "canonicalize": Canonicalizer(),
            "am": AMEngine(),
            "term_extract": TermExtractor(),
            "noise": NoiseClassifier(),
        }

    def run(self, corpus_id: int) -> PipelineResult:
        """Запускает pipeline на корпусе."""
        run_id = self.run_repo.create(corpus_id, self.config.profile)
        self.run_repo.update_status(run_id, "running")

        start = time.time()
        result = PipelineResult(corpus_id=corpus_id, profile=self.config.profile)

        try:
            # Загружаем документы корпуса
            documents = self.corpus_repo.get_documents(corpus_id)

            for doc in documents:
                doc_result = self._process_document(doc.raw_text)
                # Объединяем результаты
                result.terms.extend(doc_result.terms)
                result.ngrams.extend(doc_result.ngrams)

            # Deduplicate and rank terms
            result.terms = self._deduplicate_terms(result.terms)
            result.terms.sort(key=lambda t: t.rank)

            result.status = ProcessorStatus.READY
            self.run_repo.save_terms(run_id, result.terms)
            self.run_repo.update_status(run_id, "completed")

        except Exception as e:
            logger.error("Pipeline failed: %s", e, exc_info=True)
            result.status = ProcessorStatus.FAILED
            self.run_repo.update_status(run_id, "failed")
            raise

        result.total_time_ms = (time.time() - start) * 1000
        return result

    def _process_document(self, text: str) -> PipelineResult:
        """Обрабатывает один документ через все модули."""
        result = PipelineResult(corpus_id=0, profile=self.config.profile)
        current_data = text

        for module_name in self.config.modules:
            if module_name not in self.modules:
                continue
            module = self.modules[module_name]
            module_config = self.config.get_module_config(module_name)

            proc_result = module.process(current_data, module_config)
            result.module_results[module_name] = proc_result

            if proc_result.status == ProcessorStatus.FAILED:
                logger.warning("Module %s failed, skipping remaining", module_name)
                break

            current_data = proc_result.data

        return result

    def _deduplicate_terms(self, terms: List) -> List:
        """Дедупликация терминов по canonical form."""
        seen = {}
        for term in terms:
            key = term.canonical
            if key not in seen or term.freq > seen[key].freq:
                seen[key] = term
        return list(seen.values())
```

---

## Recipe 3: Label Studio ML Backend (NER Pre-annotation)

```python
# ml_backends/kadima_ner_backend.py
"""KADIMA NER pre-annotation backend для Label Studio."""

import logging
from typing import Dict, List, Any, Optional
from label_studio_ml.model import LabelStudioMLBase
import spacy

logger = logging.getLogger(__name__)


class KadimaNERBackend(LabelStudioMLBase):
    """
    ML backend: KADIMA spaCy pipeline → NER pre-annotations для Label Studio.
    
    Поддерживаемые labels (кастомизируются через _label_map):
    PERSON, LOCATION, ORG, DATE, QUANTITY, MATERIAL, TERM
    """

    # Маппинг: spaCy entity → Label Studio label
    _label_map = {
        "PERSON": "PERSON",
        "GPE": "LOCATION",
        "LOC": "LOCATION",
        "ORG": "ORG",
        "DATE": "DATE",
        "CARDINAL": "QUANTITY",
        "QUANTITY": "QUANTITY",
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        model_name = kwargs.get("spacy_model", "he_kadima_pipeline")
        logger.info("Loading spaCy model: %s", model_name)
        self.nlp = spacy.load(model_name)

    def predict(self, tasks: List[Dict], context: Optional[Any] = None, **kwargs) -> List[Dict]:
        """Генерация pre-annotations для задач Label Studio."""
        predictions = []

        for task in tasks:
            text = task["data"].get("text", "")
            if not text:
                predictions.append({"result": []})
                continue

            doc = self.nlp(text)
            results = []

            for ent in doc.ents:
                label = self._label_map.get(ent.label_, None)
                if label is None:
                    continue

                results.append(
                    {
                        "from_name": "label",
                        "to_name": "text",
                        "type": "labels",
                        "value": {
                            "start": ent.start_char,
                            "end": ent.end_char,
                            "text": ent.text,
                            "labels": [label],
                            "score": 0.85,
                        },
                    }
                )

            predictions.append({"result": results, "score": 0.85})

        return predictions

    def fit(self, event: str, data: Dict, **kwargs) -> Dict:
        """Обработка событий от Label Studio (annotation created, etc.)."""
        logger.info("Received event: %s", event)
        if event == "ANNOTATION_CREATED":
            # Future: trigger retraining
            logger.info("Annotation created, model can be retrained")
        return {"status": "ok"}


if __name__ == "__main__":
    from label_studio_ml.api import init_app

    app = init_app(model_class=KadimaNERBackend)
    app.run(host="0.0.0.0", port=9090)
```

---

## Recipe 4: Label Studio Client

```python
# kadima/annotation/ls_client.py
"""REST API клиент для Label Studio."""

import logging
from typing import Dict, List, Optional
import httpx

logger = logging.getLogger(__name__)


class LabelStudioClient:
    """Интеграция с Label Studio REST API."""

    def __init__(self, url: str = "http://localhost:8080", api_key: Optional[str] = None):
        self.base_url = url.rstrip("/")
        self.headers = {"Authorization": f"Token {api_key}"} if api_key else {}
        self.client = httpx.Client(base_url=self.base_url, headers=self.headers, timeout=30)

    def health_check(self) -> bool:
        """Проверить доступность Label Studio."""
        try:
            resp = self.client.get("/api/projects/")
            return resp.status_code == 200
        except Exception:
            return False

    def create_project(self, name: str, label_config: str, description: str = "") -> int:
        """Создать проект. Возвращает project ID."""
        resp = self.client.post(
            "/api/projects/",
            json={
                "title": name,
                "label_config": label_config,
                "description": description,
            },
        )
        resp.raise_for_status()
        project_id = resp.json()["id"]
        logger.info("Created LS project: %s (id=%d)", name, project_id)
        return project_id

    def import_tasks(self, project_id: int, tasks: List[Dict]) -> List[int]:
        """Импортировать задачи. Возвращает task IDs."""
        resp = self.client.post(
            f"/api/projects/{project_id}/import",
            json=tasks,
        )
        resp.raise_for_status()
        task_ids = resp.json().get("task_ids", [])
        logger.info("Imported %d tasks to project %d", len(task_ids), project_id)
        return task_ids

    def import_predictions(self, project_id: int, predictions: List[Dict]) -> None:
        """Импортировать pre-annotations (predictions)."""
        resp = self.client.post(
            f"/api/projects/{project_id}/predictions",
            json=predictions,
        )
        resp.raise_for_status()
        logger.info("Imported %d predictions to project %d", len(predictions), project_id)

    def export_annotations(self, project_id: int, export_type: str = "JSON") -> List[Dict]:
        """Экспортировать аннотации."""
        resp = self.client.get(
            f"/api/projects/{project_id}/export",
            params={"export_type": export_type},
        )
        resp.raise_for_status()
        return resp.json()

    def get_project_stats(self, project_id: int) -> Dict:
        """Статистика проекта."""
        resp = self.client.get(f"/api/projects/{project_id}")
        resp.raise_for_status()
        data = resp.json()
        return {
            "total": data.get("task_number", 0),
            "completed": data.get("num_tasks_with_annotations", 0),
            "skipped": data.get("skipped_annotations_number", 0),
        }

    def get_api_key(self, email: str, password: str) -> Optional[str]:
        """Получить API key по логину/паролю."""
        resp = self.client.post(
            "/api/user/login/",
            json={"email": email, "password": password},
        )
        if resp.status_code == 200:
            return resp.json().get("token")
        return None
```

---

## Recipe 5: LLM Client (llama.cpp)

```python
# kadima/llm/client.py
"""HTTP клиент для llama.cpp server (Dicta-LM 3.0)."""

import logging
from typing import Dict, List, Optional
import httpx

logger = logging.getLogger(__name__)


class LlamaCppClient:
    """Клиент для llama.cpp HTTP сервера."""

    def __init__(self, server_url: str = "http://localhost:8081", timeout: int = 30):
        self.server_url = server_url.rstrip("/")
        self.client = httpx.Client(base_url=self.server_url, timeout=timeout)

    def is_loaded(self) -> bool:
        """Проверить, загружена ли модель."""
        try:
            resp = self.client.get("/health")
            return resp.status_code == 200
        except Exception:
            return False

    def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        stop: Optional[List[str]] = None,
    ) -> str:
        """Генерация текста через /completion endpoint."""
        payload = {
            "prompt": prompt,
            "n_predict": max_tokens,
            "temperature": temperature,
        }
        if stop:
            payload["stop"] = stop

        try:
            resp = self.client.post("/completion", json=payload)
            resp.raise_for_status()
            return resp.json().get("content", "")
        except httpx.TimeoutException:
            logger.error("LLM timeout after %ds", self.client.timeout)
            raise
        except Exception as e:
            logger.error("LLM request failed: %s", e, exc_info=True)
            raise

    def chat(self, messages: List[Dict[str, str]], max_tokens: int = 512) -> str:
        """Chat completion. Формат Dicta-LM: [INST]...[/INST]."""
        prompt = self._format_chat(messages)
        return self.generate(prompt, max_tokens=max_tokens)

    def _format_chat(self, messages: List[Dict[str, str]]) -> str:
        """Форматирование messages в prompt формат Dicta-LM."""
        parts = []
        for msg in messages:
            if msg["role"] == "user":
                parts.append(f"<s>[INST] {msg['content']} [/INST]")
            elif msg["role"] == "assistant":
                parts.append(f"{msg['content']}</s>")
        return "\n".join(parts)
```

---

## Recipe 6: Knowledge Base Repository (v1.x)

```python
# kadima/kb/repository.py
"""SQLite repository для Knowledge Base."""

import sqlite3
import json
import logging
from typing import List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class KBTerm:
    id: Optional[int]
    surface: str
    canonical: str
    lemma: str
    pos: str
    features: dict = field(default_factory=dict)
    definition: Optional[str] = None
    embedding: Optional[bytes] = None
    source_corpus_id: Optional[int] = None
    freq: int = 0


@dataclass
class KBRelation:
    id: Optional[int]
    term_id: int
    related_term_id: int
    relation_type: str  # "synonym" / "hypernym" / "embedding_similar"
    similarity_score: float


class KBRepository:
    """CRUD для KB terms и relations."""

    def __init__(self, db_path: str = "~/.kadima/kadima.db"):
        self.db_path = db_path
        self._ensure_tables()

    def _get_conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _ensure_tables(self):
        """Создать таблицы если не существуют."""
        with self._get_conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS kb_terms (
                    id INTEGER PRIMARY KEY,
                    surface TEXT NOT NULL,
                    canonical TEXT NOT NULL,
                    lemma TEXT,
                    pos TEXT,
                    features TEXT DEFAULT '{}',
                    definition TEXT,
                    embedding BLOB,
                    source_corpus_id INTEGER,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    freq INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS kb_relations (
                    id INTEGER PRIMARY KEY,
                    term_id INTEGER REFERENCES kb_terms(id),
                    related_term_id INTEGER REFERENCES kb_terms(id),
                    relation_type TEXT,
                    similarity_score REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_kb_surface ON kb_terms(surface);
                CREATE INDEX IF NOT EXISTS idx_kb_canonical ON kb_terms(canonical);
            """)

    def create_term(self, term: KBTerm) -> int:
        """Создать термин. Возвращает ID."""
        with self._get_conn() as conn:
            cursor = conn.execute(
                """INSERT INTO kb_terms (surface, canonical, lemma, pos, features,
                   definition, embedding, source_corpus_id, freq)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    term.surface,
                    term.canonical,
                    term.lemma,
                    term.pos,
                    json.dumps(term.features, ensure_ascii=False),
                    term.definition,
                    term.embedding,
                    term.source_corpus_id,
                    term.freq,
                ),
            )
            return cursor.lastrowid

    def search(self, query: str, limit: int = 20) -> List[KBTerm]:
        """Поиск по surface или canonical."""
        with self._get_conn() as conn:
            rows = conn.execute(
                """SELECT * FROM kb_terms
                   WHERE surface LIKE ? OR canonical LIKE ? OR definition LIKE ?
                   ORDER BY freq DESC LIMIT ?""",
                (f"%{query}%", f"%{query}%", f"%{query}%", limit),
            ).fetchall()
            return [self._row_to_term(r) for r in rows]

    def get_term(self, term_id: int) -> Optional[KBTerm]:
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM kb_terms WHERE id = ?", (term_id,)).fetchone()
            return self._row_to_term(row) if row else None

    def update_definition(self, term_id: int, definition: str, source: str = "manual") -> None:
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE kb_terms SET definition = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (definition, term_id),
            )

    def get_related(self, term_id: int, top_n: int = 10) -> List[KBRelation]:
        with self._get_conn() as conn:
            rows = conn.execute(
                """SELECT * FROM kb_relations
                   WHERE term_id = ?
                   ORDER BY similarity_score DESC LIMIT ?""",
                (term_id, top_n),
            ).fetchall()
            return [
                KBRelation(
                    id=r[0], term_id=r[1], related_term_id=r[2],
                    relation_type=r[3], similarity_score=r[4]
                )
                for r in rows
            ]

    def bulk_import_from_pipeline(self, terms: List, corpus_id: int) -> int:
        """Импорт терминов из PipelineResult в KB. Возвращает count."""
        count = 0
        for term in terms:
            kb_term = KBTerm(
                id=None,
                surface=term.surface,
                canonical=term.canonical,
                lemma=term.canonical,
                pos="",
                source_corpus_id=corpus_id,
                freq=term.freq,
            )
            self.create_term(kb_term)
            count += 1
        return count

    def _row_to_term(self, row) -> KBTerm:
        return KBTerm(
            id=row[0], surface=row[1], canonical=row[2], lemma=row[3],
            pos=row[4], features=json.loads(row[5] or "{}"),
            definition=row[6], embedding=row[7],
            source_corpus_id=row[8], freq=row[10],
        )
```

---

## Recipe 7: Config Loader

```python
# kadima/pipeline/config.py
"""Pipeline configuration: dataclass + YAML loader."""

import os
import yaml
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

CONFIG_PATH = os.path.expanduser("~/.kadima/config.yaml")
DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "../../config/config.default.yaml")


@dataclass
class AnnotationConfig:
    label_studio_url: str = "http://localhost:8080"
    label_studio_api_key: Optional[str] = None
    ml_backend_url: str = "http://localhost:9090"


@dataclass
class LLMConfig:
    enabled: bool = False
    server_url: str = "http://localhost:8081"
    model: str = "dictalm-3.0-1.7b-instruct"
    max_tokens: int = 512
    temperature: float = 0.7


@dataclass
class KBConfig:
    enabled: bool = False
    embedding_model: str = "neodictabert"
    auto_generate_definitions: bool = False


@dataclass
class PipelineConfig:
    language: str = "he"
    profile: str = "balanced"
    modules: List[str] = field(default_factory=lambda: [
        "sent_split", "morph_analyzer", "ngram", "np_chunk",
        "canonicalize", "am", "term_extract", "noise"
    ])
    thresholds: Dict[str, Any] = field(default_factory=lambda: {
        "min_freq": 2,
        "pmi_threshold": 3.0,
        "hapax_filter": True,
    })
    annotation: AnnotationConfig = field(default_factory=AnnotationConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    kb: KBConfig = field(default_factory=KBConfig)

    def get_module_config(self, module_name: str) -> Dict[str, Any]:
        """Конфигурация для конкретного модуля."""
        module_configs = {
            "ngram": {
                "min_n": 2, "max_n": 5,
                "min_freq": self.thresholds.get("min_freq", 2),
            },
            "term_extract": {
                "profile": self.profile,
                "min_freq": self.thresholds.get("min_freq", 2),
                "pmi_threshold": self.thresholds.get("pmi_threshold", 3.0),
                "hapax_filter": self.thresholds.get("hapax_filter", True),
            },
        }
        return module_configs.get(module_name, {})


def load_config(path: Optional[str] = None) -> PipelineConfig:
    """Загрузить конфигурацию из YAML."""
    config_path = path or CONFIG_PATH

    if not os.path.exists(config_path):
        logger.warning("Config not found at %s, using defaults", config_path)
        return PipelineConfig()

    with open(config_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    pipeline_raw = raw.get("pipeline", {})
    return PipelineConfig(
        language=pipeline_raw.get("language", "he"),
        profile=pipeline_raw.get("profile", "balanced"),
        modules=pipeline_raw.get("modules", PipelineConfig().modules),
        thresholds=pipeline_raw.get("thresholds", PipelineConfig().thresholds),
        annotation=AnnotationConfig(**raw.get("annotation", {})),
        llm=LLMConfig(**raw.get("llm", {})),
        kb=KBConfig(**raw.get("kb", {})),
    )
```

---

## Сводка: что каждый рецепт делает

| # | Рецепт | Файл | Покрывает |
|---|--------|------|-----------|
| 1 | HebPipe Wrappers | `engine/hebpipe_wrappers.py` | M1, M3 — Processor ABC, dataclasses, error handling |
| 2 | Pipeline Orchestrator | `pipeline/orchestrator.py` | PipelineService — запуск M1→M8, сохранение в БД |
| 3 | LS ML Backend | `ml_backends/kadima_ner_backend.py` | Label Studio NER pre-annotation |
| 4 | LS Client | `annotation/ls_client.py` | REST API клиент для Label Studio |
| 5 | LLM Client | `llm/client.py` | llama.cpp HTTP клиент, chat formatting |
| 6 | KB Repository | `kb/repository.py` | SQLite CRUD для Knowledge Base |
| 7 | Config Loader | `pipeline/config.py` | YAML → dataclass, module configs |
