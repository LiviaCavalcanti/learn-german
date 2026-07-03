# AGENTS.md — Sprachheft

Guide for AI agents and developers working in this repository. Read this before making changes.

Sprachheft ("language notebook") is a **local German learning app**: collect media
(video/podcast/text), let an AI agent turn it into CEFR-tagged vocabulary + exercises,
practice with spaced repetition, look words up in an offline dictionary, and browse an
A1–B2 course. Everything runs locally.

---

## 1. TL;DR — the rules that matter most

- **Target dev environment is Ubuntu / WSL.** Do not mix Windows and Linux artifacts
  (`node_modules`, `.venv`) — native binaries differ and it breaks silently.
- **Backend:** Python 3.12 + [`uv`](https://docs.astral.sh/uv/). Generation needs the
  `llm` extra: `uv sync --extra llm --extra embeddings --extra dev`.
  (`ModuleNotFoundError: instructor` ⇒ the `llm` extra isn't installed.)
- **Frontend:** Node **≥ 20.19** (Vite 8). WSL's default Node 18 is too old
  (`CustomEvent is not defined`). Use `nvm install 22`.
- **Tests are offline-only.** They must never hit the network or a real LLM. `conftest.py`
  forces `SPRACHHEFT_LLM_MODEL=fake`, a temp DB, the local embedder, and no reminders.
- **After any change, keep it green:** `uv run pytest -q` and `uv run ruff check src tests`
  for the backend; `npm run build` (runs `tsc`) for the frontend.
- **Enum-like DB fields are stored as plain `str`**, validated at the API layer with Pydantic
  `Literal`s. Do not introduce SQLAlchemy `Enum` columns.
- The `prompts/` pack **mirrors** the generation agent's system prompt and the exercise
  JSON schema. If you change the exercise schema, update **both**.

---

## 2. Repository layout

```
learning/
  backend/            FastAPI service (Python, uv, src layout)
    pyproject.toml    deps + optional extras (llm, embeddings, transcribe, dev)
    main.py           uvicorn launcher (reload)
    src/sprachheft/   the package (see §5)
    tests/            pytest (offline; conftest sets fake LLM + temp DB)
    .env              runtime config (git-ignored; SPRACHHEFT_* keys)
  frontend/           React 19 + Vite + TS + Tailwind v4 SPA (see §9)
  content/            JSON content: taxonomy.json, course.json, content.json (legacy seed)
  prompts/            Model-agnostic LLM instruction pack (paste into Gemini/Claude/…)
  data/               SQLite DBs (git-ignored): app.sqlite, dict.sqlite, wikdict-*.sqlite3
  .claude/run-dev.sh  one-command dev launcher (Ubuntu / WSL / macOS)
  run-dev.ps1         one-command dev launcher (Windows)
  README.md           user-facing overview  ·  LEARNING-GUIDE.md  the learning method
```

---

## 3. Setup (Ubuntu / WSL)

The repo lives on the Windows drive; from WSL it's `/mnt/c/Users/<you>/code/learning`.

```bash
# --- Backend ---
curl -LsSf https://astral.sh/uv/install.sh | sh          # if uv is missing
cd backend
~/.local/bin/uv sync --extra llm --extra embeddings --extra dev

# --- Frontend --- (Node >= 20.19)
nvm install 22 && nvm use 22
cd ../frontend
npm install
```

> WSL gotcha: never reuse a `node_modules` or `.venv` created on Windows. If the build
> can't find `tsc`/esbuild/rollup binaries, delete `node_modules` and `npm install` again
> under Linux Node.

---

## 4. Run, build, test

| Task | Command (from the given dir) |
|------|------------------------------|
| Backend dev server | `backend$ uv run python main.py` → http://127.0.0.1:8000 |
| Frontend dev server | `frontend$ npm run dev` → http://localhost:5173 |
| Build offline dictionary (once) | `backend$ uv run python -m sprachheft.dictionary.loader` |
| Backend tests | `backend$ uv run pytest -q` |
| Backend lint (autofix) | `backend$ uv run ruff check --fix src tests` |
| Frontend typecheck + build | `frontend$ npm run build` (`tsc -b && vite build`) |

One-command dev launcher (starts both): `bash .claude/run-dev.sh` (Ubuntu) or
`powershell -ExecutionPolicy Bypass -File run-dev.ps1` (Windows).

Health check: `GET http://127.0.0.1:8000/health`. Interactive API docs: `/docs`.

---

## 5. Backend architecture (`src/sprachheft/`)

Layered: **routers (thin) → services (logic) → models/db**. LLM work lives in `agents/`
on top of a pluggable `llm/` provider.

| Module | Responsibility |
|--------|----------------|
| `config.py` | `Settings` (pydantic-settings, `SPRACHHEFT_` prefix). `env_file` is an **absolute** path to `backend/.env` so it loads regardless of CWD. |
| `db.py` | SQLModel engine/session; `init_db()` = `create_all` (no migrations). |
| `models.py` | SQLModel tables (§6). `utcnow()` = **naive UTC**. |
| `schemas.py` | Pydantic request/response models + shared `Literal` value types. |
| `api/` | FastAPI routers (one file per feature) + `deps.py` (`SessionDep`). Register new routers in `api/app.py`. |
| `services/` | Business logic (materials, generation, practice, review, imports, course, vocab, exercises). |
| `agents/` | LLM generators: `generator.py` (material → vocab+exercises), `rewriter.py` (expand/rewrite a transcript), `importer.py` (raw text → schema). Prompts here mirror `prompts/`. |
| `llm/` | Provider abstraction. `factory.get_llm_client()` → `FakeLLMClient` (offline) or `LiteLLMClient` (litellm + instructor). |
| `dictionary/` | Offline WikDict dictionary: `loader.py` (download+import), `service.py` (lookup), `lemmatize.py` (simplemma). |
| `embeddings/` | Semantic vocab search vectors: local hashing fallback or `fastembed:`/litellm model. |
| `srs/` | `scheduler.py` — thin wrapper over FSRS v6 (`Scheduler.review_card`). |
| `ingest/` | Ingestor seam: `manual.py` (paste) and `link.py` (yt-dlp + faster-whisper, optional). |
| `reminders/` | APScheduler daily "items due" job (disabled in tests). |
| `seed.py` | Loads `content/taxonomy.json` into `GrammarTopic` on startup. |

---

## 6. Data model (SQLite via SQLModel)

`Material`, `VocabItem`, `Exercise`, `SRState` (FSRS), `ReviewLog`, `StudySession`,
`ImportSource`, `GrammarTopic`, `VocabEmbedding`.

- **Enum-like fields** (`level`, `media_type`, exercise `type`, `source`, `item_type`,
  `rating`, `state`) are stored as **plain `str`**; validate at the API boundary with the
  `Literal`s in `schemas.py`.
- **JSON** fields use `sa_column=Column(JSON)` (e.g. `grammar_tags`, `payload`,
  `answer_key`, `fsrs_card`, `vector`).
- **Schema changes:** `init_db()` only *creates* missing tables. Add a **new table** rather
  than `ALTER`-ing an existing one (that's how `VocabEmbedding` was added).

**Exercise types (8):** `fill-in-blank`, `conjugation`, `translation`, `multiple-choice`,
`reorder`, `reading`, `interpretation`, `writing`. The first five are auto-graded
(`services/practice.py`); the rest are open (learner writes a response, reveal shows a model
answer).

---

## 7. API surface

| Area | Endpoints |
|------|-----------|
| Meta | `GET /health` |
| Materials | `POST /materials`, `GET /materials`, `GET /materials/{id}`, `DELETE /materials/{id}`, `POST /materials/{id}/generate?stage=1..4`, `POST /materials/{id}/rewrite` `{instructions, target_lines}` |
| Exercises | `GET /exercises?material_id&type&limit` |
| Vocab | `GET /vocab`, `POST /vocab`, `GET /vocab/search?q&cefr&tag&semantic`, `GET /vocab/topics`, `POST /vocab/reindex?rebuild` |
| Dictionary | `GET /dictionary/lookup?word&pos`, `GET /dictionary/status` |
| Taxonomy | `GET /taxonomy/topics?cefr` |
| Practice | `POST /practice/sessions`, `POST /practice/answer` |
| Review | `GET /review/queue?limit`, `GET /review/stats`, `POST /review/grade` |
| Imports | `POST /imports/json`, `POST /imports/text` |
| Course | `GET /course`, `GET /course/{level}`, `GET /course/lessons/{code}`, `POST /course/lessons/{code}/start` |
| Ingest | `GET /ingest/status`, `POST /ingest/transcribe` |

---

## 8. LLM, embeddings & content

- **Generation** (`/generate`, `/rewrite`, `/imports/text`) needs a model. Config via
  `SPRACHHEFT_LLM_MODEL`:
  - `fake` / empty → `FakeLLMClient` (deterministic, offline; used by tests).
  - `ollama/llama3.1` (+ `SPRACHHEFT_LLM_API_BASE=http://localhost:11434`) → local Ollama.
  - `gpt-4o-mini` / `claude-...` (+ `SPRACHHEFT_LLM_API_KEY`) → cloud.
  Requires the `llm` extra installed.
- **Semantic search** uses `SPRACHHEFT_EMBEDDING_MODEL`:
  - empty → local hashing embedder (offline, lexical).
  - `fastembed:sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` → local model
    (recommended; needs the `embeddings` extra). Avoid `jinaai/jina-embeddings-v2-base-de`
    — it fails on current onnxruntime.
  - Switching the embedding model changes vector dimensions ⇒ rebuild: `POST /vocab/reindex?rebuild=true`.
- **Content files:**
  - `content/taxonomy.json` — CEFR levels + grammar topics (seeded into `GrammarTopic`).
  - `content/course.json` — A1–B2 curriculum (4 levels × units × lessons; each lesson ties
    to a grammar topic and a seed text).
  - `content/content.json` — legacy A2 seed (kept for reference).
- **`prompts/`** — model-agnostic instruction pack that emits the same
  `material` / `vocabulary[]` / `exercises[]` JSON the `/imports/json` endpoint accepts.
  It **must stay in sync** with `agents/generator.py` and the exercise schema.

---

## 9. Frontend architecture (`frontend/src/`)

React 19 + Vite 8 + TypeScript + Tailwind v4 (`@tailwindcss/vite`) + react-router 7.
"Learning notebook" aesthetic (cream paper, serif headings, ruled-line panels).

| Path | Responsibility |
|------|----------------|
| `lib/api.ts` | Typed fetch client. Base URL from `VITE_API_BASE` (default `http://127.0.0.1:8000`). |
| `lib/types.ts` | Types mirroring API responses. |
| `components/ui.tsx` | Notebook-styled primitives (`Card`, `Button`, `Badge`, `Input`, `Textarea`, `Select`, `Field`, `Spinner`, `cx`). |
| `components/Layout.tsx` | Sidebar nav + `<Outlet/>`. |
| `components/HoverDictionary.tsx`, `TokenizedText.tsx` | Hover-to-define popover over German text. |
| `features/{dashboard,course,library,material,vocab,review,importer}/` | Pages. |
| `index.css` | Tailwind v4 `@theme` design tokens + base styles. |

**Adding a page:** create the component in `features/`, add a `<Route>` in `App.tsx`, a nav
entry in `components/Layout.tsx`, and any API method in `lib/api.ts` + type in `lib/types.ts`.

---

## 10. Conventions & gotchas

- **Style:** ruff (`line-length = 100`; rules `E,F,I,UP,B`; `B008` ignored for FastAPI
  `Depends`/`Query` defaults). Run `ruff check --fix` before finishing.
- **Timestamps:** always `models.utcnow()` (naive UTC) so SQLite comparisons stay consistent.
- **Routers:** thin — put logic in `services/`. Register in `api/app.py`.
- **Tests:** `tests/conftest.py` sets `SPRACHHEFT_DB_PATH` (temp), `SPRACHHEFT_LLM_MODEL=fake`,
  `SPRACHHEFT_ENABLE_REMINDERS=0`, `SPRACHHEFT_EMBEDDING_MODEL=""` via `setdefault`. New tests
  must stay offline. Some legacy test modules also set env at import time before importing the
  app — preserve that ordering.
- **Terminal env:** `uv` lives at `~/.local/bin`; add it to `PATH` or call it by full path.
  When scripting WSL from PowerShell, quote carefully (nested quotes break) and avoid
  `export PATH=$HOME/.local/bin:$PATH` (the interop PATH contains spaces).
- **Do not commit** `data/` or `.env` (already git-ignored). The WikDict data is CC BY-SA;
  keep the attribution noted in `dictionary/loader.py`.
- **Deferred/optional:** `transcribe` extra (yt-dlp + faster-whisper + ffmpeg) powers
  `/ingest/transcribe`; it returns `501` when unavailable — that is expected, not a bug.

---

## 11. Where to look first

- New endpoint → `api/<feature>.py` + `services/<feature>.py`, register in `api/app.py`.
- Change exercise generation → `agents/generator.py` **and** `prompts/generate-exercises.prompt.md`.
- Change the data model → `models.py` (+ `schemas.py`); remember: new table, not `ALTER`.
- Dictionary issues → `dictionary/` and rebuild `data/dict.sqlite` via the loader.
- Frontend behavior → `frontend/src/features/` + `lib/api.ts`.
