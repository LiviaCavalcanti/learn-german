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
    VocabItemUpdate,
)
from sprachheft.services import vocab as svc

router = APIRouter(prefix="/vocab", tags=["vocab"])


@router.post("", response_model=VocabItemRead, status_code=201)
def create_vocab(data: VocabItemCreate, session: SessionDep):
    return svc.create_vocab(session, data)


@router.post("/delete", response_model=VocabDeleteResult)
def delete_vocab(data: VocabDeleteIn, session: SessionDep):
    return {"deleted": svc.delete_vocab_items(session, data.ids)}


@router.patch("/{vocab_id}", response_model=VocabItemRead)
def update_vocab(vocab_id: int, data: VocabItemUpdate, session: SessionDep):
    item = svc.update_vocab(session, vocab_id, data)
    if item is None:
        raise HTTPException(status_code=404, detail="Vocab item not found")
    return item


@router.post("/{vocab_id}/replace", response_model=VocabItemRead)
def replace_vocab(
    vocab_id: int,
    session: SessionDep,
    direction: str = Query("easier", pattern="^(easier|harder)$"),
):
    """Regenerate a vocab word easier/harder ("too hard"/"too easy") and swap it in."""
    from sprachheft.models import VocabItem

    item = session.get(VocabItem, vocab_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Vocab item not found")
    try:
        return svc.replace_vocab(session, item, direction=direction)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


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
            target_lang=data.target_lang,
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
    lang: str | None = Query(None),
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    return svc.list_vocab(
        session, cefr=cefr, material_id=material_id, target_lang=lang, limit=limit, offset=offset
    )


@router.get("/search", response_model=list[VocabItemRead])
def search_vocab(
    session: SessionDep,
    q: str = Query(..., min_length=1),
    cefr: str | None = None,
    tag: str | None = None,
    lang: str | None = Query(None),
    semantic: bool = False,
    limit: int = Query(100, ge=1, le=500),
):
    if semantic:
        return svc.semantic_search(session, q, limit=limit)
    return svc.search_vocab(session, q, cefr=cefr, tag=tag, target_lang=lang, limit=limit)


@router.post("/reindex")
def reindex(session: SessionDep, rebuild: bool = False):
    return {"indexed": svc.reindex_embeddings(session, only_missing=not rebuild)}


@router.get("/topics")
def vocab_topics(session: SessionDep):
    return {"topics": svc.topic_summary(session)}
