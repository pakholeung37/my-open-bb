from __future__ import annotations

from pathlib import Path

from app.db import get_connection
from app.services.config_service import WatchlistItem


class MarketRepository:
    def __init__(self, database_path: Path):
        self.database_path = database_path

    def save_quotes(self, quotes: list[dict], watchlist: list[WatchlistItem]) -> None:
        if not quotes:
            return

        display_map = {item.symbol: item.display_name for item in watchlist}

        with get_connection(self.database_path) as conn:
            for quote in quotes:
                conn.execute(
                    """
                    INSERT INTO market_snapshots(symbol, price, change_percent, volume, fetched_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        quote["symbol"],
                        quote.get("price"),
                        quote.get("change_percent"),
                        quote.get("volume"),
                        quote["fetched_at"],
                    ),
                )

                conn.execute(
                    """
                    INSERT INTO asset_overviews
                    (symbol, display_name, last_price, change_percent, volume, pe_ratio, market_cap, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(symbol) DO UPDATE SET
                        display_name = excluded.display_name,
                        last_price = excluded.last_price,
                        change_percent = excluded.change_percent,
                        volume = excluded.volume,
                        pe_ratio = excluded.pe_ratio,
                        market_cap = excluded.market_cap,
                        updated_at = excluded.updated_at
                    """,
                    (
                        quote["symbol"],
                        display_map.get(quote["symbol"], quote["symbol"]),
                        quote.get("price"),
                        quote.get("change_percent"),
                        quote.get("volume"),
                        quote.get("pe_ratio"),
                        quote.get("market_cap"),
                        quote["fetched_at"],
                    ),
                )

    def list_watchlist_quotes(self, watchlist: list[WatchlistItem]) -> list[dict]:
        output: list[dict] = []
        with get_connection(self.database_path) as conn:
            for item in watchlist:
                row = conn.execute(
                    """
                    SELECT symbol, price, change_percent, volume, fetched_at
                    FROM market_snapshots
                    WHERE symbol = ?
                    ORDER BY fetched_at DESC
                    LIMIT 1
                    """,
                    (item.symbol,),
                ).fetchone()

                output.append(
                    {
                        "symbol": item.symbol,
                        "display_name": item.display_name,
                        "price": row["price"] if row else None,
                        "change_percent": row["change_percent"] if row else None,
                        "volume": row["volume"] if row else None,
                        "fetched_at": row["fetched_at"] if row else None,
                    }
                )
        return output

    def get_asset_overview(self, symbol: str) -> dict | None:
        with get_connection(self.database_path) as conn:
            row = conn.execute(
                """
                SELECT symbol, display_name, last_price, change_percent, volume, pe_ratio, market_cap, updated_at
                FROM asset_overviews
                WHERE symbol = ?
                """,
                (symbol.upper(),),
            ).fetchone()
        return dict(row) if row else None
