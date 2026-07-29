from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Awaitable, Callable
from typing import cast

from fastapi import Request
from fastapi.testclient import TestClient
import pytest

from app.api.routes.health import health_service
from app.api.schemas.health import DependencyCheck, DependencyStatus
from app.core.config import settings
from app.core.observability import JsonFormatter
from app.main import app, unhandled_exception_handler


def healthy(name: str) -> Callable[[], Awaitable[DependencyCheck]]:
    async def probe() -> DependencyCheck:
        return DependencyCheck(
            name=name, status=DependencyStatus.HEALTHY, detail="available"
        )

    return probe


def unavailable(name: str) -> Callable[[], Awaitable[DependencyCheck]]:
    async def probe() -> DependencyCheck:
        return DependencyCheck(
            name=name, status=DependencyStatus.UNAVAILABLE, detail=f"{name} is unavailable"
        )

    return probe


def configure_healthy_core(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("postgres", "pgvector", "valkey", "minio"):
        monkeypatch.setattr(health_service.probe, name, healthy(name))


def test_live_is_process_only_and_does_not_probe_dependencies(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def should_not_run() -> list[DependencyCheck]:
        raise AssertionError("live must not inspect dependencies")

    monkeypatch.setattr(health_service, "core_dependencies", should_not_run)

    response = client.get("/api/v1/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "HEALTHY", "service": "api"}


@pytest.mark.parametrize("failed_dependency", ["postgres", "pgvector", "valkey", "minio"])
def test_ready_returns_503_when_a_core_dependency_is_unavailable(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, failed_dependency: str
) -> None:
    configure_healthy_core(monkeypatch)
    monkeypatch.setattr(health_service.probe, failed_dependency, unavailable(failed_dependency))

    response = client.get("/api/v1/health/ready")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "UNAVAILABLE"
    failed = next(item for item in body["dependencies"] if item["name"] == failed_dependency)
    assert failed["status"] == "UNAVAILABLE"
    assert settings.POSTGRES_PASSWORD.get_secret_value() not in response.text


def test_dependencies_reports_degraded_grobid_and_unconfigured_providers(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    configure_healthy_core(monkeypatch)

    async def degraded_grobid() -> DependencyCheck:
        return DependencyCheck(
            name="grobid", status=DependencyStatus.DEGRADED, detail="grobid is unavailable"
        )

    monkeypatch.setattr(health_service.probe, "grobid", degraded_grobid)
    monkeypatch.setattr(settings, "MODEL_API_KEY", None)
    monkeypatch.setattr(settings, "OPENALEX_API_KEY", None)

    response = client.get("/api/v1/health/dependencies")

    statuses = {item["name"]: item["status"] for item in response.json()["dependencies"]}
    assert statuses["api"] == "HEALTHY"
    assert statuses["grobid"] == "DEGRADED"
    assert statuses["model"] == "UNCONFIGURED"
    assert statuses["openalex"] == "UNCONFIGURED"


def test_request_id_is_generated_forwarded_and_sanitized(client: TestClient) -> None:
    generated = client.get("/api/v1/health/live")
    forwarded = client.get("/api/v1/health/live", headers={"X-Request-ID": "trace-123"})
    oversized = client.get("/api/v1/health/live", headers={"X-Request-ID": "x" * 65})
    illegal = client.get("/api/v1/health/live", headers={"X-Request-ID": "invalid space"})

    assert len(generated.headers["X-Request-ID"]) == 32
    assert forwarded.headers["X-Request-ID"] == "trace-123"
    assert oversized.headers["X-Request-ID"] != "x" * 65
    assert illegal.headers["X-Request-ID"] != "invalid space"


def test_standard_errors_are_stable_and_secret_free(client: TestClient) -> None:
    not_found = client.get("/api/v1/missing")
    method_not_allowed = client.post("/api/v1/health/live")
    validation = client.post("/api/v1/login/access-token", data={})

    for response, code in (
        (not_found, "not_found"),
        (method_not_allowed, "method_not_allowed"),
        (validation, "validation_error"),
    ):
        assert response.status_code in {404, 405, 422}
        assert response.json()["error"]["code"] == code
        assert response.headers["X-Request-ID"] == response.json()["request_id"]
        assert "Traceback" not in response.text
        assert settings.secret_key_value not in response.text


def test_unhandled_errors_do_not_expose_exception_content() -> None:
    response = asyncio.run(
        unhandled_exception_handler(cast(Request, None), RuntimeError("secret-value"))
    )

    assert response.status_code == 500
    assert b"secret-value" not in response.body
    assert b"Traceback" not in response.body


def test_structured_logs_include_duration_and_omit_sensitive_request_values() -> None:
    record = logging.LogRecord("reca.api", logging.INFO, __file__, 1, "request.completed", (), None)
    record.request_id = "trace-123"
    record.method = "GET"
    record.path = "/api/v1/health/live"
    record.status_code = 200
    record.duration_ms = 1.25

    payload = json.loads(JsonFormatter().format(record))

    assert payload["request_id"] == "trace-123"
    assert payload["duration_ms"] == 1.25
    assert "authorization" not in json.dumps(payload).lower()
    assert settings.secret_key_value not in json.dumps(payload)


def test_openapi_health_schemas_have_unique_operation_ids_and_no_secrets() -> None:
    schema = app.openapi()
    operation_ids = [
        operation["operationId"]
        for path in schema["paths"].values()
        for operation in path.values()
        if isinstance(operation, dict) and "operationId" in operation
    ]

    assert len(operation_ids) == len(set(operation_ids))
    assert "/api/v1/health/live" in schema["paths"]
    assert settings.secret_key_value not in json.dumps(schema)
