from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class FeedItemOut(BaseModel):
    id: int
    source_id: str
    title: str
    summary: str | None
    url: str
    published_at: str | None
    symbol: str | None
    tags: list[str]


class WatchlistQuoteOut(BaseModel):
    symbol: str
    display_name: str
    price: float | None
    change_percent: float | None
    volume: float | None
    fetched_at: str | None


class AssetOverviewOut(BaseModel):
    symbol: str
    display_name: str | None
    last_price: float | None
    change_percent: float | None
    volume: float | None
    pe_ratio: float | None
    market_cap: float | None
    updated_at: str | None


class HealthOut(BaseModel):
    status: str
    database: str
    scheduler_running: bool
    last_runs: dict[str, dict[str, Any]]
    data_freshness_seconds: int | None
