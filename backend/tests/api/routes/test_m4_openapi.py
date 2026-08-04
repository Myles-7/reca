from typing import get_type_hints

from starlette.responses import Response

from app.api.routes import cleaning, data_quality, datasets
from app.main import app


def test_m4_success_responses_are_explicit_and_reads_are_published() -> None:
    schema = app.openapi()
    expected = {
        ("/api/v1/projects/{project_id}/datasets", "post", "201"),
        ("/api/v1/projects/{project_id}/datasets", "get", "200"),
        ("/api/v1/datasets/{dataset_id}", "get", "200"),
        ("/api/v1/datasets/{dataset_id}/versions", "get", "200"),
        ("/api/v1/dataset-versions/{version_id}", "get", "200"),
        ("/api/v1/dataset-versions/{version_id}/preview", "get", "200"),
        ("/api/v1/dataset-versions/{version_id}/quality-runs", "post", "202"),
        ("/api/v1/data-quality-runs/{run_id}", "get", "200"),
        ("/api/v1/data-quality-runs/{run_id}/issues", "get", "200"),
        ("/api/v1/dataset-versions/{version_id}/cleaning-plans", "post", "201"),
        ("/api/v1/cleaning-plans/{plan_id}", "get", "200"),
        ("/api/v1/cleaning-plans/{plan_id}/preview", "post", "200"),
        ("/api/v1/cleaning-plans/{plan_id}/approval-requests", "post", "201"),
        ("/api/v1/cleaning-plans/{plan_id}/execute", "post", "202"),
        ("/api/v1/data-transformations/{transformation_id}", "get", "200"),
        ("/api/v1/datasets/{dataset_id}/version-comparison", "get", "200"),
    }
    for path, method, status in expected:
        response = schema["paths"][path][method]["responses"][status]
        response_schema = response["content"]["application/json"]["schema"]
        assert response_schema.get("$ref", "").startswith("#/components/schemas/")

    generated = schema["components"]["schemas"]
    assert "M4Envelope_list_DatasetVersionPublic__" in generated
    assert "M4Envelope_DataTransformationPublic_" in generated
    transformation = generated["DataTransformationPublic"]
    assert "log_artifact_id" in transformation["required"]


def test_m4_response_models_are_not_bypassed_by_direct_responses() -> None:
    command_endpoints = (
        datasets.upload_dataset,
        datasets.invalidate_dataset_version,
        datasets.select_worksheet,
        data_quality.request_quality_run,
        data_quality.acknowledge_quality_issue,
        data_quality.ignore_quality_issue,
        cleaning.create_cleaning_plan,
        cleaning.preview_cleaning_plan,
        cleaning.request_cleaning_plan_approval,
        cleaning.execute_cleaning_plan,
        cleaning.suggest_cleaning_plan,
    )
    for endpoint in command_endpoints:
        return_type = get_type_hints(endpoint).get("return")
        assert not (
            isinstance(return_type, type) and issubclass(return_type, Response)
        ), f"{endpoint.__name__} bypasses response_model validation"
