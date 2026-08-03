from __future__ import annotations

import json
import uuid
from pathlib import Path

import pytest
from sqlmodel import Session, select

from app.adapters.storage import StorageObjectExists, StorageObjectMissing
from app.api.errors import ContractError
from app.jobs import service as job_service
from app.models import (
    Artifact,
    Job,
    ModelInvocation,
    ModelInvocationStatus,
    ProcessingRun,
    QueryPlan,
    ResearchProject,
)
from app.projects.schemas import ProjectCreate
from app.projects.service import create_project
from app.query_plans import generation, service
from app.query_plans.schemas import QueryPlanCreate, QueryPlanFields, QueryPlanFilters
from app.research_questions.schemas import ResearchQuestionVersionContent
from app.research_questions.service import create_research_question
from tests.utils.user import create_random_user


class FakeDispatcher:
    def __init__(self) -> None:
        self.calls: list[uuid.UUID] = []

    def dispatch(self, *, job_id: uuid.UUID, task_id: str) -> None:
        assert task_id
        self.calls.append(job_id)


class MemoryStorage:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    def put_file_once(
        self, *, object_key: str, path: Path, content_sha256: str, size_bytes: int
    ) -> None:
        if object_key in self.objects:
            raise StorageObjectExists(object_key)
        content = path.read_bytes()
        assert len(content) == size_bytes
        self.objects[object_key] = content

    def download_to_path(self, *, object_key: str, path: Path) -> None:
        if object_key not in self.objects:
            raise StorageObjectMissing(object_key)
        path.write_bytes(self.objects[object_key])

    def presign_download(self, *, object_key: str, expires_seconds: int) -> str:
        return f"memory://{object_key}?expires={expires_seconds}"


def make_context(db: Session, *, topic: str = "生成式AI与师范生学习投入"):
    actor = create_random_user(db)
    created = create_project(
        db,
        actor=actor,
        payload=ProjectCreate(
            name="M2 QueryPlan project",
            project_type="RESEARCH",
            discipline="education",
            research_direction="AI-supported learning",
        ),
        idempotency_key=str(uuid.uuid4()),
    )
    assert created.data is not None
    project = db.get(ResearchProject, uuid.UUID(created.data["id"]))
    assert project is not None
    _, version = create_research_question(
        db,
        actor=actor,
        project_id=project.id,
        content=ResearchQuestionVersionContent(raw_input=topic),
    )
    result = service.create_query_plan_command(
        db,
        actor=actor,
        project_id=project.id,
        payload=QueryPlanCreate(
            research_question_version_id=version.id,
            filters=QueryPlanFilters(
                from_year=2020,
                to_year=2026,
                languages=["zh", "en"],
                work_types=["article"],
                open_access_only=True,
            ),
        ),
        idempotency_key=str(uuid.uuid4()),
    )
    plan = db.get(QueryPlan, uuid.UUID(result.data["id"]))
    assert plan is not None
    return actor, project, version, plan


def claim(db: Session, job: Job) -> ProcessingRun:
    claimed = job_service.claim_job(
        db,
        job_id=job.id,
        worker_id="query-plan-test-worker",
        engine="reca-worker",
        engine_version="test",
    )
    assert claimed is not None
    run = db.get(ProcessingRun, claimed.run_id)
    assert run is not None
    return run


def test_query_plan_draft_create_update_and_project_isolation(db: Session) -> None:
    actor, _, version, plan = make_context(db)
    assert version.status == "DRAFT"
    updated = service.update_query_plan(
        db,
        actor=actor,
        query_plan_id=plan.id,
        expected_lock_version=1,
        fields=QueryPlanFields(
            chinese_terms=["学习投入"],
            english_terms=["student engagement"],
            synonyms={"zh": ["学生投入"], "en": ["learning engagement"]},
            boolean_query='"student engagement"',
        ),
        change_reason="Reviewed bilingual search terms.",
    )
    assert updated["lock_version"] == 2
    assert updated["chinese_terms"] == ["学习投入"]

    other_actor, other_project, _, _ = make_context(db, topic="other topic")
    with pytest.raises(ContractError) as error:
        service.create_query_plan_command(
            db,
            actor=other_actor,
            project_id=other_project.id,
            payload=QueryPlanCreate(research_question_version_id=version.id),
            idempotency_key=str(uuid.uuid4()),
        )
    assert error.value.code == "RESOURCE_NOT_FOUND"


def test_recorded_generation_applies_candidate_without_selecting_provider(
    db: Session,
) -> None:
    actor, project, version, plan = make_context(db)
    dispatcher = FakeDispatcher()
    result = generation.request_generation_job(
        db,
        actor=actor,
        query_plan_id=plan.id,
        idempotency_key=str(uuid.uuid4()),
        dispatcher=dispatcher,
    )
    job = db.get(Job, uuid.UUID(result.data["id"]))
    assert job is not None and dispatcher.calls == [job.id]
    invocation = db.get(ModelInvocation, job.resource_id)
    assert invocation is not None
    assert invocation.source_ids == [str(plan.id), str(version.id)]
    assert invocation.provider is None
    run = claim(db, job)
    storage = MemoryStorage()
    artifact = generation.execute_generation_job(
        db, job=job, run_id=run.id, storage_backend=storage
    )
    payload = json.loads(storage.objects[artifact.storage_key])
    assert payload["task_type"] == "QUERY_PLAN_GENERATION"
    assert payload["requires_human_review"] is True
    assert "provider" not in payload["result"]
    db.refresh(plan)
    db.refresh(invocation)
    assert invocation.status == ModelInvocationStatus.SUCCEEDED
    assert plan.source_model_invocation_id == invocation.id
    assert plan.lock_version == 2
    assert plan.filters["open_access_only"] is True  # type: ignore[index]
    assert plan.english_terms == [
        "generative artificial intelligence",
        "learning engagement",
        "pre-service teachers",
    ]
    assert (
        db.exec(select(Artifact).where(Artifact.project_id == project.id)).first()
        is not None
    )


def test_generation_degrades_without_mutating_plan_for_unmatched_input(
    db: Session,
) -> None:
    actor, project, _, plan = make_context(db, topic="unmatched research question")
    result = generation.request_generation_job(
        db,
        actor=actor,
        query_plan_id=plan.id,
        idempotency_key=str(uuid.uuid4()),
        dispatcher=FakeDispatcher(),
    )
    job = db.get(Job, uuid.UUID(result.data["id"]))
    assert job is not None
    invocation = db.get(ModelInvocation, job.resource_id)
    assert invocation is not None
    run = claim(db, job)
    with pytest.raises(generation.QueryPlanGenerationError) as error:
        generation.execute_generation_job(
            db, job=job, run_id=run.id, storage_backend=MemoryStorage()
        )
    assert error.value.code == "MODEL_CAPABILITY_UNAVAILABLE"
    db.refresh(plan)
    db.refresh(invocation)
    assert plan.lock_version == 1
    assert plan.source_model_invocation_id is None
    assert invocation.status == ModelInvocationStatus.FAILED
    assert (
        db.exec(select(Artifact).where(Artifact.project_id == project.id)).first()
        is None
    )


def test_generation_schema_failure_preserves_business_table(
    db: Session, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    actor, _, _, plan = make_context(db)
    invalid = json.loads(
        (
            generation.FIXTURE_DIRECTORY / "query-plan-generation-recorded-v1.json"
        ).read_text(encoding="utf-8")
    )
    invalid["provider"] = "OpenAlex"
    fixture_path = tmp_path / "invalid.json"
    fixture_path.write_text(json.dumps(invalid), encoding="utf-8")
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "fixture_manifest_version": "1.0",
                "fixtures": [
                    {
                        "fixture_id": "invalid-query-plan",
                        "mode": "RECORDED",
                        "output_schema": "QueryPlanGenerationOutput@1.0",
                        "path": fixture_path.name,
                        "output_hash": generation.model_service.canonical_hash(invalid),
                        "recording_version": "1.0",
                        "recording_license_status": "INTERNAL_GOLDEN_FIXTURE",
                        "recording_redaction_status": "REVIEWED_NO_PERSONAL_DATA",
                        "input_match": {
                            "research_question": "生成式AI与师范生学习投入"
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(generation, "FIXTURE_DIRECTORY", tmp_path)
    monkeypatch.setattr(generation, "FIXTURE_MANIFEST", manifest_path)
    result = generation.request_generation_job(
        db,
        actor=actor,
        query_plan_id=plan.id,
        idempotency_key=str(uuid.uuid4()),
        dispatcher=FakeDispatcher(),
        fixture_id="invalid-query-plan",
    )
    job = db.get(Job, uuid.UUID(result.data["id"]))
    assert job is not None
    run = claim(db, job)
    with pytest.raises(generation.QueryPlanGenerationError) as error:
        generation.execute_generation_job(
            db, job=job, run_id=run.id, storage_backend=MemoryStorage()
        )
    assert error.value.code == "MODEL_OUTPUT_SCHEMA_INVALID"
    db.refresh(plan)
    assert plan.lock_version == 1
    assert plan.source_model_invocation_id is None
