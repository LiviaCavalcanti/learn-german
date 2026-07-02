"""Offline dictionary module (WikDict-backed).

- ``loader``    downloads a WikDict pair DB and imports it into a normalized
                ``dict.sqlite`` (schema we control) for stable queries.
- ``service``   looks words up (exact, then lemmatized).
- ``lemmatize`` maps inflected forms to lemmas via simplemma.
"""

from __future__ import annotations

from sprachheft.dictionary.service import (
    DictEntry,
    DictionaryService,
    get_dictionary_service,
)

__all__ = ["DictEntry", "DictionaryService", "get_dictionary_service"]
