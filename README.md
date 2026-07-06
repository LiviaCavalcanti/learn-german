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
>
> Contributing or using an AI coding agent? See [AGENTS.md](AGENTS.md) for the
> architecture, conventions, and the Ubuntu/WSL developer workflow.

---

## What it does

- **Library** — add German media (video / podcast / text) by pasting a transcript
  or a link. Each material stores its transcript, an optional translation, and
  your notes.
- **Today's news** — one click fetches a current German article (easy-German
  *nachrichtenleicht* or Deutsche Welle), translates it, and turns it into
  vocabulary and exercises. Also available as a scheduled command-line script
  (see [backend/README.md](backend/README.md#daily-news-importer)).
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

## Quick start

One command installs every dependency (uv + Python 3.12, Node, and all backend
and frontend packages), creates `backend/.env`, and builds the offline
dictionary:

- **Windows** — double-click **`setup.bat`**, or from a terminal:

  ```powershell
  .\setup.bat            # install everything
  .\setup.bat -Run       # install, then start the app
  ```

- **WSL / Linux / macOS:**

  ```bash
  ./setup.sh             # install everything
  ./setup.sh --run       # install, then start the app
  ```

The scripts are idempotent, so they are safe to re-run. Add `--help` (`-Help` on
Windows) to see every option (`--minimal`, `--with-transcribe`, `--skip-dict`).
Prefer to set things up by hand? Follow the manual steps below.

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

Backend settings use the `SPRACHHEFT_` prefix and live in a `backend/.env` file.
The setup scripts create it from
[backend/.env.example](backend/.env.example) — which defaults to an offline
`fake` LLM so the app runs with no model configured. See
[backend/src/sprachheft/config.py](backend/src/sprachheft/config.py) for every
option. Common ones:

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

## Import study material from an AI chat

Already worked through some German with an AI — a grammar explanation, a
vocabulary list, a transcript you discussed? You can turn that conversation into
importable study material without a configured model. Paste the **anchor prompt**
below (with your conversation) into any chat model, then paste the JSON it returns
into the app's **Import → Prompt-pack JSON** tab (or `POST /imports/json`).

> Want full control over difficulty and scaffolding (LEVEL / STAGE dials, or a
> printable worksheet)? Use the fuller instruction pack in
> [prompts/](prompts/README.md) instead.

### The import JSON format

One object with a `material`, a `vocabulary[]` list, and an `exercises[]` list.
The material's `level` (`A1`–`B2`) sets the CEFR level for everything imported:

```json
{
  "material": {
    "title": "Ein Tag im Büro",
    "level": "A2",
    "media_type": "text",
    "source_url": null,
    "themes": ["Alltag", "Arbeit"],
    "transcript": "optional source text the material is based on"
  },
  "vocabulary": [
    {
      "word": "r Bahnhof",
      "lemma": "Bahnhof",
      "pos": "noun",
      "meaning_en": "train station",
      "cefr": "A2",
      "example_de": "Der Zug fährt vom Bahnhof ab.",
      "example_en": "The train departs from the station.",
      "grammar_tags": ["a2.dative"]
    }
  ],
  "exercises": [
    {
      "type": "fill-in-blank",
      "cefr": "A2",
      "grammar_tags": ["a2.dative"],
      "instructions": "Setze das richtige Artikelwort ein.",
      "payload": { "items": [{ "prompt": "Ich fahre mit ___ Bus.", "hint": "Dativ" }], "hints": [] },
      "answer_key": { "items": [{ "answer": "dem" }] }
    }
  ]
}
```

Each exercise `type` has its own `payload` / `answer_key` shape (answers align to
payload items **by index**):

- **fill-in-blank** — payload `{ "items": [{ "prompt": "… ___ …", "hint": "?" }] }` · key `{ "items": [{ "answer": "…" }] }`
- **conjugation** — payload `{ "verb": "gehen", "tense": "Präsens", "items": [{ "person": "ich" }] }` · key `{ "items": [{ "answer": "gehe" }] }`
- **translation** — payload `{ "direction": "en-de", "items": [{ "prompt": "…" }] }` · key `{ "items": [{ "answer": "…", "accept": ["…"] }] }`
- **multiple-choice** — payload `{ "items": [{ "prompt": "…", "options": ["…"] }] }` · key `{ "items": [{ "answer": "…", "explanation": "…" }] }` — `answer` must be exactly one of the `options`
- **reorder** — payload `{ "items": [{ "tokens": ["…"] }] }` · key `{ "items": [{ "answer": "…" }] }`
- **reading** — payload `{ "text": "…", "questions": [{ "prompt": "…" }] }` · key `{ "questions": [{ "answer": "…" }] }`
- **interpretation** — payload `{ "prompt": "…", "guiding_points": ["…"] }` · key `{ "sample_answer": "…", "rubric": ["…"] }`
- **writing** — payload `{ "theme": "…", "task": "…", "useful_phrases": ["…"], "checklist": ["…"] }` · key `{ "model_answer": "…", "rubric": ["…"] }`

The first five types are auto-graded during practice; `reading`,
`interpretation`, and `writing` reveal a model answer instead. Nouns use the
article shorthand `r` / `e` / `s` = der / die / das.

### Anchor prompt

Copy this, paste your conversation where marked, and send. The model returns a
single JSON object you can import as-is:

```text
You are an expert German-as-a-foreign-language (DaF) teacher and assessment
item-writer. Convert the German learning conversation / notes I provide into
Sprachheft study material.

Output ONLY one valid JSON object — no markdown fences, no commentary — with
exactly this shape:
{ "material": { … }, "vocabulary": [ … ], "exercises": [ … ] }

Rules:
- Choose a CEFR level (A1–B2) matching the German and set material.level; tag
  every item's "cefr".
- vocabulary: 8–15 useful items that actually appear in the conversation. Write
  nouns with the article shorthand r/e/s (der/die/das); include lemma, pos, a
  concise English meaning_en, and one short example (example_de + example_en).
- exercises: use ONLY these "type" values — fill-in-blank, conjugation,
  translation, multiple-choice, reorder, reading, interpretation, writing.
  Include a mix, with exactly one interpretation task and one writing task.
- Each "answer_key" aligns to its "payload" items by index. For multiple-choice,
  "answer" must be exactly one of the "options" strings.
- Valid JSON only: double quotes, no trailing commas, no comments, null for empty
  optionals.

Conversation / notes to convert:
<<<
(paste your AI conversation or notes here)
>>>
```

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
