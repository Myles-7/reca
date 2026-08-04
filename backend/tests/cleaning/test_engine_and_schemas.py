from __future__ import annotations

import uuid

import pandas as pd  # type: ignore[import-untyped]
import pytest
from pydantic import TypeAdapter, ValidationError

from app.api.errors import ContractError
from app.cleaning.engine import apply_actions, canonical_hash
from app.cleaning.schemas import CleaningActionInput
from app.cleaning.service import _serialize
from app.models import DatasetColumn, DatasetColumnType, DatasetFileFormat

pytestmark = pytest.mark.no_database


def _column(name: str, order: int) -> DatasetColumn:
    return DatasetColumn(
        project_id=uuid.uuid4(),
        dataset_version_id=uuid.uuid4(),
        source_name=name,
        column_order=order,
        inferred_type=DatasetColumnType.STRING,
        unique_count=2,
        missing_ratio=0,
    )


def _action(payload: dict[str, object]) -> CleaningActionInput:
    return TypeAdapter(CleaningActionInput).validate_python(payload)


def test_enabled_actions_are_deterministic_composable_and_non_mutating() -> None:
    category = _column("category", 1)
    score = _column("score", 2)
    note = _column("note", 3)
    frame = pd.DataFrame(
        {"category": ["a", "B"], "score": ["1", "bad"], "note": ["x", "y"]},
        dtype=object,
    )
    snapshot = frame.copy(deep=True)
    actions = [
        _action(
            {
                "action_type": "MAP_CATEGORY",
                "target_columns": [category.id],
                "row_selector": {"selector_type": "ALL_ROWS"},
                "parameters": {"mapping": {"a": "A"}},
                "reason": "normalize",
            }
        ),
        _action(
            {
                "action_type": "REPLACE_VALUE",
                "target_columns": [note.id],
                "row_selector": {
                    "selector_type": "VALUE_EQUALS",
                    "column_id": note.id,
                    "value": "x",
                },
                "parameters": {"replacement": "ok"},
                "reason": "replace",
            }
        ),
        _action(
            {
                "action_type": "MARK_MISSING",
                "target_columns": [note.id],
                "row_selector": {
                    "selector_type": "VALUE_EQUALS",
                    "column_id": note.id,
                    "value": "y",
                },
                "parameters": {},
                "reason": "missing",
            }
        ),
        _action(
            {
                "action_type": "CAST_TYPE",
                "target_columns": [score.id],
                "row_selector": {"selector_type": "ALL_ROWS"},
                "parameters": {"target_type": "INTEGER", "on_invalid": "MARK_MISSING"},
                "reason": "cast",
            }
        ),
        _action(
            {
                "action_type": "RENAME_COLUMN",
                "target_columns": [category.id],
                "row_selector": {"selector_type": "ALL_ROWS"},
                "parameters": {"new_name": "group"},
                "reason": "rename",
            }
        ),
        _action(
            {
                "action_type": "REPLACE_VALUE",
                "target_columns": [category.id],
                "row_selector": {
                    "selector_type": "VALUE_EQUALS",
                    "column_id": category.id,
                    "value": "B",
                },
                "parameters": {"replacement": "C"},
                "reason": "post rename",
            }
        ),
    ]

    first = apply_actions(
        frame, actions=actions, columns=[category, score, note], issue_rows={}
    )
    second = apply_actions(
        frame, actions=actions, columns=[category, score, note], issue_rows={}
    )

    pd.testing.assert_frame_equal(frame, snapshot, check_exact=True)
    pd.testing.assert_frame_equal(first.frame, second.frame, check_exact=True)
    assert first.frame.to_dict(orient="list") == {
        "group": ["A", "C"],
        "score": [1, None],
        "note": ["ok", None],
    }
    assert canonical_hash(actions) == canonical_hash(actions)
    assert len(first.sample_changes) <= 10


@pytest.mark.parametrize(
    "action_type",
    ["KEEP_ROWS", "DROP_ROWS", "IMPUTE_VALUE", "CONVERT_UNIT", "CREATE_DERIVED_COLUMN"],
)
def test_unavailable_actions_are_parsed_but_fail_closed(action_type: str) -> None:
    column = _column("value", 1)
    action = _action(
        {
            "action_type": action_type,
            "target_columns": [column.id],
            "parameters": {},
            "reason": "candidate",
        }
    )
    from app.cleaning.service import _assert_action_available

    with pytest.raises(ContractError, match="not available") as caught:
        _assert_action_available(action)
    assert caught.value.code == "ACTION_NOT_AVAILABLE"


@pytest.mark.parametrize(
    "injection",
    [
        {"code": "import os"},
        {"sql": "DROP TABLE datasets"},
        {"expression": "__import__('os')"},
        {"callable": "os.system"},
        {"url": "https://example.test"},
    ],
)
def test_code_sql_expression_callable_and_url_fields_are_rejected(
    injection: dict[str, str],
) -> None:
    column = _column("value", 1)
    payload = {
        "action_type": "REPLACE_VALUE",
        "target_columns": [column.id],
        "parameters": {"replacement": "safe", **injection},
        "reason": "reject extras",
    }
    with pytest.raises(ValidationError):
        _action(payload)


def test_cast_failure_duplicate_rename_and_formula_export_fail_safely() -> None:
    value = _column("value", 1)
    other = _column("other", 2)
    frame = pd.DataFrame({"value": ["not-number"], "other": ["=SUM(A1:A2)"]})
    cast_action = _action(
        {
            "action_type": "CAST_TYPE",
            "target_columns": [value.id],
            "parameters": {"target_type": "INTEGER", "on_invalid": "FAIL"},
            "reason": "strict",
        }
    )
    with pytest.raises(ContractError) as cast_error:
        apply_actions(
            frame, actions=[cast_action], columns=[value, other], issue_rows={}
        )
    assert cast_error.value.code == "CLEANING_CAST_FAILED"

    rename = _action(
        {
            "action_type": "RENAME_COLUMN",
            "target_columns": [value.id],
            "parameters": {"new_name": "other"},
            "reason": "collision",
        }
    )
    with pytest.raises(ContractError) as rename_error:
        apply_actions(frame, actions=[rename], columns=[value, other], issue_rows={})
    assert rename_error.value.code == "DUPLICATE_COLUMN"
    assert b"'=SUM(A1:A2)" in _serialize(frame, DatasetFileFormat.CSV)
