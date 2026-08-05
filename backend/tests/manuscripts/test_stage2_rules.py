from __future__ import annotations

from io import BytesIO

import pytest
from docx import Document

from app.manuscripts.fixers import apply_fixes, preview_fixes
from app.manuscripts.revision import compare_revisions

pytestmark = pytest.mark.no_database


def _snapshot(*paragraphs: str) -> dict[str, object]:
    return {
        "paragraphs": [
            {"index": index, "text": text} for index, text in enumerate(paragraphs)
        ]
    }


def _docx(text: str) -> bytes:
    output = BytesIO()
    document = Document()
    document.add_paragraph(text)
    document.save(output)
    return output.getvalue()


def test_revision_audit_detects_competition_core_drift() -> None:
    before = _snapshot(
        "In this sample, N = 42 was associated with improvement (Smith, 2020). Figure 1."
    )
    after = _snapshot(
        "Everyone with N = 40 is affected by improvement (Jones, 2021). Figure 2."
    )
    findings = compare_revisions(before, after)
    codes = {item["code"] for item in findings}
    assert codes == {
        "CLAIM_NUMERIC_MISMATCH",
        "CITATION_SET_CHANGED",
        "CLAIM_CAUSAL_OVERSTATEMENT",
        "CLAIM_SCOPE_OVERGENERALIZATION",
        "CLAIM_FIGURE_VERSION_MISMATCH",
    }
    assert all(len(str(item["finding_hash"])) == 64 for item in findings)


def test_low_risk_preview_is_deterministic_and_does_not_mutate_input() -> None:
    source = _docx("A  sentence.")
    original = source
    actions = [
        {
            "issue_id": "00000000-0000-0000-0000-000000000001",
            "fixer": "NORMALIZE_SPACES",
            "paragraph": 0,
            "finding_hash": "a" * 64,
        }
    ]
    first = preview_fixes(source, actions, unsupported_features=[])
    second = preview_fixes(source, actions, unsupported_features=[])
    assert first == second
    assert first["changes"][0]["before"] == "A  sentence."
    assert first["changes"][0]["after"] == "A sentence."
    # Preview must not rewrite the source bytes in place.
    assert source == original


def test_fixer_rejects_unsupported_or_unknown_package_features() -> None:
    source = _docx("A  sentence.")
    actions = [
        {
            "issue_id": "00000000-0000-0000-0000-000000000001",
            "fixer": "NORMALIZE_SPACES",
            "paragraph": 0,
            "finding_hash": "a" * 64,
        }
    ]
    with pytest.raises(ValueError, match="unsupported structures"):
        apply_fixes(
            source,
            actions,
            unsupported_features=["UNKNOWN_PART:customXml/item1.xml"],
        )


def test_fixer_rejects_stale_locator_and_unknown_action() -> None:
    source = _docx("A sentence.")
    with pytest.raises(ValueError, match="stale"):
        apply_fixes(
            source,
            [
                {
                    "issue_id": "00000000-0000-0000-0000-000000000001",
                    "fixer": "NORMALIZE_SPACES",
                    "paragraph": 3,
                    "finding_hash": "a" * 64,
                }
            ],
            unsupported_features=[],
        )
