from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, cast

logger = logging.getLogger(__name__)

_openbb_client: Any
try:
    from openbb import obb as _openbb_client  # type: ignore
except Exception:  # pragma: no cover
    _openbb_client = None

obb: Any = _openbb_client


class MarketDataError(RuntimeError):
    pass


class ProviderUnavailableError(MarketDataError):
    pass


class UpstreamFetchError(MarketDataError):
    pass


class NoDataError(MarketDataError):
    pass


def fetch_quotes(symbols: list[str], provider: str = "yfinance") -> list[dict]:
    normalized_symbols = [symbol.strip().upper() for symbol in symbols if symbol.strip()]
    if not normalized_symbols:
        return []

    _ensure_obb()

    try:
        result = obb.equity.price.quote(symbol=normalized_symbols, provider=provider)
    except Exception as exc:  # pragma: no cover
        logger.warning("OpenBB quote fetch failed: %s", exc)
        raise UpstreamFetchError(str(exc)) from exc

    data = _result_to_records(result)
    if not data:
        raise NoDataError("No quote data returned")

    rows: list[dict] = []
    fetched_at = datetime.now(timezone.utc).isoformat()
    for row in data:
        symbol = str(row.get("symbol") or row.get("ticker") or "").upper()
        if not symbol:
            continue
        rows.append(
            {
                "symbol": symbol,
                "price": _to_float(row.get("last_price") or row.get("price") or row.get("last")),
                "change_percent": _to_float(row.get("change_percent") or row.get("chg_pct") or row.get("percent_change")),
                "volume": _to_float(row.get("volume")),
                "fetched_at": fetched_at,
                "pe_ratio": _to_float(row.get("pe_ratio") or row.get("pe") or row.get("trailing_pe")),
                "market_cap": _to_float(row.get("market_cap") or row.get("marketcap")),
                "provider": provider,
            }
        )

    if not rows:
        raise NoDataError("No quote rows could be parsed")
    return rows


def fetch_bars(symbol: str, interval: str, lookback_days: int, provider: str = "yfinance") -> list[dict]:
    if interval not in {"1h", "1d"}:
        raise ValueError(f"Unsupported interval: {interval}")

    _ensure_obb()

    normalized_symbol = symbol.strip().upper()
    if not normalized_symbol:
        return []

    start_date = (datetime.now(timezone.utc) - timedelta(days=lookback_days)).date().isoformat()
    result = _fetch_historical_result(normalized_symbol, interval, start_date, provider)
    data = _result_to_records(result)

    if not data:
        raise NoDataError(f"No historical bars returned for {normalized_symbol} {interval}")

    fetched_at = datetime.now(timezone.utc).isoformat()
    bars: list[dict] = []
    for row in data:
        ts = _normalize_timestamp(
            row.get("date")
            or row.get("datetime")
            or row.get("timestamp")
            or row.get("time")
            or row.get("index")
        )
        if not ts:
            continue

        bars.append(
            {
                "symbol": normalized_symbol,
                "interval": interval,
                "ts": ts,
                "open": _to_float(row.get("open") or row.get("Open")),
                "high": _to_float(row.get("high") or row.get("High")),
                "low": _to_float(row.get("low") or row.get("Low")),
                "close": _to_float(row.get("close") or row.get("Close") or row.get("adj_close") or row.get("Adj Close")),
                "volume": _to_float(row.get("volume") or row.get("Volume")),
                "provider": provider,
                "fetched_at": fetched_at,
            }
        )

    if not bars:
        raise NoDataError(f"No bars could be parsed for {normalized_symbol} {interval}")

    bars.sort(key=lambda row: row["ts"])
    return bars


def _fetch_historical_result(symbol: str, interval: str, start_date: str, provider: str) -> Any:
    attempts = [
        {
            "symbol": symbol,
            "provider": provider,
            "interval": interval,
            "start_date": start_date,
        },
        {
            "symbol": symbol,
            "provider": provider,
            "start_date": start_date,
            "interval": interval,
        },
        {
            "symbol": symbol,
            "provider": provider,
            "start_date": start_date,
        },
    ]

    last_exc: Exception | None = None
    for kwargs in attempts:
        try:
            return obb.equity.price.historical(**kwargs)
        except TypeError as exc:
            last_exc = exc
            continue
        except Exception as exc:  # pragma: no cover
            logger.warning("OpenBB historical fetch failed: %s", exc)
            raise UpstreamFetchError(str(exc)) from exc

    raise UpstreamFetchError(str(last_exc) if last_exc else "OpenBB historical call failed")


def _result_to_records(result: Any) -> list[dict[str, Any]]:
    if result is None:
        return []

    if hasattr(result, "to_df"):
        df = result.to_df()
        if hasattr(df, "reset_index"):
            df = df.reset_index()
        if hasattr(df, "to_dict"):
            return cast(list[dict[str, Any]], df.to_dict("records"))

    if isinstance(result, list):
        return [row for row in result if isinstance(row, dict)]

    return []


def _ensure_obb() -> None:
    if obb is None:
        raise ProviderUnavailableError("OpenBB is not available")


def _normalize_timestamp(value: object) -> str | None:
    if value is None:
        return None

    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc).isoformat()
        return value.astimezone(timezone.utc).isoformat()

    text = str(value).strip()
    if not text:
        return None

    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        else:
            parsed = parsed.astimezone(timezone.utc)
        return parsed.isoformat()
    except ValueError:
        return text


def _to_float(value: object) -> float | None:
    try:
        if value is None:
            return None
        if isinstance(value, (float, int)):
            return float(value)
        if isinstance(value, str):
            return float(value)
        return None
    except (TypeError, ValueError):
        return None
