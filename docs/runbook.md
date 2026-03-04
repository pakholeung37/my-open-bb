# Runbook

## Startup

1. `cd infra`
2. `docker compose up --build`
3. Open `http://localhost:7000`

## Manual refresh

- Agent-first market refresh:
- `POST http://localhost:8000/api/v1/market/refresh`

Legacy refresh endpoint is still available:

- `POST http://localhost:8000/api/v1/refresh`

## Common checks

- API health: `GET /api/v1/health`
- Feed list: `GET /api/v1/feed?limit=20`
- Quotes: `GET /api/v1/market/quotes?symbols=AAPL,MSFT`
- Bars: `GET /api/v1/market/bars?symbol=AAPL&interval=1d&lookback_days=30`

## Troubleshooting

- If market endpoints return `503`, ensure backend is installed with OpenBB market extras (`uv pip install -e '.[dev,market]'`).
- If market endpoints return `502`, inspect upstream/provider connectivity and OpenBB logs.
- If feed data is empty, validate `configs/feeds.yaml` URLs.
- If containers restart, inspect logs with `docker compose logs api` and `docker compose logs web`.
