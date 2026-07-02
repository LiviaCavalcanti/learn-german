"""Import external material: prompt-pack JSON (deterministic) or raw text (LLM)."""

from __future__ import annotations

import json

from sqlmodel import Session

from sprachheft.config import get_settings
from sprachheft.models import ImportSource, Material
from sprachheft.schemas import GenerationResult, ImportJsonIn
from sprachheft.services.generation import persist_result


def import_json(session: Session, payload: ImportJsonIn) -> dict:
    settings = get_settings()
    material_data = payload.material or {}
    title = payload.title or material_data.get("title") or "Imported material"
    level = payload.level or material_data.get("level") or settings.default_level

    material = Material(
        title=title,
        media_type=material_data.get("media_type", "text"),
        source_url=material_data.get("source_url"),
        level=level,
        transcript=material_data.get("transcript") or "",
        notes="Imported (JSON)",
    )
    session.add(material)
    session.commit()
    session.refresh(material)

    result = GenerationResult(
        themes=material_data.get("themes", []),
        vocabulary=payload.vocabulary,
        exercises=payload.exercises,
    )
    counts = persist_result(session, material, result, source="imported")

    raw = {
        "material": material_data,
        "vocabulary": [v.model_dump() for v in payload.vocabulary],
        "exercises": [e.model_dump() for e in payload.exercises],
    }
    session.add(ImportSource(title=title, raw_text=json.dumps(raw, ensure_ascii=False)))
    session.commit()
    return {"material_id": material.id, **counts}


def import_text(
    session: Session,
    raw_text: str,
    *,
    level: str | None = None,
    title: str | None = None,
) -> dict:
    from sprachheft.agents.importer import normalize

    settings = get_settings()
    resolved_level = level or settings.default_level
    result = normalize(raw_text, resolved_level)

    material = Material(
        title=title or "Imported text",
        media_type="text",
        level=resolved_level,
        transcript=raw_text,
        notes="Imported (text)",
    )
    session.add(material)
    session.commit()
    session.refresh(material)

    counts = persist_result(session, material, result, source="imported")
    session.add(ImportSource(title=title or "Imported text", raw_text=raw_text))
    session.commit()
    return {"material_id": material.id, **counts}
