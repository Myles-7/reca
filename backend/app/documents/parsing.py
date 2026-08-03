from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from xml.etree.ElementTree import Element

from defusedxml import ElementTree
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.adapters.documents import DocumentParseError

TEI_NAMESPACE = "http://www.tei-c.org/ns/1.0"
_COORD_RE = re.compile(
    r"^(?P<page>\d+),(?P<x>-?\d+(?:\.\d+)?),(?P<y>-?\d+(?:\.\d+)?),"
    r"(?P<width>\d+(?:\.\d+)?),(?P<height>\d+(?:\.\d+)?)$"
)


@dataclass(frozen=True)
class ParsedPage:
    page_number: int
    text: str
    width: float | None
    height: float | None
    metadata: dict[str, Any]


@dataclass(frozen=True)
class ParsedChunk:
    page_start: int
    page_end: int
    section_path: list[str] | None
    chunk_index: int
    content: str
    content_hash: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class ParsedDocument:
    pages: list[ParsedPage]
    chunks: list[ParsedChunk]
    language: str | None


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _text(element: Element) -> str:
    return " ".join("".join(element.itertext()).split())


def _coordinates(value: str | None) -> list[dict[str, float | int]]:
    parsed: list[dict[str, float | int]] = []
    for item in (value or "").split(";"):
        match = _COORD_RE.fullmatch(item.strip())
        if match is None:
            continue
        parsed.append(
            {
                "page": int(match.group("page")),
                "x": float(match.group("x")),
                "y": float(match.group("y")),
                "width": float(match.group("width")),
                "height": float(match.group("height")),
            }
        )
    return parsed


def convert_tei(tei: bytes) -> ParsedDocument:
    try:
        root = ElementTree.fromstring(tei)
    except (ElementTree.ParseError, ValueError) as exc:
        raise DocumentParseError(
            "GROBID_SCHEMA_INVALID", "GROBID TEI is malformed.", retryable=False
        ) from exc
    if root.tag != f"{{{TEI_NAMESPACE}}}TEI":
        raise DocumentParseError(
            "GROBID_SCHEMA_INVALID", "GROBID TEI root is invalid.", retryable=False
        )
    body = root.find(f".//{{{TEI_NAMESPACE}}}body")
    if body is None:
        raise DocumentParseError(
            "GROBID_SCHEMA_INVALID", "GROBID TEI has no body.", retryable=False
        )
    language = root.get("{http://www.w3.org/XML/1998/namespace}lang")
    blocks: list[
        tuple[int, float, float, int, str, list[str], list[dict[str, Any]]]
    ] = []
    order = 0

    def visit(element: Element, section_path: list[str]) -> None:
        nonlocal order
        current_path = section_path
        if _local_name(element.tag) == "div":
            head = element.find(f"{{{TEI_NAMESPACE}}}head")
            heading = _text(head) if head is not None else ""
            if heading:
                current_path = [*section_path, heading]
        name = _local_name(element.tag)
        block_has_coordinates = False
        if name in {"head", "p", "s"}:
            content = _text(element)
            coords = _coordinates(element.get("coords"))
            if content and coords:
                block_has_coordinates = True
                first = coords[0]
                blocks.append(
                    (
                        int(first["page"]),
                        float(first["y"]),
                        float(first["x"]),
                        order,
                        content,
                        current_path,
                        coords,
                    )
                )
                order += 1
        for child in list(element):
            if name == "p" and block_has_coordinates and _local_name(child.tag) == "s":
                continue
            visit(child, current_path)

    visit(body, [])
    if not blocks:
        raise DocumentParseError(
            "GROBID_SCHEMA_INVALID",
            "GROBID TEI contains no page-addressable text.",
            retryable=False,
        )
    blocks.sort(key=lambda item: item[:4])
    page_blocks: dict[int, list[tuple[str, list[dict[str, Any]], list[str]]]] = {}
    chunks: list[ParsedChunk] = []
    for index, (page, _y, _x, _order, content, section_path, coords) in enumerate(
        blocks
    ):
        page_blocks.setdefault(page, []).append((content, coords, section_path))
        chunks.append(
            ParsedChunk(
                page_start=page,
                page_end=max(int(coord["page"]) for coord in coords),
                section_path=section_path or None,
                chunk_index=index,
                content=content,
                content_hash=hashlib.sha256(content.encode("utf-8")).hexdigest(),
                metadata={"parser": "GROBID", "coordinates": coords},
            )
        )
    pages = [
        ParsedPage(
            page_number=page,
            text="\n\n".join(item[0] for item in items),
            width=None,
            height=None,
            metadata={
                "parser": "GROBID",
                "coordinates": [coord for item in items for coord in item[1]],
            },
        )
        for page, items in sorted(page_blocks.items())
    ]
    return ParsedDocument(pages=pages, chunks=chunks, language=language)


def parse_with_pypdf(pdf_path: Path) -> ParsedDocument:
    try:
        reader = PdfReader(pdf_path, strict=False)
        if reader.is_encrypted:
            raise DocumentParseError(
                "PDF_ENCRYPTED", "Encrypted PDFs cannot be parsed.", retryable=False
            )
        pages: list[ParsedPage] = []
        chunks: list[ParsedChunk] = []
        for page_number, page in enumerate(reader.pages, start=1):
            content = "\n".join((page.extract_text() or "").splitlines()).strip()
            width = float(page.mediabox.width)
            height = float(page.mediabox.height)
            pages.append(
                ParsedPage(
                    page_number=page_number,
                    text=content,
                    width=width,
                    height=height,
                    metadata={
                        "parser": "PYPDF",
                        "degraded": True,
                        "coordinates_available": False,
                        "structure_available": False,
                    },
                )
            )
            if content:
                chunks.append(
                    ParsedChunk(
                        page_start=page_number,
                        page_end=page_number,
                        section_path=None,
                        chunk_index=len(chunks),
                        content=content,
                        content_hash=hashlib.sha256(
                            content.encode("utf-8")
                        ).hexdigest(),
                        metadata={
                            "parser": "PYPDF",
                            "degraded": True,
                            "coordinates_available": False,
                            "structure_available": False,
                        },
                    )
                )
    except DocumentParseError:
        raise
    except (PdfReadError, OSError, ValueError) as exc:
        raise DocumentParseError(
            "PDF_CORRUPT", "The PDF could not be parsed.", retryable=False
        ) from exc
    if not pages or not chunks:
        raise DocumentParseError(
            "PDF_SCANNED_NO_TEXT",
            "The PDF contains no extractable text; OCR is not available in M2.",
            retryable=False,
        )
    return ParsedDocument(pages=pages, chunks=chunks, language=None)
