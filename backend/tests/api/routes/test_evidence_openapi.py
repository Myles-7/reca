from types import SimpleNamespace

import pytest
from pydantic import AnyHttpUrl, SecretStr

from app.agents.service import ModelExecutionMode
from app.api.errors import ContractError
from app.api.routes import evidence as evidence_routes
from app.main import app

pytestmark = pytest.mark.no_database


def test_production_provider_identity_is_configured_or_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(ContractError) as unconfigured:
        evidence_routes._configured_extraction_identity()
    assert unconfigured.value.code == "MODEL_PROVIDER_UNCONFIGURED"

    monkeypatch.setattr(
        evidence_routes,
        "settings",
        SimpleNamespace(
            model_status="CONFIGURED",
            MODEL_BASE_URL=AnyHttpUrl("https://model.example/v1"),
            MODEL_API_KEY=SecretStr("provider-secret"),
            MODEL_NAME="reca-structured-model",
        ),
    )
    extraction_identity = evidence_routes._configured_extraction_identity()
    analysis_identity = evidence_routes._configured_analysis_identity()
    assert extraction_identity.mode == ModelExecutionMode.LIVE
    assert analysis_identity.mode == ModelExecutionMode.LIVE
    assert extraction_identity.model_name == analysis_identity.model_name


def test_m3_stage3_openapi_paths_and_write_headers() -> None:
    schema = app.openapi()
    paths = schema["paths"]
    expected = {
        "/api/v1/documents/{document_id}/literature-extractions",
        "/api/v1/literature-extractions/{extraction_id}",
        "/api/v1/literature-extraction-fields/{field_id}",
        "/api/v1/documents/{document_id}/evidence-spans",
        "/api/v1/evidence-spans/{evidence_span_id}",
        "/api/v1/evidence-spans/{evidence_span_id}/verification-records",
        "/api/v1/literature/{literature_id}/decisions",
        "/api/v1/projects/{project_id}/literature-matrix",
        "/api/v1/projects/{project_id}/evidence-search",
        "/api/v1/projects/{project_id}/evidence-set-summaries",
        "/api/v1/evidence-set-summaries/{summary_id}",
        "/api/v1/projects/{project_id}/topic-generation-runs",
        "/api/v1/topic-generation-runs/{run_id}",
    }

    assert expected <= paths.keys()
    assert not any("literature-records" in path for path in paths)
    assert not any(path.endswith("/confirm") for path in paths if "extraction" in path)

    writes = [
        ("/api/v1/documents/{document_id}/literature-extractions", "post"),
        ("/api/v1/literature-extraction-fields/{field_id}", "patch"),
        ("/api/v1/documents/{document_id}/evidence-spans", "post"),
        (
            "/api/v1/evidence-spans/{evidence_span_id}/verification-records",
            "post",
        ),
        ("/api/v1/literature/{literature_id}/decisions", "post"),
        ("/api/v1/projects/{project_id}/evidence-set-summaries", "post"),
        ("/api/v1/projects/{project_id}/topic-generation-runs", "post"),
    ]
    for path, method in writes:
        headers = {
            parameter["name"]
            for parameter in paths[path][method]["parameters"]
            if parameter["in"] == "header"
        }
        assert "Idempotency-Key" in headers

    patch_headers = {
        parameter["name"]
        for parameter in paths["/api/v1/literature-extraction-fields/{field_id}"][
            "patch"
        ]["parameters"]
        if parameter["in"] == "header"
    }
    assert "If-Match" in patch_headers

    candidate_count = schema["components"]["schemas"]["TopicGenerationCreate"][
        "properties"
    ]["candidate_count"]
    assert candidate_count["minimum"] == candidate_count["maximum"] == 3
    for path in (
        "/api/v1/documents/{document_id}/literature-extractions",
        "/api/v1/projects/{project_id}/evidence-set-summaries",
        "/api/v1/projects/{project_id}/topic-generation-runs",
    ):
        assert "201" in paths[path]["post"]["responses"]
        assert "202" not in paths[path]["post"]["responses"]
    retrieval_modes = schema["components"]["schemas"]["EvidenceRetrievalMode"]["enum"]
    assert retrieval_modes == ["KEYWORD", "HYBRID"]
