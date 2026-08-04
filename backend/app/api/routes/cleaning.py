from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Header, Query, Response

from app.api.deps import CurrentUser, SessionDep
from app.api.errors import ContractError
from app.api.m4_responses import (
    ApprovalRequestEnvelope,
    CleaningPlanEnvelope,
    CleaningPlanSuggestionEnvelope,
    DataTransformationEnvelope,
    TransformationExecutionEnvelope,
    VersionComparisonEnvelope,
)
from app.cleaning import service
from app.cleaning.schemas import (
    CleaningPlanCreate,
    CleaningPlanSuggestionRequest,
    CleaningPlanUpdate,
)
from app.cleaning.suggestion import suggest_plan
from app.core.observability import current_request_id
from app.jobs.dispatcher import dispatcher

router = APIRouter(tags=["data-cleaning"])


def _meta(*, replayed: bool = False) -> dict[str, Any]:
    return {
        "request_id": current_request_id(),
        "schema_version": "1.0",
        "idempotency_replayed": replayed,
    }


def _required_idempotency_key(value: str | None) -> str:
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


def _if_match(value: str | None) -> int:
    if value is None:
        raise ContractError(
            status_code=400,
            code="VALIDATION_ERROR",
            message="If-Match is required for CleaningPlan updates.",
        )
    normalized = value.strip().strip('"')
    try:
        result = int(normalized)
    except ValueError as exc:
        raise ContractError(
            status_code=400,
            code="VALIDATION_ERROR",
            message="If-Match must contain a positive lock version.",
        ) from exc
    if result < 1:
        raise ContractError(
            status_code=400,
            code="VALIDATION_ERROR",
            message="If-Match must contain a positive lock version.",
        )
    return result


@router.post(
    "/dataset-versions/{version_id}/cleaning-plans",
    status_code=201,
    response_model=CleaningPlanEnvelope,
)
def create_cleaning_plan(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    version_id: uuid.UUID,
    payload: CleaningPlanCreate,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> dict[str, Any]:
    result = service.create_plan(
        session,
        actor=current_user,
        version_id=version_id,
        payload=payload,
        idempotency_key=_required_idempotency_key(idempotency_key),
    )
    return {
        "data": result.data,
        "meta": _meta(replayed=result.idempotency_replayed),
    }


@router.get("/cleaning-plans/{plan_id}", response_model=CleaningPlanEnvelope)
def get_cleaning_plan(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    plan_id: uuid.UUID,
    response: Response,
) -> dict[str, Any]:
    data = service.get_plan(session, actor=current_user, plan_id=plan_id)
    response.headers["ETag"] = f'"{data["lock_version"]}"'
    return {"data": data, "meta": _meta()}


@router.patch("/cleaning-plans/{plan_id}", response_model=CleaningPlanEnvelope)
def update_cleaning_plan(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    plan_id: uuid.UUID,
    payload: CleaningPlanUpdate,
    response: Response,
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> dict[str, Any]:
    data = service.update_plan(
        session,
        actor=current_user,
        plan_id=plan_id,
        payload=payload,
        expected_lock_version=_if_match(if_match),
    )
    response.headers["ETag"] = f'"{data["lock_version"]}"'
    return {"data": data, "meta": _meta()}


def _operation_response(result: Any) -> dict[str, Any]:
    return {
        "data": result.data,
        "meta": _meta(replayed=result.idempotency_replayed),
    }


@router.post("/cleaning-plans/{plan_id}/preview", response_model=CleaningPlanEnvelope)
def preview_cleaning_plan(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    plan_id: uuid.UUID,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> dict[str, Any]:
    return _operation_response(
        service.preview_plan(
            session,
            actor=current_user,
            plan_id=plan_id,
            idempotency_key=_required_idempotency_key(idempotency_key),
        )
    )


@router.post(
    "/cleaning-plans/{plan_id}/approval-requests",
    status_code=201,
    response_model=ApprovalRequestEnvelope,
)
def request_cleaning_plan_approval(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    plan_id: uuid.UUID,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> dict[str, Any]:
    return _operation_response(
        service.request_approval(
            session,
            actor=current_user,
            plan_id=plan_id,
            idempotency_key=_required_idempotency_key(idempotency_key),
        )
    )


@router.post(
    "/cleaning-plans/{plan_id}/execute",
    status_code=202,
    response_model=TransformationExecutionEnvelope,
)
def execute_cleaning_plan(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    plan_id: uuid.UUID,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> dict[str, Any]:
    return _operation_response(
        service.execute_plan(
            session,
            actor=current_user,
            plan_id=plan_id,
            idempotency_key=_required_idempotency_key(idempotency_key),
            dispatcher=dispatcher,
        )
    )


@router.get(
    "/datasets/{dataset_id}/version-comparison",
    response_model=VersionComparisonEnvelope,
)
def compare_dataset_versions(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    dataset_id: uuid.UUID,
    base_version_id: Annotated[uuid.UUID, Query()],
    target_version_id: Annotated[uuid.UUID, Query()],
) -> dict[str, Any]:
    return {
        "data": service.compare_versions(
            session,
            actor=current_user,
            dataset_id=dataset_id,
            base_version_id=base_version_id,
            target_version_id=target_version_id,
        ),
        "meta": _meta(),
    }


@router.post(
    "/dataset-versions/{version_id}/cleaning-plan-suggestions",
    response_model=CleaningPlanSuggestionEnvelope,
)
def suggest_cleaning_plan(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    version_id: uuid.UUID,
    payload: CleaningPlanSuggestionRequest,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> dict[str, Any]:
    return _operation_response(
        suggest_plan(
            session,
            actor=current_user,
            version_id=version_id,
            payload=payload,
            idempotency_key=_required_idempotency_key(idempotency_key),
        )
    )


@router.get(
    "/data-transformations/{transformation_id}",
    response_model=DataTransformationEnvelope,
)
def get_data_transformation(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    transformation_id: uuid.UUID,
) -> dict[str, Any]:
    return {
        "data": service.get_transformation(
            session, actor=current_user, transformation_id=transformation_id
        ),
        "meta": _meta(),
    }
