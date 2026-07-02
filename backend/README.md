# Sprachheft — backend

FastAPI backend for the German learning notebook: media capture, AI exercise
generation, spaced-repetition review, and an offline WikDict dictionary.

## Setup

```powershell
uv sync                 # base install
uv sync --extra llm     # + litellm/instructor for the generation agent
uv sync --extra dev     # + pytest/ruff
```

## Run

```powershell
uv run python main.py   # dev server with reload on http://127.0.0.1:8000
```

Health check: `GET http://127.0.0.1:8000/health`

## Dictionary

```powershell
uv run python -m sprachheft.dictionary.loader   # download + build data/dict.sqlite (WikDict, CC BY-SA)
```

## Configuration

Environment variables use the `SPRACHHEFT_` prefix (see `src/sprachheft/config.py`)
and can be placed in a `.env` file. Key settings: `SPRACHHEFT_LLM_MODEL`,
`SPRACHHEFT_LLM_API_BASE`, `SPRACHHEFT_DEFAULT_LEVEL`.
