# Engineering Standards

## Frontend standards (aligned with ~/web/midi-lab)

- Package manager: `bun` only.
- Lint/format tool: `Biome` only (no ESLint, no Prettier).
- TypeScript mode: `strict` enabled.
- Runtime/build: `Vite`.

### Frontend commands

From `apps/web`:

- `bun run dev`: start Vite dev server
- `bun run typecheck`: TypeScript static checks
- `bun run lint`: Biome checks
- `bun run format`: Biome auto-fix/format
- `bun run build`: production build
- `bun run test`: Vitest

### Frontend style policy

- Keep presentational components in `src/components`.
- Keep route-level pages in `src/pages`.
- Keep API client code in `src/lib`.
- Use single quotes and no semicolons (Biome formatter).
- New code must pass `bun run lint` and `bun run typecheck`.

## Python standards (for non-Python-first contributors)

- Environment manager: `uv`.
- Python version: `3.14` for local dev; package floor `>=3.11`.
- Quality gate: `ruff`, `mypy`, `pytest`.

### Python commands

From `apps/api`:

- `uv venv .venv314 --python 3.14`
- `source .venv314/bin/activate`
- `uv pip install -e '.[dev]'`
- `ruff check app tests`
- `mypy app`
- `pytest`

### Python coding policy

- Always add type hints for new functions.
- Keep side-effect code in services/repositories, not route handlers.
- Keep route handlers thin: validate input, call service, return schema.
- Add or update tests for behavior changes.
- Prefer small pure helper functions for parsing/normalization.
