"""Reference data (grammar taxonomy) API router."""

from __future__ import annotations

from fastapi import APIRouter, Query
from sqlmodel import select

from sprachheft.api.deps import SessionDep
from sprachheft.models import GrammarTopic
from sprachheft.schemas import GrammarTopicRead

router = APIRouter(prefix="/taxonomy", tags=["taxonomy"])


@router.get("/topics", response_model=list[GrammarTopicRead])
def list_topics(session: SessionDep, cefr: str | None = None, lang: str = Query("de")):
    stmt = select(GrammarTopic).where(GrammarTopic.target_lang == lang)
    if cefr:
        stmt = stmt.where(GrammarTopic.cefr == cefr)
    stmt = stmt.order_by(GrammarTopic.cefr, GrammarTopic.code)
    return list(session.exec(stmt).all())
