from __future__ import annotations

import json
import uuid
from datetime import timedelta
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, func, select

from app import crud
from app.adapters.literature import (
    LiteratureProviderError,
    ProviderErrorCode,
    PyAlexOpenAlexProvider,
    RecordedOpenAlexTransport,
)
from app.api.errors import ContractError
from app.api.routes import literature as route_module
from app.jobs import service as job_service
from app.literature import service
from app.literature.normalization import normalize_doi, normalize_title
from app.models import (
    Job,
    LiteratureDecisionStatus,
    LiteratureRecord,
    LiteratureSearchCandidate,
    LiteratureSearchRun,
    LiteratureSourceType,
    LiteratureVerificationStatus,
    UserCreate,
    get_datetime_utc,
)
from tests.api.routes.test_research_questions import create_project, create_question
from tests.utils.user import user_authentication_headers
from tests.utils.utils import random_lower_string

_FIXTURE = (
    Path(__file__).resolve().parents[2]
    / "fixtures"
    / "openalex"
    / "works_recorded.json"
)


class FakeDispatcher:
    def __init__(self) -> None:
        self.job_ids: list[uuid.UUID] = []

    def dispatch(self, *, job_id: uuid.UUID, task_id: str) -> None:
        assert task_id
        self.job_ids.append(job_id)


class FailingProvider:
    def __init__(self, code: ProviderErrorCode) -> None:
        self.code = code

    async def search(self, *_args: Any, **_kwargs: Any) -> Any:
        raise LiteratureProviderError(
            code=self.code,
            message="Forced Provider failure.",
            retryable=True,
        )


def _recorded_provider(
    recordings: dict[str, dict[str, Any]] | None = None,
) -> PyAlexOpenAlexProvider:
    if recordings is None:
        fixture = json.loads(_FIXTURE.read_text(encoding="utf-8"))
        recordings = fixture["recordings"]
    return PyAlexOpenAlexProvider(transport=RecordedOpenAlexTransport(recordings))


def _create_plan(client: TestClient, headers: dict[str, str], project_id: str) -> str:
    question = create_question(client, headers, project_id)
    response = client.post(
        f"/api/v1/projects/{project_id}/query-plans",
        headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        json={
            "research_question_version_id": question["current_version"]["id"],
            "english_terms": ["research workflow"],
            "boolean_query": '"research workflow"',
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]["id"]


def _request_search(
    client: TestClient, headers: dict[str, str], plan_id: str
) -> dict[str, Any]:
    response = client.post(
        f"/api/v1/query-plans/{plan_id}/search-runs",
        headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"page_size": 25, "use_cache": True},
    )
    assert response.status_code == 202, response.text
    return response.json()["data"]


def _execute_search(
    db: Session,
    accepted: dict[str, Any],
    provider: Any,
) -> LiteratureSearchRun:
    job_id = uuid.UUID(accepted["job"]["id"])
    claim = job_service.claim_job(
        db,
        job_id=job_id,
        worker_id="literature-test-worker",
        engine="pytest",
        engine_version="1",
    )
    assert claim is not None
    job = db.get(Job, job_id)
    assert job is not None
    return service.execute_search_job(
        db,
        job=job,
        run_id=claim.run_id,
        provider=provider,
    )


@pytest.mark.no_database
@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("https://doi.org/10.1000/ABC", "10.1000/abc"),
        ("doi:10.12345/Value.With.Punctuation", "10.12345/value.with.punctuation"),
        ("10.1000", None),
        ("not-a-doi", None),
        ("", None),
    ],
)
def test_literature_normalization_is_deterministic(
    source: str, expected: str | None
) -> None:
    assert normalize_doi(source) == expected
    assert normalize_title("  Full-width：Ｔｉｔｌｅ!  ") == "full width title"


@pytest.mark.no_database
def test_concurrent_doi_constraint_failure_is_retryable_conflict() -> None:
    session = MagicMock(spec=Session)
    session.flush.side_effect = IntegrityError("insert", {}, Exception("unique"))

    with pytest.raises(ContractError) as exc_info:
        service._flush_or_conflict(session)

    assert exc_info.value.status_code == 409
    assert exc_info.value.code == "INVALID_STATE_TRANSITION"
    assert exc_info.value.retryable is True
    session.rollback.assert_called_once_with()


def test_search_candidates_remain_separate_until_explicit_import(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dispatcher = FakeDispatcher()
    monkeypatch.setattr(route_module, "dispatcher", dispatcher)
    project_id = create_project(client, normal_user_token_headers)
    plan_id = _create_plan(client, normal_user_token_headers, project_id)
    accepted = _request_search(client, normal_user_token_headers, plan_id)
    run = _execute_search(db, accepted, _recorded_provider())
    assert run.result_count == 1
    assert run.degraded is True

    results = client.get(
        f"/api/v1/literature-search-runs/{run.id}/results",
        headers=normal_user_token_headers,
    )
    assert results.status_code == 200, results.text
    candidates = results.json()["data"]["results"]
    assert len(candidates) == 1
    assert results.json()["data"]["search_run"]["allowed_actions"] == [
        "literature_search.read",
        "literature_search.import",
    ]
    assert candidates[0]["allowed_actions"] == [
        "literature_candidate.read",
        "literature_candidate.import",
    ]
    before_import = client.get(
        f"/api/v1/projects/{project_id}/literature",
        headers=normal_user_token_headers,
    )
    assert before_import.json()["pagination"]["total"] == 0
    assert before_import.json()["allowed_actions"] == [
        "literature.read",
        "literature.search",
        "literature.import",
        "literature.import_doi",
        "document.upload",
    ]

    imported = client.post(
        f"/api/v1/projects/{project_id}/literature/import",
        headers={
            **normal_user_token_headers,
            "Idempotency-Key": str(uuid.uuid4()),
        },
        json={"search_run_id": str(run.id), "result_ids": [candidates[0]["id"]]},
    )
    assert imported.status_code == 200, imported.text
    literature_id = imported.json()["data"]["imported"][0]["literature_record_id"]
    assert (
        db.exec(
            select(func.count())
            .select_from(LiteratureRecord)
            .where(LiteratureRecord.project_id == project_id)
        ).one()
        == 1
    )
    assert (
        db.exec(select(func.count()).select_from(LiteratureSearchCandidate)).one() == 1
    )

    repeated = client.post(
        f"/api/v1/projects/{project_id}/literature/import",
        headers={
            **normal_user_token_headers,
            "Idempotency-Key": str(uuid.uuid4()),
        },
        json={"search_run_id": str(run.id), "result_ids": [candidates[0]["id"]]},
    )
    assert repeated.status_code == 200
    assert repeated.json()["data"]["imported"][0] == {
        "candidate_id": candidates[0]["id"],
        "literature_record_id": literature_id,
        "matched_existing": True,
    }

    detail = client.get(
        f"/api/v1/literature/{literature_id}", headers=normal_user_token_headers
    )
    assert detail.json()["data"]["allowed_actions"] == [
        "literature.read",
        "document.upload",
    ]

    reviewer_password = random_lower_string()
    reviewer = crud.create_user(
        session=db,
        user_create=UserCreate(
            email=f"{random_lower_string()}@example.com",
            password=reviewer_password,
        ),
    )
    added = client.post(
        f"/api/v1/projects/{project_id}/members",
        headers={
            **normal_user_token_headers,
            "Idempotency-Key": str(uuid.uuid4()),
        },
        json={"user_id": str(reviewer.id), "role": "REVIEWER"},
    )
    assert added.status_code == 201
    reviewer_headers = user_authentication_headers(
        client=client, email=reviewer.email, password=reviewer_password
    )
    reviewer_list = client.get(
        f"/api/v1/projects/{project_id}/literature", headers=reviewer_headers
    )
    reviewer_results = client.get(
        f"/api/v1/literature-search-runs/{run.id}/results",
        headers=reviewer_headers,
    )
    assert reviewer_list.json()["allowed_actions"] == ["literature.read"]
    assert reviewer_list.json()["data"][0]["allowed_actions"] == ["literature.read"]
    assert reviewer_results.json()["data"]["search_run"]["allowed_actions"] == [
        "literature_search.read"
    ]
    assert reviewer_results.json()["data"]["results"][0]["allowed_actions"] == [
        "literature_candidate.read"
    ]

    outsider_password = random_lower_string()
    outsider = crud.create_user(
        session=db,
        user_create=UserCreate(
            email=f"{random_lower_string()}@example.com",
            password=outsider_password,
        ),
    )
    outsider_headers = user_authentication_headers(
        client=client, email=outsider.email, password=outsider_password
    )
    hidden_results = client.get(
        f"/api/v1/literature-search-runs/{run.id}/results",
        headers=outsider_headers,
    )
    hidden_record = client.get(
        f"/api/v1/literature/{literature_id}", headers=outsider_headers
    )
    assert hidden_results.status_code == hidden_record.status_code == 404


def test_doi_import_is_project_scoped_and_title_collision_requires_review(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(service, "PyAlexOpenAlexProvider", lambda: _recorded_provider())
    first_project = create_project(client, normal_user_token_headers)
    path = f"/api/v1/projects/{first_project}/literature/import-doi"
    invalid = client.post(
        path,
        headers={
            **normal_user_token_headers,
            "Idempotency-Key": str(uuid.uuid4()),
        },
        json={"doi": "wrong"},
    )
    assert invalid.status_code == 422
    assert invalid.json()["error"]["code"] == "INVALID_DOI"

    first = client.post(
        path,
        headers={
            **normal_user_token_headers,
            "Idempotency-Key": str(uuid.uuid4()),
        },
        json={"doi": "https://doi.org/10.1000/RECA.Sample"},
    )
    duplicate = client.post(
        path,
        headers={
            **normal_user_token_headers,
            "Idempotency-Key": str(uuid.uuid4()),
        },
        json={"doi": "10.1000/reca.sample"},
    )
    assert first.status_code == 201
    assert duplicate.status_code == 200
    assert duplicate.json()["data"]["id"] == first.json()["data"]["id"]

    second_project = create_project(client, normal_user_token_headers)
    cross_project = client.post(
        f"/api/v1/projects/{second_project}/literature/import-doi",
        headers={
            **normal_user_token_headers,
            "Idempotency-Key": str(uuid.uuid4()),
        },
        json={"doi": "10.1000/reca.sample"},
    )
    assert cross_project.status_code == 201
    assert cross_project.json()["data"]["id"] != first.json()["data"]["id"]

    review_project = create_project(client, normal_user_token_headers)
    manual = LiteratureRecord(
        project_id=uuid.UUID(review_project),
        source_type=LiteratureSourceType.MANUAL,
        title="A Recorded Study of Research Workflows",
        normalized_title=normalize_title("A Recorded Study of Research Workflows"),
        verification_status=LiteratureVerificationStatus.UNVERIFIED,
        current_decision=LiteratureDecisionStatus.UNCERTAIN,
    )
    db.add(manual)
    db.commit()
    review = client.post(
        f"/api/v1/projects/{review_project}/literature/import-doi",
        headers={
            **normal_user_token_headers,
            "Idempotency-Key": str(uuid.uuid4()),
        },
        json={"doi": "10.1000/reca.sample"},
    )
    assert review.status_code == 409
    assert review.json()["error"]["code"] == "LITERATURE_DEDUP_REVIEW_REQUIRED"


def test_stale_cache_is_explicit_and_provider_failure_never_fabricates_results(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dispatcher = FakeDispatcher()
    monkeypatch.setattr(route_module, "dispatcher", dispatcher)
    project_id = create_project(client, normal_user_token_headers)
    plan_id = _create_plan(client, normal_user_token_headers, project_id)

    source = _execute_search(
        db,
        _request_search(client, normal_user_token_headers, plan_id),
        _recorded_provider(),
    )
    source.fetched_at = get_datetime_utc() - timedelta(days=2)
    db.add(source)
    db.commit()
    fallback = _execute_search(
        db,
        _request_search(client, normal_user_token_headers, plan_id),
        FailingProvider(ProviderErrorCode.TIMEOUT),
    )
    assert fallback.status.value == "COMPLETED"
    assert fallback.cache_hit is True
    assert fallback.cache_stale is True
    assert fallback.degraded is True
    assert fallback.error_code == ProviderErrorCode.TIMEOUT.value
    assert fallback.result_count == source.result_count == 1

    zero_project = create_project(client, normal_user_token_headers)
    zero_plan = _create_plan(client, normal_user_token_headers, zero_project)
    zero_provider = _recorded_provider(
        {"search:*": {"meta": {"count": 0, "next_cursor": None}, "results": []}}
    )
    zero_run = _execute_search(
        db,
        _request_search(client, normal_user_token_headers, zero_plan),
        zero_provider,
    )
    assert zero_run.result_count == 0
    assert (
        db.exec(
            select(func.count())
            .select_from(LiteratureSearchCandidate)
            .where(LiteratureSearchCandidate.search_run_id == zero_run.id)
        ).one()
        == 0
    )
    assert (
        client.get(
            f"/api/v1/projects/{zero_project}/literature",
            headers=normal_user_token_headers,
        ).json()["pagination"]["total"]
        == 0
    )

    failed_project = create_project(client, normal_user_token_headers)
    failed_plan = _create_plan(client, normal_user_token_headers, failed_project)
    failed_accepted = _request_search(client, normal_user_token_headers, failed_plan)
    with pytest.raises(service.LiteratureSearchExecutionError) as exc_info:
        _execute_search(
            db,
            failed_accepted,
            FailingProvider(ProviderErrorCode.RATE_LIMITED),
        )
    assert exc_info.value.code == ProviderErrorCode.RATE_LIMITED.value
    failed_run = db.get(
        LiteratureSearchRun, uuid.UUID(failed_accepted["search_run"]["id"])
    )
    assert failed_run is not None
    assert failed_run.status.value == "FAILED"
    assert failed_run.result_count == 0
    assert (
        db.exec(
            select(func.count())
            .select_from(LiteratureSearchCandidate)
            .where(LiteratureSearchCandidate.search_run_id == failed_run.id)
        ).one()
        == 0
    )
