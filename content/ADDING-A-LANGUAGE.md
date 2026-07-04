# Adding a new language / course to Sprachheft

A step-by-step playbook for an AI agent (or developer) to add a new **target
language** — the language a learner studies — and author its course. Read
[`AGENTS.md`](../AGENTS.md) first for repo conventions; this file is the focused
how-to for language expansion.

The app is already fully **language-generic**: generation, feedback, conjugation,
dictionary lookup, phonetics and text-to-speech all thread a `lang` code through
and adapt from a single registry entry. To add a language you mostly **register a
profile** and **author content JSON** — you rarely write new Python/TSX logic.

---

## 0. Mental model

There are two independent axes:

- **Target language** — what the learner is studying (e.g. German `de`, Spanish
  `es`). Needs a registry entry **and** authored content.
- **Native language** — the explanation language that meanings, feedback and
  translations are written in (e.g. English `en`). Just a code + display name.

A target language becomes **visible in the app only once
`content/<code>/course.json` exists** (see `available_targets()` in
[`backend/src/sprachheft/languages.py`](../backend/src/sprachheft/languages.py)).
Registering a profile without content does nothing user-facing; authoring content
without a profile is ignored. You need **both**.

### What is automatic once a profile + content exist

- `GET /languages` lists it as a selectable target.
- `seed_taxonomy()` upserts its grammar topics into the `GrammarTopic` table on
  startup ([`seed.py`](../backend/src/sprachheft/seed.py)).
- The course API serves its levels/units/lessons; the onboarding picker shows it.
- Generation, feedback, conjugation, dictionary, IPA and TTS all adapt via the
  profile — no per-language code needed.

---

## 1. TL;DR checklist

| # | Where | What | Required? |
|---|-------|------|-----------|
| 1 | `backend/src/sprachheft/languages.py` | Add a `LanguageProfile` to `LANGUAGES` (and optionally `NATIVE_LANGUAGES`). | **Yes** |
| 2 | `frontend/src/components/Flag.tsx` | Add an inline-SVG flag keyed by the code. | **Yes** (else no flag renders) |
| 3 | `content/<code>/taxonomy.json` | CEFR levels + grammar-topic list (namespaced codes). | **Yes** |
| 4 | `content/<code>/course.json` | The course: levels → units → lessons. | **Yes** (this is what makes the language appear) |
| 5 | Offline dictionary (`data/dict.sqlite`) | Optional per-language WikDict build; falls back to a Google-Translate link. | Optional |
| 6 | Verify | Valid JSON, backend green, frontend build, restart backend, smoke-test. | **Yes** |

`fr` (French) and `it` (Italian) are **already registered** in `LANGUAGES` **and
already have flags** in `Flag.tsx`, but have **no content** yet — for those, skip
steps 1–2 and go straight to step 3 (author `taxonomy.json` + `course.json`).

---

## 2. Step 1 — Register the language profile

Edit [`backend/src/sprachheft/languages.py`](../backend/src/sprachheft/languages.py)
and add an entry to the `LANGUAGES` dict, keyed by the **ISO 639-1** code. Example
for Portuguese (`pt`):

```python
"pt": LanguageProfile(
    code="pt",
    name="Portuguese",              # English display name
    endonym="Português",            # native name shown in the picker
    level_framework="CEFR",
    levels=("A1", "A2", "B1", "B2"),
    voice="pt-PT",                  # BCP-47 hint for browser TTS (or "pt-BR")
    lemmatizer="pt",                # simplemma code, or "" if unsupported
    has_conjugation=True,
    content_dir="pt",               # sub-folder under content/
    article_note="For nouns, include the definite article o/a to mark gender.",
),
```

If the new language should also be usable as an **explanation language**, add it
to `NATIVE_LANGUAGES` too:

```python
NATIVE_LANGUAGES: dict[str, str] = {
    "en": "English",
    ...
    "pt": "Portuguese",
}
```

### What each profile field drives

| Field | Used by | Effect |
|-------|---------|--------|
| `code` | everywhere | the `lang` query param / DB `target_lang`; must be unique. |
| `name` | agent prompts (`generator`, `composer`, `feedback`, `conjugation`, …) | `"You are an expert {name} teacher …"`. |
| `endonym` | frontend picker | native label under the flag. |
| `level_framework`, `levels` | `/languages`, UI | proficiency scale + allowed level codes. |
| `voice` | `LanguageContext` → `setSpeechLang` | which browser voice reads words aloud. |
| `lemmatizer` | dictionary lookup + conjugation | simplemma language for lemma candidates / infinitive hints. `""` ⇒ surface form only. |
| `has_conjugation` | conjugation feature | whether the verb-table feature applies. |
| `content_dir` | course + taxonomy loaders + `available_targets` | sub-folder holding this language's JSON. |
| `article_note` | vocab/generation prompts | short instruction about noun gender/articles (`""` if the language has none). |

> Keep the profile **data-only**. The prompts already branch on `get_language(lang)`;
> only German has a bespoke conjugation prompt, everything else uses a generic one
> that asks the model for whatever tenses/persons the language uses.

---

## 3. Step 2 — Add the flag

Edit [`frontend/src/components/Flag.tsx`](../frontend/src/components/Flag.tsx) and
add an inline **SVG** flag to the `FLAGS` record, keyed by the code. **Do not use
emoji flags** (they don't render on Windows). Keep it simple — a few `<rect>`s:

```tsx
pt: (
  <svg viewBox="0 0 6 4" preserveAspectRatio="xMidYMid slice" className="h-full w-full">
    <rect width="6" height="4" fill="#DA291C" />
    <rect width="2.4" height="4" fill="#046A38" />
  </svg>
),
```

The caller sizes it via `className`; the SVG fills the box and is cropped with
`slice`, so any aspect ratio stays tidy.

---

## 4. Step 3 — Author `content/<code>/taxonomy.json`

The taxonomy is the **grammar backbone**: the CEFR levels plus the list of grammar
topics that lessons and generated/imported material get tagged against. It's
seeded into the `GrammarTopic` table on startup.

### Schema

```jsonc
{
  "version": 1,
  "title": "Portuguese A1–B2 taxonomy backbone",
  "note": "Short description of scope.",
  "levels": [
    { "code": "A1", "title": "Foundations",        "descriptor": "…CEFR can-do…" },
    { "code": "A2", "title": "Everyday Fluency",    "descriptor": "…" },
    { "code": "B1", "title": "Independent User",    "descriptor": "…" },
    { "code": "B2", "title": "Upper-Intermediate",  "descriptor": "…" }
  ],
  "conventions": {
    "articleShorthand": { "m": "o", "f": "a" },
    "exerciseTypes": ["fill-in-blank", "conjugation", "translation",
                      "multiple-choice", "reorder", "reading",
                      "interpretation", "writing"]
  },
  "grammarTopics": [
    { "code": "pt.a1.ser-estar", "cefr": "A1", "title": "ser & estar",
      "description": "The two verbs 'to be': permanent vs states/location." },
    { "code": "pt.a1.present-regular", "cefr": "A1", "title": "Present tense (regular)",
      "description": "Regular -ar/-er/-ir present conjugation." }
    // …one entry per grammar point, A1 → B2…
  ]
}
```

### Critical rule — namespace your topic codes

`GrammarTopic.code` is **globally unique across all languages** in the database.
German uses bare codes (`a1.sein-haben`) for historical reasons; **every new
language MUST prefix its codes with the language code** to avoid collisions:

- ✅ `pt.a1.ser-estar`, `pt.b1.subjunctive`
- ❌ `a1.ser-estar` (would collide with / overwrite another language's `a1.*`)

Spanish already follows this (`es.a1.*`) — copy that pattern. The `course.json`
lesson `grammar_topics` must reference these **exact** codes.

---

## 5. Step 4 — Author `content/<code>/course.json`

This is the curriculum: `levels[] → units[] → lessons[]`. Starting a lesson creates
a `Material` from the lesson's text so the generation agent (and the fixed drills)
can build practice.

### Two levels of richness

You can ship a course at either fidelity — pick per your goal:

**A) Lean lesson** (fastest; how Spanish `es` is authored). The learner presses
*Start*, a Material is created from `seed_text`, and the **LLM generates** vocab +
exercises on demand.

```jsonc
{
  "code": "pt.a1.ser-estar",
  "title": "ser & estar",
  "grammar_topics": ["pt.a1.ser-estar"],     // must exist in taxonomy.json
  "can_do": "I can introduce myself and say how I am.",
  "seed_text": "Olá, eu sou a Ana. Sou estudante e estou cansada, mas estou contente."
}
```

**B) Rich lesson** (how German `de` is authored). Adds a hand-written reading
`story`, comprehension `questions`, and fixed auto-graded `exercises`, so the
lesson has content **without needing the LLM**:

```jsonc
{
  "code": "pt.a1.ser-estar",
  "title": "ser & estar",
  "grammar_topics": ["pt.a1.ser-estar"],
  "can_do": "I can introduce myself and say how I am.",
  "seed_text": "Olá, eu sou a Ana …",        // 1–3 sentences; used as fallback transcript
  "intro": "In this lesson you'll learn …",   // English lesson intro (learner-facing)
  "story": "…a 500–700 word target-language reading text…",
  "questions": [
    { "prompt": "…target-language question…",
      "translation": "…native-language gloss…",
      "reference": "…model answer (stays server-side)…" }
  ],
  "exercises": [ /* see the exercise schema below */ ]
}
```

### Top-level structure

```jsonc
{
  "title": "Portuguese A1–B2 Course",
  "note": "Curriculum backbone …",
  "levels": [
    {
      "level": "A1",
      "title": "Foundations",
      "units": [
        { "unit": 1, "title": "Primeiros passos",
          "lessons": [ /* lesson objects */ ] }
      ]
    }
    // A2, B1, B2 …
  ]
}
```

### Lesson field reference

| Field | Type | Required | Purpose |
|-------|------|----------|---------|
| `code` | string | ✅ | Unique lesson id; conventionally a grammar-topic code. |
| `title` | string | ✅ | Lesson title. |
| `grammar_topics` | string[] | ✅ | Taxonomy codes this lesson drills (namespaced). |
| `can_do` | string | ✅ | CEFR-style can-do statement (English). |
| `seed_text` | string | ✅ | 1–3 target-language sentences; becomes the Material transcript if there's no `story`. |
| `intro` | string | optional | Learner-facing English intro. |
| `story` | string | optional | Long target-language reading text (see guidance). Overrides `seed_text` as the transcript. |
| `questions` | object[] | optional | Reading-comprehension questions over `story` (`prompt`, `translation`, `reference`). |
| `exercises` | object[] | optional | Fixed auto-graded drills shipped with the lesson. |

> The public `GET /course/lessons/{code}` endpoint **strips** each question's
> `reference` and the whole `exercises` array (exercises are delivered separately
> as gradable `Exercise` rows). So authored answer keys never leak to the client.

---

## 6. Content-authoring guidelines (text · levels · questions · exercises)

### Level (CEFR) calibration
Keep every lesson's language **inside its level**, introducing grammar only after
it's taught (respect the taxonomy order):

- **A1** — present tense, "to be"/"to have", articles, basic objects, simple
  questions, modals, basic past; short simple sentences; everyday topics.
- **A2** — datives/indirect objects, more prepositions, full past tense(s),
  comparatives, common subordinate clauses, reflexives; short connected texts.
- **B1** — adjective agreement/declension, relative & infinitive clauses,
  narration, conditional/subjunctive basics, passive intro; opinions & stories.
- **B2** — full passive, reported speech, participial/nominal style, advanced
  connectors; abstract/argumentative register.

### The `story` text
- **Length:** ~500–700 words for a rich A1 lesson (scale up gently by level).
- **Form:** several short paragraphs with **natural dialogue** (use the target
  language's quotation convention). Recycle the lesson's grammar and vocabulary
  heavily and concretely.
- **Content:** everyday, human, self-contained scenes (introductions, routines,
  shopping, a party, a class). Keep names/culture appropriate to the language.
  Optionally keep a light professional/tech flavour as German does.
- **Correctness:** native-quality, level-appropriate target language only — no
  mixed-language hybrids, no invented grammar. Proofread accents/diacritics.

### The `questions` (reading comprehension)
- 6–8 per rich lesson, answerable **from the story**, in order of appearance.
- `prompt` — the question in the **target** language.
- `translation` — a gloss in the **native** language (English by default).
- `reference` — a correct model answer in the target language (server-side only;
  used to grade the learner's free-text answer via the feedback agent).

### The `exercises` (fixed, auto-graded drills)
- ~5 per lesson, drilling **this** lesson's grammar and recycling its vocabulary.
- Use the **auto-graded** types for fixed drills: `fill-in-blank`, `conjugation`,
  `translation`, `multiple-choice`, `reorder`. (`reading`, `interpretation`,
  `writing` are open/LLM-graded — usually left to the generation agent.)
- **Every item needs an answer** in `answer_key`, aligned by index with
  `payload.items`.

### Exercise `payload` / `answer_key` contracts
(Same schema the import/generation pipeline uses — see
[`prompts/generate-exercises.prompt.md`](../prompts/generate-exercises.prompt.md).)

```jsonc
// fill-in-blank  (use ___ for the gap)
{ "type": "fill-in-blank", "instructions": "…",
  "payload": { "items": [ { "prompt": "Eu ___ estudante.", "hint": "ser" } ], "hints": [] },
  "answer_key": { "items": [ { "answer": "sou" } ] } }

// conjugation
{ "type": "conjugation", "instructions": "…",
  "payload": { "verb": "ser", "tense": "Presente", "items": [ { "person": "eu" } ] },
  "answer_key": { "items": [ { "answer": "sou" } ] } }

// translation  (direction: "en-de" style code, target/native)
{ "type": "translation", "instructions": "…",
  "payload": { "direction": "en-pt", "items": [ { "prompt": "I am ready." } ] },
  "answer_key": { "items": [ { "answer": "Estou pronto.", "accept": ["Estou pronta."] } ] } }

// multiple-choice
{ "type": "multiple-choice", "instructions": "…",
  "payload": { "items": [ { "prompt": "Eu ___ cansada.", "options": ["sou","estou","és"] } ], "hints": [] },
  "answer_key": { "items": [ { "answer": "estou", "explanation": "temporary state → estar" } ] } }

// reorder
{ "type": "reorder", "instructions": "…",
  "payload": { "items": [ { "tokens": ["sou","Eu","estudante"] } ], "hints": [] },
  "answer_key": { "items": [ { "answer": "Eu sou estudante" } ] } }

// reading  (open)
{ "type": "reading", "instructions": "…",
  "payload": { "text": "…", "questions": [ { "prompt": "…" } ] },
  "answer_key": { "questions": [ { "answer": "…" } ] } }

// interpretation  (open)
{ "type": "interpretation", "instructions": "…",
  "payload": { "prompt": "…", "guiding_points": ["…"] },
  "answer_key": { "sample_answer": "…", "rubric": ["…"] } }

// writing  (open)
{ "type": "writing", "instructions": "…",
  "payload": { "theme": "…", "task": "Escreve 5–7 frases sobre …",
               "target_length": "60–80 palavras", "useful_phrases": [], "checklist": [], "hints": [] },
  "answer_key": { "model_answer": "…", "rubric": ["…"] } }
```

---

## 7. Step 5 — Optional per-language features

These improve the experience but are **not required** to ship a course; each
degrades gracefully.

- **Offline dictionary** — hover-to-define uses `data/dict.sqlite`, built from a
  single WikDict pair (default `de-en`) via
  `uv run python -m sprachheft.dictionary.loader --pair <x>-en`. The current build
  holds one language's entries; for languages without a local dictionary, hover
  lookup **falls back to a Google-Translate link** (already `lang`-aware). Treat a
  bundled dictionary as optional/advanced.
- **Lemmatizer** — set `lemmatizer` to the [simplemma](https://github.com/adbar/simplemma)
  code so dictionary candidates and conjugation infinitive hints work. Empty ⇒
  surface-form only.
- **Conjugation** — just set `has_conjugation=True`; the generic prompt handles
  any language. Only add a bespoke prompt (like `GERMAN_SYSTEM_PROMPT` in
  [`agents/conjugation.py`](../backend/src/sprachheft/agents/conjugation.py)) if
  you want tighter control.
- **Phonetics / IPA** — `to_ipa(word, lang)` is espeak-based and language-aware;
  it returns `None` when the optional `phonetics` extra isn't installed.
- **TTS** — set `voice` to a BCP-47 tag the browser recognises.

---

## 8. Step 6 — Verify (keep it green)

1. **Valid JSON** — no trailing commas, double quotes only:
   ```bash
   python -m json.tool content/<code>/taxonomy.json > /dev/null
   python -m json.tool content/<code>/course.json  > /dev/null
   ```
2. **Codes line up** — every lesson `grammar_topics` entry exists in
   `taxonomy.json`, and all topic codes are language-prefixed & unique.
3. **Backend green** (from `backend/`):
   ```bash
   uv run pytest -q
   uv run ruff check src tests
   ```
4. **Frontend build** (from `frontend/`): `npm run build` (runs `tsc`).
5. **Restart the backend** — `get_course`/`_load` are `@lru_cache`d and taxonomy
   is seeded at startup, so changes to JSON or `languages.py` need a restart.
6. **Smoke-test**:
   - `GET /languages` includes your code under `targets`.
   - `GET /course?lang=<code>` returns your levels.
   - `GET /course/lessons/<code>?lang=<code>` returns a lesson (no `reference`/`exercises`).
   - The onboarding picker shows the new flag + endonym; selecting it loads the course.

---

## 9. Where languages are consumed (reference map)

| Concern | File |
|---------|------|
| Registry / profiles | `backend/src/sprachheft/languages.py` |
| `/languages` API | `backend/src/sprachheft/api/languages.py` |
| Taxonomy seeding | `backend/src/sprachheft/seed.py` |
| Course load/serve | `backend/src/sprachheft/services/course.py`, `api/course.py` |
| Generation / feedback / import / rewrite / conjugation prompts | `backend/src/sprachheft/agents/*.py` (all call `get_language`) |
| Dictionary lookup + lemmatize | `backend/src/sprachheft/dictionary/` |
| IPA | `backend/src/sprachheft/phonetics/` |
| Defaults (`default_target_lang`, `default_native_lang`) | `backend/src/sprachheft/config.py` |
| Language selection / picker | `frontend/src/contexts/LanguageContext.tsx`, `features/onboarding/LanguagePicker.tsx` |
| Flags | `frontend/src/components/Flag.tsx` |
| TTS voice wiring | `frontend/src/lib/pronunciation.ts` |

**Reference implementations:** German (`content/de/`) = full rich course; Spanish
(`content/es/`) = lean partial course. Copy whichever matches your goal.
