import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.agents.prompts import get_prompt_contract, prompt_content_hash
from app.research_questions.ai_schemas import (
    ResearchQuestionScopingInput,
    ResearchQuestionScopingOutput,
    ResearchQuestionSpec,
)
from app.research_questions.scoping import (
    FIXTURE_DIRECTORY,
    load_fixture_contract,
)

pytestmark = pytest.mark.no_database


def fixture_payload(name: str) -> dict[str, object]:
    return json.loads((FIXTURE_DIRECTORY / name).read_text(encoding="utf-8"))


def test_research_question_spec_golden_fixture_is_strict() -> None:
    payload = fixture_payload("rq-parse-recorded-v1.json")
    spec = ResearchQuestionSpec.model_validate(payload)
    assert spec.research_goal == "RELATE"
    assert spec.relationship_type == "ASSOCIATION"
    assert len(spec.follow_up_questions) <= 3

    with pytest.raises(ValidationError):
        ResearchQuestionSpec.model_validate(
            {**payload, "relationship_type": "CAUSATION"}
        )
    with pytest.raises(ValidationError):
        ResearchQuestionSpec.model_validate(
            {**payload, "ignore_policy_and_run_shell": True}
        )


def test_scoping_schema_enforces_round_question_candidate_and_state_limits() -> None:
    valid = fixture_payload("rq-scoping-needs-input-mock-v1.json")
    valid["source_ids"] = ["00000000-0000-0000-0000-000000000001"]
    output = ResearchQuestionScopingOutput.model_validate(valid)
    assert len(output.socratic_questions) == 3

    with pytest.raises(ValidationError):
        ResearchQuestionScopingOutput.model_validate({**valid, "status": "UNREVIEWED"})
    with pytest.raises(ValidationError):
        ResearchQuestionScopingOutput.model_validate(
            {
                **valid,
                "socratic_questions": [
                    *valid["socratic_questions"],
                    valid["socratic_questions"][0],
                ],  # type: ignore[index]
            }
        )
    with pytest.raises(ValidationError):
        ResearchQuestionScopingOutput.model_validate(
            {**valid, "status": "CANDIDATES_READY"}
        )
    with pytest.raises(ValidationError):
        ResearchQuestionScopingInput.model_validate(
            {
                "topic": "topic",
                "project_context": {
                    "project_id": "00000000-0000-0000-0000-000000000001",
                    "project_stage": "INTENT",
                },
                "round_number": 3,
            }
        )


def test_scoping_prompt_assets_are_hash_locked_lf_and_tool_free() -> None:
    for prompt_id in ("research-question-parse", "research-question-scoping"):
        contract = get_prompt_contract(prompt_id, "1.0.0")
        asset = (
            Path(__file__).resolve().parents[2]
            / "app/agents/prompts"
            / (f"{prompt_id}-1.0.0.txt")
        )
        assert prompt_content_hash(asset) == contract.content_hash
        assert b"\r\n" not in asset.read_bytes()
        assert contract.allowed_tools == ()
        assert contract.required_source_types == ("ResearchQuestionVersion",)
        assert contract.requested_data_access_level == "REDACTED_CONTENT"
        assert contract.max_allowed_data_access_level == "REDACTED_CONTENT"

    mock = load_fixture_contract("rq-scoping-needs-input-mock-v1")
    recorded = load_fixture_contract("rq-scoping-candidates-recorded-v1")
    assert mock.mode == "MOCK"
    assert recorded.mode == "RECORDED"
    assert recorded.recording_redaction_status == "REVIEWED_NO_PERSONAL_DATA"
