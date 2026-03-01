# Architecture

## Runtime flow

1. Scheduler triggers every 5 minutes.
2. Feed ingestion pulls configured RSS sources, normalizes fields, and writes deduplicated items.
3. Market refresh fetches watchlist quotes through OpenBB adapter and stores latest snapshots.
4. Frontend polls backend every 60 seconds and supports manual refresh.

## API endpoints

- `GET /api/v1/health`
- `GET /api/v1/feed`
- `GET /api/v1/market/watchlist`
- `GET /api/v1/assets/{symbol}`
- `POST /api/v1/refresh`

## Data stores

SQLite tables:

- `feed_items`
- `market_snapshots`
- `asset_overviews`
- `ingestion_runs`
