import uuid

import pandas as pd
import pytest

from app.analysis.engine import execute, validate
from app.analysis.schemas import EngineRequest

pytestmark = pytest.mark.no_database


def _request(
    method: str, columns: list[tuple[str, str]], **parameters: object
) -> EngineRequest:
    return EngineRequest.model_validate(
        {
            "method": method,
            "columns": [
                {
                    "column_id": uuid.uuid5(uuid.NAMESPACE_DNS, name),
                    "name": name,
                    "kind": kind,
                }
                for name, kind in columns
            ],
            "missing_data_policy": {"mode": "PAIRWISE_COMPLETE"},
            "parameters": {"confidence_level": 0.95, **parameters},
        }
    )


def test_independent_welch_returns_structured_effect_and_ci() -> None:
    request = _request(
        "INDEPENDENT_TWO_GROUP",
        [("group", "categorical"), ("value", "numeric")],
        independence_confirmed=True,
        variance_mode="WELCH",
    )
    output = execute(
        pd.DataFrame({"group": ["A"] * 3 + ["B"] * 4, "value": [1, 2, 3, 4, 5, 6, 7]}),
        request,
    )
    result = output.results[0].payload
    assert result["mean_difference"] == pytest.approx(-3.5)
    assert result["df"] == pytest.approx(4.959183673469388)
    assert result["p_value"] == pytest.approx(0.01007694334798886)
    assert result["effect_size"]["value"] == pytest.approx(-3.0310889132455348)
    assert result["confidence_interval"]["lower"] < -3.5
    assert result["confidence_interval"]["upper"] < 0


def test_independent_requires_exactly_two_groups() -> None:
    request = _request(
        "INDEPENDENT_TWO_GROUP",
        [("group", "categorical"), ("value", "numeric")],
        independence_confirmed=True,
    )
    with pytest.raises(ValueError, match="exactly two groups"):
        execute(pd.DataFrame({"group": ["A", "B", "C"], "value": [1, 2, 3]}), request)


def test_paired_uses_declared_unique_pair_ids() -> None:
    request = _request(
        "PAIRED_TWO_GROUP",
        [("before", "numeric"), ("after", "numeric"), ("pair", "categorical")],
        pairing_confirmed=True,
        pair_id_column_id=uuid.uuid5(uuid.NAMESPACE_DNS, "pair"),
    )
    output = execute(
        pd.DataFrame(
            {"before": [2, 4, 6], "after": [1, 2, 3], "pair": ["a", "b", "c"]}
        ),
        request,
    )
    payload = output.results[0].payload
    assert payload["pair_n"] == 3
    assert payload["mean_difference"] == pytest.approx(2.0)
    assert payload["statistic"] == pytest.approx(3.464101615137755)
    duplicate = pd.DataFrame({"before": [2, 4], "after": [1, 2], "pair": ["a", "a"]})
    checks = validate(duplicate, request)
    assert any(
        check.check_code == "PAIRING_VALIDITY" and check.blocks_approval
        for check in checks
    )
    with pytest.raises(ValueError, match="unique"):
        execute(duplicate, request)


def test_simple_regression_reads_structured_statsmodels_properties() -> None:
    request = _request("SIMPLE_LINEAR_REGRESSION", [("x", "numeric"), ("y", "numeric")])
    output = execute(
        pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [3, 5, 8, 9, 11]}), request
    )
    payload = output.results[0].payload
    assert payload["intercept"]["coefficient"] == pytest.approx(1.2)
    assert payload["slope"]["coefficient"] == pytest.approx(2.0)
    assert payload["r_squared"] == pytest.approx(0.9803921568627451)
    assert payload["diagnostics"]["maximum_cooks_distance"] is not None


def test_regression_rejects_constant_x() -> None:
    request = _request("SIMPLE_LINEAR_REGRESSION", [("x", "numeric"), ("y", "numeric")])
    with pytest.raises(ValueError, match="non-constant X"):
        execute(pd.DataFrame({"x": [1, 1, 1], "y": [1, 2, 3]}), request)
