"""Reference data (grammar taxonomy) API router."""

from __future__ import annotations

from fastapi import APIRouter
from sqlmodel import select

from sprachheft.api.deps import SessionDep
from sprachheft.models import GrammarTopic
from sprachheft.schemas import GrammarTopicRead

router = APIRouter(prefix="/taxonomy", tags=["taxonomy"])


@router.get("/topics", response_model=list[GrammarTopicRead])
def list_topics(session: SessionDep, cefr: str | None = None):
    stmt = select(GrammarTopic).order_by(GrammarTopic.cefr, GrammarTopic.code)
    if cefr:
        stmt = stmt.where(GrammarTopic.cefr == cefr)
    return list(session.exec(stmt).all())
