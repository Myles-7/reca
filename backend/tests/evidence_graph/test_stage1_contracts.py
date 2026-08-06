from pathlib import Path

import pytest
from sqlalchemy import CheckConstraint, ForeignKeyConstraint, Index

from app.evidence_graph.completeness import RULE_SET_VERSION
from app.evidence_graph.projector import MAX_DEPTH, MAX_NODES
from app.evidence_graph.resolvers import RESOLVERS
from app.evidence_graph.schemas import EvidenceCompleteness
from app.evidence_graph.service import RELATION_MATRIX
from app.main import app
from app.models import (
    AuditResult,
    AuditResultOutcome,
    AuditResultStatus,
    ClaimEvidenceLink,
    EvidenceObjectType,
    EvidenceRelationType,
    ProjectMemberRole,
)
from app.projects.service import ROLE_ACTIONS

pytestmark = pytest.mark.no_database


def _named(model: type[object], kind: type[object]) -> set[str]:
    table = model.__table__  # ty: ignore[unresolved-attribute]
    values = table.indexes if kind is Index else table.constraints
    return {
        value.name
        for value in values
        if isinstance(value, kind) and value.name is not None
    }


def test_m7_models_freeze_link_and_generic_audit_invariants() -> None:
    assert {
        "ck_claim_evidence_links_hash",
        "ck_claim_evidence_links_active_confirmation",
        "ck_claim_evidence_links_invalidation",
    } <= _named(ClaimEvidenceLink, CheckConstraint)
    assert "fk_claim_evidence_links_claim_project" in _named(
        ClaimEvidenceLink, ForeignKeyConstraint
    )
    assert "uq_claim_evidence_links_canonical_live" in _named(ClaimEvidenceLink, Index)
    assert {
        "ck_audit_results_target_shape",
        "ck_audit_results_source_hashes",
    } <= _named(AuditResult, CheckConstraint)
    assert AuditResultStatus.COMPLETED.value == "COMPLETED"
    assert AuditResultOutcome.VERIFIED.value == "VERIFIED"
    assert AuditResultStatus.__name__ != AuditResultOutcome.__name__


def test_m7_resolvers_are_explicit_and_complete() -> None:
    assert set(RESOLVERS) == set(EvidenceObjectType)
    assert all(callable(resolver) for resolver in RESOLVERS.values())


def test_m7_relation_matrix_is_fail_closed() -> None:
    assert set(RELATION_MATRIX) == set(EvidenceRelationType)
    assert (
        EvidenceObjectType.EVIDENCE_SPAN
        in RELATION_MATRIX[EvidenceRelationType.SUPPORTED_BY]
    )
    assert (
        EvidenceObjectType.APPROVAL
        not in RELATION_MATRIX[EvidenceRelationType.SUPPORTED_BY]
    )
    assert (
        EvidenceObjectType.FIGURE in RELATION_MATRIX[EvidenceRelationType.VISUALIZED_AS]
    )


def test_m7_permissions_and_graph_limits_are_server_owned() -> None:
    assert "evidence.read" in ROLE_ACTIONS[ProjectMemberRole.VIEWER]
    assert "evidence.link.create" not in ROLE_ACTIONS[ProjectMemberRole.VIEWER]
    for role in (
        ProjectMemberRole.REVIEWER,
        ProjectMemberRole.EDITOR,
        ProjectMemberRole.OWNER,
    ):
        assert "evidence.audit.run" in ROLE_ACTIONS[role]
    assert MAX_DEPTH == 4
    assert MAX_NODES == 500


def test_m7_completeness_contract_has_no_quality_score() -> None:
    assert RULE_SET_VERSION == "m7-evidence-completeness/1.0"
    assert "score" not in EvidenceCompleteness.model_fields
    assert "quality" not in EvidenceCompleteness.model_fields


def test_m7_openapi_registers_stage1_routes_and_write_headers() -> None:
    paths = app.openapi()["paths"]
    expected = {
        "/api/v1/claims/{claim_id}/evidence-links",
        "/api/v1/evidence-links/{link_id}",
        "/api/v1/projects/{project_id}/evidence-graph",
        "/api/v1/claims/{claim_id}/audits",
    }
    assert expected <= paths.keys()
    create_headers = {
        value["name"]
        for value in paths["/api/v1/claims/{claim_id}/evidence-links"]["post"][
            "parameters"
        ]
        if value["in"] == "header"
    }
    transition_headers = {
        value["name"]
        for value in paths["/api/v1/evidence-links/{link_id}"]["patch"]["parameters"]
        if value["in"] == "header"
    }
    assert "Idempotency-Key" in create_headers
    assert {"Idempotency-Key", "If-Match"} <= transition_headers
    assert "202" in paths["/api/v1/claims/{claim_id}/audits"]["post"]["responses"]
    audit_schema = app.openapi()["components"]["schemas"]["ClaimAuditPublic"]
    assert "job_id" in audit_schema["properties"]


def test_m7_migration_is_additive_and_freezes_export_only() -> None:
    root = Path(__file__).resolve().parents[3]
    migration = (
        root / "backend/app/alembic/versions/0018_m7_evidence_export.py"
    ).read_text(encoding="utf-8")
    assert 'down_revision: str | None = "0017_m6_manuscripts"' in migration
    assert migration.count('"audit_results"') > 1
    assert 'op.create_table(\n        "audit_results"' not in migration
    for table in (
        "claim_evidence_links",
        "exports",
        "repro_packages",
        "export_items",
    ):
        assert f'"{table}"' in migration
    assert "uq_claim_evidence_links_canonical_live" in migration
    assert "ck_audit_results_target_shape" in migration
    assert "create_type=False" in migration
