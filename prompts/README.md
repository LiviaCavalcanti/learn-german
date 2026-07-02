# Sprachheft — LLM instruction pack

Copy-paste prompts for generating study material in **any** chat interface
(Gemini, Claude, ChatGPT, local models). Everything they produce follows the
same JSON schema Sprachheft uses, so you can paste the output straight into the
app's **Import** view later, or just study from the readable worksheet.

## Files

| File | Use it to… |
|------|------------|
| [generate-exercises.prompt.md](generate-exercises.prompt.md) | Turn a transcript into CEFR-tagged vocabulary + exercises (incl. **writing** & **interpretation**). |
| [vocab-topic-summary.prompt.md](vocab-topic-summary.prompt.md) | Summarize / quiz the words you've already learned about a topic. |

## How to use

1. Open one of the prompt files and copy **everything below the `=== COPY BELOW ===` line**.
2. Paste it into your chat model.
3. Fill in the `INPUT` block (level, stage, transcript, …) and send.
4. Choose the output you want with `MODE`:
   - `MODE: JSON` → a single JSON object you can import into Sprachheft.
   - `MODE: WORKSHEET` → a printable study sheet with an answer key at the end.

## The two dials

- **LEVEL** (`A1`–`B2`) sets *how hard* the German is.
- **STAGE** (`1`–`4`) sets *how much help* you get, and **shrinks over time**:
  - `1` = just introduced → maximum hints, word banks, English support, lots of multiple-choice.
  - `2` = practising → partial hints.
  - `3` = confident → German instructions, at most a short tip.
  - `4` = consolidating → German only, **no hints**, free production, paraphrases accepted.

Raise the STAGE as a topic becomes familiar and the model automatically removes scaffolding.

## Article shorthand

Nouns are written with `r` / `e` / `s` = `der` / `die` / `das`
(e.g. `r Bahnhof`, `e Küche`, `s Büro`). Keep this convention in the output.

## Relationship to the app

- The `MODE: JSON` output matches Sprachheft's exercise schema exactly
  (`material`, `vocabulary[]`, `exercises[]`), so it's importable.
- In-app you also get **vocabulary search + topic summaries** (`/vocab/search`,
  `/vocab/topics`). Full **semantic search** over your learned words is a planned
  enhancement (pluggable embeddings) — these prompts complement it today.
