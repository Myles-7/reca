from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from pydantic import ValidationError
from sqlmodel import Session, select

from app.adapters.storage import ObjectStorage, StorageError
from app.agents import service as model_service
from app.agents.prompts import get_prompt_contract
from app.api.errors import ContractError
from app.artifacts import service as artifact_service
from app.jobs import service as job_service
from app.models import (
    Artifact,
    ArtifactType,
    AuditActorType,
    AuditLog,
    AuditOutcome,
    Job,
    JobTaskType,
    ModelDataAccessLevel,
    ModelInvocation,
    ModelInvocationStatus,
    QueryPlan,
    QueryPlanStatus,
    ResearchQuestionVersion,
    ResearchQuestionVersionStatus,
    User,
    get_datetime_utc,
)
from app.projects import service as project_service
from app.query_plans.ai_schemas import (
    QueryPlanGenerationEnvelope,
    QueryPlanGenerationInput,
    QueryPlanGenerationOutput,
)
from app.research_questions.ai_schemas import (
    AIModelMetadata,
    ConfidenceLabel,
)

PROMPT_ID = "query-plan-generation"
PROMPT_VERSION = "1.0.0"
TASK_TYPE = "QUERY_PLAN_GENERATION"
FIXTURE_DIRECTORY = Path(__file__).with_name("fixtures")
FIXTURE_MANIFEST = FIXTURE_DIRECTORY / "manifest.json"
DEFAULT_RECORDED_FIXTURE = "query-plan-generation-recorded-v1"


class QueryPlanGenerationError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class FixtureContract:
    fixture_id: str
    mode: model_service.ModelExecutionMode
    output_schema: str
    path: Path
    output_hash: str
    recording_version: str | None = None
    recording_license_status: str | None = None
    recording_redaction_status: str | None = None
    input_match: dict[str, Any] | None = None


def load_fixture_contract(fixture_id: str) -> FixtureContract:
    try:
        manifest = json.loads(FIXTURE_MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise QueryPlanGenerationError(
            "MODEL_FIXTURE_INVALID", "QueryPlan fixture manifest is invalid."
        ) from exc
    if manifest.get("fixture_manifest_version") != "1.0":
        raise QueryPlanGenerationError(
            "MODEL_FIXTURE_INVALID", "QueryPlan fixture manifest version is invalid."
        )
    entry = next(
        (
            item
            for item in manifest.get("fixtures", [])
            if isinstance(item, dict) and item.get("fixture_id") == fixture_id
        ),
        None,
    )
    if entry is None:
        raise QueryPlanGenerationError(
            "MODEL_FIXTURE_INVALID", "QueryPlan fixture is not registered."
        )
    try:
        return FixtureContract(
            fixture_id=fixture_id,
            mode=model_service.ModelExecutionMode(entry["mode"]),
            output_schema=str(entry["output_schema"]),
            path=FIXTURE_DIRECTORY / str(entry["path"]),
            output_hash=str(entry["output_hash"]),
            recording_version=entry.get("recording_version"),
            recording_license_status=entry.get("recording_license_status"),
            recording_redaction_status=entry.get("recording_redaction_status"),
            input_match=entry.get("input_match"),
        )
    except (KeyError, ValueError, TypeError) as exc:
        raise QueryPlanGenerationError(
            "MODEL_FIXTURE_INVALID", "QueryPlan fixture registration is invalid."
        ) from exc


def _source_resolver(
    session: Session, source_id: uuid.UUID
) -> model_service.SourceReference | None:
    plan = session.get(QueryPlan, source_id)
    if plan is not None:
        return model_service.SourceReference(
            source_id=plan.id, project_id=plan.project_id, source_type="QueryPlan"
        )
    version = session.get(ResearchQuestionVersion, source_id)
    if version is not None:
        return model_service.SourceReference(
            source_id=version.id,
            project_id=version.project_id,
            source_type="ResearchQuestionVersion",
        )
    return None


def _plan_and_version(
    session: Session, *, query_plan_id: uuid.UUID
) -> tuple[QueryPlan, ResearchQuestionVersion]:
    plan = session.get(QueryPlan, query_plan_id)
    if plan is None:
        raise ContractError(
            status_code=404, code="RESOURCE_NOT_FOUND", message="Resource not found."
        )
    version = session.exec(
        select(ResearchQuestionVersion).where(
            ResearchQuestionVersion.id == plan.research_question_version_id,
            ResearchQuestionVersion.project_id == plan.project_id,
        )
    ).first()
    if version is None:
        raise ContractError(
            status_code=404, code="RESOURCE_NOT_FOUND", message="Resource not found."
        )
    return plan, version


def _build_input(
    *, plan: QueryPlan, version: ResearchQuestionVersion
) -> QueryPlanGenerationInput:
    question = (version.normalized_question or version.raw_input).strip()
    return QueryPlanGenerationInput(
        query_plan_id=plan.id,
        query_plan_lock_version=plan.lock_version,
        research_question_version_id=version.id,
        research_question=question,
        current_filters=plan.filters,
    )


def request_generation_job(
    session: Session,
    *,
    actor: User,
    query_plan_id: uuid.UUID,
    idempotency_key: str,
    dispatcher: job_service.JobDispatcher,
    mode: model_service.ModelExecutionMode = model_service.ModelExecutionMode.RECORDED,
    fixture_id: str = DEFAULT_RECORDED_FIXTURE,
) -> project_service.OperationResult:
    plan, version = _plan_and_version(session, query_plan_id=query_plan_id)
    project_service.authorize_project(
        session, project_id=plan.project_id, actor=actor, action="project.update"
    )
    if plan.status != QueryPlanStatus.DRAFT:
        raise ContractError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="Only a DRAFT QueryPlan may be generated.",
        )
    if version.status == ResearchQuestionVersionStatus.SUPERSEDED:
        raise ContractError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="A superseded ResearchQuestionVersion cannot generate a QueryPlan.",
        )
    generation_input = _build_input(plan=plan, version=version)
    digest = project_service.request_hash(generation_input)
    path = "/api/v1/query-plans/{query_plan_id}/generate"
    replay = project_service._replay_or_conflict(
        session,
        actor_id=actor.id,
        project_id=plan.project_id,
        method="POST",
        path_template=path,
        key=idempotency_key,
        payload_hash=digest,
    )
    if replay is not None:
        return replay
    fixture = load_fixture_contract(fixture_id)
    if fixture.mode != mode or fixture.output_schema != "QueryPlanGenerationOutput@1.0":
        raise ContractError(
            status_code=409,
            code="MODEL_FIXTURE_INVALID",
            message="The configured QueryPlan fixture does not match the execution mode.",
        )
    prompt = get_prompt_contract(PROMPT_ID, PROMPT_VERSION)
    invocation = model_service.create_model_invocation(
        session,
        command=model_service.InvocationCreate(
            project_id=plan.project_id,
            authorization_actor=actor,
            actor_type=AuditActorType.USER,
            actor_id=str(actor.id),
            task_type=TASK_TYPE,
            prompt_id=prompt.prompt_id,
            prompt_version=prompt.prompt_version,
            prompt_content_hash=prompt.content_hash,
            input_schema_name=prompt.input_schema.name,
            input_schema_version=prompt.input_schema.version,
            output_schema_name=prompt.output_schema.name,
            output_schema_version=prompt.output_schema.version,
            requested_data_access_level=ModelDataAccessLevel.REDACTED_CONTENT,
            max_allowed_data_access_level=ModelDataAccessLevel.REDACTED_CONTENT,
            effective_data_access_level=ModelDataAccessLevel.REDACTED_CONTENT,
            source_ids=(plan.id, version.id),
            sanitized_input=generation_input.model_dump(mode="json"),
            mode=mode,
            fixture_id=fixture.fixture_id
            if mode == model_service.ModelExecutionMode.MOCK
            else None,
            recording_id=fixture.fixture_id
            if mode == model_service.ModelExecutionMode.RECORDED
            else None,
            recording_version=fixture.recording_version,
            recording_hash=fixture.output_hash,
            recording_license_status=fixture.recording_license_status,
            recording_redaction_status=fixture.recording_redaction_status,
            execution_metadata={
                "query_plan_id": str(plan.id),
                "research_question_version_id": str(version.id),
                "query_plan_lock_version": plan.lock_version,
                "fixture_id": fixture.fixture_id,
            },
        ),
        source_resolver=_source_resolver,
    )
    job = job_service.create_job(
        session,
        project_id=plan.project_id,
        command=job_service.JobCreate(
            task_type=JobTaskType.QUERY_PLAN_GENERATION,
            resource_type="model_invocation",
            resource_id=invocation.id,
            idempotency_key=idempotency_key,
            requested_by_user_id=actor.id,
            max_retries=2,
            retryable=True,
        ),
    )
    project_service._commit(session)
    dispatched = job_service.dispatch_job(session, job_id=job.id, dispatcher=dispatcher)
    result = project_service.OperationResult(
        data=job_service.job_data(session, dispatched), status_code=202
    )
    project_service._store_idempotency(
        session,
        actor_id=actor.id,
        project_id=plan.project_id,
        method="POST",
        path_template=path,
        key=idempotency_key,
        payload_hash=digest,
        result=result,
    )
    project_service._commit(session)
    return result


def _fail_invocation(
    session: Session, *, invocation: ModelInvocation, code: str, impact: str
) -> None:
    model_service.fail_model_invocation(
        session,
        invocation_id=invocation.id,
        error_code=code,
        degradation=model_service.DegradationRecord(
            requested_capability=TASK_TYPE,
            primary_provider="configured-model-provider",
            fallback_provider=None,
            reason_code=code,
            impact=impact,
            result_status="UNAVAILABLE",
            user_visible_message=(
                "QueryPlan generation is unavailable; the existing draft was preserved."
            ),
        ),
    )


def execute_generation_job(
    session: Session,
    *,
    job: Job,
    run_id: uuid.UUID,
    storage_backend: ObjectStorage | None = None,
) -> Artifact:
    if job.task_type != JobTaskType.QUERY_PLAN_GENERATION:
        raise QueryPlanGenerationError(
            "JOB_HANDLER_MISMATCH", "Job is not a QueryPlan generation job."
        )
    invocation = session.get(ModelInvocation, job.resource_id)
    if (
        invocation is None
        or invocation.project_id != job.project_id
        or invocation.status != ModelInvocationStatus.PENDING
    ):
        raise QueryPlanGenerationError(
            "MODEL_INVOCATION_INVALID_STATE",
            "ModelInvocation is not available for QueryPlan generation.",
        )
    execution = (invocation.implementation_metadata or {}).get("execution", {})
    try:
        plan_id = uuid.UUID(str(execution["query_plan_id"]))
        version_id = uuid.UUID(str(execution["research_question_version_id"]))
        expected_lock_version = int(execution["query_plan_lock_version"])
    except (KeyError, TypeError, ValueError) as exc:
        _fail_invocation(
            session,
            invocation=invocation,
            code="MODEL_INPUT_INVALID",
            impact="The governed QueryPlan execution metadata is invalid.",
        )
        raise QueryPlanGenerationError(
            "MODEL_INPUT_INVALID", "QueryPlan generation input is invalid."
        ) from exc
    plan, version = _plan_and_version(session, query_plan_id=plan_id)
    if (
        plan.project_id != job.project_id
        or version.id != version_id
        or invocation.source_ids != [str(plan.id), str(version.id)]
    ):
        _fail_invocation(
            session,
            invocation=invocation,
            code="MODEL_OUTPUT_SOURCE_MISSING",
            impact="The governed QueryPlan sources are missing or cross-project.",
        )
        raise QueryPlanGenerationError(
            "MODEL_OUTPUT_SOURCE_MISSING", "QueryPlan sources are invalid."
        )
    generation_input = _build_input(plan=plan, version=version)
    if (
        generation_input.query_plan_lock_version != expected_lock_version
        or model_service.canonical_hash(generation_input.model_dump(mode="json"))
        != invocation.input_hash
    ):
        _fail_invocation(
            session,
            invocation=invocation,
            code="RESOURCE_VERSION_CONFLICT",
            impact="The QueryPlan changed after generation was requested.",
        )
        raise QueryPlanGenerationError(
            "RESOURCE_VERSION_CONFLICT", "The QueryPlan changed before generation."
        )
    fixture = load_fixture_contract(str(execution.get("fixture_id", "")))
    job_service.set_run_context(
        session,
        job_id=job.id,
        run_id=run_id,
        input_hash=invocation.input_hash,
        parameters={"query_plan_lock_version": expected_lock_version},
        implementation_metadata={
            "model_invocation_id": str(invocation.id),
            "fixture_id": fixture.fixture_id,
            "mode": fixture.mode.value,
        },
    )
    model_service.mark_model_invocation_running(session, invocation_id=invocation.id)
    if fixture.input_match is not None and fixture.input_match != {
        "research_question": generation_input.research_question
    }:
        invocation = session.get(ModelInvocation, invocation.id)
        assert invocation is not None
        _fail_invocation(
            session,
            invocation=invocation,
            code="MODEL_CAPABILITY_UNAVAILABLE",
            impact="No reviewed offline recording matches this research question.",
        )
        raise QueryPlanGenerationError(
            "MODEL_CAPABILITY_UNAVAILABLE",
            "No reviewed recording matches the QueryPlan input.",
        )
    try:
        raw = json.loads(fixture.path.read_text(encoding="utf-8"))
        if model_service.canonical_hash(raw) != fixture.output_hash:
            raise QueryPlanGenerationError(
                "MODEL_RECORDING_HASH_MISMATCH",
                "The reviewed QueryPlan recording hash does not match.",
            )
        output = QueryPlanGenerationOutput.model_validate(raw)
    except QueryPlanGenerationError as exc:
        invocation = session.get(ModelInvocation, invocation.id)
        assert invocation is not None
        _fail_invocation(
            session,
            invocation=invocation,
            code=exc.code,
            impact="The reviewed recording failed its integrity check.",
        )
        raise
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        invocation = session.get(ModelInvocation, invocation.id)
        assert invocation is not None
        _fail_invocation(
            session,
            invocation=invocation,
            code="MODEL_OUTPUT_SCHEMA_INVALID",
            impact="The fixture output did not match the registered Schema.",
        )
        raise QueryPlanGenerationError(
            "MODEL_OUTPUT_SCHEMA_INVALID", "QueryPlan output Schema is invalid."
        ) from exc
    current_open_access = bool((plan.filters or {}).get("open_access_only", False))
    filters = output.filters.model_dump(mode="json")
    filters["open_access_only"] = current_open_access
    plan = session.exec(
        select(QueryPlan).where(QueryPlan.id == plan.id).with_for_update()
    ).one()
    if (
        plan.lock_version != expected_lock_version
        or plan.status != QueryPlanStatus.DRAFT
    ):
        _fail_invocation(
            session,
            invocation=invocation,
            code="RESOURCE_VERSION_CONFLICT",
            impact="The QueryPlan changed before the candidate could be applied.",
        )
        raise QueryPlanGenerationError(
            "RESOURCE_VERSION_CONFLICT", "The QueryPlan changed before apply."
        )
    envelope = QueryPlanGenerationEnvelope(
        result=output,
        source_ids=[plan.id, version.id],
        confidence=0.82,
        confidence_label=ConfidenceLabel.HIGH,
        limitations=list(output.limitations),
        warnings=[],
        requires_human_review=True,
        review_reasons=[
            "AI-generated query terms are editable suggestions and do not execute retrieval."
        ],
        generated_at=get_datetime_utc(),
        model_metadata=AIModelMetadata(
            model_invocation_id=invocation.id,
            provider="deterministic-fixture",
            model=fixture.fixture_id,
            prompt_version=PROMPT_VERSION,
        ),
    )
    try:
        artifact = artifact_service.create_generated_json_artifact(
            session,
            project_id=plan.project_id,
            payload=envelope.model_dump(mode="json"),
            filename=f"query-plan-generation-{invocation.id}.json",
            artifact_type=ArtifactType.MODEL_OUTPUT,
            metadata={
                "schema_name": "QueryPlanGenerationEnvelope",
                "schema_version": "1.0",
                "query_plan_id": str(plan.id),
                "research_question_version_id": str(version.id),
                "model_invocation_id": str(invocation.id),
                "processing_run_id": str(run_id),
                "mode": fixture.mode.value,
            },
            storage_backend=storage_backend,
        )
    except StorageError as exc:
        invocation = session.get(ModelInvocation, invocation.id)
        assert invocation is not None
        _fail_invocation(
            session,
            invocation=invocation,
            code="MODEL_OUTPUT_PERSISTENCE_FAILED",
            impact="Validated QueryPlan output could not be stored.",
        )
        raise QueryPlanGenerationError(
            "MODEL_OUTPUT_PERSISTENCE_FAILED", "QueryPlan output storage failed."
        ) from exc
    plan.chinese_terms = output.chinese_terms.core
    plan.english_terms = output.english_terms.core
    plan.synonyms = {
        "zh": output.chinese_terms.synonyms,
        "en": output.english_terms.synonyms,
    }
    plan.object_terms = {
        "zh": output.chinese_terms.object_terms,
        "en": output.english_terms.object_terms,
    }
    plan.method_terms = {
        "zh": output.chinese_terms.method_terms,
        "en": output.english_terms.method_terms,
    }
    plan.boolean_query = output.boolean_query
    plan.filters = filters
    plan.limitations = output.limitations
    plan.source_model_invocation_id = invocation.id
    plan.lock_version += 1
    plan.updated_at = get_datetime_utc()
    session.add(plan)
    session.add(
        AuditLog(
            project_id=plan.project_id,
            actor_type=AuditActorType.SYSTEM,
            actor_id="query-plan-generation",
            action="QUERY_PLAN_AI_SUGGESTION_APPLIED",
            object_type="query_plan",
            object_id=plan.id,
            after_snapshot={
                "lock_version": plan.lock_version,
                "model_invocation_id": str(invocation.id),
                "artifact_id": str(artifact.id),
                "provider_selected": False,
            },
            job_id=job.id,
            request_id=invocation.request_id,
            outcome=AuditOutcome.SUCCEEDED,
        )
    )
    model_service.complete_model_invocation(
        session,
        invocation_id=invocation.id,
        sanitized_output=cast(dict[str, Any], raw),
    )
    return artifact
