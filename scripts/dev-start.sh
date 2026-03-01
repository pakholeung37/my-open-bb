#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_DIR="$ROOT_DIR/apps/api"
WEB_DIR="$ROOT_DIR/apps/web"

API_HOST="${API_HOST:-0.0.0.0}"
API_PORT="${API_PORT:-8000}"
WEB_HOST="${WEB_HOST:-0.0.0.0}"
WEB_PORT="${WEB_PORT:-5173}"

API_PID=""
WEB_PID=""

log() {
  printf '[dev-start] %s\n' "$*"
}

cleanup() {
  set +e
  if [[ -n "$WEB_PID" ]] && kill -0 "$WEB_PID" 2>/dev/null; then
    log "Stopping web (pid=$WEB_PID)"
    kill "$WEB_PID" 2>/dev/null
  fi
  if [[ -n "$API_PID" ]] && kill -0 "$API_PID" 2>/dev/null; then
    log "Stopping api (pid=$API_PID)"
    kill "$API_PID" 2>/dev/null
  fi
}

ensure_commands() {
  command -v bun >/dev/null 2>&1 || {
    log "bun is required but not found"
    exit 1
  }
  command -v uv >/dev/null 2>&1 || {
    log "uv is required but not found"
    exit 1
  }
}

ensure_api_env() {
  if [[ ! -x "$API_DIR/.venv314/bin/python" ]]; then
    log "Creating backend venv (.venv314) with Python 3.14"
    (cd "$API_DIR" && uv venv .venv314 --python 3.14)
  fi

  if [[ ! -x "$API_DIR/.venv314/bin/uvicorn" ]]; then
    log "Installing backend dependencies"
    (cd "$API_DIR" && source .venv314/bin/activate && uv pip install -e '.[dev]')
  fi
}

ensure_web_env() {
  if [[ ! -d "$WEB_DIR/node_modules" ]]; then
    log "Installing frontend dependencies with bun"
    (cd "$WEB_DIR" && bun install)
  fi
}

start_api() {
  log "Starting API on http://$API_HOST:$API_PORT"
  (
    cd "$API_DIR"
    source .venv314/bin/activate
    uvicorn app.main:app --host "$API_HOST" --port "$API_PORT"
  ) &
  API_PID=$!
}

start_web() {
  log "Starting Web on http://localhost:$WEB_PORT"
  (
    cd "$WEB_DIR"
    bun run dev --host "$WEB_HOST" --port "$WEB_PORT"
  ) &
  WEB_PID=$!
}

main() {
  trap cleanup EXIT INT TERM

  ensure_commands
  ensure_api_env
  ensure_web_env
  start_api
  start_web

  log "Services started"
  log "Web: http://localhost:$WEB_PORT"
  log "API: http://localhost:$API_PORT"
  log "Press Ctrl+C to stop"

  while true; do
    if ! kill -0 "$API_PID" 2>/dev/null; then
      wait "$API_PID" || true
      break
    fi
    if ! kill -0 "$WEB_PID" 2>/dev/null; then
      wait "$WEB_PID" || true
      break
    fi
    sleep 1
  done
}

main "$@"
