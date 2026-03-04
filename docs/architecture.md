# Architecture

## Runtime flow

1. Scheduler triggers every 5 minutes (if `APP_ENABLE_SCHEDULER=true`).
2. Feed ingestion pulls configured RSS sources, normalizes fields, and writes deduplicated items.
3. Market refresh fetches watchlist quotes and historical bars (`1h`, `1d`) through OpenBB with `provider=yfinance`.
4. Agent calls market endpoints for quotes/bars and can request force refresh.

## API endpoints

- `GET /api/v1/health`
- `GET /api/v1/feed`
- `GET /api/v1/market/quotes`
- `GET /api/v1/market/bars`
- `POST /api/v1/market/refresh`

Backward-compatible endpoints kept for existing UI:

- `GET /api/v1/market/watchlist`
- `GET /api/v1/assets/{symbol}`
- `POST /api/v1/refresh`

## Data stores

DuckDB tables:

- `feed_items`
- `market_quotes`
- `market_bars`
- `asset_overviews`
- `ingestion_runs`
