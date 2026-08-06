from __future__ import annotations

import pytest
from sqlalchemy import CheckConstraint, ForeignKeyConstraint, UniqueConstraint

from app.approvals.service import decision_permission_actions
from app.main import app
from app.models import Export, ExportItem, JobTaskType, ProjectMemberRole, ReproPackage
from app.projects.service import ROLE_ACTIONS
from app.workers.jobs import _handlers

pytestmark = pytest.mark.no_database


def _constraints(model: type[object]) -> set[object]:
    return set(model.__table__.constraints)  # ty: ignore[unresolved-attribute]


def test_export_permissions_follow_frozen_role_matrix() -> None:
    for role in ProjectMemberRole:
        assert {"export.read", "export.readiness", "export.download"} <= ROLE_ACTIONS[
            role
        ]
    for role in (ProjectMemberRole.EDITOR, ProjectMemberRole.OWNER):
        assert {"export.create", "export.confirm"} <= ROLE_ACTIONS[role]
    for role in (ProjectMemberRole.VIEWER, ProjectMemberRole.REVIEWER):
        assert "export.create" not in ROLE_ACTIONS[role]
        assert "export.confirm" not in ROLE_ACTIONS[role]


def test_export_worker_handler_is_registered() -> None:
    assert JobTaskType.REPRO_PACKAGE_EXPORT in _handlers
    assert decision_permission_actions["export"] == "export.confirm"


def test_export_models_freeze_project_history_and_path_constraints() -> None:
    export_model_constraints = _constraints(Export)
    package_model_constraints = _constraints(ReproPackage)
    item_model_constraints = _constraints(ExportItem)
    export_constraints = {
        getattr(item, "name", None) for item in export_model_constraints
    }
    package_constraints = {
        getattr(item, "name", None) for item in package_model_constraints
    }
    item_constraints = {getattr(item, "name", None) for item in item_model_constraints}
    assert {
        "uq_exports_idempotency",
        "fk_exports_readiness_project",
        "fk_exports_approval_project",
        "fk_exports_job_project",
        "ck_exports_scope_hash",
    } <= export_constraints
    assert {
        "uq_repro_packages_export",
        "uq_repro_packages_version",
        "fk_repro_packages_artifact_project",
        "fk_repro_packages_manifest_project",
    } <= package_constraints
    assert {
        "uq_export_items_path",
        "fk_export_items_export_project",
        "fk_export_items_artifact_project",
        "ck_export_items_safe_path",
    } <= item_constraints
    assert any(
        isinstance(item, ForeignKeyConstraint) for item in item_model_constraints
    )
    assert any(isinstance(item, CheckConstraint) for item in item_model_constraints)
    assert any(isinstance(item, UniqueConstraint) for item in item_model_constraints)


def test_stage2_api_paths_are_registered() -> None:
    paths = app.openapi()["paths"]
    assert "/api/v1/projects/{project_id}/exports/readiness-check" in paths
    assert "/api/v1/projects/{project_id}/exports/repro-package" in paths
    assert "/api/v1/exports/{export_id}" in paths
    assert "/api/v1/repro-packages/{package_id}" in paths
    assert "/api/v1/repro-packages/{package_id}/download" in paths
    assert "/api/v1/projects/{project_id}/repro-packages" in paths
    for path in (
        "/api/v1/projects/{project_id}/exports/readiness-check",
        "/api/v1/projects/{project_id}/exports/repro-package",
    ):
        headers = {
            item["name"]
            for item in paths[path]["post"]["parameters"]
            if item["in"] == "header"
        }
        assert "Idempotency-Key" in headers
    history_schema = app.openapi()["components"]["schemas"]["ReproPackageHistoryItem"][
        "properties"
    ]
    assert {"id", "package_version", "sha256", "artifact_id"} <= history_schema.keys()
    assert "manifest" not in history_schema
