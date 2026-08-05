from pathlib import Path

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory

from app.models import AuditLog, ProjectMember

pytestmark = pytest.mark.no_database


def test_pgvector_migration_is_idempotent() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    migration = (
        repository_root
        / "backend/app/alembic/versions/0002_enable_pgvector_extension.py"
    ).read_text(encoding="utf-8")

    assert "CREATE EXTENSION IF NOT EXISTS vector" in migration
    assert "0001_reca_user_foundation" in migration


def test_m0_migrations_do_not_create_m1_business_tables() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    migrations = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (repository_root / "backend/app/alembic/versions").glob(
            "000[12]_*.py"
        )
    ).lower()

    for forbidden_table in (
        "researchproject",
        "artifact",
        "approvalrecord",
        "processingrun",
        "literaturerecord",
        "datasetversion",
        "analysisrun",
        "claim",
    ):
        assert forbidden_table not in migrations
    assert '"job"' not in migrations


def test_m1_project_migration_preserves_owner_and_audit_invariants() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    migration = (
        repository_root / "backend/app/alembic/versions/0003_project_foundation.py"
    ).read_text(encoding="utf-8")

    assert '"research_projects"' in migration
    assert '"project_members"' in migration
    assert '"audit_logs"' in migration
    assert '"idempotency_records"' in migration
    assert "uq_project_members_active_owner" in migration
    assert "role = 'OWNER' AND removed_at IS NULL" in migration
    assert "uq_project_members_project_user" in migration
    assert "audit_logs_append_only" in migration
    assert 'down_revision = "0002_enable_pgvector_extension"' in migration


def test_m1_artifact_migration_preserves_storage_and_immutability_invariants() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    migration = (
        repository_root / "backend/app/alembic/versions/0004_artifact_foundation.py"
    ).read_text(encoding="utf-8")

    assert '"artifacts"' in migration
    assert '"artifact_relations"' in migration
    assert "uq_artifacts_storage_key" in migration
    assert "ix_artifacts_sha256" in migration
    assert "ck_artifacts_original_immutable" in migration
    assert "artifacts_immutable_content" in migration
    assert "available artifact content is immutable" in migration
    assert 'down_revision = "0003_project_foundation"' in migration


def test_m1_job_migration_preserves_job_and_attempt_invariants() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    migration = (
        repository_root
        / "backend/app/alembic/versions/0005_job_processing_foundation.py"
    ).read_text(encoding="utf-8")

    assert '"jobs"' in migration
    assert '"processing_runs"' in migration
    assert "uq_processing_runs_job_attempt" in migration
    assert "ck_jobs_progress_percent" in migration
    assert "ix_jobs_project_status" in migration
    assert "ix_processing_runs_project_status" in migration
    assert 'down_revision = "0004_artifact_foundation"' in migration


def test_m1_approval_migration_preserves_history_and_audit_invariants() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    migration = (
        repository_root / "backend/app/alembic/versions/0006_approval_foundation.py"
    ).read_text(encoding="utf-8")

    assert '"approval_records"' in migration
    assert '"approval_items"' in migration
    assert "ck_approval_records_payload_hash" in migration
    assert "approval_records_history_guard" in migration
    assert "approval_items_history_guard" in migration
    assert "fk_audit_logs_approval_id_approval_records" in migration
    assert 'down_revision = "0005_job_processing_foundation"' in migration


def test_sqlmodel_metadata_preserves_inherited_m1_constraints() -> None:
    approval_foreign_keys = {
        constraint.name: constraint
        for constraint in AuditLog.__table__.foreign_key_constraints
    }
    approval_constraint = approval_foreign_keys[
        "fk_audit_logs_approval_id_approval_records"
    ]
    assert approval_constraint.ondelete == "RESTRICT"
    assert [column.name for column in approval_constraint.columns] == ["approval_id"]
    assert [element.target_fullname for element in approval_constraint.elements] == [
        "approval_records.id"
    ]

    owner_index = next(
        index
        for index in ProjectMember.__table__.indexes
        if index.name == "uq_project_members_active_owner"
    )
    assert owner_index.unique is True
    assert [column.name for column in owner_index.columns] == ["project_id"]
    assert str(owner_index.dialect_options["postgresql"]["where"]) == (
        "role = 'OWNER' AND removed_at IS NULL"
    )


def test_m1_model_invocation_migration_preserves_governance_invariants() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    migration = (
        repository_root
        / "backend/app/alembic/versions/0007_model_invocation_governance.py"
    ).read_text(encoding="utf-8")

    assert '"model_invocations"' in migration
    assert "model_invocation_status" in migration
    assert "model_data_access_level" in migration
    assert "ck_model_invocations_effective_access" in migration
    assert "ck_model_invocations_outcome_fields" in migration
    assert "model_invocations_history_guard" in migration
    assert 'down_revision = "0006_approval_foundation"' in migration


def test_m2_research_question_migration_preserves_domain_invariants() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    migration = (
        repository_root
        / "backend/app/alembic/versions/0008_research_question_domain.py"
    ).read_text(encoding="utf-8")

    assert '"research_questions"' in migration
    assert '"research_question_versions"' in migration
    assert "uq_research_question_versions_question_number" in migration
    assert "fk_research_question_versions_question_project" in migration
    assert "fk_research_questions_current_version_scope" in migration
    assert "fk_research_projects_current_rq_version_project" in migration
    assert "research_question_versions_history_guard" in migration
    assert "NEEDS_USER_INPUT" not in migration
    assert 'down_revision = "0007_model_invocation_governance"' in migration


def test_m2_scoping_migration_registers_reversible_job_type() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    migration_path = (
        repository_root / "backend/app/alembic/versions/0009_rq_scoping_job.py"
    )
    migration = migration_path.read_text(encoding="utf-8")

    assert "RESEARCH_QUESTION_SCOPING" in migration
    assert "ALTER TYPE job_task_type" in migration
    assert "CREATE TYPE job_task_type AS ENUM" in migration
    assert 'revision = "0009_rq_scoping_job"' in migration
    assert migration_path.stem == "0009_rq_scoping_job"
    assert len(migration_path.stem) <= 32
    assert 'down_revision = "0008_research_question_domain"' in migration
    assert "fk_audit_logs_model_invocation_project" in migration
    assert "ix_audit_logs_model_invocation_id" in migration
    assert "Cannot downgrade 0009" in migration
    assert "NEEDS_USER_INPUT" not in migration


def test_m6_migration_graph_has_one_contiguous_head() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    config = Config(str(repository_root / "backend/alembic.ini"))
    config.set_main_option(
        "script_location", str(repository_root / "backend/app/alembic")
    )
    scripts = ScriptDirectory.from_config(config)

    assert scripts.get_heads() == ["0017_m6_manuscripts"]
    revisions = list(scripts.walk_revisions(base="base", head="heads"))
    assert revisions[-1].down_revision is None
    for current, parent in zip(revisions, revisions[1:], strict=False):
        assert current.down_revision == parent.revision


def test_m6_manuscript_migration_freezes_scope_and_immutability() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    migration_path = (
        repository_root / "backend/app/alembic/versions/0017_m6_manuscripts.py"
    )
    migration = migration_path.read_text(encoding="utf-8")
    assert 'down_revision: str | None = "0016_m5_figures"' in migration
    for table in (
        "manuscripts",
        "manuscript_versions",
        "manuscript_check_runs",
        "manuscript_issues",
        "manuscript_issue_evidence",
        "manuscript_transformations",
        "claims",
        "audit_results",
    ):
        assert f'"{table}"' in migration
    assert "fk_manuscripts_current_version_scope" in migration
    assert "fk_manuscript_versions_artifact_project" in migration
    assert "trg_manuscript_versions_immutable" in migration
    assert "MANUSCRIPT_REVISION_AUDIT" in migration


def test_m4_data_quality_migration_freezes_eight_tables_and_scope_constraints() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    migration_path = (
        repository_root / "backend/app/alembic/versions/0014_m4_data_quality.py"
    )
    migration = migration_path.read_text(encoding="utf-8")

    assert migration_path.stem == "0014_m4_data_quality"
    assert "down_revision = '0013_m3_evidence_matrix'" in migration
    tables = (
        "datasets",
        "dataset_versions",
        "dataset_columns",
        "data_quality_runs",
        "data_quality_issues",
        "cleaning_plans",
        "cleaning_plan_actions",
        "data_transformations",
    )
    assert migration.count("op.create_table(") == len(tables)
    for table in tables:
        assert f"op.create_table('{table}'" in migration
    for constraint in (
        "uq_dataset_versions_number",
        "fk_datasets_current_version_scope",
        "fk_dataset_versions_artifact_project",
        "fk_dataset_versions_parent_scope",
        "fk_dataset_versions_transformation_project",
        "fk_data_transformations_output_project",
    ):
        assert constraint in migration
    assert "CREATE TRIGGER" not in migration.upper()


def test_m2_query_plan_migration_preserves_scope_and_job_contract() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    migration = (
        repository_root / "backend/app/alembic/versions/0010_query_plan_domain.py"
    ).read_text(encoding="utf-8")

    assert 'revision = "0010_query_plan_domain"' in migration
    assert len("0010_query_plan_domain") <= 32
    assert 'down_revision = "0009_rq_scoping_job"' in migration
    assert '"query_plans"' in migration
    assert "fk_query_plans_rq_version_project" in migration
    assert "fk_query_plans_model_invocation_project" in migration
    assert "ck_query_plans_lock_version" in migration
    assert "QUERY_PLAN_GENERATION" in migration
    assert "DRAFT" in migration


def test_m2_literature_migration_preserves_candidate_and_dedup_boundaries() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    migration = (
        repository_root / "backend/app/alembic/versions/0011_literature_search.py"
    ).read_text(encoding="utf-8")

    assert 'revision = "0011_literature_search"' in migration
    assert len("0011_literature_search") <= 32
    assert 'down_revision = "0010_query_plan_domain"' in migration
    assert '"literature_search_runs"' in migration
    assert '"literature_search_candidates"' in migration
    assert '"literature_records"' in migration
    assert "fk_literature_candidates_run_project" in migration
    assert "uq_literature_records_project_doi" in migration
    assert "uq_literature_records_project_title" not in migration
    assert "LITERATURE_SEARCH" in migration


def test_m2_document_migration_preserves_artifact_and_project_boundaries() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    migration = (
        repository_root / "backend/app/alembic/versions/0012_document_upload.py"
    ).read_text(encoding="utf-8")

    assert 'revision = "0012_document_upload"' in migration
    assert len("0012_document_upload") <= 32
    assert 'down_revision = "0011_literature_search"' in migration
    assert '"documents"' in migration
    assert '"document_pages"' in migration
    assert '"document_chunks"' in migration
    assert "fk_documents_artifact_project" in migration
    assert "fk_literature_records_document_project" in migration
    assert "uq_document_pages_document_number" in migration
    assert "uq_documents_artifact" in migration
    assert 'ondelete="RESTRICT"' in migration


def test_m3_evidence_migration_preserves_scope_and_history_invariants() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    migration_path = (
        repository_root / "backend/app/alembic/versions/0013_m3_evidence_matrix.py"
    )
    migration = migration_path.read_text(encoding="utf-8")

    assert migration_path.stem == "0013_m3_evidence_matrix"
    assert len(migration_path.stem) <= 32
    assert 'down_revision = "0012_document_upload"' in migration
    for table in (
        "literature_extractions",
        "literature_extraction_fields",
        "literature_extraction_field_revisions",
        "evidence_spans",
        "evidence_span_verification_records",
        "literature_decisions",
        "evidence_set_summaries",
        "topic_generation_runs",
        "topic_candidates",
        "topic_candidate_evidence",
    ):
        assert f'"{table}"' in migration
    assert "m3_append_only_guard" in migration
    assert "m3_topic_run_completion_guard" in migration
    assert "TOPIC_GENERATE" in migration
