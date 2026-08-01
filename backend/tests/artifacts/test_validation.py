import zipfile
from pathlib import Path

import pytest

from app.artifacts.validation import (
    ArtifactValidationError,
    normalize_filename,
    policy_for,
    verify_file_content,
)
from app.models import ArtifactType

pytestmark = pytest.mark.no_database


def test_filename_normalization_removes_path_and_control_characters() -> None:
    assert normalize_filename("../../secret\x00.pdf") == "secret_.pdf"
    assert normalize_filename(r"..\..\paper.pdf") == "paper.pdf"


def test_declaration_rejects_dangerous_double_extension() -> None:
    with pytest.raises(ArtifactValidationError) as exc_info:
        policy_for(
            artifact_type=ArtifactType.PDF_DOCUMENT,
            filename="payload.exe.pdf",
            declared_mime="application/pdf",
        )

    assert exc_info.value.code == "FILE_TYPE_UNSUPPORTED"


def test_pdf_and_csv_content_headers_are_validated(tmp_path: Path) -> None:
    _, pdf_policy = policy_for(
        artifact_type=ArtifactType.PDF_DOCUMENT,
        filename="paper.pdf",
        declared_mime="application/pdf",
    )
    valid_pdf = tmp_path / "valid.pdf"
    valid_pdf.write_bytes(b"%PDF-1.7\nexample")
    assert verify_file_content(valid_pdf, policy=pdf_policy) == "application/pdf"

    invalid_pdf = tmp_path / "invalid.pdf"
    invalid_pdf.write_bytes(b"MZ executable")
    with pytest.raises(ArtifactValidationError):
        verify_file_content(invalid_pdf, policy=pdf_policy)

    _, csv_policy = policy_for(
        artifact_type=ArtifactType.DATASET_FILE,
        filename="data.csv",
        declared_mime="text/csv",
    )
    binary_csv = tmp_path / "binary.csv"
    binary_csv.write_bytes(b"a,b\n1,\x002")
    with pytest.raises(ArtifactValidationError):
        verify_file_content(binary_csv, policy=csv_policy)


def test_office_container_must_match_declared_type(tmp_path: Path) -> None:
    docx = tmp_path / "paper.docx"
    with zipfile.ZipFile(docx, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types />")
        archive.writestr("word/document.xml", "<document />")
    _, docx_policy = policy_for(
        artifact_type=ArtifactType.MANUSCRIPT_DOCX,
        filename="paper.docx",
        declared_mime=(
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ),
    )
    assert verify_file_content(docx, policy=docx_policy) == docx_policy.mime_type

    renamed_xlsx = tmp_path / "paper.xlsx"
    renamed_xlsx.write_bytes(docx.read_bytes())
    _, xlsx_policy = policy_for(
        artifact_type=ArtifactType.DATASET_FILE,
        filename="paper.xlsx",
        declared_mime=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
    )
    with pytest.raises(ArtifactValidationError):
        verify_file_content(renamed_xlsx, policy=xlsx_policy)
