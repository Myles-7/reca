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
    ResearchProject,
    ResearchQuestion,
    ResearchQuestionVersion,
    ResearchQuestionVersionStatus,
    User,
    get_datetime_utc,
)
from app.projects import service as project_service
from app.research_questions.ai_schemas import (
    AIModelMetadata,
    ConfidenceLabel,
    ProjectContextSnapshot,
    ResearchQuestionScopingEnvelope,
    ResearchQuestionScopingInput,
    ResearchQuestionScopingOutput,
    ResearchQuestionScopingStatus,
)

PROMPT_ID = "research-question-scoping"
PROMPT_VERSION = "1.0.0"
TASK_TYPE = "RESEARCH_QUESTION_SCOPING"
SOURCE_TYPE = "ResearchQuestionVersion"
FIXTURE_DIRECTORY = Path(__file__).with_name("fixtures")
FIXTURE_MANIFEST = FIXTURE_DIRECTORY / "manifest.json"
DEFAULT_RECORDED_FIXTURE = "rq-scoping-candidates-recorded-v1"


class ScopingExecutionError(RuntimeError):
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
        raise ScopingExecutionError(
            "MODEL_FIXTURE_INVALID", "Scoping fixture manifest is invalid."
        ) from exc
    if manifest.get("fixture_manifest_version") != "1.0":
        raise ScopingExecutionError(
            "MODEL_FIXTURE_INVALID", "Scoping fixture manifest version is invalid."
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
        raise ScopingExecutionError(
            "MODEL_FIXTURE_INVALID", "Scoping fixture is not registered."
        )
    try:
        contract = FixtureContract(
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
        raise ScopingExecutionError(
            "MODEL_FIXTURE_INVALID", "Scoping fixture contract is invalid."
        ) from exc
    try:
        raw = json.loads(contract.path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ScopingExecutionError(
            "MODEL_FIXTURE_INVALID", "Scoping fixture content is invalid."
        ) from exc
    if model_service.canonical_hash(raw) != contract.output_hash:
        raise ScopingExecutionError(
            "MODEL_RECORDING_HASH_MISMATCH",
            "Scoping fixture content hash does not match its contract.",
        )
    return contract


def _source_resolver(
    session: Session, source_id: uuid.UUID
) -> model_service.SourceReference | None:
    version = session.get(ResearchQuestionVersion, source_id)
    if version is None:
        return None
    return model_service.SourceReference(
        source_id=version.id,
        project_id=version.project_id,
        source_type=SOURCE_TYPE,
    )


def _version_and_project(
    session: Session, *, version_id: uuid.UUID
) -> tuple[ResearchQuestionVersion, ResearchProject]:
    version = session.get(ResearchQuestionVersion, version_id)
    if version is None:
        raise ContractError(
            status_code=404,
            code="RESOURCE_NOT_FOUND",
            message="Resource not found.",
        )
    project = session.get(ResearchProject, version.project_id)
    question = session.get(ResearchQuestion, version.research_question_id)
    if (
        project is None
        or question is None
        or question.project_id != version.project_id
        or question.current_version_id != version.id
    ):
        raise ContractError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="Only the current ResearchQuestionVersion may be scoped.",
        )
    return version, project


def _scoping_round(session: Session, *, version: ResearchQuestionVersion) -> int:
    invocations = session.exec(
        select(ModelInvocation).where(
            ModelInvocation.project_id == version.project_id,
            ModelInvocation.task_type == TASK_TYPE,
        )
    ).all()
    previous = sum(
        str(version.id) in invocation.source_ids for invocation in invocations
    )
    if previous >= 2:
        raise ContractError(
            status_code=409,
            code="SCOPING_ROUND_LIMIT_REACHED",
            message="ResearchQuestion scoping is limited to two rounds per version.",
        )
    return previous + 1


def _build_input(
    *,
    version: ResearchQuestionVersion,
    project: ResearchProject,
    round_number: int,
    max_follow_up_questions: int,
    language: str,
) -> ResearchQuestionScopingInput:
    return ResearchQuestionScopingInput(
        topic=version.raw_input,
        project_context=ProjectContextSnapshot(
            project_id=project.id,
            project_stage=project.current_stage.value,
            discipline=project.discipline,
            research_direction=project.research_direction,
        ),
        allowed_evidence_ids=[],
        round_number=round_number,
        max_follow_up_questions=max_follow_up_questions,
        language=language,
    )


def request_scoping_job(
    session: Session,
    *,
    actor: User,
    version_id: uuid.UUID,
    max_follow_up_questions: int,
    language: str,
    idempotency_key: str,
    dispatcher: job_service.JobDispatcher,
    mode: model_service.ModelExecutionMode = model_service.ModelExecutionMode.RECORDED,
    fixture_id: str = DEFAULT_RECORDED_FIXTURE,
) -> project_service.OperationResult:
    version, project = _version_and_project(session, version_id=version_id)
    project_service.authorize_project(
        session,
        project_id=version.project_id,
        actor=actor,
        action="project.update",
    )
    if version.status not in {
        ResearchQuestionVersionStatus.DRAFT,
        ResearchQuestionVersionStatus.NEEDS_INPUT,
    }:
        raise ContractError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="Only DRAFT or NEEDS_INPUT versions may be scoped.",
        )
    request_payload = {
        "version_id": version.id,
        "max_follow_up_questions": max_follow_up_questions,
        "language": language,
    }
    digest = project_service.request_hash(request_payload)
    path = "/api/v1/research-question-versions/{version_id}/parse"
    replay = project_service._replay_or_conflict(
        session,
        actor_id=actor.id,
        project_id=version.project_id,
        method="POST",
        path_template=path,
        key=idempotency_key,
        payload_hash=digest,
    )
    if replay:
        return replay

    round_number = _scoping_round(session, version=version)
    scoping_input = _build_input(
        version=version,
        project=project,
        round_number=round_number,
        max_follow_up_questions=max_follow_up_questions,
        language=language,
    )
    fixture = load_fixture_contract(fixture_id)
    if (
        fixture.mode != mode
        or fixture.output_schema != "ResearchQuestionScopingOutput@1.0"
    ):
        raise ContractError(
            status_code=409,
            code="MODEL_FIXTURE_INVALID",
            message="The configured scoping fixture does not match the execution mode.",
        )
    prompt = get_prompt_contract(PROMPT_ID, PROMPT_VERSION)
    invocation = model_service.create_model_invocation(
        session,
        command=model_service.InvocationCreate(
            project_id=version.project_id,
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
            source_ids=(version.id,),
            sanitized_input=scoping_input.model_dump(mode="json"),
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
                "round_number": round_number,
                "max_follow_up_questions": max_follow_up_questions,
                "language": language,
                "fixture_id": fixture.fixture_id,
            },
        ),
        source_resolver=_source_resolver,
    )
    job = job_service.create_job(
        session,
        project_id=version.project_id,
        command=job_service.JobCreate(
            task_type=JobTaskType.RESEARCH_QUESTION_SCOPING,
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
        project_id=version.project_id,
        method="POST",
        path_template=path,
        key=idempotency_key,
        payload_hash=digest,
        result=result,
    )
    project_service._commit(session)
    return result


def _replace_source_token(value: Any, source_id: uuid.UUID) -> Any:
    if value == "$SOURCE_ID":
        return str(source_id)
    if isinstance(value, list):
        return [_replace_source_token(item, source_id) for item in value]
    if isinstance(value, dict):
        return {
            key: _replace_source_token(item, source_id) for key, item in value.items()
        }
    return value


def _fail_invocation(
    session: Session,
    *,
    invocation: ModelInvocation,
    code: str,
    impact: str,
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
                "Research question scoping is unavailable; no candidate was saved."
            ),
        ),
    )


def execute_scoping_job(
    session: Session,
    *,
    job: Job,
    run_id: uuid.UUID,
    storage_backend: ObjectStorage | None = None,
) -> Artifact:
    if job.task_type != JobTaskType.RESEARCH_QUESTION_SCOPING:
        raise ScopingExecutionError(
            "JOB_HANDLER_MISMATCH", "Job is not a ResearchQuestion scoping job."
        )
    invocation = session.get(ModelInvocation, job.resource_id)
    if (
        invocation is None
        or invocation.project_id != job.project_id
        or invocation.status != ModelInvocationStatus.PENDING
    ):
        raise ScopingExecutionError(
            "MODEL_INVOCATION_INVALID_STATE",
            "ModelInvocation is not available for scoping.",
        )
    source_ids = [uuid.UUID(value) for value in invocation.source_ids]
    if len(source_ids) != 1:
        _fail_invocation(
            session,
            invocation=invocation,
            code="MODEL_OUTPUT_SOURCE_MISSING",
            impact="The governed ResearchQuestionVersion source is unavailable.",
        )
        raise ScopingExecutionError(
            "MODEL_OUTPUT_SOURCE_MISSING", "Scoping source is missing."
        )
    version, project = _version_and_project(session, version_id=source_ids[0])
    metadata = invocation.implementation_metadata or {}
    execution = metadata.get("execution")
    if not isinstance(execution, dict):
        _fail_invocation(
            session,
            invocation=invocation,
            code="MODEL_FIXTURE_INVALID",
            impact="Execution metadata is unavailable.",
        )
        raise ScopingExecutionError(
            "MODEL_FIXTURE_INVALID", "Scoping execution metadata is invalid."
        )
    scoping_input = _build_input(
        version=version,
        project=project,
        round_number=int(execution.get("round_number", 0)),
        max_follow_up_questions=int(execution.get("max_follow_up_questions", 0)),
        language=str(execution.get("language", "")),
    )
    if (
        model_service.canonical_hash(scoping_input.model_dump(mode="json"))
        != invocation.input_hash
    ):
        _fail_invocation(
            session,
            invocation=invocation,
            code="MODEL_INPUT_HASH_MISMATCH",
            impact="The immutable model input could not be reconstructed.",
        )
        raise ScopingExecutionError(
            "MODEL_INPUT_HASH_MISMATCH", "Scoping input hash does not match."
        )

    fixture_id = str(execution.get("fixture_id", ""))
    fixture = load_fixture_contract(fixture_id)
    job_service.set_run_context(
        session,
        job_id=job.id,
        run_id=run_id,
        input_hash=invocation.input_hash,
        parameters={
            "round_number": scoping_input.round_number,
            "max_follow_up_questions": scoping_input.max_follow_up_questions,
            "language": scoping_input.language,
        },
        implementation_metadata={
            "model_invocation_id": str(invocation.id),
            "fixture_id": fixture.fixture_id,
            "mode": fixture.mode.value,
        },
    )
    model_service.mark_model_invocation_running(session, invocation_id=invocation.id)
    if fixture.input_match is not None:
        actual_match = {
            "topic": scoping_input.topic,
            "round_number": scoping_input.round_number,
            "language": scoping_input.language,
        }
        if actual_match != fixture.input_match:
            invocation = session.get(ModelInvocation, invocation.id)
            assert invocation is not None
            _fail_invocation(
                session,
                invocation=invocation,
                code="MODEL_CAPABILITY_UNAVAILABLE",
                impact="No reviewed offline recording matches this input.",
            )
            raise ScopingExecutionError(
                "MODEL_CAPABILITY_UNAVAILABLE",
                "No reviewed recording matches the scoping input.",
            )
    raw = json.loads(fixture.path.read_text(encoding="utf-8"))
    substituted = _replace_source_token(raw, version.id)
    try:
        output = ResearchQuestionScopingOutput.model_validate(substituted)
    except ValidationError as exc:
        invocation = session.get(ModelInvocation, invocation.id)
        assert invocation is not None
        _fail_invocation(
            session,
            invocation=invocation,
            code="MODEL_OUTPUT_SCHEMA_INVALID",
            impact="The fixture output did not match the registered Schema.",
        )
        raise ScopingExecutionError(
            "MODEL_OUTPUT_SCHEMA_INVALID", "Scoping output Schema is invalid."
        ) from exc
    if output.source_ids != [version.id] or any(
        source_id != version.id
        for candidate in output.candidates
        for source_id in candidate.supporting_source_ids
    ):
        invocation = session.get(ModelInvocation, invocation.id)
        assert invocation is not None
        _fail_invocation(
            session,
            invocation=invocation,
            code="MODEL_OUTPUT_SOURCE_MISSING",
            impact="Output provenance does not match the governed source.",
        )
        raise ScopingExecutionError(
            "MODEL_OUTPUT_SOURCE_MISSING", "Scoping output source is invalid."
        )
    if len(output.socratic_questions) > scoping_input.max_follow_up_questions or (
        scoping_input.round_number == 2
        and output.status == ResearchQuestionScopingStatus.NEEDS_USER_INPUT
    ):
        invocation = session.get(ModelInvocation, invocation.id)
        assert invocation is not None
        _fail_invocation(
            session,
            invocation=invocation,
            code="MODEL_OUTPUT_SCHEMA_INVALID",
            impact="The scoping round or question limit was exceeded.",
        )
        raise ScopingExecutionError(
            "MODEL_OUTPUT_SCHEMA_INVALID", "Scoping limits were exceeded."
        )

    confidence = (
        0.84
        if output.status == ResearchQuestionScopingStatus.CANDIDATES_READY
        else 0.55
    )
    envelope = ResearchQuestionScopingEnvelope(
        task_type="RESEARCH_QUESTION_SCOPING",
        result=output,
        source_ids=[version.id],
        confidence=confidence,
        confidence_label=(
            ConfidenceLabel.HIGH if confidence >= 0.8 else ConfidenceLabel.MEDIUM
        ),
        limitations=list(output.evidence_gaps),
        warnings=[],
        requires_human_review=True,
        review_reasons=["AI scoping outputs are candidates and require user review."],
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
            project_id=job.project_id,
            payload=envelope.model_dump(mode="json"),
            filename=f"research-question-scoping-{invocation.id}.json",
            artifact_type=ArtifactType.MODEL_OUTPUT,
            metadata={
                "schema_name": "ResearchQuestionScopingEnvelope",
                "schema_version": "1.0",
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
            impact="Validated candidate output could not be stored.",
        )
        raise ScopingExecutionError(
            "MODEL_OUTPUT_PERSISTENCE_FAILED", "Scoping output storage failed."
        ) from exc
    session.add(
        AuditLog(
            project_id=job.project_id,
            actor_type=AuditActorType.SYSTEM,
            actor_id="research-question-scoping",
            action="RESEARCH_QUESTION_SCOPING_CANDIDATE_CREATED",
            object_type="artifact",
            object_id=artifact.id,
            after_snapshot={
                "artifact_id": str(artifact.id),
                "model_invocation_id": str(invocation.id),
                "processing_run_id": str(run_id),
                "status": output.status.value,
                "candidate_count": len(output.candidates),
                "question_count": len(output.socratic_questions),
            },
            job_id=job.id,
            model_invocation_id=invocation.id,
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
