"""M7 evidence graph and frozen export structures.

Revision ID: 0018_m7_evidence_export
Revises: 0017_m6_manuscripts
"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0018_m7_evidence_export"
down_revision: str | None = "0017_m6_manuscripts"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _uuid() -> sa.Uuid:
    return sa.Uuid()


def _string(length: int) -> sqlmodel.sql.sqltypes.AutoString:
    return sqlmodel.sql.sqltypes.AutoString(length=length)


def _create_enum(name: str, *values: str) -> postgresql.ENUM:
    enum = postgresql.ENUM(*values, name=name)
    enum.create(op.get_bind(), checkfirst=True)
    return postgresql.ENUM(*values, name=name, create_type=False)


def upgrade() -> None:
    for value in (
        "LITERATURE_EVIDENCE_AUDIT",
        "NUMERIC_CONSISTENCY_AUDIT",
        "FIGURE_VERSION_AUDIT",
        "CAUSALITY_AUDIT",
        "CLAIM_COMPLETENESS_AUDIT",
        "EXPORT_READINESS_AUDIT",
        "READ_SCOPE_AUDIT",
        "PROMPT_CONTRACT_AUDIT",
        "DEGRADATION_AUDIT",
    ):
        op.execute(f"ALTER TYPE audit_type ADD VALUE IF NOT EXISTS '{value}'")

    audit_outcome = _create_enum(
        "audit_result_outcome",
        "VERIFIED",
        "NEEDS_REVIEW",
        "INSUFFICIENT_EVIDENCE",
        "SOURCE_INCOMPLETE",
        "CONFLICTED",
        "DATA_MISMATCH",
        "FIGURE_MISMATCH",
        "OVERCLAIM_RISK",
        "REJECTED_BY_USER",
        "INVALIDATED",
    )
    evidence_type = _create_enum(
        "evidence_object_type",
        "LITERATURE_RECORD",
        "EVIDENCE_SPAN",
        "DATASET_VERSION",
        "DATA_TRANSFORMATION",
        "ANALYSIS_PLAN",
        "ANALYSIS_RUN",
        "ANALYSIS_RESULT",
        "FIGURE",
        "MANUSCRIPT_VERSION",
        "APPROVAL",
        "AUDIT_RESULT",
    )
    relation_type = _create_enum(
        "evidence_relation_type",
        "SUPPORTED_BY",
        "CONTRADICTED_BY",
        "DERIVED_FROM",
        "TRANSFORMED_FROM",
        "ANALYZED_BY",
        "PRODUCED_BY",
        "VISUALIZED_AS",
        "CONFIRMED_BY",
        "AUDITED_BY",
        "INVALIDATED_BY",
    )
    strength = _create_enum(
        "evidence_link_strength", "STRONG", "MODERATE", "WEAK", "UNKNOWN"
    )
    link_status = _create_enum(
        "evidence_link_status", "SUGGESTED", "ACTIVE", "REJECTED", "INVALIDATED"
    )
    export_type = _create_enum(
        "export_type",
        "REPRO_PACKAGE",
        "LITERATURE_MATRIX",
        "DATA_QUALITY_REPORT",
        "ANALYSIS_REPORT",
        "MANUSCRIPT_CHECK_REPORT",
    )
    export_status = _create_enum(
        "export_status",
        "DRAFT",
        "VALIDATING",
        "NEEDS_CONFIRMATION",
        "QUEUED",
        "PACKAGING",
        "COMPLETED",
        "FAILED",
        "CANCELLED",
    )
    include_status = _create_enum(
        "export_item_include_status",
        "INCLUDED",
        "EXCLUDED",
        "METADATA_ONLY",
        "REFERENCE_ONLY",
        "BLOCKED",
        "MISSING",
    )

    op.alter_column("audit_results", "before_version_id", nullable=True)
    op.alter_column("audit_results", "after_version_id", nullable=True)
    op.alter_column("audit_results", "manuscript_id", nullable=True)
    op.alter_column("audit_results", "before_source_hash", nullable=True)
    op.alter_column("audit_results", "after_source_hash", nullable=True)
    op.drop_constraint("ck_audit_results_source_hashes", "audit_results", type_="check")
    op.add_column("audit_results", sa.Column("target_object_type", _string(100)))
    op.add_column("audit_results", sa.Column("target_object_id", _uuid()))
    op.add_column("audit_results", sa.Column("source_snapshot", postgresql.JSONB()))
    op.add_column("audit_results", sa.Column("source_snapshot_hash", _string(64)))
    op.add_column("audit_results", sa.Column("outcome", audit_outcome))
    op.add_column(
        "audit_results",
        sa.Column("findings", postgresql.JSONB(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "audit_results",
        sa.Column(
            "evidence_object_ids",
            postgresql.JSONB(),
            nullable=False,
            server_default="[]",
        ),
    )
    op.add_column(
        "audit_results",
        sa.Column(
            "limitations", postgresql.JSONB(), nullable=False, server_default="[]"
        ),
    )
    op.add_column(
        "audit_results",
        sa.Column("degraded", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "audit_results", sa.Column("invalidated_at", sa.DateTime(timezone=True))
    )
    for column in ("findings", "evidence_object_ids", "limitations", "degraded"):
        op.alter_column("audit_results", column, server_default=None)
    op.create_index(
        "ix_audit_results_target_object_type", "audit_results", ["target_object_type"]
    )
    op.create_index(
        "ix_audit_results_target_object_id", "audit_results", ["target_object_id"]
    )
    op.create_index(
        "ix_audit_results_project_target",
        "audit_results",
        ["project_id", "target_object_type", "target_object_id"],
    )
    op.create_check_constraint(
        "ck_audit_results_source_hashes",
        "audit_results",
        "(before_source_hash IS NULL OR before_source_hash ~ '^[0-9a-f]{64}$') AND "
        "(after_source_hash IS NULL OR after_source_hash ~ '^[0-9a-f]{64}$') AND "
        "(source_snapshot_hash IS NULL OR source_snapshot_hash ~ '^[0-9a-f]{64}$')",
    )
    op.create_check_constraint(
        "ck_audit_results_target_shape",
        "audit_results",
        "(audit_type = 'REVISION_DRIFT_AUDIT' AND before_version_id IS NOT NULL "
        "AND after_version_id IS NOT NULL AND manuscript_id IS NOT NULL "
        "AND before_source_hash IS NOT NULL AND after_source_hash IS NOT NULL) OR "
        "(audit_type <> 'REVISION_DRIFT_AUDIT' AND target_object_type IS NOT NULL "
        "AND target_object_id IS NOT NULL AND source_snapshot IS NOT NULL "
        "AND source_snapshot_hash IS NOT NULL)",
    )

    op.create_table(
        "claim_evidence_links",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("project_id", _uuid(), nullable=False),
        sa.Column("claim_id", _uuid(), nullable=False),
        sa.Column("evidence_object_type", evidence_type, nullable=False),
        sa.Column("evidence_object_id", _uuid(), nullable=False),
        sa.Column("relation_type", relation_type, nullable=False),
        sa.Column("strength", strength, nullable=False),
        sa.Column("status", link_status, nullable=False),
        sa.Column("source_hash", _string(64), nullable=False),
        sa.Column("source_version", postgresql.JSONB(), nullable=False),
        sa.Column("explanation", sa.Text()),
        sa.Column(
            "created_by_actor_type",
            postgresql.ENUM(name="audit_actor_type", create_type=False),
            nullable=False,
        ),
        sa.Column("created_by_actor_id", _string(255)),
        sa.Column("idempotency_key", _string(255), nullable=False),
        sa.Column("lock_version", sa.Integer(), nullable=False),
        sa.Column("confirmed_by_user_id", _uuid()),
        sa.Column("confirmed_at", sa.DateTime(timezone=True)),
        sa.Column("invalidated_at", sa.DateTime(timezone=True)),
        sa.Column("invalidation_reason", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "id", "project_id", name="uq_claim_evidence_links_id_project"
        ),
        sa.UniqueConstraint(
            "project_id", "idempotency_key", name="uq_claim_evidence_links_idempotency"
        ),
        sa.ForeignKeyConstraint(
            ["claim_id", "project_id"],
            ["claims.id", "claims.project_id"],
            name="fk_claim_evidence_links_claim_project",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["confirmed_by_user_id"], ["user.id"], ondelete="SET NULL"
        ),
        sa.CheckConstraint(
            "source_hash ~ '^[0-9a-f]{64}$'", name="ck_claim_evidence_links_hash"
        ),
        sa.CheckConstraint("lock_version >= 1", name="ck_claim_evidence_links_lock"),
        sa.CheckConstraint(
            "(status = 'ACTIVE' AND confirmed_at IS NOT NULL) OR status <> 'ACTIVE'",
            name="ck_claim_evidence_links_active_confirmation",
        ),
        sa.CheckConstraint(
            "(status = 'INVALIDATED' AND invalidated_at IS NOT NULL AND invalidation_reason IS NOT NULL) OR status <> 'INVALIDATED'",
            name="ck_claim_evidence_links_invalidation",
        ),
    )
    for column in (
        "project_id",
        "claim_id",
        "evidence_object_id",
        "confirmed_by_user_id",
    ):
        op.create_index(
            f"ix_claim_evidence_links_{column}", "claim_evidence_links", [column]
        )
    op.create_index(
        "ix_claim_evidence_links_project_claim",
        "claim_evidence_links",
        ["project_id", "claim_id"],
    )
    op.create_index(
        "ix_claim_evidence_links_project_evidence",
        "claim_evidence_links",
        ["project_id", "evidence_object_type", "evidence_object_id"],
    )
    op.create_index(
        "ix_claim_evidence_links_project_status",
        "claim_evidence_links",
        ["project_id", "status"],
    )
    op.create_index(
        "uq_claim_evidence_links_canonical_live",
        "claim_evidence_links",
        [
            "project_id",
            "claim_id",
            "evidence_object_type",
            "evidence_object_id",
            "relation_type",
        ],
        unique=True,
        postgresql_where=sa.text("status IN ('SUGGESTED', 'ACTIVE')"),
    )

    op.create_table(
        "exports",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("project_id", _uuid(), nullable=False),
        sa.Column("export_type", export_type, nullable=False),
        sa.Column("status", export_status, nullable=False),
        sa.Column("requested_by_user_id", _uuid(), nullable=False),
        sa.Column("scope", postgresql.JSONB(), nullable=False),
        sa.Column("scope_hash", _string(64), nullable=False),
        sa.Column("readiness_audit_id", _uuid()),
        sa.Column("approval_record_id", _uuid()),
        sa.Column("job_id", _uuid()),
        sa.Column("idempotency_key", _string(255), nullable=False),
        sa.Column("lock_version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("error_code", _string(100)),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "project_id", name="uq_exports_id_project"),
        sa.UniqueConstraint(
            "project_id", "idempotency_key", name="uq_exports_idempotency"
        ),
        sa.ForeignKeyConstraint(
            ["project_id"], ["research_projects.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["requested_by_user_id"], ["user.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["readiness_audit_id", "project_id"],
            ["audit_results.id", "audit_results.project_id"],
            name="fk_exports_readiness_project",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["approval_record_id", "project_id"],
            ["approval_records.id", "approval_records.project_id"],
            name="fk_exports_approval_project",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["job_id", "project_id"],
            ["jobs.id", "jobs.project_id"],
            name="fk_exports_job_project",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint("lock_version >= 1", name="ck_exports_lock"),
        sa.CheckConstraint(
            "scope_hash ~ '^[0-9a-f]{64}$'", name="ck_exports_scope_hash"
        ),
    )
    for column in (
        "project_id",
        "requested_by_user_id",
        "readiness_audit_id",
        "approval_record_id",
        "job_id",
    ):
        op.create_index(f"ix_exports_{column}", "exports", [column])
    op.create_index("ix_exports_project_status", "exports", ["project_id", "status"])

    op.create_table(
        "repro_packages",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("export_id", _uuid(), nullable=False),
        sa.Column("project_id", _uuid(), nullable=False),
        sa.Column("artifact_id", _uuid(), nullable=False),
        sa.Column("manifest_artifact_id", _uuid(), nullable=False),
        sa.Column("package_version", sa.Integer(), nullable=False),
        sa.Column("schema_version", _string(100), nullable=False),
        sa.Column("contains_sensitive_data", sa.Boolean(), nullable=False),
        sa.Column("contains_restricted_data", sa.Boolean(), nullable=False),
        sa.Column("file_count", sa.Integer(), nullable=False),
        sa.Column("total_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("sha256", _string(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "project_id", name="uq_repro_packages_id_project"),
        sa.UniqueConstraint("export_id", name="uq_repro_packages_export"),
        sa.UniqueConstraint(
            "project_id", "package_version", name="uq_repro_packages_version"
        ),
        sa.ForeignKeyConstraint(
            ["export_id", "project_id"],
            ["exports.id", "exports.project_id"],
            name="fk_repro_packages_export_project",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["artifact_id", "project_id"],
            ["artifacts.id", "artifacts.project_id"],
            name="fk_repro_packages_artifact_project",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["manifest_artifact_id", "project_id"],
            ["artifacts.id", "artifacts.project_id"],
            name="fk_repro_packages_manifest_project",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint("package_version >= 1", name="ck_repro_packages_version"),
        sa.CheckConstraint(
            "file_count >= 0 AND total_size_bytes >= 0", name="ck_repro_packages_sizes"
        ),
        sa.CheckConstraint("sha256 ~ '^[0-9a-f]{64}$'", name="ck_repro_packages_hash"),
    )
    for column in ("export_id", "project_id", "artifact_id", "manifest_artifact_id"):
        op.create_index(f"ix_repro_packages_{column}", "repro_packages", [column])

    op.create_table(
        "export_items",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("export_id", _uuid(), nullable=False),
        sa.Column("project_id", _uuid(), nullable=False),
        sa.Column("object_type", _string(100), nullable=False),
        sa.Column("object_id", _uuid()),
        sa.Column("artifact_id", _uuid()),
        sa.Column("package_path", _string(1024), nullable=False),
        sa.Column("sha256", _string(64)),
        sa.Column("include_status", include_status, nullable=False),
        sa.Column("exclusion_reason", sa.Text()),
        sa.Column("source_snapshot", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "project_id", name="uq_export_items_id_project"),
        sa.UniqueConstraint("export_id", "package_path", name="uq_export_items_path"),
        sa.ForeignKeyConstraint(
            ["export_id", "project_id"],
            ["exports.id", "exports.project_id"],
            name="fk_export_items_export_project",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["artifact_id", "project_id"],
            ["artifacts.id", "artifacts.project_id"],
            name="fk_export_items_artifact_project",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "package_path !~ '(^/|^[A-Za-z]:|\\\\|(^|/)\\.\\.(/|$)|\\x00)'",
            name="ck_export_items_safe_path",
        ),
        sa.CheckConstraint(
            "sha256 IS NULL OR sha256 ~ '^[0-9a-f]{64}$'", name="ck_export_items_hash"
        ),
    )
    for column in ("export_id", "project_id", "object_id", "artifact_id"):
        op.create_index(f"ix_export_items_{column}", "export_items", [column])
    op.create_index(
        "ix_export_items_project_export", "export_items", ["project_id", "export_id"]
    )


def downgrade() -> None:
    op.drop_table("export_items")
    op.drop_table("repro_packages")
    op.drop_table("exports")
    op.drop_index(
        "uq_claim_evidence_links_canonical_live", table_name="claim_evidence_links"
    )
    op.drop_table("claim_evidence_links")
    op.drop_constraint("ck_audit_results_target_shape", "audit_results", type_="check")
    op.drop_constraint("ck_audit_results_source_hashes", "audit_results", type_="check")
    op.drop_index("ix_audit_results_project_target", table_name="audit_results")
    op.drop_index("ix_audit_results_target_object_id", table_name="audit_results")
    op.drop_index("ix_audit_results_target_object_type", table_name="audit_results")
    for column in (
        "invalidated_at",
        "degraded",
        "limitations",
        "evidence_object_ids",
        "findings",
        "outcome",
        "source_snapshot_hash",
        "source_snapshot",
        "target_object_id",
        "target_object_type",
    ):
        op.drop_column("audit_results", column)
    op.create_check_constraint(
        "ck_audit_results_source_hashes",
        "audit_results",
        "before_source_hash ~ '^[0-9a-f]{64}$' AND after_source_hash ~ '^[0-9a-f]{64}$'",
    )
    op.alter_column("audit_results", "after_source_hash", nullable=False)
    op.alter_column("audit_results", "before_source_hash", nullable=False)
    op.alter_column("audit_results", "manuscript_id", nullable=False)
    op.alter_column("audit_results", "after_version_id", nullable=False)
    op.alter_column("audit_results", "before_version_id", nullable=False)
    for enum_name in (
        "export_item_include_status",
        "export_status",
        "export_type",
        "evidence_link_status",
        "evidence_link_strength",
        "evidence_relation_type",
        "evidence_object_type",
        "audit_result_outcome",
    ):
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
