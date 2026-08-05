from pathlib import Path

import pytest
from docx import Document

from app.manuscripts.parser import parse_docx
from app.manuscripts.rules import run_rules
from app.models import ManuscriptIssueType

pytestmark = pytest.mark.no_database


def _document(path: Path) -> None:
    document = Document()
    document.add_heading("Results", level=1)
    document.add_paragraph(
        "The treatment causes improvement in all participants (Smith, 2020).  N = 42."
    )
    document.add_heading("References", level=1)
    document.add_paragraph("Jones, A. (2021). Unused. doi:bad-doi")
    document.add_paragraph("Jones, A. (2021). Duplicate.")
    document.save(path)


def test_parser_emits_stable_locators_and_hash(tmp_path: Path) -> None:
    path = tmp_path / "sample.docx"
    _document(path)
    first = parse_docx(path)
    second = parse_docx(path)
    assert first["schema"] == "reca.manuscript.parse.v1"
    assert first["paragraphs"][1]["locator"] == {
        "schema": "reca.manuscript.locator.v1",
        "paragraph": 1,
        "table": None,
        "cell": None,
    }
    assert first["text_hash"] == second["text_hash"]


def test_p0_rules_find_citation_causality_duplicate_doi_and_format(
    tmp_path: Path,
) -> None:
    path = tmp_path / "sample.docx"
    _document(path)
    findings = run_rules(parse_docx(path), {"CITATION", "CAUSALITY", "BASIC_FORMAT"})
    codes = {item.issue_type for item in findings}
    assert ManuscriptIssueType.IN_TEXT_CITATION_MISSING_REFERENCE in codes
    assert ManuscriptIssueType.UNUSED_REFERENCE in codes
    assert ManuscriptIssueType.DUPLICATE_REFERENCE in codes
    assert ManuscriptIssueType.INVALID_DOI_FORMAT in codes
    assert ManuscriptIssueType.CAUSAL_OVERCLAIM in codes
    assert ManuscriptIssueType.POPULATION_OVERGENERALIZATION in codes
    assert ManuscriptIssueType.PUNCTUATION_ISSUE in codes
    assert all(
        not item.auto_fixable for item in findings if item.severity.value == "HIGH"
    )


def test_parser_reports_tracked_changes_as_low_confidence(tmp_path: Path) -> None:
    path = tmp_path / "tracked.docx"
    _document(path)
    import zipfile

    with zipfile.ZipFile(path) as archive:
        members = {name: archive.read(name) for name in archive.namelist()}
        members["word/document.xml"] = members["word/document.xml"].replace(
            b"<w:t>Results</w:t>", b"<w:ins><w:r><w:t>Inserted</w:t></w:r></w:ins>"
        )
    with zipfile.ZipFile(path, "w") as archive:
        for name, content in members.items():
            archive.writestr(name, content)
    snapshot = parse_docx(path)
    assert snapshot["confidence"] == "LOW"
    assert "TRACKED_INSERTION" in snapshot["unsupported_features"]
