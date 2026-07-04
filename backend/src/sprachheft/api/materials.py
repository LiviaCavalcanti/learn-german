"""Materials API router."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from sprachheft.api.deps import SessionDep
from sprachheft.schemas import (
    MaterialCreate,
    MaterialRead,
    MaterialSummary,
    MaterialUpdate,
    RewriteIn,
)
from sprachheft.services import materials as svc

router = APIRouter(prefix="/materials", tags=["materials"])


@router.post("", response_model=MaterialRead, status_code=201)
def create_material(data: MaterialCreate, session: SessionDep):
    try:
        return svc.create_material(session, data)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("", response_model=list[MaterialSummary])
def list_materials(session: SessionDep, lang: str | None = Query(None)):
    summaries: list[MaterialSummary] = []
    for material in svc.list_materials(session, lang):
        assert material.id is not None
        vocab_count, exercise_count = svc.counts_for(session, material.id)
        summaries.append(
            MaterialSummary(
                id=material.id,
                title=material.title,
                media_type=material.media_type,
                level=material.level,
                created_at=material.created_at,
                vocab_count=vocab_count,
                exercise_count=exercise_count,
            )
        )
    return summaries


@router.get("/{material_id}", response_model=MaterialRead)
def get_material(material_id: int, session: SessionDep):
    material = svc.get_material(session, material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    return material


@router.patch("/{material_id}", response_model=MaterialRead)
def update_material(material_id: int, data: MaterialUpdate, session: SessionDep):
    material = svc.update_material(session, material_id, data)
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    return material


@router.delete("/{material_id}", status_code=204)
def delete_material(material_id: int, session: SessionDep):
    if not svc.delete_material(session, material_id):
        raise HTTPException(status_code=404, detail="Material not found")


@router.post("/{material_id}/generate")
def generate_material(
    material_id: int,
    session: SessionDep,
    stage: int = Query(2, ge=1, le=4),
    section: str | None = Query(None, pattern="^(vocab|exercises)$"),
    batch: int = Query(0, ge=0),
):
    material = svc.get_material(session, material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    from sprachheft.services import generation

    if section == "vocab":
        return generation.generate_vocab_section(session, material, stage)
    if section == "exercises":
        try:
            return generation.generate_exercises_section(session, material, stage, batch)
        except IndexError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
    return generation.generate_for_material(session, material, stage=stage)


@router.post("/{material_id}/rewrite", response_model=MaterialRead)
def rewrite_material(material_id: int, payload: RewriteIn, session: SessionDep):
    material = svc.get_material(session, material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    return svc.rewrite_material(
        session, material, payload.instructions, payload.target_lines
    )
