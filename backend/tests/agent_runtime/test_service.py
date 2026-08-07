import uuid

import pytest
from sqlalchemy import delete, update
from sqlalchemy.exc import DBAPIError
from sqlmodel import Session, col, select

from app import crud
from app.agent_runtime import service
from app.agent_runtime.schemas import (
    AgentRunCreate,
    AgentRunView,
    SafeSummary,
    ToolCallRequest,
)
from app.api.errors import ContractError
from app.models import (
    AgentEvent,
    AgentEventType,
    AgentRun,
    AgentRunStatus,
    AuditLog,
    ProjectType,
    ResearchProject,
    ToolCall,
    ToolCallStatus,
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
        payload=ProjectCreate(name="M8 runtime", project_type=ProjectType.RESEARCH),
        idempotency_key=str(uuid.uuid4()),
    )
    assert result.data is not None
    project = db.get(ResearchProject, uuid.UUID(result.data["id"]))
    assert project is not None
    return owner, project


def create_run(
    db: Session, owner: User, project: ResearchProject, key: str | None = None
) -> AgentRunView:
    return service.create_agent_run(
        db,
        actor=owner,
        command=AgentRunCreate(
            project_id=project.id,
            safe_input_summary=SafeSummary(kind="goal", text="Review current project"),
            idempotency_key=key or str(uuid.uuid4()),
        ),
    )


def test_agent_run_idempotency_state_events_and_terminal_database_guard(
    db: Session,
) -> None:
    owner, project = create_project(db)
    key = str(uuid.uuid4())
    first = create_run(db, owner, project, key)
    replay = create_run(db, owner, project, key)
    assert replay.id == first.id and replay.idempotency_replayed is True
    with pytest.raises(ContractError) as mismatch:
        service.create_agent_run(
            db,
            actor=owner,
            command=AgentRunCreate(
                project_id=project.id,
                safe_input_summary=SafeSummary(kind="goal", text="Different"),
                idempotency_key=key,
            ),
        )
    assert mismatch.value.code == "IDEMPOTENCY_CONFLICT"
    planning = service.transition_agent_run(
        db,
        actor=owner,
        project_id=project.id,
        agent_run_id=first.id,
        target=AgentRunStatus.PLANNING,
    )
    assert planning.status == AgentRunStatus.PLANNING
    event = service.append_agent_event(
        db,
        actor=owner,
        project_id=project.id,
        agent_run_id=first.id,
        event_type=AgentEventType.USER_MESSAGE,
        safe_summary=SafeSummary(kind="user_message", text="Continue"),
    )
    assert event.sequence_number == 1 and "Continue" not in event.content_hash
    cancelled = service.cancel_agent_run(
        db, actor=owner, project_id=project.id, agent_run_id=first.id
    )
    assert cancelled.status == AgentRunStatus.CANCELLED
    with pytest.raises(ContractError):
        service.append_agent_event(
            db,
            actor=owner,
            project_id=project.id,
            agent_run_id=first.id,
            event_type=AgentEventType.CONTINUE_INTENT,
            safe_summary=SafeSummary(kind="continue"),
        )
    try:
        with pytest.raises(DBAPIError, match="immutable"):
            db.exec(
                update(AgentRun)
                .where(col(AgentRun.id) == first.id)
                .values(status=AgentRunStatus.PLANNING)
            )
            db.commit()
    finally:
        db.rollback()
    try:
        with pytest.raises(DBAPIError, match="append-only"):
            db.exec(delete(AgentEvent).where(col(AgentEvent.id) == event.id))
            db.commit()
    finally:
        db.rollback()


def test_tool_call_policy_idempotency_terminal_and_audit(db: Session) -> None:
    owner, project = create_project(db)
    run = create_run(db, owner, project)
    service.transition_agent_run(
        db,
        actor=owner,
        project_id=project.id,
        agent_run_id=run.id,
        target=AgentRunStatus.PLANNING,
    )
    command = ToolCallRequest(
        agent_run_id=run.id,
        tool_name="get_project_state",
        safe_input_summary=SafeSummary(kind="tool", text="state"),
        idempotency_key=str(uuid.uuid4()),
    )
    first = service.request_tool_call(
        db, actor=owner, project_id=project.id, command=command
    )
    replay = service.request_tool_call(
        db, actor=owner, project_id=project.id, command=command
    )
    assert replay.id == first.id and replay.idempotency_replayed is True
    running = service.transition_tool_call(
        db,
        actor=owner,
        project_id=project.id,
        tool_call_id=first.id,
        target=ToolCallStatus.RUNNING,
    )
    completed = service.transition_tool_call(
        db,
        actor=owner,
        project_id=project.id,
        tool_call_id=first.id,
        target=ToolCallStatus.COMPLETED,
        safe_output_summary=SafeSummary(
            kind="result", attributes={"artifact_count": 0}
        ),
    )
    assert (
        running.status == ToolCallStatus.RUNNING
        and completed.status == ToolCallStatus.COMPLETED
    )
    stored = db.get(ToolCall, first.id)
    assert stored is not None and stored.output_hash is not None
    audits = db.exec(select(AuditLog).where(AuditLog.tool_call_id == first.id)).all()
    assert [audit.action for audit in audits] == [
        "TOOL_CALL_REQUESTED",
        "TOOL_CALL_RUNNING",
        "TOOL_CALL_COMPLETED",
    ]
    try:
        with pytest.raises(DBAPIError, match="immutable"):
            db.exec(
                update(ToolCall)
                .where(col(ToolCall.id) == first.id)
                .values(status=ToolCallStatus.RUNNING)
            )
            db.commit()
    finally:
        db.rollback()


def test_cross_project_and_unregistered_tools_fail_closed(db: Session) -> None:
    owner, project = create_project(db)
    other_owner, other_project = create_project(db)
    run = create_run(db, owner, project)
    with pytest.raises(ContractError) as hidden:
        service.get_agent_run(
            db, actor=other_owner, project_id=project.id, agent_run_id=run.id
        )
    assert hidden.value.status_code == 404
    with pytest.raises(ContractError) as cross_project:
        service.request_tool_call(
            db,
            actor=owner,
            project_id=other_project.id,
            command=ToolCallRequest(
                agent_run_id=run.id,
                tool_name="get_project_state",
                safe_input_summary=SafeSummary(kind="tool"),
                idempotency_key=str(uuid.uuid4()),
            ),
        )
    assert cross_project.value.status_code == 404
    with pytest.raises(ContractError) as prohibited:
        service.request_tool_call(
            db,
            actor=owner,
            project_id=project.id,
            command=ToolCallRequest(
                agent_run_id=run.id,
                tool_name="execute_shell",
                safe_input_summary=SafeSummary(kind="tool"),
                idempotency_key=str(uuid.uuid4()),
            ),
        )
    assert prohibited.value.code == "PROHIBITED_TOOL"
