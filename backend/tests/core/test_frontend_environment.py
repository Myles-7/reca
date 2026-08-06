import re
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.no_database


def test_frontend_environment_layer_has_an_explicit_public_whitelist() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    source = (repository_root / "frontend/src/shared/environment.ts").read_text(
        encoding="utf-8"
    )

    allowed = {"VITE_API_URL", "VITE_APP_ENV", "VITE_DEMO_MODE"}
    referenced = set(re.findall(r"import\.meta\.env\.(VITE_[A-Z_]+)", source))

    assert referenced == allowed
    for secret_name in (
        "POSTGRES_PASSWORD",
        "SECRET_KEY",
        "MINIO_ROOT_PASSWORD",
        "MODEL_API_KEY",
        "OPENALEX_API_KEY",
    ):
        assert secret_name not in source


def test_environment_template_declares_all_public_variables_without_secrets() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    content = (repository_root / ".env.example").read_text(encoding="utf-8")

    for variable in ("VITE_API_URL", "VITE_APP_ENV", "VITE_DEMO_MODE"):
        assert f"{variable}=" in content


def test_environment_template_covers_required_core_configuration() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    content = (repository_root / ".env.example").read_text(encoding="utf-8")

    required = (
        "ENVIRONMENT",
        "SECRET_KEY",
        "FIRST_SUPERUSER",
        "FIRST_SUPERUSER_PASSWORD",
        "POSTGRES_SERVER",
        "POSTGRES_PORT",
        "POSTGRES_DB",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "VALKEY_URL",
        "MINIO_ENDPOINT",
        "MINIO_ROOT_USER",
        "MINIO_ROOT_PASSWORD",
        "MINIO_BUCKET",
        "GROBID_URL",
        "CELERY_BROKER_URL",
        "CELERY_RESULT_BACKEND",
        "MODEL_API_KEY",
        "OPENALEX_API_KEY",
    )

    for variable in required:
        assert f"{variable}=" in content


def test_api_and_worker_share_the_configured_minio_bucket() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    content = (repository_root / "docker-compose.yml").read_text(encoding="utf-8")
    worker_section = content.split("\n  worker:\n", 1)[1].split("\n  minio:\n", 1)[0]

    assert "MINIO_BUCKET: ${MINIO_BUCKET:-reca}" in worker_section


def test_minio_public_download_port_has_an_edge_network_path() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    compose = yaml.safe_load(
        (repository_root / "docker-compose.yml").read_text(encoding="utf-8")
    )
    minio = compose["services"]["minio"]

    assert set(minio["networks"]) == {"edge", "internal"}
    assert minio["ports"] == ["127.0.0.1:${MINIO_PORT:-9000}:9000"]
