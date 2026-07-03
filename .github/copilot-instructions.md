# Copilot instructions — Sprachheft

Sprachheft is a local German-learning app: **FastAPI backend** (`backend/`, Python 3.12 +
`uv`) and a **React + Vite + TS + Tailwind v4 frontend** (`frontend/`, Node ≥ 20.19).
Full details: [`AGENTS.md`](../AGENTS.md).

## Environment (Ubuntu / WSL)
- Backend: `cd backend && uv sync --extra llm --extra embeddings --extra dev` then
  `uv run python main.py` (→ :8000). `ModuleNotFoundError: instructor` ⇒ install the `llm` extra.
- Frontend: Node ≥ 20.19 (`nvm install 22`); `cd frontend && npm install && npm run dev` (→ :5173).
- Never share `node_modules` or `.venv` between Windows and Linux — rebuild per-OS.

## Always keep green before finishing
- Backend: `uv run pytest -q` and `uv run ruff check src tests` (line-length 100).
- Frontend: `npm run build` (runs `tsc`).

## Backend rules
- Layered: **thin routers (`api/`) → `services/` → `models.py`/`db.py`**. Register new routers in `api/app.py`.
- Enum-like DB fields are stored as **plain `str`** and validated at the API with Pydantic `Literal`s (`schemas.py`). No SQLAlchemy `Enum` columns.
- JSON columns use `sa_column=Column(JSON)`. Timestamps use `models.utcnow()` (naive UTC).
- `init_db()` only creates missing tables (no migrations) — add a **new table**, don't `ALTER`.
- LLM calls go through `llm/` (`get_llm_client()`): `SPRACHHEFT_LLM_MODEL=fake` → offline
  `FakeLLMClient`; else litellm+instructor. Agent prompts in `agents/` mirror the `prompts/` pack —
  change both together when the exercise schema changes.

## Tests must be offline
`tests/conftest.py` forces a temp DB, `SPRACHHEFT_LLM_MODEL=fake`, the local embedder, and no
reminders. New tests must not require the network, a real LLM, or model/dictionary downloads.

## Frontend rules
- API via `lib/api.ts` (typed, `VITE_API_BASE`) + `lib/types.ts`. Pages in `features/`,
  shared UI in `components/ui.tsx`. New page = component + `<Route>` in `App.tsx` + nav in `Layout.tsx`.
- Keep the notebook aesthetic (tokens in `index.css` `@theme`; use `ui.tsx` primitives).
