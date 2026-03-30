# kadima/api/app.py
"""FastAPI application factory для KADIMA REST API."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from kadima.api.routers import corpora, pipeline, validation

# v1.x routers (conditionally imported)
try:
    from kadima.api.routers import annotation, kb, llm
    HAS_EXTENDED = True
except ImportError:
    HAS_EXTENDED = False


def create_app() -> FastAPI:
    """Создать FastAPI приложение."""
    app = FastAPI(
        title="KADIMA API",
        description="Hebrew NLP Platform — REST API",
        version=__import__("kadima").__version__,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:8080"],  # Label Studio
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Core routers (v1.0)
    app.include_router(corpora.router, prefix="/api/v1", tags=["corpora"])
    app.include_router(pipeline.router, prefix="/api/v1", tags=["pipeline"])
    app.include_router(validation.router, prefix="/api/v1", tags=["validation"])

    # Extended routers (v1.x)
    if HAS_EXTENDED:
        app.include_router(annotation.router, prefix="/api/v1", tags=["annotation"])
        app.include_router(kb.router, prefix="/api/v1", tags=["kb"])
        app.include_router(llm.router, prefix="/api/v1", tags=["llm"])

    @app.get("/health")
    async def health():
        return {"status": "ok", "version": __import__("kadima").__version__}

    return app


app = create_app()
