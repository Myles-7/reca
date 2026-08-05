import json
import uuid
from pathlib import Path

import pandas as pd
import pytest

from app.analysis.engine import execute
from app.analysis.schemas import EngineRequest

pytestmark = pytest.mark.no_database

FIXTURE = Path(__file__).parent / "m5_analysis/v1/p0_must.json"
FULL_FIXTURE = Path(__file__).parent / "m5_analysis/v1/p0_full.json"


def _request(method: str, names: list[tuple[str, str]]) -> EngineRequest:
    return EngineRequest.model_validate(
        {
            "method": method,
            "columns": [
                {
                    "column_id": uuid.uuid5(uuid.NAMESPACE_DNS, name),
                    "name": name,
                    "kind": kind,
                }
                for name, kind in names
            ],
            "missing_data_policy": {"mode": "PAIRWISE_COMPLETE"},
            "parameters": {
                "confidence_level": 0.95,
                "assumption_confirmations": ["LINEARITY"],
            },
        }
    )


def test_p0_must_golden_fixture_is_independently_asserted() -> None:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    numeric = fixture["descriptive_numeric"]
    categorical = fixture["descriptive_categorical"]
    output = execute(
        pd.DataFrame(
            {
                "numeric": numeric["values"],
                "category": categorical["values"] + [None, None],
            }
        ),
        _request(
            "DESCRIPTIVE_STATISTICS",
            [("numeric", "numeric"), ("category", "categorical")],
        ),
    )
    observed = output.results[0].payload
    for key in ("n", "missing_n", "mean", "standard_deviation", "q1", "median", "q3"):
        assert observed[key] == pytest.approx(numeric[key])

    for case, method in (
        ("pearson_positive", "PEARSON_CORRELATION"),
        ("pearson_negative", "PEARSON_CORRELATION"),
        ("spearman_ties", "SPEARMAN_CORRELATION"),
    ):
        expected = fixture[case]
        result = execute(
            pd.DataFrame({"x": expected["x"], "y": expected["y"]}),
            _request(method, [("x", "numeric"), ("y", "numeric")]),
        )
        assert result.results[0].payload["coefficient"] == pytest.approx(
            expected["coefficient"], abs=1e-12
        )
        assert result.effective_n == expected["effective_n"]


def test_p0_full_golden_fixture_is_independently_asserted() -> None:
    fixture = json.loads(FULL_FIXTURE.read_text(encoding="utf-8"))
    tolerance = fixture["tolerance"]
    independent = fixture["independent_welch"]
    independent_request = _request(
        "INDEPENDENT_TWO_GROUP", [("group", "categorical"), ("value", "numeric")]
    )
    independent_request.parameters.independence_confirmed = True
    independent_result = (
        execute(
            pd.DataFrame(
                {"group": independent["group"], "value": independent["value"]}
            ),
            independent_request,
        )
        .results[0]
        .payload
    )
    for key in ("mean_difference", "df", "p_value"):
        assert independent_result[key] == pytest.approx(
            independent[key], abs=tolerance["absolute"], rel=tolerance["relative"]
        )

    paired = fixture["paired"]
    pair_id = uuid.uuid5(uuid.NAMESPACE_DNS, "pair")
    paired_request = _request(
        "PAIRED_TWO_GROUP",
        [("before", "numeric"), ("after", "numeric"), ("pair", "categorical")],
    )
    paired_request.parameters.pairing_confirmed = True
    paired_request.parameters.pair_id_column_id = pair_id
    paired_result = (
        execute(
            pd.DataFrame(
                {
                    "before": paired["before"],
                    "after": paired["after"],
                    "pair": paired["pair"],
                }
            ),
            paired_request,
        )
        .results[0]
        .payload
    )
    assert paired_result["mean_difference"] == pytest.approx(paired["mean_difference"])
    assert paired_result["statistic"] == pytest.approx(paired["statistic"])

    regression = fixture["regression"]
    regression_result = (
        execute(
            pd.DataFrame({"x": regression["x"], "y": regression["y"]}),
            _request("SIMPLE_LINEAR_REGRESSION", [("x", "numeric"), ("y", "numeric")]),
        )
        .results[0]
        .payload
    )
    assert regression_result["intercept"]["coefficient"] == pytest.approx(
        regression["intercept"]
    )
    assert regression_result["slope"]["coefficient"] == pytest.approx(
        regression["slope"]
    )
    assert regression_result["r_squared"] == pytest.approx(regression["r_squared"])
