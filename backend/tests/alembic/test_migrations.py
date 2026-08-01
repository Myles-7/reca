from pathlib import Path

import pytest

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
