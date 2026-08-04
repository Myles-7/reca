from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd  # type: ignore[import-untyped]
import pytest

from app.data_quality.engine import (
    MAX_AFFECTED_ROWS,
    MAX_EXAMPLES,
    ColumnContext,
    scan_dataframe,
)
from app.data_quality.registry import (
    RECA_P0_DEFAULT,
    resolve_persisted_ruleset,
    select_ruleset,
)
from app.models import (
    DataQualityIssueType,
    DatasetColumnType,
    DatasetSemanticRole,
)

pytestmark = pytest.mark.no_database

FIXTURES = (
    Path(__file__).resolve().parents[3] / "tests" / "golden" / "m4_data_quality" / "v1"
)


def _context(
    name: str,
    order: int,
    *,
    inferred: DatasetColumnType = DatasetColumnType.STRING,
    semantic_role: DatasetSemanticRole | None = None,
    is_identifier: bool = False,
    is_sensitive: bool = False,
    unit: str | None = None,
) -> ColumnContext:
    return ColumnContext(
        id=None,
        source_name=name,
        column_order=order,
        inferred_type=inferred,
        semantic_role=semantic_role,
        is_identifier=is_identifier,
        is_sensitive=is_sensitive,
        unit=unit,
    )


def test_registry_identity_and_sensitive_selection_are_versioned() -> None:
    full = select_ruleset("RECA_P0_DEFAULT", include_sensitive_field_detection=True)
    filtered = select_ruleset(
        "RECA_P0_DEFAULT", include_sensitive_field_detection=False
    )

    assert full.version == filtered.version == "1.0.0"
    assert len(full.content_hash) == len(filtered.content_hash) == 64
    assert full.content_hash != filtered.content_hash
    assert full.content_hash == RECA_P0_DEFAULT.content_hash
    assert resolve_persisted_ruleset(
        ruleset_id=full.ruleset_id,
        version=full.version,
        content_hash=full.content_hash,
    ) == (full, True)
    assert resolve_persisted_ruleset(
        ruleset_id=filtered.ruleset_id,
        version=filtered.version,
        content_hash=filtered.content_hash,
    ) == (filtered, False)


def test_golden_issue_families_are_stable_aggregated_and_non_mutating() -> None:
    path = FIXTURES / "issues.csv"
    before_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    frame = pd.read_csv(path, dtype=object, keep_default_na=False)
    snapshot = frame.copy(deep=True)
    columns = tuple(
        _context(
            name,
            order,
            inferred=(
                DatasetColumnType.DATE
                if name == "visit_date"
                else DatasetColumnType.STRING
            ),
            semantic_role=(
                DatasetSemanticRole.ID
                if name == "id"
                else DatasetSemanticRole.GROUP_VARIABLE
                if name == "group"
                else None
            ),
            is_identifier=name == "id",
            is_sensitive=name == "email",
        )
        for order, name in enumerate(frame.columns)
    )

    facts = scan_dataframe(
        frame,
        columns=columns,
        ruleset=RECA_P0_DEFAULT,
        include_sensitive_field_detection=True,
    )

    pd.testing.assert_frame_equal(snapshot, frame, check_exact=True)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before_hash
    issue_types = {fact.issue_type for fact in facts}
    assert {
        DataQualityIssueType.MISSING_VALUE,
        DataQualityIssueType.DUPLICATE_ROW,
        DataQualityIssueType.DUPLICATE_ID,
        DataQualityIssueType.CONSTANT_COLUMN,
        DataQualityIssueType.MIXED_TYPE,
        DataQualityIssueType.CATEGORY_INCONSISTENCY,
        DataQualityIssueType.OUT_OF_RANGE,
        DataQualityIssueType.EXTREME_VALUE,
        DataQualityIssueType.GROUP_IMBALANCE,
        DataQualityIssueType.SUSPICIOUS_UNIT,
        DataQualityIssueType.INVALID_DATE,
        DataQualityIssueType.POSSIBLE_SENSITIVE_FIELD,
    } <= issue_types
    assert all(fact.affected_row_count > 0 for fact in facts)
    assert all(len(fact.affected_rows) <= MAX_AFFECTED_ROWS for fact in facts)
    assert all(len(fact.evidence["examples"]) <= MAX_EXAMPLES for fact in facts)
    assert all(
        fact.evidence["ruleset_hash"] == RECA_P0_DEFAULT.content_hash for fact in facts
    )
    sensitive = [
        fact
        for fact in facts
        if fact.issue_type == DataQualityIssueType.POSSIBLE_SENSITIVE_FIELD
    ]
    assert sensitive
    assert all(set(fact.evidence["examples"]) <= {"[MASKED]"} for fact in sensitive)
    clues = [
        fact
        for fact in facts
        if fact.issue_type
        in {DataQualityIssueType.EXTREME_VALUE, DataQualityIssueType.GROUP_IMBALANCE}
    ]
    assert clues and all(
        "clue" in fact.description.lower()
        and "not confirmed"
        in fact.description.lower().replace("not a confirmed", "not confirmed")
        for fact in clues
    )


def test_sensitive_detection_is_masked_and_can_be_excluded_by_ruleset_hash() -> None:
    frame = pd.read_csv(FIXTURES / "sensitive.csv", dtype=object)
    columns = tuple(
        _context(name, order, is_sensitive=True)
        for order, name in enumerate(frame.columns)
    )
    full = scan_dataframe(
        frame,
        columns=columns,
        ruleset=RECA_P0_DEFAULT,
        include_sensitive_field_detection=True,
    )
    filtered_rules = select_ruleset(
        "RECA_P0_DEFAULT", include_sensitive_field_detection=False
    )
    filtered = scan_dataframe(
        frame,
        columns=columns,
        ruleset=filtered_rules,
        include_sensitive_field_detection=False,
    )

    full_sensitive = [
        fact
        for fact in full
        if fact.issue_type == DataQualityIssueType.POSSIBLE_SENSITIVE_FIELD
    ]
    assert {fact.column_name for fact in full_sensitive} >= {
        "phone",
        "email",
        "id_card",
        "student_number",
    }
    assert all(
        set(fact.evidence["examples"]) == {"[MASKED]"} for fact in full_sensitive
    )
    assert not any(
        fact.issue_type == DataQualityIssueType.POSSIBLE_SENSITIVE_FIELD
        for fact in filtered
    )


def test_failure_rows_and_examples_are_bounded_without_per_cell_issues() -> None:
    frame = pd.DataFrame(
        {"email": [f"person-{index}@example.test" for index in range(250)]}
    )
    facts = scan_dataframe(
        frame,
        columns=(_context("email", 0, is_sensitive=True),),
        ruleset=RECA_P0_DEFAULT,
        include_sensitive_field_detection=True,
    )
    sensitive = next(
        fact
        for fact in facts
        if fact.issue_type == DataQualityIssueType.POSSIBLE_SENSITIVE_FIELD
    )

    assert sensitive.affected_row_count == 250
    assert len(sensitive.affected_rows) == MAX_AFFECTED_ROWS
    assert sensitive.evidence["examples"] == ["[MASKED]"]
    assert sensitive.evidence["affected_rows_truncated"] is True
