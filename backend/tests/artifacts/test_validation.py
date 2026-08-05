import stat
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
        archive.writestr(
            "[Content_Types].xml",
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Override PartName="/word/document.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
            "</Types>",
        )
        archive.writestr(
            "word/document.xml",
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>',
        )
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


def _docx_policy():
    return policy_for(
        artifact_type=ArtifactType.MANUSCRIPT_DOCX,
        filename="paper.docx",
        declared_mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )[1]


def _write_docx(
    path: Path,
    *,
    main_type: str | None = None,
    extras: dict[str, str | bytes] | None = None,
) -> None:
    content_type = (
        main_type
        or "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(
            "[Content_Types].xml",
            f'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Override PartName="/word/document.xml" ContentType="{content_type}"/></Types>',
        )
        archive.writestr(
            "word/document.xml",
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>',
        )
        for name, content in (extras or {}).items():
            archive.writestr(name, content)


@pytest.mark.parametrize(
    ("name", "extras"),
    [
        ("nested", {"word/embeddings/payload.zip": b"PK\x03\x04"}),
        ("traversal", {"../escape.xml": "<x/>"}),
        (
            "external-image",
            {
                "word/_rels/document.xml.rels": '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="r1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="https://example.invalid/a.png" TargetMode="External"/></Relationships>'
            },
        ),
        (
            "remote-template",
            {
                "word/_rels/settings.xml.rels": '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="r1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/attachedTemplate" Target="https://example.invalid/a.dotm" TargetMode="External"/></Relationships>'
            },
        ),
        (
            "ole",
            {
                "word/_rels/document.xml.rels": '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="r1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/oleObject" Target="embeddings/a.bin"/></Relationships>'
            },
        ),
    ],
)
def test_docx_security_preflight_rejects_active_packages(
    tmp_path: Path, name: str, extras: dict[str, str | bytes]
) -> None:
    path = tmp_path / f"{name}.docx"
    _write_docx(path, extras=extras)
    with pytest.raises(ArtifactValidationError):
        verify_file_content(path, policy=_docx_policy())


def test_docx_security_preflight_rejects_macro_and_symlink(tmp_path: Path) -> None:
    macro = tmp_path / "macro.docx"
    _write_docx(
        macro,
        main_type="application/vnd.ms-word.document.macroEnabled.main+xml",
        extras={"word/vbaProject.bin": b"macro"},
    )
    with pytest.raises(ArtifactValidationError):
        verify_file_content(macro, policy=_docx_policy())

    linked = tmp_path / "linked.docx"
    _write_docx(linked)
    with zipfile.ZipFile(linked, "a") as archive:
        info = zipfile.ZipInfo("word/media/link.png")
        info.create_system = 3
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        archive.writestr(info, "../../outside")
    with pytest.raises(ArtifactValidationError):
        verify_file_content(linked, policy=_docx_policy())


def test_docx_allows_inert_external_hyperlink_without_fetching(tmp_path: Path) -> None:
    path = tmp_path / "hyperlink.docx"
    _write_docx(
        path,
        extras={
            "word/_rels/document.xml.rels": '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="r1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" Target="https://example.invalid/reference" TargetMode="External"/></Relationships>'
        },
    )
    assert verify_file_content(path, policy=_docx_policy()) == _docx_policy().mime_type
