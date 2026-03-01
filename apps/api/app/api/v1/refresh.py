from fastapi import APIRouter, HTTPException

from app.dependencies import get_ingestion_service

router = APIRouter(tags=["refresh"])


@router.post("/refresh")
def refresh_now():
    service = get_ingestion_service()
    ok, payload = service.refresh_manual()
    if not ok:
        raise HTTPException(status_code=429, detail=payload["message"])
    return payload
