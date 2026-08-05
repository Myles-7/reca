import os
from collections.abc import Generator

# Settings are constructed at application import time. These test-only defaults
# permit isolated configuration tests without creating a local .env file.
_TEST_ENVIRONMENT = {
    "ENVIRONMENT": "test",
    "SECRET_KEY": "test-secret-key-not-for-production-1234567890",
    "FIRST_SUPERUSER": "admin@example.com",
    "FIRST_SUPERUSER_PASSWORD": "test-admin-password",
    "POSTGRES_SERVER": "localhost",
    "POSTGRES_DB": "reca_test",
    "POSTGRES_USER": "reca",
    "POSTGRES_PASSWORD": "test-postgres-password",
    "VALKEY_URL": "valkey://localhost:6379/0",
    "MINIO_ENDPOINT": "http://localhost:9000",
    "MINIO_ROOT_USER": "reca-test-admin",
    "MINIO_ROOT_PASSWORD": "test-minio-password",
    "GROBID_URL": "http://localhost:8070",
    "CELERY_BROKER_URL": "redis://localhost:6379/0",
    "CELERY_RESULT_BACKEND": "redis://localhost:6379/1",
}

for _name, _value in _TEST_ENVIRONMENT.items():
    os.environ.setdefault(_name, _value)

# These imports must follow the test-only environment defaults above.
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlmodel import Session, delete  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.core.db import engine, init_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import User  # noqa: E402
from tests.utils.user import authentication_token_from_email  # noqa: E402
from tests.utils.utils import get_superuser_token_headers  # noqa: E402


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Keep pure unit tests independent from the integration database fixture."""
    for item in items:
        if "no_database" not in item.keywords:
            item.add_marker(pytest.mark.usefixtures("db"))


@pytest.fixture(scope="session")
def db() -> Generator[Session]:
    with Session(engine) as session:
        init_db(session)
        yield session
        session.rollback()
        session.execute(
            text(
                "TRUNCATE TABLE figure_validation_issues, figures, figure_render_runs, "
                "figure_plans, code_artifacts, analysis_results, analysis_runs, "
                "analysis_assumption_checks, analysis_plans, "
                "topic_candidate_evidence, topic_candidates, "
                "topic_generation_runs, evidence_set_summaries, "
                "literature_decisions, evidence_span_verification_records, "
                "literature_extraction_field_revisions, "
                "literature_extraction_fields, evidence_spans, "
                "literature_extractions, document_chunks, document_pages, documents, "
                "literature_search_candidates, "
                "literature_records, literature_search_runs, query_plans, "
                "research_question_versions, "
                "research_questions, "
                "model_invocations, approval_items, approval_records, "
                "processing_runs, jobs, audit_logs, "
                "idempotency_records, artifact_relations, artifacts, "
                "project_members, research_projects CASCADE"
            )
        )
        statement = delete(User)
        session.execute(statement)
        session.commit()


@pytest.fixture(scope="module")
def client() -> Generator[TestClient]:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def superuser_token_headers(client: TestClient) -> dict[str, str]:
    return get_superuser_token_headers(client)


@pytest.fixture(scope="module")
def normal_user_token_headers(client: TestClient, db: Session) -> dict[str, str]:
    return authentication_token_from_email(
        client=client, email=settings.EMAIL_TEST_USER, db=db
    )
