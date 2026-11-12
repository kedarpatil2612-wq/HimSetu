"""HIMSETU — FastAPI REST API Server Factory.

Milestone 3: Backend REST API architecture with CORS, database persistence,
dataset management, and scientific processing pipelines.
"""

from __future__ import annotations

from typing import Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from himsetu.api.routes.health import router as health_router
from himsetu.api.routes.datasets import router as datasets_router
from himsetu.api.routes.processing import router as processing_router
from himsetu.db.database import Database
from himsetu.db.repository import DatasetRepository, JobRepository
from himsetu.engine import HimSetuEngine
from himsetu.ingestion.registry import DatasetRegistry


def create_app(
    engine: Optional[HimSetuEngine] = None,
    registry: Optional[DatasetRegistry] = None,
    db: Optional[Database] = None,
) -> FastAPI:
    """Create and configure the HIMSETU FastAPI application."""
    app = FastAPI(
        title="HIMSETU REST API",
        description="AI-Based Subsurface Lunar Ice Detection & Mission Planning System Backend",
        version="0.3.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # 1. CORS Configuration for React Frontend (Milestone 5)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 2. Dependency Wiring & State Attachment
    if engine is None:
        engine = HimSetuEngine()
        engine.initialize()

    if registry is None:
        registry = DatasetRegistry()

    if db is None:
        db = Database()

    dataset_repo = DatasetRepository(db)
    job_repo = JobRepository(db)

    # Sync existing registry items into db repository
    for ds in registry.list_all():
        dataset_repo.save(ds)

    app.state.engine = engine
    app.state.registry = registry
    app.state.db = db
    app.state.dataset_repo = dataset_repo
    app.state.job_repo = job_repo

    # 3. Mount Route Modules
    app.include_router(health_router)
    app.include_router(datasets_router)
    app.include_router(processing_router)

    return app
