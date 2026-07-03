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
from sprachheft.languages import normalize_target
from sprachheft.models import Material, ReviewLog, SRState, VocabEmbedding, VocabItem
from sprachheft.schemas import (
    GenerationResult,
    GenVocab,
    VocabComposeIn,
    VocabItemCreate,
    VocabItemUpdate,
)


def list_vocab(
    session: Session,
    *,
    cefr: str | None = None,
    material_id: int | None = None,
    target_lang: str | None = None,
    limit: int = 200,
    offset: int = 0,
) -> list[VocabItem]:
    stmt = select(VocabItem).order_by(VocabItem.created_at.desc())
    if cefr:
        stmt = stmt.where(VocabItem.cefr == cefr)
    if material_id is not None:
        stmt = stmt.where(VocabItem.material_id == material_id)
    if target_lang:
        stmt = stmt.where(VocabItem.target_lang == target_lang)
    stmt = stmt.offset(offset).limit(limit)
    return list(session.exec(stmt).all())


def search_vocab(
    session: Session,
    query: str,
    *,
    cefr: str | None = None,
    tag: str | None = None,
    target_lang: str | None = None,
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
    if target_lang:
        stmt = stmt.where(VocabItem.target_lang == target_lang)
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
        target_lang=normalize_target(data.target_lang),
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


def replace_vocab(session: Session, item: VocabItem, *, direction: str) -> VocabItem:
    """Regenerate a vocabulary item easier/harder and replace it in place.

    Powers the learner's "too hard" / "too easy" control. Keeps the item id and its
    review card; refreshes the word and its metadata.
    """
    material = session.get(Material, item.material_id) if item.material_id else None
    if material is None:
        raise ValueError("Vocabulary item is not linked to a material")

    from sprachheft.agents.generator import generate_one_vocab
    from sprachheft.services.generation import shift_level

    level = shift_level(item.cefr or material.level, direction)
    gv = generate_one_vocab(
        material, avoid=[item.word, item.lemma], difficulty=direction, level=level
    )
    item.word = gv.word
    item.lemma = (gv.lemma or gv.word).strip() or item.lemma
    item.pos = gv.pos
    item.meaning_en = gv.meaning_en
    item.cefr = gv.cefr or level
    item.example_de = gv.example_de
    item.example_en = gv.example_en
    item.grammar_tags = gv.grammar_tags
    session.add(item)
    # The stored embedding is now stale; drop it so a search reindex recomputes it.
    for row in session.exec(
        select(VocabEmbedding).where(VocabEmbedding.vocab_id == item.id)
    ).all():
        session.delete(row)
    session.commit()
    session.refresh(item)
    return item


def add_verb(
    session: Session,
    infinitive: str,
    *,
    english: str = "",
    partizip_ii: str = "",
    auxiliary: str = "",
    cefr: str | None = None,
    target_lang: str = "de",
) -> tuple[VocabItem, bool]:
    """Add a verb to the vocabulary, deduplicated by lemma. Returns (item, created)."""
    lemma = (infinitive or "").strip().lower()
    if not lemma:
        raise ValueError("infinitive is required")
    existing = session.exec(
        select(VocabItem).where(
            func.lower(VocabItem.lemma) == lemma,
            func.lower(func.coalesce(VocabItem.pos, "")) == "verb",
        )
    ).first()
    if existing is not None:
        return existing, False
    example_de = None
    if partizip_ii.strip():
        helper = "bin" if auxiliary.strip().lower() == "sein" else "habe"
        example_de = f"Ich {helper} {partizip_ii.strip()}."
    item = create_vocab(
        session,
        VocabItemCreate(
            word=infinitive.strip(),
            lemma=lemma,
            pos="verb",
            meaning_en=english.strip(),
            cefr=cefr,
            example_de=example_de,
            grammar_tags=["verb"],
            target_lang=target_lang,
        ),
    )
    return item, True


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
    target_lang = normalize_target(items[0].target_lang)
    native_lang = "en"
    if items[0].material_id:
        parent = session.get(Material, items[0].material_id)
        if parent:
            native_lang = parent.native_lang

    composed = compose(items, level, data.instructions, target_lang, native_lang)
    text = (composed.text or "").strip()
    if not text:
        raise ValueError(
            "Text generation returned nothing — is the language model configured?"
        )

    material = Material(
        title=data.title or composed.title or "Practice text",
        media_type="text",
        source_lang=target_lang,
        native_lang=native_lang,
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


def update_vocab(
    session: Session, vocab_id: int, data: VocabItemUpdate
) -> VocabItem | None:
    """Apply a partial update. Drops the (now stale) embedding when the word,
    meaning, or example changes so a later reindex regenerates it."""
    item = session.get(VocabItem, vocab_id)
    if item is None:
        return None

    fields = data.model_dump(exclude_unset=True)
    content_changed = False
    for key, value in fields.items():
        if value is None:
            continue
        if key in ("word", "meaning_en", "example_de") and getattr(item, key) != value:
            content_changed = True
        setattr(item, key, value)

    session.add(item)
    if content_changed:
        embedding = session.get(VocabEmbedding, vocab_id)
        if embedding is not None:
            session.delete(embedding)
    session.commit()
    session.refresh(item)
    return item


def delete_vocab_items(session: Session, ids: list[int]) -> int:
    """Delete vocab items and their SR state, review logs, and embeddings.

    Accepts a list so the UI can remove a de-duplicated word (all its copies)
    or several selected words in one call.
    """
    deleted = 0
    for vocab_id in dict.fromkeys(ids):  # de-dupe, keep order
        item = session.get(VocabItem, vocab_id)
        if item is None:
            continue
        embedding = session.get(VocabEmbedding, vocab_id)
        if embedding is not None:
            session.delete(embedding)
        states = session.exec(
            select(SRState).where(
                SRState.item_type == "vocab", SRState.item_id == vocab_id
            )
        ).all()
        for state in states:
            logs = session.exec(
                select(ReviewLog).where(ReviewLog.srstate_id == state.id)
            ).all()
            for log in logs:
                session.delete(log)
            session.delete(state)
        session.delete(item)
        deleted += 1
    session.commit()
    return deleted


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
