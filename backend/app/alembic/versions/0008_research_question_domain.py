"""Add the M2 ResearchQuestion domain and version invariants.

Revision ID: 0008_research_question_domain
Revises: 0007_model_invocation_governance
Create Date: 2026-08-01
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0008_research_question_domain"
down_revision = "0007_model_invocation_governance"
branch_labels = None
depends_on = None

research_question_status_enum = postgresql.ENUM(
    "DRAFT",
    "CONFIRMED",
    "SUPERSEDED",
    "ARCHIVED",
    name="research_question_status",
    create_type=False,
)
research_question_version_status_enum = postgresql.ENUM(
    "DRAFT",
    "NEEDS_INPUT",
    "READY",
    "CONFIRMED",
    "SUPERSEDED",
    name="research_question_version_status",
    create_type=False,
)
research_goal_enum = postgresql.ENUM(
    "DESCRIBE",
    "COMPARE",
    "RELATE",
    "PREDICT",
    name="research_goal",
    create_type=False,
)
research_relationship_type_enum = postgresql.ENUM(
    "ASSOCIATION",
    "COMPARISON",
    "PREDICTION",
    "UNSPECIFIED",
    name="research_relationship_type",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    research_question_status_enum.create(bind, checkfirst=True)
    research_question_version_status_enum.create(bind, checkfirst=True)
    research_goal_enum.create(bind, checkfirst=True)
    research_relationship_type_enum.create(bind, checkfirst=True)

    op.create_unique_constraint(
        "uq_model_invocations_id_project",
        "model_invocations",
        ["id", "project_id"],
    )

    op.create_table(
        "research_questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", research_question_status_enum, nullable=False),
        sa.Column("current_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["research_projects.id"],
            name="fk_research_questions_project_id_research_projects",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["user.id"],
            name="fk_research_questions_created_by_user",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_research_questions"),
        sa.UniqueConstraint(
            "id", "project_id", name="uq_research_questions_id_project"
        ),
    )
    for column in ("project_id", "current_version_id", "created_by"):
        op.create_index(
            f"ix_research_questions_{column}", "research_questions", [column]
        )
    op.create_index(
        "ix_research_questions_project_status",
        "research_questions",
        ["project_id", "status"],
    )

    op.create_table(
        "research_question_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "research_question_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("raw_input", sa.Text(), nullable=False),
        sa.Column("normalized_question", sa.Text(), nullable=True),
        sa.Column("research_object", sa.Text(), nullable=True),
        sa.Column("population", sa.Text(), nullable=True),
        sa.Column("context", sa.Text(), nullable=True),
        sa.Column("independent_variables", postgresql.JSONB(), nullable=True),
        sa.Column("dependent_variables", postgresql.JSONB(), nullable=True),
        sa.Column("control_variables", postgresql.JSONB(), nullable=True),
        sa.Column("research_goal", research_goal_enum, nullable=True),
        sa.Column(
            "relationship_type", research_relationship_type_enum, nullable=True
        ),
        sa.Column("method_preference", postgresql.JSONB(), nullable=True),
        sa.Column("time_scope", postgresql.JSONB(), nullable=True),
        sa.Column("region_scope", postgresql.JSONB(), nullable=True),
        sa.Column("language_scope", postgresql.JSONB(), nullable=True),
        sa.Column("resource_constraints", postgresql.JSONB(), nullable=True),
        sa.Column("ethical_constraints", postgresql.JSONB(), nullable=True),
        sa.Column("uncertainties", postgresql.JSONB(), nullable=True),
        sa.Column(
            "source_model_invocation_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column("status", research_question_version_status_enum, nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "version_number >= 1",
            name="ck_research_question_versions_number_positive",
        ),
        sa.ForeignKeyConstraint(
            ["research_question_id", "project_id"],
            ["research_questions.id", "research_questions.project_id"],
            name="fk_research_question_versions_question_project",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["source_model_invocation_id", "project_id"],
            ["model_invocations.id", "model_invocations.project_id"],
            name="fk_research_question_versions_model_invocation_project",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["user.id"],
            name="fk_research_question_versions_created_by_user",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_research_question_versions"),
        sa.UniqueConstraint(
            "research_question_id",
            "version_number",
            name="uq_research_question_versions_question_number",
        ),
        sa.UniqueConstraint(
            "id", "project_id", name="uq_research_question_versions_id_project"
        ),
        sa.UniqueConstraint(
            "id",
            "research_question_id",
            "project_id",
            name="uq_research_question_versions_id_question_project",
        ),
    )
    for column in (
        "research_question_id",
        "project_id",
        "source_model_invocation_id",
        "created_by",
    ):
        op.create_index(
            f"ix_research_question_versions_{column}",
            "research_question_versions",
            [column],
        )
    op.create_index(
        "ix_research_question_versions_project_status",
        "research_question_versions",
        ["project_id", "status"],
    )

    op.create_foreign_key(
        "fk_research_questions_current_version_scope",
        "research_questions",
        "research_question_versions",
        ["current_version_id", "id", "project_id"],
        ["id", "research_question_id", "project_id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_research_projects_current_rq_version_project",
        "research_projects",
        "research_question_versions",
        ["current_research_question_version_id", "id"],
        ["id", "project_id"],
        ondelete="RESTRICT",
    )

    op.execute(
        """
        CREATE FUNCTION enforce_research_question_version_history()
        RETURNS trigger AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                RAISE EXCEPTION 'research_question_versions are retained history';
            END IF;
            IF TG_OP = 'UPDATE' THEN
                IF NEW.id IS DISTINCT FROM OLD.id
                    OR NEW.research_question_id IS DISTINCT FROM OLD.research_question_id
                    OR NEW.project_id IS DISTINCT FROM OLD.project_id
                    OR NEW.version_number IS DISTINCT FROM OLD.version_number
                    OR NEW.raw_input IS DISTINCT FROM OLD.raw_input
                    OR NEW.normalized_question IS DISTINCT FROM OLD.normalized_question
                    OR NEW.research_object IS DISTINCT FROM OLD.research_object
                    OR NEW.population IS DISTINCT FROM OLD.population
                    OR NEW.context IS DISTINCT FROM OLD.context
                    OR NEW.independent_variables IS DISTINCT FROM OLD.independent_variables
                    OR NEW.dependent_variables IS DISTINCT FROM OLD.dependent_variables
                    OR NEW.control_variables IS DISTINCT FROM OLD.control_variables
                    OR NEW.research_goal IS DISTINCT FROM OLD.research_goal
                    OR NEW.relationship_type IS DISTINCT FROM OLD.relationship_type
                    OR NEW.method_preference IS DISTINCT FROM OLD.method_preference
                    OR NEW.time_scope IS DISTINCT FROM OLD.time_scope
                    OR NEW.region_scope IS DISTINCT FROM OLD.region_scope
                    OR NEW.language_scope IS DISTINCT FROM OLD.language_scope
                    OR NEW.resource_constraints IS DISTINCT FROM OLD.resource_constraints
                    OR NEW.ethical_constraints IS DISTINCT FROM OLD.ethical_constraints
                    OR NEW.uncertainties IS DISTINCT FROM OLD.uncertainties
                    OR NEW.source_model_invocation_id IS DISTINCT FROM OLD.source_model_invocation_id
                    OR NEW.created_by IS DISTINCT FROM OLD.created_by
                    OR NEW.created_at IS DISTINCT FROM OLD.created_at THEN
                    RAISE EXCEPTION 'research_question_version content is immutable';
                END IF;
                IF OLD.status IS DISTINCT FROM NEW.status AND NOT (
                    (OLD.status = 'DRAFT' AND NEW.status IN ('NEEDS_INPUT', 'READY'))
                    OR (OLD.status = 'NEEDS_INPUT' AND NEW.status IN ('DRAFT', 'READY'))
                    OR (OLD.status = 'READY' AND NEW.status IN ('DRAFT', 'CONFIRMED'))
                    OR (OLD.status = 'CONFIRMED' AND NEW.status = 'SUPERSEDED')
                ) THEN
                    RAISE EXCEPTION 'invalid research_question_version transition';
                END IF;
            END IF;
            IF NEW.status = 'CONFIRMED' AND NOT EXISTS (
                SELECT 1 FROM approval_records ar
                WHERE ar.project_id = NEW.project_id
                  AND ar.approval_type = 'RESEARCH_QUESTION_CONFIRMATION'
                  AND ar.target_object_type = 'research_question_version'
                  AND ar.target_object_id = NEW.id
                  AND ar.status = 'APPROVED'
            ) THEN
                RAISE EXCEPTION 'confirmed research_question_version requires approved ApprovalRecord';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER research_question_versions_history_guard
        BEFORE INSERT OR UPDATE OR DELETE ON research_question_versions
        FOR EACH ROW EXECUTE FUNCTION enforce_research_question_version_history();
        """
    )


def downgrade() -> None:
    op.execute(
        "DROP TRIGGER research_question_versions_history_guard "
        "ON research_question_versions"
    )
    op.execute("DROP FUNCTION enforce_research_question_version_history()")
    op.drop_constraint(
        "fk_research_projects_current_rq_version_project",
        "research_projects",
        type_="foreignkey",
    )
    op.execute(
        "UPDATE research_projects "
        "SET current_research_question_version_id = NULL "
        "WHERE current_research_question_version_id IS NOT NULL"
    )
    op.drop_constraint(
        "fk_research_questions_current_version_scope",
        "research_questions",
        type_="foreignkey",
    )
    op.drop_index(
        "ix_research_question_versions_project_status",
        table_name="research_question_versions",
    )
    for column in (
        "created_by",
        "source_model_invocation_id",
        "project_id",
        "research_question_id",
    ):
        op.drop_index(
            f"ix_research_question_versions_{column}",
            table_name="research_question_versions",
        )
    op.drop_table("research_question_versions")
    op.drop_index(
        "ix_research_questions_project_status", table_name="research_questions"
    )
    for column in ("created_by", "current_version_id", "project_id"):
        op.drop_index(
            f"ix_research_questions_{column}", table_name="research_questions"
        )
    op.drop_table("research_questions")
    op.drop_constraint(
        "uq_model_invocations_id_project",
        "model_invocations",
        type_="unique",
    )

    bind = op.get_bind()
    research_relationship_type_enum.drop(bind, checkfirst=True)
    research_goal_enum.drop(bind, checkfirst=True)
    research_question_version_status_enum.drop(bind, checkfirst=True)
    research_question_status_enum.drop(bind, checkfirst=True)
