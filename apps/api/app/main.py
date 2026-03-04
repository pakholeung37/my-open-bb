from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import api_router
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.db import init_db
from app.dependencies import get_ingestion_service
from app.services.scheduler_service import SchedulerService

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    init_db(settings.database_path)

    ingestion_service = get_ingestion_service()
    scheduler: SchedulerService | None = None
    if settings.enable_scheduler:
        scheduler = SchedulerService(settings.refresh_interval_minutes, ingestion_service.refresh_all)
        scheduler.start()

    app.state.scheduler = scheduler
    yield

    if scheduler is not None:
        scheduler.shutdown()


settings = get_settings()
app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router)
