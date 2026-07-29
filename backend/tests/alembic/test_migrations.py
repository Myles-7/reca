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


def test_foundation_migrations_do_not_create_m1_business_tables() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    migrations = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (repository_root / "backend/app/alembic/versions").glob("*.py")
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
