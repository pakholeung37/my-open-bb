from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.services import openbb_adapter


class _FakeFrame:
    def __init__(self, rows: list[dict]):
        self._rows = rows

    def reset_index(self):
        return self

    def to_dict(self, orient: str) -> list[dict]:
        assert orient == "records"
        return self._rows


class _FakeResult:
    def __init__(self, rows: list[dict]):
        self._rows = rows

    def to_df(self) -> _FakeFrame:
        return _FakeFrame(self._rows)


class _FakePriceApi:
    def quote(self, symbol: list[str], provider: str):
        assert provider == "yfinance"
        return _FakeResult(
            [
                {
                    "symbol": symbol[0],
                    "last_price": 200.0,
                    "change_percent": 0.5,
                    "volume": 10000,
                    "pe_ratio": 30.0,
                    "market_cap": 1000000,
                }
            ]
        )

    def historical(self, **kwargs):
        return _FakeResult(
            [
                {
                    "date": datetime(2026, 3, 3, tzinfo=timezone.utc),
                    "open": 100.0,
                    "high": 110.0,
                    "low": 90.0,
                    "close": 105.0,
                    "volume": 1000.0,
                }
            ]
        )


class _FakeEquityApi:
    def __init__(self):
        self.price = _FakePriceApi()


class _FakeObb:
    def __init__(self):
        self.equity = _FakeEquityApi()


def test_fetch_quotes_raises_when_openbb_unavailable(monkeypatch):
    monkeypatch.setattr(openbb_adapter, "obb", None)

    with pytest.raises(openbb_adapter.ProviderUnavailableError):
        openbb_adapter.fetch_quotes(["AAPL"])


def test_fetch_quotes_parses_rows(monkeypatch):
    monkeypatch.setattr(openbb_adapter, "obb", _FakeObb())

    rows = openbb_adapter.fetch_quotes(["AAPL"], provider="yfinance")

    assert len(rows) == 1
    assert rows[0]["symbol"] == "AAPL"
    assert rows[0]["provider"] == "yfinance"


def test_fetch_bars_parses_rows(monkeypatch):
    monkeypatch.setattr(openbb_adapter, "obb", _FakeObb())

    rows = openbb_adapter.fetch_bars(symbol="AAPL", interval="1d", lookback_days=30, provider="yfinance")

    assert len(rows) == 1
    assert rows[0]["symbol"] == "AAPL"
    assert rows[0]["interval"] == "1d"


def test_fetch_bars_rejects_unsupported_interval(monkeypatch):
    monkeypatch.setattr(openbb_adapter, "obb", _FakeObb())

    with pytest.raises(ValueError):
        openbb_adapter.fetch_bars(symbol="AAPL", interval="5m", lookback_days=30, provider="yfinance")
