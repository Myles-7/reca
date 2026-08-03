import uuid

import pytest
from pydantic import ValidationError

from app.query_plans.ai_schemas import QueryPlanGenerationOutput
from app.query_plans.schemas import QueryPlanCreate, QueryPlanFilters


def test_query_plan_schema_accepts_bilingual_terms_boolean_and_filters() -> None:
    payload = QueryPlanCreate(
        research_question_version_id=uuid.uuid4(),
        chinese_terms=[" 生成式人工智能 ", "学习投入"],
        english_terms=["generative AI", "student engagement"],
        synonyms={"zh": ["生成式AI"], "en": ["generative AI"]},
        boolean_query='("generative AI") AND ("student engagement")',
        filters=QueryPlanFilters(
            from_year=2020,
            to_year=2026,
            languages=["zh", "en"],
            work_types=["article"],
            open_access_only=True,
        ),
    )
    assert payload.chinese_terms == ["生成式人工智能", "学习投入"]
    assert payload.filters is not None and payload.filters.open_access_only is True


def test_query_plan_schemas_reject_provider_and_invalid_ranges() -> None:
    with pytest.raises(ValidationError):
        QueryPlanCreate.model_validate(
            {
                "research_question_version_id": str(uuid.uuid4()),
                "provider": "OpenAlex",
            }
        )
    with pytest.raises(ValidationError):
        QueryPlanFilters(from_year=2026, to_year=2020)


def test_ai_query_plan_schema_is_strict_and_provider_neutral() -> None:
    valid = {
        "chinese_terms": {"core": ["学习投入"]},
        "english_terms": {"core": ["student engagement"]},
        "boolean_query": '"student engagement"',
        "filters": {
            "from_year": 2020,
            "to_year": 2026,
            "languages": ["zh", "en"],
            "work_types": ["article"],
        },
        "expansion_options": [],
        "narrowing_options": [],
        "limitations": ["No retrieval was executed."],
    }
    assert QueryPlanGenerationOutput.model_validate(valid).filters.languages == [
        "zh",
        "en",
    ]
    with pytest.raises(ValidationError):
        QueryPlanGenerationOutput.model_validate({**valid, "provider": "OpenAlex"})
