from __future__ import annotations

import uuid
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models import FigureChartType


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RenderStyle(StrictModel):
    width_inches: float = Field(default=7.0, ge=3.0, le=12.0)
    height_inches: float = Field(default=4.5, ge=2.5, le=10.0)
    dpi: int = Field(default=144, ge=72, le=300)
    title: str | None = Field(default=None, max_length=200)
    x_label: str | None = Field(default=None, max_length=200)
    y_label: str | None = Field(default=None, max_length=200)
    x_unit: str | None = Field(default=None, max_length=80)
    y_unit: str | None = Field(default=None, max_length=80)


class ScatterParameters(RenderStyle):
    kind: Literal["SCATTER"] = "SCATTER"
    x_column_id: uuid.UUID
    y_column_id: uuid.UUID


class GroupComparisonParameters(RenderStyle):
    kind: Literal["GROUP_COMPARISON"] = "GROUP_COMPARISON"
    group_column_id: uuid.UUID
    value_column_id: uuid.UUID
    error_bar: Literal["CI_FROM_RESULT", "NONE"] = "CI_FROM_RESULT"


class HistogramParameters(RenderStyle):
    kind: Literal["HISTOGRAM"] = "HISTOGRAM"
    value_column_id: uuid.UUID
    bins: int = Field(default=20, ge=5, le=100)


class BoxplotParameters(RenderStyle):
    kind: Literal["BOXPLOT"] = "BOXPLOT"
    value_column_id: uuid.UUID
    group_column_id: uuid.UUID | None = None


class CorrelationMatrixParameters(RenderStyle):
    kind: Literal["CORRELATION_MATRIX"] = "CORRELATION_MATRIX"
    column_ids: list[uuid.UUID] = Field(min_length=2, max_length=20)

    @model_validator(mode="after")
    def distinct_columns(self) -> CorrelationMatrixParameters:
        if len(set(self.column_ids)) != len(self.column_ids):
            raise ValueError("Correlation matrix columns must be distinct")
        return self


FigureParameters = Annotated[
    ScatterParameters
    | GroupComparisonParameters
    | HistogramParameters
    | BoxplotParameters
    | CorrelationMatrixParameters,
    Field(discriminator="kind"),
]


class FigurePlanCreate(StrictModel):
    dataset_version_id: uuid.UUID
    analysis_run_id: uuid.UUID | None = None
    analysis_result_id: uuid.UUID | None = None
    chart_type: FigureChartType
    parameters: FigureParameters
    caption: str = Field(min_length=1, max_length=4000)

    @model_validator(mode="after")
    def consistent_shape(self) -> FigurePlanCreate:
        if self.parameters.kind != self.chart_type.value:
            raise ValueError("chart_type must match the parameter discriminator")
        if self.analysis_result_id is not None and self.analysis_run_id is None:
            raise ValueError("analysis_result_id requires analysis_run_id")
        if (
            isinstance(self.parameters, GroupComparisonParameters)
            and self.parameters.error_bar == "CI_FROM_RESULT"
            and self.analysis_result_id is None
        ):
            raise ValueError("CI_FROM_RESULT requires an AnalysisResult")
        return self


class FigureRenderCreate(StrictModel):
    reason: str | None = Field(default=None, max_length=2000)


class FigureRecommendationRequest(StrictModel):
    dataset_version_id: uuid.UUID
    analysis_run_id: uuid.UUID | None = None


class FigureInvalidate(StrictModel):
    reason: str = Field(min_length=1, max_length=2000)
