from __future__ import annotations

from fastapi.testclient import TestClient

from app.dependencies import get_ingestion_service
from app.main import app
from app.services.openbb_adapter import ProviderUnavailableError, UpstreamFetchError


def test_market_quotes_endpoint_returns_data(monkeypatch):
    service = get_ingestion_service()

    def fake_get_quotes(symbols: list[str], force_refresh: bool = False) -> dict:
        assert symbols == ["AAPL", "MSFT"]
        assert force_refresh is False
        return {
            "provider": "yfinance",
            "fetched_at": "2026-03-04T00:00:00+00:00",
            "quotes": [
                {
                    "symbol": "AAPL",
                    "price": 200.0,
                    "change_percent": 1.2,
                    "volume": 1000.0,
                    "pe_ratio": 30.0,
                    "market_cap": 1000000.0,
                    "provider": "yfinance",
                    "fetched_at": "2026-03-04T00:00:00+00:00",
                }
            ],
        }

    monkeypatch.setattr(service, "get_quotes", fake_get_quotes)

    client = TestClient(app)
    response = client.get("/api/v1/market/quotes", params={"symbols": "AAPL,MSFT"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] == "yfinance"
    assert len(payload["quotes"]) == 1
    assert payload["quotes"][0]["symbol"] == "AAPL"


def test_market_quotes_endpoint_validates_empty_symbols():
    client = TestClient(app)
    response = client.get("/api/v1/market/quotes", params={"symbols": ""})

    assert response.status_code == 400


def test_market_quotes_endpoint_maps_provider_unavailable(monkeypatch):
    service = get_ingestion_service()

    def fake_get_quotes(symbols: list[str], force_refresh: bool = False) -> dict:
        raise ProviderUnavailableError("OpenBB is not available")

    monkeypatch.setattr(service, "get_quotes", fake_get_quotes)

    client = TestClient(app)
    response = client.get("/api/v1/market/quotes", params={"symbols": "AAPL"})

    assert response.status_code == 503


def test_market_bars_endpoint_maps_upstream_error(monkeypatch):
    service = get_ingestion_service()

    def fake_get_bars(symbol: str, interval: str, lookback_days: int, force_refresh: bool = False) -> dict:
        raise UpstreamFetchError("upstream failed")

    monkeypatch.setattr(service, "get_bars", fake_get_bars)

    client = TestClient(app)
    response = client.get(
        "/api/v1/market/bars",
        params={"symbol": "AAPL", "interval": "1d", "lookback_days": 30},
    )

    assert response.status_code == 502


def test_market_refresh_endpoint_returns_cooldown(monkeypatch):
    service = get_ingestion_service()

    def fake_refresh_market_manual(
        symbols: list[str] | None = None,
        include_bars: bool = True,
        intervals: list[str] | None = None,
        lookback_days: int | None = None,
    ) -> tuple[bool, dict]:
        return False, {"status": "cooldown", "message": "Retry after 10s"}

    monkeypatch.setattr(service, "refresh_market_manual", fake_refresh_market_manual)

    client = TestClient(app)
    response = client.post("/api/v1/market/refresh", json={"symbols": ["AAPL"]})

    assert response.status_code == 429
