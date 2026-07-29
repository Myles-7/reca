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
}

for _name, _value in _TEST_ENVIRONMENT.items():
    os.environ.setdefault(_name, _value)

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, delete

from app.core.config import settings
from app.core.db import engine, init_db
from app.main import app
from app.models import User
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import get_superuser_token_headers


@pytest.fixture(scope="session", autouse=True)
def db() -> Generator[Session]:
    with Session(engine) as session:
        init_db(session)
        yield session
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
