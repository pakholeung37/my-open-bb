from __future__ import annotations

from pathlib import Path

from app.db import init_db
from app.repositories.market_repository import MarketRepository


def test_market_repository_saves_and_reads_quotes_and_bars(tmp_path: Path):
    database_path = tmp_path / "market_test.duckdb"
    init_db(database_path)
    repository = MarketRepository(database_path)

    quote = {
        "symbol": "AAPL",
        "price": 210.12,
        "change_percent": 0.8,
        "volume": 12345.0,
        "pe_ratio": 31.1,
        "market_cap": 3100000000000.0,
        "provider": "yfinance",
        "fetched_at": "2026-03-04T00:00:00+00:00",
    }
    repository.save_quotes([quote], display_map={"AAPL": "Apple"})

    latest_quotes = repository.list_latest_quotes(["AAPL"])
    assert len(latest_quotes) == 1
    assert latest_quotes[0]["symbol"] == "AAPL"
    assert latest_quotes[0]["provider"] == "yfinance"

    overview = repository.get_asset_overview("AAPL")
    assert overview is not None
    assert overview["display_name"] == "Apple"

    bars = [
        {
            "ts": "2026-03-03T00:00:00+00:00",
            "open": 200.0,
            "high": 215.0,
            "low": 198.0,
            "close": 210.0,
            "volume": 1000.0,
            "provider": "yfinance",
            "fetched_at": "2026-03-04T00:00:00+00:00",
        },
        {
            "ts": "2026-03-04T00:00:00+00:00",
            "open": 210.0,
            "high": 220.0,
            "low": 205.0,
            "close": 218.0,
            "volume": 1200.0,
            "provider": "yfinance",
            "fetched_at": "2026-03-04T00:00:00+00:00",
        },
    ]
    repository.save_bars(symbol="AAPL", interval="1d", bars=bars)

    read_bars = repository.list_bars(symbol="AAPL", interval="1d")
    assert len(read_bars) == 2
    assert read_bars[0]["ts"] == "2026-03-03T00:00:00+00:00"
