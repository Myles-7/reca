import pytest

from app.main import app
from app.models import JobTaskType
from app.workers.jobs import _handlers

pytestmark = pytest.mark.no_database


def test_analysis_worker_handler_is_registered() -> None:
    assert JobTaskType.ANALYSIS_RUN in _handlers
    assert JobTaskType.FIGURE_RENDER in _handlers


def test_analysis_contract_paths_are_registered() -> None:
    paths = set(app.openapi()["paths"])
    assert {
        "/api/v1/projects/{project_id}/analysis-plans",
        "/api/v1/analysis-plans/{plan_id}",
        "/api/v1/analysis-plans/{plan_id}/validate",
        "/api/v1/analysis-plans/{plan_id}/approval-requests",
        "/api/v1/analysis-plans/{plan_id}/runs",
        "/api/v1/analysis-runs/{run_id}",
        "/api/v1/analysis-runs/{run_id}/results",
        "/api/v1/analysis-runs/{run_id}/invalidate",
    }.issubset(paths)
    assert {
        "/api/v1/projects/{project_id}/figure-plans",
        "/api/v1/figure-plans/{plan_id}",
        "/api/v1/projects/{project_id}/figure-recommendations",
        "/api/v1/figure-plans/{plan_id}/render-runs",
        "/api/v1/figure-render-runs/{run_id}",
        "/api/v1/figures/{figure_id}",
        "/api/v1/figures/{figure_id}/validation-issues",
        "/api/v1/figures/{figure_id}/approval-requests",
        "/api/v1/figures/{figure_id}/downloads/{format_name}",
    }.issubset(paths)
