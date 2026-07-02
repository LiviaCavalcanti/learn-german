"""Vocabulary API router: list, keyword search, and topic summaries."""

from __future__ import annotations

from fastapi import APIRouter, Query

from sprachheft.api.deps import SessionDep
from sprachheft.schemas import VocabItemCreate, VocabItemRead
from sprachheft.services import vocab as svc

router = APIRouter(prefix="/vocab", tags=["vocab"])


@router.post("", response_model=VocabItemRead, status_code=201)
def create_vocab(data: VocabItemCreate, session: SessionDep):
    return svc.create_vocab(session, data)


@router.get("", response_model=list[VocabItemRead])
def list_vocab(
    session: SessionDep,
    cefr: str | None = None,
    material_id: int | None = None,
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    return svc.list_vocab(
        session, cefr=cefr, material_id=material_id, limit=limit, offset=offset
    )


@router.get("/search", response_model=list[VocabItemRead])
def search_vocab(
    session: SessionDep,
    q: str = Query(..., min_length=1),
    cefr: str | None = None,
    tag: str | None = None,
    semantic: bool = False,
    limit: int = Query(100, ge=1, le=500),
):
    if semantic:
        return svc.semantic_search(session, q, limit=limit)
    return svc.search_vocab(session, q, cefr=cefr, tag=tag, limit=limit)


@router.post("/reindex")
def reindex(session: SessionDep, rebuild: bool = False):
    return {"indexed": svc.reindex_embeddings(session, only_missing=not rebuild)}


@router.get("/topics")
def vocab_topics(session: SessionDep):
    return {"topics": svc.topic_summary(session)}
