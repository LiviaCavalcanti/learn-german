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

## Daily news importer

`scripts/daily_article.py` fetches a German news article, adds it as a material,
translates it (deep-translator / Google Translate), and generates questions — the
same pipeline as the **Library → Today's news** button, but runnable from the
command line or a scheduler. It talks to the running backend over HTTP.

Install the optional extra once:

```powershell
uv sync --extra daily      # feedparser + deep-translator + trafilatura
```

Then, with the backend running (`uv run python main.py`):

```powershell
uv run python scripts/daily_article.py               # newest easy-German article
uv run python scripts/daily_article.py --source dw --level B1
uv run python scripts/daily_article.py --feed-url <rss-url> --level A2
uv run python scripts/daily_article.py --dry-run     # fetch + preview, save nothing
```

Built-in sources: `nachrichtenleicht` (Einfache Sprache, ~A2) and `dw` (Deutsche
Welle news, ~B1). A JSON state file (`data/daily_article_state.json`) remembers
what was already imported, so each run picks the next unseen article. Run with
`--help` for every flag (`--stage`, `--no-generate`, `--no-translate`, `--force`, …).

Schedule it once a day:

- **cron** — `0 7 * * * cd /path/to/learning/backend && uv run python scripts/daily_article.py`
- **Windows Task Scheduler** — program `powershell`, arguments:
  `-NoProfile -Command "cd C:\path\to\learning\backend; uv run python scripts/daily_article.py"`

## Configuration

Environment variables use the `SPRACHHEFT_` prefix (see `src/sprachheft/config.py`)
and can be placed in a `.env` file. Key settings: `SPRACHHEFT_LLM_MODEL`,
`SPRACHHEFT_LLM_API_BASE`, `SPRACHHEFT_DEFAULT_LEVEL`.
