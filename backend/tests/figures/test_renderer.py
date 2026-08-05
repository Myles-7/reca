import uuid

import pandas as pd
import pytest

from app.figures import renderer
from app.figures.schemas import FigurePlanCreate

pytestmark = pytest.mark.no_database


def _parameters(kind: str, ids: dict[str, uuid.UUID]) -> object:
    base = {"kind": kind, "title": "Research figure", "dpi": 120}
    payloads = {
        "SCATTER": {**base, "x_column_id": ids["x"], "y_column_id": ids["y"]},
        "GROUP_COMPARISON": {
            **base,
            "group_column_id": ids["group"],
            "value_column_id": ids["y"],
        },
        "HISTOGRAM": {**base, "value_column_id": ids["x"], "bins": 5},
        "BOXPLOT": {
            **base,
            "value_column_id": ids["y"],
            "group_column_id": ids["group"],
        },
        "CORRELATION_MATRIX": {**base, "column_ids": [ids["x"], ids["y"]]},
    }
    return FigurePlanCreate.model_validate(
        {
            "dataset_version_id": uuid.uuid4(),
            "analysis_run_id": uuid.uuid4() if kind == "GROUP_COMPARISON" else None,
            "analysis_result_id": uuid.uuid4() if kind == "GROUP_COMPARISON" else None,
            "chart_type": kind,
            "parameters": payloads[kind],
            "caption": "A deterministic Figure.",
        }
    ).parameters


@pytest.mark.parametrize(
    "kind",
    ["SCATTER", "GROUP_COMPARISON", "HISTOGRAM", "BOXPLOT", "CORRELATION_MATRIX"],
)
def test_five_templates_produce_openable_formats(
    monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    monkeypatch.setattr(renderer, "FONT_FAMILY", "DejaVu Sans")
    ids = {name: uuid.uuid5(uuid.NAMESPACE_DNS, name) for name in ("x", "y", "group")}
    frame = pd.DataFrame(
        {"x": [1, 2, 3, 4], "y": [2, 4, 3, 6], "group": ["A", "A", "B", "B"]}
    )
    result = renderer.render(
        frame=frame,
        parameters=_parameters(kind, ids),  # type: ignore[arg-type]
        column_names={str(value): name for name, value in ids.items()},
        result_payload={
            "groups": [
                {"label": "A", "n": 2, "mean": 3.0},
                {"label": "B", "n": 2, "mean": 4.5},
            ],
            "mean_difference": -1.5,
            "confidence_interval": {
                "lower": -2.2,
                "upper": -0.8,
                "level": 0.95,
            },
        }
        if kind == "GROUP_COMPARISON"
        else None,
    )
    assert result.png.startswith(b"\x89PNG\r\n\x1a\n")
    assert b"<svg" in result.svg[:500]
    assert result.pdf.startswith(b"%PDF")
    assert b"User/model code is never executed" in result.code
    assert result.environment["backend"].lower() == "agg"


def test_approved_font_is_fail_closed_when_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(renderer, "FONT_FAMILY", "RECA Definitely Missing Font")
    with pytest.raises(ValueError, match="Failed to find font"):
        renderer._font()


def test_render_rejects_pixel_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(renderer, "FONT_FAMILY", "DejaVu Sans")
    monkeypatch.setattr(renderer, "MAX_PIXELS", 1)
    ids = {name: uuid.uuid5(uuid.NAMESPACE_DNS, name) for name in ("x", "y", "group")}
    with pytest.raises(ValueError, match="pixel limit"):
        renderer.render(
            frame=pd.DataFrame({"x": [1], "y": [2]}),
            parameters=_parameters("SCATTER", ids),  # type: ignore[arg-type]
            column_names={str(value): name for name, value in ids.items()},
        )
