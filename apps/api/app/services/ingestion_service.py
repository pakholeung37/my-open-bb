from __future__ import annotations

import logging
from datetime import datetime, timezone
from threading import Lock

from app.core.config import Settings
from app.repositories.feed_repository import FeedRepository
from app.repositories.ingestion_repository import IngestionRepository
from app.repositories.market_repository import MarketRepository
from app.services.config_service import load_feeds, load_watchlist
from app.services.feed_service import fetch_and_normalize
from app.services.openbb_adapter import fetch_watchlist_quotes

logger = logging.getLogger(__name__)


class IngestionService:
    def __init__(
        self,
        settings: Settings,
        feed_repository: FeedRepository,
        market_repository: MarketRepository,
        ingestion_repository: IngestionRepository,
    ):
        self.settings = settings
        self.feed_repository = feed_repository
        self.market_repository = market_repository
        self.ingestion_repository = ingestion_repository
        self._lock = Lock()
        self._manual_last_triggered_at: datetime | None = None

    def refresh_all(self) -> dict:
        feed_result = self.refresh_feeds()
        market_result = self.refresh_market()
        return {"feeds": feed_result, "market": market_result}

    def refresh_feeds(self) -> dict:
        started = datetime.now(timezone.utc)
        try:
            feeds = load_feeds(self.settings.feeds_path)
            watchlist = load_watchlist(self.settings.watchlist_path)
            items = fetch_and_normalize(feeds, watchlist)
            inserted = self.feed_repository.save_items(items)
            finished = datetime.now(timezone.utc)
            self.ingestion_repository.record_run(
                job_type="feed",
                status="success",
                started_at=started.isoformat(),
                finished_at=finished.isoformat(),
                message=f"Inserted {inserted} items",
            )
            return {"status": "success", "inserted": inserted}
        except Exception as exc:  # pragma: no cover
            finished = datetime.now(timezone.utc)
            self.ingestion_repository.record_run(
                job_type="feed",
                status="error",
                started_at=started.isoformat(),
                finished_at=finished.isoformat(),
                message=str(exc),
            )
            logger.exception("Feed refresh failed")
            return {"status": "error", "message": str(exc)}

    def refresh_market(self) -> dict:
        started = datetime.now(timezone.utc)
        try:
            watchlist = load_watchlist(self.settings.watchlist_path)
            symbols = [item.symbol for item in watchlist]
            quotes = fetch_watchlist_quotes(symbols)
            self.market_repository.save_quotes(quotes, watchlist)
            finished = datetime.now(timezone.utc)
            self.ingestion_repository.record_run(
                job_type="market",
                status="success",
                started_at=started.isoformat(),
                finished_at=finished.isoformat(),
                message=f"Fetched {len(quotes)} quotes",
            )
            return {"status": "success", "fetched": len(quotes)}
        except Exception as exc:  # pragma: no cover
            finished = datetime.now(timezone.utc)
            self.ingestion_repository.record_run(
                job_type="market",
                status="error",
                started_at=started.isoformat(),
                finished_at=finished.isoformat(),
                message=str(exc),
            )
            logger.exception("Market refresh failed")
            return {"status": "error", "message": str(exc)}

    def refresh_manual(self) -> tuple[bool, dict]:
        with self._lock:
            now = datetime.now(timezone.utc)
            if self._manual_last_triggered_at is not None:
                elapsed = (now - self._manual_last_triggered_at).total_seconds()
                if elapsed < self.settings.manual_refresh_cooldown_seconds:
                    return False, {
                        "status": "cooldown",
                        "message": f"Retry after {int(self.settings.manual_refresh_cooldown_seconds - elapsed)}s",
                    }

            self._manual_last_triggered_at = now

        result = self.refresh_all()
        return True, {"status": "success", "result": result}

    def health_report(self, scheduler_running: bool) -> dict:
        latest_runs = self.ingestion_repository.latest_by_job_type()
        newest = self.feed_repository.newest_published_at()
        freshness: int | None = None
        if newest:
            try:
                newest_dt = datetime.fromisoformat(newest)
                freshness = int((datetime.now(timezone.utc) - newest_dt).total_seconds())
            except ValueError:
                freshness = None

        return {
            "status": "ok",
            "database": "ok",
            "scheduler_running": scheduler_running,
            "last_runs": latest_runs,
            "data_freshness_seconds": freshness,
        }
