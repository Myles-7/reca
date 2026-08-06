from __future__ import annotations

import hashlib
import json
import math
import unicodedata
import uuid
from dataclasses import dataclass
from typing import Any

import pandas as pd  # type: ignore[import-untyped]
from fastapi.encoders import jsonable_encoder

from app.api.errors import ContractError
from app.cleaning.schemas import (
    AllRowsSelector,
    CastTypeAction,
    CleaningActionInput,
    IssueRowsSelector,
    MapCategoryAction,
    MarkMissingAction,
    NumericRangeSelector,
    RenameColumnAction,
    ReplaceValueAction,
    RowSelector,
    ValueEqualsSelector,
    ValueInSelector,
)
from app.models import DatasetColumn, DatasetColumnType

MAX_SAMPLE_CHANGES = 10


@dataclass(frozen=True)
class TransformationResult:
    frame: pd.DataFrame
    affected_rows: tuple[int, ...]
    affected_columns: tuple[str, ...]
    sample_changes: tuple[dict[str, Any], ...]
    warnings: tuple[str, ...]


def canonicalize(value: Any) -> Any:
    encoded = jsonable_encoder(value)
    if isinstance(encoded, dict):
        return {
            unicodedata.normalize("NFC", str(key)): canonicalize(item)
            for key, item in sorted(encoded.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(encoded, list):
        return [canonicalize(item) for item in encoded]
    if isinstance(encoded, str):
        return unicodedata.normalize("NFC", encoded)
    if isinstance(encoded, float) and not math.isfinite(encoded):
        raise ContractError(
            status_code=422,
            code="VALIDATION_ERROR",
            message="NaN and Infinity are not valid action parameters.",
        )
    return encoded


def canonical_hash(value: Any) -> str:
    payload = json.dumps(
        canonicalize(value),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _column_map(columns: list[DatasetColumn]) -> dict[uuid.UUID, str]:
    return {column.id: column.source_name for column in columns}


def _selector_mask(
    frame: pd.DataFrame,
    selector: RowSelector,
    columns: dict[uuid.UUID, str],
    issue_rows: dict[uuid.UUID, tuple[int, ...]],
) -> pd.Series:
    if isinstance(selector, AllRowsSelector):
        return pd.Series(True, index=frame.index)
    if isinstance(selector, IssueRowsSelector):
        indexes = {
            index for issue_id in selector.issue_ids for index in issue_rows[issue_id]
        }
        return frame.index.to_series().isin(indexes)
    column = columns[selector.column_id]
    series = frame[column]
    if isinstance(selector, ValueEqualsSelector):
        return series == selector.value
    if isinstance(selector, ValueInSelector):
        return series.isin(selector.values)
    if selector.selector_type == "IS_NULL":
        return series.isna() | series.astype("string").str.strip().eq("")
    if selector.selector_type == "IS_NOT_NULL":
        return ~(series.isna() | series.astype("string").str.strip().eq(""))
    if not isinstance(selector, NumericRangeSelector):
        raise ContractError(
            status_code=422,
            code="CLEANING_SELECTOR_INVALID",
            message="The row selector is not supported.",
        )
    numeric = pd.to_numeric(series, errors="coerce")
    mask = numeric.notna()
    if selector.minimum is not None:
        mask &= (
            numeric.ge(selector.minimum)
            if selector.include_minimum
            else numeric.gt(selector.minimum)
        )
    if selector.maximum is not None:
        mask &= (
            numeric.le(selector.maximum)
            if selector.include_maximum
            else numeric.lt(selector.maximum)
        )
    return mask


def _cast(series: pd.Series, target: DatasetColumnType, on_invalid: str) -> pd.Series:
    original_missing = series.isna() | series.astype("string").str.strip().eq("")
    if target in {DatasetColumnType.INTEGER, DatasetColumnType.NUMERIC}:
        converted = pd.to_numeric(series, errors="coerce")
        if target == DatasetColumnType.INTEGER:
            converted = converted.round().astype("Int64")
    elif target == DatasetColumnType.BOOLEAN:
        mapping = {
            "true": True,
            "false": False,
            "yes": True,
            "no": False,
            "1": True,
            "0": False,
        }
        converted = series.astype("string").str.strip().str.casefold().map(mapping)
    elif target in {DatasetColumnType.DATE, DatasetColumnType.DATETIME}:
        converted = pd.to_datetime(series, errors="coerce")
        if target == DatasetColumnType.DATE:
            converted = converted.dt.date
    else:
        converted = series.astype("string")
    invalid = ~original_missing & converted.isna()
    if invalid.any() and on_invalid == "FAIL":
        raise ContractError(
            status_code=422,
            code="CLEANING_CAST_FAILED",
            message="CAST_TYPE encountered values that cannot be converted.",
        )
    return converted


def apply_actions(
    frame: pd.DataFrame,
    *,
    actions: list[CleaningActionInput],
    columns: list[DatasetColumn],
    issue_rows: dict[uuid.UUID, tuple[int, ...]],
) -> TransformationResult:
    source = frame.copy(deep=True)
    working = frame.copy(deep=True)
    by_id = _column_map(columns)
    affected_rows: set[int] = set()
    affected_columns: set[str] = set()
    samples: list[dict[str, Any]] = []

    for action in actions:
        mask = _selector_mask(working, action.row_selector, by_id, issue_rows)
        target_names = [by_id[column_id] for column_id in action.target_columns]
        before = working.loc[mask, target_names].copy(deep=True)
        if isinstance(action, MarkMissingAction):
            working.loc[mask, target_names] = None
        elif isinstance(action, ReplaceValueAction):
            working.loc[mask, target_names] = action.parameters.replacement
        elif isinstance(action, MapCategoryAction):
            name = target_names[0]
            mapping = action.parameters.mapping
            working.loc[mask, name] = working.loc[mask, name].map(
                lambda value, mapping=mapping: mapping.get(str(value), value)
            )
        elif isinstance(action, CastTypeAction):
            for name in target_names:
                converted = _cast(
                    working.loc[mask, name],
                    action.parameters.target_type,
                    action.parameters.on_invalid,
                )
                working.loc[mask, name] = converted
        elif isinstance(action, RenameColumnAction):
            old_name = target_names[0]
            new_name = action.parameters.new_name.strip()
            if new_name in working.columns and new_name != old_name:
                raise ContractError(
                    status_code=422,
                    code="DUPLICATE_COLUMN",
                    message="RENAME_COLUMN would create a duplicate column name.",
                )
            working = working.rename(columns={old_name: new_name})
            by_id[action.target_columns[0]] = new_name
            affected_columns.update({old_name, new_name})
            continue
        after = working.loc[mask, target_names]
        changed = (before.astype("string") != after.astype("string")) | (
            before.isna() != after.isna()
        )
        for row_index in changed.any(axis=1)[changed.any(axis=1)].index:
            affected_rows.add(int(row_index))
            if len(samples) < MAX_SAMPLE_CHANGES:
                samples.append(
                    {
                        "row": int(row_index),
                        "columns": [
                            name
                            for name in target_names
                            if bool(changed.loc[row_index, name])
                        ],
                        "before": {
                            name: before.loc[row_index, name] for name in target_names
                        },
                        "after": {
                            name: after.loc[row_index, name] for name in target_names
                        },
                    }
                )
        affected_columns.update(
            name for name in target_names if bool(changed[name].any())
        )

    pd.testing.assert_frame_equal(source, frame, check_exact=True)
    return TransformationResult(
        frame=working,
        affected_rows=tuple(sorted(affected_rows)),
        affected_columns=tuple(sorted(affected_columns)),
        sample_changes=tuple(samples),
        warnings=(),
    )
