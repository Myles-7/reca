import pytest

from app.main import app

pytestmark = pytest.mark.no_database


def test_m6_stage1_openapi_exposes_manuscript_vertical_chain() -> None:
    paths = app.openapi()["paths"]
    for path in (
        "/api/v1/projects/{project_id}/manuscripts",
        "/api/v1/projects/{project_id}/manuscript",
        "/api/v1/manuscripts/{manuscript_id}",
        "/api/v1/manuscripts/{manuscript_id}/versions",
        "/api/v1/manuscript-versions/{version_id}",
        "/api/v1/manuscript-versions/{version_id}/download",
        "/api/v1/manuscript-versions/{version_id}/check-runs",
        "/api/v1/manuscript-check-runs/{run_id}",
        "/api/v1/manuscript-check-runs/{run_id}/issues",
        "/api/v1/manuscript-issues/{issue_id}",
        "/api/v1/manuscript-issues/{issue_id}/accept",
        "/api/v1/manuscript-issues/{issue_id}/reject",
    ):
        assert path in paths


def test_m6_stage2_backend_paths_are_enabled() -> None:
    paths = app.openapi()["paths"]
    for path in (
        "/api/v1/projects/{project_id}/manuscript-revision-audits",
        "/api/v1/manuscript-revision-audits/{audit_id}",
        "/api/v1/manuscript-versions/{version_id}/fix-plans",
        "/api/v1/manuscript-fix-plans/{plan_id}",
        "/api/v1/manuscript-fix-plans/{plan_id}/preview",
        "/api/v1/manuscript-fix-plans/{plan_id}/approval-requests",
        "/api/v1/manuscript-fix-plans/{plan_id}/execute",
        "/api/v1/projects/{project_id}/claims",
        "/api/v1/claims/{claim_id}",
        "/api/v1/claims/{claim_id}/confirmation-requests",
    ):
        assert path in paths


def test_m6_responses_are_typed_and_fail_closed_errors_are_documented() -> None:
    document = app.openapi()
    paths = document["paths"]
    expected = {
        (
            "/api/v1/projects/{project_id}/manuscripts",
            "post",
        ): "ManuscriptCreatedEnvelope",
        (
            "/api/v1/projects/{project_id}/manuscript",
            "get",
        ): "ProjectManuscriptDiscoveryEnvelope",
        ("/api/v1/manuscripts/{manuscript_id}", "get"): "ManuscriptEnvelope",
        (
            "/api/v1/manuscripts/{manuscript_id}/versions",
            "get",
        ): "ManuscriptVersionListEnvelope",
        (
            "/api/v1/manuscript-versions/{version_id}/check-runs",
            "post",
        ): "ManuscriptCheckRequestEnvelope",
        ("/api/v1/manuscript-check-runs/{run_id}", "get"): "ManuscriptCheckRunEnvelope",
        ("/api/v1/manuscript-issues/{issue_id}", "get"): "ManuscriptIssueEnvelope",
        (
            "/api/v1/manuscript-fix-plans/{plan_id}",
            "get",
        ): "ManuscriptTransformationEnvelope",
        (
            "/api/v1/manuscript-revision-audits/{audit_id}",
            "get",
        ): "RevisionAuditEnvelope",
        ("/api/v1/claims/{claim_id}", "get"): "ClaimEnvelope",
    }
    for (path, method), schema_name in expected.items():
        operation = paths[path][method]
        success = next(code for code in operation["responses"] if code.startswith("2"))
        schema = operation["responses"][success]["content"]["application/json"][
            "schema"
        ]
        assert schema == {"$ref": f"#/components/schemas/{schema_name}"}
        assert {"404", "409", "422"}.issubset(operation["responses"])


def test_m6_concurrency_and_idempotency_headers_are_in_openapi() -> None:
    paths = app.openapi()["paths"]

    for path, method in (
        ("/api/v1/manuscript-issues/{issue_id}/accept", "post"),
        ("/api/v1/manuscript-issues/{issue_id}/reject", "post"),
        ("/api/v1/manuscript-fix-plans/{plan_id}/preview", "post"),
        ("/api/v1/claims/{claim_id}", "patch"),
    ):
        headers = {item["name"] for item in paths[path][method]["parameters"]}
        assert "If-Match" in headers
        assert "428" in paths[path][method]["responses"]

    for path in (
        "/api/v1/manuscript-versions/{version_id}/check-runs",
        "/api/v1/projects/{project_id}/manuscript-revision-audits",
        "/api/v1/manuscript-versions/{version_id}/fix-plans",
        "/api/v1/manuscript-fix-plans/{plan_id}/approval-requests",
        "/api/v1/manuscript-fix-plans/{plan_id}/execute",
        "/api/v1/projects/{project_id}/claims",
        "/api/v1/claims/{claim_id}/confirmation-requests",
    ):
        headers = {item["name"] for item in paths[path]["post"]["parameters"]}
        assert "Idempotency-Key" in headers


def test_m6_public_schemas_expose_status_actions_hashes_and_degradation() -> None:
    schemas = app.openapi()["components"]["schemas"]
    required_fields = {
        "ManuscriptVersionPublic": {"status", "source_hash", "allowed_actions"},
        "ManuscriptCheckRunPublic": {
            "status",
            "source_hash",
            "degradation",
            "allowed_actions",
        },
        "ManuscriptIssuePublic": {
            "status",
            "locator",
            "finding_hash",
            "auto_fixable",
            "allowed_actions",
        },
        "ManuscriptTransformationPublic": {
            "status",
            "input_artifact_hash",
            "preview_hash",
            "payload_hash",
            "lock_version",
            "allowed_actions",
        },
        "RevisionAuditPublic": {
            "status",
            "before_source_hash",
            "after_source_hash",
            "result_hash",
            "allowed_actions",
        },
        "ClaimPublic": {
            "status",
            "source_location",
            "source_hash",
            "text_hash",
            "lock_version",
            "allowed_actions",
        },
    }
    for schema_name, fields in required_fields.items():
        assert fields.issubset(schemas[schema_name]["properties"])
