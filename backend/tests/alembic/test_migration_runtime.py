import uuid
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url

from app.core.config import settings


def _alembic_config() -> Config:
    backend_root = Path(__file__).resolve().parents[2]
    config = Config(str(backend_root / "alembic.ini"))
    config.set_main_option("script_location", str(backend_root / "app/alembic"))
    return config


def test_scoping_migration_downgrade_policy_with_existing_data() -> None:
    database_name = f"reca_migration_{uuid.uuid4().hex}"
    original_database = settings.POSTGRES_DB
    admin_url = make_url(settings.database_url).set(database="postgres")
    test_url = make_url(settings.database_url).set(database=database_name)
    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    test_engine = create_engine(test_url)

    with admin_engine.connect() as connection:
        connection.execute(text(f'CREATE DATABASE "{database_name}"'))

    try:
        settings.POSTGRES_DB = database_name
        config = _alembic_config()
        command.upgrade(config, "0009_rq_scoping_job")

        owner_id = uuid.uuid4()
        project_id = uuid.uuid4()
        job_id = uuid.uuid4()
        resource_id = uuid.uuid4()
        with test_engine.begin() as connection:
            connection.execute(
                text(
                    'INSERT INTO "user" '
                    "(id, email, is_active, is_superuser, hashed_password, created_at) "
                    "VALUES (:id, :email, true, false, :password, now())"
                ),
                {
                    "id": owner_id,
                    "email": f"migration-{owner_id}@example.com",
                    "password": "not-used-by-migration-test",
                },
            )
            connection.execute(
                text(
                    "INSERT INTO research_projects "
                    "(id, owner_id, name, project_type, current_stage, status, "
                    "lock_version, created_at, updated_at) "
                    "VALUES (:id, :owner_id, 'Migration test', 'RESEARCH', "
                    "'INTENT', 'ACTIVE', 1, now(), now())"
                ),
                {"id": project_id, "owner_id": owner_id},
            )
            connection.execute(
                text(
                    "INSERT INTO jobs "
                    "(id, project_id, task_type, resource_type, resource_id, status, "
                    "idempotency_key, progress_percent, retry_count, max_retries, "
                    "created_at, retryable) "
                    "VALUES (:id, :project_id, 'RESEARCH_QUESTION_SCOPING', "
                    "'research_question_version', :resource_id, 'DRAFT', "
                    ":idempotency_key, 0, 0, 3, now(), false)"
                ),
                {
                    "id": job_id,
                    "project_id": project_id,
                    "resource_id": resource_id,
                    "idempotency_key": f"migration-test-{job_id}",
                },
            )

        with pytest.raises(RuntimeError, match="scoping job data exists"):
            command.downgrade(config, "0008_research_question_domain")

        with test_engine.begin() as connection:
            connection.execute(text("DELETE FROM jobs WHERE id = :id"), {"id": job_id})

        command.downgrade(config, "0008_research_question_domain")
        assert "model_invocation_id" not in {
            column["name"] for column in inspect(test_engine).get_columns("audit_logs")
        }

        command.upgrade(config, "0009_rq_scoping_job")
        assert "model_invocation_id" in {
            column["name"] for column in inspect(test_engine).get_columns("audit_logs")
        }
    finally:
        settings.POSTGRES_DB = original_database
        test_engine.dispose()
        with admin_engine.connect() as connection:
            connection.execute(
                text(
                    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                    "WHERE datname = :database_name AND pid <> pg_backend_pid()"
                ),
                {"database_name": database_name},
            )
            connection.execute(text(f'DROP DATABASE IF EXISTS "{database_name}"'))
        admin_engine.dispose()
