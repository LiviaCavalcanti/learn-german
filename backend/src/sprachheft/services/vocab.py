"""Vocabulary retrieval, keyword search, and topic summaries.

Keyword search covers word/lemma/meaning/example. True semantic search over
learned words is a planned enhancement: add an embedding column + vector ranker
behind the same ``search_vocab`` interface (pluggable, e.g. via the LLM provider
or a local embeddings model) without changing callers.
"""

from __future__ import annotations

from collections import defaultdict

from sqlalchemy import func, or_
from sqlmodel import Session, select

from sprachheft.config import get_settings
from sprachheft.embeddings import cosine, embed_texts
from sprachheft.models import Material, SRState, VocabEmbedding, VocabItem
from sprachheft.schemas import (
    GenerationResult,
    GenVocab,
    VocabComposeIn,
    VocabItemCreate,
)


def list_vocab(
    session: Session,
    *,
    cefr: str | None = None,
    material_id: int | None = None,
    limit: int = 200,
    offset: int = 0,
) -> list[VocabItem]:
    stmt = select(VocabItem).order_by(VocabItem.created_at.desc())
    if cefr:
        stmt = stmt.where(VocabItem.cefr == cefr)
    if material_id is not None:
        stmt = stmt.where(VocabItem.material_id == material_id)
    stmt = stmt.offset(offset).limit(limit)
    return list(session.exec(stmt).all())


def search_vocab(
    session: Session,
    query: str,
    *,
    cefr: str | None = None,
    tag: str | None = None,
    limit: int = 100,
) -> list[VocabItem]:
    like = f"%{query.lower()}%"
    stmt = select(VocabItem).where(
        or_(
            func.lower(VocabItem.word).like(like),
            func.lower(VocabItem.lemma).like(like),
            func.lower(VocabItem.meaning_en).like(like),
            func.lower(func.coalesce(VocabItem.example_de, "")).like(like),
        )
    )
    if cefr:
        stmt = stmt.where(VocabItem.cefr == cefr)
    stmt = stmt.limit(limit * 3 if tag else limit)
    items = list(session.exec(stmt).all())
    if tag:
        items = [v for v in items if tag in (v.grammar_tags or [])]
    return items[:limit]


def topic_summary(session: Session) -> list[dict]:
    """Group learned words by grammar topic tag with counts and samples."""
    rows = session.exec(select(VocabItem)).all()
    buckets: dict[str, list[VocabItem]] = defaultdict(list)
    for item in rows:
        tags = item.grammar_tags or []
        if not tags:
            buckets["(untagged)"].append(item)
        for tag in tags:
            buckets[tag].append(item)

    summary: list[dict] = []
    for tag, items in sorted(buckets.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        summary.append(
            {
                "topic": tag,
                "count": len(items),
                "samples": [
                    {"word": i.word, "meaning_en": i.meaning_en} for i in items[:8]
                ],
            }
        )
    return summary


def create_vocab(session: Session, data: VocabItemCreate) -> VocabItem:
    item = VocabItem(
        material_id=data.material_id,
        word=data.word,
        lemma=(data.lemma or data.word),
        pos=data.pos,
        meaning_en=data.meaning_en,
        cefr=data.cefr,
        example_de=data.example_de,
        example_en=data.example_en,
        grammar_tags=data.grammar_tags,
    )
    session.add(item)
    session.flush()
    session.add(SRState(item_type="vocab", item_id=item.id))
    session.commit()
    session.refresh(item)
    return item


def compose_material(session: Session, data: VocabComposeIn) -> dict:
    """Generate a German text + exercises from selected words and save it.

    The result is a normal ``Material`` (so it appears in the library, practice,
    and review): the composed text becomes the transcript, the composed exercises
    are persisted, and the selected words are saved as the material's vocabulary.
    """
    from sprachheft.agents.composer import compose
    from sprachheft.services.generation import persist_result

    items: list[VocabItem] = []
    seen: set[int] = set()
    for vocab_id in data.vocab_ids:
        if vocab_id in seen:
            continue
        seen.add(vocab_id)
        item = session.get(VocabItem, vocab_id)
        if item is not None:
            items.append(item)
    if not items:
        raise ValueError("Select at least one vocabulary word.")

    settings = get_settings()
    level = data.level or items[0].cefr or settings.default_level

    composed = compose(items, level, data.instructions)
    text = (composed.text or "").strip()
    if not text:
        raise ValueError(
            "Text generation returned nothing — is the language model configured?"
        )

    material = Material(
        title=data.title or composed.title or "Practice text",
        media_type="text",
        level=level,
        transcript=text,
        notes="Composed from vocabulary",
    )
    session.add(material)
    session.commit()
    session.refresh(material)

    result = GenerationResult(
        vocabulary=[
            GenVocab(
                word=v.word,
                lemma=v.lemma,
                pos=v.pos,
                meaning_en=v.meaning_en,
                cefr=v.cefr or level,
                example_de=v.example_de,
                example_en=v.example_en,
                grammar_tags=v.grammar_tags,
            )
            for v in items
        ],
        exercises=composed.exercises,
    )
    counts = persist_result(session, material, result, source="generated")
    return {"material_id": material.id, "title": material.title, **counts}


def reindex_embeddings(session: Session, *, only_missing: bool = True) -> int:
    vocab = list(session.exec(select(VocabItem)).all())
    existing: set[int] = set()
    if only_missing:
        existing = {row.vocab_id for row in session.exec(select(VocabEmbedding)).all()}
    todo = [v for v in vocab if v.id not in existing]
    if not todo:
        return 0
    texts = [f"{v.word} {v.meaning_en} {v.example_de or ''}".strip() for v in todo]
    vectors = embed_texts(texts)
    for item, vector in zip(todo, vectors, strict=False):
        row = session.get(VocabEmbedding, item.id)
        if row:
            row.vector = vector
            row.dim = len(vector)
            session.add(row)
        else:
            session.add(VocabEmbedding(vocab_id=item.id, vector=vector, dim=len(vector)))
    session.commit()
    return len(todo)


def semantic_search(session: Session, query: str, *, limit: int = 20) -> list[VocabItem]:
    rows = list(session.exec(select(VocabEmbedding)).all())
    if not rows:
        return []
    query_vec = embed_texts([query])[0]
    vocab_by_id = {v.id: v for v in session.exec(select(VocabItem)).all()}
    scored: list[tuple[float, VocabItem]] = []
    for row in rows:
        item = vocab_by_id.get(row.vocab_id)
        if item is not None:
            scored.append((cosine(query_vec, row.vector), item))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [item for _score, item in scored[:limit]]
