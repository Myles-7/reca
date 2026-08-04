from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any

from app.api.errors import ContractError
from app.models import DataQualityIssueType, DataQualitySeverity


@dataclass(frozen=True)
class RuleDefinition:
    rule_id: str
    issue_type: DataQualityIssueType
    severity: DataQualitySeverity
    parameters: dict[str, Any]
    wording_version: str = "1.0"


@dataclass(frozen=True)
class RuleSet:
    ruleset_id: str
    version: str
    rules: tuple[RuleDefinition, ...]

    @property
    def content_hash(self) -> str:
        payload = {
            "ruleset_id": self.ruleset_id,
            "version": self.version,
            "rules": [
                {
                    **asdict(rule),
                    "issue_type": rule.issue_type.value,
                    "severity": rule.severity.value,
                }
                for rule in self.rules
            ],
        }
        canonical = json.dumps(
            payload,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


RECA_P0_DEFAULT = RuleSet(
    ruleset_id="RECA_P0_DEFAULT",
    version="1.0.0",
    rules=(
        RuleDefinition(
            "MISSING_VALUE",
            DataQualityIssueType.MISSING_VALUE,
            DataQualitySeverity.MEDIUM,
            {"default_missing_codes": ["NA", "N/A", "NULL", "MISSING"]},
        ),
        RuleDefinition(
            "DUPLICATE_ROW",
            DataQualityIssueType.DUPLICATE_ROW,
            DataQualitySeverity.MEDIUM,
            {"keep": False},
        ),
        RuleDefinition(
            "DUPLICATE_CONFIRMED_ID",
            DataQualityIssueType.DUPLICATE_ID,
            DataQualitySeverity.HIGH,
            {"requires_confirmed_identifier": True},
        ),
        RuleDefinition(
            "CONSTANT_COLUMN",
            DataQualityIssueType.CONSTANT_COLUMN,
            DataQualitySeverity.INFO,
            {"minimum_non_missing": 1},
        ),
        RuleDefinition(
            "MIXED_TYPE",
            DataQualityIssueType.MIXED_TYPE,
            DataQualitySeverity.HIGH,
            {"incompatible_families": ["numeric", "date", "boolean", "text"]},
        ),
        RuleDefinition(
            "CATEGORY_INCONSISTENCY",
            DataQualityIssueType.CATEGORY_INCONSISTENCY,
            DataQualitySeverity.MEDIUM,
            {"max_cardinality": 100, "normalization": "trim_casefold"},
        ),
        RuleDefinition(
            "HEURISTIC_OUT_OF_RANGE",
            DataQualityIssueType.OUT_OF_RANGE,
            DataQualitySeverity.MEDIUM,
            {
                "ranges": {
                    "age": [0, 120],
                    "percent": [0, 100],
                    "percentage": [0, 100],
                    "score": [0, 100],
                },
                "heuristic": True,
            },
        ),
        RuleDefinition(
            "IQR_EXTREME_VALUE_CLUE",
            DataQualityIssueType.EXTREME_VALUE,
            DataQualitySeverity.INFO,
            {"iqr_multiplier": 1.5, "minimum_values": 4},
        ),
        RuleDefinition(
            "GROUP_IMBALANCE_CLUE",
            DataQualityIssueType.GROUP_IMBALANCE,
            DataQualitySeverity.INFO,
            {"minimum_values": 10, "dominant_ratio": 0.8},
        ),
        RuleDefinition(
            "SUSPICIOUS_UNIT",
            DataQualityIssueType.SUSPICIOUS_UNIT,
            DataQualitySeverity.MEDIUM,
            {"suffix_units": {"kg": "kg", "cm": "cm", "mm": "mm", "ms": "ms"}},
        ),
        RuleDefinition(
            "INVALID_DATE",
            DataQualityIssueType.INVALID_DATE,
            DataQualitySeverity.HIGH,
            {"name_tokens": ["date", "time", "日期", "时间"]},
        ),
        RuleDefinition(
            "POSSIBLE_SENSITIVE_FIELD",
            DataQualityIssueType.POSSIBLE_SENSITIVE_FIELD,
            DataQualitySeverity.MEDIUM,
            {
                "name_tokens": [
                    "email",
                    "phone",
                    "mobile",
                    "id_card",
                    "student_id",
                    "student_number",
                    "邮箱",
                    "电话",
                    "身份证",
                    "学号",
                ],
                "patterns": ["email", "phone", "id_card", "student_number"],
            },
        ),
    ),
)

_REGISTRY = {RECA_P0_DEFAULT.ruleset_id: RECA_P0_DEFAULT}


def get_ruleset(ruleset_id: str) -> RuleSet:
    try:
        return _REGISTRY[ruleset_id]
    except KeyError as exc:
        raise ContractError(
            status_code=422,
            code="QUALITY_RULESET_NOT_FOUND",
            message="The requested data quality rule set is not available.",
        ) from exc


def select_ruleset(
    ruleset_id: str, *, include_sensitive_field_detection: bool
) -> RuleSet:
    base = get_ruleset(ruleset_id)
    if include_sensitive_field_detection:
        return base
    return RuleSet(
        ruleset_id=base.ruleset_id,
        version=base.version,
        rules=tuple(
            rule
            for rule in base.rules
            if rule.issue_type != DataQualityIssueType.POSSIBLE_SENSITIVE_FIELD
        ),
    )


def resolve_persisted_ruleset(
    *, ruleset_id: str, version: str, content_hash: str
) -> tuple[RuleSet, bool]:
    for include_sensitive in (True, False):
        candidate = select_ruleset(
            ruleset_id,
            include_sensitive_field_detection=include_sensitive,
        )
        if candidate.version == version and candidate.content_hash == content_hash:
            return candidate, include_sensitive
    raise ContractError(
        status_code=409,
        code="QUALITY_RULESET_STALE",
        message="The persisted quality rule set identity is not executable.",
    )
