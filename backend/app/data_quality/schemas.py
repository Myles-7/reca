from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class QualityRunCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rule_set: str = Field(default="RECA_P0_DEFAULT", min_length=1, max_length=100)
    include_sensitive_field_detection: bool = True


class QualityIssueAcknowledge(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str | None = Field(default=None, max_length=2_000)


class QualityIssueIgnore(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str = Field(min_length=1, max_length=2_000)
