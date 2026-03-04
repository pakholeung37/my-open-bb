from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


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


class QuoteOut(BaseModel):
    symbol: str
    price: float | None
    change_percent: float | None
    volume: float | None
    pe_ratio: float | None
    market_cap: float | None
    provider: str
    fetched_at: str


class BarOut(BaseModel):
    ts: str
    open: float | None
    high: float | None
    low: float | None
    close: float | None
    volume: float | None


class MarketQuotesResponse(BaseModel):
    provider: str
    fetched_at: str | None
    quotes: list[QuoteOut]


class MarketBarsResponse(BaseModel):
    provider: str
    symbol: str
    interval: Literal["1h", "1d"]
    fetched_at: str | None
    bars: list[BarOut]


def _default_intervals() -> list[Literal["1h", "1d"]]:
    return ["1h", "1d"]


class MarketRefreshRequest(BaseModel):
    symbols: list[str] | None = None
    include_bars: bool = True
    intervals: list[Literal["1h", "1d"]] = Field(default_factory=_default_intervals)
    lookback_days: int | None = Field(default=None, ge=1, le=3650)


class MarketRefreshResult(BaseModel):
    status: str
    quotes_count: int
    bars_count: int
    symbols: list[str]
    intervals: list[str]
    finished_at: str


class MarketRefreshResponse(BaseModel):
    status: str
    result: MarketRefreshResult


class HealthOut(BaseModel):
    status: str
    database: str
    scheduler_running: bool
    last_runs: dict[str, dict[str, Any]]
    data_freshness_seconds: int | None
    market_data_freshness_seconds: int | None = None
    upstream_status: str = "ok"
