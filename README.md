# Sprachheft

A local-first German learning notebook. Capture real media (video, podcast, or
plain text), let an AI agent turn it into CEFR-tagged vocabulary and exercises,
and keep it all in memory with daily spaced-repetition review — backed by an
offline German↔English dictionary.

Everything runs on your machine: your materials, your progress, and your
dictionary all live in a local SQLite database. Nothing is sent anywhere unless
you point it at a cloud LLM yourself.

> New to the method? Read the companion [Learner's Guide](LEARNING-GUIDE.md) —
> the "why" and "how" of going from A1 to B2 on your own.

---

## What it does

- **Library** — add German media (video / podcast / text) by pasting a transcript
  or a link. Each material stores its transcript, an optional translation, and
  your notes.
- **AI generation** — from a material, an agent extracts high-frequency
  vocabulary (lemmatized, POS- and CEFR-tagged) and generates grammar, vocab, and
  interpretation exercises with answer keys.
- **Vocabulary** — a searchable personal word list with semantic search, fed by
  the media you actually consume.
- **Daily review** — an [FSRS](https://github.com/open-spaced-repetition)
  scheduler surfaces the vocab and exercises that are due, weighting weak spots so
  you review at the right moment.
- **Course** — an A1→B2 grammar taxonomy you can work through lesson by lesson.
- **Import** — paste external grammar content or exercises (JSON) and merge them
  into your library, practice, and review.
- **Offline dictionary** — hover any German word for an instant
  [WikDict](https://www.wikdict.com/) definition, no network required.
- **Reminders** — an optional daily nudge to clear your review queue.

## Architecture

| Layer | Stack |
|---|---|
| **Backend** | Python 3.12 · FastAPI · SQLModel / SQLite · pydantic-settings · FSRS · APScheduler · [uv](https://docs.astral.sh/uv/) |
| **AI (optional)** | litellm + instructor — pluggable local (Ollama) or cloud (OpenAI, Anthropic, …) models with Pydantic-validated structured output |
| **Dictionary** | WikDict `de-en` (CC BY-SA 4.0), built into a local SQLite file |
| **Frontend** | React 19 · TypeScript · Vite · Tailwind CSS · React Router |

```
learning/
  backend/            FastAPI app (package: sprachheft)
    main.py           dev server launcher (uvicorn)
    src/sprachheft/   api · agents · llm · dictionary · srs · ingest · services
    tests/            pytest suite
  frontend/           React + Vite single-page app
    src/features/     dashboard · course · library · material · vocab · review · importer
  content/            course + taxonomy JSON (git-friendly backbone)
  data/               local SQLite databases (app + dictionary)
  run-dev.ps1         dev launcher (Windows PowerShell)
  .claude/run-dev.sh  dev launcher (WSL / Linux / macOS)
  LEARNING-GUIDE.md   the method: how to actually learn German with this app
```

---

## Prerequisites

- [**uv**](https://docs.astral.sh/uv/getting-started/installation/) (installs and
  manages Python 3.12 for the backend)
- [**Node.js**](https://nodejs.org/) 20+ and npm (for the frontend)

## Setup & run

The app has two parts — a backend API and a frontend UI. Run each in its own
terminal.

### 1. Backend (API — http://127.0.0.1:8000)

```powershell
cd backend
uv sync --extra llm      # base install + the AI generation agent (omit --extra llm for a lighter install)
uv run python main.py    # dev server with reload
```

Verify it's up: open http://127.0.0.1:8000/health, or the interactive API docs at
http://127.0.0.1:8000/docs.

### 2. Dictionary (first time only)

Download and build the offline WikDict database into `data/dict.sqlite`:

```shell
cd backend
uv run python -m sprachheft.dictionary.loader
```

### 3. Frontend (UI — http://localhost:5173)

```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 in your browser.

### One-command dev launcher

To start the backend and frontend together:

- **Windows:** `powershell -ExecutionPolicy Bypass -File .\run-dev.ps1`
- **WSL / Linux / macOS:** `bash ./run-dev.sh`

Both print the backend and frontend URLs and remind you to build the dictionary
on first run.

---

## Configuration

Backend settings use the `SPRACHHEFT_` prefix and can live in a `backend/.env`
file (see [backend/src/sprachheft/config.py](backend/src/sprachheft/config.py)).
Common options:

| Variable | Purpose | Default |
|---|---|---|
| `SPRACHHEFT_LLM_MODEL` | litellm model string, e.g. `ollama/llama3.1`, `gpt-4o-mini`, `claude-3-5-sonnet-latest` | `ollama/llama3.1` |
| `SPRACHHEFT_LLM_API_BASE` | Base URL for local providers (e.g. Ollama) | — |
| `SPRACHHEFT_LLM_API_KEY` | API key for a cloud provider | — |
| `SPRACHHEFT_DEFAULT_LEVEL` | Default CEFR level for new content | `A2` |
| `SPRACHHEFT_REMINDER_TIME` | Daily review reminder (local `HH:MM`) | `18:00` |

The frontend reads the backend URL from `VITE_API_BASE` (defaults to
`http://127.0.0.1:8000`).

> The AI generation agent needs the `llm` extra (`uv sync --extra llm`) and a
> configured model. Point `SPRACHHEFT_LLM_MODEL` at a local Ollama model to keep
> everything fully offline, or at a cloud model with an API key.

## Testing

```powershell
cd backend
uv sync --extra dev
uv run pytest        # test suite
uv run ruff check    # lint
```

```powershell
cd frontend
npm run lint         # oxlint
npm run build        # type-check + production build
```

## Optional extras

- **Transcription** (`uv sync --extra transcribe`) — yt-dlp + faster-whisper to
  auto-transcribe audio/video instead of pasting a transcript manually. Requires
  `ffmpeg` on your PATH.
- **Embeddings** (`uv sync --extra embeddings`) — fastembed for higher-quality
  semantic vocabulary search (falls back to a local hashing method otherwise).
