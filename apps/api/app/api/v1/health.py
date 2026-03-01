from fastapi import APIRouter, Request

from app.dependencies import get_ingestion_service
from app.schemas import HealthOut

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthOut)
def health(request: Request) -> HealthOut:
    service = get_ingestion_service()
    scheduler_running = bool(getattr(request.app.state, "scheduler", None) and request.app.state.scheduler.running)
    payload = service.health_report(scheduler_running=scheduler_running)
    return HealthOut(**payload)
