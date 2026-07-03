"""Tutor (teacher chat) API: conversation, learner profile, and review cards."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from sprachheft.api.deps import SessionDep
from sprachheft.schemas import (
    CardSuggestIn,
    ChatMessageRead,
    ChatSendIn,
    ChatSessionCreate,
    ChatSessionDetail,
    ChatSessionRead,
    ChatTurnOut,
    LearnerProfileRead,
    ReviewCardCreate,
    ReviewCardCreated,
    TeacherCardSuggestion,
)
from sprachheft.services import tutor as svc

router = APIRouter(prefix="/tutor", tags=["tutor"])


@router.get("/sessions", response_model=list[ChatSessionRead])
def list_sessions(session: SessionDep):
    return svc.list_sessions(session)


@router.post("/sessions", response_model=ChatSessionRead, status_code=201)
def create_session(data: ChatSessionCreate, session: SessionDep):
    return svc.create_session(session, title=data.title, context=data.context)


@router.get("/sessions/{chat_id}", response_model=ChatSessionDetail)
def get_session(chat_id: int, session: SessionDep):
    chat = svc.get_session(session, chat_id)
    if chat is None:
        raise HTTPException(status_code=404, detail="Chat session not found")
    detail = ChatSessionDetail.model_validate(chat)
    detail.messages = [
        ChatMessageRead.model_validate(m) for m in svc.get_messages(session, chat_id)
    ]
    return detail


@router.delete("/sessions/{chat_id}", status_code=204)
def delete_session(chat_id: int, session: SessionDep):
    if not svc.delete_session(session, chat_id):
        raise HTTPException(status_code=404, detail="Chat session not found")


@router.post("/sessions/{chat_id}/messages", response_model=ChatTurnOut)
def send_message(chat_id: int, data: ChatSendIn, session: SessionDep):
    try:
        user_message, teacher_message = svc.send_message(
            session, chat_id, data.message, data.context
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ChatTurnOut(
        user_message=ChatMessageRead.model_validate(user_message),
        teacher_message=ChatMessageRead.model_validate(teacher_message),
    )


@router.get("/profile", response_model=LearnerProfileRead)
def get_profile(session: SessionDep):
    return svc.get_or_create_profile(session)


@router.post("/cards/suggest", response_model=TeacherCardSuggestion)
def suggest_card(data: CardSuggestIn, session: SessionDep):
    try:
        return svc.suggest_card(
            session, text=data.text, message_id=data.message_id, context=data.context
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/cards", response_model=ReviewCardCreated, status_code=201)
def create_card(data: ReviewCardCreate, session: SessionDep):
    try:
        exercise_id, srstate_id = svc.create_review_card(
            session, front=data.front, back=data.back, cefr=data.cefr, tags=data.tags
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ReviewCardCreated(exercise_id=exercise_id, srstate_id=srstate_id)
