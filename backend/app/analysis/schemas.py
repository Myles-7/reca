from __future__ import annotations

import uuid
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models import (
    AlternativeHypothesis,
    AnalysisGoal,
    AnalysisMethod,
    AssumptionCheckCode,
    MissingDataMode,
    VarianceMode,
)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class MissingDataPolicy(StrictModel):
    mode: MissingDataMode


class EqualsFilter(StrictModel):
    operator: Literal["EQUALS"]
    column_id: uuid.UUID
    value: str | int | float | bool


class InFilter(StrictModel):
    operator: Literal["IN"]
    column_id: uuid.UUID
    values: list[str | int | float | bool] = Field(min_length=1, max_length=100)


class NullFilter(StrictModel):
    operator: Literal["IS_NULL", "IS_NOT_NULL"]
    column_id: uuid.UUID


class NumericRangeFilter(StrictModel):
    operator: Literal["NUMERIC_RANGE"]
    column_id: uuid.UUID
    minimum: float | None = None
    maximum: float | None = None
    include_minimum: bool = True
    include_maximum: bool = True

    @model_validator(mode="after")
    def validate_bounds(self) -> NumericRangeFilter:
        if self.minimum is None and self.maximum is None:
            raise ValueError("NUMERIC_RANGE requires at least one bound")
        if (
            self.minimum is not None
            and self.maximum is not None
            and self.minimum > self.maximum
        ):
            raise ValueError("minimum must not exceed maximum")
        return self


SampleFilter = Annotated[
    EqualsFilter | InFilter | NullFilter | NumericRangeFilter,
    Field(discriminator="operator"),
]


class AnalysisParameters(StrictModel):
    confidence_level: float = Field(default=0.95, ge=0.8, le=0.99)
    alternative: AlternativeHypothesis = AlternativeHypothesis.TWO_SIDED
    variance_mode: VarianceMode = VarianceMode.WELCH
    independence_confirmed: bool = False
    pairing_confirmed: bool = False
    pair_id_column_id: uuid.UUID | None = None
    assumption_confirmations: list[AssumptionCheckCode] = Field(
        default_factory=list, max_length=20
    )
    acknowledged_quality_issue_ids: list[uuid.UUID] = Field(
        default_factory=list, max_length=200
    )
    sensitive_column_acknowledgements: list[uuid.UUID] = Field(
        default_factory=list, max_length=20
    )


class AnalysisPlanCreate(StrictModel):
    research_question_version_id: uuid.UUID
    dataset_version_id: uuid.UUID
    analysis_goal: AnalysisGoal
    method: AnalysisMethod
    dependent_variable_ids: list[uuid.UUID] = Field(default_factory=list, max_length=20)
    independent_variable_ids: list[uuid.UUID] = Field(
        default_factory=list, max_length=20
    )
    control_variable_ids: list[uuid.UUID] = Field(default_factory=list, max_length=20)
    missing_data_policy: MissingDataPolicy
    sample_filter: SampleFilter | None = None
    parameters: AnalysisParameters = Field(default_factory=AnalysisParameters)

    @model_validator(mode="after")
    def validate_method_shape(self) -> AnalysisPlanCreate:
        all_ids = (
            self.dependent_variable_ids
            + self.independent_variable_ids
            + self.control_variable_ids
        )
        if not all_ids or len(all_ids) > 20 or len(set(all_ids)) != len(all_ids):
            raise ValueError("Plan must reference 1-20 distinct columns")
        if self.method == AnalysisMethod.DESCRIPTIVE_STATISTICS:
            if self.control_variable_ids:
                raise ValueError(
                    "Descriptive statistics do not accept control variables"
                )
        elif self.method in {
            AnalysisMethod.PEARSON_CORRELATION,
            AnalysisMethod.SPEARMAN_CORRELATION,
            AnalysisMethod.SIMPLE_LINEAR_REGRESSION,
        } and (
            len(self.dependent_variable_ids) != 1
            or len(self.independent_variable_ids) != 1
        ):
            raise ValueError("Correlation/regression requires exactly one X and one Y")
        elif self.method == AnalysisMethod.INDEPENDENT_TWO_GROUP and (
            len(self.dependent_variable_ids) != 1
            or len(self.independent_variable_ids) != 1
            or self.control_variable_ids
            or not self.parameters.independence_confirmed
        ):
            raise ValueError(
                "Independent comparison requires outcome, group and confirmation"
            )
        elif self.method == AnalysisMethod.PAIRED_TWO_GROUP and (
            len(self.dependent_variable_ids) != 2
            or self.independent_variable_ids
            or len(self.control_variable_ids) != 1
            or self.parameters.pair_id_column_id != self.control_variable_ids[0]
            or not self.parameters.pairing_confirmed
        ):
            raise ValueError(
                "Paired comparison requires two outcomes and one confirmed pair ID"
            )
        expected_goal = {
            AnalysisMethod.DESCRIPTIVE_STATISTICS: AnalysisGoal.DESCRIBE,
            AnalysisMethod.PEARSON_CORRELATION: AnalysisGoal.CORRELATION,
            AnalysisMethod.SPEARMAN_CORRELATION: AnalysisGoal.CORRELATION,
            AnalysisMethod.INDEPENDENT_TWO_GROUP: AnalysisGoal.COMPARE_GROUPS,
            AnalysisMethod.PAIRED_TWO_GROUP: AnalysisGoal.COMPARE_GROUPS,
            AnalysisMethod.SIMPLE_LINEAR_REGRESSION: AnalysisGoal.MODEL,
        }[self.method]
        if self.analysis_goal != expected_goal:
            raise ValueError("analysis_goal does not match method")
        return self


class AnalysisPlanUpdate(StrictModel):
    analysis_goal: AnalysisGoal | None = None
    method: AnalysisMethod | None = None
    dependent_variable_ids: list[uuid.UUID] | None = Field(default=None, max_length=20)
    independent_variable_ids: list[uuid.UUID] | None = Field(
        default=None, max_length=20
    )
    control_variable_ids: list[uuid.UUID] | None = Field(default=None, max_length=20)
    missing_data_policy: MissingDataPolicy | None = None
    sample_filter: SampleFilter | None = None
    parameters: AnalysisParameters | None = None


class AnalysisRunCreate(StrictModel):
    run_reason: str | None = Field(default=None, max_length=2000)


class AnalysisInvalidate(StrictModel):
    reason: str = Field(min_length=1, max_length=2000)


class EngineColumn(StrictModel):
    column_id: uuid.UUID
    name: str
    kind: Literal["numeric", "categorical"]


class EngineRequest(StrictModel):
    method: AnalysisMethod
    columns: list[EngineColumn]
    missing_data_policy: MissingDataPolicy
    parameters: AnalysisParameters


class AssumptionDTO(StrictModel):
    check_code: str
    status: str
    subject_key: str = "__plan__"
    explanation: str
    evidence: dict[str, Any] = Field(default_factory=dict)
    blocks_approval: bool = False


class ResultDTO(StrictModel):
    result_key: str
    result_type: str
    is_primary: bool = False
    payload: dict[str, Any]


class EngineOutput(StrictModel):
    effective_n: int
    results: list[ResultDTO]
    assumptions: list[AssumptionDTO]
    warnings: list[str] = Field(default_factory=list)
