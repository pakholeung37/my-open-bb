# API Service

FastAPI backend for the OpenBB personal information platform.

## Run locally (uv + Python 3.14)

```bash
uv venv .venv314 --python 3.14
source .venv314/bin/activate
uv pip install -e '.[dev,market]'
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Quality checks

```bash
source .venv314/bin/activate
ruff check app tests
mypy app
pytest
```

## Key endpoints

- `GET /api/v1/health`
- `GET /api/v1/feed`
- `GET /api/v1/market/quotes`
- `GET /api/v1/market/bars`
- `POST /api/v1/market/refresh`

Backward-compatible endpoints:

- `GET /api/v1/market/watchlist`
- `GET /api/v1/assets/{symbol}`
- `POST /api/v1/refresh`
