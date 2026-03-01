# OpenBB Personal Information Platform

MVP implementation of a personal information platform powered by OpenBB.

## Scope in this repository

- FastAPI backend with 5-minute scheduler
- SQLite persistence layer
- RSS feed ingestion and watchlist market snapshots
- React + Vite frontend with 3 pages
- Docker Compose local runtime

## Project structure

- `apps/api`: Backend API and ingestion jobs
- `apps/web`: Frontend dashboard
- `configs`: Watchlist and feed source configuration
- `infra`: Docker Compose setup
- `docs`: Architecture and runbook notes

## Run with Docker

```bash
cd infra
docker compose up --build
```

- Web: http://localhost:5173
- API docs: http://localhost:8000/docs

## Run without Docker

### One-command startup (recommended)

```bash
./scripts/dev-start.sh
```

This starts API (`:8000`) and web (`:5173`) together, and stops both on `Ctrl+C`.

### API

```bash
cd apps/api
uv venv .venv314 --python 3.14
source .venv314/bin/activate
uv pip install -e '.[dev]'
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Web

```bash
cd apps/web
bun install
bun run dev
bun run typecheck
bun run lint
```

Vite dev server proxies `/api/*` requests to `http://127.0.0.1:8000` by default.
Set `VITE_PROXY_TARGET` if your API runs on a different host.

## Configuration

- `configs/watchlist.yaml`: tracked watchlist symbols
- `configs/feeds.yaml`: RSS/news feed sources
- `.env.example`: environment variable reference

## Notes

- If OpenBB credentials/providers are not configured, market quote refresh may return empty snapshots.
- Feed ingestion remains available and can be tested independently.
