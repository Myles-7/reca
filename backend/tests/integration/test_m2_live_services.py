from __future__ import annotations

import asyncio
import os
import uuid
from pathlib import Path

import pytest

from app.adapters.documents import GrobidAdapter
from app.adapters.literature import LiteratureQueryPlanDTO, PyAlexOpenAlexProvider
from tests.documents.test_parsing import text_pdf_bytes

pytestmark = pytest.mark.no_database


@pytest.mark.skipif(
    os.getenv("RECA_RUN_LIVE_OPENALEX") != "1",
    reason="set RECA_RUN_LIVE_OPENALEX=1 for the real OpenAlex smoke",
)
def test_live_openalex_provider_smoke() -> None:
    page = asyncio.run(
        PyAlexOpenAlexProvider().search(
            LiteratureQueryPlanDTO(
                project_id=str(uuid.uuid4()),
                query_plan_id=str(uuid.uuid4()),
                english_terms=("research workflow",),
            ),
            page_size=1,
        )
    )
    assert page.transport_mode == "LIVE"
    assert page.degraded is False
    assert len(page.records) == 1
    assert page.records[0].source_identifier.startswith("https://openalex.org/")
    assert page.implementation_metadata["provider"] == "OPENALEX_PYALEX"
    assert page.implementation_metadata["transport_mode"] == "LIVE"


@pytest.mark.skipif(
    os.getenv("RECA_RUN_LIVE_GROBID") != "1",
    reason="set RECA_RUN_LIVE_GROBID=1 for the real GROBID smoke",
)
def test_live_grobid_parse_smoke(tmp_path: Path) -> None:
    pdf_path = tmp_path / "m2-live-smoke.pdf"
    pdf_path.write_bytes(text_pdf_bytes("M2 live GROBID smoke"))
    result = GrobidAdapter().parse(pdf_path, extract_coordinates=True)
    assert result.tei.startswith(b"<?xml")
    assert b"<TEI" in result.tei or b"<tei" in result.tei
    assert result.version is not None
