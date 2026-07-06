"""News importer API: list sources, list latest articles, import one as a Material."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from sprachheft.api.deps import SessionDep
from sprachheft.news import deps_available
from sprachheft.schemas import (
    NewsArticleOut,
    NewsImportIn,
    NewsImportOut,
    NewsSourcesOut,
)
from sprachheft.services import news as svc

router = APIRouter(prefix="/news", tags=["news"])

_UNAVAILABLE = (
    "News fetching needs the optional 'daily' extra. Install it and restart the "
    "backend: cd backend && uv sync --extra daily"
)


@router.get("/sources", response_model=NewsSourcesOut)
def sources():
    return svc.list_sources()


@router.get("/latest", response_model=list[NewsArticleOut])
def latest(
    source: str = Query("nachrichtenleicht"),
    limit: int = Query(12, ge=1, le=30),
):
    if not deps_available():
        raise HTTPException(status_code=501, detail=_UNAVAILABLE)
    try:
        return svc.latest(source, limit)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown news source '{source}'.") from exc
    except Exception as exc:  # noqa: BLE001 — network/parse failures
        raise HTTPException(status_code=502, detail=f"Could not fetch news: {exc}") from exc


@router.post("/import", response_model=NewsImportOut, status_code=201)
def import_news(data: NewsImportIn, session: SessionDep):
    if not deps_available():
        raise HTTPException(status_code=501, detail=_UNAVAILABLE)
    try:
        return svc.import_article(session, data)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 — network/parse failures
        raise HTTPException(status_code=502, detail=f"News import failed: {exc}") from exc
