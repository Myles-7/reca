import uuid

import pandas as pd
import pytest

from app.analysis.engine import execute, validate
from app.analysis.schemas import EngineColumn, EngineRequest
from app.models import AnalysisMethod

pytestmark = pytest.mark.no_database


def _request(
    method: AnalysisMethod, *, kinds: tuple[str, ...] = ("numeric", "numeric")
) -> EngineRequest:
    columns = [
        EngineColumn(column_id=uuid.uuid4(), name=name, kind=kind)  # type: ignore[arg-type]
        for name, kind in zip(("x", "y"), kinds, strict=True)
    ]
    return EngineRequest.model_validate(
        {
            "method": method,
            "columns": columns,
            "missing_data_policy": {"mode": "PAIRWISE_COMPLETE"},
            "parameters": {
                "confidence_level": 0.95,
                "assumption_confirmations": ["LINEARITY"],
            },
        }
    )


def test_numeric_and_categorical_descriptive_statistics_are_stable() -> None:
    request = _request(
        AnalysisMethod.DESCRIPTIVE_STATISTICS,
        kinds=("numeric", "categorical"),
    )
    output = execute(
        pd.DataFrame(
            {"x": [1.0, 2.0, 3.0, 4.0, 5.0, None], "y": ["A", "B", "A", None, "B", "A"]}
        ),
        request,
    )
    numeric = output.results[0].payload
    categorical = output.results[1].payload
    assert numeric["n"] == 5
    assert numeric["missing_n"] == 1
    assert numeric["standard_deviation"] == pytest.approx(1.5811388300841898)
    assert (numeric["q1"], numeric["median"], numeric["q3"]) == (2.0, 3.0, 4.0)
    assert categorical["n"] == 5
    assert sum(
        item["proportion"] for item in categorical["categories"]
    ) == pytest.approx(1.0)


def test_complete_case_descriptive_uses_one_shared_sample() -> None:
    request = _request(AnalysisMethod.DESCRIPTIVE_STATISTICS)
    request = EngineRequest.model_validate(
        {
            **request.model_dump(mode="json"),
            "missing_data_policy": {"mode": "COMPLETE_CASE"},
        }
    )
    output = execute(
        pd.DataFrame({"x": [1.0, 2.0, None], "y": [10.0, None, 30.0]}), request
    )
    assert [result.payload["n"] for result in output.results] == [1, 1]


@pytest.mark.parametrize(
    ("method", "y", "expected"),
    [
        (AnalysisMethod.PEARSON_CORRELATION, [2, 4, 6, 8, 10], 1.0),
        (AnalysisMethod.PEARSON_CORRELATION, [10, 8, 6, 4, 2], -1.0),
        (AnalysisMethod.SPEARMAN_CORRELATION, [10, 20, 20, 30, 40], 1.0),
    ],
)
def test_correlation_golden_values(
    method: AnalysisMethod, y: list[int], expected: float
) -> None:
    x = (
        [1, 2, 2, 3, 4]
        if method == AnalysisMethod.SPEARMAN_CORRELATION
        else [1, 2, 3, 4, 5]
    )
    output = execute(pd.DataFrame({"x": x, "y": y}), _request(method))
    payload = output.results[0].payload
    assert payload["coefficient"] == pytest.approx(expected, abs=1e-12)
    assert payload["effective_n"] == 5
    assert "CORRELATION_DOES_NOT_SUPPORT_CAUSAL_INFERENCE" in output.warnings


def test_pairwise_missing_and_pearson_ci() -> None:
    output = execute(
        pd.DataFrame({"x": [1.0, 2.0, None, 4.0, 5.0], "y": [1.0, 2.0, 3.0, 4.0, 5.0]}),
        _request(AnalysisMethod.PEARSON_CORRELATION),
    )
    payload = output.results[0].payload
    assert payload["effective_n"] == 4
    assert payload["missing_n"] == 1
    assert payload["confidence_interval"]["lower"] is not None
    assert payload["confidence_interval"]["upper"] is not None


def test_constant_and_small_sample_fail_closed() -> None:
    request = _request(AnalysisMethod.PEARSON_CORRELATION)
    checks = validate(pd.DataFrame({"x": [1, 1, 1], "y": [1, 2, 3]}), request)
    assert any(
        check.check_code == "CONSTANT"
        and check.status == "FAILED"
        and check.blocks_approval
        for check in checks
    )
    with pytest.raises(ValueError, match="blocking failure"):
        execute(pd.DataFrame({"x": [1, 1, 1], "y": [1, 2, 3]}), request)
    with pytest.raises(ValueError, match="blocking failure"):
        execute(pd.DataFrame({"x": [1, None], "y": [2, 3]}), request)


def test_unconfirmed_pearson_linearity_blocks_execution() -> None:
    request = _request(AnalysisMethod.PEARSON_CORRELATION)
    request = EngineRequest.model_validate(
        {
            **request.model_dump(mode="json"),
            "parameters": {"confidence_level": 0.95},
        }
    )
    checks = validate(pd.DataFrame({"x": [1, 2, 3], "y": [2, 4, 6]}), request)
    assert any(
        check.check_code == "LINEARITY"
        and check.status == "REQUIRES_USER_CONFIRMATION"
        and check.blocks_approval
        for check in checks
    )
    with pytest.raises(ValueError, match="blocking failure"):
        execute(pd.DataFrame({"x": [1, 2, 3], "y": [2, 4, 6]}), request)


def test_spearman_differs_from_pearson_for_monotonic_nonlinear_data() -> None:
    frame = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [1, 4, 9, 16, 25]})
    pearson = (
        execute(frame, _request(AnalysisMethod.PEARSON_CORRELATION))
        .results[0]
        .payload["coefficient"]
    )
    spearman = (
        execute(frame, _request(AnalysisMethod.SPEARMAN_CORRELATION))
        .results[0]
        .payload["coefficient"]
    )
    assert spearman == pytest.approx(1.0)
    assert pearson < spearman
