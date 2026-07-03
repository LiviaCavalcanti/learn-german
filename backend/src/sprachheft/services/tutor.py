"""Tutor (teacher chat) service.

Owns the conversation flow, builds a progress snapshot for the teacher, maintains
the evolving :class:`LearnerProfile`, and turns teacher messages into review cards.
"""

from __future__ import annotations

from collections import Counter

from sqlmodel import Session, select

from sprachheft.agents import tutor as tutor_agent
from sprachheft.config import get_settings
from sprachheft.models import (
    ChatMessage,
    ChatSession,
    Exercise,
    LearnerProfile,
    Material,
    SRState,
    VocabItem,
    utcnow,
)
from sprachheft.schemas import ChatContext, ChatReply, TeacherCardSuggestion

_MAX_PROFILE_ITEMS = 25
_HISTORY_LIMIT = 30


# --- Sessions ----------------------------------------------------------------
def create_session(
    session: Session, *, title: str | None = None, context: ChatContext | None = None
) -> ChatSession:
    ctx = context.model_dump() if context and context.kind != "none" else {}
    chat = ChatSession(title=(title or "Conversation").strip() or "Conversation", context=ctx)
    session.add(chat)
    session.commit()
    session.refresh(chat)
    return chat


def list_sessions(session: Session) -> list[ChatSession]:
    return list(
        session.exec(select(ChatSession).order_by(ChatSession.updated_at.desc())).all()
    )


def get_session(session: Session, chat_id: int) -> ChatSession | None:
    return session.get(ChatSession, chat_id)


def get_messages(session: Session, chat_id: int) -> list[ChatMessage]:
    return list(
        session.exec(
            select(ChatMessage)
            .where(ChatMessage.session_id == chat_id)
            .order_by(ChatMessage.created_at, ChatMessage.id)
        ).all()
    )


def delete_session(session: Session, chat_id: int) -> bool:
    chat = session.get(ChatSession, chat_id)
    if chat is None:
        return False
    for message in session.exec(
        select(ChatMessage).where(ChatMessage.session_id == chat_id)
    ).all():
        session.delete(message)
    session.delete(chat)
    session.commit()
    return True


# --- Learner profile ---------------------------------------------------------
def get_or_create_profile(session: Session) -> LearnerProfile:
    profile = session.exec(select(LearnerProfile).order_by(LearnerProfile.id)).first()
    if profile is None:
        profile = LearnerProfile()
        session.add(profile)
        session.commit()
        session.refresh(profile)
    return profile


def _merge(existing: list[str], new: list[str], *, drop: set[str]) -> list[str]:
    """Merge two lists case-insensitively, dropping keys in ``drop``, most-recent last."""
    out: list[str] = []
    seen: set[str] = set()
    for item in [*existing, *new]:
        value = (item or "").strip()
        key = value.lower()
        if not value or key in drop or key in seen:
            continue
        seen.add(key)
        out.append(value)
    return out[-_MAX_PROFILE_ITEMS:]


def update_profile(session: Session, reply: ChatReply) -> LearnerProfile:
    """Grow the profile from a chat turn: newly mastered items leave 'difficulties'."""
    profile = get_or_create_profile(session)
    mastered_keys = {m.strip().lower() for m in reply.mastered if m.strip()}
    difficulty_keys = {d.strip().lower() for d in reply.difficulties if d.strip()}
    profile.difficulties = _merge(profile.difficulties, reply.difficulties, drop=mastered_keys)
    profile.strengths = _merge(profile.strengths, reply.mastered, drop=difficulty_keys)
    profile.updated_at = utcnow()
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile


def _profile_text(profile: LearnerProfile) -> str:
    parts: list[str] = []
    if profile.summary:
        parts.append(profile.summary)
    if profile.focus:
        parts.append(f"Current focus: {profile.focus}")
    if profile.strengths:
        parts.append("Strengths: " + ", ".join(profile.strengths))
    if profile.difficulties:
        parts.append("Difficulties: " + ", ".join(profile.difficulties))
    return "\n".join(parts)


# --- Progress snapshot -------------------------------------------------------
def _difficulty_snapshot(session: Session, limit: int = 8) -> list[str]:
    states = session.exec(
        select(SRState).where(SRState.lapses > 0).order_by(SRState.lapses.desc()).limit(limit)
    ).all()
    out: list[str] = []
    for state in states:
        if state.item_type == "vocab":
            vocab = session.get(VocabItem, state.item_id)
            if vocab:
                out.append(f"{vocab.word} ({vocab.meaning_en}) — {state.lapses} lapse(s)")
        else:
            exercise = session.get(Exercise, state.item_id)
            if exercise:
                tags = ", ".join(exercise.grammar_tags or [])
                suffix = f" [{tags}]" if tags else ""
                out.append(f"{exercise.type}{suffix} — {state.lapses} lapse(s)")
    return out


def build_progress_context(session: Session) -> str:
    settings = get_settings()
    now = utcnow()
    total_vocab = len(session.exec(select(VocabItem.id)).all())
    total_exercises = len(session.exec(select(Exercise.id)).all())
    due_now = len(session.exec(select(SRState.id).where(SRState.due <= now)).all())
    recent_vocab = session.exec(
        select(VocabItem).order_by(VocabItem.created_at.desc()).limit(12)
    ).all()
    tag_counter: Counter[str] = Counter()
    for vocab in session.exec(select(VocabItem)).all():
        for tag in vocab.grammar_tags or []:
            tag_counter[tag] += 1
    recent_materials = session.exec(
        select(Material).order_by(Material.created_at.desc()).limit(5)
    ).all()
    difficulties = _difficulty_snapshot(session)

    lines = [
        f"Default level: {settings.default_level}",
        (
            f"Vocabulary learned: {total_vocab}; exercises practised: {total_exercises}; "
            f"due for review now: {due_now}."
        ),
    ]
    if recent_vocab:
        lines.append(
            "Recently learned words: "
            + ", ".join(f"{v.word} ({v.meaning_en})" for v in recent_vocab)
        )
    if tag_counter:
        lines.append(
            "Grammar topics seen: "
            + ", ".join(f"{tag} ×{count}" for tag, count in tag_counter.most_common(8))
        )
    if recent_materials:
        lines.append(
            "Recent materials: " + ", ".join(f"{m.title} ({m.level})" for m in recent_materials)
        )
    if difficulties:
        lines.append("Struggling with (most-lapsed cards): " + "; ".join(difficulties))
    return "\n".join(lines)


# --- Attached learning element -----------------------------------------------
def resolve_context(session: Session, context: ChatContext | None) -> str:
    if context is None or context.kind == "none":
        return ""
    if context.kind == "text":
        return (context.text or "").strip()
    if context.kind == "material" and context.id is not None:
        material = session.get(Material, context.id)
        if material:
            out = f"Material: {material.title} (level {material.level})\n{material.transcript}"
            if material.translation:
                out += f"\nTranslation:\n{material.translation}"
            return out
    if context.kind == "vocab" and context.id is not None:
        vocab = session.get(VocabItem, context.id)
        if vocab:
            example = f" — e.g. {vocab.example_de}" if vocab.example_de else ""
            return f"Word: {vocab.word} = {vocab.meaning_en}{example}"
    if context.kind == "exercise" and context.id is not None:
        exercise = session.get(Exercise, context.id)
        if exercise:
            return (
                f"Exercise ({exercise.type}): {exercise.instructions}\n"
                f"Content: {exercise.payload}"
            )
    return (context.text or "").strip()


# --- Conversation ------------------------------------------------------------
def send_message(
    session: Session,
    chat_id: int,
    message: str,
    context: ChatContext | None = None,
) -> tuple[ChatMessage, ChatMessage]:
    chat = session.get(ChatSession, chat_id)
    if chat is None:
        raise ValueError("Chat session not found")
    text = (message or "").strip()
    if not text:
        raise ValueError("Message is empty")

    if context is not None and context.kind != "none":
        chat.context = context.model_dump()

    history = get_messages(session, chat_id)[-_HISTORY_LIMIT:]

    user_message = ChatMessage(session_id=chat_id, role="user", content=text)
    session.add(user_message)

    active_context = context
    if (active_context is None or active_context.kind == "none") and chat.context:
        active_context = ChatContext.model_validate(chat.context)

    reply = tutor_agent.chat(
        history,
        text,
        progress=build_progress_context(session),
        profile=_profile_text(get_or_create_profile(session)),
        attached=resolve_context(session, active_context),
    )

    teacher_message = ChatMessage(
        session_id=chat_id, role="teacher", content=(reply.reply or "").strip() or "…"
    )
    session.add(teacher_message)
    chat.updated_at = utcnow()
    session.add(chat)
    session.commit()
    session.refresh(user_message)
    session.refresh(teacher_message)

    update_profile(session, reply)
    return user_message, teacher_message


# --- Review cards ------------------------------------------------------------
def suggest_card(
    session: Session,
    *,
    text: str = "",
    message_id: int | None = None,
    context: ChatContext | None = None,
) -> TeacherCardSuggestion:
    source_text = (text or "").strip()
    if not source_text and message_id is not None:
        message = session.get(ChatMessage, message_id)
        if message:
            source_text = message.content
    if not source_text:
        raise ValueError("No text to build a card from")
    return tutor_agent.suggest_card(
        source_text,
        context_text=resolve_context(session, context),
        level=get_settings().default_level,
    )


def create_review_card(
    session: Session,
    *,
    front: str,
    back: str,
    cefr: str | None = None,
    tags: list[str] | None = None,
) -> tuple[int, int]:
    """Persist a teacher flashcard as an exercise + SR state, returning their ids."""
    front = (front or "").strip()
    back = (back or "").strip()
    if not front or not back:
        raise ValueError("Both front and back are required")
    exercise = Exercise(
        material_id=None,
        source="chat",
        type="flashcard",
        cefr=cefr or get_settings().default_level,
        grammar_tags=list(tags or []),
        instructions=front,
        payload={"hints": []},
        answer_key={"model_answer": back},
    )
    session.add(exercise)
    session.flush()
    state = SRState(item_type="exercise", item_id=exercise.id)
    session.add(state)
    session.commit()
    session.refresh(exercise)
    session.refresh(state)
    return exercise.id, state.id
