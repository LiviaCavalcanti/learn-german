"""Dictionary API: offline lookup with hover-friendly payloads."""

from __future__ import annotations

from dataclasses import asdict
from urllib.parse import quote

from fastapi import APIRouter, Query

from sprachheft.dictionary.lemmatize import lemmatize
from sprachheft.dictionary.service import get_dictionary_service
from sprachheft.languages import get_language, normalize_native, normalize_target
from sprachheft.schemas import DictEntryOut, DictionaryLookupResponse

router = APIRouter(prefix="/dictionary", tags=["dictionary"])


def google_translate_url(word: str, source: str = "de", target: str = "en") -> str:
    return (
        f"https://translate.google.com/?sl={source}&tl={target}"
        f"&text={quote(word)}&op=translate"
    )


@router.get("/status")
def status():
    service = get_dictionary_service()
    return {"available": service.is_available(), "entry_count": service.entry_count()}


@router.get("/lookup", response_model=DictionaryLookupResponse)
def lookup(
    word: str = Query(..., min_length=1),
    pos: str | None = None,
    lang: str = Query("de"),
    native: str = Query("en"),
):
    target = normalize_target(lang)
    nat = normalize_native(native)
    service = get_dictionary_service()
    entries = [DictEntryOut(**asdict(e)) for e in service.lookup(word, pos=pos, lang=target)]
    return DictionaryLookupResponse(
        query=word,
        lemma=lemmatize(word, get_language(target).lemmatizer),
        available=service.is_available(),
        entries=entries,
        google_translate_url=google_translate_url(word, target, nat),
    )
