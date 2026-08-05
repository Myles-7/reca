from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any

from app.manuscripts.parser import excerpt
from app.models import ManuscriptIssueSeverity, ManuscriptIssueType

RULE_SET_VERSION = "m6-p0-must-1.0"


@dataclass(frozen=True)
class Finding:
    issue_type: ManuscriptIssueType
    severity: ManuscriptIssueSeverity
    locator: dict[str, Any]
    original_text: str | None
    normalized_reference: str | None
    reason: str
    suggestion: str | None
    auto_fixable: bool = False
    confidence: str = "HIGH"

    @property
    def finding_hash(self) -> str:
        payload = {
            "code": self.issue_type.value,
            "locator": self.locator,
            "reference": self.normalized_reference,
            "reason": self.reason,
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()


_AUTHOR_YEAR = re.compile(
    r"\(([A-Z][A-Za-z'-]+(?:\s+(?:et al\.|&\s*[A-Z][A-Za-z'-]+))?),\s*(19|20)\d{2}[a-z]?\)"
)
_DOI = re.compile(r"\bdoi\s*:\s*([^\s,;]+)", re.IGNORECASE)
_VALID_DOI = re.compile(r"^10\.\d{4,9}/[-._;()/:A-Z0-9]+$", re.IGNORECASE)
_SAMPLE_SIZE = re.compile(r"\bN\s*=\s*(\d+)\b")
_FIGURE_REFERENCE = re.compile(r"\b(?:Figure|Fig\.)\s*(\d+)\b", re.IGNORECASE)
_ABBREVIATION = re.compile(r"\b[A-Z][A-Z0-9-]{2,}\b")


def run_rules(snapshot: dict[str, Any], checks: set[str]) -> list[Finding]:
    paragraphs = snapshot.get("paragraphs", [])
    texts = [str(item.get("text", "")) for item in paragraphs]
    reference_start = next(
        (
            index
            for index, text in enumerate(texts)
            if text.strip().lower() in {"references", "bibliography", "参考文献"}
        ),
        len(texts),
    )
    body = texts[:reference_start]
    references = texts[reference_start + 1 :] if reference_start < len(texts) else []
    findings: list[Finding] = []

    if "CITATION" in checks:
        cited = {
            (match.group(1).lower(), match.group(0)[-5:-1])
            for text in body
            for match in _AUTHOR_YEAR.finditer(text)
        }
        ref_keys: list[tuple[str, str, int]] = []
        for offset, text in enumerate(references, start=reference_start + 1):
            author_match = re.match(r"\s*([A-Z][A-Za-z'-]+)", text)
            year_match = re.search(r"\b((?:19|20)\d{2}[a-z]?)\b", text)
            if author_match and year_match:
                ref_keys.append(
                    (
                        author_match.group(1).lower(),
                        year_match.group(1),
                        offset,
                    )
                )
            for doi in _DOI.finditer(text):
                if not _VALID_DOI.fullmatch(doi.group(1).rstrip(".")):
                    findings.append(
                        _finding(
                            ManuscriptIssueType.INVALID_DOI_FORMAT,
                            ManuscriptIssueSeverity.MEDIUM,
                            paragraphs[offset],
                            text,
                            "Reference contains an invalid DOI format.",
                            doi.group(1),
                        )
                    )
        ref_set = {(author, year) for author, year, _ in ref_keys}
        for author, year in sorted(cited - ref_set):
            findings.append(
                Finding(
                    ManuscriptIssueType.IN_TEXT_CITATION_MISSING_REFERENCE,
                    ManuscriptIssueSeverity.HIGH,
                    {
                        "schema": "reca.manuscript.locator.v1",
                        "paragraph": None,
                        "citation": f"{author}:{year}",
                    },
                    None,
                    f"{author}:{year}",
                    "An in-text citation has no matching bibliography entry.",
                    "Add or verify the corresponding reference.",
                )
            )
        for author, year, index in ref_keys:
            if (author, year) not in cited:
                findings.append(
                    _finding(
                        ManuscriptIssueType.UNUSED_REFERENCE,
                        ManuscriptIssueSeverity.MEDIUM,
                        paragraphs[index],
                        references[index - reference_start - 1],
                        "Bibliography entry is not cited in the manuscript.",
                        f"{author}:{year}",
                    )
                )
        seen: set[tuple[str, str]] = set()
        for author, year, index in ref_keys:
            if (author, year) in seen:
                findings.append(
                    _finding(
                        ManuscriptIssueType.DUPLICATE_REFERENCE,
                        ManuscriptIssueSeverity.MEDIUM,
                        paragraphs[index],
                        texts[index],
                        "Bibliography contains a duplicate author-year entry.",
                        f"{author}:{year}",
                    )
                )
            seen.add((author, year))

    for index, text in enumerate(body):
        paragraph = paragraphs[index]
        lowered = text.lower()
        if "CAUSALITY" in checks and re.search(
            r"\b(causes?|caused|leads? to|results? in)\b", lowered
        ):
            findings.append(
                _finding(
                    ManuscriptIssueType.CAUSAL_OVERCLAIM,
                    ManuscriptIssueSeverity.HIGH,
                    paragraph,
                    text,
                    "Causal language requires a verified causal design and cannot be inferred from association alone.",
                    None,
                )
            )
        if "CAUSALITY" in checks and re.search(
            r"\b(all|everyone|entire population|普遍|所有人)\b", lowered
        ):
            findings.append(
                _finding(
                    ManuscriptIssueType.POPULATION_OVERGENERALIZATION,
                    ManuscriptIssueSeverity.HIGH,
                    paragraph,
                    text,
                    "Population-wide wording may exceed the sampled population.",
                    None,
                )
            )
        if "BASIC_FORMAT" in checks and re.search(r" {2,}", text):
            findings.append(
                _finding(
                    ManuscriptIssueType.PUNCTUATION_ISSUE,
                    ManuscriptIssueSeverity.LOW,
                    paragraph,
                    text,
                    "Paragraph contains repeated spaces.",
                    "Use a single space.",
                    auto_fixable=True,
                )
            )
        if "BASIC_FORMAT" in checks and re.search(r"\d(?:kg|mg|cm|mm|%)\b", text):
            findings.append(
                _finding(
                    ManuscriptIssueType.UNIT_FORMAT_ISSUE,
                    ManuscriptIssueSeverity.LOW,
                    paragraph,
                    text,
                    "A numeric value and its unit require normalized spacing.",
                    None,
                    auto_fixable=True,
                )
            )

    if "NUMERIC_CONSISTENCY" in checks:
        sample_sizes = [
            (int(match.group(1)), paragraphs[index])
            for index, text in enumerate(body)
            for match in _SAMPLE_SIZE.finditer(text)
        ]
        distinct_sizes = {value for value, _ in sample_sizes}
        if len(distinct_sizes) > 1:
            for value, paragraph in sample_sizes:
                findings.append(
                    _finding(
                        ManuscriptIssueType.SAMPLE_SIZE_MISMATCH,
                        ManuscriptIssueSeverity.HIGH,
                        paragraph,
                        str(paragraph["text"]),
                        "The manuscript contains inconsistent sample-size values; formal project evidence must be reviewed.",
                        f"N={value}",
                    )
                )

    if "BASIC_FORMAT" in checks:
        figure_numbers = [
            (int(match.group(1)), paragraphs[index])
            for index, text in enumerate(body)
            for match in _FIGURE_REFERENCE.finditer(text)
        ]
        values = [number for number, _ in figure_numbers]
        if values and sorted(set(values)) != list(range(1, max(values) + 1)):
            number, paragraph = figure_numbers[0]
            findings.append(
                _finding(
                    ManuscriptIssueType.FIGURE_NUMBERING_ISSUE,
                    ManuscriptIssueSeverity.MEDIUM,
                    paragraph,
                    str(paragraph["text"]),
                    "Figure references are not a contiguous sequence starting at 1.",
                    f"Figure {number}",
                )
            )
        previous_level = 0
        for paragraph in paragraphs:
            style = str(paragraph.get("style") or "")
            match = re.fullmatch(r"Heading (\d+)", style)
            if not match:
                continue
            level = int(match.group(1))
            if previous_level and level > previous_level + 1:
                findings.append(
                    _finding(
                        ManuscriptIssueType.HEADING_LEVEL_ISSUE,
                        ManuscriptIssueSeverity.LOW,
                        paragraph,
                        str(paragraph["text"]),
                        "Heading level skips an intermediate level.",
                        style,
                    )
                )
            previous_level = level

    if "TERMINOLOGY" in checks:
        full_text = "\n".join(body)
        for abbreviation in sorted(set(_ABBREVIATION.findall(full_text))):
            if not re.search(
                rf"\([^)]*\b{re.escape(abbreviation)}\b[^)]*\)", full_text
            ):
                index = next(i for i, text in enumerate(body) if abbreviation in text)
                findings.append(
                    _finding(
                        ManuscriptIssueType.UNDEFINED_ABBREVIATION,
                        ManuscriptIssueSeverity.MEDIUM,
                        paragraphs[index],
                        body[index],
                        "An abbreviation is used without a detectable definition.",
                        abbreviation,
                    )
                )
    return findings


def _finding(
    code: ManuscriptIssueType,
    severity: ManuscriptIssueSeverity,
    paragraph: dict[str, Any],
    text: str,
    reason: str,
    normalized: str | None,
    *,
    auto_fixable: bool = False,
) -> Finding:
    return Finding(
        code,
        severity,
        dict(paragraph["locator"]),
        excerpt(text),
        normalized,
        reason,
        None,
        auto_fixable=auto_fixable
        and severity in {ManuscriptIssueSeverity.LOW, ManuscriptIssueSeverity.INFO},
    )
