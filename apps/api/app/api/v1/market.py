from __future__ import annotations

from typing import Literal, NoReturn

from fastapi import APIRouter, HTTPException, Query

from app.core.config import get_settings
from app.dependencies import get_ingestion_service
from app.repositories.market_repository import MarketRepository
from app.schemas import (
    BarOut,
    MarketBarsResponse,
    MarketQuotesResponse,
    MarketRefreshRequest,
    MarketRefreshResponse,
    QuoteOut,
    WatchlistQuoteOut,
)
from app.services.config_service import load_watchlist
from app.services.openbb_adapter import (
    MarketDataError,
    NoDataError,
    ProviderUnavailableError,
    UpstreamFetchError,
)

router = APIRouter(tags=["market"])


@router.get("/market/watchlist", response_model=list[WatchlistQuoteOut])
def watchlist_quotes() -> list[WatchlistQuoteOut]:
    settings = get_settings()
    watchlist = load_watchlist(settings.watchlist_path)
    repository = MarketRepository(settings.database_path)
    rows = repository.list_watchlist_quotes(watchlist)
    return [WatchlistQuoteOut(**row) for row in rows]


@router.get("/market/quotes", response_model=MarketQuotesResponse)
def market_quotes(
    symbols: str = Query(..., description="Comma-separated symbol list, e.g. AAPL,MSFT,SPY"),
    force_refresh: bool = Query(default=False),
) -> MarketQuotesResponse:
    parsed_symbols = _parse_symbols(symbols)
    if not parsed_symbols:
        raise HTTPException(status_code=400, detail="symbols is required")

    service = get_ingestion_service()
    try:
        payload = service.get_quotes(parsed_symbols, force_refresh=force_refresh)
    except MarketDataError as exc:
        _raise_market_http_error(exc)

    quotes = [QuoteOut(**row) for row in payload["quotes"]]
    return MarketQuotesResponse(provider=payload["provider"], fetched_at=payload["fetched_at"], quotes=quotes)


@router.get("/market/bars", response_model=MarketBarsResponse)
def market_bars(
    symbol: str = Query(...),
    interval: Literal["1h", "1d"] = Query(...),
    lookback_days: int | None = Query(default=None, ge=1, le=3650),
    force_refresh: bool = Query(default=False),
) -> MarketBarsResponse:
    service = get_ingestion_service()
    resolved_lookback = lookback_days or get_settings().market_default_lookback_days
    try:
        payload = service.get_bars(
            symbol=symbol,
            interval=interval,
            lookback_days=resolved_lookback,
            force_refresh=force_refresh,
        )
    except MarketDataError as exc:
        _raise_market_http_error(exc)

    bars = [
        BarOut(
            ts=row["ts"],
            open=row.get("open"),
            high=row.get("high"),
            low=row.get("low"),
            close=row.get("close"),
            volume=row.get("volume"),
        )
        for row in payload["bars"]
    ]
    return MarketBarsResponse(
        provider=payload["provider"],
        symbol=payload["symbol"],
        interval=payload["interval"],
        fetched_at=payload["fetched_at"],
        bars=bars,
    )


@router.post("/market/refresh", response_model=MarketRefreshResponse)
def refresh_market(payload: MarketRefreshRequest) -> MarketRefreshResponse:
    service = get_ingestion_service()
    try:
        ok, result = service.refresh_market_manual(
            symbols=payload.symbols,
            include_bars=payload.include_bars,
            intervals=list(payload.intervals),
            lookback_days=payload.lookback_days,
        )
    except MarketDataError as exc:
        _raise_market_http_error(exc)

    if not ok:
        raise HTTPException(status_code=429, detail=result["message"])
    return MarketRefreshResponse(**result)


def _parse_symbols(value: str) -> list[str]:
    return sorted({symbol.strip().upper() for symbol in value.split(",") if symbol.strip()})


def _raise_market_http_error(exc: MarketDataError) -> NoReturn:
    if isinstance(exc, ProviderUnavailableError):
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if isinstance(exc, NoDataError):
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if isinstance(exc, UpstreamFetchError):
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    raise HTTPException(status_code=502, detail=str(exc)) from exc
