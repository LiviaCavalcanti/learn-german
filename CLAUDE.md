# CLAUDE.md

This repository's canonical agent guide is **[AGENTS.md](AGENTS.md)** — read it before
making any change. It covers the Ubuntu/WSL setup, the backend/frontend architecture,
conventions (enum-like fields stored as `str`; new table instead of `ALTER`; offline-only
tests via the fake LLM), the API surface, the LLM/embeddings configuration, and the common
gotchas. The user-facing overview is [README.md](README.md); the learning method is
[LEARNING-GUIDE.md](LEARNING-GUIDE.md).

Non-negotiables:

- Backend: `cd backend && uv sync --extra llm --extra embeddings --extra dev`;
  run `uv run python main.py`; keep `uv run pytest -q` and `uv run ruff check src tests` green.
- Frontend: Node ≥ 20.19 (`nvm install 22`); `npm run build` must pass (`tsc`).
- Never share `node_modules`/`.venv` across Windows and Linux.
- Tests must stay offline (`SPRACHHEFT_LLM_MODEL=fake`, local embedder, temp DB).
- Keep `agents/` prompts and the `prompts/` pack in sync with the exercise schema.
