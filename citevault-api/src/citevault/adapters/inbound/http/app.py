"""FastAPI app factory."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from citevault.adapters.inbound.http.evidence_routes import router as evidence_router
from citevault.adapters.inbound.http.ollama_routes import router as ollama_router
from citevault.adapters.inbound.http.settings_routes import router as settings_router
from citevault.adapters.inbound.http.tailor_routes import router as tailor_router
from citevault.composition.container import Container, ContainerConfig

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not hasattr(app.state, "container"):
        db = os.environ.get("CITEVAULT_DB", "./citevault.db")
        host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        model = os.environ.get("CITEVAULT_MODEL", "gemma4:e4b")
        timeout_s = float(os.environ.get("CITEVAULT_LLM_TIMEOUT", "600"))
        logger.info("Starting Citevault — db=%s ollama=%s model=%s timeout=%ss", db, host, model, int(timeout_s))
        app.state.container = Container(ContainerConfig(
            db_path=db,
            ollama_base_url=host,
            ollama_model=model,
            ollama_timeout_s=timeout_s,
        ))
    yield
    logger.info("Citevault shutting down.")


def create_app() -> FastAPI:
    cors_env = os.environ.get("CITEVAULT_CORS_ORIGINS", "")
    cors_origins = [o.strip() for o in cors_env.split(",") if o.strip()] or ["*"]

    app = FastAPI(title="Citevault", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(evidence_router)
    app.include_router(tailor_router)
    app.include_router(settings_router)
    app.include_router(ollama_router)

    @app.get("/api/health")
    def health(request: Request) -> dict[str, str]:
        container = request.app.state.container
        if not container.is_ready:
            return {"status": "loading"}
        return {"status": "ok"}

    return app


app = create_app()
