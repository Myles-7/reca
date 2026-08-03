from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models import QueryPlanStatus
from app.projects.schemas import ResponseMeta


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


def _normalized_terms(values: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        term = value.strip()
        if not term:
            raise ValueError("terms must not contain blank values")
        marker = term.casefold()
        if marker not in seen:
            seen.add(marker)
            normalized.append(term)
    return normalized


class QueryPlanFilters(StrictModel):
    from_year: int | None = Field(default=None, ge=1, le=9999)
    to_year: int | None = Field(default=None, ge=1, le=9999)
    languages: list[str] = Field(default_factory=list)
    work_types: list[str] = Field(default_factory=list)
    open_access_only: bool = False

    @field_validator("languages", "work_types")
    @classmethod
    def validate_terms(cls, values: list[str]) -> list[str]:
        return _normalized_terms(values)

    @model_validator(mode="after")
    def validate_year_range(self) -> QueryPlanFilters:
        if (
            self.from_year is not None
            and self.to_year is not None
            and self.from_year > self.to_year
        ):
            raise ValueError("from_year must be less than or equal to to_year")
        return self


class QueryPlanFields(StrictModel):
    chinese_terms: list[str] | None = None
    english_terms: list[str] | None = None
    synonyms: dict[str, list[str]] | None = None
    object_terms: dict[str, list[str]] | None = None
    method_terms: dict[str, list[str]] | None = None
    boolean_query: str | None = Field(default=None, max_length=20_000)
    filters: QueryPlanFilters | None = None
    limitations: list[str] | None = None

    @field_validator("chinese_terms", "english_terms", "limitations")
    @classmethod
    def validate_optional_terms(cls, values: list[str] | None) -> list[str] | None:
        return _normalized_terms(values) if values is not None else None

    @field_validator("synonyms", "object_terms", "method_terms")
    @classmethod
    def validate_grouped_terms(
        cls, values: dict[str, list[str]] | None
    ) -> dict[str, list[str]] | None:
        if values is None:
            return None
        normalized: dict[str, list[str]] = {}
        for language, terms in values.items():
            key = language.strip()
            if not key:
                raise ValueError("term group keys must not be blank")
            normalized[key] = _normalized_terms(terms)
        return normalized

    @field_validator("boolean_query")
    @classmethod
    def validate_boolean_query(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError("boolean_query must not be blank")
        return normalized


class QueryPlanCreate(QueryPlanFields):
    research_question_version_id: uuid.UUID


class QueryPlanUpdate(StrictModel):
    fields: QueryPlanFields
    change_reason: str = Field(min_length=1, max_length=2000)


class QueryPlanGenerateRequest(StrictModel):
    pass


class QueryPlanPublic(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    research_question_version_id: uuid.UUID
    chinese_terms: list[str] | None
    english_terms: list[str] | None
    synonyms: dict[str, list[str]] | None
    object_terms: dict[str, list[str]] | None
    method_terms: dict[str, list[str]] | None
    boolean_query: str | None
    filters: dict[str, Any] | None
    limitations: list[str] | None
    source_model_invocation_id: uuid.UUID | None
    status: QueryPlanStatus
    lock_version: int
    created_at: datetime
    updated_at: datetime
    allowed_actions: list[str]


class QueryPlanEnvelope(BaseModel):
    data: QueryPlanPublic
    meta: ResponseMeta
