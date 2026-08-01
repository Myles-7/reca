from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.config import Settings

pytestmark = pytest.mark.no_database


def build_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "PROJECT_NAME": "RECA",
        "ENVIRONMENT": "local",
        "SECRET_KEY": "local-secret-key-that-is-long-enough-for-testing",
        "FIRST_SUPERUSER": "admin@example.com",
        "FIRST_SUPERUSER_PASSWORD": "local-admin-password",
        "POSTGRES_SERVER": "postgres",
        "POSTGRES_DB": "reca",
        "POSTGRES_USER": "reca",
        "POSTGRES_PASSWORD": "postgres-password",
        "VALKEY_URL": "valkey://valkey:6379/0",
        "MINIO_ENDPOINT": "http://minio:9000",
        "MINIO_ROOT_USER": "reca-admin",
        "MINIO_ROOT_PASSWORD": "minio-password",
        "GROBID_URL": "http://grobid:8070",
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


def test_local_minimal_configuration_keeps_optional_providers_unconfigured() -> None:
    configured = build_settings()

    assert configured.ENVIRONMENT == "local"
    assert configured.model_status == "UNCONFIGURED"
    assert configured.openalex_status == "UNCONFIGURED"


@pytest.mark.parametrize("environment", ["test", "demo"])
def test_test_and_demo_configurations_are_supported(environment: str) -> None:
    assert build_settings(ENVIRONMENT=environment).ENVIRONMENT == environment


def test_production_rejects_placeholder_or_short_secret_without_leaking_it() -> None:
    secret = "change-me-real-secret"

    with pytest.raises(ValidationError) as captured:
        build_settings(ENVIRONMENT="production", SECRET_KEY=secret)

    assert secret not in str(captured.value)
    assert "production SECRET_KEY is invalid" in str(captured.value)


def test_production_rejects_short_secret() -> None:
    with pytest.raises(ValidationError):
        build_settings(ENVIRONMENT="production", SECRET_KEY="short-secret")


def test_invalid_environment_and_urls_fail_safely() -> None:
    with pytest.raises(ValidationError):
        build_settings(ENVIRONMENT="staging")
    with pytest.raises(ValidationError):
        build_settings(VALKEY_URL="http://valkey:6379")
    with pytest.raises(ValidationError):
        build_settings(MINIO_ENDPOINT="not-a-url")
    with pytest.raises(ValidationError):
        build_settings(MINIO_PUBLIC_ENDPOINT="not-a-url")


def test_minio_public_endpoint_is_optional_and_browser_facing() -> None:
    configured = build_settings(MINIO_PUBLIC_ENDPOINT="http://127.0.0.1:19000")

    assert str(configured.MINIO_ENDPOINT).rstrip("/") == "http://minio:9000"
    assert str(configured.MINIO_PUBLIC_ENDPOINT).rstrip("/") == (
        "http://127.0.0.1:19000"
    )


def test_production_rejects_wildcard_cors_and_minio_requires_all_fields() -> None:
    with pytest.raises(ValidationError):
        build_settings(
            ENVIRONMENT="production",
            BACKEND_CORS_ORIGINS=["*"],
        )
    with pytest.raises(ValidationError):
        build_settings(MINIO_ROOT_PASSWORD=None)


def test_settings_representation_redacts_secrets() -> None:
    secret = "settings-secret-that-must-not-appear"
    configured = build_settings(SECRET_KEY=secret)

    assert secret not in repr(configured)
    assert "**********" in repr(configured)
