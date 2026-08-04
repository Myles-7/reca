from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, cast

import pandas as pd  # type: ignore[import-untyped]
import pytest

from app.data_quality.engine import ColumnContext, scan_dataframe
from app.data_quality.registry import RECA_P0_DEFAULT
from app.datasets import parsers
from app.models import DatasetColumnType

pytestmark = pytest.mark.no_database

FIXTURE_DIR = (
    Path(__file__).resolve().parents[3] / "tests" / "golden" / "m4_data_quality" / "v1"
)


def _manifest() -> dict[str, Any]:
    return cast(
        dict[str, Any],
        json.loads((FIXTURE_DIR / "manifest.json").read_text(encoding="utf-8")),
    )


def test_manifest_fixes_ruleset_identity_limits_and_fixture_hashes() -> None:
    manifest = _manifest()

    assert manifest["golden_set_id"] == "M4_DATA_QUALITY"
    assert manifest["golden_set_version"] == "1.0"
    assert manifest["contains_real_personal_data"] is False
    assert manifest["ruleset"] == {
        "id": RECA_P0_DEFAULT.ruleset_id,
        "version": RECA_P0_DEFAULT.version,
        "content_hash": RECA_P0_DEFAULT.content_hash,
    }
    assert manifest["limits"] == {"max_affected_rows": 100, "max_examples": 5}
    assert manifest["expected_rule_ids"] == [
        rule.rule_id for rule in RECA_P0_DEFAULT.rules
    ]
    for filename, expected_hash in manifest["files"].items():
        assert (
            hashlib.sha256((FIXTURE_DIR / filename).read_bytes()).hexdigest()
            == expected_hash
        )


def test_clean_fixture_has_no_quality_facts_under_declared_projection() -> None:
    frame = pd.read_csv(FIXTURE_DIR / "clean.csv", dtype=object)
    columns = tuple(
        ColumnContext(
            id=None,
            source_name=name,
            column_order=order,
            inferred_type=(
                DatasetColumnType.DATE
                if name == "observed_on"
                else DatasetColumnType.NUMERIC
                if name == "measure"
                else DatasetColumnType.STRING
            ),
        )
        for order, name in enumerate(frame.columns)
    )

    assert (
        scan_dataframe(
            frame,
            columns=columns,
            ruleset=RECA_P0_DEFAULT,
            include_sensitive_field_detection=True,
        )
        == ()
    )


def test_multisheet_xlsx_fixture_is_safe_visible_and_hidden_aware() -> None:
    path = FIXTURE_DIR / "multi_sheet.xlsx"
    sheets = parsers.worksheet_manifest(path)

    assert [(sheet.name, sheet.visibility) for sheet in sheets] == [
        ("Clean", "VISIBLE"),
        ("Issues", "VISIBLE"),
        ("Hidden", "HIDDEN"),
    ]
    parsed = parsers.parse_xlsx(path, "Issues")
    assert parsed.headers == ("id", "value")
    assert parsed.row_count == 2
    assert parsed.preview_rows == ({"id": "x", "value": 1}, {"id": "x", "value": 1})
