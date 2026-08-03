from __future__ import annotations

import asyncio
import hashlib
import json
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime
from enum import StrEnum
from typing import Any, Literal, Protocol, cast
from urllib.parse import parse_qsl, urlsplit, urlunsplit

import httpx
from pyalex import Works  # type: ignore[import-untyped]
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.core.config import settings
from app.literature.normalization import normalize_doi
from app.models import QueryPlan

PYALEX_ADOPTED_VERSION = "0.21"
PYALEX_UPSTREAM_COMMIT = "875c708cbb6e449feebc46d2a7a26af8ed8b2fdd"
OPENALEX_NORMALIZATION_VERSION = "openalex-work-v1"
OPENALEX_PROVIDER_NAME = "OPENALEX_PYALEX"
OPENALEX_MAX_PAGE_SIZE = 200

_WORK_SELECT_FIELDS = (
    "id",
    "doi",
    "title",
    "publication_date",
    "publication_year",
    "type",
    "authorships",
    "primary_location",
    "locations",
    "abstract_inverted_index",
    "topics",
    "open_access",
)


class _FrozenDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class LiteratureQueryFiltersDTO(_FrozenDTO):
    from_year: int | None = Field(default=None, ge=1, le=9999)
    to_year: int | None = Field(default=None, ge=1, le=9999)
    languages: tuple[str, ...] = ()
    work_types: tuple[str, ...] = ()
    open_access_only: bool = False


class LiteratureQueryPlanDTO(_FrozenDTO):
    project_id: str
    query_plan_id: str
    chinese_terms: tuple[str, ...] = ()
    english_terms: tuple[str, ...] = ()
    synonyms: dict[str, tuple[str, ...]] = Field(default_factory=dict)
    object_terms: dict[str, tuple[str, ...]] = Field(default_factory=dict)
    method_terms: dict[str, tuple[str, ...]] = Field(default_factory=dict)
    boolean_query: str | None = None
    filters: LiteratureQueryFiltersDTO = Field(
        default_factory=LiteratureQueryFiltersDTO
    )

    @classmethod
    def from_query_plan(cls, query_plan: QueryPlan) -> LiteratureQueryPlanDTO:
        filters = LiteratureQueryFiltersDTO.model_validate(query_plan.filters or {})
        return cls(
            project_id=str(query_plan.project_id),
            query_plan_id=str(query_plan.id),
            chinese_terms=tuple(query_plan.chinese_terms or ()),
            english_terms=tuple(query_plan.english_terms or ()),
            synonyms=_tuple_groups(query_plan.synonyms),
            object_terms=_tuple_groups(query_plan.object_terms),
            method_terms=_tuple_groups(query_plan.method_terms),
            boolean_query=query_plan.boolean_query,
            filters=filters,
        )


class LiteratureAuthorDTO(_FrozenDTO):
    source_identifier: str | None = None
    display_name: str
    orcid: str | None = None
    institutions: tuple[str, ...] = ()


class LiteratureLocationDTO(_FrozenDTO):
    landing_page_url: str | None = None
    pdf_url: str | None = None
    source_identifier: str | None = None
    source_name: str | None = None
    version: str | None = None
    license: str | None = None
    is_open_access: bool | None = None


class LiteratureRecordDTO(_FrozenDTO):
    provider: str = OPENALEX_PROVIDER_NAME
    source_identifier: str
    source_doi: str | None = None
    normalized_doi: str | None = None
    title: str
    publication_date: date | None = None
    publication_year: int | None = None
    work_type: str | None = None
    authors: tuple[LiteratureAuthorDTO, ...] = ()
    source_name: str | None = None
    abstract: str | None = None
    topics: tuple[str, ...] = ()
    open_access_status: str | None = None
    is_open_access: bool | None = None
    candidate_locations: tuple[LiteratureLocationDTO, ...] = ()
    raw_source_data: dict[str, Any]
    normalization_version: str = OPENALEX_NORMALIZATION_VERSION


class ProviderSnapshotDTO(_FrozenDTO):
    provider: str = OPENALEX_PROVIDER_NAME
    source_url: str
    retrieved_at: datetime
    sha256: str
    raw_response: dict[str, Any]


class LiteratureSearchPageDTO(_FrozenDTO):
    project_id: str
    query_plan_id: str
    records: tuple[LiteratureRecordDTO, ...]
    next_cursor: str | None
    provider_query: dict[str, Any]
    snapshot: ProviderSnapshotDTO
    transport_mode: Literal["LIVE", "RECORDED"]
    degraded: bool
    limitations: tuple[str, ...] = ()
    implementation_metadata: dict[str, Any]


class LiteratureVerificationResult(_FrozenDTO):
    verified: bool
    matched_source_identifier: str | None = None
    matched_doi: str | None = None
    limitations: tuple[str, ...] = ()


class ProviderErrorCode(StrEnum):
    INVALID_QUERY = "INVALID_QUERY"
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    NOT_FOUND = "NOT_FOUND"
    TIMEOUT = "TIMEOUT"
    RATE_LIMITED = "RATE_LIMITED"
    OFFLINE = "OFFLINE"
    UPSTREAM_ERROR = "UPSTREAM_ERROR"
    SCHEMA_CHANGED = "SCHEMA_CHANGED"
    RECORDED_RESPONSE_MISSING = "RECORDED_RESPONSE_MISSING"


class LiteratureProviderError(Exception):
    def __init__(
        self,
        *,
        code: ProviderErrorCode,
        message: str,
        retryable: bool,
        upstream_status: int | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable
        self.upstream_status = upstream_status


class LiteratureProvider(Protocol):
    async def search(
        self,
        query_plan: LiteratureQueryPlanDTO,
        *,
        cursor: str = "*",
        page_size: int = 25,
    ) -> LiteratureSearchPageDTO: ...

    async def get_by_doi(self, doi: str) -> LiteratureRecordDTO | None: ...

    async def verify(
        self, record: LiteratureRecordDTO
    ) -> LiteratureVerificationResult: ...


@dataclass(frozen=True)
class OpenAlexTransportResponse:
    payload: dict[str, Any]
    mode: Literal["LIVE", "RECORDED"]
    attempts: int
    status_code: int


class OpenAlexTransport(Protocol):
    async def get_json(
        self,
        *,
        request_key: str,
        url: str,
        params: Sequence[tuple[str, str]],
        headers: Mapping[str, str],
    ) -> OpenAlexTransportResponse: ...


class HttpxOpenAlexTransport:
    def __init__(
        self,
        *,
        client: httpx.AsyncClient | None = None,
        max_attempts: int = 2,
        retry_backoff_seconds: float = 0.25,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        self._client = client
        self._max_attempts = max_attempts
        self._retry_backoff_seconds = retry_backoff_seconds
        self._sleep = sleep

    async def get_json(
        self,
        *,
        request_key: str,
        url: str,
        params: Sequence[tuple[str, str]],
        headers: Mapping[str, str],
    ) -> OpenAlexTransportResponse:
        del request_key
        owns_client = self._client is None
        client = self._client or httpx.AsyncClient(
            timeout=httpx.Timeout(
                settings.REQUEST_TIMEOUT_SECONDS,
                connect=settings.CONNECT_TIMEOUT_SECONDS,
            ),
            trust_env=False,
        )
        try:
            for attempt in range(1, self._max_attempts + 1):
                try:
                    response = await client.get(
                        url, params=list(params), headers=headers
                    )
                except httpx.TimeoutException as exc:
                    if attempt < self._max_attempts:
                        await self._sleep(self._retry_backoff_seconds * attempt)
                        continue
                    raise LiteratureProviderError(
                        code=ProviderErrorCode.TIMEOUT,
                        message="OpenAlex request timed out.",
                        retryable=True,
                    ) from exc
                except httpx.NetworkError as exc:
                    raise LiteratureProviderError(
                        code=ProviderErrorCode.OFFLINE,
                        message="OpenAlex is unavailable from this environment.",
                        retryable=True,
                    ) from exc

                if response.status_code == 404:
                    raise LiteratureProviderError(
                        code=ProviderErrorCode.NOT_FOUND,
                        message="OpenAlex resource was not found.",
                        retryable=False,
                        upstream_status=404,
                    )
                if response.status_code in {401, 403}:
                    raise LiteratureProviderError(
                        code=ProviderErrorCode.AUTHENTICATION_FAILED,
                        message="OpenAlex authentication or access was rejected.",
                        retryable=False,
                        upstream_status=response.status_code,
                    )
                if response.status_code == 429:
                    if attempt < self._max_attempts:
                        await self._sleep(
                            _retry_delay(response, attempt, self._retry_backoff_seconds)
                        )
                        continue
                    raise LiteratureProviderError(
                        code=ProviderErrorCode.RATE_LIMITED,
                        message="OpenAlex rate limit was reached.",
                        retryable=True,
                        upstream_status=429,
                    )
                if response.status_code in {500, 502, 503, 504}:
                    if attempt < self._max_attempts:
                        await self._sleep(self._retry_backoff_seconds * attempt)
                        continue
                    raise LiteratureProviderError(
                        code=ProviderErrorCode.UPSTREAM_ERROR,
                        message="OpenAlex returned a temporary upstream error.",
                        retryable=True,
                        upstream_status=response.status_code,
                    )
                if response.status_code >= 400:
                    raise LiteratureProviderError(
                        code=ProviderErrorCode.INVALID_QUERY,
                        message="OpenAlex rejected the provider query.",
                        retryable=False,
                        upstream_status=response.status_code,
                    )
                try:
                    payload = response.json()
                except ValueError as exc:
                    raise LiteratureProviderError(
                        code=ProviderErrorCode.SCHEMA_CHANGED,
                        message="OpenAlex returned non-JSON content.",
                        retryable=False,
                        upstream_status=response.status_code,
                    ) from exc
                if not isinstance(payload, dict):
                    raise LiteratureProviderError(
                        code=ProviderErrorCode.SCHEMA_CHANGED,
                        message="OpenAlex returned an unexpected JSON shape.",
                        retryable=False,
                        upstream_status=response.status_code,
                    )
                return OpenAlexTransportResponse(
                    payload=cast(dict[str, Any], payload),
                    mode="LIVE",
                    attempts=attempt,
                    status_code=response.status_code,
                )
        finally:
            if owns_client:
                await client.aclose()
        raise AssertionError("OpenAlex transport exhausted without a result")


class RecordedOpenAlexTransport:
    def __init__(self, recordings: Mapping[str, Mapping[str, Any]]) -> None:
        self._recordings = recordings

    async def get_json(
        self,
        *,
        request_key: str,
        url: str,
        params: Sequence[tuple[str, str]],
        headers: Mapping[str, str],
    ) -> OpenAlexTransportResponse:
        del url, params, headers
        payload = self._recordings.get(request_key)
        if payload is None:
            raise LiteratureProviderError(
                code=ProviderErrorCode.RECORDED_RESPONSE_MISSING,
                message="No reviewed OpenAlex recording matches this request.",
                retryable=False,
            )
        copied = json.loads(json.dumps(payload, ensure_ascii=True))
        return OpenAlexTransportResponse(
            payload=cast(dict[str, Any], copied),
            mode="RECORDED",
            attempts=1,
            status_code=200,
        )


class _OpenAlexSource(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str | None = None
    display_name: str | None = None


class _OpenAlexLocation(BaseModel):
    model_config = ConfigDict(extra="ignore")
    landing_page_url: str | None = None
    pdf_url: str | None = None
    source: _OpenAlexSource | None = None
    version: str | None = None
    license: str | None = None
    is_oa: bool | None = None


class _OpenAlexAuthor(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str | None = None
    display_name: str = Field(min_length=1)
    orcid: str | None = None


class _OpenAlexInstitution(BaseModel):
    model_config = ConfigDict(extra="ignore")
    display_name: str | None = None


class _OpenAlexAuthorship(BaseModel):
    model_config = ConfigDict(extra="ignore")
    author: _OpenAlexAuthor
    institutions: list[_OpenAlexInstitution] = Field(default_factory=list)


class _OpenAlexTopic(BaseModel):
    model_config = ConfigDict(extra="ignore")
    display_name: str = Field(min_length=1)


class _OpenAlexAccess(BaseModel):
    model_config = ConfigDict(extra="ignore")
    is_oa: bool | None = None
    oa_status: str | None = None


class _OpenAlexWork(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(min_length=1)
    doi: str | None = None
    title: str = Field(min_length=1)
    publication_date: date | None = None
    publication_year: int | None = None
    type: str | None = None
    authorships: list[_OpenAlexAuthorship] = Field(default_factory=list)
    primary_location: _OpenAlexLocation | None = None
    locations: list[_OpenAlexLocation] = Field(default_factory=list)
    abstract_inverted_index: dict[str, list[int]] | None = None
    topics: list[_OpenAlexTopic] = Field(default_factory=list)
    open_access: _OpenAlexAccess | None = None


class _OpenAlexMeta(BaseModel):
    model_config = ConfigDict(extra="ignore")
    count: int = Field(ge=0)
    next_cursor: str | None = None


class _OpenAlexSearchResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    meta: _OpenAlexMeta
    results: list[_OpenAlexWork]


class PyAlexOpenAlexProvider:
    def __init__(
        self,
        *,
        transport: OpenAlexTransport | None = None,
        api_url: str | None = None,
        api_key: str | None = None,
        contact_email: str | None = None,
    ) -> None:
        self._transport = transport or HttpxOpenAlexTransport()
        self._api_url = (api_url or str(settings.OPENALEX_API_URL)).rstrip("/")
        self._api_key = api_key or (
            settings.OPENALEX_API_KEY.get_secret_value()
            if settings.OPENALEX_API_KEY is not None
            else None
        )
        self._contact_email = contact_email or settings.OPENALEX_CONTACT_EMAIL

    async def search(
        self,
        query_plan: LiteratureQueryPlanDTO,
        *,
        cursor: str = "*",
        page_size: int = 25,
    ) -> LiteratureSearchPageDTO:
        if not 1 <= page_size <= OPENALEX_MAX_PAGE_SIZE:
            raise LiteratureProviderError(
                code=ProviderErrorCode.INVALID_QUERY,
                message=f"page_size must be between 1 and {OPENALEX_MAX_PAGE_SIZE}.",
                retryable=False,
            )
        query_text = _query_text(query_plan)
        if not query_text:
            raise LiteratureProviderError(
                code=ProviderErrorCode.INVALID_QUERY,
                message="QueryPlan does not contain searchable terms.",
                retryable=False,
            )
        builder = Works().search(query_text)
        filters = _openalex_filters(query_plan.filters)
        if filters:
            builder = builder.filter(**filters)
        builder = builder.select(list(_WORK_SELECT_FIELDS))
        url, params = self._request_parts(builder.url)
        params.extend((("per-page", str(page_size)), ("cursor", cursor)))
        return await self._search_page(
            request_key=f"search:{cursor}",
            url=url,
            params=params,
            query_plan=query_plan,
        )

    async def get_by_doi(self, doi: str) -> LiteratureRecordDTO | None:
        normalized = normalize_doi(doi)
        if normalized is None:
            raise LiteratureProviderError(
                code=ProviderErrorCode.INVALID_QUERY,
                message="A valid DOI is required.",
                retryable=False,
            )
        builder = Works().filter(doi=normalized).select(list(_WORK_SELECT_FIELDS))
        url, params = self._request_parts(builder.url)
        params.append(("per-page", "1"))
        try:
            response = await self._transport.get_json(
                request_key=f"doi:{normalized}",
                url=url,
                params=params,
                headers=self._headers(),
            )
        except LiteratureProviderError as exc:
            if exc.code == ProviderErrorCode.NOT_FOUND:
                return None
            raise
        parsed = _validate_response(response.payload, response.status_code)
        if not parsed.results:
            return None
        return _normalize_work(parsed.results[0])

    async def verify(self, record: LiteratureRecordDTO) -> LiteratureVerificationResult:
        if record.normalized_doi is None:
            return LiteratureVerificationResult(
                verified=False,
                limitations=(
                    "The candidate has no DOI for deterministic verification.",
                ),
            )
        matched = await self.get_by_doi(record.normalized_doi)
        if matched is None:
            return LiteratureVerificationResult(verified=False)
        return LiteratureVerificationResult(
            verified=(
                matched.source_identifier == record.source_identifier
                and matched.normalized_doi == record.normalized_doi
            ),
            matched_source_identifier=matched.source_identifier,
            matched_doi=matched.normalized_doi,
        )

    async def _search_page(
        self,
        *,
        request_key: str,
        url: str,
        params: list[tuple[str, str]],
        query_plan: LiteratureQueryPlanDTO,
    ) -> LiteratureSearchPageDTO:
        response = await self._transport.get_json(
            request_key=request_key,
            url=url,
            params=params,
            headers=self._headers(),
        )
        parsed = _validate_response(response.payload, response.status_code)
        retrieved_at = datetime.now(UTC)
        canonical = json.dumps(
            response.payload,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        provider_query = _params_dict(params)
        recorded = response.mode == "RECORDED"
        return LiteratureSearchPageDTO(
            project_id=query_plan.project_id,
            query_plan_id=query_plan.query_plan_id,
            records=tuple(_normalize_work(work) for work in parsed.results),
            next_cursor=parsed.meta.next_cursor,
            provider_query=provider_query,
            snapshot=ProviderSnapshotDTO(
                source_url=url,
                retrieved_at=retrieved_at,
                sha256=hashlib.sha256(canonical).hexdigest(),
                raw_response=response.payload,
            ),
            transport_mode=response.mode,
            degraded=recorded,
            limitations=(
                ("Recorded OpenAlex response; results are not live.",)
                if recorded
                else ()
            ),
            implementation_metadata={
                "provider": OPENALEX_PROVIDER_NAME,
                "pyalex_version": PYALEX_ADOPTED_VERSION,
                "pyalex_upstream_commit": PYALEX_UPSTREAM_COMMIT,
                "normalization_version": OPENALEX_NORMALIZATION_VERSION,
                "transport_mode": response.mode,
                "transport_attempts": response.attempts,
                "license": "MIT",
                "openalex_dataset_license": "CC0",
                "linked_full_text_rights": "SEPARATE_REVIEW_REQUIRED",
            },
        )

    def _request_parts(self, pyalex_url: str) -> tuple[str, list[tuple[str, str]]]:
        built = urlsplit(pyalex_url)
        configured = urlsplit(self._api_url)
        path = f"{configured.path.rstrip('/')}{built.path}"
        url = urlunsplit((configured.scheme, configured.netloc, path, "", ""))
        return url, list(parse_qsl(built.query, keep_blank_values=True))

    def _headers(self) -> dict[str, str]:
        headers = {"User-Agent": "RECA/0.1 OpenAlexProvider"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        if self._contact_email:
            headers["From"] = self._contact_email
        return headers


def _tuple_groups(
    value: Mapping[str, Sequence[str]] | None,
) -> dict[str, tuple[str, ...]]:
    if not value:
        return {}
    return {key: tuple(items) for key, items in value.items()}


def _query_text(query_plan: LiteratureQueryPlanDTO) -> str:
    if query_plan.boolean_query:
        return query_plan.boolean_query.strip()
    terms: list[str] = []
    terms.extend(query_plan.english_terms)
    terms.extend(query_plan.chinese_terms)
    for groups in (
        query_plan.synonyms,
        query_plan.object_terms,
        query_plan.method_terms,
    ):
        for values in groups.values():
            terms.extend(values)
    unique: list[str] = []
    seen: set[str] = set()
    for term in terms:
        normalized = term.strip()
        marker = normalized.casefold()
        if normalized and marker not in seen:
            seen.add(marker)
            unique.append(normalized)
    return " ".join(unique)


def _openalex_filters(filters: LiteratureQueryFiltersDTO) -> dict[str, Any]:
    values: dict[str, Any] = {}
    if filters.from_year is not None:
        values["from_publication_date"] = f"{filters.from_year:04d}-01-01"
    if filters.to_year is not None:
        values["to_publication_date"] = f"{filters.to_year:04d}-12-31"
    if filters.languages:
        values["language"] = "|".join(filters.languages)
    if filters.work_types:
        values["type"] = "|".join(filters.work_types)
    if filters.open_access_only:
        values["open_access"] = {"is_oa": True}
    return values


def _params_dict(params: Sequence[tuple[str, str]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in params:
        existing = result.get(key)
        if existing is None:
            result[key] = value
        elif isinstance(existing, list):
            existing.append(value)
        else:
            result[key] = [existing, value]
    return result


def _validate_response(
    payload: Mapping[str, Any], upstream_status: int
) -> _OpenAlexSearchResponse:
    try:
        return _OpenAlexSearchResponse.model_validate(payload)
    except ValidationError as exc:
        raise LiteratureProviderError(
            code=ProviderErrorCode.SCHEMA_CHANGED,
            message="OpenAlex response did not match the reviewed Schema.",
            retryable=False,
            upstream_status=upstream_status,
        ) from exc


def _normalize_work(work: _OpenAlexWork) -> LiteratureRecordDTO:
    locations = tuple(_normalize_location(location) for location in work.locations)
    if not locations and work.primary_location is not None:
        locations = (_normalize_location(work.primary_location),)
    primary_source = (
        work.primary_location.source.display_name
        if work.primary_location is not None
        and work.primary_location.source is not None
        else None
    )
    return LiteratureRecordDTO(
        source_identifier=work.id,
        source_doi=work.doi,
        normalized_doi=normalize_doi(work.doi),
        title=work.title.strip(),
        publication_date=work.publication_date,
        publication_year=work.publication_year,
        work_type=work.type,
        authors=tuple(
            LiteratureAuthorDTO(
                source_identifier=authorship.author.id,
                display_name=authorship.author.display_name,
                orcid=authorship.author.orcid,
                institutions=tuple(
                    institution.display_name
                    for institution in authorship.institutions
                    if institution.display_name
                ),
            )
            for authorship in work.authorships
        ),
        source_name=primary_source,
        abstract=_abstract_text(work.abstract_inverted_index),
        topics=tuple(topic.display_name for topic in work.topics),
        open_access_status=(
            work.open_access.oa_status if work.open_access is not None else None
        ),
        is_open_access=(
            work.open_access.is_oa if work.open_access is not None else None
        ),
        candidate_locations=locations,
        raw_source_data=work.model_dump(mode="json"),
    )


def _normalize_location(location: _OpenAlexLocation) -> LiteratureLocationDTO:
    return LiteratureLocationDTO(
        landing_page_url=location.landing_page_url,
        pdf_url=location.pdf_url,
        source_identifier=location.source.id if location.source else None,
        source_name=location.source.display_name if location.source else None,
        version=location.version,
        license=location.license,
        is_open_access=location.is_oa,
    )


def _abstract_text(inverted: Mapping[str, Sequence[int]] | None) -> str | None:
    if not inverted:
        return None
    positioned = sorted(
        (position, word)
        for word, positions in inverted.items()
        for position in positions
    )
    return " ".join(word for _, word in positioned) or None


def _retry_delay(
    response: httpx.Response, attempt: int, fallback_seconds: float
) -> float:
    retry_after = response.headers.get("Retry-After")
    if retry_after is not None:
        try:
            return min(max(float(retry_after), 0.0), 5.0)
        except ValueError:
            pass
    return fallback_seconds * attempt
