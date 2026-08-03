from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import httpx
import pytest

from app.adapters.literature import (
    HttpxOpenAlexTransport,
    LiteratureProviderError,
    LiteratureQueryFiltersDTO,
    LiteratureQueryPlanDTO,
    ProviderErrorCode,
    PyAlexOpenAlexProvider,
    RecordedOpenAlexTransport,
    normalize_doi,
)

pytestmark = pytest.mark.no_database

_FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "openalex"
    / "works_recorded.json"
)


def _recordings() -> dict[str, dict[str, Any]]:
    payload = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    return payload["recordings"]


def _query() -> LiteratureQueryPlanDTO:
    return LiteratureQueryPlanDTO(
        project_id="project-1",
        query_plan_id="query-plan-1",
        chinese_terms=("研究流程",),
        english_terms=("research workflow",),
        synonyms={"en": ("scholarly workflow",)},
        boolean_query='"research workflow" AND metadata',
        filters=LiteratureQueryFiltersDTO(
            from_year=2024,
            to_year=2026,
            languages=("zh", "en"),
            work_types=("article", "review"),
            open_access_only=True,
        ),
    )


def test_recorded_search_normalizes_doi_authors_abstract_and_provenance() -> None:
    provider = PyAlexOpenAlexProvider(
        transport=RecordedOpenAlexTransport(_recordings()),
        api_url="https://api.openalex.org",
        api_key="secret-not-recorded",
        contact_email="provider@example.test",
    )

    page = asyncio.run(provider.search(_query(), page_size=1))

    assert page.project_id == "project-1"
    assert page.query_plan_id == "query-plan-1"
    assert page.transport_mode == "RECORDED"
    assert page.degraded is True
    assert page.limitations == ("Recorded OpenAlex response; results are not live.",)
    assert page.next_cursor == "cursor-page-2"
    assert len(page.records) == 1
    record = page.records[0]
    assert record.__class__.__module__ == "app.adapters.literature"
    assert record.normalized_doi == "10.1000/reca.sample"
    assert [author.display_name for author in record.authors] == [
        "Recorded Author One",
        "Recorded Author Two",
    ]
    assert record.abstract == "Recorded metadata is deterministic"
    assert record.source_name == "Recorded Journal"
    assert record.raw_source_data["id"] == record.source_identifier
    assert page.snapshot.sha256
    assert "secret-not-recorded" not in json.dumps(page.model_dump(mode="json"))
    assert page.implementation_metadata["pyalex_version"] == "0.21"


def test_cursor_page_and_query_filters_are_explicit_and_bounded() -> None:
    provider = PyAlexOpenAlexProvider(
        transport=RecordedOpenAlexTransport(_recordings())
    )

    first = asyncio.run(provider.search(_query(), cursor="*", page_size=1))
    second = asyncio.run(
        provider.search(_query(), cursor=first.next_cursor or "", page_size=1)
    )

    assert first.provider_query["search"] == '"research workflow" AND metadata'
    assert "from_publication_date:2024-01-01" in first.provider_query["filter"]
    assert "to_publication_date:2026-12-31" in first.provider_query["filter"]
    assert "language:zh|en" in first.provider_query["filter"]
    assert "type:article|review" in first.provider_query["filter"]
    assert "open_access.is_oa:true" in first.provider_query["filter"]
    assert first.provider_query["per-page"] == "1"
    assert first.provider_query["cursor"] == "*"
    assert second.next_cursor is None
    assert second.records[0].title == "第二页录制文献"

    with pytest.raises(LiteratureProviderError) as exc_info:
        asyncio.run(provider.search(_query(), page_size=201))
    assert exc_info.value.code == ProviderErrorCode.INVALID_QUERY


def test_recorded_missing_request_is_explicitly_unavailable() -> None:
    provider = PyAlexOpenAlexProvider(transport=RecordedOpenAlexTransport({}))

    with pytest.raises(LiteratureProviderError) as exc_info:
        asyncio.run(provider.search(_query()))

    assert exc_info.value.code == ProviderErrorCode.RECORDED_RESPONSE_MISSING
    assert exc_info.value.retryable is False


def test_schema_change_fails_closed_without_returning_partial_records() -> None:
    provider = PyAlexOpenAlexProvider(
        transport=RecordedOpenAlexTransport(
            {"search:*": {"meta": {"count": 1, "next_cursor": None}}}
        )
    )

    with pytest.raises(LiteratureProviderError) as exc_info:
        asyncio.run(provider.search(_query()))

    assert exc_info.value.code == ProviderErrorCode.SCHEMA_CHANGED
    assert exc_info.value.retryable is False


def test_http_transport_retries_429_once_then_succeeds() -> None:
    calls = 0
    sleeps: list[float] = []

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(429, headers={"Retry-After": "0"})
        return httpx.Response(
            200,
            json={"meta": {"count": 0, "next_cursor": None}, "results": []},
        )

    async def record_sleep(seconds: float) -> None:
        sleeps.append(seconds)

    async def run() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            transport = HttpxOpenAlexTransport(
                client=client, max_attempts=2, sleep=record_sleep
            )
            response = await transport.get_json(
                request_key="search:*",
                url="https://api.openalex.org/works",
                params=(),
                headers={},
            )
            assert response.attempts == 2

    asyncio.run(run())
    assert calls == 2
    assert sleeps == [0.0]


def test_http_transport_normalizes_timeout_rate_limit_offline_and_schema() -> None:
    async def assert_error(
        handler: httpx.MockTransport, expected: ProviderErrorCode
    ) -> None:
        async with httpx.AsyncClient(transport=handler) as client:
            transport = HttpxOpenAlexTransport(client=client, max_attempts=1)
            with pytest.raises(LiteratureProviderError) as exc_info:
                await transport.get_json(
                    request_key="search:*",
                    url="https://api.openalex.org/works",
                    params=(),
                    headers={},
                )
            assert exc_info.value.code == expected

    def timeout_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("forced timeout", request=request)

    def offline_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("forced offline", request=request)

    asyncio.run(
        assert_error(httpx.MockTransport(timeout_handler), ProviderErrorCode.TIMEOUT)
    )
    asyncio.run(
        assert_error(httpx.MockTransport(offline_handler), ProviderErrorCode.OFFLINE)
    )
    asyncio.run(
        assert_error(
            httpx.MockTransport(lambda request: httpx.Response(429)),
            ProviderErrorCode.RATE_LIMITED,
        )
    )
    asyncio.run(
        assert_error(
            httpx.MockTransport(lambda request: httpx.Response(401)),
            ProviderErrorCode.AUTHENTICATION_FAILED,
        )
    )
    asyncio.run(
        assert_error(
            httpx.MockTransport(
                lambda request: httpx.Response(200, content=b"not-json")
            ),
            ProviderErrorCode.SCHEMA_CHANGED,
        )
    )


def test_get_by_doi_and_verification_reuse_recorded_normalization() -> None:
    provider = PyAlexOpenAlexProvider(
        transport=RecordedOpenAlexTransport(_recordings())
    )

    record = asyncio.run(provider.get_by_doi("https://doi.org/10.1000/RECA.Sample"))
    assert record is not None
    assert record.normalized_doi == "10.1000/reca.sample"
    verification = asyncio.run(provider.verify(record))
    assert verification.verified is True
    assert verification.matched_source_identifier == record.source_identifier


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("https://doi.org/10.1000/ABC", "10.1000/abc"),
        ("http://doi.org/10.1000/ABC", "10.1000/abc"),
        ("doi:10.1000/ABC", "10.1000/abc"),
        (" 10.1000/ABC ", "10.1000/abc"),
        ("", None),
        (None, None),
    ],
)
def test_normalize_doi(source: str | None, expected: str | None) -> None:
    assert normalize_doi(source) == expected
