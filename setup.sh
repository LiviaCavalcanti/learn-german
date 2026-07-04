#!/usr/bin/env bash
#
# Sprachheft — one-command setup (Linux / WSL / macOS)
# ====================================================
# Installs every dependency the app needs and (optionally) starts it:
#
#   * uv            — Python package/venv manager (installs Python 3.12 itself)
#   * backend deps  — FastAPI service + optional extras (llm, embeddings, ...)
#   * Node.js       — via nvm if available (frontend needs >= 20.19)
#   * frontend deps — npm ci (reproducible install)
#   * backend/.env  — created from .env.example if missing
#   * dictionary    — offline WikDict database (data/dict.sqlite)
#
# Usage:
#   ./setup.sh                 full install (recommended)
#   ./setup.sh --run           install, then start backend + frontend
#   ./setup.sh --minimal       backend base + dev only (skip llm/embeddings/phonetics)
#   ./setup.sh --with-transcribe   also install yt-dlp + faster-whisper (needs ffmpeg)
#   ./setup.sh --skip-dict     don't download/build the offline dictionary
#   ./setup.sh --help
#
# Safe to re-run: every step is idempotent.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

NODE_MIN_MAJOR=20
NODE_MIN_MINOR=19

# ── options ──────────────────────────────────────────────────────────────────
RUN=0
MINIMAL=0
WITH_TRANSCRIBE=0
SKIP_DICT=0

usage() {
  cat <<'EOF'
Sprachheft setup (Linux / WSL / macOS)

  ./setup.sh                    full install (recommended)
  ./setup.sh --run              install, then start backend + frontend
  ./setup.sh --minimal          backend base + dev only (skip llm/embeddings/phonetics)
  ./setup.sh --with-transcribe  also install yt-dlp + faster-whisper (needs ffmpeg)
  ./setup.sh --skip-dict        don't download/build the offline dictionary
  ./setup.sh --help
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --run)             RUN=1 ;;
    --minimal)         MINIMAL=1 ;;
    --with-transcribe) WITH_TRANSCRIBE=1 ;;
    --skip-dict)       SKIP_DICT=1 ;;
    -h|--help)         usage; exit 0 ;;
    *) printf 'Unknown option: %s\n\n' "$1" >&2; usage >&2; exit 2 ;;
  esac
  shift
done

# ── pretty logging ───────────────────────────────────────────────────────────
if [ -t 1 ] && [ -z "${NO_COLOR:-}" ]; then
  BOLD=$'\033[1m'; BLU=$'\033[34m'; GRN=$'\033[32m'; YLW=$'\033[33m'; RED=$'\033[31m'; RST=$'\033[0m'
else
  BOLD=; BLU=; GRN=; YLW=; RED=; RST=
fi
step() { printf '\n%s==>%s %s%s%s\n' "$BLU" "$RST" "$BOLD" "$*" "$RST"; }
info() { printf '     %s\n' "$*"; }
ok()   { printf '  %s[OK]%s %s\n' "$GRN" "$RST" "$*"; }
warn() { printf '  %s[!]%s  %s\n' "$YLW" "$RST" "$*" >&2; }
die()  { printf '\n  %s[x] %s%s\n' "$RED" "$*" "$RST" >&2; exit 1; }

trap 'die "Setup failed. See the messages above."' ERR

# ── 1. uv (Python toolchain) ─────────────────────────────────────────────────
ensure_uv() {
  if command -v uv >/dev/null 2>&1; then
    ok "uv $(uv --version 2>/dev/null | awk '{print $2}') found"
    return
  fi
  step "Installing uv (Python package manager)"
  if command -v curl >/dev/null 2>&1; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
  elif command -v wget >/dev/null 2>&1; then
    wget -qO- https://astral.sh/uv/install.sh | sh
  else
    die "Need curl or wget to install uv. Install one, or install uv manually: https://docs.astral.sh/uv/"
  fi
  export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
  command -v uv >/dev/null 2>&1 || die "uv installed but not on PATH — open a new shell and re-run."
  ok "uv installed"
}

# ── 2. backend dependencies ──────────────────────────────────────────────────
install_backend() {
  local extras=(dev)
  if [ "$MINIMAL" != "1" ]; then
    extras+=(llm embeddings phonetics)
  fi
  if [ "$WITH_TRANSCRIBE" = "1" ]; then
    extras+=(transcribe)
  fi

  local args=(sync)
  local e
  for e in "${extras[@]}"; do args+=(--extra "$e"); done

  step "Installing backend dependencies (uv ${args[*]})"
  info "uv will download Python 3.12 automatically if it is missing."
  ( cd "$ROOT/backend" && uv "${args[@]}" )
  ok "Backend ready (extras: ${extras[*]})"
}

# ── 3. Node.js (frontend runtime) ────────────────────────────────────────────
node_ok() {
  command -v node >/dev/null 2>&1 || return 1
  local v major rest minor
  v="$(node -v 2>/dev/null | sed 's/^v//')"
  major="${v%%.*}"; rest="${v#*.}"; minor="${rest%%.*}"
  [ "$major" -gt "$NODE_MIN_MAJOR" ] && return 0
  [ "$major" -eq "$NODE_MIN_MAJOR" ] && [ "$minor" -ge "$NODE_MIN_MINOR" ] && return 0
  return 1
}

ensure_node() {
  # Load nvm into this shell if it's installed.
  export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"
  if [ -s "$NVM_DIR/nvm.sh" ]; then
    # shellcheck disable=SC1091
    . "$NVM_DIR/nvm.sh"
    nvm use default >/dev/null 2>&1 || true
  fi

  if node_ok; then
    ok "Node $(node -v) found"
    return 0
  fi

  if command -v nvm >/dev/null 2>&1; then
    step "Installing Node.js 22 via nvm"
    if [ -f "$ROOT/frontend/.nvmrc" ]; then
      ( cd "$ROOT/frontend" && nvm install )
    else
      nvm install 22
    fi
    nvm use 22 >/dev/null 2>&1 || true
    node_ok && { ok "Node $(node -v) ready"; return 0; }
  fi

  warn "Node.js >= ${NODE_MIN_MAJOR}.${NODE_MIN_MINOR} not found — skipping frontend."
  info "Install nvm + Node, then re-run:"
  info "  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash"
  info "  nvm install 22"
  return 1
}

# ── 4. frontend dependencies ─────────────────────────────────────────────────
install_frontend() {
  step "Installing frontend dependencies (npm)"
  (
    cd "$ROOT/frontend"
    if [ -f package-lock.json ]; then
      npm ci || { warn "npm ci failed — falling back to npm install"; npm install; }
    else
      npm install
    fi
  )
  ok "Frontend ready"
}

# ── 5. configuration file ────────────────────────────────────────────────────
ensure_env() {
  step "Configuration (backend/.env)"
  if [ -f "$ROOT/backend/.env" ]; then
    info "backend/.env already exists — left untouched."
  else
    cp "$ROOT/backend/.env.example" "$ROOT/backend/.env"
    ok "Created backend/.env from .env.example (offline 'fake' LLM by default)."
  fi
}

# ── 6. offline dictionary ────────────────────────────────────────────────────
build_dictionary() {
  [ "$SKIP_DICT" = "1" ] && { info "Skipping dictionary build (--skip-dict)."; return; }
  if [ -f "$ROOT/data/dict.sqlite" ]; then
    ok "Offline dictionary already built (data/dict.sqlite)."
    return
  fi
  step "Building offline dictionary (WikDict, ~25 MB download, CC BY-SA)"
  if ! ( cd "$ROOT/backend" && uv run python -m sprachheft.dictionary.loader ); then
    warn "Dictionary build failed (offline?). Re-run later:"
    info "  cd backend && uv run python -m sprachheft.dictionary.loader"
  else
    ok "Dictionary built."
  fi
}

# ── optional: start the app ──────────────────────────────────────────────────
run_app() {
  trap - ERR
  step "Starting Sprachheft"
  local pids=()
  _cleanup() { echo; echo "Stopping..."; for p in "${pids[@]:-}"; do kill "$p" 2>/dev/null || true; done; }
  trap _cleanup EXIT INT TERM
  ( cd "$ROOT/backend" && uv run python main.py ) & pids+=($!)
  ( cd "$ROOT/frontend" && npm run dev ) & pids+=($!)
  echo "  Backend : http://127.0.0.1:8000/health"
  echo "  Frontend: http://localhost:5173"
  echo "  Press Ctrl+C to stop both."
  wait || true
}

# ── run ──────────────────────────────────────────────────────────────────────
printf '%s%sSprachheft setup%s  (%s)\n' "$BOLD" "$BLU" "$RST" "$ROOT"

ensure_uv
install_backend

FRONTEND_OK=0
if ensure_node; then
  install_frontend
  FRONTEND_OK=1
fi

ensure_env
build_dictionary

step "Setup complete"
info "Start the app:"
info "  ./setup.sh --run           (backend + frontend together)"
info "  cd backend  && uv run python main.py    → http://127.0.0.1:8000"
info "  cd frontend && npm run dev              → http://localhost:5173"
info "Configure the LLM and ports in backend/.env"
[ "$FRONTEND_OK" = "1" ] || warn "Frontend was skipped — install Node >= ${NODE_MIN_MAJOR}.${NODE_MIN_MINOR} and re-run."

if [ "$RUN" = "1" ]; then
  if [ "$FRONTEND_OK" = "1" ]; then
    run_app
  else
    die "Cannot --run without a working Node.js/frontend."
  fi
fi
