from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Header

from app.api.deps import CurrentUser, SessionDep
from app.api.errors import ContractError, ContractErrorResponse
from app.api.m6_responses import (
    ApprovalRequestEnvelope,
    ClaimEnvelope,
    ManuscriptCheckRequestEnvelope,
    ManuscriptCheckRunEnvelope,
    ManuscriptCreatedEnvelope,
    ManuscriptDownloadEnvelope,
    ManuscriptEnvelope,
    ManuscriptIssueEnvelope,
    ManuscriptIssueListEnvelope,
    ManuscriptTransformationEnvelope,
    ManuscriptVersionEnvelope,
    ManuscriptVersionListEnvelope,
    ProjectManuscriptDiscoveryEnvelope,
    RevisionAuditEnvelope,
    RevisionAuditRequestEnvelope,
    TransformationExecutionEnvelope,
)
from app.core.observability import current_request_id
from app.jobs.dispatcher import dispatcher
from app.manuscripts import service, stage2
from app.manuscripts.schemas import (
    CheckRunCreate,
    ClaimCreate,
    ClaimUpdate,
    FixPlanCreate,
    IssueDecision,
    ManuscriptCreate,
    RevisionAuditCreate,
)

router = APIRouter(tags=["manuscripts"])

ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {
        "model": ContractErrorResponse,
        "description": "Malformed request or missing idempotency key.",
    },
    403: {"model": ContractErrorResponse, "description": "The action is not allowed."},
    404: {
        "model": ContractErrorResponse,
        "description": "Resource not found (no disclosure).",
    },
    409: {
        "model": ContractErrorResponse,
        "description": "Conflict or stale input, including approval stale/expired, fix not approved, hash mismatch, unsupported DOCX, low-confidence input, or invalid state.",
    },
    412: {
        "model": ContractErrorResponse,
        "description": "If-Match precondition failed.",
    },
    413: {"model": ContractErrorResponse, "description": "DOCX safety limit exceeded."},
    415: {
        "model": ContractErrorResponse,
        "description": "Unsupported document media or capability.",
    },
    422: {
        "model": ContractErrorResponse,
        "description": "Validation or source locator error.",
    },
    428: {
        "model": ContractErrorResponse,
        "description": "If-Match precondition is required.",
    },
    503: {
        "model": ContractErrorResponse,
        "description": "External capability unavailable.",
    },
}


def _meta(*, replayed: bool = False) -> dict[str, Any]:
    return {
        "request_id": current_request_id(),
        "schema_version": "1.0",
        "idempotency_replayed": replayed,
    }


def _required_key(value: str | None) -> str:
    if value is None or not value.strip():
        raise ContractError(
            status_code=400,
            code="MISSING_IDEMPOTENCY_KEY",
            message="Idempotency-Key is required for this operation.",
        )
    if len(value) > 255:
        raise ContractError(
            status_code=422,
            code="VALIDATION_ERROR",
            message="Idempotency-Key exceeds the maximum length.",
        )
    return value


def _if_match(value: str | None, *, resource: str = "resource") -> int:
    if value is None:
        raise ContractError(
            status_code=428,
            code="PRECONDITION_REQUIRED",
            message=f"If-Match is required for this {resource} operation.",
        )
    candidate = value.strip().removeprefix("W/").strip('"')
    try:
        parsed = int(candidate)
    except ValueError as error:
        raise ContractError(
            status_code=422,
            code="VALIDATION_ERROR",
            message="If-Match must contain a positive lock version.",
        ) from error
    if parsed < 1:
        raise ContractError(
            status_code=422,
            code="VALIDATION_ERROR",
            message="If-Match must contain a positive lock version.",
        )
    return parsed


@router.post(
    "/projects/{project_id}/manuscripts",
    status_code=201,
    response_model=ManuscriptCreatedEnvelope,
    responses=ERROR_RESPONSES,
)
def create_manuscript(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    project_id: uuid.UUID,
    payload: ManuscriptCreate,
) -> dict[str, Any]:
    return {
        "data": service.create_manuscript(
            session, actor=current_user, project_id=project_id, payload=payload
        ),
        "meta": _meta(),
    }


@router.get(
    "/projects/{project_id}/manuscript",
    response_model=ProjectManuscriptDiscoveryEnvelope,
    responses=ERROR_RESPONSES,
)
def discover_project_manuscript(
    *, session: SessionDep, current_user: CurrentUser, project_id: uuid.UUID
) -> dict[str, Any]:
    return {
        "data": service.discover_project_manuscripts(
            session, actor=current_user, project_id=project_id
        ),
        "meta": _meta(),
    }


@router.get(
    "/manuscripts/{manuscript_id}",
    response_model=ManuscriptEnvelope,
    responses=ERROR_RESPONSES,
)
def get_manuscript(
    *, session: SessionDep, current_user: CurrentUser, manuscript_id: uuid.UUID
) -> dict[str, Any]:
    return {
        "data": service.get_manuscript(
            session, actor=current_user, manuscript_id=manuscript_id
        ),
        "meta": _meta(),
    }


@router.get(
    "/manuscripts/{manuscript_id}/versions",
    response_model=ManuscriptVersionListEnvelope,
    responses=ERROR_RESPONSES,
)
def list_versions(
    *, session: SessionDep, current_user: CurrentUser, manuscript_id: uuid.UUID
) -> dict[str, Any]:
    return {
        "data": service.list_versions(
            session, actor=current_user, manuscript_id=manuscript_id
        ),
        "meta": _meta(),
    }


@router.get(
    "/manuscript-versions/{version_id}",
    response_model=ManuscriptVersionEnvelope,
    responses=ERROR_RESPONSES,
)
def get_version(
    *, session: SessionDep, current_user: CurrentUser, version_id: uuid.UUID
) -> dict[str, Any]:
    return {
        "data": service.get_version(session, actor=current_user, version_id=version_id),
        "meta": _meta(),
    }


@router.get(
    "/manuscript-versions/{version_id}/download",
    response_model=ManuscriptDownloadEnvelope,
    responses=ERROR_RESPONSES,
)
def download_version(
    *, session: SessionDep, current_user: CurrentUser, version_id: uuid.UUID
) -> dict[str, Any]:
    return {
        "data": service.authorize_download(
            session, actor=current_user, version_id=version_id
        ),
        "meta": _meta(),
    }


@router.post(
    "/manuscript-versions/{version_id}/check-runs",
    status_code=202,
    response_model=ManuscriptCheckRequestEnvelope,
    responses=ERROR_RESPONSES,
)
def create_check_run(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    version_id: uuid.UUID,
    payload: CheckRunCreate,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> dict[str, Any]:
    result = service.create_check_run(
        session,
        actor=current_user,
        version_id=version_id,
        payload=payload,
        idempotency_key=_required_key(idempotency_key),
        dispatcher=dispatcher,
    )
    return {"data": result.data, "meta": _meta(replayed=result.idempotency_replayed)}


@router.get(
    "/manuscript-check-runs/{run_id}",
    response_model=ManuscriptCheckRunEnvelope,
    responses=ERROR_RESPONSES,
)
def get_check_run(
    *, session: SessionDep, current_user: CurrentUser, run_id: uuid.UUID
) -> dict[str, Any]:
    return {
        "data": service.get_check_run(session, actor=current_user, run_id=run_id),
        "meta": _meta(),
    }


@router.get(
    "/manuscript-check-runs/{run_id}/issues",
    response_model=ManuscriptIssueListEnvelope,
    responses=ERROR_RESPONSES,
)
def list_issues(
    *, session: SessionDep, current_user: CurrentUser, run_id: uuid.UUID
) -> dict[str, Any]:
    return {
        "data": service.list_issues(session, actor=current_user, run_id=run_id),
        "meta": _meta(),
    }


@router.get(
    "/manuscript-issues/{issue_id}",
    response_model=ManuscriptIssueEnvelope,
    responses=ERROR_RESPONSES,
)
def get_issue(
    *, session: SessionDep, current_user: CurrentUser, issue_id: uuid.UUID
) -> dict[str, Any]:
    return {
        "data": service.get_issue(session, actor=current_user, issue_id=issue_id),
        "meta": _meta(),
    }


@router.post(
    "/manuscript-issues/{issue_id}/accept",
    response_model=ManuscriptIssueEnvelope,
    responses=ERROR_RESPONSES,
)
def accept_issue(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    issue_id: uuid.UUID,
    payload: IssueDecision,
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> dict[str, Any]:
    return {
        "data": service.decide_issue(
            session,
            actor=current_user,
            issue_id=issue_id,
            accept=True,
            reason=payload.reason,
            if_match=_if_match(if_match),
        ),
        "meta": _meta(),
    }


@router.post(
    "/manuscript-issues/{issue_id}/reject",
    response_model=ManuscriptIssueEnvelope,
    responses=ERROR_RESPONSES,
)
def reject_issue(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    issue_id: uuid.UUID,
    payload: IssueDecision,
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> dict[str, Any]:
    if payload.reason is None or not payload.reason.strip():
        raise ContractError(
            status_code=422,
            code="VALIDATION_ERROR",
            message="A rejection reason is required.",
        )
    return {
        "data": service.decide_issue(
            session,
            actor=current_user,
            issue_id=issue_id,
            accept=False,
            reason=payload.reason,
            if_match=_if_match(if_match),
        ),
        "meta": _meta(),
    }


@router.post(
    "/projects/{project_id}/manuscript-revision-audits",
    status_code=202,
    response_model=RevisionAuditRequestEnvelope,
    responses=ERROR_RESPONSES,
)
def create_revision_audit(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    project_id: uuid.UUID,
    payload: RevisionAuditCreate,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> dict[str, Any]:
    result = stage2.create_revision_audit(
        session,
        actor=current_user,
        project_id=project_id,
        payload=payload,
        idempotency_key=_required_key(idempotency_key),
        dispatcher=dispatcher,
    )
    return {"data": result.data, "meta": _meta(replayed=result.idempotency_replayed)}


@router.get(
    "/manuscript-revision-audits/{audit_id}",
    response_model=RevisionAuditEnvelope,
    responses=ERROR_RESPONSES,
)
def get_revision_audit(
    *, session: SessionDep, current_user: CurrentUser, audit_id: uuid.UUID
) -> dict[str, Any]:
    return {
        "data": stage2.get_revision_audit(
            session, actor=current_user, audit_id=audit_id
        ),
        "meta": _meta(),
    }


@router.post(
    "/manuscript-versions/{version_id}/fix-plans",
    status_code=201,
    response_model=ManuscriptTransformationEnvelope,
    responses=ERROR_RESPONSES,
)
def create_fix_plan(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    version_id: uuid.UUID,
    payload: FixPlanCreate,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> dict[str, Any]:
    result = stage2.create_fix_plan(
        session,
        actor=current_user,
        version_id=version_id,
        payload=payload,
        idempotency_key=_required_key(idempotency_key),
    )
    return {"data": result.data, "meta": _meta(replayed=result.idempotency_replayed)}


@router.get(
    "/manuscript-fix-plans/{plan_id}",
    response_model=ManuscriptTransformationEnvelope,
    responses=ERROR_RESPONSES,
)
def get_fix_plan(
    *, session: SessionDep, current_user: CurrentUser, plan_id: uuid.UUID
) -> dict[str, Any]:
    return {
        "data": stage2.get_fix_plan(session, actor=current_user, plan_id=plan_id),
        "meta": _meta(),
    }


@router.post(
    "/manuscript-fix-plans/{plan_id}/preview",
    response_model=ManuscriptTransformationEnvelope,
    responses=ERROR_RESPONSES,
)
def preview_fix_plan(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    plan_id: uuid.UUID,
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> dict[str, Any]:
    return {
        "data": stage2.preview_fix_plan(
            session,
            actor=current_user,
            plan_id=plan_id,
            if_match=_if_match(if_match, resource="FixPlan"),
        ),
        "meta": _meta(),
    }


@router.post(
    "/manuscript-fix-plans/{plan_id}/approval-requests",
    status_code=201,
    response_model=ApprovalRequestEnvelope,
    responses=ERROR_RESPONSES,
)
def request_fix_approval(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    plan_id: uuid.UUID,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> dict[str, Any]:
    result = stage2.request_fix_approval(
        session,
        actor=current_user,
        plan_id=plan_id,
        idempotency_key=_required_key(idempotency_key),
    )
    return {"data": result.data, "meta": _meta(replayed=result.idempotency_replayed)}


@router.post(
    "/manuscript-fix-plans/{plan_id}/execute",
    status_code=202,
    response_model=TransformationExecutionEnvelope,
    responses=ERROR_RESPONSES,
)
def execute_fix_plan(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    plan_id: uuid.UUID,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> dict[str, Any]:
    result = stage2.execute_fix_plan(
        session,
        actor=current_user,
        plan_id=plan_id,
        idempotency_key=_required_key(idempotency_key),
        dispatcher=dispatcher,
    )
    return {"data": result.data, "meta": _meta(replayed=result.idempotency_replayed)}


@router.post(
    "/projects/{project_id}/claims",
    status_code=201,
    response_model=ClaimEnvelope,
    responses=ERROR_RESPONSES,
)
def create_claim(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    project_id: uuid.UUID,
    payload: ClaimCreate,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> dict[str, Any]:
    result = stage2.create_claim(
        session,
        actor=current_user,
        project_id=project_id,
        payload=payload,
        idempotency_key=_required_key(idempotency_key),
    )
    return {"data": result.data, "meta": _meta(replayed=result.idempotency_replayed)}


@router.get(
    "/claims/{claim_id}", response_model=ClaimEnvelope, responses=ERROR_RESPONSES
)
def get_claim(
    *, session: SessionDep, current_user: CurrentUser, claim_id: uuid.UUID
) -> dict[str, Any]:
    return {
        "data": stage2.get_claim(session, actor=current_user, claim_id=claim_id),
        "meta": _meta(),
    }


@router.patch(
    "/claims/{claim_id}", response_model=ClaimEnvelope, responses=ERROR_RESPONSES
)
def update_claim(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    claim_id: uuid.UUID,
    payload: ClaimUpdate,
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> dict[str, Any]:
    return {
        "data": stage2.update_claim(
            session,
            actor=current_user,
            claim_id=claim_id,
            payload=payload,
            if_match=_if_match(if_match, resource="Claim"),
        ),
        "meta": _meta(),
    }


@router.post(
    "/claims/{claim_id}/confirmation-requests",
    status_code=201,
    response_model=ApprovalRequestEnvelope,
    responses=ERROR_RESPONSES,
)
def request_claim_confirmation(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    claim_id: uuid.UUID,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> dict[str, Any]:
    result = stage2.request_claim_confirmation(
        session,
        actor=current_user,
        claim_id=claim_id,
        idempotency_key=_required_key(idempotency_key),
    )
    return {"data": result.data, "meta": _meta(replayed=result.idempotency_replayed)}
