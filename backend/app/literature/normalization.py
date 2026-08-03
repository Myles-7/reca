from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher

_DOI_PATTERN = re.compile(r"^10\.\d{4,9}/\S+$", re.IGNORECASE)


def normalize_doi(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    if not normalized:
        return None
    lowered = normalized.casefold()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if lowered.startswith(prefix):
            normalized = normalized[len(prefix) :].strip()
            break
    normalized = normalized.casefold()
    if not _DOI_PATTERN.fullmatch(normalized):
        return None
    return normalized


def normalize_title(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold().strip()
    tokens: list[str] = []
    pending_space = False
    for character in normalized:
        category = unicodedata.category(character)
        if category[0] in {"L", "N"}:
            if pending_space and tokens:
                tokens.append(" ")
            tokens.append(character)
            pending_space = False
        else:
            pending_space = True
    return "".join(tokens).strip()


def title_similarity(left: str, right: str) -> float:
    normalized_left = normalize_title(left)
    normalized_right = normalize_title(right)
    if not normalized_left or not normalized_right:
        return 0.0
    return SequenceMatcher(None, normalized_left, normalized_right).ratio()
