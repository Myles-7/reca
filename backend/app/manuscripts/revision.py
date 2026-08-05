from __future__ import annotations

import hashlib
import json
import re
from typing import Any

REVISION_RULE_SET_VERSION = "manu-p0-018-1.0"

_NUMBER = re.compile(
    r"\b(?P<label>N|p|r|beta|β)\s*(?:=|<|>)\s*(?P<value>-?\d+(?:\.\d+)?)",
    re.IGNORECASE,
)
_CITATION = re.compile(r"\(([^()]+?,\s*(?:19|20)\d{2}[a-z]?)\)")
_FIGURE = re.compile(r"\b(?:Figure|Fig\.)\s*(\d+)\b", re.IGNORECASE)
_CAUSAL = re.compile(
    r"\b(causes?|caused|leads? to|results? in|impacts?|affects?|affected)\b",
    re.IGNORECASE,
)
_ASSOCIATIVE = re.compile(
    r"\b(associated|association|correlated|correlation|related)\b", re.IGNORECASE
)
_LIMIT = re.compile(
    r"\b(in this sample|among participants|within the sample|sampled population)\b",
    re.IGNORECASE,
)
_UNIVERSAL = re.compile(
    r"\b(all|everyone|entire population|universally)\b", re.IGNORECASE
)


def _paragraph_map(snapshot: dict[str, Any]) -> dict[int, str]:
    return {
        int(item["index"]): str(item.get("text", ""))
        for item in snapshot.get("paragraphs", [])
    }


def _finding(
    code: str,
    *,
    paragraph: int | None,
    before: str | None,
    after: str | None,
    detail: dict[str, Any],
) -> dict[str, Any]:
    payload = {
        "code": code,
        "paragraph": paragraph,
        "before": before,
        "after": after,
        "detail": detail,
    }
    payload["finding_hash"] = hashlib.sha256(
        json.dumps(
            payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")
        ).encode()
    ).hexdigest()
    return payload


def compare_revisions(
    before: dict[str, Any], after: dict[str, Any]
) -> list[dict[str, Any]]:
    baseline = _paragraph_map(before)
    candidate = _paragraph_map(after)
    findings: list[dict[str, Any]] = []
    for index in sorted(set(baseline) | set(candidate)):
        old = baseline.get(index, "")
        new = candidate.get(index, "")
        old_numbers = {
            (m.group("label").lower(), m.group("value")) for m in _NUMBER.finditer(old)
        }
        new_numbers = {
            (m.group("label").lower(), m.group("value")) for m in _NUMBER.finditer(new)
        }
        if old_numbers != new_numbers and (old_numbers or new_numbers):
            findings.append(
                _finding(
                    "CLAIM_NUMERIC_MISMATCH",
                    paragraph=index,
                    before=old[:240],
                    after=new[:240],
                    detail={
                        "removed": sorted(old_numbers - new_numbers),
                        "added": sorted(new_numbers - old_numbers),
                    },
                )
            )
        old_citations = set(_CITATION.findall(old))
        new_citations = set(_CITATION.findall(new))
        if old_citations != new_citations:
            findings.append(
                _finding(
                    "CITATION_SET_CHANGED",
                    paragraph=index,
                    before=old[:240],
                    after=new[:240],
                    detail={
                        "removed": sorted(old_citations - new_citations),
                        "added": sorted(new_citations - old_citations),
                    },
                )
            )
        if _ASSOCIATIVE.search(old) and _CAUSAL.search(new) and not _CAUSAL.search(old):
            findings.append(
                _finding(
                    "CLAIM_CAUSAL_OVERSTATEMENT",
                    paragraph=index,
                    before=old[:240],
                    after=new[:240],
                    detail={"transition": "ASSOCIATION_TO_CAUSAL"},
                )
            )
        if (
            _LIMIT.search(old)
            and not _LIMIT.search(new)
            and (_UNIVERSAL.search(new) or new)
        ):
            findings.append(
                _finding(
                    "CLAIM_SCOPE_OVERGENERALIZATION",
                    paragraph=index,
                    before=old[:240],
                    after=new[:240],
                    detail={"removed_limitation": True},
                )
            )
        if set(_FIGURE.findall(old)) != set(_FIGURE.findall(new)):
            findings.append(
                _finding(
                    "CLAIM_FIGURE_VERSION_MISMATCH",
                    paragraph=index,
                    before=old[:240],
                    after=new[:240],
                    detail={
                        "before_figures": sorted(set(_FIGURE.findall(old))),
                        "after_figures": sorted(set(_FIGURE.findall(new))),
                    },
                )
            )
    return findings
