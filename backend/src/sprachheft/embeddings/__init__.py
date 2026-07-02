"""Embeddings for semantic vocabulary search.

Pluggable: if ``SPRACHHEFT_EMBEDDING_MODEL`` is set, real embeddings are computed
via litellm (e.g. ``ollama/nomic-embed-text`` or ``text-embedding-3-small``).
Otherwise a deterministic local hashing embedder is used so similarity search
works offline (lexical, not truly semantic). Swap in your own vectors (e.g. from
graph-rag) behind ``embed_texts`` without changing callers.
"""

from __future__ import annotations

import hashlib
import math
from functools import lru_cache

from sprachheft.config import get_settings

_LOCAL_DIM = 256


def _bucket(token: str, dim: int) -> int:
    return int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16) % dim


def _local_embed(text: str, dim: int = _LOCAL_DIM) -> list[float]:
    vec = [0.0] * dim
    lowered = (text or "").lower()
    grams = [lowered[i : i + 3] for i in range(max(0, len(lowered) - 2))]
    for token in lowered.split() + grams:
        if token:
            vec[_bucket(token, dim)] += 1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


@lru_cache(maxsize=2)
def _fastembed_model(name: str):
    from fastembed import TextEmbedding

    return TextEmbedding(model_name=name)


def _fastembed_embed(name: str, texts: list[str]) -> list[list[float]]:
    model = _fastembed_model(name)
    return [[float(x) for x in vector] for vector in model.embed(list(texts))]


def embed_texts(texts: list[str]) -> list[list[float]]:
    settings = get_settings()
    model = (settings.embedding_model or "").strip()
    if not model:
        return [_local_embed(t) for t in texts]
    if model.startswith("fastembed:"):
        try:
            return _fastembed_embed(model.split(":", 1)[1], texts)
        except Exception:
            return [_local_embed(t) for t in texts]
    try:
        import litellm

        kwargs: dict = {}
        if settings.llm_api_base:
            kwargs["api_base"] = settings.llm_api_base
        if settings.llm_api_key:
            kwargs["api_key"] = settings.llm_api_key
        resp = litellm.embedding(model=model, input=texts, **kwargs)
        return [item["embedding"] for item in resp["data"]]
    except Exception:
        return [_local_embed(t) for t in texts]


def cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (na * nb)
