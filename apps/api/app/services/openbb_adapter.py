from __future__ import annotations

import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

try:
    from openbb import obb  # type: ignore
except Exception:  # pragma: no cover
    obb = None


def fetch_watchlist_quotes(symbols: list[str]) -> list[dict]:
    if not symbols:
        return []

    if obb is None:
        logger.warning("OpenBB is not available; returning empty market data")
        return []

    try:
        result = obb.equity.price.quote(symbol=symbols, provider="yfinance")
        data = result.to_df().to_dict("records") if hasattr(result, "to_df") else []
    except Exception as exc:  # pragma: no cover
        logger.warning("OpenBB quote fetch failed: %s", exc)
        return []

    rows: list[dict] = []
    fetched_at = datetime.now(timezone.utc).isoformat()
    for row in data:
        symbol = str(row.get("symbol") or "").upper()
        if not symbol:
            continue
        rows.append(
            {
                "symbol": symbol,
                "price": _to_float(row.get("last_price") or row.get("price")),
                "change_percent": _to_float(row.get("change_percent") or row.get("chg_pct")),
                "volume": _to_float(row.get("volume")),
                "fetched_at": fetched_at,
                "pe_ratio": _to_float(row.get("pe_ratio") or row.get("pe")),
                "market_cap": _to_float(row.get("market_cap")),
            }
        )
    return rows


def _to_float(value):
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None
