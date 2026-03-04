from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from app.db import fetchall_dicts, fetchone_dict, get_connection
from app.services.config_service import WatchlistItem


class MarketRepository:
    def __init__(self, database_path: Path):
        self.database_path = database_path

    def save_quotes(self, quotes: list[dict], display_map: dict[str, str] | None = None) -> None:
        if not quotes:
            return

        resolved_display_map = display_map or {}
        with get_connection(self.database_path) as conn:
            for quote in quotes:
                symbol = str(quote["symbol"]).upper()
                fetched_at = quote["fetched_at"]
                provider = str(quote.get("provider") or "yfinance")

                conn.execute(
                    """
                    INSERT INTO market_quotes(symbol, price, change_percent, volume, pe_ratio, market_cap, provider, fetched_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        symbol,
                        quote.get("price"),
                        quote.get("change_percent"),
                        quote.get("volume"),
                        quote.get("pe_ratio"),
                        quote.get("market_cap"),
                        provider,
                        fetched_at,
                    ],
                )

                conn.execute("DELETE FROM asset_overviews WHERE symbol = ?", [symbol])
                conn.execute(
                    """
                    INSERT INTO asset_overviews
                    (symbol, display_name, last_price, change_percent, volume, pe_ratio, market_cap, provider, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        symbol,
                        resolved_display_map.get(symbol, symbol),
                        quote.get("price"),
                        quote.get("change_percent"),
                        quote.get("volume"),
                        quote.get("pe_ratio"),
                        quote.get("market_cap"),
                        provider,
                        fetched_at,
                    ],
                )

    def save_bars(self, symbol: str, interval: str, bars: list[dict]) -> None:
        if not bars:
            return

        normalized_symbol = symbol.upper()
        with get_connection(self.database_path) as conn:
            for bar in bars:
                ts = bar["ts"]
                conn.execute(
                    "DELETE FROM market_bars WHERE symbol = ? AND interval = ? AND ts = ?",
                    [normalized_symbol, interval, ts],
                )
                conn.execute(
                    """
                    INSERT INTO market_bars(symbol, interval, ts, open, high, low, close, volume, provider, fetched_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        normalized_symbol,
                        interval,
                        ts,
                        bar.get("open"),
                        bar.get("high"),
                        bar.get("low"),
                        bar.get("close"),
                        bar.get("volume"),
                        bar.get("provider") or "yfinance",
                        bar.get("fetched_at"),
                    ],
                )

    def list_watchlist_quotes(self, watchlist: list[WatchlistItem]) -> list[dict]:
        symbols = [item.symbol for item in watchlist]
        latest = {row["symbol"]: row for row in self.list_latest_quotes(symbols)}
        output: list[dict] = []
        for item in watchlist:
            row = latest.get(item.symbol)
            output.append(
                {
                    "symbol": item.symbol,
                    "display_name": item.display_name,
                    "price": row.get("price") if row else None,
                    "change_percent": row.get("change_percent") if row else None,
                    "volume": row.get("volume") if row else None,
                    "fetched_at": _to_iso(row.get("fetched_at")) if row else None,
                }
            )
        return output

    def list_latest_quotes(self, symbols: list[str]) -> list[dict]:
        normalized = [symbol.strip().upper() for symbol in symbols if symbol.strip()]
        if not normalized:
            return []

        placeholders = ",".join("?" for _ in normalized)
        query = f"""
            SELECT symbol, price, change_percent, volume, pe_ratio, market_cap, provider, fetched_at
            FROM (
                SELECT
                    symbol,
                    price,
                    change_percent,
                    volume,
                    pe_ratio,
                    market_cap,
                    provider,
                    fetched_at,
                    ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY fetched_at DESC) AS rn
                FROM market_quotes
                WHERE symbol IN ({placeholders})
            ) ranked
            WHERE rn = 1
            ORDER BY symbol
        """
        with get_connection(self.database_path) as conn:
            rows = fetchall_dicts(conn, query, normalized)

        output: list[dict] = []
        for row in rows:
            output.append(
                {
                    "symbol": row["symbol"],
                    "price": row.get("price"),
                    "change_percent": row.get("change_percent"),
                    "volume": row.get("volume"),
                    "pe_ratio": row.get("pe_ratio"),
                    "market_cap": row.get("market_cap"),
                    "provider": row.get("provider"),
                    "fetched_at": _to_iso(row.get("fetched_at")),
                }
            )
        return output

    def list_bars(self, symbol: str, interval: str, since_ts: str | None = None) -> list[dict]:
        params: list = [symbol.upper(), interval]
        where_since = ""
        if since_ts:
            where_since = " AND ts >= ?"
            params.append(since_ts)

        with get_connection(self.database_path) as conn:
            rows = fetchall_dicts(
                conn,
                f"""
                SELECT symbol, interval, ts, open, high, low, close, volume, provider, fetched_at
                FROM market_bars
                WHERE symbol = ? AND interval = ?{where_since}
                ORDER BY ts ASC
                """,
                params,
            )

        output: list[dict] = []
        for row in rows:
            output.append(
                {
                    "symbol": row["symbol"],
                    "interval": row["interval"],
                    "ts": _to_iso(row.get("ts")),
                    "open": row.get("open"),
                    "high": row.get("high"),
                    "low": row.get("low"),
                    "close": row.get("close"),
                    "volume": row.get("volume"),
                    "provider": row.get("provider"),
                    "fetched_at": _to_iso(row.get("fetched_at")),
                }
            )
        return output

    def newest_quote_fetched_at(self) -> str | None:
        with get_connection(self.database_path) as conn:
            row = fetchone_dict(conn, "SELECT MAX(fetched_at) AS newest FROM market_quotes")
        if not row:
            return None
        return _to_iso(row.get("newest"))

    def get_asset_overview(self, symbol: str) -> dict | None:
        with get_connection(self.database_path) as conn:
            row = fetchone_dict(
                conn,
                """
                SELECT symbol, display_name, last_price, change_percent, volume, pe_ratio, market_cap, updated_at
                FROM asset_overviews
                WHERE symbol = ?
                """,
                [symbol.upper()],
            )
        if not row:
            return None
        row["updated_at"] = _to_iso(row.get("updated_at"))
        return row


def _to_iso(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc).isoformat()
        return value.astimezone(timezone.utc).isoformat()
    return str(value)
