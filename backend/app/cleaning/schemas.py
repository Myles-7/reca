from __future__ import annotations

import uuid
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models import DatasetColumnType

LiteralValue = str | int | float | bool | None


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AllRowsSelector(StrictModel):
    selector_type: Literal["ALL_ROWS"] = "ALL_ROWS"


class IssueRowsSelector(StrictModel):
    selector_type: Literal["ISSUE_ROWS"] = "ISSUE_ROWS"
    issue_ids: list[uuid.UUID] = Field(min_length=1, max_length=50)


class ValueEqualsSelector(StrictModel):
    selector_type: Literal["VALUE_EQUALS"]
    column_id: uuid.UUID
    value: LiteralValue


class ValueInSelector(StrictModel):
    selector_type: Literal["VALUE_IN"]
    column_id: uuid.UUID
    values: list[LiteralValue] = Field(min_length=1, max_length=100)


class NullSelector(StrictModel):
    selector_type: Literal["IS_NULL", "IS_NOT_NULL"]
    column_id: uuid.UUID


class NumericRangeSelector(StrictModel):
    selector_type: Literal["NUMERIC_RANGE"]
    column_id: uuid.UUID
    minimum: float | None = None
    maximum: float | None = None
    include_minimum: bool = True
    include_maximum: bool = True

    @model_validator(mode="after")
    def validate_range(self) -> NumericRangeSelector:
        if self.minimum is None and self.maximum is None:
            raise ValueError("minimum or maximum is required")
        if (
            self.minimum is not None
            and self.maximum is not None
            and self.minimum > self.maximum
        ):
            raise ValueError("minimum cannot exceed maximum")
        return self


RowSelector = Annotated[
    AllRowsSelector
    | IssueRowsSelector
    | ValueEqualsSelector
    | ValueInSelector
    | NullSelector
    | NumericRangeSelector,
    Field(discriminator="selector_type"),
]


class MarkMissingParameters(StrictModel):
    replacement: None = None


class ReplaceValueParameters(StrictModel):
    replacement: LiteralValue


class MapCategoryParameters(StrictModel):
    mapping: dict[str, LiteralValue]

    @field_validator("mapping")
    @classmethod
    def validate_mapping(
        cls, value: dict[str, LiteralValue]
    ) -> dict[str, LiteralValue]:
        if not value or len(value) > 100:
            raise ValueError("mapping must contain between 1 and 100 entries")
        if any(not key or len(key) > 256 for key in value):
            raise ValueError("mapping keys must be bounded non-empty strings")
        return value


class CastTypeParameters(StrictModel):
    target_type: DatasetColumnType
    on_invalid: Literal["FAIL", "MARK_MISSING"] = "FAIL"

    @field_validator("target_type")
    @classmethod
    def validate_target_type(cls, value: DatasetColumnType) -> DatasetColumnType:
        if value in {DatasetColumnType.UNKNOWN, DatasetColumnType.CATEGORY}:
            raise ValueError("target_type is not available for deterministic casting")
        return value


class RenameColumnParameters(StrictModel):
    new_name: str = Field(min_length=1, max_length=255, pattern=r"^[^\x00-\x1f]+$")


class ActionBase(StrictModel):
    target_columns: list[uuid.UUID] = Field(min_length=1, max_length=20)
    row_selector: RowSelector = Field(default_factory=AllRowsSelector)
    reason: str = Field(min_length=1, max_length=2000)
    source_issue_ids: list[uuid.UUID] = Field(default_factory=list, max_length=50)

    @field_validator("target_columns", "source_issue_ids")
    @classmethod
    def unique_ids(cls, value: list[uuid.UUID]) -> list[uuid.UUID]:
        if len(value) != len(set(value)):
            raise ValueError("IDs must be unique")
        return value


class MarkMissingAction(ActionBase):
    action_type: Literal["MARK_MISSING"]
    parameters: MarkMissingParameters = Field(default_factory=MarkMissingParameters)


class ReplaceValueAction(ActionBase):
    action_type: Literal["REPLACE_VALUE"]
    parameters: ReplaceValueParameters


class MapCategoryAction(ActionBase):
    action_type: Literal["MAP_CATEGORY"]
    parameters: MapCategoryParameters

    @model_validator(mode="after")
    def one_target(self) -> MapCategoryAction:
        if len(self.target_columns) != 1:
            raise ValueError("MAP_CATEGORY requires exactly one target column")
        return self


class CastTypeAction(ActionBase):
    action_type: Literal["CAST_TYPE"]
    parameters: CastTypeParameters


class RenameColumnAction(ActionBase):
    action_type: Literal["RENAME_COLUMN"]
    parameters: RenameColumnParameters

    @model_validator(mode="after")
    def validate_rename(self) -> RenameColumnAction:
        if len(self.target_columns) != 1:
            raise ValueError("RENAME_COLUMN requires exactly one target column")
        if self.row_selector.selector_type != "ALL_ROWS":
            raise ValueError("RENAME_COLUMN requires ALL_ROWS")
        return self


class UnavailableParameters(StrictModel):
    pass


class UnavailableAction(ActionBase):
    action_type: Literal[
        "KEEP_ROWS",
        "DROP_ROWS",
        "IMPUTE_VALUE",
        "CONVERT_UNIT",
        "CREATE_DERIVED_COLUMN",
    ]
    parameters: UnavailableParameters = Field(default_factory=UnavailableParameters)


CleaningActionInput = Annotated[
    MarkMissingAction
    | ReplaceValueAction
    | MapCategoryAction
    | CastTypeAction
    | RenameColumnAction
    | UnavailableAction,
    Field(discriminator="action_type"),
]


class CleaningPlanCreate(StrictModel):
    title: str = Field(min_length=1, max_length=255)
    rationale: str | None = Field(default=None, max_length=5000)
    actions: list[CleaningActionInput] = Field(min_length=1, max_length=50)


class CleaningPlanUpdate(StrictModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    rationale: str | None = Field(default=None, max_length=5000)
    actions: list[CleaningActionInput] | None = Field(
        default=None, min_length=1, max_length=50
    )

    @model_validator(mode="after")
    def require_change(self) -> CleaningPlanUpdate:
        if not self.model_fields_set:
            raise ValueError("At least one field is required")
        return self


class CleaningPlanSuggestionRequest(StrictModel):
    mode: Literal["MOCK", "LIVE"] = "LIVE"
    fixture_output: dict[str, Any] | None = None

    @model_validator(mode="after")
    def validate_mode_input(self) -> CleaningPlanSuggestionRequest:
        if self.mode == "MOCK" and self.fixture_output is None:
            raise ValueError("fixture_output is required in MOCK mode")
        if self.mode == "LIVE" and self.fixture_output is not None:
            raise ValueError("fixture_output is only allowed in MOCK mode")
        return self


class SuggestionColumn(StrictModel):
    id: uuid.UUID
    name: str
    inferred_type: DatasetColumnType
    confirmed_type: DatasetColumnType | None = None
    missing_ratio: float
    unique_count: int
    is_identifier: bool
    is_sensitive: bool


class SuggestionIssue(StrictModel):
    id: uuid.UUID
    rule_code: str
    issue_type: str
    severity: str
    column_id: uuid.UUID | None = None
    affected_row_count: int
    evidence_summary: dict[str, Any]


class CleaningPlanSuggestionInput(StrictModel):
    dataset_version_id: uuid.UUID
    data_hash: str
    row_count: int
    column_count: int
    columns: list[SuggestionColumn] = Field(min_length=1, max_length=200)
    issues: list[SuggestionIssue] = Field(min_length=1, max_length=100)
    allowed_action_types: list[str]


class CleaningPlanSuggestion(StrictModel):
    title: str = Field(min_length=1, max_length=255)
    rationale: str | None = Field(default=None, max_length=5000)
    actions: list[CleaningActionInput] = Field(min_length=1, max_length=50)
    warnings: list[str] = Field(default_factory=list, max_length=20)
