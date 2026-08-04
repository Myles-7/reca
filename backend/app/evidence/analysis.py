from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Protocol, cast

from fastapi.encoders import jsonable_encoder
from pydantic import ValidationError
from sqlmodel import Session, col, select

from app.adapters.model_provider import (
    ModelProviderError,
    OpenAICompatibleJsonProvider,
)
from app.adapters.storage import ObjectStorage, StorageError
from app.agents import service as model_service
from app.agents.prompts import get_prompt_contract
from app.api.errors import ContractError
from app.artifacts import service as artifact_service
from app.core.config import settings
from app.evidence.retrieval import current_included_literature
from app.evidence.schemas import (
    EvidenceContextSpan,
    EvidenceSetSummaryCreate,
    EvidenceSetSummaryInput,
    EvidenceSetSummaryOutput,
    EvidenceSetSummaryPublic,
    TopicCandidatePublic,
    TopicCandidateSource,
    TopicGenerationCreate,
    TopicGenerationInput,
    TopicGenerationOutput,
    TopicGenerationRunPublic,
)
from app.jobs import service as job_service
from app.jobs.dispatcher import dispatcher as default_dispatcher
from app.models import (
    Artifact,
    ArtifactType,
    AuditActorType,
    AuditLog,
    AuditOutcome,
    EvidenceSetSummary,
    EvidenceSpan,
    Job,
    JobStatus,
    JobTaskType,
    LiteratureRecord,
    LocationVerificationStatus,
    ModelDataAccessLevel,
    ModelInvocation,
    ModelInvocationStatus,
    ProcessingRun,
    ResearchQuestionVersion,
    ResearchQuestionVersionStatus,
    TopicCandidate,
    TopicCandidateEvidence,
    TopicGenerationRun,
    User,
)
from app.projects import service as project_service

SUMMARY_PROMPT_ID = "evidence-set-summary"
TOPIC_PROMPT_ID = "topic-candidate-generation"
PROMPT_VERSION = "1.0.0"
SUMMARY_TASK_TYPE = "EVIDENCE_SET_SUMMARY"
TOPIC_TASK_TYPE = "TOPIC_CANDIDATE_GENERATION"
SUMMARY_PATH = "/api/v1/projects/{project_id}/evidence-set-summaries"
TOPIC_PATH = "/api/v1/projects/{project_id}/topic-generation-runs"
_FORBIDDEN_GAP_PHRASES = (
    "学术界完全没有",
    "从未有人研究",
    "已经证明不存在研究",
    "已经证明某个空白",
    "academia has never",
    "no research exists",
    "proven research gap",
)


class EvidenceAnalysisError(RuntimeError):
    def __init__(self, code: str, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable


@dataclass(frozen=True)
class AnalysisProviderIdentity:
    provider_id: str
    provider_name: str
    model_name: str
    mode: model_service.ModelExecutionMode
    fixture_id: str | None = None
    recording_id: str | None = None
    recording_version: str | None = None
    recording_hash: str | None = None
    recording_license_status: str | None = None
    recording_redaction_status: str | None = None


class AnalysisProvider(Protocol):
    identity: AnalysisProviderIdentity

    def summarize(self, payload: EvidenceSetSummaryInput) -> dict[str, Any]: ...

    def generate_topics(self, payload: TopicGenerationInput) -> dict[str, Any]: ...


@dataclass(frozen=True)
class AnalysisExecutionResult:
    output_object_type: str
    output_object_id: uuid.UUID
    output_artifact: Artifact | None


@dataclass
class OpenAICompatibleAnalysisProvider:
    identity: AnalysisProviderIdentity
    client: OpenAICompatibleJsonProvider

    def summarize(self, payload: EvidenceSetSummaryInput) -> dict[str, Any]:
        return self._generate(SUMMARY_PROMPT_ID, payload)

    def generate_topics(self, payload: TopicGenerationInput) -> dict[str, Any]:
        return self._generate(TOPIC_PROMPT_ID, payload)

    def _generate(
        self,
        prompt_id: str,
        payload: EvidenceSetSummaryInput | TopicGenerationInput,
    ) -> dict[str, Any]:
        try:
            return self.client.generate(
                prompt_id=prompt_id, prompt_version=PROMPT_VERSION, payload=payload
            )
        except ModelProviderError as exc:
            raise EvidenceAnalysisError(
                exc.code, str(exc), retryable=exc.retryable
            ) from exc


def configured_analysis_provider(
    identity: AnalysisProviderIdentity,
) -> AnalysisProvider:
    if settings.model_status != "CONFIGURED":
        raise EvidenceAnalysisError(
            "MODEL_PROVIDER_UNCONFIGURED",
            "No production evidence analysis provider is configured.",
            retryable=False,
        )
    assert settings.MODEL_BASE_URL is not None
    assert settings.MODEL_API_KEY is not None
    assert settings.MODEL_NAME is not None
    expected = AnalysisProviderIdentity(
        provider_id="openai-compatible",
        provider_name="openai-compatible",
        model_name=settings.MODEL_NAME,
        mode=model_service.ModelExecutionMode.LIVE,
    )
    if identity != expected:
        raise EvidenceAnalysisError(
            "MODEL_PROVIDER_MISMATCH",
            "Configured provider does not match invocation provenance.",
            retryable=False,
        )
    return OpenAICompatibleAnalysisProvider(
        identity=identity,
        client=OpenAICompatibleJsonProvider(
            base_url=str(settings.MODEL_BASE_URL),
            api_key=settings.MODEL_API_KEY.get_secret_value(),
            model_name=settings.MODEL_NAME,
            timeout_seconds=settings.REQUEST_TIMEOUT_SECONDS,
        ),
    )


def _not_found() -> ContractError:
    return ContractError(
        status_code=404, code="RESOURCE_NOT_FOUND", message="Resource not found."
    )


def _source_resolver(
    session: Session, source_id: uuid.UUID
) -> model_service.SourceReference | None:
    models: tuple[tuple[Any, str], ...] = (
        (LiteratureRecord, "LiteratureRecord"),
        (EvidenceSpan, "EvidenceSpan"),
        (ResearchQuestionVersion, "ResearchQuestionVersion"),
        (EvidenceSetSummary, "EvidenceSetSummary"),
    )
    for model, source_type in models:
        source = session.get(model, source_id)
        if source is not None:
            return model_service.SourceReference(
                source_id=source.id,
                project_id=source.project_id,
                source_type=source_type,
            )
    return None


def _identity_from_invocation(invocation: ModelInvocation) -> AnalysisProviderIdentity:
    metadata = invocation.implementation_metadata or {}
    execution = metadata.get("execution", {})
    try:
        mode = model_service.ModelExecutionMode(str(metadata["mode"]))
        provider_id = str(execution["provider_id"])
    except (KeyError, TypeError, ValueError) as exc:
        raise EvidenceAnalysisError(
            "MODEL_INPUT_INVALID", "Model execution provenance is invalid."
        ) from exc
    return AnalysisProviderIdentity(
        provider_id=provider_id,
        provider_name=invocation.provider or "unconfigured",
        model_name=invocation.model or "unconfigured",
        mode=mode,
        fixture_id=cast(str | None, metadata.get("fixture_id")),
        recording_id=cast(str | None, metadata.get("recording_id")),
        recording_version=cast(str | None, metadata.get("recording_version")),
        recording_hash=cast(str | None, metadata.get("recording_hash")),
        recording_license_status=cast(
            str | None, metadata.get("recording_license_status")
        ),
        recording_redaction_status=cast(
            str | None, metadata.get("recording_redaction_status")
        ),
    )


def _validate_execution_provider(
    *,
    invocation: ModelInvocation,
    provider: AnalysisProvider,
) -> AnalysisProviderIdentity:
    identity = _identity_from_invocation(invocation)
    if provider.identity != identity:
        raise EvidenceAnalysisError(
            "MODEL_PROVIDER_MISMATCH",
            "Injected provider does not match invocation provenance.",
        )
    return identity


def _validate_recorded_output(
    *, identity: AnalysisProviderIdentity, raw: dict[str, Any]
) -> None:
    if (
        identity.mode == model_service.ModelExecutionMode.RECORDED
        and identity.recording_hash != model_service.canonical_hash(raw)
    ):
        raise EvidenceAnalysisError(
            "MODEL_RECORDING_HASH_MISMATCH",
            "Recorded model output does not match invocation provenance.",
        )


def _invocation_command(
    *,
    actor: User,
    task_type: str,
    prompt_id: str,
    payload: EvidenceSetSummaryInput | TopicGenerationInput,
    source_ids: tuple[uuid.UUID, ...],
    provider: AnalysisProviderIdentity,
    retry_of_invocation_id: uuid.UUID | None = None,
    resource_id: uuid.UUID,
) -> model_service.InvocationCreate:
    prompt = get_prompt_contract(prompt_id, PROMPT_VERSION)
    return model_service.InvocationCreate(
        project_id=payload.project_id,
        authorization_actor=actor,
        actor_type=AuditActorType.USER,
        actor_id=str(actor.id),
        task_type=task_type,
        prompt_id=prompt.prompt_id,
        prompt_version=prompt.prompt_version,
        prompt_content_hash=prompt.content_hash,
        input_schema_name=prompt.input_schema.name,
        input_schema_version=prompt.input_schema.version,
        output_schema_name=prompt.output_schema.name,
        output_schema_version=prompt.output_schema.version,
        requested_data_access_level=ModelDataAccessLevel.VERIFIED_EVIDENCE_ONLY,
        max_allowed_data_access_level=ModelDataAccessLevel.VERIFIED_EVIDENCE_ONLY,
        effective_data_access_level=ModelDataAccessLevel.VERIFIED_EVIDENCE_ONLY,
        source_ids=source_ids,
        sanitized_input=payload.model_dump(mode="json"),
        mode=provider.mode,
        provider=provider.provider_name,
        model=provider.model_name,
        fixture_id=provider.fixture_id,
        recording_id=provider.recording_id,
        recording_version=provider.recording_version,
        recording_hash=provider.recording_hash,
        recording_license_status=provider.recording_license_status,
        recording_redaction_status=provider.recording_redaction_status,
        retry_of_invocation_id=retry_of_invocation_id,
        execution_metadata={
            "provider_id": provider.provider_id,
            "resource_id": str(resource_id),
        },
    )


def _audit(
    session: Session,
    *,
    project_id: uuid.UUID,
    action: str,
    object_type: str,
    object_id: uuid.UUID,
    actor_type: AuditActorType,
    actor_id: str | None,
    job_id: uuid.UUID | None,
    invocation_id: uuid.UUID | None,
    processing_run_id: uuid.UUID | None = None,
    after: dict[str, Any] | None = None,
    outcome: AuditOutcome = AuditOutcome.SUCCEEDED,
) -> None:
    snapshot = dict(after or {})
    if processing_run_id is not None:
        snapshot["processing_run_id"] = str(processing_run_id)
    session.add(
        AuditLog(
            project_id=project_id,
            actor_type=actor_type,
            actor_id=actor_id,
            action=action,
            object_type=object_type,
            object_id=object_id,
            after_snapshot=jsonable_encoder(snapshot) if snapshot else None,
            job_id=job_id,
            model_invocation_id=invocation_id,
            outcome=outcome,
        )
    )


def _summary_request(summary: EvidenceSetSummary) -> dict[str, Any]:
    request = summary.result_payload.get("request")
    if not isinstance(request, dict):
        raise EvidenceAnalysisError(
            "MODEL_INPUT_INVALID", "Evidence summary request metadata is unavailable."
        )
    return request


def build_summary_input(
    session: Session, *, summary: EvidenceSetSummary
) -> EvidenceSetSummaryInput:
    request = _summary_request(summary)
    literature_ids = [uuid.UUID(value) for value in summary.included_literature_ids]
    literature = session.exec(
        select(LiteratureRecord).where(
            LiteratureRecord.project_id == summary.project_id,
            col(LiteratureRecord.id).in_(literature_ids),
            col(LiteratureRecord.deleted_at).is_(None),
        )
    ).all()
    if {row.id for row in literature} != set(literature_ids):
        raise EvidenceAnalysisError(
            "SUMMARY_SCOPE_CHANGED", "The included literature snapshot is unavailable."
        )
    current_ids = {
        row.id
        for row in current_included_literature(session, project_id=summary.project_id)
    }
    if not set(literature_ids) <= current_ids:
        raise EvidenceAnalysisError(
            "SUMMARY_SCOPE_CHANGED",
            "The literature decision snapshot changed before summary execution.",
        )
    documents = {row.document_id: row.id for row in literature if row.document_id}
    require_spans = bool(request.get("require_evidence_spans", True))
    span_statement = select(EvidenceSpan).where(
        EvidenceSpan.project_id == summary.project_id,
        col(EvidenceSpan.document_id).in_(documents),
        col(EvidenceSpan.invalidated_at).is_(None),
    )
    if require_spans:
        span_statement = span_statement.where(
            EvidenceSpan.location_verification_status
            == LocationVerificationStatus.VERIFIED
        )
    spans = session.exec(span_statement.order_by(col(EvidenceSpan.id))).all()
    evidence = [
        EvidenceContextSpan(
            evidence_span_id=span.id,
            literature_record_id=documents[span.document_id],
            document_id=span.document_id,
            page_number=span.page_number,
            source_text=span.source_text,
            source_text_hash=span.source_text_hash,
            location_status=span.location_verification_status,
            limitations=(
                []
                if span.location_verification_status
                == LocationVerificationStatus.VERIFIED
                else [f"Location status is {span.location_verification_status.value}."]
            ),
        )
        for span in spans
    ]
    limitations = list(cast(list[str], request.get("input_limitations", [])))
    if not evidence:
        limitations.append(
            "The current included literature snapshot has no eligible EvidenceSpan content."
        )
    return EvidenceSetSummaryInput(
        summary_id=summary.id,
        project_id=summary.project_id,
        included_literature_ids=literature_ids,
        summary_types=cast(list[Any], request["summary_types"]),
        require_evidence_spans=require_spans,
        evidence=evidence,
        input_limitations=list(dict.fromkeys(limitations)),
    )


def _research_question_payload(version: ResearchQuestionVersion) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        jsonable_encoder(
            {
                "normalized_question": version.normalized_question,
                "research_object": version.research_object,
                "population": version.population,
                "context": version.context,
                "independent_variables": version.independent_variables,
                "dependent_variables": version.dependent_variables,
                "control_variables": version.control_variables,
                "research_goal": version.research_goal,
                "relationship_type": version.relationship_type,
                "method_preference": version.method_preference,
                "uncertainties": version.uncertainties,
            }
        ),
    )


def build_topic_input(
    session: Session, *, run: TopicGenerationRun
) -> TopicGenerationInput:
    version = session.exec(
        select(ResearchQuestionVersion).where(
            ResearchQuestionVersion.id == run.research_question_version_id,
            ResearchQuestionVersion.project_id == run.project_id,
        )
    ).first()
    summary = session.exec(
        select(EvidenceSetSummary).where(
            EvidenceSetSummary.id == run.evidence_summary_id,
            EvidenceSetSummary.project_id == run.project_id,
        )
    ).first()
    if version is None or summary is None:
        raise EvidenceAnalysisError(
            "MODEL_OUTPUT_SOURCE_MISSING", "Topic generation sources are unavailable."
        )
    if version.status != ResearchQuestionVersionStatus.CONFIRMED:
        raise EvidenceAnalysisError(
            "RESEARCH_QUESTION_VERSION_NOT_CONFIRMED",
            "Topic generation requires a confirmed ResearchQuestionVersion.",
        )
    if summary.status != JobStatus.COMPLETED:
        raise EvidenceAnalysisError(
            "EVIDENCE_SUMMARY_NOT_COMPLETED",
            "Topic generation requires a completed EvidenceSetSummary.",
        )
    output = EvidenceSetSummaryOutput.model_validate(summary.result_payload)
    return TopicGenerationInput(
        topic_generation_run_id=run.id,
        project_id=run.project_id,
        research_question_version_id=version.id,
        research_question=_research_question_payload(version),
        evidence_set_summary_id=summary.id,
        evidence_summary=output,
        candidate_count=3,
        user_constraints=run.user_constraints or {},
    )


def request_summary_job(
    session: Session,
    *,
    actor: User,
    project_id: uuid.UUID,
    payload: EvidenceSetSummaryCreate,
    idempotency_key: str,
    provider: AnalysisProviderIdentity,
    dispatcher: job_service.JobDispatcher = default_dispatcher,
) -> project_service.OperationResult:
    project_service.authorize_project(
        session, project_id=project_id, actor=actor, action="project.update"
    )
    requested = set(payload.included_literature_ids)
    rows = session.exec(
        select(LiteratureRecord).where(col(LiteratureRecord.id).in_(requested))
    ).all()
    if {row.id for row in rows} != requested or any(
        row.project_id != project_id for row in rows
    ):
        raise _not_found()
    current_included = {
        row.id for row in current_included_literature(session, project_id=project_id)
    }
    included = sorted(requested & current_included, key=str)
    if not included:
        raise ContractError(
            status_code=409,
            code="CURRENT_LITERATURE_SET_EMPTY",
            message="No requested literature is currently included.",
        )
    excluded_count = len(requested - current_included)
    request_payload = {
        "summary_types": [value.value for value in payload.summary_types],
        "require_evidence_spans": payload.require_evidence_spans,
        "input_limitations": (
            [
                f"{excluded_count} requested LiteratureRecord entries were excluded because they are not in the current included set."
            ]
            if excluded_count
            else []
        ),
    }
    digest = project_service.request_hash(
        {"payload": payload, "provider_id": provider.provider_id}
    )
    replay = project_service._replay_or_conflict(
        session,
        actor_id=actor.id,
        project_id=project_id,
        method="POST",
        path_template=SUMMARY_PATH,
        key=idempotency_key,
        payload_hash=digest,
    )
    if replay is not None:
        return replay
    summary = EvidenceSetSummary(
        project_id=project_id,
        included_literature_ids=[str(value) for value in included],
        scope_statement=f"Pending analysis of the current set of {len(included)} included literature records.",
        result_payload={"request": request_payload},
        status=JobStatus.DRAFT,
    )
    session.add(summary)
    session.flush()
    summary_input = build_summary_input(session, summary=summary)
    source_ids = tuple(included) + tuple(
        item.evidence_span_id for item in summary_input.evidence
    )
    invocation = model_service.create_model_invocation(
        session,
        command=_invocation_command(
            actor=actor,
            task_type=SUMMARY_TASK_TYPE,
            prompt_id=SUMMARY_PROMPT_ID,
            payload=summary_input,
            source_ids=source_ids,
            provider=provider,
            resource_id=summary.id,
        ),
        source_resolver=_source_resolver,
        commit=False,
    )
    job = job_service.create_job(
        session,
        project_id=project_id,
        command=job_service.JobCreate(
            task_type=JobTaskType.LITERATURE_SUMMARIZE,
            resource_type="evidence_set_summary",
            resource_id=summary.id,
            idempotency_key=idempotency_key,
            requested_by_user_id=actor.id,
            max_retries=2,
            retryable=True,
        ),
    )
    summary.job_id = job.id
    summary.source_model_invocation_id = invocation.id
    summary.status = JobStatus.QUEUED
    session.add(summary)
    _audit(
        session,
        project_id=project_id,
        action="EVIDENCE_SET_SUMMARY_REQUESTED",
        object_type="evidence_set_summary",
        object_id=summary.id,
        actor_type=AuditActorType.USER,
        actor_id=str(actor.id),
        job_id=job.id,
        invocation_id=invocation.id,
        after={
            "included_count": len(included),
            "excluded_requested_count": excluded_count,
        },
    )
    initial = project_service.OperationResult(
        data=job_service.job_data(session, job), status_code=201
    )
    project_service._store_idempotency(
        session,
        actor_id=actor.id,
        project_id=project_id,
        method="POST",
        path_template=SUMMARY_PATH,
        key=idempotency_key,
        payload_hash=digest,
        result=initial,
    )
    project_service._commit(session)
    dispatched = job_service.dispatch_job(session, job_id=job.id, dispatcher=dispatcher)
    if dispatched.status == JobStatus.DISPATCH_FAILED:
        model_service.fail_model_invocation(
            session,
            invocation_id=invocation.id,
            error_code="JOB_DISPATCH_FAILED",
            degradation=model_service.DegradationRecord(
                requested_capability=SUMMARY_TASK_TYPE,
                primary_provider=invocation.provider,
                fallback_provider=None,
                reason_code="JOB_DISPATCH_FAILED",
                impact="No summary worker accepted the request.",
                result_status="FAILED",
                user_visible_message="Evidence summary generation could not be queued.",
            ),
        )
        failed_summary = session.get(EvidenceSetSummary, summary.id)
        assert failed_summary is not None
        failed_summary.status = JobStatus.FAILED
        session.add(failed_summary)
        project_service._commit(session)
    result = project_service.OperationResult(
        data=job_service.job_data(session, dispatched), status_code=201
    )
    project_service._update_idempotency_result(
        session,
        actor_id=actor.id,
        project_id=project_id,
        method="POST",
        path_template=SUMMARY_PATH,
        key=idempotency_key,
        result=result,
    )
    project_service._commit(session)
    return result


def request_topic_job(
    session: Session,
    *,
    actor: User,
    project_id: uuid.UUID,
    payload: TopicGenerationCreate,
    idempotency_key: str,
    provider: AnalysisProviderIdentity,
    dispatcher: job_service.JobDispatcher = default_dispatcher,
) -> project_service.OperationResult:
    project_service.authorize_project(
        session, project_id=project_id, actor=actor, action="project.update"
    )
    version = session.get(ResearchQuestionVersion, payload.research_question_version_id)
    summary = session.get(EvidenceSetSummary, payload.evidence_set_summary_id)
    if (
        version is None
        or summary is None
        or version.project_id != project_id
        or summary.project_id != project_id
    ):
        raise _not_found()
    if version.status != ResearchQuestionVersionStatus.CONFIRMED:
        raise ContractError(
            status_code=409,
            code="RESEARCH_QUESTION_VERSION_NOT_CONFIRMED",
            message="Topic generation requires a confirmed ResearchQuestionVersion.",
        )
    if summary.status != JobStatus.COMPLETED:
        raise ContractError(
            status_code=409,
            code="EVIDENCE_SUMMARY_NOT_COMPLETED",
            message="Topic generation requires a completed EvidenceSetSummary.",
        )
    digest = project_service.request_hash(
        {"payload": payload, "provider_id": provider.provider_id}
    )
    replay = project_service._replay_or_conflict(
        session,
        actor_id=actor.id,
        project_id=project_id,
        method="POST",
        path_template=TOPIC_PATH,
        key=idempotency_key,
        payload_hash=digest,
    )
    if replay is not None:
        return replay
    run = TopicGenerationRun(
        project_id=project_id,
        research_question_version_id=version.id,
        evidence_summary_id=summary.id,
        user_constraints=payload.user_constraints,
        status=JobStatus.DRAFT,
    )
    session.add(run)
    session.flush()
    topic_input = build_topic_input(session, run=run)
    invocation = model_service.create_model_invocation(
        session,
        command=_invocation_command(
            actor=actor,
            task_type=TOPIC_TASK_TYPE,
            prompt_id=TOPIC_PROMPT_ID,
            payload=topic_input,
            source_ids=(version.id, summary.id),
            provider=provider,
            resource_id=run.id,
        ),
        source_resolver=_source_resolver,
        commit=False,
    )
    job = job_service.create_job(
        session,
        project_id=project_id,
        command=job_service.JobCreate(
            task_type=JobTaskType.TOPIC_GENERATE,
            resource_type="topic_generation_run",
            resource_id=run.id,
            idempotency_key=idempotency_key,
            requested_by_user_id=actor.id,
            max_retries=2,
            retryable=True,
        ),
    )
    run.job_id = job.id
    run.source_model_invocation_id = invocation.id
    run.status = JobStatus.QUEUED
    session.add(run)
    _audit(
        session,
        project_id=project_id,
        action="TOPIC_GENERATION_REQUESTED",
        object_type="topic_generation_run",
        object_id=run.id,
        actor_type=AuditActorType.USER,
        actor_id=str(actor.id),
        job_id=job.id,
        invocation_id=invocation.id,
        after={"candidate_count": 3, "evidence_summary_id": str(summary.id)},
    )
    initial = project_service.OperationResult(
        data=job_service.job_data(session, job), status_code=201
    )
    project_service._store_idempotency(
        session,
        actor_id=actor.id,
        project_id=project_id,
        method="POST",
        path_template=TOPIC_PATH,
        key=idempotency_key,
        payload_hash=digest,
        result=initial,
    )
    project_service._commit(session)
    dispatched = job_service.dispatch_job(session, job_id=job.id, dispatcher=dispatcher)
    if dispatched.status == JobStatus.DISPATCH_FAILED:
        model_service.fail_model_invocation(
            session,
            invocation_id=invocation.id,
            error_code="JOB_DISPATCH_FAILED",
            degradation=model_service.DegradationRecord(
                requested_capability=TOPIC_TASK_TYPE,
                primary_provider=invocation.provider,
                fallback_provider=None,
                reason_code="JOB_DISPATCH_FAILED",
                impact="No topic worker accepted the request.",
                result_status="FAILED",
                user_visible_message="Topic generation could not be queued.",
            ),
        )
        failed_run = session.get(TopicGenerationRun, run.id)
        assert failed_run is not None
        failed_run.status = JobStatus.FAILED
        session.add(failed_run)
        project_service._commit(session)
    result = project_service.OperationResult(
        data=job_service.job_data(session, dispatched), status_code=201
    )
    project_service._update_idempotency_result(
        session,
        actor_id=actor.id,
        project_id=project_id,
        method="POST",
        path_template=TOPIC_PATH,
        key=idempotency_key,
        result=result,
    )
    project_service._commit(session)
    return result


def _retry_invocation(
    session: Session,
    *,
    job: Job,
    previous: ModelInvocation,
    payload: EvidenceSetSummaryInput | TopicGenerationInput,
    source_ids: tuple[uuid.UUID, ...],
    task_type: str,
    prompt_id: str,
    resource_id: uuid.UUID,
) -> ModelInvocation:
    if job.requested_by_user_id is None:
        raise EvidenceAnalysisError(
            "MODEL_AUTHORIZATION_ACTOR_MISSING", "Retry actor is unavailable."
        )
    actor = session.get(User, job.requested_by_user_id)
    if actor is None:
        raise EvidenceAnalysisError(
            "MODEL_AUTHORIZATION_ACTOR_MISSING", "Retry actor is unavailable."
        )
    return model_service.create_model_invocation(
        session,
        command=_invocation_command(
            actor=actor,
            task_type=task_type,
            prompt_id=prompt_id,
            payload=payload,
            source_ids=source_ids,
            provider=_identity_from_invocation(previous),
            retry_of_invocation_id=previous.id,
            resource_id=resource_id,
        ),
        source_resolver=_source_resolver,
        commit=False,
    )


def _invocation_for_execution(
    session: Session,
    *,
    job: Job,
    run_id: uuid.UUID,
    resource: EvidenceSetSummary | TopicGenerationRun,
    payload: EvidenceSetSummaryInput | TopicGenerationInput,
    source_ids: tuple[uuid.UUID, ...],
    task_type: str,
    prompt_id: str,
) -> ModelInvocation:
    processing = session.get(ProcessingRun, run_id)
    invocation = session.get(ModelInvocation, resource.source_model_invocation_id)
    if processing is None or processing.job_id != job.id or invocation is None:
        raise EvidenceAnalysisError(
            "MODEL_INVOCATION_INVALID_STATE", "Analysis provenance is unavailable."
        )
    if (
        processing.attempt_number > 1
        and invocation.status == ModelInvocationStatus.FAILED
    ):
        invocation = _retry_invocation(
            session,
            job=job,
            previous=invocation,
            payload=payload,
            source_ids=source_ids,
            task_type=task_type,
            prompt_id=prompt_id,
            resource_id=resource.id,
        )
        resource.source_model_invocation_id = invocation.id
        session.add(resource)
        project_service._commit(session)
    if invocation.status != ModelInvocationStatus.PENDING:
        raise EvidenceAnalysisError(
            "MODEL_INVOCATION_INVALID_STATE", "Analysis invocation is not pending."
        )
    if (
        model_service.canonical_hash(payload.model_dump(mode="json"))
        != invocation.input_hash
    ):
        raise EvidenceAnalysisError(
            "MODEL_INPUT_HASH_MISMATCH", "Analysis input no longer matches provenance."
        )
    return invocation


def _fail_analysis(
    session: Session,
    *,
    resource: EvidenceSetSummary | TopicGenerationRun,
    invocation_id: uuid.UUID,
    job: Job,
    run_id: uuid.UUID,
    code: str,
) -> None:
    session.rollback()
    invocation = session.get(ModelInvocation, invocation_id)
    if invocation is not None and invocation.status in {
        ModelInvocationStatus.PENDING,
        ModelInvocationStatus.RUNNING,
    }:
        model_service.fail_model_invocation(
            session,
            invocation_id=invocation.id,
            error_code=code,
            degradation=model_service.DegradationRecord(
                requested_capability=invocation.task_type,
                primary_provider=invocation.provider,
                fallback_provider=None,
                reason_code=code,
                impact="No unvalidated evidence analysis result was persisted.",
                result_status="UNAVAILABLE",
                user_visible_message="Evidence analysis failed without creating scientific conclusions.",
            ),
        )
    reloaded: Any = session.get(type(resource), resource.id)
    if reloaded is not None:
        reloaded.status = JobStatus.FAILED
        reloaded.processing_run_id = run_id
        session.add(reloaded)
        _audit(
            session,
            project_id=reloaded.project_id,
            action="EVIDENCE_ANALYSIS_FAILED",
            object_type=(
                "evidence_set_summary"
                if isinstance(reloaded, EvidenceSetSummary)
                else "topic_generation_run"
            ),
            object_id=reloaded.id,
            actor_type=AuditActorType.WORKER,
            actor_id="evidence-analysis-worker",
            job_id=job.id,
            invocation_id=invocation_id,
            processing_run_id=run_id,
            after={"error_code": code},
            outcome=AuditOutcome.FAILED,
        )
        project_service._commit(session)


def _validate_summary_sources(
    *,
    summary_input: EvidenceSetSummaryInput,
    output: EvidenceSetSummaryOutput,
) -> None:
    if set(output.included_literature_ids) != set(
        summary_input.included_literature_ids
    ):
        raise EvidenceAnalysisError(
            "MODEL_OUTPUT_SOURCE_MISSING",
            "Summary literature sources do not match the current included snapshot.",
        )
    serialized = output.model_dump_json().casefold()
    if any(phrase.casefold() in serialized for phrase in _FORBIDDEN_GAP_PHRASES):
        raise EvidenceAnalysisError(
            "MODEL_OUTPUT_UNSAFE_CLAIM",
            "Summary contains a prohibited universal research-gap claim.",
        )
    items = (
        output.consensus_items
        + output.controversy_items
        + output.evidence_gap_items
        + output.counterexamples
        + output.method_difference_items
        + output.sample_difference_items
        + output.missing_literature
    )
    literature_ids = set(summary_input.included_literature_ids)
    span_ids = {item.evidence_span_id for item in summary_input.evidence}
    contradicting: set[uuid.UUID] = set()
    for item in items:
        if not set(item.supporting_literature_ids) <= literature_ids:
            raise EvidenceAnalysisError(
                "MODEL_OUTPUT_SOURCE_MISSING", "Summary cited non-included literature."
            )
        if not set(item.contradicting_literature_ids) <= literature_ids:
            raise EvidenceAnalysisError(
                "MODEL_OUTPUT_SOURCE_MISSING", "Summary cited non-included literature."
            )
        if not set(item.evidence_span_ids) <= span_ids:
            raise EvidenceAnalysisError(
                "MODEL_OUTPUT_SOURCE_MISSING", "Summary cited unavailable evidence."
            )
        contradicting.update(item.contradicting_literature_ids)
    counterexample_sources = {
        source_id
        for item in output.counterexamples
        for source_id in (
            item.supporting_literature_ids + item.contradicting_literature_ids
        )
    }
    if not contradicting <= counterexample_sources:
        raise EvidenceAnalysisError(
            "MODEL_OUTPUT_COUNTEREXAMPLE_HIDDEN",
            "Contradicting literature must be retained as counterexamples.",
        )


def _validate_topic_sources(
    session: Session,
    *,
    topic_input: TopicGenerationInput,
    output: TopicGenerationOutput,
) -> None:
    literature_ids = set(topic_input.evidence_summary.included_literature_ids)
    literature = session.exec(
        select(LiteratureRecord).where(
            LiteratureRecord.project_id == topic_input.project_id,
            col(LiteratureRecord.id).in_(literature_ids),
        )
    ).all()
    document_to_literature = {
        item.document_id: item.id for item in literature if item.document_id
    }
    summary_items = (
        topic_input.evidence_summary.consensus_items
        + topic_input.evidence_summary.controversy_items
        + topic_input.evidence_summary.evidence_gap_items
        + topic_input.evidence_summary.counterexamples
        + topic_input.evidence_summary.method_difference_items
        + topic_input.evidence_summary.sample_difference_items
        + topic_input.evidence_summary.missing_literature
    )
    summary_span_ids = {
        span_id for item in summary_items for span_id in item.evidence_span_ids
    }
    for candidate in output.candidates:
        for source in candidate.sources:
            if source.literature_record_id is not None:
                if source.literature_record_id not in literature_ids:
                    raise EvidenceAnalysisError(
                        "MODEL_OUTPUT_SOURCE_MISSING",
                        "Topic candidate cited non-included literature.",
                    )
                continue
            span = session.get(EvidenceSpan, source.evidence_span_id)
            if (
                span is None
                or span.project_id != topic_input.project_id
                or span.invalidated_at is not None
                or document_to_literature.get(span.document_id) not in literature_ids
                or span.id not in summary_span_ids
            ):
                raise EvidenceAnalysisError(
                    "MODEL_OUTPUT_SOURCE_MISSING",
                    "Topic candidate cited unavailable evidence.",
                )
        serialized = candidate.model_dump_json().casefold()
        if any(phrase.casefold() in serialized for phrase in _FORBIDDEN_GAP_PHRASES):
            raise EvidenceAnalysisError(
                "MODEL_OUTPUT_UNSAFE_CLAIM",
                "Topic candidate contains a prohibited universal research-gap claim.",
            )


def execute_summary_job(
    session: Session,
    *,
    job: Job,
    run_id: uuid.UUID,
    provider: AnalysisProvider | None = None,
    storage_backend: ObjectStorage | None = None,
) -> AnalysisExecutionResult:
    if job.task_type != JobTaskType.LITERATURE_SUMMARIZE:
        raise EvidenceAnalysisError("JOB_HANDLER_MISMATCH", "Job is not a summary job.")
    summary = session.get(EvidenceSetSummary, job.resource_id)
    if summary is None or summary.project_id != job.project_id:
        raise EvidenceAnalysisError("RESOURCE_NOT_FOUND", "Summary is unavailable.")
    summary_input = build_summary_input(session, summary=summary)
    source_ids = tuple(summary_input.included_literature_ids) + tuple(
        item.evidence_span_id for item in summary_input.evidence
    )
    invocation = _invocation_for_execution(
        session,
        job=job,
        run_id=run_id,
        resource=summary,
        payload=summary_input,
        source_ids=source_ids,
        task_type=SUMMARY_TASK_TYPE,
        prompt_id=SUMMARY_PROMPT_ID,
    )
    try:
        provider = provider or configured_analysis_provider(
            _identity_from_invocation(invocation)
        )
        identity = _validate_execution_provider(
            invocation=invocation, provider=provider
        )
        summary.status = JobStatus.RUNNING
        summary.processing_run_id = run_id
        session.add(summary)
        job_service.set_run_context(
            session,
            job_id=job.id,
            run_id=run_id,
            input_hash=invocation.input_hash,
            parameters={"included_count": len(summary_input.included_literature_ids)},
            implementation_metadata={
                "model_invocation_id": str(invocation.id),
                "provider_id": provider.identity.provider_id,
            },
        )
        model_service.mark_model_invocation_running(
            session, invocation_id=invocation.id
        )
        raw = provider.summarize(summary_input)
        _validate_recorded_output(identity=identity, raw=raw)
        output = EvidenceSetSummaryOutput.model_validate(raw)
        _validate_summary_sources(summary_input=summary_input, output=output)
        artifact = artifact_service.create_generated_json_artifact(
            session,
            project_id=summary.project_id,
            payload=output.model_dump(mode="json"),
            filename=f"evidence-set-summary-{summary.id}.json",
            artifact_type=ArtifactType.MODEL_OUTPUT,
            metadata={
                "schema_name": "EvidenceSetSummaryOutput",
                "schema_version": "1.0",
                "evidence_set_summary_id": str(summary.id),
                "model_invocation_id": str(invocation.id),
                "processing_run_id": str(run_id),
            },
            created_by=job.requested_by_user_id,
            storage_backend=storage_backend,
        )
        summary.scope_statement = output.scope_statement
        summary.result_payload = output.model_dump(mode="json")
        summary.status = JobStatus.COMPLETED
        session.add(summary)
        _audit(
            session,
            project_id=summary.project_id,
            action="EVIDENCE_SET_SUMMARY_COMPLETED",
            object_type="evidence_set_summary",
            object_id=summary.id,
            actor_type=AuditActorType.WORKER,
            actor_id="evidence-analysis-worker",
            job_id=job.id,
            invocation_id=invocation.id,
            processing_run_id=run_id,
            after={"included_count": len(output.included_literature_ids)},
        )
        model_service.complete_model_invocation(
            session,
            invocation_id=invocation.id,
            sanitized_output=output.model_dump(mode="json"),
        )
        return AnalysisExecutionResult(
            output_object_type="evidence_set_summary",
            output_object_id=summary.id,
            output_artifact=artifact,
        )
    except (EvidenceAnalysisError, ValidationError, StorageError) as exc:
        code = str(getattr(exc, "code", "MODEL_OUTPUT_SCHEMA_INVALID"))
        _fail_analysis(
            session,
            resource=summary,
            invocation_id=invocation.id,
            job=job,
            run_id=run_id,
            code=code,
        )
        if isinstance(exc, EvidenceAnalysisError):
            raise
        raise EvidenceAnalysisError(code, "Evidence summary execution failed.") from exc


def _persist_topic_candidates(
    session: Session,
    *,
    run: TopicGenerationRun,
    output: TopicGenerationOutput,
) -> None:
    for item in sorted(
        output.candidates, key=lambda candidate: candidate.candidate_order
    ):
        candidate = TopicCandidate(
            project_id=run.project_id,
            topic_generation_run_id=run.id,
            candidate_order=item.candidate_order,
            question_text=item.question_text,
            research_object=item.research_object,
            variables=item.variables,
            literature_basis=item.literature_basis,
            possible_innovation=item.possible_innovation,
            data_requirements=item.data_requirements,
            recommended_method=item.recommended_method,
            literature_basis_level=item.literature_basis_level,
            data_availability=item.data_availability,
            method_difficulty=item.method_difficulty,
            time_feasibility=item.time_feasibility,
            ethical_risk=item.ethical_risk,
            major_risks=item.major_risks,
            limitations=item.limitations,
            supervisor_confirmation_items=item.supervisor_confirmation_items,
        )
        session.add(candidate)
        session.flush()
        for source in item.sources:
            session.add(
                TopicCandidateEvidence(
                    project_id=run.project_id,
                    topic_candidate_id=candidate.id,
                    literature_record_id=source.literature_record_id,
                    evidence_span_id=source.evidence_span_id,
                    relation_type=source.relation_type,
                    explanation=source.explanation,
                )
            )


def execute_topic_job(
    session: Session,
    *,
    job: Job,
    run_id: uuid.UUID,
    provider: AnalysisProvider | None = None,
    storage_backend: ObjectStorage | None = None,
) -> AnalysisExecutionResult:
    if job.task_type != JobTaskType.TOPIC_GENERATE:
        raise EvidenceAnalysisError("JOB_HANDLER_MISMATCH", "Job is not a topic job.")
    run = session.get(TopicGenerationRun, job.resource_id)
    if run is None or run.project_id != job.project_id:
        raise EvidenceAnalysisError("RESOURCE_NOT_FOUND", "Topic run is unavailable.")
    topic_input = build_topic_input(session, run=run)
    invocation = _invocation_for_execution(
        session,
        job=job,
        run_id=run_id,
        resource=run,
        payload=topic_input,
        source_ids=(
            topic_input.research_question_version_id,
            topic_input.evidence_set_summary_id,
        ),
        task_type=TOPIC_TASK_TYPE,
        prompt_id=TOPIC_PROMPT_ID,
    )
    try:
        provider = provider or configured_analysis_provider(
            _identity_from_invocation(invocation)
        )
        identity = _validate_execution_provider(
            invocation=invocation, provider=provider
        )
        run.status = JobStatus.RUNNING
        run.processing_run_id = run_id
        session.add(run)
        job_service.set_run_context(
            session,
            job_id=job.id,
            run_id=run_id,
            input_hash=invocation.input_hash,
            parameters={"candidate_count": 3},
            implementation_metadata={
                "model_invocation_id": str(invocation.id),
                "provider_id": provider.identity.provider_id,
            },
        )
        model_service.mark_model_invocation_running(
            session, invocation_id=invocation.id
        )
        raw = provider.generate_topics(topic_input)
        _validate_recorded_output(identity=identity, raw=raw)
        output = TopicGenerationOutput.model_validate(raw)
        _validate_topic_sources(session, topic_input=topic_input, output=output)
        artifact = artifact_service.create_generated_json_artifact(
            session,
            project_id=run.project_id,
            payload=output.model_dump(mode="json"),
            filename=f"topic-generation-{run.id}.json",
            artifact_type=ArtifactType.MODEL_OUTPUT,
            metadata={
                "schema_name": "TopicGenerationOutput",
                "schema_version": "1.0",
                "topic_generation_run_id": str(run.id),
                "model_invocation_id": str(invocation.id),
                "processing_run_id": str(run_id),
            },
            created_by=job.requested_by_user_id,
            storage_backend=storage_backend,
        )
        _persist_topic_candidates(session, run=run, output=output)
        session.flush()
        run.status = JobStatus.COMPLETED
        session.add(run)
        _audit(
            session,
            project_id=run.project_id,
            action="TOPIC_GENERATION_COMPLETED",
            object_type="topic_generation_run",
            object_id=run.id,
            actor_type=AuditActorType.WORKER,
            actor_id="evidence-analysis-worker",
            job_id=job.id,
            invocation_id=invocation.id,
            processing_run_id=run_id,
            after={"candidate_count": 3},
        )
        model_service.complete_model_invocation(
            session,
            invocation_id=invocation.id,
            sanitized_output=output.model_dump(mode="json"),
        )
        return AnalysisExecutionResult(
            output_object_type="topic_generation_run",
            output_object_id=run.id,
            output_artifact=artifact,
        )
    except (EvidenceAnalysisError, ValidationError, StorageError) as exc:
        code = str(getattr(exc, "code", "MODEL_OUTPUT_SCHEMA_INVALID"))
        _fail_analysis(
            session,
            resource=run,
            invocation_id=invocation.id,
            job=job,
            run_id=run_id,
            code=code,
        )
        if isinstance(exc, EvidenceAnalysisError):
            raise
        raise EvidenceAnalysisError(code, "Topic generation execution failed.") from exc


def summary_data(
    summary: EvidenceSetSummary, *, can_generate_topics: bool
) -> dict[str, Any]:
    result = None
    if summary.status == JobStatus.COMPLETED:
        result = EvidenceSetSummaryOutput.model_validate(summary.result_payload)
    actions = ["evidence_set_summary.read"]
    if can_generate_topics and summary.status == JobStatus.COMPLETED:
        actions.append("topic_generation.create")
    return EvidenceSetSummaryPublic(
        id=summary.id,
        project_id=summary.project_id,
        included_literature_ids=[
            uuid.UUID(value) for value in summary.included_literature_ids
        ],
        scope_statement=summary.scope_statement,
        result=result,
        job_id=summary.job_id,
        processing_run_id=summary.processing_run_id,
        source_model_invocation_id=summary.source_model_invocation_id,
        status=summary.status,
        allowed_actions=actions,
        created_at=summary.created_at,
    ).model_dump(mode="json")


def get_summary(
    session: Session, *, actor: User, summary_id: uuid.UUID
) -> dict[str, Any]:
    summary = session.get(EvidenceSetSummary, summary_id)
    if summary is None:
        raise _not_found()
    access = project_service.authorize_project(
        session, project_id=summary.project_id, actor=actor, action="project.read"
    )
    can_generate = (
        access.membership is not None
        and "project.update"
        in project_service.ROLE_ACTIONS.get(access.membership.role, frozenset())
    )
    return summary_data(summary, can_generate_topics=can_generate)


def _candidate_data(
    session: Session, candidate: TopicCandidate
) -> TopicCandidatePublic:
    links = session.exec(
        select(TopicCandidateEvidence)
        .where(
            TopicCandidateEvidence.project_id == candidate.project_id,
            TopicCandidateEvidence.topic_candidate_id == candidate.id,
        )
        .order_by(col(TopicCandidateEvidence.id))
    ).all()
    return TopicCandidatePublic(
        id=candidate.id,
        project_id=candidate.project_id,
        topic_generation_run_id=candidate.topic_generation_run_id,
        candidate_order=candidate.candidate_order,
        question_text=candidate.question_text,
        research_object=candidate.research_object,
        variables=candidate.variables,
        literature_basis=candidate.literature_basis,
        possible_innovation=candidate.possible_innovation,
        data_requirements=candidate.data_requirements,
        recommended_method=candidate.recommended_method,
        literature_basis_level=candidate.literature_basis_level,
        data_availability=candidate.data_availability,
        method_difficulty=candidate.method_difficulty,
        time_feasibility=candidate.time_feasibility,
        ethical_risk=candidate.ethical_risk,
        major_risks=candidate.major_risks,
        limitations=candidate.limitations,
        supervisor_confirmation_items=candidate.supervisor_confirmation_items,
        status=candidate.status,
        sources=[
            TopicCandidateSource(
                literature_record_id=link.literature_record_id,
                evidence_span_id=link.evidence_span_id,
                relation_type=link.relation_type,
                explanation=link.explanation,
            )
            for link in links
        ],
        created_at=candidate.created_at,
    )


def topic_run_data(
    session: Session, run: TopicGenerationRun, *, can_generate: bool
) -> dict[str, Any]:
    candidates = session.exec(
        select(TopicCandidate)
        .where(
            TopicCandidate.project_id == run.project_id,
            TopicCandidate.topic_generation_run_id == run.id,
        )
        .order_by(col(TopicCandidate.candidate_order))
    ).all()
    return TopicGenerationRunPublic(
        id=run.id,
        project_id=run.project_id,
        research_question_version_id=run.research_question_version_id,
        evidence_summary_id=run.evidence_summary_id,
        user_constraints=run.user_constraints,
        job_id=run.job_id,
        processing_run_id=run.processing_run_id,
        source_model_invocation_id=run.source_model_invocation_id,
        status=run.status,
        candidates=[_candidate_data(session, candidate) for candidate in candidates],
        allowed_actions=(
            ["topic_generation.read", "topic_generation.create"]
            if can_generate
            else ["topic_generation.read"]
        ),
        created_at=run.created_at,
    ).model_dump(mode="json")


def get_topic_run(
    session: Session, *, actor: User, run_id: uuid.UUID
) -> dict[str, Any]:
    run = session.get(TopicGenerationRun, run_id)
    if run is None:
        raise _not_found()
    access = project_service.authorize_project(
        session, project_id=run.project_id, actor=actor, action="project.read"
    )
    can_generate = (
        access.membership is not None
        and "project.update"
        in project_service.ROLE_ACTIONS.get(access.membership.role, frozenset())
    )
    return topic_run_data(session, run, can_generate=can_generate)
