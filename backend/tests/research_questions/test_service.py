from __future__ import annotations

import threading
import uuid

import pytest
from sqlalchemy import update
from sqlalchemy.exc import DBAPIError
from sqlmodel import Session, select

from app.api.errors import ContractError
from app.approvals import service as approval_service
from app.core.db import engine
from app.models import (
    ApprovalStatus,
    AuditLog,
    ResearchProject,
    ResearchQuestion,
    ResearchQuestionStatus,
    ResearchQuestionVersion,
    ResearchQuestionVersionStatus,
    User,
)
from app.projects.schemas import ProjectCreate
from app.projects.service import create_project
from app.research_questions import service
from app.research_questions.schemas import ResearchQuestionVersionContent
from tests.utils.user import create_random_user


def make_project(
    db: Session, actor: User, name: str = "M2 RQ project"
) -> ResearchProject:
    result = create_project(
        db,
        actor=actor,
        payload=ProjectCreate(name=name, project_type="RESEARCH"),
        idempotency_key=str(uuid.uuid4()),
    )
    assert result.data is not None
    project = db.get(ResearchProject, uuid.UUID(str(result.data["id"])))
    assert project is not None
    return project


def content(raw_input: str) -> ResearchQuestionVersionContent:
    return ResearchQuestionVersionContent(
        raw_input=raw_input,
        normalized_question=f"Normalized: {raw_input}",
        research_object="teacher education students",
        independent_variables=["generative AI use"],
        dependent_variables=["learning engagement"],
        uncertainties={"data_source": "needs confirmation"},
    )


def make_ready_version(
    db: Session, actor: User, project: ResearchProject
) -> tuple[ResearchQuestion, ResearchQuestionVersion]:
    question, version = service.create_research_question(
        db,
        actor=actor,
        project_id=project.id,
        content=content("Initial research idea"),
    )
    version = service.transition_version_status(
        db,
        actor=actor,
        version_id=version.id,
        target_status=ResearchQuestionVersionStatus.READY,
        reason="Required fields were reviewed.",
    )
    db.refresh(question)
    assert question.status == ResearchQuestionStatus.DRAFT
    return question, version


def test_create_and_save_always_append_versions_with_audit(db: Session) -> None:
    actor = create_random_user(db)
    project = make_project(db, actor)
    question, first = service.create_research_question(
        db,
        actor=actor,
        project_id=project.id,
        content=content("First idea"),
    )
    second = service.save_new_version(
        db,
        actor=actor,
        research_question_id=question.id,
        based_on_version_id=first.id,
        content=content("Refined idea"),
        change_reason="Narrow the population.",
    )

    db.refresh(question)
    versions = db.exec(
        select(ResearchQuestionVersion)
        .where(ResearchQuestionVersion.research_question_id == question.id)
        .order_by(ResearchQuestionVersion.version_number)
    ).all()
    assert [(item.id, item.version_number) for item in versions] == [
        (first.id, 1),
        (second.id, 2),
    ]
    assert first.raw_input == "First idea"
    assert question.current_version_id == second.id
    audit = db.exec(
        select(AuditLog).where(
            AuditLog.object_id == second.id,
            AuditLog.action == "RESEARCH_QUESTION_VERSION_CREATED",
        )
    ).one()
    assert audit.project_id == project.id
    assert audit.reason == "Narrow the population."
    assert audit.before_snapshot == {
        "based_on_version_id": str(first.id),
        "version_number": 1,
    }


def test_stale_save_is_rejected_without_creating_a_version(db: Session) -> None:
    actor = create_random_user(db)
    project = make_project(db, actor)
    question, first = service.create_research_question(
        db,
        actor=actor,
        project_id=project.id,
        content=content("First"),
    )
    service.save_new_version(
        db,
        actor=actor,
        research_question_id=question.id,
        based_on_version_id=first.id,
        content=content("Second"),
        change_reason="First save",
    )

    with pytest.raises(ContractError) as error:
        service.save_new_version(
            db,
            actor=actor,
            research_question_id=question.id,
            based_on_version_id=first.id,
            content=content("Conflicting second"),
            change_reason="Stale save",
        )
    assert error.value.code == "RESOURCE_VERSION_CONFLICT"
    count = len(
        db.exec(
            select(ResearchQuestionVersion).where(
                ResearchQuestionVersion.research_question_id == question.id
            )
        ).all()
    )
    assert count == 2


def test_duplicate_version_number_is_rejected_by_database(db: Session) -> None:
    actor = create_random_user(db)
    project = make_project(db, actor)
    question, _version = service.create_research_question(
        db,
        actor=actor,
        project_id=project.id,
        content=content("Unique version number"),
    )
    duplicate = ResearchQuestionVersion(
        research_question_id=question.id,
        project_id=project.id,
        version_number=1,
        raw_input="Duplicate version number",
        created_by=actor.id,
    )
    db.add(duplicate)
    with pytest.raises(DBAPIError):
        db.commit()
    db.rollback()


def test_domain_statuses_reject_ai_output_values_and_illegal_transitions(
    db: Session,
) -> None:
    assert "NEEDS_USER_INPUT" not in ResearchQuestionVersionStatus
    assert "CANDIDATES_READY" not in ResearchQuestionVersionStatus
    actor = create_random_user(db)
    project = make_project(db, actor)
    _question, version = service.create_research_question(
        db,
        actor=actor,
        project_id=project.id,
        content=content("Status test"),
    )

    with pytest.raises(ContractError) as error:
        service.transition_version_status(
            db,
            actor=actor,
            version_id=version.id,
            target_status=ResearchQuestionVersionStatus.CONFIRMED,
        )
    assert error.value.code == "INVALID_STATE_TRANSITION"


def test_confirmation_requires_approved_record_and_updates_project_atomically(
    db: Session,
) -> None:
    actor = create_random_user(db)
    project = make_project(db, actor)
    question, version = make_ready_version(db, actor, project)

    with pytest.raises(DBAPIError):
        db.execute(
            update(ResearchQuestionVersion)
            .where(ResearchQuestionVersion.id == version.id)
            .values(status=ResearchQuestionVersionStatus.CONFIRMED)
        )
        db.commit()
    db.rollback()

    approval = service.request_confirmation(db, actor=actor, version_id=version.id)
    approval_service.decide_approval(
        db,
        actor=actor,
        approval_id=approval.id,
        decision=ApprovalStatus.APPROVED,
        decision_reason="The scoped question is ready.",
        item_decisions=[],
        idempotency_key=str(uuid.uuid4()),
    )

    db.refresh(approval)
    db.refresh(version)
    db.refresh(question)
    db.refresh(project)
    assert approval.status == ApprovalStatus.APPROVED
    assert version.status == ResearchQuestionVersionStatus.CONFIRMED
    assert question.status == ResearchQuestionStatus.CONFIRMED
    assert project.current_research_question_version_id == version.id
    audit = db.exec(
        select(AuditLog).where(
            AuditLog.action == "RESEARCH_QUESTION_CONFIRMED",
            AuditLog.object_id == version.id,
        )
    ).one()
    assert audit.approval_id == approval.id


def test_database_rejects_inserting_confirmed_version_without_approval(
    db: Session,
) -> None:
    actor = create_random_user(db)
    project = make_project(db, actor)
    question, first = service.create_research_question(
        db,
        actor=actor,
        project_id=project.id,
        content=content("Approval insert guard"),
    )
    invalid = ResearchQuestionVersion(
        research_question_id=question.id,
        project_id=project.id,
        version_number=first.version_number + 1,
        raw_input="Unapproved confirmed insert",
        status=ResearchQuestionVersionStatus.CONFIRMED,
        created_by=actor.id,
    )
    db.add(invalid)
    with pytest.raises(DBAPIError):
        db.commit()
    db.rollback()


def test_rejected_confirmation_returns_ready_version_to_draft(db: Session) -> None:
    actor = create_random_user(db)
    project = make_project(db, actor)
    _question, version = make_ready_version(db, actor, project)
    approval = service.request_confirmation(db, actor=actor, version_id=version.id)

    approval_service.decide_approval(
        db,
        actor=actor,
        approval_id=approval.id,
        decision=ApprovalStatus.REJECTED,
        decision_reason="Clarify the population.",
        item_decisions=[],
        idempotency_key=str(uuid.uuid4()),
    )

    db.refresh(version)
    assert version.status == ResearchQuestionVersionStatus.DRAFT


def test_approval_becomes_stale_when_a_new_version_is_saved(db: Session) -> None:
    actor = create_random_user(db)
    project = make_project(db, actor)
    question, version = make_ready_version(db, actor, project)
    approval = service.request_confirmation(db, actor=actor, version_id=version.id)
    service.save_new_version(
        db,
        actor=actor,
        research_question_id=question.id,
        based_on_version_id=version.id,
        content=content("New current version"),
        change_reason="Changed after requesting approval.",
    )

    with pytest.raises(ContractError) as error:
        approval_service.decide_approval(
            db,
            actor=actor,
            approval_id=approval.id,
            decision=ApprovalStatus.APPROVED,
            decision_reason="This decision is stale.",
            item_decisions=[],
            idempotency_key=str(uuid.uuid4()),
        )
    assert error.value.code == "APPROVAL_STALE"
    db.refresh(approval)
    db.refresh(version)
    assert approval.status == ApprovalStatus.SUPERSEDED
    assert version.status == ResearchQuestionVersionStatus.READY


def test_confirming_new_version_supersedes_previous_confirmation(db: Session) -> None:
    actor = create_random_user(db)
    project = make_project(db, actor)
    question, first = make_ready_version(db, actor, project)
    first_approval = service.request_confirmation(db, actor=actor, version_id=first.id)
    approval_service.decide_approval(
        db,
        actor=actor,
        approval_id=first_approval.id,
        decision=ApprovalStatus.APPROVED,
        decision_reason="Confirm first version.",
        item_decisions=[],
        idempotency_key=str(uuid.uuid4()),
    )
    second = service.save_new_version(
        db,
        actor=actor,
        research_question_id=question.id,
        based_on_version_id=first.id,
        content=content("Second confirmed version"),
        change_reason="Refine the relationship.",
    )
    second = service.transition_version_status(
        db,
        actor=actor,
        version_id=second.id,
        target_status=ResearchQuestionVersionStatus.READY,
    )
    second_approval = service.request_confirmation(
        db, actor=actor, version_id=second.id
    )
    approval_service.decide_approval(
        db,
        actor=actor,
        approval_id=second_approval.id,
        decision=ApprovalStatus.APPROVED,
        decision_reason="Confirm replacement.",
        item_decisions=[],
        idempotency_key=str(uuid.uuid4()),
    )

    db.refresh(first)
    db.refresh(second)
    assert first.status == ResearchQuestionVersionStatus.SUPERSEDED
    assert second.status == ResearchQuestionVersionStatus.CONFIRMED


def test_cross_project_question_and_current_pointer_are_rejected(db: Session) -> None:
    actor = create_random_user(db)
    first_project = make_project(db, actor, "First project")
    second_project = make_project(db, actor, "Second project")
    first_question, _first_version = service.create_research_question(
        db,
        actor=actor,
        project_id=first_project.id,
        content=content("First project question"),
    )
    _second_question, second_version = service.create_research_question(
        db,
        actor=actor,
        project_id=second_project.id,
        content=content("Second project question"),
    )

    invalid = ResearchQuestionVersion(
        research_question_id=first_question.id,
        project_id=second_project.id,
        version_number=2,
        raw_input="Cross-project version",
        created_by=actor.id,
    )
    db.add(invalid)
    with pytest.raises(DBAPIError):
        db.commit()
    db.rollback()

    with pytest.raises(DBAPIError):
        db.execute(
            update(ResearchQuestion)
            .where(ResearchQuestion.id == first_question.id)
            .values(current_version_id=second_version.id)
        )
        db.commit()
    db.rollback()


def test_version_content_is_database_immutable(db: Session) -> None:
    actor = create_random_user(db)
    project = make_project(db, actor)
    _question, version = service.create_research_question(
        db,
        actor=actor,
        project_id=project.id,
        content=content("Immutable input"),
    )

    with pytest.raises(DBAPIError):
        db.execute(
            update(ResearchQuestionVersion)
            .where(ResearchQuestionVersion.id == version.id)
            .values(raw_input="Mutated input")
        )
        db.commit()
    db.rollback()
    db.refresh(version)
    assert version.raw_input == "Immutable input"


def test_concurrent_saves_from_same_base_allow_one_winner(db: Session) -> None:
    actor = create_random_user(db)
    project = make_project(db, actor)
    question, base = service.create_research_question(
        db,
        actor=actor,
        project_id=project.id,
        content=content("Concurrent base"),
    )
    barrier = threading.Barrier(2)
    outcomes: list[str] = []
    lock = threading.Lock()

    def save(label: str) -> None:
        with Session(engine) as worker_session:
            worker_actor = worker_session.get(User, actor.id)
            assert worker_actor is not None
            barrier.wait()
            try:
                service.save_new_version(
                    worker_session,
                    actor=worker_actor,
                    research_question_id=question.id,
                    based_on_version_id=base.id,
                    content=content(label),
                    change_reason=label,
                )
                outcome = "saved"
            except ContractError as error:
                outcome = error.code
            with lock:
                outcomes.append(outcome)

    threads = [
        threading.Thread(target=save, args=("Concurrent A",)),
        threading.Thread(target=save, args=("Concurrent B",)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)
        assert not thread.is_alive()

    assert sorted(outcomes) == ["RESOURCE_VERSION_CONFLICT", "saved"]
    versions = db.exec(
        select(ResearchQuestionVersion).where(
            ResearchQuestionVersion.research_question_id == question.id
        )
    ).all()
    assert sorted(item.version_number for item in versions) == [1, 2]
