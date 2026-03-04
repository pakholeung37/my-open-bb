from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from threading import Lock

from app.core.config import Settings
from app.repositories.feed_repository import FeedRepository
from app.repositories.ingestion_repository import IngestionRepository
from app.repositories.market_repository import MarketRepository
from app.services.config_service import load_feeds, load_watchlist
from app.services.feed_service import fetch_and_normalize
from app.services.openbb_adapter import (
    MarketDataError,
    NoDataError,
    UpstreamFetchError,
    fetch_bars,
    fetch_quotes,
)

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
        try:
            return self.refresh_market_data()
        except Exception as exc:  # pragma: no cover
            logger.exception("Market refresh failed")
            return {"status": "error", "message": str(exc)}

    def refresh_market_data(
        self,
        symbols: list[str] | None = None,
        include_bars: bool = True,
        intervals: list[str] | None = None,
        lookback_days: int | None = None,
    ) -> dict:
        resolved_symbols = self._resolve_symbols(symbols)
        if not resolved_symbols:
            raise NoDataError("No symbols provided for market refresh")

        quote_result = self.refresh_market_quotes(resolved_symbols)

        used_intervals = intervals or ["1h", "1d"]
        used_lookback = lookback_days or self.settings.market_default_lookback_days
        bars_count = 0

        if include_bars:
            for symbol in resolved_symbols:
                for interval in used_intervals:
                    bar_result = self.refresh_market_bars(
                        symbol=symbol,
                        interval=interval,
                        lookback_days=used_lookback,
                    )
                    bars_count += int(bar_result["fetched"])

        return {
            "status": "success",
            "quotes_count": quote_result["fetched"],
            "bars_count": bars_count,
            "symbols": resolved_symbols,
            "intervals": used_intervals,
            "finished_at": datetime.now(timezone.utc).isoformat(),
        }

    def refresh_market_quotes(self, symbols: list[str]) -> dict:
        started = datetime.now(timezone.utc)
        try:
            quotes = fetch_quotes(symbols, provider=self.settings.market_provider)
            display_map = {item.symbol: item.display_name for item in load_watchlist(self.settings.watchlist_path)}
            self.market_repository.save_quotes(quotes, display_map=display_map)

            finished = datetime.now(timezone.utc)
            self.ingestion_repository.record_run(
                job_type="market_quotes",
                status="success",
                started_at=started.isoformat(),
                finished_at=finished.isoformat(),
                message=f"Fetched {len(quotes)} quotes",
            )
            return {"status": "success", "fetched": len(quotes)}
        except MarketDataError as exc:
            finished = datetime.now(timezone.utc)
            self.ingestion_repository.record_run(
                job_type="market_quotes",
                status="error",
                started_at=started.isoformat(),
                finished_at=finished.isoformat(),
                message=str(exc),
            )
            raise
        except Exception as exc:  # pragma: no cover
            finished = datetime.now(timezone.utc)
            self.ingestion_repository.record_run(
                job_type="market_quotes",
                status="error",
                started_at=started.isoformat(),
                finished_at=finished.isoformat(),
                message=str(exc),
            )
            raise UpstreamFetchError(str(exc)) from exc

    def refresh_market_bars(self, symbol: str, interval: str, lookback_days: int) -> dict:
        started = datetime.now(timezone.utc)
        job_type = f"market_bars_{interval}"
        try:
            bars = fetch_bars(
                symbol=symbol,
                interval=interval,
                lookback_days=lookback_days,
                provider=self.settings.market_provider,
            )
            self.market_repository.save_bars(symbol=symbol, interval=interval, bars=bars)

            finished = datetime.now(timezone.utc)
            self.ingestion_repository.record_run(
                job_type=job_type,
                status="success",
                started_at=started.isoformat(),
                finished_at=finished.isoformat(),
                message=f"Fetched {len(bars)} bars for {symbol.upper()} {interval}",
            )
            return {"status": "success", "fetched": len(bars)}
        except MarketDataError as exc:
            finished = datetime.now(timezone.utc)
            self.ingestion_repository.record_run(
                job_type=job_type,
                status="error",
                started_at=started.isoformat(),
                finished_at=finished.isoformat(),
                message=f"{symbol.upper()} {interval}: {exc}",
            )
            raise
        except Exception as exc:  # pragma: no cover
            finished = datetime.now(timezone.utc)
            self.ingestion_repository.record_run(
                job_type=job_type,
                status="error",
                started_at=started.isoformat(),
                finished_at=finished.isoformat(),
                message=f"{symbol.upper()} {interval}: {exc}",
            )
            raise UpstreamFetchError(str(exc)) from exc

    def get_quotes(self, symbols: list[str], force_refresh: bool = False) -> dict:
        normalized_symbols = self._resolve_symbols(symbols)
        if not normalized_symbols:
            raise NoDataError("No symbols provided")

        rows = self.market_repository.list_latest_quotes(normalized_symbols)

        if force_refresh or not self._quotes_are_fresh(rows, len(normalized_symbols)):
            self.refresh_market_quotes(normalized_symbols)
            rows = self.market_repository.list_latest_quotes(normalized_symbols)

        if not rows:
            raise NoDataError("No quote data available")

        fetched_values = [str(row["fetched_at"]) for row in rows if row.get("fetched_at")]
        fetched_at = max(fetched_values) if fetched_values else None
        return {
            "provider": self.settings.market_provider,
            "fetched_at": fetched_at,
            "quotes": rows,
        }

    def get_bars(self, symbol: str, interval: str, lookback_days: int, force_refresh: bool = False) -> dict:
        normalized_symbol = symbol.strip().upper()
        if not normalized_symbol:
            raise NoDataError("No symbol provided")

        if force_refresh:
            self.refresh_market_bars(symbol=normalized_symbol, interval=interval, lookback_days=lookback_days)

        since_ts = (datetime.now(timezone.utc) - timedelta(days=lookback_days)).isoformat()
        rows = self.market_repository.list_bars(normalized_symbol, interval, since_ts=since_ts)

        if not rows:
            self.refresh_market_bars(symbol=normalized_symbol, interval=interval, lookback_days=lookback_days)
            rows = self.market_repository.list_bars(normalized_symbol, interval, since_ts=since_ts)

        if not rows:
            raise NoDataError(f"No bars found for {normalized_symbol} {interval}")

        fetched_values = [str(row["fetched_at"]) for row in rows if row.get("fetched_at")]
        fetched_at = max(fetched_values) if fetched_values else None
        return {
            "provider": self.settings.market_provider,
            "symbol": normalized_symbol,
            "interval": interval,
            "fetched_at": fetched_at,
            "bars": rows,
        }

    def refresh_manual(self) -> tuple[bool, dict]:
        ok, cooldown_payload = self._check_manual_cooldown()
        if not ok:
            return False, cooldown_payload

        result = self.refresh_all()
        return True, {"status": "success", "result": result}

    def refresh_market_manual(
        self,
        symbols: list[str] | None = None,
        include_bars: bool = True,
        intervals: list[str] | None = None,
        lookback_days: int | None = None,
    ) -> tuple[bool, dict]:
        ok, cooldown_payload = self._check_manual_cooldown()
        if not ok:
            return False, cooldown_payload

        result = self.refresh_market_data(
            symbols=symbols,
            include_bars=include_bars,
            intervals=intervals,
            lookback_days=lookback_days,
        )
        return True, {"status": "success", "result": result}

    def health_report(self, scheduler_running: bool) -> dict:
        latest_runs = self.ingestion_repository.latest_by_job_type()
        feed_freshness = _seconds_since(self.feed_repository.newest_published_at())
        market_freshness = _seconds_since(self.market_repository.newest_quote_fetched_at())

        upstream_status = "ok"
        market_runs = [
            run
            for job_type, run in latest_runs.items()
            if job_type == "market_quotes" or job_type.startswith("market_bars_")
        ]
        if any(run.get("status") == "error" for run in market_runs):
            upstream_status = "degraded"

        return {
            "status": "ok",
            "database": "ok",
            "scheduler_running": scheduler_running,
            "last_runs": latest_runs,
            "data_freshness_seconds": feed_freshness,
            "market_data_freshness_seconds": market_freshness,
            "upstream_status": upstream_status,
        }

    def _check_manual_cooldown(self) -> tuple[bool, dict]:
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
        return True, {}

    def _resolve_symbols(self, symbols: list[str] | None) -> list[str]:
        if symbols:
            resolved = [symbol.strip().upper() for symbol in symbols if symbol.strip()]
        else:
            resolved = [item.symbol for item in load_watchlist(self.settings.watchlist_path)]
        deduped = sorted(set(resolved))
        return deduped

    def _quotes_are_fresh(self, rows: list[dict], expected_symbols: int) -> bool:
        if len(rows) < expected_symbols:
            return False
        freshness_values = [_seconds_since(row.get("fetched_at")) for row in rows]
        typed_freshness_values: list[int] = [value for value in freshness_values if value is not None]
        if len(typed_freshness_values) < expected_symbols:
            return False
        if not typed_freshness_values:
            return False
        newest_age = max(typed_freshness_values)
        return newest_age <= self.settings.market_quote_ttl_seconds


def _seconds_since(value: object) -> int | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    else:
        parsed = parsed.astimezone(timezone.utc)
    return int((datetime.now(timezone.utc) - parsed).total_seconds())
