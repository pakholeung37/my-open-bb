from __future__ import annotations

from functools import lru_cache

from app.core.config import get_settings
from app.repositories.feed_repository import FeedRepository
from app.repositories.ingestion_repository import IngestionRepository
from app.repositories.market_repository import MarketRepository
from app.services.ingestion_service import IngestionService


@lru_cache(maxsize=1)
def get_ingestion_service() -> IngestionService:
    settings = get_settings()
    feed_repository = FeedRepository(settings.database_path)
    market_repository = MarketRepository(settings.database_path)
    ingestion_repository = IngestionRepository(settings.database_path)
    return IngestionService(
        settings=settings,
        feed_repository=feed_repository,
        market_repository=market_repository,
        ingestion_repository=ingestion_repository,
    )
