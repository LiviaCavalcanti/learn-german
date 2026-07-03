"""Vocabulary API router: list, keyword search, and topic summaries."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from sprachheft.api.deps import SessionDep
from sprachheft.schemas import (
    VerbVocabIn,
    VerbVocabResult,
    VocabComposeIn,
    VocabComposeResult,
    VocabDeleteIn,
    VocabDeleteResult,
    VocabItemCreate,
    VocabItemRead,
)
from sprachheft.services import vocab as svc

router = APIRouter(prefix="/vocab", tags=["vocab"])


@router.post("", response_model=VocabItemRead, status_code=201)
def create_vocab(data: VocabItemCreate, session: SessionDep):
    return svc.create_vocab(session, data)


@router.post("/delete", response_model=VocabDeleteResult)
def delete_vocab(data: VocabDeleteIn, session: SessionDep):
    return {"deleted": svc.delete_vocab_items(session, data.ids)}


@router.post("/verb", response_model=VerbVocabResult)
def add_verb(data: VerbVocabIn, session: SessionDep):
    try:
        item, created = svc.add_verb(
            session,
            data.infinitive,
            english=data.english,
            partizip_ii=data.partizip_ii,
            auxiliary=data.auxiliary,
            cefr=data.cefr,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"created": created, "item": item}


@router.post("/compose", response_model=VocabComposeResult, status_code=201)
def compose_from_vocab(data: VocabComposeIn, session: SessionDep):
    try:
        return svc.compose_material(session, data)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


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
