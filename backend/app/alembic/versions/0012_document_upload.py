"""Add M2 Document persistence and Artifact binding.

Revision ID: 0012_document_upload
Revises: 0011_literature_search
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0012_document_upload"
down_revision = "0011_literature_search"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


class VectorType(sa.types.UserDefinedType[object]):
    cache_ok = True

    def get_col_spec(self, **_kw: object) -> str:
        return "VECTOR"


def upgrade() -> None:
    bind = op.get_bind()
    document_type = postgresql.ENUM(
        "SCHOLARLY_PDF", "MANUSCRIPT", "OTHER", name="document_type"
    )
    parser_type = postgresql.ENUM(
        "GROBID", "PYPDF", "NONE", name="document_parser_type"
    )
    parse_confidence = postgresql.ENUM(
        "HIGH",
        "MEDIUM",
        "LOW",
        "UNKNOWN",
        name="document_parse_confidence",
    )
    document_type.create(bind, checkfirst=True)
    parser_type.create(bind, checkfirst=True)
    parse_confidence.create(bind, checkfirst=True)

    op.create_unique_constraint(
        "uq_artifacts_id_project", "artifacts", ["id", "project_id"]
    )
    op.create_table(
        "documents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("artifact_id", sa.Uuid(), nullable=False),
        sa.Column(
            "document_type",
            postgresql.ENUM(name="document_type", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "parser_type",
            postgresql.ENUM(name="document_parser_type", create_type=False),
            nullable=True,
        ),
        sa.Column("parser_version", sa.String(length=100), nullable=True),
        sa.Column(
            "parse_status",
            postgresql.ENUM(name="job_status", create_type=False),
            nullable=False,
        ),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("language", sa.String(length=50), nullable=True),
        sa.Column("is_scanned", sa.Boolean(), nullable=True),
        sa.Column(
            "parse_confidence",
            postgresql.ENUM(name="document_parse_confidence", create_type=False),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "page_count IS NULL OR page_count >= 1",
            name="ck_documents_page_count_positive",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["research_projects.id"],
            name="fk_documents_project",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["artifact_id", "project_id"],
            ["artifacts.id", "artifacts.project_id"],
            name="fk_documents_artifact_project",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_documents"),
        sa.UniqueConstraint("id", "project_id", name="uq_documents_id_project"),
        sa.UniqueConstraint("artifact_id", name="uq_documents_artifact"),
    )
    for column in ("project_id", "artifact_id"):
        op.create_index(f"ix_documents_{column}", "documents", [column])
    op.create_index(
        "ix_documents_project_status", "documents", ["project_id", "parse_status"]
    )
    op.create_index(
        "ix_documents_project_created", "documents", ["project_id", "created_at"]
    )

    op.create_table(
        "document_pages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("printed_page_label", sa.String(length=100), nullable=True),
        sa.Column("text_content", sa.Text(), nullable=True),
        sa.Column("width", sa.Float(), nullable=True),
        sa.Column("height", sa.Float(), nullable=True),
        sa.Column("parser_metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "page_number >= 1", name="ck_document_pages_number_positive"
        ),
        sa.CheckConstraint(
            "width IS NULL OR width > 0", name="ck_document_pages_width_positive"
        ),
        sa.CheckConstraint(
            "height IS NULL OR height > 0", name="ck_document_pages_height_positive"
        ),
        sa.ForeignKeyConstraint(
            ["document_id", "project_id"],
            ["documents.id", "documents.project_id"],
            name="fk_document_pages_document_project",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_document_pages"),
        sa.UniqueConstraint(
            "document_id",
            "page_number",
            name="uq_document_pages_document_number",
        ),
    )
    for column in ("document_id", "project_id"):
        op.create_index(f"ix_document_pages_{column}", "document_pages", [column])
    op.create_index(
        "ix_document_pages_project_document",
        "document_pages",
        ["project_id", "document_id"],
    )

    op.create_table(
        "document_chunks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("page_start", sa.Integer(), nullable=False),
        sa.Column("page_end", sa.Integer(), nullable=False),
        sa.Column("section_path", postgresql.JSONB(), nullable=True),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=True),
        sa.Column("embedding", VectorType(), nullable=True),
        sa.Column("embedding_model", sa.String(length=200), nullable=True),
        sa.Column("embedding_version", sa.String(length=100), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("page_start >= 1", name="ck_document_chunks_page_start"),
        sa.CheckConstraint(
            "page_end >= page_start", name="ck_document_chunks_page_range"
        ),
        sa.CheckConstraint("chunk_index >= 0", name="ck_document_chunks_index"),
        sa.CheckConstraint(
            "content_hash ~ '^[0-9a-f]{64}$'",
            name="ck_document_chunks_content_hash",
        ),
        sa.ForeignKeyConstraint(
            ["document_id", "project_id"],
            ["documents.id", "documents.project_id"],
            name="fk_document_chunks_document_project",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_document_chunks"),
    )
    for column in ("project_id", "document_id"):
        op.create_index(f"ix_document_chunks_{column}", "document_chunks", [column])
    op.create_index(
        "ix_document_chunks_project_document",
        "document_chunks",
        ["project_id", "document_id"],
    )
    op.create_index(
        "ix_document_chunks_document_index",
        "document_chunks",
        ["document_id", "chunk_index"],
    )

    op.create_foreign_key(
        "fk_literature_records_document_project",
        "literature_records",
        "documents",
        ["document_id", "project_id"],
        ["id", "project_id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_literature_records_document_project",
        "literature_records",
        type_="foreignkey",
    )
    op.drop_table("document_chunks")
    op.drop_table("document_pages")
    op.drop_table("documents")
    op.drop_constraint("uq_artifacts_id_project", "artifacts", type_="unique")
    postgresql.ENUM(name="document_parse_confidence").drop(
        op.get_bind(), checkfirst=True
    )
    postgresql.ENUM(name="document_parser_type").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="document_type").drop(op.get_bind(), checkfirst=True)
