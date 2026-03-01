# Runbook

## Startup

1. `cd infra`
2. `docker compose up --build`
3. Open `http://localhost:5173`

## Manual refresh

- Trigger from UI button on Dashboard, or call:
- `POST http://localhost:8000/api/v1/refresh`

## Common checks

- API health: `GET /api/v1/health`
- Feed list: `GET /api/v1/feed?limit=20`
- Watchlist quotes: `GET /api/v1/market/watchlist`

## Troubleshooting

- If market data is empty, confirm OpenBB provider credentials and internet access.
- If feed data is empty, validate `configs/feeds.yaml` URLs.
- If containers restart, inspect logs with `docker compose logs api` and `docker compose logs web`.
