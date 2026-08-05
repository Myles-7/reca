from __future__ import annotations

import hashlib
import io
import platform
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg", force=True)

import matplotlib.font_manager as font_manager
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd  # type: ignore[import-untyped]
from matplotlib.figure import Figure

from app.figures.schemas import (
    BoxplotParameters,
    CorrelationMatrixParameters,
    FigureParameters,
    GroupComparisonParameters,
    HistogramParameters,
    ScatterParameters,
)

STYLE_VERSION = "reca-figure-style/1.0.0"
TEMPLATE_VERSION = "reca-figure-python/1.0.0"
FONT_FAMILY = "Noto Sans CJK SC"
MAX_PIXELS = 18_000_000


@dataclass(frozen=True)
class RenderedFigure:
    png: bytes
    svg: bytes
    pdf: bytes
    code: bytes
    environment: dict[str, Any]


def _font() -> tuple[str, str]:
    path = font_manager.findfont(FONT_FAMILY, fallback_to_default=False)
    return path, hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _numeric(frame: pd.DataFrame, name: str) -> pd.Series:
    values = pd.to_numeric(frame[name], errors="coerce")
    return values[np.isfinite(values.to_numpy(dtype=float))]


def _label(label: str | None, unit: str | None, fallback: str) -> str:
    base = label or fallback
    return f"{base} ({unit})" if unit else base


def _draw(
    frame: pd.DataFrame,
    parameters: FigureParameters,
    column_names: dict[str, str],
    result_payload: dict[str, Any] | None,
) -> Figure:
    figure, axis = plt.subplots(
        figsize=(parameters.width_inches, parameters.height_inches),
        constrained_layout=True,
    )
    if isinstance(parameters, ScatterParameters):
        x_name = column_names[str(parameters.x_column_id)]
        y_name = column_names[str(parameters.y_column_id)]
        scoped = frame[[x_name, y_name]].apply(pd.to_numeric, errors="coerce").dropna()
        axis.scatter(scoped[x_name], scoped[y_name], s=26, alpha=0.8)
        axis.set_xlabel(_label(parameters.x_label, parameters.x_unit, x_name))
        axis.set_ylabel(_label(parameters.y_label, parameters.y_unit, y_name))
    elif isinstance(parameters, HistogramParameters):
        name = column_names[str(parameters.value_column_id)]
        axis.hist(_numeric(frame, name), bins=parameters.bins, edgecolor="white")
        axis.set_xlabel(_label(parameters.x_label, parameters.x_unit, name))
        axis.set_ylabel(parameters.y_label or "Count")
    elif isinstance(parameters, BoxplotParameters):
        value_name = column_names[str(parameters.value_column_id)]
        if parameters.group_column_id is None:
            axis.boxplot([_numeric(frame, value_name)], tick_labels=[value_name])
        else:
            group_name = column_names[str(parameters.group_column_id)]
            scoped = frame[[group_name, value_name]].dropna()
            labels = sorted(scoped[group_name].astype(str).unique())
            values = [
                pd.to_numeric(
                    scoped.loc[scoped[group_name].astype(str) == label, value_name],
                    errors="coerce",
                ).dropna()
                for label in labels
            ]
            axis.boxplot(values, tick_labels=labels)
            axis.set_xlabel(parameters.x_label or group_name)
        axis.set_ylabel(_label(parameters.y_label, parameters.y_unit, value_name))
    elif isinstance(parameters, GroupComparisonParameters):
        group_name = column_names[str(parameters.group_column_id)]
        value_name = column_names[str(parameters.value_column_id)]
        if result_payload is None:
            raise ValueError("Group comparison requires an immutable AnalysisResult")
        groups = result_payload.get("groups")
        if not isinstance(groups, list) or len(groups) != 2:
            raise ValueError("AnalysisResult has no valid group summary")
        labels = [str(item["label"]) for item in groups]
        means = [float(item["mean"]) for item in groups]
        axis.bar(labels, means)
        axis.set_xlabel(parameters.x_label or group_name)
        axis.set_ylabel(_label(parameters.y_label, parameters.y_unit, value_name))
        axis.text(
            0.99,
            0.98,
            f"N = {sum(int(item['n']) for item in groups)}",
            transform=axis.transAxes,
            ha="right",
            va="top",
        )
        interval = result_payload.get("confidence_interval")
        difference = result_payload.get("mean_difference")
        if parameters.error_bar == "CI_FROM_RESULT":
            if not isinstance(difference, int | float) or not isinstance(
                interval, dict
            ):
                raise ValueError(
                    "AnalysisResult has no valid comparison confidence interval"
                )
            if not all(
                isinstance(interval.get(key), int | float)
                for key in ("lower", "upper", "level")
            ):
                raise ValueError(
                    "AnalysisResult has no valid comparison confidence interval"
                )
            axis.text(
                0.01,
                0.98,
                f"Difference = {float(difference):.4g}; "
                f"{float(interval['level']) * 100:.0f}% CI "
                f"[{float(interval['lower']):.4g}, {float(interval['upper']):.4g}]",
                transform=axis.transAxes,
                ha="left",
                va="top",
            )
    else:
        assert isinstance(parameters, CorrelationMatrixParameters)
        names = [column_names[str(column_id)] for column_id in parameters.column_ids]
        matrix = (
            frame[names].apply(pd.to_numeric, errors="coerce").corr(method="pearson")
        )
        image = axis.imshow(matrix.to_numpy(), vmin=-1, vmax=1, cmap="coolwarm")
        axis.set_xticks(range(len(names)), names, rotation=45, ha="right")
        axis.set_yticks(range(len(names)), names)
        figure.colorbar(image, ax=axis, label="Pearson r")
    if parameters.title:
        axis.set_title(parameters.title)
    axis.grid(True, alpha=0.18)
    return figure


def render(
    *,
    frame: pd.DataFrame,
    parameters: FigureParameters,
    column_names: dict[str, str],
    result_payload: dict[str, Any] | None = None,
) -> RenderedFigure:
    if (
        parameters.width_inches * parameters.height_inches * parameters.dpi**2
        > MAX_PIXELS
    ):
        raise ValueError("Requested Figure exceeds the pixel limit")
    font_path, font_hash = _font()
    rc: Any = {
        "font.family": FONT_FAMILY,
        "svg.hashsalt": "reca-m5-v1",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
    }
    buffers = {name: io.BytesIO() for name in ("png", "svg", "pdf")}
    with matplotlib.rc_context(rc):
        figure = _draw(frame, parameters, column_names, result_payload)
        try:
            figure.savefig(
                buffers["png"],
                format="png",
                dpi=parameters.dpi,
                metadata={"Software": "RECA FigureRenderer"},
            )
            figure.savefig(
                buffers["svg"],
                format="svg",
                metadata={"Date": None, "Creator": "RECA FigureRenderer"},
            )
            figure.savefig(
                buffers["pdf"],
                format="pdf",
                metadata={"Creator": "RECA FigureRenderer", "CreationDate": None},
            )
        finally:
            plt.close(figure)
    code = (
        "# Generated by RECA. User/model code is never executed.\n"
        f"TEMPLATE_VERSION = {TEMPLATE_VERSION!r}\n"
        f"CHART_TYPE = {parameters.kind!r}\n"
        "# Rendering is performed by app.figures.renderer from a validated FigurePlan.\n"
    ).encode()
    environment = {
        "python": platform.python_version(),
        "matplotlib": matplotlib.__version__,
        "numpy": np.__version__,
        "backend": matplotlib.get_backend(),
        "font_family": FONT_FAMILY,
        "font_path": font_path,
        "font_hash": font_hash,
        "style_version": STYLE_VERSION,
        "template_version": TEMPLATE_VERSION,
    }
    return RenderedFigure(
        png=buffers["png"].getvalue(),
        svg=buffers["svg"].getvalue(),
        pdf=buffers["pdf"].getvalue(),
        code=code,
        environment=environment,
    )
