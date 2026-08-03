from __future__ import annotations

from io import BytesIO
from pathlib import Path

import httpx
import pytest
from pypdf import PdfReader, PdfWriter
from pypdf.generic import (
    DecodedStreamObject,
    DictionaryObject,
    NameObject,
)

from app.adapters.documents import DocumentParseError, GrobidAdapter
from app.core.config import settings
from app.documents.parsing import convert_tei, parse_with_pypdf

TEI = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:lang="zh">
  <text><body><div><head coords="1,50,50,200,20">Methods</head>
    <p coords="1,300,100,200,40">Right column</p>
    <p coords="1,50,100,200,40">Left column</p>
    <p coords="2,50,80,400,40">中文结果稳定。</p>
  </div></body></text>
</TEI>""".encode()


def text_pdf_bytes(text: str = "RECA fallback text") -> bytes:
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    font_ref = writer._add_object(font)
    page[NameObject("/Resources")] = DictionaryObject(
        {NameObject("/Font"): DictionaryObject({NameObject("/F1"): font_ref})}
    )
    stream = DecodedStreamObject()
    stream.set_data(f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode())
    page[NameObject("/Contents")] = writer._add_object(stream)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def test_tei_converter_orders_columns_and_preserves_chinese_pages() -> None:
    parsed = convert_tei(TEI)

    assert parsed.language == "zh"
    assert [page.page_number for page in parsed.pages] == [1, 2]
    assert parsed.pages[0].text.split("\n\n") == [
        "Methods",
        "Left column",
        "Right column",
    ]
    assert parsed.pages[1].text == "中文结果稳定。"
    assert [chunk.chunk_index for chunk in parsed.chunks] == [0, 1, 2, 3]
    assert parsed.chunks[1].section_path == ["Methods"]
    assert parsed.chunks[1].metadata["coordinates"][0]["page"] == 1


@pytest.mark.parametrize(
    "tei",
    [
        b"not xml",
        b"<TEI><text><body><p>no namespace</p></body></text></TEI>",
        b'<TEI xmlns="http://www.tei-c.org/ns/1.0"><text/></TEI>',
        b'<!DOCTYPE x [<!ENTITY x SYSTEM "file:///etc/passwd">]><TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body><p coords="1,1,1,1,1">&x;</p></body></text></TEI>',
    ],
)
def test_tei_converter_fails_closed_for_invalid_or_unsafe_xml(tei: bytes) -> None:
    with pytest.raises(DocumentParseError) as raised:
        convert_tei(tei)
    assert raised.value.code == "GROBID_SCHEMA_INVALID"
    assert raised.value.retryable is False


def test_pypdf_fallback_extracts_only_real_page_text(tmp_path: Path) -> None:
    path = tmp_path / "text.pdf"
    path.write_bytes(text_pdf_bytes())

    parsed = parse_with_pypdf(path)

    assert [page.page_number for page in parsed.pages] == [1]
    assert parsed.pages[0].text == "RECA fallback text"
    assert parsed.pages[0].metadata["coordinates_available"] is False
    assert parsed.chunks[0].section_path is None
    assert parsed.chunks[0].metadata["structure_available"] is False


def test_pypdf_rejects_encrypted_corrupt_and_scanned_pdf(tmp_path: Path) -> None:
    encrypted_writer = PdfWriter()
    encrypted_writer.add_blank_page(width=100, height=100)
    encrypted_writer.encrypt("secret")
    encrypted = tmp_path / "encrypted.pdf"
    with encrypted.open("wb") as target:
        encrypted_writer.write(target)
    blank_writer = PdfWriter()
    blank_writer.add_blank_page(width=100, height=100)
    scanned = tmp_path / "scanned.pdf"
    with scanned.open("wb") as target:
        blank_writer.write(target)
    corrupt = tmp_path / "corrupt.pdf"
    corrupt.write_bytes(b"%PDF-1.7\ncorrupt")

    expected = {
        encrypted: "PDF_ENCRYPTED",
        scanned: "PDF_SCANNED_NO_TEXT",
        corrupt: "PDF_CORRUPT",
    }
    for path, code in expected.items():
        with pytest.raises(DocumentParseError) as raised:
            parse_with_pypdf(path)
        assert raised.value.code == code
        assert raised.value.retryable is False


def test_grobid_adapter_returns_raw_tei_and_version(tmp_path: Path) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path == "/api/version":
            return httpx.Response(200, json={"version": "0.8.2", "revision": "abc"})
        return httpx.Response(200, content=TEI)

    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(text_pdf_bytes())
    result = GrobidAdapter(transport=httpx.MockTransport(handler)).parse(
        pdf, extract_coordinates=True
    )

    assert result.tei == TEI
    assert result.version == "0.8.2"
    assert result.revision == "abc"
    body = requests[0].read()
    assert b"teiCoordinates" in body
    assert b'name="input"' in body


@pytest.mark.parametrize(
    ("failure", "code", "retryable"),
    [
        (httpx.ReadTimeout("late"), "GROBID_TIMEOUT", True),
        (httpx.Response(503), "GROBID_UNAVAILABLE", True),
        (httpx.Response(204), "GROBID_EMPTY_OUTPUT", False),
        (httpx.Response(200, content=b""), "GROBID_EMPTY_OUTPUT", False),
        (httpx.Response(415), "GROBID_INPUT_REJECTED", False),
        (httpx.Response(500), "GROBID_PROCESSING_FAILED", False),
    ],
)
def test_grobid_adapter_normalizes_failures(
    tmp_path: Path,
    failure: Exception | httpx.Response,
    code: str,
    retryable: bool,
) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        if isinstance(failure, Exception):
            raise failure
        return failure

    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(text_pdf_bytes())
    with pytest.raises(DocumentParseError) as raised:
        GrobidAdapter(transport=httpx.MockTransport(handler)).parse(
            pdf, extract_coordinates=False
        )
    assert raised.value.code == code
    assert raised.value.retryable is retryable


def test_generated_pdf_fixture_is_readable() -> None:
    reader = PdfReader(BytesIO(text_pdf_bytes()))
    assert reader.pages[0].extract_text() == "RECA fallback text"


def test_grobid_adapter_enforces_streaming_response_limit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "GROBID_MAX_RESPONSE_BYTES", 32)
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(text_pdf_bytes())

    with pytest.raises(DocumentParseError) as raised:
        GrobidAdapter(
            transport=httpx.MockTransport(
                lambda _request: httpx.Response(200, content=TEI)
            )
        ).parse(pdf, extract_coordinates=True)

    assert raised.value.code == "GROBID_OUTPUT_TOO_LARGE"
    assert raised.value.retryable is False
