from __future__ import annotations

import uuid
from typing import Any, Protocol

from fastapi.encoders import jsonable_encoder
from pydantic import ValidationError
from sqlmodel import Session, col, select

from app.adapters.model_provider import ModelProviderError, OpenAICompatibleJsonProvider
from app.agents import service as model_service
from app.agents.prompts import get_prompt_contract
from app.api.errors import ContractError
from app.cleaning import service as cleaning_service
from app.cleaning.schemas import (
    CleaningPlanSuggestion,
    CleaningPlanSuggestionInput,
    CleaningPlanSuggestionRequest,
    SuggestionColumn,
    SuggestionIssue,
)
from app.core.config import settings
from app.datasets import service as dataset_service
from app.models import (
    AuditActorType,
    DataQualityIssue,
    DatasetColumn,
    DatasetVersion,
    ModelDataAccessLevel,
    User,
)
from app.projects import service as project_service

PROMPT_ID = "cleaning-plan-suggestion"
PROMPT_VERSION = "1.0.0"
TASK_TYPE = "CLEANING_PLAN_SUGGESTION"
PATH = "/api/v1/dataset-versions/{version_id}/cleaning-plan-suggestions"
ALLOWED_ACTION_TYPES = (
    "MARK_MISSING",
    "MAP_CATEGORY",
    "REPLACE_VALUE",
    "CAST_TYPE",
    "RENAME_COLUMN",
)


class SuggestionProvider(Protocol):
    provider_name: str
    model_name: str

    def generate(self, payload: CleaningPlanSuggestionInput) -> dict[str, Any]: ...


class ConfiguredSuggestionProvider:
    provider_name = "openai-compatible"

    def __init__(self) -> None:
        if settings.model_status != "CONFIGURED":
            raise ContractError(
                status_code=503,
                code="MODEL_PROVIDER_UNCONFIGURED",
                message="No CleaningPlan suggestion provider is configured.",
            )
        assert settings.MODEL_BASE_URL is not None
        assert settings.MODEL_API_KEY is not None
        assert settings.MODEL_NAME is not None
        self.model_name = settings.MODEL_NAME
        self.client = OpenAICompatibleJsonProvider(
            base_url=str(settings.MODEL_BASE_URL),
            api_key=settings.MODEL_API_KEY.get_secret_value(),
            model_name=settings.MODEL_NAME,
            timeout_seconds=settings.REQUEST_TIMEOUT_SECONDS,
        )

    def generate(self, payload: CleaningPlanSuggestionInput) -> dict[str, Any]:
        return self.client.generate(
            prompt_id=PROMPT_ID, prompt_version=PROMPT_VERSION, payload=payload
        )


def _source_resolver(
    session: Session, source_id: uuid.UUID
) -> model_service.SourceReference | None:
    version = session.get(DatasetVersion, source_id)
    if version is not None:
        return model_service.SourceReference(
            source_id=version.id,
            project_id=version.project_id,
            source_type="DatasetVersion",
        )
    column = session.get(DatasetColumn, source_id)
    if column is not None:
        return model_service.SourceReference(
            source_id=column.id,
            project_id=column.project_id,
            source_type="DatasetColumn",
        )
    issue = session.get(DataQualityIssue, source_id)
    if issue is not None:
        return model_service.SourceReference(
            source_id=issue.id,
            project_id=issue.project_id,
            source_type="DataQualityIssue",
        )
    return None


def _input(
    session: Session, version: DatasetVersion
) -> tuple[CleaningPlanSuggestionInput, tuple[uuid.UUID, ...]]:
    columns = list(
        session.exec(
            select(DatasetColumn)
            .where(DatasetColumn.dataset_version_id == version.id)
            .order_by(col(DatasetColumn.column_order))
        )
    )
    issues = list(
        session.exec(
            select(DataQualityIssue)
            .where(DataQualityIssue.dataset_version_id == version.id)
            .order_by(col(DataQualityIssue.created_at), col(DataQualityIssue.id))
            .limit(100)
        )
    )
    if not columns or not issues:
        raise ContractError(
            status_code=409,
            code="MODEL_SOURCE_REQUIRED",
            message="A field dictionary and quality issues are required for suggestions.",
        )
    payload = CleaningPlanSuggestionInput(
        dataset_version_id=version.id,
        data_hash=version.data_hash,
        row_count=version.row_count or 0,
        column_count=version.column_count or 0,
        columns=[
            SuggestionColumn(
                id=column.id,
                name=column.source_name,
                inferred_type=column.inferred_type,
                confirmed_type=column.confirmed_type,
                missing_ratio=column.missing_ratio or 0,
                unique_count=column.unique_count or 0,
                is_identifier=column.is_identifier,
                is_sensitive=column.is_sensitive,
            )
            for column in columns
        ],
        issues=[
            SuggestionIssue(
                id=issue.id,
                rule_code=issue.rule_code,
                issue_type=issue.issue_type.value,
                severity=issue.severity.value,
                column_id=issue.column_id,
                affected_row_count=issue.affected_row_count or 0,
                evidence_summary={
                    key: value
                    for key, value in issue.evidence.items()
                    if key not in {"examples", "sample_values", "values"}
                },
            )
            for issue in issues
        ],
        allowed_action_types=list(ALLOWED_ACTION_TYPES),
    )
    return payload, (
        version.id,
        *(column.id for column in columns),
        *(issue.id for issue in issues),
    )


def suggest_plan(
    session: Session,
    *,
    actor: User,
    version_id: uuid.UUID,
    payload: CleaningPlanSuggestionRequest,
    idempotency_key: str,
    provider: SuggestionProvider | None = None,
) -> project_service.OperationResult:
    version, _, _ = dataset_service._version_access(
        session,
        actor=actor,
        version_id=version_id,
        action="dataset.cleaning.plan",
    )
    digest = project_service.request_hash(
        {"version_id": str(version.id), "payload": payload}
    )
    replay = project_service._replay_or_conflict(
        session,
        actor_id=actor.id,
        project_id=version.project_id,
        method="POST",
        path_template=PATH,
        key=idempotency_key,
        payload_hash=digest,
    )
    if replay is not None:
        return replay
    model_input, source_ids = _input(session, version)
    contract = get_prompt_contract(PROMPT_ID, PROMPT_VERSION)
    selected_provider = provider
    provider_name = "mock"
    model_name = "fixture"
    mode = model_service.ModelExecutionMode.MOCK
    fixture_id: str | None = (
        f"inline-{model_service.canonical_hash(payload.fixture_output)}"
    )
    if payload.mode == "LIVE":
        if selected_provider is None and settings.model_status == "CONFIGURED":
            selected_provider = ConfiguredSuggestionProvider()
        provider_name = (
            selected_provider.provider_name if selected_provider else "unconfigured"
        )
        model_name = (
            selected_provider.model_name if selected_provider else "unconfigured"
        )
        mode = model_service.ModelExecutionMode.LIVE
        fixture_id = None
    invocation = model_service.create_model_invocation(
        session,
        command=model_service.InvocationCreate(
            project_id=version.project_id,
            authorization_actor=actor,
            actor_type=AuditActorType.USER,
            actor_id=str(actor.id),
            task_type=TASK_TYPE,
            prompt_id=PROMPT_ID,
            prompt_version=PROMPT_VERSION,
            prompt_content_hash=contract.content_hash,
            input_schema_name="CleaningPlanSuggestionInput",
            input_schema_version="1.0",
            output_schema_name="CleaningPlanSuggestion",
            output_schema_version="1.0",
            requested_data_access_level=ModelDataAccessLevel.REDACTED_CONTENT,
            max_allowed_data_access_level=ModelDataAccessLevel.REDACTED_CONTENT,
            effective_data_access_level=ModelDataAccessLevel.METADATA_ONLY,
            source_ids=source_ids,
            sanitized_input=model_input,
            mode=mode,
            provider=provider_name,
            model=model_name,
            fixture_id=fixture_id,
            execution_metadata={"sensitive_values_sent": False},
        ),
        source_resolver=_source_resolver,
    )
    model_service.mark_model_invocation_running(session, invocation_id=invocation.id)
    try:
        if payload.mode == "MOCK":
            raw = payload.fixture_output
        elif selected_provider is None:
            raise ModelProviderError(
                "MODEL_PROVIDER_UNCONFIGURED",
                "No CleaningPlan suggestion provider is configured.",
                retryable=False,
            )
        else:
            raw = selected_provider.generate(model_input)
        suggestion = CleaningPlanSuggestion.model_validate(raw)
        cleaning_service._validate_action_scope(
            session, version=version, actions=suggestion.actions
        )
    except (ValidationError, ContractError, ModelProviderError) as error:
        code = str(getattr(error, "code", "MODEL_OUTPUT_SCHEMA_INVALID"))
        model_service.fail_model_invocation(
            session,
            invocation_id=invocation.id,
            error_code=code,
            degradation={
                "requested_capability": "CleaningPlan suggestion",
                "primary_provider": provider_name,
                "fallback_provider": None,
                "reason_code": code,
                "impact": "No suggestion or CleaningPlan was created.",
                "result_status": "FAILED",
                "user_visible_message": "The AI suggestion could not be validated.",
            },
        )
        raise ContractError(
            status_code=503
            if code in {"MODEL_PROVIDER_UNAVAILABLE", "MODEL_PROVIDER_UNCONFIGURED"}
            else 422,
            code=code,
            message="The AI suggestion failed closed and was not persisted as a plan.",
        ) from error
    model_service.complete_model_invocation(
        session,
        invocation_id=invocation.id,
        sanitized_output=suggestion.model_dump(mode="json"),
    )
    result = project_service.OperationResult(
        data=jsonable_encoder(
            {
                "model_invocation_id": invocation.id,
                "status": "CANDIDATE",
                "suggestion": suggestion,
                "allowed_actions": ["cleaning_plan.create"],
            }
        ),
        status_code=200,
    )
    project_service._store_idempotency(
        session,
        actor_id=actor.id,
        project_id=version.project_id,
        method="POST",
        path_template=PATH,
        key=idempotency_key,
        payload_hash=digest,
        result=result,
    )
    project_service._commit(session)
    return result
