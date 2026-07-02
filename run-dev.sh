#!/usr/bin/env bash
# Sprachheft dev launcher (WSL / Ubuntu) — starts the FastAPI backend and the
# Vite frontend together in one terminal. Ctrl+C stops both.
#
#   bash .claude/run-dev.sh
#
# WSL equivalent of run-dev.ps1: uv comes from ~/.local/bin, Node/npm from nvm.

set -uo pipefail

# Workspace root = parent of this script's directory (.claude/).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"

# uv on PATH.
export PATH="$HOME/.local/bin:$PATH"

# Node/npm via nvm (default alias).
export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"
if [ -s "$NVM_DIR/nvm.sh" ]; then
  # shellcheck disable=SC1091
  . "$NVM_DIR/nvm.sh"
  nvm use default >/dev/null 2>&1 || true
fi

# Track child PIDs and stop both on exit / Ctrl+C.
pids=()
cleanup() {
  echo
  echo "Shutting down..."
  for pid in "${pids[@]}"; do
    kill "$pid" 2>/dev/null || true
  done
}
trap cleanup EXIT INT TERM

# Backend — FastAPI dev server on http://127.0.0.1:8000
( cd "$ROOT/backend" && uv run python main.py ) &
pids+=($!)

# Frontend — Vite dev server on http://localhost:5173
( cd "$ROOT/frontend" && npm run dev ) &
pids+=($!)

echo "Backend:  http://127.0.0.1:8000/health"
echo "Frontend: http://localhost:5173"
echo "First time only: run 'uv run python -m sprachheft.dictionary.loader' in backend to build the dictionary."
echo "Press Ctrl+C to stop both."

# Wait for either process to exit.
wait
