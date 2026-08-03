from __future__ import annotations

import uuid
from typing import Literal

from pydantic import Field, field_validator, model_validator

from app.query_plans.schemas import StrictModel, _normalized_terms
from app.research_questions.ai_schemas import AIOutputEnvelope


class QueryPlanTermSet(StrictModel):
    core: list[str] = Field(default_factory=list)
    synonyms: list[str] = Field(default_factory=list)
    object_terms: list[str] = Field(default_factory=list)
    method_terms: list[str] = Field(default_factory=list)

    @field_validator("core", "synonyms", "object_terms", "method_terms")
    @classmethod
    def validate_terms(cls, values: list[str]) -> list[str]:
        return _normalized_terms(values)


class QueryPlanSuggestionFilters(StrictModel):
    from_year: int | None = Field(default=None, ge=1, le=9999)
    to_year: int | None = Field(default=None, ge=1, le=9999)
    languages: list[str] = Field(default_factory=list)
    work_types: list[str] = Field(default_factory=list)

    @field_validator("languages", "work_types")
    @classmethod
    def validate_terms(cls, values: list[str]) -> list[str]:
        return _normalized_terms(values)

    @model_validator(mode="after")
    def validate_year_range(self) -> QueryPlanSuggestionFilters:
        if (
            self.from_year is not None
            and self.to_year is not None
            and self.from_year > self.to_year
        ):
            raise ValueError("from_year must be less than or equal to to_year")
        return self


class QueryPlanGenerationInput(StrictModel):
    query_plan_id: uuid.UUID
    query_plan_lock_version: int = Field(ge=1)
    research_question_version_id: uuid.UUID
    research_question: str = Field(min_length=1, max_length=20_000)
    current_filters: dict[str, object] | None = None


class QueryPlanGenerationOutput(StrictModel):
    chinese_terms: QueryPlanTermSet
    english_terms: QueryPlanTermSet
    boolean_query: str = Field(min_length=1, max_length=20_000)
    filters: QueryPlanSuggestionFilters
    expansion_options: list[str] = Field(default_factory=list)
    narrowing_options: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)

    @field_validator("expansion_options", "narrowing_options", "limitations")
    @classmethod
    def validate_explanations(cls, values: list[str]) -> list[str]:
        return _normalized_terms(values)


class QueryPlanGenerationEnvelope(AIOutputEnvelope[QueryPlanGenerationOutput]):
    task_type: Literal["QUERY_PLAN_GENERATION"] = "QUERY_PLAN_GENERATION"
