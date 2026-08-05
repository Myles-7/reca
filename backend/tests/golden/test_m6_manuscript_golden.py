import json
from pathlib import Path

import pytest

from app.manuscripts.rules import run_rules

pytestmark = pytest.mark.no_database


def test_m6_p0_must_golden_cases() -> None:
    fixture = json.loads(
        (Path(__file__).parent / "m6_manuscripts" / "v1" / "p0_must.json").read_text(
            encoding="utf-8"
        )
    )
    for case in fixture["cases"]:
        paragraphs = [
            {
                "index": index,
                **paragraph,
                "locator": {
                    "schema": "reca.manuscript.locator.v1",
                    "paragraph": index,
                    "table": None,
                    "cell": None,
                },
            }
            for index, paragraph in enumerate(case["paragraphs"])
        ]
        snapshot = {"paragraphs": paragraphs, "tables": []}
        actual = {
            finding.issue_type.value
            for finding in run_rules(snapshot, set(case["checks"]))
        }
        assert set(case["expected_codes"]).issubset(actual), case["id"]
