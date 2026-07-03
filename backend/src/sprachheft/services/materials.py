"""Material persistence and retrieval."""

from __future__ import annotations

from sqlalchemy import func
from sqlmodel import Session, select

from sprachheft.ingest import IngestRequest, resolve
from sprachheft.languages import normalize_native, normalize_target
from sprachheft.models import Exercise, Material, VocabItem
from sprachheft.schemas import MaterialCreate


def create_material(session: Session, data: MaterialCreate) -> Material:
    result = resolve(
        IngestRequest(
            media_type=data.media_type,
            source_url=data.source_url,
            transcript=data.transcript,
            translation=data.translation,
        )
    )
    material = Material(
        title=data.title,
        media_type=data.media_type,
        source_url=result.source_url,
        source_lang=normalize_target(data.source_lang),
        native_lang=normalize_native(data.native_lang),
        level=data.level,
        transcript=result.transcript,
        translation=result.translation,
        notes=data.notes,
    )
    session.add(material)
    session.commit()
    session.refresh(material)
    return material


def rewrite_material(
    session: Session,
    material: Material,
    instructions: str | None,
    target_lines: int = 15,
) -> Material:
    from sprachheft.agents.rewriter import rewrite_text

    material.transcript = rewrite_text(material, instructions, target_lines)
    session.add(material)
    session.commit()
    session.refresh(material)
    return material


def list_materials(session: Session, lang: str | None = None) -> list[Material]:
    stmt = select(Material).order_by(Material.created_at.desc())
    if lang:
        stmt = stmt.where(Material.source_lang == lang)
    return list(session.exec(stmt).all())


def get_material(session: Session, material_id: int) -> Material | None:
    return session.get(Material, material_id)


def counts_for(session: Session, material_id: int) -> tuple[int, int]:
    vocab = session.exec(
        select(func.count(VocabItem.id)).where(VocabItem.material_id == material_id)
    ).one()
    exercises = session.exec(
        select(func.count(Exercise.id)).where(Exercise.material_id == material_id)
    ).one()
    return int(vocab), int(exercises)


def delete_material(session: Session, material_id: int) -> bool:
    material = session.get(Material, material_id)
    if not material:
        return False
    session.delete(material)
    session.commit()
    return True
