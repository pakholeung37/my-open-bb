# AGENTS.md

This file defines execution standards for coding agents in this repository.

## 1. Stack and toolchain

- Frontend (`apps/web`): React + Vite + TypeScript + Bun + Biome.
- Backend (`apps/api`): FastAPI + DuckDB + uv-managed Python environment.
- Do not add ESLint or Prettier. Frontend lint/format is Biome-only.

## 2. Required checks before finishing work

### Frontend

Run in `apps/web`:

- `bun run typecheck`
- `bun run lint`
- `bun run test`
- `bun run build`

### Backend

Run in `apps/api` (with `.venv314` activated):

- `ruff check app tests`
- `mypy app`
- `pytest`

If a check cannot run, state exactly why.

## 3. Code organization rules

### Frontend

- `src/pages`: route-level pages only.
- `src/components`: reusable UI components.
- `src/lib`: API/network helpers.
- `src/types.ts`: shared DTO/types.

### Backend

- `app/api/v1`: HTTP route handlers only.
- `app/services`: business workflows.
- `app/repositories`: persistence/data access.
- `app/schemas.py`: request/response models.

## 4. Style and quality rules

- Keep functions focused and small.
- Prefer explicit types over `Any`.
- Avoid hidden side effects in utility functions.
- Add tests for every bug fix and feature behavior change.
- Keep public API behavior backward-compatible unless explicitly changing contract.

## 5. Runtime and startup

- One-command local startup from repo root:
  - `./scripts/dev-start.sh`
- This script starts backend (`:8000`) and frontend (`:7000`) together.

## 6. Dependency policy

- Frontend dependencies are managed by `bun` and `bun.lock`.
- Backend dependencies are declared in `apps/api/pyproject.toml`.
- Use stable releases unless a pre-release is explicitly required.

## 7. Documentation update rule

When changing architecture, standards, commands, or runtime behavior, update:

- `README.md`
- `docs/engineering-standards.md`
- This `AGENTS.md` when agent workflow expectations change.
