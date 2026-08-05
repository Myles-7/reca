import uuid
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.analysis.schemas import AnalysisPlanCreate
from app.figures.schemas import FigurePlanCreate
from app.models import AnalysisPlanStatus, AnalysisRunStatus, SQLModel

pytestmark = pytest.mark.no_database


def _payload() -> dict[str, object]:
    return {
        "research_question_version_id": uuid.uuid4(),
        "dataset_version_id": uuid.uuid4(),
        "analysis_goal": "CORRELATION",
        "method": "PEARSON_CORRELATION",
        "dependent_variable_ids": [uuid.uuid4()],
        "independent_variable_ids": [uuid.uuid4()],
        "control_variable_ids": [],
        "missing_data_policy": {"mode": "PAIRWISE_COMPLETE"},
        "parameters": {"confidence_level": 0.95},
    }


def test_analysis_plan_schema_rejects_code_and_free_form_filters() -> None:
    payload = _payload()
    payload["sample_filter"] = {"operator": "PYTHON", "expression": "__import__('os')"}
    with pytest.raises(ValidationError):
        AnalysisPlanCreate.model_validate(payload)
    payload = _payload()
    payload["function_name"] = "scipy.stats.pearsonr"
    with pytest.raises(ValidationError):
        AnalysisPlanCreate.model_validate(payload)


def test_analysis_plan_schema_requires_method_shape() -> None:
    payload = _payload()
    payload["independent_variable_ids"] = []
    with pytest.raises(ValidationError, match="exactly one X and one Y"):
        AnalysisPlanCreate.model_validate(payload)


def test_analysis_models_and_state_separation_are_registered() -> None:
    assert {
        "analysis_plans",
        "analysis_assumption_checks",
        "analysis_runs",
        "analysis_results",
        "code_artifacts",
    }.issubset(SQLModel.metadata.tables)
    assert "RUNNING" not in {status.value for status in AnalysisPlanStatus}
    assert AnalysisRunStatus.RUNNING.value == "RUNNING"


def test_m5_migration_freezes_scope_hash_and_result_immutability() -> None:
    migration = (
        Path(__file__).resolve().parents[2]
        / "app/alembic/versions/0015_m5_analysis_figures.py"
    ).read_text(encoding="utf-8")
    assert 'down_revision: str | None = "0014_m4_data_quality"' in migration
    assert migration.count("op.create_table(") == 5
    for table in (
        "analysis_plans",
        "analysis_assumption_checks",
        "analysis_runs",
        "analysis_results",
        "code_artifacts",
    ):
        assert f'"{table}"' in migration
    for constraint in (
        "fk_analysis_plans_dataset_project",
        "fk_analysis_runs_approval_project",
        "uq_analysis_runs_idempotency",
        "trg_analysis_results_immutable",
    ):
        assert constraint in migration


def test_figure_schema_rejects_executable_or_mismatched_parameters() -> None:
    payload = {
        "dataset_version_id": uuid.uuid4(),
        "chart_type": "SCATTER",
        "parameters": {
            "kind": "SCATTER",
            "x_column_id": uuid.uuid4(),
            "y_column_id": uuid.uuid4(),
            "python": "__import__('os')",
        },
        "caption": "Confirmed scatter.",
    }
    with pytest.raises(ValidationError):
        FigurePlanCreate.model_validate(payload)
    payload["parameters"] = {
        "kind": "HISTOGRAM",
        "value_column_id": uuid.uuid4(),
    }
    with pytest.raises(ValidationError, match="chart_type"):
        FigurePlanCreate.model_validate(payload)


def test_0016_adds_figures_without_rewriting_0015() -> None:
    migration = (
        Path(__file__).resolve().parents[2] / "app/alembic/versions/0016_m5_figures.py"
    ).read_text(encoding="utf-8")
    assert 'down_revision: str | None = "0015_m5_analysis"' in migration
    assert migration.count("op.create_table(") == 4
    for table in (
        "figure_plans",
        "figure_render_runs",
        "figures",
        "figure_validation_issues",
    ):
        assert f'"{table}"' in migration
    assert "ck_code_artifacts_exactly_one_owner" in migration
    assert "SIMPLE_LINEAR_REGRESSION" in migration
