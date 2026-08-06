from __future__ import annotations

import uuid
from collections import deque
from typing import Any

from sqlmodel import Session, col, select

from app.api.errors import ContractError
from app.models import (
    AnalysisPlan,
    AnalysisResult,
    AnalysisRun,
    AuditResult,
    Claim,
    ClaimEvidenceLink,
    DataTransformation,
    EvidenceLinkStatus,
    EvidenceObjectType,
    Figure,
    ProjectMemberRole,
    User,
)
from app.projects import service as project_service

from .completeness import evaluate_claim
from .resolvers import resolve_evidence
from .schemas import (
    EvidenceGraphProjection,
    EvidenceReference,
    EvidenceRisk,
    GraphEdge,
    GraphNode,
)

MAX_DEPTH = 4
MAX_NODES = 500


def _role(access: project_service.ProjectAccess) -> ProjectMemberRole:
    return access.membership.role if access.membership else ProjectMemberRole.OWNER


def _risk(reference: EvidenceReference) -> EvidenceRisk:
    if not reference.known_status:
        return EvidenceRisk.UNKNOWN
    if reference.invalidated or reference.stale:
        return EvidenceRisk.HIGH
    if reference.restricted or reference.limitations:
        return EvidenceRisk.MEDIUM
    return EvidenceRisk.LOW


def _node(reference: EvidenceReference, *, source_kind: str, rank: int) -> GraphNode:
    return GraphNode(
        id=f"{reference.object_type.value.lower()}:{reference.object_id}",
        node_type=reference.object_type,
        object_id=reference.object_id,
        label=reference.label,
        raw_status=reference.raw_status,
        known_status=reference.known_status,
        risk=_risk(reference),
        invalidated=reference.invalidated,
        stale=reference.stale,
        source_kind=source_kind,
        detail_intent=reference.detail_intent,
        allowed_actions=reference.allowed_actions,
        limitations=reference.limitations,
        lane=reference.object_type.value.lower(),
        rank=rank,
    )


def _claim_node(claim: Claim, role: ProjectMemberRole, *, rank: int = 0) -> GraphNode:
    return GraphNode(
        id=f"claim:{claim.id}",
        node_type="CLAIM",
        object_id=claim.id,
        label=claim.claim_text[:240],
        raw_status=claim.status,
        known_status=True,
        risk=EvidenceRisk.HIGH if claim.invalidated_at else EvidenceRisk.LOW,
        invalidated=claim.invalidated_at is not None,
        stale=claim.invalidated_at is not None,
        source_kind="DOMAIN",
        detail_intent="claim",
        allowed_actions=["claim.read"]
        + (
            ["evidence.link.create"]
            if "evidence.link.create" in project_service.ROLE_ACTIONS[role]
            else []
        ),
        limitations=[],
        lane="claim",
        rank=rank,
    )


def _derived_targets(
    session: Session, reference: EvidenceReference
) -> list[tuple[EvidenceObjectType, uuid.UUID, str]]:
    targets: list[tuple[EvidenceObjectType, uuid.UUID, str]] = []
    if reference.object_type == EvidenceObjectType.ANALYSIS_RESULT:
        result = session.get(AnalysisResult, reference.object_id)
        if result:
            targets.append(
                (EvidenceObjectType.ANALYSIS_RUN, result.analysis_run_id, "PRODUCED_BY")
            )
    elif reference.object_type == EvidenceObjectType.ANALYSIS_RUN:
        run = session.get(AnalysisRun, reference.object_id)
        if run:
            targets.extend(
                [
                    (
                        EvidenceObjectType.ANALYSIS_PLAN,
                        run.analysis_plan_id,
                        "DERIVED_FROM",
                    ),
                    (
                        EvidenceObjectType.DATASET_VERSION,
                        run.dataset_version_id,
                        "DERIVED_FROM",
                    ),
                    (
                        EvidenceObjectType.APPROVAL,
                        run.approval_record_id,
                        "CONFIRMED_BY",
                    ),
                ]
            )
    elif reference.object_type == EvidenceObjectType.ANALYSIS_PLAN:
        plan = session.get(AnalysisPlan, reference.object_id)
        if plan:
            targets.append(
                (
                    EvidenceObjectType.DATASET_VERSION,
                    plan.dataset_version_id,
                    "DERIVED_FROM",
                )
            )
            if plan.approval_record_id:
                targets.append(
                    (
                        EvidenceObjectType.APPROVAL,
                        plan.approval_record_id,
                        "CONFIRMED_BY",
                    )
                )
    elif reference.object_type == EvidenceObjectType.FIGURE:
        figure = session.get(Figure, reference.object_id)
        if figure:
            targets.append(
                (
                    EvidenceObjectType.DATASET_VERSION,
                    figure.dataset_version_id,
                    "DERIVED_FROM",
                )
            )
            if figure.analysis_result_id:
                targets.append(
                    (
                        EvidenceObjectType.ANALYSIS_RESULT,
                        figure.analysis_result_id,
                        "DERIVED_FROM",
                    )
                )
            if figure.approval_record_id:
                targets.append(
                    (
                        EvidenceObjectType.APPROVAL,
                        figure.approval_record_id,
                        "CONFIRMED_BY",
                    )
                )
    elif reference.object_type == EvidenceObjectType.DATA_TRANSFORMATION:
        transformation = session.get(DataTransformation, reference.object_id)
        if transformation:
            targets.append(
                (
                    EvidenceObjectType.DATASET_VERSION,
                    transformation.source_dataset_version_id,
                    "TRANSFORMED_FROM",
                )
            )
            targets.append(
                (
                    EvidenceObjectType.APPROVAL,
                    transformation.approval_record_id,
                    "CONFIRMED_BY",
                )
            )
    return targets


def project_graph(
    session: Session,
    *,
    actor: User,
    project_id: uuid.UUID,
    root_claim_id: uuid.UUID | None,
    depth: int,
    node_types: set[str] | None,
    risk_only: bool,
    include_invalidated: bool,
    cursor: str | None,
    limit: int,
) -> EvidenceGraphProjection:
    if depth < 0 or depth > MAX_DEPTH:
        raise ContractError(
            status_code=422,
            code="GRAPH_DEPTH_INVALID",
            message="Graph depth is outside the supported range.",
        )
    if limit < 1 or limit > MAX_NODES:
        raise ContractError(
            status_code=422,
            code="GRAPH_LIMIT_INVALID",
            message="Graph limit is outside the supported range.",
        )
    access = project_service.authorize_project(
        session, project_id=project_id, actor=actor, action="evidence.read"
    )
    role = _role(access)
    claim_statement = select(Claim).where(Claim.project_id == project_id)
    if root_claim_id:
        claim_statement = claim_statement.where(Claim.id == root_claim_id)
    claims = session.exec(claim_statement.order_by(col(Claim.id))).all()
    if root_claim_id and not claims:
        raise ContractError(
            status_code=404, code="RESOURCE_NOT_FOUND", message="Resource not found."
        )
    nodes: dict[str, GraphNode] = {}
    edges: dict[str, GraphEdge] = {}
    completeness: dict[str, Any] = {}
    queue: deque[tuple[EvidenceReference, int]] = deque()
    limitations: list[str] = []
    for claim in claims:
        claim_id = f"claim:{claim.id}"
        nodes[claim_id] = _claim_node(claim, role)
        completeness[str(claim.id)] = evaluate_claim(session, claim=claim)
        if depth == 0:
            continue
        formal_targets: list[tuple[EvidenceObjectType, uuid.UUID, str]] = []
        if claim.approval_record_id:
            formal_targets.append(
                (
                    EvidenceObjectType.APPROVAL,
                    claim.approval_record_id,
                    "CONFIRMED_BY",
                )
            )
        for audit in session.exec(
            select(AuditResult).where(
                AuditResult.project_id == project_id,
                AuditResult.target_object_type == "CLAIM",
                AuditResult.target_object_id == claim.id,
            )
        ).all():
            formal_targets.append(
                (EvidenceObjectType.AUDIT_RESULT, audit.id, "AUDITED_BY")
            )
        for target_type, target_id, relation in formal_targets:
            try:
                reference = resolve_evidence(
                    session,
                    project_id=project_id,
                    object_type=target_type,
                    object_id=target_id,
                )
            except ContractError as error:
                if error.status_code == 404:
                    limitations.append(
                        "Some formal Claim lineage is outside the current authorized scope."
                    )
                    continue
                raise
            target = f"{reference.object_type.value.lower()}:{reference.object_id}"
            nodes[target] = _node(reference, source_kind="DERIVED", rank=1)
            edge_id = f"derived:{claim_id}:{relation}:{target}"
            edges[edge_id] = GraphEdge(
                id=edge_id,
                source=claim_id,
                target=target,
                relation_type=relation,
                strength=None,
                raw_status="ACTIVE",
                known_status=True,
                risk=_risk(reference),
                invalidated=reference.invalidated,
                source_kind="DERIVED",
            )
            queue.append((reference, 1))
        link_statement = select(ClaimEvidenceLink).where(
            ClaimEvidenceLink.project_id == project_id,
            ClaimEvidenceLink.claim_id == claim.id,
        )
        if not include_invalidated:
            link_statement = link_statement.where(
                ClaimEvidenceLink.status != EvidenceLinkStatus.INVALIDATED
            )
        for link in session.exec(
            link_statement.order_by(col(ClaimEvidenceLink.id))
        ).all():
            try:
                reference = resolve_evidence(
                    session,
                    project_id=project_id,
                    object_type=link.evidence_object_type,
                    object_id=link.evidence_object_id,
                )
            except ContractError as error:
                if error.status_code == 404:
                    limitations.append(
                        "Some evidence is outside the current authorized scope."
                    )
                    continue
                raise
            target = f"{reference.object_type.value.lower()}:{reference.object_id}"
            nodes[target] = _node(reference, source_kind="STORED", rank=1)
            edge_id = f"link:{link.id}"
            edges[edge_id] = GraphEdge(
                id=edge_id,
                source=claim_id,
                target=target,
                relation_type=link.relation_type,
                strength=link.strength,
                raw_status=link.status,
                known_status=True,
                risk=(
                    EvidenceRisk.HIGH
                    if link.status == EvidenceLinkStatus.INVALIDATED
                    else _risk(reference)
                ),
                invalidated=link.status == EvidenceLinkStatus.INVALIDATED,
                source_kind="STORED",
            )
            queue.append((reference, 1))

    visited: set[tuple[EvidenceObjectType, uuid.UUID]] = set()
    while queue:
        reference, current_depth = queue.popleft()
        key = (reference.object_type, reference.object_id)
        if key in visited or current_depth >= depth:
            continue
        visited.add(key)
        source_id = f"{reference.object_type.value.lower()}:{reference.object_id}"
        for target_type, target_id, relation in _derived_targets(session, reference):
            try:
                target_ref = resolve_evidence(
                    session,
                    project_id=project_id,
                    object_type=target_type,
                    object_id=target_id,
                )
            except ContractError as error:
                if error.status_code == 404:
                    limitations.append(
                        "Some derived lineage is outside the current authorized scope."
                    )
                    continue
                raise
            target_node = f"{target_type.value.lower()}:{target_id}"
            nodes[target_node] = _node(
                target_ref, source_kind="DERIVED", rank=current_depth + 1
            )
            edge_id = f"derived:{source_id}:{relation}:{target_node}"
            edges[edge_id] = GraphEdge(
                id=edge_id,
                source=source_id,
                target=target_node,
                relation_type=relation,
                strength=None,
                raw_status="ACTIVE",
                known_status=True,
                risk=_risk(target_ref),
                invalidated=target_ref.invalidated,
                source_kind="DERIVED",
            )
            queue.append((target_ref, current_depth + 1))

    node_list = sorted(nodes.values(), key=lambda item: item.id)
    if node_types:
        node_list = [item for item in node_list if item.node_type in node_types]
    if risk_only:
        node_list = [item for item in node_list if item.risk != EvidenceRisk.LOW]
    if not include_invalidated:
        node_list = [item for item in node_list if not item.invalidated]
    if cursor:
        node_list = [item for item in node_list if item.id > cursor]
    partial = len(node_list) > limit
    selected = node_list[:limit]
    selected_ids = {item.id for item in selected}
    edge_list = sorted(
        [
            item
            for item in edges.values()
            if item.source in selected_ids and item.target in selected_ids
        ],
        key=lambda item: item.id,
    )
    if partial:
        limitations.append(
            "Graph node limit reached; use next_cursor for progressive expansion."
        )
    return EvidenceGraphProjection(
        nodes=selected,
        edges=edge_list,
        completeness=completeness,
        partial=partial,
        next_cursor=selected[-1].id if partial and selected else None,
        limitations=sorted(set(limitations)),
        scope={
            "project_id": str(project_id),
            "root_claim_id": str(root_claim_id) if root_claim_id else None,
            "depth": depth,
            "limit": limit,
        },
    )
