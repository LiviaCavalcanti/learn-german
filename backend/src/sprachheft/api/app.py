"""FastAPI application factory."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sprachheft import __version__
from sprachheft.api import (
    course,
    dictionary,
    exercises,
    imports,
    ingest,
    materials,
    practice,
    reference,
    review,
    vocab,
)
from sprachheft.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    from sprachheft.db import init_db
    from sprachheft.reminders.scheduler import shutdown_reminders, start_reminders
    from sprachheft.seed import seed_taxonomy

    init_db()
    seed_taxonomy()
    start_reminders()
    try:
        yield
    finally:
        shutdown_reminders()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version=__version__, lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["meta"])
    def health() -> dict:
        return {"status": "ok", "app": settings.app_name, "version": __version__}

    app.include_router(materials.router)
    app.include_router(reference.router)
    app.include_router(vocab.router)
    app.include_router(dictionary.router)
    app.include_router(exercises.router)
    app.include_router(practice.router)
    app.include_router(review.router)
    app.include_router(imports.router)
    app.include_router(course.router)
    app.include_router(ingest.router)

    return app


app = create_app()
