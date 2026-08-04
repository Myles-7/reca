from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models import (
    DatasetColumnConfirmationStatus,
    DatasetColumnType,
    DatasetLicenseStatus,
    DatasetSemanticRole,
    DatasetSourceType,
    DatasetStatus,
)


class DatasetUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=10_000)
    source_type: DatasetSourceType | None = None
    publisher: str | None = Field(default=None, max_length=255)
    source_platform: str | None = Field(default=None, max_length=255)
    source_identifier: str | None = Field(default=None, max_length=500)
    doi: str | None = Field(default=None, max_length=500)
    acquired_at: date | None = None
    license_name: str | None = Field(default=None, max_length=255)
    license_status: DatasetLicenseStatus | None = None
    recommended_citation: str | None = Field(default=None, max_length=10_000)
    known_limitations: list[str] | None = Field(default=None, max_length=100)
    status: DatasetStatus | None = None

    @model_validator(mode="after")
    def require_change(self) -> DatasetUpdate:
        if not self.model_fields_set:
            raise ValueError("At least one field is required.")
        return self


class DatasetColumnUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_name: str | None = Field(default=None, max_length=255)
    confirmed_type: DatasetColumnType | None = None
    semantic_role: DatasetSemanticRole | None = None
    unit: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=10_000)
    missing_codes: list[str] | None = Field(default=None, max_length=100)
    category_mapping: dict[str, Any] | None = None
    is_identifier: bool | None = None
    is_sensitive: bool | None = None
    confirmation_status: DatasetColumnConfirmationStatus | None = None

    @model_validator(mode="after")
    def require_change(self) -> DatasetColumnUpdate:
        if not self.model_fields_set:
            raise ValueError("At least one field is required.")
        if (
            self.confirmation_status == DatasetColumnConfirmationStatus.CONFIRMED
            and self.confirmed_type is None
            and "confirmed_type" in self.model_fields_set
        ):
            raise ValueError(
                "A confirmed field cannot explicitly clear confirmed_type."
            )
        return self


class WorksheetSelection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    worksheet_name: str = Field(min_length=1, max_length=255)
    acknowledge_hidden: bool = False


class DatasetVersionInvalidation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str = Field(min_length=1, max_length=2_000)
