from __future__ import annotations

import hashlib
import uuid

import pytest
from sqlmodel import Session, select

from app.api.errors import ContractError
from app.exports import service
from app.exports.schemas import ExportReadinessRequest, ReproPackageCreate
from app.models import (
    AuditActorType,
    AuditResult,
    AuditType,
    Claim,
    ClaimConfidence,
    ClaimStatus,
    ClaimType,
    Export,
    Job,
    JobTaskType,
    ProjectMemberRole,
)
from app.projects import service as project_service
from app.projects.schemas import MemberAdd
from tests.projects.test_service import create_project
from tests.utils.user import create_random_user


class RecordingDispatcher:
    def __init__(self) -> None:
        self.calls: list[tuple[uuid.UUID, str]] = []

    def dispatch(self, *, job_id: uuid.UUID, task_id: str) -> None:
        self.calls.append((job_id, task_id))


def test_readiness_and_export_create_are_deterministic_and_idempotent(
    db: Session,
) -> None:
    owner, project = create_project(db)
    readiness_key = str(uuid.uuid4())
    readiness = service.readiness_check(
        db,
        actor=owner,
        project_id=project.id,
        request=ExportReadinessRequest(),
        idempotency_key=readiness_key,
    )
    replay = service.readiness_check(
        db,
        actor=owner,
        project_id=project.id,
        request=ExportReadinessRequest(),
        idempotency_key=readiness_key,
    )
    assert readiness.status_code == 200
    assert replay.idempotency_replayed is True
    audits = db.exec(
        select(AuditResult).where(
            AuditResult.project_id == project.id,
            AuditResult.audit_type == AuditType.EXPORT_READINESS_AUDIT,
        )
    ).all()
    assert len(audits) == 1

    dispatcher = RecordingDispatcher()
    export_key = str(uuid.uuid4())
    created = service.create_repro_package_export(
        db,
        actor=owner,
        project_id=project.id,
        request=ReproPackageCreate(),
        idempotency_key=export_key,
        dispatcher=dispatcher,
    )
    export_replay = service.create_repro_package_export(
        db,
        actor=owner,
        project_id=project.id,
        request=ReproPackageCreate(),
        idempotency_key=export_key,
        dispatcher=dispatcher,
    )
    assert created.status_code == 202
    assert export_replay.idempotency_replayed is True
    assert len(dispatcher.calls) == 1
    exports = db.exec(select(Export).where(Export.project_id == project.id)).all()
    jobs = db.exec(select(Job).where(Job.project_id == project.id)).all()
    assert len(exports) == 1
    assert len(jobs) == 1
    assert jobs[0].task_type == JobTaskType.REPRO_PACKAGE_EXPORT


def test_readiness_persists_uuid_issue_references_as_json_values(db: Session) -> None:
    owner, project = create_project(db)
    claim_text = "An unconfirmed Claim requires an explicit readiness warning."
    source_id = uuid.uuid4()
    claim = Claim(
        project_id=project.id,
        claim_type=ClaimType.MANUSCRIPT_STATEMENT,
        claim_text=claim_text,
        source_object_type="manuscript_version",
        source_object_id=source_id,
        source_location={"section": "acceptance"},
        source_hash=hashlib.sha256(str(source_id).encode()).hexdigest(),
        text_hash=hashlib.sha256(claim_text.encode()).hexdigest(),
        status=ClaimStatus.NEEDS_EVIDENCE,
        confidence=ClaimConfidence.UNKNOWN,
        created_by_actor_type=AuditActorType.USER,
        created_by_actor_id=str(owner.id),
    )
    db.add(claim)
    db.commit()

    result = service.readiness_check(
        db,
        actor=owner,
        project_id=project.id,
        request=ExportReadinessRequest(),
        idempotency_key=str(uuid.uuid4()),
    )

    warning = next(
        item for item in result.data["warnings"] if item["code"] == "CLAIM_UNCONFIRMED"
    )
    audit = db.get(AuditResult, uuid.UUID(result.data["audit_id"]))
    assert warning["object_id"] == str(claim.id)
    assert audit is not None
    assert audit.findings[0]["object_id"] == str(claim.id)
    assert audit.source_snapshot is not None
    assert audit.source_snapshot["warnings"][0]["object_id"] == str(claim.id)


@pytest.mark.parametrize("role", [ProjectMemberRole.VIEWER, ProjectMemberRole.REVIEWER])
def test_viewer_and_reviewer_cannot_create_exports(
    db: Session, role: ProjectMemberRole
) -> None:
    owner, project = create_project(db)
    member = create_random_user(db)
    project_service.add_member(
        db,
        actor=owner,
        project_id=project.id,
        payload=MemberAdd(user_id=member.id, role=role),
        idempotency_key=str(uuid.uuid4()),
    )

    with pytest.raises(ContractError) as error:
        service.create_repro_package_export(
            db,
            actor=member,
            project_id=project.id,
            request=ReproPackageCreate(),
            idempotency_key=str(uuid.uuid4()),
            dispatcher=RecordingDispatcher(),
        )
    assert error.value.status_code == 403
