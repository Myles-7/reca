"""Add the M1 Artifact and ArtifactRelation foundation.

Revision ID: 0004_artifact_foundation
Revises: 0003_project_foundation
Create Date: 2026-08-01
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0004_artifact_foundation"
down_revision = "0003_project_foundation"
branch_labels = None
depends_on = None

artifact_type_enum = postgresql.ENUM(
    "PDF_DOCUMENT",
    "DATASET_FILE",
    "MANUSCRIPT_DOCX",
    "FIGURE_PNG",
    "FIGURE_SVG",
    "FIGURE_PDF",
    "ANALYSIS_CODE",
    "ANALYSIS_LOG",
    "JSON_RESULT",
    "CSV_EXPORT",
    "XLSX_EXPORT",
    "REPRO_PACKAGE",
    "MANIFEST",
    "MODEL_OUTPUT",
    "OTHER",
    name="artifact_type",
    create_type=False,
)
storage_provider_enum = postgresql.ENUM(
    "MINIO", "S3", "LOCAL", name="storage_provider", create_type=False
)
artifact_status_enum = postgresql.ENUM(
    "UPLOADING",
    "AVAILABLE",
    "FAILED",
    "DELETED",
    "QUARANTINED",
    name="artifact_status",
    create_type=False,
)
artifact_relation_type_enum = postgresql.ENUM(
    "DERIVED_FROM",
    "GENERATED_FROM",
    "PACKAGED_IN",
    "PREVIEW_OF",
    "REPLACEMENT_OF",
    "CODE_FOR",
    "LOG_FOR",
    name="artifact_relation_type",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    for enum in (
        artifact_type_enum,
        storage_provider_enum,
        artifact_status_enum,
        artifact_relation_type_enum,
    ):
        enum.create(bind, checkfirst=True)

    op.create_table(
        "artifacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("artifact_type", artifact_type_enum, nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=True),
        sa.Column("storage_provider", storage_provider_enum, nullable=False),
        sa.Column("storage_key", sa.String(length=512), nullable=False),
        sa.Column("mime_type", sa.String(length=255), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("source_artifact_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_original", sa.Boolean(), nullable=False),
        sa.Column("is_immutable", sa.Boolean(), nullable=False),
        sa.Column("status", artifact_status_enum, nullable=False),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "NOT is_original OR is_immutable",
            name="ck_artifacts_original_immutable",
        ),
        sa.CheckConstraint(
            "sha256 ~ '^[0-9a-f]{64}$'",
            name="ck_artifacts_sha256_lower_hex",
        ),
        sa.CheckConstraint("size_bytes >= 0", name="ck_artifacts_size_nonnegative"),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["user.id"],
            name="fk_artifacts_created_by_user",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["research_projects.id"],
            name="fk_artifacts_project_id_research_projects",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["source_artifact_id"],
            ["artifacts.id"],
            name="fk_artifacts_source_artifact_id_artifacts",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_artifacts"),
        sa.UniqueConstraint("storage_key", name="uq_artifacts_storage_key"),
    )
    op.create_index("ix_artifacts_project_id", "artifacts", ["project_id"])
    op.create_index("ix_artifacts_sha256", "artifacts", ["sha256"])
    op.create_index(
        "ix_artifacts_source_artifact_id", "artifacts", ["source_artifact_id"]
    )
    op.create_index("ix_artifacts_created_by", "artifacts", ["created_by"])
    op.create_index(
        "ix_artifacts_project_status", "artifacts", ["project_id", "status"]
    )
    op.create_index(
        "ix_artifacts_project_created", "artifacts", ["project_id", "created_at"]
    )

    op.create_table(
        "artifact_relations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_artifact_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_artifact_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("relation_type", artifact_relation_type_enum, nullable=False),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "source_artifact_id <> target_artifact_id",
            name="ck_artifact_relations_not_self",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["research_projects.id"],
            name="fk_artifact_relations_project_id_research_projects",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["source_artifact_id"],
            ["artifacts.id"],
            name="fk_artifact_relations_source_artifact_id_artifacts",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["target_artifact_id"],
            ["artifacts.id"],
            name="fk_artifact_relations_target_artifact_id_artifacts",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_artifact_relations"),
        sa.UniqueConstraint(
            "source_artifact_id",
            "target_artifact_id",
            "relation_type",
            name="uq_artifact_relations_source_target_type",
        ),
    )
    op.create_index(
        "ix_artifact_relations_project_id", "artifact_relations", ["project_id"]
    )
    op.create_index(
        "ix_artifact_relations_source_artifact_id",
        "artifact_relations",
        ["source_artifact_id"],
    )
    op.create_index(
        "ix_artifact_relations_target_artifact_id",
        "artifact_relations",
        ["target_artifact_id"],
    )
    op.create_index(
        "ix_artifact_relations_project_created",
        "artifact_relations",
        ["project_id", "created_at"],
    )

    op.execute(
        """
        CREATE FUNCTION enforce_artifact_immutability() RETURNS trigger AS $$
        BEGIN
            IF OLD.status = 'AVAILABLE' AND (
                NEW.storage_key IS DISTINCT FROM OLD.storage_key OR
                NEW.mime_type IS DISTINCT FROM OLD.mime_type OR
                NEW.size_bytes IS DISTINCT FROM OLD.size_bytes OR
                NEW.sha256 IS DISTINCT FROM OLD.sha256 OR
                NEW.is_original IS DISTINCT FROM OLD.is_original OR
                NEW.is_immutable IS DISTINCT FROM OLD.is_immutable
            ) THEN
                RAISE EXCEPTION 'available artifact content is immutable';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER artifacts_immutable_content
        BEFORE UPDATE ON artifacts
        FOR EACH ROW EXECUTE FUNCTION enforce_artifact_immutability();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER artifacts_immutable_content ON artifacts")
    op.execute("DROP FUNCTION enforce_artifact_immutability()")

    op.drop_index(
        "ix_artifact_relations_project_created", table_name="artifact_relations"
    )
    op.drop_index(
        "ix_artifact_relations_target_artifact_id", table_name="artifact_relations"
    )
    op.drop_index(
        "ix_artifact_relations_source_artifact_id", table_name="artifact_relations"
    )
    op.drop_index("ix_artifact_relations_project_id", table_name="artifact_relations")
    op.drop_table("artifact_relations")

    op.drop_index("ix_artifacts_project_created", table_name="artifacts")
    op.drop_index("ix_artifacts_project_status", table_name="artifacts")
    op.drop_index("ix_artifacts_created_by", table_name="artifacts")
    op.drop_index("ix_artifacts_source_artifact_id", table_name="artifacts")
    op.drop_index("ix_artifacts_sha256", table_name="artifacts")
    op.drop_index("ix_artifacts_project_id", table_name="artifacts")
    op.drop_table("artifacts")

    bind = op.get_bind()
    for enum in (
        artifact_relation_type_enum,
        artifact_status_enum,
        storage_provider_enum,
        artifact_type_enum,
    ):
        enum.drop(bind, checkfirst=True)
