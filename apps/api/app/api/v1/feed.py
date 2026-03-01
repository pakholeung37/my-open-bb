from fastapi import APIRouter, Query

from app.core.config import get_settings
from app.repositories.feed_repository import FeedRepository
from app.schemas import FeedItemOut

router = APIRouter(tags=["feed"])


@router.get("/feed", response_model=list[FeedItemOut])
def list_feed(
    source_id: str | None = None,
    symbol: str | None = None,
    tag: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[FeedItemOut]:
    settings = get_settings()
    repository = FeedRepository(settings.database_path)
    rows = repository.list_items(source_id=source_id, symbol=symbol, tag=tag, limit=limit, offset=offset)
    return [FeedItemOut(**row) for row in rows]
