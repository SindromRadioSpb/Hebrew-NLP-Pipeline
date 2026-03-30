# kadima/annotation/ml_backend.py
"""Label Studio ML Backend — prediction service.

Implements the LS ML backend protocol:
  POST /predict  — pre-annotate tasks
  POST /setup    — initialize with labeling config
  POST /train    — (stub) trigger training
  GET  /health   — health check

Run standalone:
    python -m kadima.annotation.ml_backend --port 9090

Or via Docker (docker-compose).
"""

import logging
import argparse
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from fastapi import FastAPI
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# ── LS ML Backend protocol models ────────────────────────────────────────────


class TaskData(BaseModel):
    """Single task from Label Studio."""
    text: Optional[str] = None
    term_surface: Optional[str] = None
    context: Optional[str] = None


class Task(BaseModel):
    """Label Studio task."""
    id: Optional[int] = None
    data: TaskData


class Prediction(BaseModel):
    """Prediction result for one task."""
    model_version: str = "kadima-0.9"
    score: float = 0.0
    result: List[Dict[str, Any]] = Field(default_factory=list)


class PredictRequest(BaseModel):
    """POST /predict body."""
    tasks: List[Task]
    label_config: Optional[str] = None
    project: Optional[Dict] = None


class PredictResponse(BaseModel):
    """POST /predict response."""
    results: List[Prediction]


class SetupRequest(BaseModel):
    """POST /setup body."""
    label_config: str
    project: Optional[Dict] = None


class SetupResponse(BaseModel):
    """POST /setup response."""
    model_version: str = "kadima-0.9"
    health: Dict = Field(default_factory=lambda: {"isBroken": False})


class TrainRequest(BaseModel):
    """POST /train body."""
    annotations: List[Dict] = Field(default_factory=list)
    project: Optional[Dict] = None
    label_config: Optional[str] = None


class TrainResponse(BaseModel):
    """POST /train response."""
    model_version: str = "kadima-0.9"
    job_id: Optional[int] = None


# ── Prediction engines ───────────────────────────────────────────────────────


@dataclass
class NERPrediction:
    """NER span prediction."""
    label: str
    start: int
    end: int
    text: str
    confidence: float = 0.8


def predict_ner(text: str, pipeline=None) -> List[NERPrediction]:
    """Generate NER predictions for Hebrew text.

    Args:
        text: Hebrew text to annotate.
        pipeline: Optional pipeline instance (uses mock if None).

    Returns:
        List of NERPrediction spans.
    """
    if pipeline is None:
        # Stub: return empty predictions (no pipeline loaded)
        logger.debug("No pipeline loaded, returning empty NER predictions")
        return []

    # TODO: integrate with kadima.pipeline.orchestrator
    # results = pipeline.run_on_text(text)
    # for term in results.terms:
    #     spans.append(NERPrediction(label="TERM", ...))
    return []


def predict_term_review(term_surface: str, context: str = "") -> Dict[str, Any]:
    """Generate term review prediction.

    For term review tasks, we pre-fill the decision based on
    existing KB or pipeline confidence.
    """
    # Stub: no prediction, let human decide
    return {
        "decision": None,
        "confidence": 0.0,
    }


# ── FastAPI app ──────────────────────────────────────────────────────────────


def create_app() -> FastAPI:
    """Create Label Studio ML Backend app."""
    app = FastAPI(
        title="KADIMA ML Backend",
        description="Label Studio ML Backend for Hebrew NLP annotation",
        version="0.9.0",
    )

    # State
    app.state.label_config = ""
    app.state.model_version = "kadima-0.9"
    app.state.pipeline = None

    @app.get("/health")
    async def health():
        return {
            "status": "ok",
            "model_version": app.state.model_version,
            "pipeline_loaded": app.state.pipeline is not None,
        }

    @app.post("/setup", response_model=SetupResponse)
    async def setup(request: SetupRequest):
        """Initialize model with labeling config."""
        app.state.label_config = request.label_config
        logger.info("Setup received label_config (%d chars)", len(request.label_config))

        # Detect project type from label_config
        if "NER" in request.label_config or "PERSON" in request.label_config:
            project_type = "ner"
        elif "term_surface" in request.label_config:
            project_type = "term_review"
        elif "pos" in request.label_config:
            project_type = "pos"
        else:
            project_type = "unknown"

        logger.info("Detected project type: %s", project_type)

        return SetupResponse(
            model_version=app.state.model_version,
            health={"isBroken": False},
        )

    @app.post("/predict", response_model=PredictResponse)
    async def predict(request: PredictRequest):
        """Generate predictions for tasks."""
        results = []

        for task in request.tasks:
            text = task.data.text or ""
            term = task.data.term_surface or ""

            prediction = Prediction(
                model_version=app.state.model_version,
                score=0.0,
                result=[],
            )

            if text:
                # NER-style: predict entity spans
                ner_preds = predict_ner(text, pipeline=app.state.pipeline)
                for np in ner_preds:
                    prediction.result.append({
                        "from_name": "label",
                        "to_name": "text",
                        "type": "labels",
                        "value": {
                            "start": np.start,
                            "end": np.end,
                            "text": np.text,
                            "labels": [np.label],
                        },
                        "score": np.confidence,
                    })
                    prediction.score = max(prediction.score, np.confidence)

            elif term:
                # Term review-style: pre-fill decision
                review = predict_term_review(term, task.data.context or "")
                if review["decision"]:
                    prediction.result.append({
                        "from_name": "decision",
                        "to_name": "term_surface",
                        "type": "choices",
                        "value": {
                            "choices": [review["decision"]],
                        },
                        "score": review["confidence"],
                    })
                    prediction.score = review["confidence"]

            results.append(prediction)

        return PredictResponse(results=results)

    @app.post("/train", response_model=TrainResponse)
    async def train(request: TrainRequest):
        """Receive annotations for training.

        Processes annotated tasks and updates internal statistics.
        For NER: collects entity spans, updates term frequency counts.
        For term review: collects human decisions, updates KB.

        Returns:
            TrainResponse with model_version and job_id.
        """
        n = len(request.annotations)
        logger.info("Train called with %d annotations", n)

        if n == 0:
            return TrainResponse(
                model_version=app.state.model_version,
                job_id=None,
            )

        # ── Extract ground-truth entities from annotations ──
        entity_count = 0
        term_decisions = {}

        for annotation in request.annotations:
            results = annotation.get("result", [])
            for r in results:
                rtype = r.get("type")

                if rtype == "labels":
                    # NER annotation — collect entity spans
                    value = r.get("value", {})
                    labels = value.get("labels", [])
                    text = value.get("text", "")
                    if labels and text:
                        entity_count += 1

                elif rtype == "choices":
                    # Term review — collect decisions
                    value = r.get("value", {})
                    choices = value.get("choices", [])
                    task = annotation.get("task", {})
                    term_surface = task.get("data", {}).get("term_surface", "")
                    if term_surface and choices:
                        term_decisions[term_surface] = choices[0]

        # ── Update pipeline/KB if available ──
        if app.state.pipeline and term_decisions:
            logger.info("Applying %d term decisions to pipeline", len(term_decisions))
            # TODO: integrate with kadima.pipeline.orchestrator
            # for term, decision in term_decisions.items():
            #     if decision == "accept":
            #         pipeline.kb.add_term(term)

        logger.info(
            "Training complete: %d annotations, %d entities, %d term decisions",
            n, entity_count, len(term_decisions),
        )

        return TrainResponse(
            model_version=app.state.model_version,
            job_id=None,
        )

    return app


app = create_app()


# ── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    parser = argparse.ArgumentParser(description="KADIMA ML Backend for Label Studio")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=9090)
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    uvicorn.run(app, host=args.host, port=args.port)
