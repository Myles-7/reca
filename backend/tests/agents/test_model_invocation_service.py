import json
import uuid
from dataclasses import replace

import pytest
from sqlalchemy import update
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlmodel import Session, select

from app import crud
from app.agents import service
from app.agents.prompts import get_prompt_contract
from app.agents.service import (
    DegradationRecord,
    InvocationCreate,
    ModelExecutionMode,
    ModelGovernanceError,
    SourceReference,
)
from app.api.errors import ContractError
from app.models import (
    AuditActorType,
    AuditLog,
    AuditOutcome,
    ModelDataAccessLevel,
    ModelInvocation,
    ModelInvocationStatus,
    ResearchProject,
    User,
    UserCreate,
)
from app.projects import service as project_service
from app.projects.schemas import ProjectCreate
from tests.utils.utils import random_email, random_lower_string


def create_project(db: Session) -> tuple[User, ResearchProject]:
    owner = crud.create_user(
        session=db,
        user_create=UserCreate(email=random_email(), password=random_lower_string()),
    )
    result = project_service.create_project(
        db,
        actor=owner,
        payload=ProjectCreate(name="Model governance", project_type="RESEARCH"),
        idempotency_key=str(uuid.uuid4()),
    )
    assert result.data is not None
    project = db.get(ResearchProject, uuid.UUID(result.data["id"]))
    assert project is not None
    return owner, project


def command(
    *,
    owner: User,
    project: ResearchProject,
    mode: ModelExecutionMode = ModelExecutionMode.MOCK,
    effective: ModelDataAccessLevel = ModelDataAccessLevel.METADATA_ONLY,
) -> InvocationCreate:
    contract = get_prompt_contract("governance-contract-test", "1.0.0")
    return InvocationCreate(
        project_id=project.id,
        authorization_actor=owner,
        actor_type=AuditActorType.USER,
        actor_id=str(owner.id),
        task_type=contract.task_type,
        prompt_id=contract.prompt_id,
        prompt_version=contract.prompt_version,
        prompt_content_hash=contract.content_hash,
        input_schema_name=contract.input_schema.name,
        input_schema_version=contract.input_schema.version,
        output_schema_name=contract.output_schema.name,
        output_schema_version=contract.output_schema.version,
        requested_data_access_level=ModelDataAccessLevel.METADATA_ONLY,
        max_allowed_data_access_level=ModelDataAccessLevel.METADATA_ONLY,
        effective_data_access_level=effective,
        source_ids=(),
        sanitized_input={"topic": "fixture", "secret": "must-not-be-persisted"},
        mode=mode,
        fixture_id="mock-governance-v1" if mode == ModelExecutionMode.MOCK else None,
        recording_id="recording-v1" if mode == ModelExecutionMode.RECORDED else None,
        recording_version="1.0" if mode == ModelExecutionMode.RECORDED else None,
        recording_hash=service.canonical_hash({"status": "recorded-fixture"})
        if mode == ModelExecutionMode.RECORDED
        else None,
        recording_license_status="INTERNAL_FIXTURE"
        if mode == ModelExecutionMode.RECORDED
        else None,
        recording_redaction_status="REVIEWED"
        if mode == ModelExecutionMode.RECORDED
        else None,
        request_id="trace-model-1",
    )


def test_mock_invocation_is_labeled_hashed_audited_and_immutable(db: Session) -> None:
    owner, project = create_project(db)
    invocation = service.create_model_invocation(
        db, command=command(owner=owner, project=project)
    )

    assert invocation.status == ModelInvocationStatus.PENDING
    assert invocation.provider is None
    assert invocation.model is None
    assert invocation.implementation_metadata == {
        "mode": "MOCK",
        "fixture_id": "mock-governance-v1",
    }
    assert invocation.input_hash == service.canonical_hash(
        {"topic": "fixture", "secret": "must-not-be-persisted"}
    )

    running = service.mark_model_invocation_running(db, invocation_id=invocation.id)
    completed = service.complete_model_invocation(
        db,
        invocation_id=running.id,
        sanitized_output={"status": "fixture-only"},
    )
    assert completed.status == ModelInvocationStatus.SUCCEEDED
    assert completed.output_hash == service.canonical_hash({"status": "fixture-only"})

    audits = db.exec(
        select(AuditLog).where(
            AuditLog.object_type == "model_invocation",
            AuditLog.object_id == invocation.id,
        )
    ).all()
    serialized = json.dumps([audit.after_snapshot for audit in audits])
    assert [audit.action for audit in audits] == [
        "MODEL_INVOCATION_CREATED",
        "MODEL_INVOCATION_SUCCEEDED",
    ]
    assert all(audit.model_invocation_id == invocation.id for audit in audits)
    assert "must-not-be-persisted" not in serialized

    with pytest.raises(DBAPIError):
        db.execute(
            update(ModelInvocation)
            .where(ModelInvocation.id == invocation.id)
            .values(input_hash="0" * 64)
        )
        db.commit()
    db.rollback()


def test_recorded_invocation_is_offline_and_explicitly_labeled(db: Session) -> None:
    owner, project = create_project(db)
    invocation = service.create_model_invocation(
        db,
        command=command(owner=owner, project=project, mode=ModelExecutionMode.RECORDED),
    )

    assert invocation.implementation_metadata == {
        "mode": "RECORDED",
        "recording_id": "recording-v1",
        "recording_version": "1.0",
        "recording_hash": service.canonical_hash({"status": "recorded-fixture"}),
        "recording_license_status": "INTERNAL_FIXTURE",
        "recording_redaction_status": "REVIEWED",
        "network_access": "DISABLED",
    }
    service.mark_model_invocation_running(db, invocation_id=invocation.id)
    completed = service.complete_model_invocation(
        db,
        invocation_id=invocation.id,
        sanitized_output={"status": "recorded-fixture"},
    )
    assert completed.status == ModelInvocationStatus.SUCCEEDED


def test_caller_owned_invocation_rolls_back_with_parent_transaction(
    db: Session,
) -> None:
    owner, project = create_project(db)
    invocation = service.create_model_invocation(
        db,
        command=command(owner=owner, project=project),
        commit=False,
    )
    invocation_id = invocation.id

    db.rollback()

    assert db.get(ModelInvocation, invocation_id) is None
    assert not db.exec(
        select(AuditLog).where(AuditLog.model_invocation_id == invocation_id)
    ).all()


def test_live_invocation_requires_and_persists_provider_identity(db: Session) -> None:
    owner, project = create_project(db)
    live = replace(
        command(owner=owner, project=project),
        mode=ModelExecutionMode.LIVE,
        fixture_id=None,
        provider="openai-compatible",
        model="reca-structured-model",
    )
    invocation = service.create_model_invocation(db, command=live)
    assert invocation.provider == "openai-compatible"
    assert invocation.model == "reca-structured-model"
    assert invocation.implementation_metadata == {
        "mode": "LIVE",
        "network_access": "ENABLED",
    }

    with pytest.raises(ModelGovernanceError) as captured:
        service.create_model_invocation(
            db, command=replace(live, provider=None, model=None)
        )
    assert captured.value.code == "MODEL_PROVIDER_INVALID"


def test_prompt_hash_schema_and_access_escalation_are_rejected(db: Session) -> None:
    owner, project = create_project(db)
    base = command(owner=owner, project=project)

    for changed, code in (
        (replace(base, prompt_content_hash="0" * 64), "PROMPT_CONTRACT_MISMATCH"),
        (replace(base, output_schema_version="2.0"), "PROMPT_CONTRACT_MISMATCH"),
        (
            replace(
                base,
                effective_data_access_level=ModelDataAccessLevel.REDACTED_CONTENT,
            ),
            "MODEL_DATA_ACCESS_DENIED",
        ),
    ):
        with pytest.raises(ModelGovernanceError) as exc_info:
            service.create_model_invocation(db, command=changed)
        assert exc_info.value.code == code

    recorded = service.create_model_invocation(
        db,
        command=command(owner=owner, project=project, mode=ModelExecutionMode.RECORDED),
    )
    service.mark_model_invocation_running(db, invocation_id=recorded.id)
    with pytest.raises(ModelGovernanceError) as recording_error:
        service.complete_model_invocation(
            db,
            invocation_id=recorded.id,
            sanitized_output={"status": "different-recording"},
        )
    assert recording_error.value.code == "MODEL_RECORDING_HASH_MISMATCH"


def test_cross_project_source_and_nonmember_are_rejected(
    db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    owner, project = create_project(db)
    outsider, other_project = create_project(db)
    source_id = uuid.uuid4()
    base_contract = get_prompt_contract("governance-contract-test", "1.0.0")
    monkeypatch.setattr(
        service,
        "get_prompt_contract",
        lambda *_args, **_kwargs: replace(
            base_contract, required_source_types=("artifact",)
        ),
    )
    with_source = replace(
        command(owner=owner, project=project), source_ids=(source_id,)
    )

    with pytest.raises(ModelGovernanceError) as exc_info:
        service.create_model_invocation(
            db,
            command=with_source,
            source_resolver=lambda _session, resolved_id: SourceReference(
                source_id=resolved_id,
                project_id=other_project.id,
                source_type="artifact",
            ),
        )
    assert exc_info.value.code == "MODEL_SOURCE_INVALID"

    with pytest.raises(ContractError) as authorization_error:
        service.create_model_invocation(
            db,
            command=replace(with_source, authorization_actor=outsider),
            source_resolver=lambda _session, resolved_id: SourceReference(
                source_id=resolved_id,
                project_id=project.id,
                source_type="artifact",
            ),
        )
    assert getattr(authorization_error.value, "code", None) == "RESOURCE_NOT_FOUND"


def test_audit_model_invocation_relation_enforces_project_scope(db: Session) -> None:
    owner, project = create_project(db)
    _, other_project = create_project(db)
    invocation = service.create_model_invocation(
        db, command=command(owner=owner, project=project)
    )
    invalid_audit = AuditLog(
        project_id=other_project.id,
        actor_type=AuditActorType.SYSTEM,
        actor_id="cross-project-test",
        action="MODEL_INVOCATION_CROSS_PROJECT_TEST",
        object_type="model_invocation",
        object_id=invocation.id,
        model_invocation_id=invocation.id,
        outcome=AuditOutcome.FAILED,
    )

    savepoint = db.begin_nested()
    db.add(invalid_audit)
    with pytest.raises(IntegrityError):
        db.flush()
    savepoint.rollback()

    assert "model_invocation_id" in AuditLog.model_fields


def test_failed_invocation_is_terminal_and_retry_creates_new_record(
    db: Session,
) -> None:
    owner, project = create_project(db)
    first = service.create_model_invocation(
        db, command=command(owner=owner, project=project)
    )
    failed = service.fail_model_invocation(
        db,
        invocation_id=first.id,
        error_code="RECORDED_FIXTURE_REJECTED",
        degradation=DegradationRecord(
            requested_capability="GOVERNANCE_CONTRACT_TEST",
            primary_provider=None,
            fallback_provider="RECORDED",
            reason_code="FIXTURE_UNAVAILABLE",
            impact="No model output was produced.",
            result_status="FAILED",
            user_visible_message="The recorded fixture is unavailable.",
        ),
    )
    retry = service.create_model_invocation(
        db,
        command=replace(
            command(owner=owner, project=project),
            retry_of_invocation_id=failed.id,
        ),
    )

    assert failed.status == ModelInvocationStatus.FAILED
    assert retry.id != failed.id
    assert retry.implementation_metadata is not None
    assert retry.implementation_metadata["retry_of_invocation_id"] == str(failed.id)
