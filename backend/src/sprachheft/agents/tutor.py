"""Tutor agent: a conversational German teacher backed by the LLM provider.

Two capabilities:
- ``chat`` — reply to the student in a personalised way, using their progress and
  profile, and observe what they struggle with / have mastered (to grow the profile).
- ``suggest_card`` — turn a teacher message into a concise review flashcard.
"""

from __future__ import annotations

from sprachheft.llm import get_llm_client
from sprachheft.models import ChatMessage
from sprachheft.schemas import ChatReply, TeacherCardSuggestion

TEACHER_SYSTEM_PROMPT = """You are Frau Wolf, a warm, patient, expert \
German-as-a-foreign-language (DaF) teacher having a one-on-one chat with a student. \
Teach conversationally, like a real chat.

How to reply:
- Keep replies focused and not too long. Ask a follow-up question or give a tiny task when \
it helps the student practise.
- Use German at the student's CEFR level, but explain grammar, rules and tricky points in \
clear English so they always understand. For A1-A2 keep the German simple and gloss new words.
- When the student makes a mistake, gently correct it and briefly explain the underlying rule \
with a short example.
- Personalise using the student's PROGRESS and PROFILE below: reinforce weak areas, build on \
what they already know, and don't overwhelm them.
- If a LEARNING ELEMENT (a material, word, or exercise) is attached, ground your answer in it.

Also quietly assess the student to help them over time. In addition to the reply, return:
- difficulties: concrete things the student seems to struggle with in THIS message (e.g. \
"dative after 'mit'", "adjective endings", "word order in subordinate clauses"). Empty if none.
- mastered: things the student clearly handled correctly in THIS message. Empty if none.
Keep both lists short (0-3 items) and specific."""


def _system_prompt(progress: str, profile: str, attached: str) -> str:
    parts = [TEACHER_SYSTEM_PROMPT]
    if profile.strip():
        parts.append("STUDENT PROFILE (what you've learned about them so far):\n" + profile.strip())
    if progress.strip():
        parts.append("STUDENT PROGRESS (from the app):\n" + progress.strip())
    if attached.strip():
        parts.append("ATTACHED LEARNING ELEMENT / CONTEXT:\n" + attached.strip())
    return "\n\n".join(parts)


def build_chat_messages(
    history: list[ChatMessage],
    new_message: str,
    *,
    progress: str = "",
    profile: str = "",
    attached: str = "",
) -> list[dict]:
    messages: list[dict] = [
        {"role": "system", "content": _system_prompt(progress, profile, attached)}
    ]
    for message in history:
        role = "assistant" if message.role == "teacher" else "user"
        messages.append({"role": role, "content": message.content})
    messages.append({"role": "user", "content": new_message})
    return messages


def chat(
    history: list[ChatMessage],
    new_message: str,
    *,
    progress: str = "",
    profile: str = "",
    attached: str = "",
) -> ChatReply:
    client = get_llm_client()
    messages = build_chat_messages(
        history, new_message, progress=progress, profile=profile, attached=attached
    )
    return client.generate_structured(messages, ChatReply)


CARD_SYSTEM_PROMPT = """You turn a German teacher's chat message into ONE concise \
spaced-repetition flashcard for the student to review later.

- front: a short prompt, question, or cue in German (or a word/phrase to recall) for the \
key point. Keep it short.
- back: the concise answer or explanation. Keep it short and correct; a brief German example \
is welcome.
- cefr: the CEFR level of the card (A1, A2, B1 or B2).
- tags: 0-3 lowercase grammar/topic tags (e.g. "dativ", "perfekt").

Pick the single most useful, self-contained learning point in the teacher's message. Use \
correct, natural German."""


def build_card_messages(text: str, context_text: str = "", level: str = "A2") -> list[dict]:
    user = f"LEVEL: {level}\n"
    if context_text.strip():
        user += f"CONTEXT:\n{context_text.strip()}\n"
    user += f"TEACHER_MESSAGE:\n{text.strip()}\n"
    return [
        {"role": "system", "content": CARD_SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]


def suggest_card(text: str, *, context_text: str = "", level: str = "A2") -> TeacherCardSuggestion:
    client = get_llm_client()
    messages = build_card_messages(text, context_text, level)
    return client.generate_structured(messages, TeacherCardSuggestion)
