"""Deterministic offline LLM client for tests and no-network development.

Derives a few plausible items from the transcript so the end-to-end generation
flow can be exercised without any model. Not a real generator.
"""

from __future__ import annotations

import random
import re

from sprachheft.schemas import (
    AnswerFeedback,
    ChatReply,
    ComposedText,
    ConjugationCell,
    ConjugationTable,
    ConjugationTense,
    ExerciseBatch,
    FeedbackError,
    GenerationResult,
    GenExercise,
    GenVocab,
    RewrittenText,
    TeacherCardSuggestion,
    VocabBatch,
)

_WORD_RE = re.compile(r"[A-Za-zÄÖÜäöüß]{4,}")
_STOP = {"heute", "eine", "einen", "meine", "meiner", "diese", "dieser", "haben", "sein"}


def _pick_words(text: str, n: int = 3) -> list[str]:
    picked: list[str] = []
    for match in _WORD_RE.findall(text or ""):
        if match.lower() in _STOP:
            continue
        if match.lower() not in {p.lower() for p in picked}:
            picked.append(match)
        if len(picked) >= n:
            break
    return picked


def _extract_field(text: str, key: str, default: str = "") -> str:
    """Read a ``KEY: value`` line from a formatted user message."""
    prefix = key.upper() + ":"
    for line in (text or "").splitlines():
        if line.strip().upper().startswith(prefix):
            return line.split(":", 1)[1].strip() or default
    return default


def _section(content: str, start: str, end: str | None = None) -> str:
    """Extract the text after ``start`` (up to ``end`` if given) from a message."""
    if start not in (content or ""):
        return ""
    tail = content.split(start, 1)[1]
    if end and end in tail:
        tail = tail.split(end, 1)[0]
    return tail.strip()


def _fake_verdict(answer: str, reference: str) -> tuple[str, float]:
    """Deterministic offline correctness estimate via token overlap with the reference."""
    if not (reference or "").strip():
        return ("partial", 0.5)

    def toks(text: str) -> set[str]:
        return {w for w in re.findall(r"[a-zäöüß]+", text.lower()) if len(w) > 2}

    ref = toks(reference)
    if not ref:
        return ("partial", 0.5)
    overlap = len(toks(answer) & ref) / len(ref)
    if overlap >= 0.6:
        return ("correct", 1.0)
    if overlap >= 0.25:
        return ("partial", 0.5)
    return ("incorrect", 0.0)


def _extract_words(text: str) -> list[str]:
    """Read the ``- word — meaning`` bullet list under a ``WORDS:`` header."""
    words: list[str] = []
    capturing = False
    for line in (text or "").splitlines():
        stripped = line.strip()
        if stripped.upper().startswith("WORDS:"):
            capturing = True
            continue
        if not capturing:
            continue
        if stripped.startswith("-"):
            token = stripped.lstrip("-").strip()
            for sep in ("—", " – ", " - "):
                if sep in token:
                    token = token.split(sep, 1)[0].strip()
                    break
            if token:
                words.append(token)
        elif stripped.upper().startswith(("INSTRUCTIONS:", "LEVEL:", "TITLE:")):
            break
    return words


_FILLERS = [
    "Außerdem finde ich das Thema sehr interessant.",
    "Meine Kollegen und ich sprechen oft darüber.",
    "Am Anfang war es schwierig, aber jetzt geht es besser.",
    "Jeden Tag lerne ich etwas Neues dazu.",
    "Das hilft mir sehr bei der Arbeit.",
    "Manchmal mache ich Fehler, aber das ist ganz normal.",
    "Später möchte ich noch mehr üben.",
    "Zum Schluss fasse ich alles kurz zusammen.",
]


def _expand_text(text: str, min_lines: int = 15) -> str:
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", (text or "").strip()) if s.strip()]
    if not sentences:
        sentences = ["Das ist ein kurzer Beispieltext auf Deutsch."]
    lines = list(sentences)
    i = 0
    while len(lines) < min_lines:
        lines.append(_FILLERS[i % len(_FILLERS)])
        i += 1
    return "\n".join(lines)


# --- Offline verb conjugation ------------------------------------------------
# A compact rule-based conjugator: correct for regular (weak) German verbs, with
# the three high-frequency irregular auxiliaries hard-coded. A real model gives
# full accuracy for strong/irregular verbs; this keeps offline mode usable. For
# non-German targets a minimal deterministic stub is returned instead.
_PERSON_LABELS = ("ich", "du", "er/sie/es", "wir", "ihr", "sie/Sie")
_WUERDE = ("würde", "würdest", "würde", "würden", "würdet", "würden")

_PRESENT_IRREGULAR = {
    "sein": ("bin", "bist", "ist", "sind", "seid", "sind"),
    "haben": ("habe", "hast", "hat", "haben", "habt", "haben"),
    "werden": ("werde", "wirst", "wird", "werden", "werdet", "werden"),
}
_PRAT_IRREGULAR = {
    "sein": ("war", "warst", "war", "waren", "wart", "waren"),
    "haben": ("hatte", "hattest", "hatte", "hatten", "hattet", "hatten"),
    "werden": ("wurde", "wurdest", "wurde", "wurden", "wurdet", "wurden"),
}
_KONJ2_IRREGULAR = {
    "sein": ("wäre", "wärst", "wäre", "wären", "wärt", "wären"),
    "haben": ("hätte", "hättest", "hätte", "hätten", "hättet", "hätten"),
    "werden": ("würde", "würdest", "würde", "würden", "würdet", "würden"),
}
_PARTIZIP_IRREGULAR = {"sein": "gewesen", "haben": "gehabt", "werden": "geworden"}
_IMPERATIVE_IRREGULAR = {
    "sein": ("sei", "seid", "seien Sie"),
    "haben": ("hab", "habt", "haben Sie"),
    "werden": ("werde", "werdet", "werden Sie"),
}
_AUXILIARY = {"sein": "sein", "werden": "sein"}
_INSEPARABLE_PREFIXES = ("be", "ge", "er", "ver", "zer", "ent", "emp", "miss")


def _verb_stem(inf: str) -> str:
    if inf.endswith("en"):
        return inf[:-2]
    if inf.endswith("n"):
        return inf[:-1]
    return inf


def _present_regular(inf: str) -> tuple[str, ...]:
    stem = _verb_stem(inf)
    e = "e" if stem.endswith(("d", "t")) else ""
    du = stem + ("est" if e else "st")
    return (stem + "e", du, stem + e + "t", inf, stem + e + "t", inf)


def _praeteritum_regular(inf: str) -> tuple[str, ...]:
    stem = _verb_stem(inf)
    e = "e" if stem.endswith(("d", "t")) else ""
    base = stem + e + "te"
    return (base, base + "st", base, base + "n", base + "t", base + "n")


def _partizip_regular(inf: str) -> str:
    stem = _verb_stem(inf)
    e = "e" if stem.endswith(("d", "t")) else ""
    if inf.endswith("ieren"):
        return stem + "t"
    if inf.startswith(_INSEPARABLE_PREFIXES):
        return stem + e + "t"
    return "ge" + stem + e + "t"


def _imperative_regular(inf: str) -> tuple[str, str, str]:
    stem = _verb_stem(inf)
    e = "e" if stem.endswith(("d", "t")) else ""
    return (stem + ("e" if e else ""), stem + e + "t", inf + " Sie")


def _tense(name: str, values: tuple[str, ...], note: str = "") -> ConjugationTense:
    """Build a tense from the six German personal forms."""
    return ConjugationTense(
        name=name,
        note=note,
        cells=[
            ConjugationCell(label=label, form=value)
            for label, value in zip(_PERSON_LABELS, values, strict=True)
        ],
    )


def _stub_conjugation(inf: str, lang: str) -> ConjugationTable:
    """A minimal deterministic table so offline tests exercise the flow.

    Used for non-German targets, where the app relies on a real model for
    accurate forms. The shape is valid; the forms are placeholders.
    """
    labels = ("1sg", "2sg", "3sg", "1pl", "2pl", "3pl")
    cells = [ConjugationCell(label=label, form=f"{inf}·{label}") for label in labels]
    return ConjugationTable(
        infinitive=inf,
        language=lang,
        english="",
        regular=True,
        notes="offline stub — connect a model for real forms",
        tenses=[ConjugationTense(name="Present", cells=cells)],
    )


def build_conjugation(inf: str, lang: str = "de") -> ConjugationTable:
    """Build a conjugation table for ``inf`` using regular rules + irregular tables."""
    inf = (inf or "").strip() or ("machen" if lang == "de" else "verb")
    if lang != "de":
        return _stub_conjugation(inf, lang)
    key = inf.lower()
    regular = key not in _PRESENT_IRREGULAR

    present = _PRESENT_IRREGULAR.get(key) or _present_regular(inf)
    praeteritum = _PRAT_IRREGULAR.get(key) or _praeteritum_regular(inf)
    partizip = _PARTIZIP_IRREGULAR.get(key) or _partizip_regular(inf)
    auxiliary = _AUXILIARY.get(key, "haben")
    imperative = _IMPERATIVE_IRREGULAR.get(key) or _imperative_regular(inf)

    aux_present = _PRESENT_IRREGULAR["sein" if auxiliary == "sein" else "haben"]
    werden_present = _PRESENT_IRREGULAR["werden"]
    perfekt = tuple(f"{aux_present[i]} {partizip}" for i in range(6))
    futur1 = tuple(f"{werden_present[i]} {inf}" for i in range(6))
    konjunktiv2 = _KONJ2_IRREGULAR.get(key) or tuple(f"{w} {inf}" for w in _WUERDE)

    return ConjugationTable(
        infinitive=inf,
        language="de",
        english="",
        regular=regular,
        auxiliary=auxiliary,
        partizip_ii=partizip,
        notes="" if regular else "irregular — connect a model for full accuracy",
        tenses=[
            _tense("Präsens", present),
            _tense("Präteritum", praeteritum),
            _tense("Perfekt", perfekt),
            _tense("Futur I", futur1),
            _tense("Konjunktiv II", konjunktiv2),
            ConjugationTense(
                name="Imperativ",
                cells=[
                    ConjugationCell(label="du", form=imperative[0]),
                    ConjugationCell(label="ihr", form=imperative[1]),
                    ConjugationCell(label="Sie", form=imperative[2]),
                ],
            ),
        ],
    )


class FakeLLMClient:
    def generate_structured(self, messages: list[dict], response_model, **kwargs):
        if response_model is AnswerFeedback:
            return self._fake_feedback(messages)

        if response_model is ChatReply:
            return self._fake_chat(messages)

        if response_model is TeacherCardSuggestion:
            return self._fake_card_suggestion(messages)

        transcript = ""
        for message in messages:
            if message.get("role") == "user":
                transcript = message.get("content", "")

        if response_model is ConjugationTable:
            return self._fake_conjugation(transcript)

        if response_model is RewrittenText:
            current = transcript
            if "CURRENT_TEXT:" in transcript:
                current = transcript.split("CURRENT_TEXT:", 1)[1].strip()
            return RewrittenText(text=_expand_text(current, 15))

        if response_model is ComposedText:
            return self._fake_composed(transcript)

        if response_model is GenExercise:
            return self._fake_single_exercise(transcript)

        if response_model is VocabBatch:
            return VocabBatch(vocabulary=self._fake_vocab(transcript))

        if response_model is ExerciseBatch:
            return ExerciseBatch(exercises=self._fake_exercise_batch(transcript))

        words = _pick_words(transcript) or ["Alltag", "lernen", "wichtig"]
        vocabulary = [
            GenVocab(
                word=word,
                lemma=word.lower(),
                pos="noun" if word[:1].isupper() else "verb",
                meaning_en=f"(meaning of {word})",
                cefr="A2",
                example_de=f"{word} kommt im Text vor.",
                example_en=f"{word} appears in the text.",
                grammar_tags=[],
            )
            for word in words[:3]
        ]
        first = words[0] if words else "Wort"
        exercises = [
            GenExercise(
                type="fill-in-blank",
                cefr="A2",
                grammar_tags=[],
                instructions="Setze das fehlende Wort ein.",
                payload={"items": [{"prompt": "Das ___ ist wichtig.", "hint": first}], "hints": []},
                answer_key={"items": [{"answer": first}]},
            ),
            GenExercise(
                type="writing",
                cefr="A2",
                grammar_tags=[],
                instructions="Schreibe ein paar Sätze zum Thema.",
                payload={
                    "theme": "Alltag",
                    "task": "Schreibe 3–5 Sätze über deinen Tag.",
                    "target_length": "40–60 Wörter",
                    "useful_phrases": [],
                    "checklist": ["Perfekt benutzen"],
                    "hints": [],
                },
                answer_key={
                    "model_answer": "Heute habe ich gearbeitet.",
                    "rubric": ["Thema getroffen"],
                },
            ),
        ]
        result = GenerationResult(themes=["Alltag"], vocabulary=vocabulary, exercises=exercises)
        if response_model is GenerationResult:
            return result
        return response_model.model_validate(result.model_dump())

    def _fake_composed(self, user_message: str) -> ComposedText:
        """Build a short text + exercises from the selected WORDS (offline)."""
        words = (
            _extract_words(user_message)
            or _pick_words(user_message)
            or ["Alltag", "lernen", "wichtig"]
        )
        level = _extract_field(user_message, "LEVEL", "A2")
        lines = ["Heute lerne ich einige neue Wörter auf Deutsch."]
        for word in words:
            lines.append(f"Das Wort {word} kommt in diesem Text vor.")
        lines.append("So kann ich die Wörter im Zusammenhang üben.")
        lines.append("Am Ende wiederhole ich alles noch einmal.")
        text = "\n".join(lines)

        first = words[0]
        joined = ", ".join(words)
        exercises = [
            GenExercise(
                type="fill-in-blank",
                cefr=level,
                instructions="Setze das passende Wort aus dem Text ein.",
                payload={
                    "items": [
                        {"prompt": "Das Wort ___ kommt in diesem Text vor.", "hint": first}
                    ],
                    "hints": [],
                },
                answer_key={"items": [{"answer": first}]},
            ),
            GenExercise(
                type="writing",
                cefr=level,
                instructions="Schreibe ein paar Sätze mit den neuen Wörtern.",
                payload={
                    "theme": "Wortschatz",
                    "task": f"Schreibe 3–5 Sätze und benutze: {joined}.",
                    "target_length": "40–60 Wörter",
                    "useful_phrases": [],
                    "checklist": ["Alle Wörter benutzen"],
                    "hints": [],
                },
                answer_key={
                    "model_answer": " ".join(f"Ich benutze das Wort {w}." for w in words),
                    "rubric": ["Alle Wörter benutzt"],
                },
            ),
        ]
        return ComposedText(
            title=f"Übung: {', '.join(words[:3])}", text=text, exercises=exercises
        )

    def _fake_single_exercise(self, user_message: str) -> GenExercise:
        """Build one plausible exercise of the requested TYPE (offline variant)."""
        ex_type = "fill-in-blank"
        for line in user_message.splitlines():
            if line.strip().upper().startswith("TYPE:"):
                ex_type = line.split(":", 1)[1].strip() or ex_type
                break
        transcript = user_message
        if "TRANSCRIPT:" in user_message:
            transcript = user_message.split("TRANSCRIPT:", 1)[1]
        return self._build_fake_exercise(ex_type, transcript)

    def _fake_vocab(self, user_message: str) -> list[GenVocab]:
        """Build a few plausible vocabulary items from the transcript (offline)."""
        transcript = user_message
        if "TRANSCRIPT:" in user_message:
            transcript = user_message.split("TRANSCRIPT:", 1)[1]
        words = _pick_words(transcript) or ["Alltag", "lernen", "wichtig"]
        return [
            GenVocab(
                word=word,
                lemma=word.lower(),
                pos="noun" if word[:1].isupper() else "verb",
                meaning_en=f"(meaning of {word})",
                cefr="A2",
                example_de=f"{word} kommt im Text vor.",
                example_en=f"{word} appears in the text.",
                grammar_tags=[],
            )
            for word in words[:8]
        ]

    def _fake_exercise_batch(self, user_message: str) -> list[GenExercise]:
        """Build one exercise per requested TYPE in the TYPES: line (offline)."""
        types: list[str] = []
        for line in user_message.splitlines():
            if line.strip().upper().startswith("TYPES:"):
                types = [t.strip() for t in line.split(":", 1)[1].split(",") if t.strip()]
                break
        if not types:
            types = ["fill-in-blank"]
        transcript = user_message
        if "TRANSCRIPT:" in user_message:
            transcript = user_message.split("TRANSCRIPT:", 1)[1]
        return [self._build_fake_exercise(t, transcript) for t in types]

    def _build_fake_exercise(self, ex_type: str, transcript: str) -> GenExercise:
        word = (_pick_words(transcript) or ["Alltag"])[0]

        if ex_type == "conjugation":
            verb, form, person = random.choice(
                [
                    ("arbeiten", "arbeite", "ich"),
                    ("gehen", "gehst", "du"),
                    ("machen", "macht", "er"),
                    ("lernen", "lernen", "wir"),
                ]
            )
            return GenExercise(
                type="conjugation",
                cefr="A2",
                instructions="Konjugiere das Verb in Klammern.",
                payload={
                    "items": [{"prompt": f"{person} ({verb}) heute.", "person": person}],
                    "hints": [],
                },
                answer_key={"items": [{"answer": form}]},
            )
        if ex_type == "translation":
            en, de = random.choice(
                [
                    ("I work in the office.", "Ich arbeite im Büro."),
                    ("She drinks coffee.", "Sie trinkt Kaffee."),
                    ("We write an email.", "Wir schreiben eine E-Mail."),
                ]
            )
            return GenExercise(
                type="translation",
                cefr="A2",
                instructions="Übersetze ins Deutsche.",
                payload={"items": [{"prompt": en}], "hints": []},
                answer_key={"items": [{"answer": de}]},
            )
        if ex_type == "multiple-choice":
            q = random.choice(
                [
                    {
                        "prompt": "Das ist ___ Büro.",
                        "options": ["ein", "eine", "einen"],
                        "answer": "ein",
                    },
                    {
                        "prompt": "Ich trinke ___ Kaffee.",
                        "options": ["ein", "einen", "eine"],
                        "answer": "einen",
                    },
                    {
                        "prompt": "Wir schreiben ___ E-Mail.",
                        "options": ["ein", "eine", "einen"],
                        "answer": "eine",
                    },
                ]
            )
            return GenExercise(
                type="multiple-choice",
                cefr="A2",
                instructions="Wähle die richtige Antwort.",
                payload={"items": [{"prompt": q["prompt"], "options": q["options"]}], "hints": []},
                answer_key={"items": [{"answer": q["answer"]}]},
            )
        if ex_type == "reorder":
            ordered, tokens = random.choice(
                [
                    ("Ich arbeite im Büro", ["im", "Ich", "Büro", "arbeite"]),
                    ("Sie trinkt gern Kaffee", ["Kaffee", "Sie", "gern", "trinkt"]),
                ]
            )
            return GenExercise(
                type="reorder",
                cefr="A2",
                instructions="Bringe die Wörter in die richtige Reihenfolge.",
                payload={"items": [{"tokens": tokens}], "hints": []},
                answer_key={"items": [{"answer": ordered}]},
            )
        if ex_type == "reading":
            return GenExercise(
                type="reading",
                cefr="A2",
                instructions="Lies den Text und beantworte die Frage.",
                payload={
                    "text": _expand_text(transcript, 6),
                    "questions": [{"prompt": "Worum geht es im Text?"}],
                    "hints": [],
                },
                answer_key={"items": [{"answer": "Um den Alltag und die Arbeit."}]},
            )
        if ex_type == "interpretation":
            return GenExercise(
                type="interpretation",
                cefr="A2",
                instructions="Interpretiere den Text.",
                payload={
                    "prompt": random.choice(
                        [
                            "Was denkst du über das Thema? Begründe deine Meinung.",
                            "Welche Absicht hat die Person im Text?",
                        ]
                    ),
                    "guiding_points": ["Nenne ein Beispiel aus dem Text.", "Gib deine Meinung."],
                    "hints": [],
                },
                answer_key={
                    "model_answer": "Ich denke, das Thema ist wichtig, weil ...",
                    "rubric": ["Meinung genannt"],
                },
            )
        if ex_type == "writing":
            return GenExercise(
                type="writing",
                cefr="A2",
                instructions="Schreibe einen kurzen Text.",
                payload={
                    "theme": random.choice(["Mein Arbeitstag", "Mein Wochenende", "Meine Pläne"]),
                    "task": "Schreibe 4–6 Sätze zum Thema.",
                    "target_length": "40–60 Wörter",
                    "useful_phrases": ["zuerst", "danach", "am Ende"],
                    "checklist": ["Perfekt benutzen", "Verbindungswörter benutzen"],
                    "hints": [],
                },
                answer_key={
                    "model_answer": "Heute habe ich viel gearbeitet.",
                    "rubric": ["Thema getroffen"],
                },
            )
        # default: fill-in-blank
        adj = random.choice(["wichtig", "neu", "interessant"])
        return GenExercise(
            type="fill-in-blank",
            cefr="A2",
            instructions="Setze das passende Wort ein.",
            payload={
                "items": [{"prompt": f"Im Text ist ___ {adj}.", "hint": word}],
                "hints": [],
            },
            answer_key={"items": [{"answer": word}]},
        )

    def _fake_conjugation(self, user_message: str) -> ConjugationTable:
        """Build a conjugation table offline from the VERB / INFINITIVE hint."""
        verb = ""
        infinitive = ""
        lang = "de"
        for line in user_message.splitlines():
            stripped = line.strip()
            upper = stripped.upper()
            if upper.startswith("VERB:"):
                verb = stripped.split(":", 1)[1].strip()
            elif upper.startswith("LANG:"):
                lang = (stripped.split(":", 1)[1].strip() or "de").lower()
            elif "INFINITIVE" in upper and ":" in stripped:
                infinitive = stripped.split(":", 1)[1].strip()
        return build_conjugation(infinitive or verb, lang)

    def _fake_feedback(self, messages: list[dict]) -> AnswerFeedback:
        content = ""
        for message in messages:
            if message.get("role") == "user":
                content = message.get("content", "")
        answer = _section(content, "STUDENT ANSWER:")
        reference = _section(content, "REFERENCE ANSWER:", "STUDENT ANSWER:")
        if not answer:
            return AnswerFeedback(
                has_errors=True,
                corrected="",
                errors=[
                    FeedbackError(
                        original="",
                        correction="",
                        explanation="No answer was provided to check.",
                    )
                ],
                summary="Please write an answer so it can be checked.",
                verdict="unanswered",
                score=0.0,
            )
        verdict, score = _fake_verdict(answer, reference)
        return AnswerFeedback(
            has_errors=False,
            corrected=answer,
            errors=[],
            summary=(
                "Offline check — connect a real model in Settings for detailed, "
                "reference-based feedback."
            ),
            verdict=verdict,
            score=score,
        )

    def _fake_chat(self, messages: list[dict]) -> ChatReply:
        """A deterministic offline teacher reply that echoes the student's message."""
        student = ""
        for message in messages:
            if message.get("role") == "user":
                student = message.get("content", "")
        student = (student or "").strip()
        snippet = student.splitlines()[0][:200] if student else ""
        reply = "Gern helfe ich dir! "
        if snippet:
            reply += f"Du hast geschrieben: „{snippet}“. "
        reply += (
            "Lass uns das Schritt für Schritt anschauen. Ein Beispiel: "
            "„Ich lerne jeden Tag ein bisschen Deutsch.“ Versuch, einen ähnlichen Satz zu "
            "bilden — ich korrigiere dich dann. (Offline-Modus: verbinde ein Sprachmodell "
            "für echte Antworten.)"
        )
        return ChatReply(reply=reply, difficulties=[], mastered=[])

    def _fake_card_suggestion(self, messages: list[dict]) -> TeacherCardSuggestion:
        """Split a teacher message into a plausible front/back flashcard (offline)."""
        user = ""
        for message in messages:
            if message.get("role") == "user":
                user = message.get("content", "")
        level = _extract_field(user, "LEVEL", "A2")
        text = user
        if "TEACHER_MESSAGE:" in user:
            text = user.split("TEACHER_MESSAGE:", 1)[1].strip()
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
        front = (sentences[0] if sentences else text[:60]) or "Neue Karte"
        back = " ".join(sentences[1:]).strip() or text.strip() or front
        return TeacherCardSuggestion(front=front[:200], back=back[:500], cefr=level, tags=[])
