from __future__ import annotations

import math
import warnings
from collections import Counter
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
import statsmodels.api as sm  # type: ignore[import-untyped]
from scipy import stats  # type: ignore[import-untyped]

from app.analysis.registry import require_supported
from app.analysis.schemas import (
    AssumptionDTO,
    EngineOutput,
    EngineRequest,
    ResultDTO,
)
from app.models import AnalysisMethod, AnalysisResultType, AssumptionCheckCode

MIN_CORRELATION_N = 3
MIN_GROUP_N = 2
MIN_REGRESSION_N = 3


def _finite(value: Any) -> float | None:
    try:
        number = float(value)
    except TypeError, ValueError:
        return None
    return number if math.isfinite(number) else None


def _numeric_summary(series: pd.Series, *, confidence_level: float) -> dict[str, Any]:
    numeric = pd.to_numeric(series, errors="coerce")
    values = numeric[np.isfinite(numeric.to_numpy(dtype=float))]
    n = int(values.size)
    missing = int(series.size - n)
    mean = _finite(values.mean()) if n else None
    sd = _finite(values.std(ddof=1)) if n >= 2 else None
    ci: dict[str, float | None] = {
        "lower": None,
        "upper": None,
        "level": confidence_level,
    }
    if n >= 2 and sd is not None and mean is not None:
        critical = float(stats.t.ppf((1.0 + confidence_level) / 2.0, n - 1))
        margin = critical * sd / math.sqrt(n)
        ci = {
            "lower": _finite(mean - margin),
            "upper": _finite(mean + margin),
            "level": confidence_level,
        }
    quantiles = (
        values.quantile([0.25, 0.5, 0.75], interpolation="linear") if n else None
    )
    return {
        "n": n,
        "missing_n": missing,
        "mean": mean,
        "standard_deviation": sd,
        "minimum": _finite(values.min()) if n else None,
        "q1": _finite(quantiles.loc[0.25]) if quantiles is not None else None,
        "median": _finite(quantiles.loc[0.5]) if quantiles is not None else None,
        "q3": _finite(quantiles.loc[0.75]) if quantiles is not None else None,
        "maximum": _finite(values.max()) if n else None,
        "mean_confidence_interval": ci,
    }


def _categorical_summary(series: pd.Series) -> dict[str, Any]:
    values = [value for value in series.tolist() if not pd.isna(value)]
    counts = Counter(str(value) for value in values)
    n = len(values)
    categories = [
        {"value": key, "count": count, "proportion": count / n if n else None}
        for key, count in sorted(counts.items())
    ]
    return {"n": n, "missing_n": int(series.size - n), "categories": categories}


def _common_assumptions(
    frame: pd.DataFrame, request: EngineRequest
) -> list[AssumptionDTO]:
    checks: list[AssumptionDTO] = []
    for index, column in enumerate(request.columns):
        series = frame[column.name]
        numeric_required = request.method != AnalysisMethod.DESCRIPTIVE_STATISTICS
        if request.method == AnalysisMethod.INDEPENDENT_TWO_GROUP and index == 0:
            numeric_required = False
        if request.method == AnalysisMethod.PAIRED_TWO_GROUP and index == 2:
            numeric_required = False
        type_ok = (
            column.kind == "numeric"
            if numeric_required
            else column.kind in {"numeric", "categorical"}
        )
        checks.append(
            AssumptionDTO(
                check_code="DATA_TYPE",
                status="PASSED" if type_ok else "FAILED",
                subject_key=str(column.column_id),
                explanation="The confirmed column type is supported."
                if type_ok
                else "The method requires confirmed numeric columns.",
                evidence={"kind": column.kind},
                blocks_approval=not type_ok,
            )
        )
        missing_n = int(series.isna().sum())
        checks.append(
            AssumptionDTO(
                check_code="MISSINGNESS",
                status="WARNING" if missing_n else "PASSED",
                subject_key=str(column.column_id),
                explanation="Missing values are handled by the declared policy.",
                evidence={"missing_n": missing_n, "total_n": int(series.size)},
            )
        )
        non_missing = series.dropna()
        constant = non_missing.nunique(dropna=True) <= 1
        constant_blocks = constant and (
            request.method != AnalysisMethod.DESCRIPTIVE_STATISTICS
            and not (request.method == AnalysisMethod.PAIRED_TWO_GROUP and index == 2)
        )
        checks.append(
            AssumptionDTO(
                check_code="CONSTANT",
                status="FAILED" if constant else "PASSED",
                subject_key=str(column.column_id),
                explanation="The column is constant."
                if constant
                else "The column contains variation.",
                evidence={"unique_n": int(non_missing.nunique(dropna=True))},
                blocks_approval=constant_blocks,
            )
        )
    return checks


def validate(frame: pd.DataFrame, request: EngineRequest) -> list[AssumptionDTO]:
    require_supported(request.method)
    checks = _common_assumptions(frame, request)
    selected = [column.name for column in request.columns]
    effective = frame[selected].dropna()
    minimum = 1 if request.method == AnalysisMethod.DESCRIPTIVE_STATISTICS else 3
    effective_n = (
        max((int(frame[name].notna().sum()) for name in selected), default=0)
        if request.method == AnalysisMethod.DESCRIPTIVE_STATISTICS
        and request.missing_data_policy.mode.value == "PAIRWISE_COMPLETE"
        else len(effective)
    )
    ok = effective_n >= minimum
    checks.append(
        AssumptionDTO(
            check_code="SAMPLE_SIZE",
            status="PASSED" if ok else "FAILED",
            explanation="Effective sample size meets the method minimum."
            if ok
            else "Effective sample size is below the method minimum.",
            evidence={"effective_n": effective_n, "minimum_n": minimum},
            blocks_approval=not ok,
        )
    )
    correlation = request.method in {
        AnalysisMethod.PEARSON_CORRELATION,
        AnalysisMethod.SPEARMAN_CORRELATION,
    }
    linearity_confirmed = (
        AssumptionCheckCode.LINEARITY in request.parameters.assumption_confirmations
    )
    checks.append(
        AssumptionDTO(
            check_code="LINEARITY",
            status=(
                "PASSED"
                if request.method == AnalysisMethod.PEARSON_CORRELATION
                and linearity_confirmed
                else "REQUIRES_USER_CONFIRMATION"
                if request.method == AnalysisMethod.PEARSON_CORRELATION
                else "NOT_APPLICABLE"
            ),
            explanation=(
                "The user confirmed that a linear summary is appropriate."
                if request.method == AnalysisMethod.PEARSON_CORRELATION
                and linearity_confirmed
                else "Pearson correlation requires the user to confirm that a linear summary is appropriate."
                if request.method == AnalysisMethod.PEARSON_CORRELATION
                else "Linearity is not a blocking assumption for this method."
            ),
            blocks_approval=request.method == AnalysisMethod.PEARSON_CORRELATION
            and not linearity_confirmed,
        )
    )
    checks.append(
        AssumptionDTO(
            check_code="OUTLIER_INFLUENCE",
            status="WARNING" if correlation else "NOT_APPLICABLE",
            explanation="Correlation can be influenced by outliers; inspect the recorded data-quality context."
            if correlation
            else "Outlier influence is not separately evaluated for this summary.",
        )
    )
    if request.method == AnalysisMethod.INDEPENDENT_TWO_GROUP:
        group = frame[selected[0]].dropna()
        groups = sorted(str(value) for value in group.unique())
        group_counts = group.astype(str).value_counts()
        valid = (
            len(groups) == 2
            and bool((group_counts >= MIN_GROUP_N).all())
            and request.parameters.independence_confirmed
        )
        equal_confirmed = (
            AssumptionCheckCode.VARIANCE_HOMOGENEITY
            in request.parameters.assumption_confirmations
        )
        checks.extend(
            [
                AssumptionDTO(
                    check_code="NORMALITY",
                    status="WARNING",
                    explanation="Group comparison records normality as a review warning.",
                ),
                AssumptionDTO(
                    check_code="VARIANCE_HOMOGENEITY",
                    status=(
                        "REQUIRES_USER_CONFIRMATION"
                        if request.parameters.variance_mode.value == "EQUAL"
                        and not equal_confirmed
                        else "WARNING"
                    ),
                    explanation="Equal-variance mode requires explicit justification; Welch remains robust to unequal variances.",
                    blocks_approval=(
                        request.parameters.variance_mode.value == "EQUAL"
                        and not equal_confirmed
                    ),
                    evidence={"groups": groups, "group_counts": group_counts.to_dict()},
                ),
                AssumptionDTO(
                    check_code="PAIRING_VALIDITY",
                    status="NOT_APPLICABLE",
                    explanation="Independent comparison does not use paired observations.",
                ),
            ]
        )
        if not valid:
            checks.append(
                AssumptionDTO(
                    check_code="SAMPLE_SIZE",
                    status="FAILED",
                    explanation="Exactly two independent groups and confirmation are required.",
                    evidence={"group_count": len(groups)},
                    blocks_approval=True,
                )
            )
    elif request.method == AnalysisMethod.PAIRED_TWO_GROUP:
        pair_ids = frame[selected[2]]
        valid = (
            request.parameters.pairing_confirmed
            and pair_ids.notna().all()
            and not pair_ids.duplicated().any()
        )
        checks.extend(
            [
                AssumptionDTO(
                    check_code="PAIRING_VALIDITY",
                    status="PASSED" if valid else "FAILED",
                    explanation="Pair identifiers are complete and unique."
                    if valid
                    else "Pair identifiers must be complete, unique and confirmed.",
                    evidence={
                        "pair_n": int(pair_ids.notna().sum()),
                        "duplicate_n": int(pair_ids.duplicated().sum()),
                    },
                    blocks_approval=not valid,
                ),
                AssumptionDTO(
                    check_code="NORMALITY",
                    status="WARNING",
                    explanation="Normality of paired differences requires review.",
                ),
                AssumptionDTO(
                    check_code="VARIANCE_HOMOGENEITY",
                    status="NOT_APPLICABLE",
                    explanation="Paired comparison does not require equal group variances.",
                ),
            ]
        )
    elif request.method == AnalysisMethod.SIMPLE_LINEAR_REGRESSION:
        checks.extend(
            [
                AssumptionDTO(
                    check_code="RESIDUAL_DIAGNOSTIC",
                    status="WARNING",
                    explanation="Residual normality and homoscedasticity require review.",
                ),
                AssumptionDTO(
                    check_code="OUTLIER_INFLUENCE",
                    status="WARNING",
                    explanation="Regression influence diagnostics are recorded with the result.",
                ),
            ]
        )
    return checks


def _alternative(value: str) -> str:
    return {"TWO_SIDED": "two-sided", "LESS": "less", "GREATER": "greater"}[value]


def _comparison_ci(
    estimate: float, standard_error: float, df: float, level: float
) -> dict[str, float | None]:
    critical = float(stats.t.ppf((1.0 + level) / 2.0, df))
    return {
        "lower": _finite(estimate - critical * standard_error),
        "upper": _finite(estimate + critical * standard_error),
        "level": level,
    }


def _independent(frame: pd.DataFrame, request: EngineRequest) -> EngineOutput:
    group_name, outcome_name = (column.name for column in request.columns[:2])
    scoped = frame[[group_name, outcome_name]].dropna().copy()
    scoped[outcome_name] = pd.to_numeric(scoped[outcome_name], errors="coerce")
    scoped = scoped[np.isfinite(scoped[outcome_name].to_numpy(dtype=float))]
    labels = sorted(scoped[group_name].astype(str).unique().tolist())
    if len(labels) != 2:
        raise ValueError("Independent comparison requires exactly two groups")
    first = scoped.loc[scoped[group_name].astype(str) == labels[0], outcome_name]
    second = scoped.loc[scoped[group_name].astype(str) == labels[1], outcome_name]
    if len(first) < MIN_GROUP_N or len(second) < MIN_GROUP_N:
        raise ValueError("Each independent group requires at least two observations")
    equal_var = request.parameters.variance_mode.value == "EQUAL"
    outcome = stats.ttest_ind(
        first,
        second,
        equal_var=equal_var,
        alternative=_alternative(request.parameters.alternative.value),
    )
    statistic = _finite(outcome.statistic)
    p_value = _finite(outcome.pvalue)
    df = _finite(outcome.df)
    if statistic is None or p_value is None or df is None:
        raise ValueError("External statistical output was non-finite")
    mean_difference = float(first.mean() - second.mean())
    if equal_var:
        pooled_variance = (
            (len(first) - 1) * first.var(ddof=1)
            + (len(second) - 1) * second.var(ddof=1)
        ) / df
        standard_error = math.sqrt(
            pooled_variance * (1.0 / len(first) + 1.0 / len(second))
        )
        pooled_sd = math.sqrt(pooled_variance)
    else:
        standard_error = math.sqrt(
            first.var(ddof=1) / len(first) + second.var(ddof=1) / len(second)
        )
        pooled_sd = math.sqrt((first.var(ddof=1) + second.var(ddof=1)) / 2.0)
    effect = mean_difference / pooled_sd if pooled_sd > 0 else None
    assumptions = validate(frame, request)
    return EngineOutput(
        effective_n=len(scoped),
        assumptions=assumptions,
        warnings=["GROUP_COMPARISON_DOES_NOT_ESTABLISH_CAUSALITY"],
        results=[
            ResultDTO(
                result_key="group_comparison",
                result_type=AnalysisResultType.GROUP_COMPARISON.value,
                is_primary=True,
                payload={
                    "group_column_id": str(request.columns[0].column_id),
                    "outcome_column_id": str(request.columns[1].column_id),
                    "groups": [
                        {
                            "label": labels[0],
                            "n": len(first),
                            "mean": _finite(first.mean()),
                        },
                        {
                            "label": labels[1],
                            "n": len(second),
                            "mean": _finite(second.mean()),
                        },
                    ],
                    "mean_difference": _finite(mean_difference),
                    "statistic": statistic,
                    "df": df,
                    "p_value": p_value,
                    "confidence_interval": _comparison_ci(
                        mean_difference,
                        standard_error,
                        df,
                        request.parameters.confidence_level,
                    ),
                    "effect_size": {"name": "cohen_d", "value": _finite(effect)},
                    "variance_mode": request.parameters.variance_mode.value,
                    "alternative": request.parameters.alternative.value,
                    "effective_n": len(scoped),
                    "missing_n": int(len(frame) - len(scoped)),
                },
            )
        ],
    )


def _paired(frame: pd.DataFrame, request: EngineRequest) -> EngineOutput:
    first_name, second_name, pair_name = (column.name for column in request.columns[:3])
    scoped = frame[[first_name, second_name, pair_name]].dropna().copy()
    if scoped[pair_name].duplicated().any():
        raise ValueError("Pair identifiers must be unique")
    first = pd.to_numeric(scoped[first_name], errors="coerce")
    second = pd.to_numeric(scoped[second_name], errors="coerce")
    finite = np.isfinite(first.to_numpy(dtype=float)) & np.isfinite(
        second.to_numpy(dtype=float)
    )
    first, second = first[finite], second[finite]
    if len(first) < MIN_GROUP_N:
        raise ValueError("Paired comparison requires at least two complete pairs")
    outcome = stats.ttest_rel(
        first,
        second,
        alternative=_alternative(request.parameters.alternative.value),
    )
    statistic, p_value = _finite(outcome.statistic), _finite(outcome.pvalue)
    df = float(len(first) - 1)
    if statistic is None or p_value is None:
        raise ValueError("External statistical output was non-finite")
    differences = first.to_numpy(dtype=float) - second.to_numpy(dtype=float)
    mean_difference = float(np.mean(differences))
    sd_difference = float(np.std(differences, ddof=1))
    standard_error = sd_difference / math.sqrt(len(differences))
    effect = mean_difference / sd_difference if sd_difference > 0 else None
    return EngineOutput(
        effective_n=len(first),
        assumptions=validate(frame, request),
        warnings=["PAIRED_COMPARISON_REQUIRES_CONFIRMED_PAIR_SEMANTICS"],
        results=[
            ResultDTO(
                result_key="paired_comparison",
                result_type=AnalysisResultType.GROUP_COMPARISON.value,
                is_primary=True,
                payload={
                    "first_column_id": str(request.columns[0].column_id),
                    "second_column_id": str(request.columns[1].column_id),
                    "pair_id_column_id": str(request.columns[2].column_id),
                    "pair_n": len(first),
                    "mean_first": _finite(first.mean()),
                    "mean_second": _finite(second.mean()),
                    "mean_difference": _finite(mean_difference),
                    "statistic": statistic,
                    "df": df,
                    "p_value": p_value,
                    "confidence_interval": _comparison_ci(
                        mean_difference,
                        standard_error,
                        df,
                        request.parameters.confidence_level,
                    ),
                    "effect_size": {"name": "cohen_dz", "value": _finite(effect)},
                    "alternative": request.parameters.alternative.value,
                    "effective_n": len(first),
                    "missing_n": int(len(frame) - len(first)),
                },
            )
        ],
    )


def _regression(frame: pd.DataFrame, request: EngineRequest) -> EngineOutput:
    x_name, y_name = (column.name for column in request.columns[:2])
    scoped = frame[[x_name, y_name]].dropna().copy()
    x = pd.to_numeric(scoped[x_name], errors="coerce")
    y = pd.to_numeric(scoped[y_name], errors="coerce")
    finite = np.isfinite(x.to_numpy(dtype=float)) & np.isfinite(y.to_numpy(dtype=float))
    x, y = x[finite], y[finite]
    if len(x) < MIN_REGRESSION_N or x.nunique() <= 1:
        raise ValueError(
            "Regression requires at least three observations and non-constant X"
        )
    design = sm.add_constant(x.to_numpy(dtype=float), has_constant="add")
    fitted = sm.OLS(y.to_numpy(dtype=float), design, missing="raise").fit()
    interval = fitted.conf_int(alpha=1.0 - request.parameters.confidence_level)
    values = [
        *fitted.params,
        *fitted.bse,
        *fitted.pvalues,
        *interval.ravel(),
        fitted.rsquared,
    ]
    if any(_finite(value) is None for value in values):
        raise ValueError("External statistical output was non-finite")
    influence = fitted.get_influence()
    max_cooks = _finite(np.max(influence.cooks_distance[0]))
    residuals = fitted.resid
    return EngineOutput(
        effective_n=len(x),
        assumptions=validate(frame, request),
        warnings=["REGRESSION_ASSOCIATION_DOES_NOT_ESTABLISH_CAUSALITY"],
        results=[
            ResultDTO(
                result_key="regression",
                result_type=AnalysisResultType.REGRESSION.value,
                is_primary=True,
                payload={
                    "x_column_id": str(request.columns[0].column_id),
                    "y_column_id": str(request.columns[1].column_id),
                    "effective_n": len(x),
                    "missing_n": int(len(frame) - len(x)),
                    "intercept": {
                        "coefficient": _finite(fitted.params[0]),
                        "standard_error": _finite(fitted.bse[0]),
                        "p_value": _finite(fitted.pvalues[0]),
                        "confidence_interval": {
                            "lower": _finite(interval[0, 0]),
                            "upper": _finite(interval[0, 1]),
                            "level": request.parameters.confidence_level,
                        },
                    },
                    "slope": {
                        "coefficient": _finite(fitted.params[1]),
                        "standard_error": _finite(fitted.bse[1]),
                        "p_value": _finite(fitted.pvalues[1]),
                        "confidence_interval": {
                            "lower": _finite(interval[1, 0]),
                            "upper": _finite(interval[1, 1]),
                            "level": request.parameters.confidence_level,
                        },
                    },
                    "r_squared": _finite(fitted.rsquared),
                    "diagnostics": {
                        "residual_mean": _finite(np.mean(residuals)),
                        "residual_standard_deviation": _finite(
                            np.std(residuals, ddof=1)
                        ),
                        "maximum_cooks_distance": max_cooks,
                    },
                },
            )
        ],
    )


def execute(frame: pd.DataFrame, request: EngineRequest) -> EngineOutput:
    require_supported(request.method)
    if request.method == AnalysisMethod.INDEPENDENT_TWO_GROUP:
        return _independent(frame, request)
    if request.method == AnalysisMethod.PAIRED_TWO_GROUP:
        return _paired(frame, request)
    if request.method == AnalysisMethod.SIMPLE_LINEAR_REGRESSION:
        return _regression(frame, request)
    selected = [column.name for column in request.columns]
    scoped = frame[selected].copy()
    if (
        request.method == AnalysisMethod.DESCRIPTIVE_STATISTICS
        and request.missing_data_policy.mode.value == "COMPLETE_CASE"
    ):
        scoped = scoped.dropna()
    assumptions = validate(scoped, request)
    if any(
        check.blocks_approval
        and check.status in {"FAILED", "UNKNOWN", "REQUIRES_USER_CONFIRMATION"}
        for check in assumptions
    ):
        raise ValueError("Analysis assumptions contain a blocking failure")
    output_warnings: list[str] = []
    if request.method == AnalysisMethod.DESCRIPTIVE_STATISTICS:
        results: list[ResultDTO] = []
        effective_n = 0
        for column in request.columns:
            if column.kind == "numeric":
                payload = _numeric_summary(
                    scoped[column.name],
                    confidence_level=request.parameters.confidence_level,
                )
                result_type = AnalysisResultType.DESCRIPTIVE_NUMERIC
            else:
                payload = _categorical_summary(scoped[column.name])
                result_type = AnalysisResultType.DESCRIPTIVE_CATEGORICAL
            effective_n = max(effective_n, int(payload["n"]))
            results.append(
                ResultDTO(
                    result_key=str(column.column_id),
                    result_type=result_type.value,
                    is_primary=len(results) == 0,
                    payload={
                        "column_id": str(column.column_id),
                        "column_name": column.name,
                        **payload,
                    },
                )
            )
        return EngineOutput(
            effective_n=effective_n,
            results=results,
            assumptions=assumptions,
            warnings=output_warnings,
        )

    complete = scoped.dropna()
    x = pd.to_numeric(complete.iloc[:, 0], errors="coerce")
    y = pd.to_numeric(complete.iloc[:, 1], errors="coerce")
    finite_mask = np.isfinite(x.to_numpy(dtype=float)) & np.isfinite(
        y.to_numpy(dtype=float)
    )
    x = x[finite_mask]
    y = y[finite_mask]
    if len(x) < MIN_CORRELATION_N:
        raise ValueError("Effective sample size is below the correlation minimum")
    captured: list[warnings.WarningMessage]
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        if request.method == AnalysisMethod.PEARSON_CORRELATION:
            outcome = stats.pearsonr(x, y)
            coefficient = _finite(outcome.statistic)
            p_value = _finite(outcome.pvalue)
            try:
                interval = outcome.confidence_interval(
                    request.parameters.confidence_level
                )
                confidence_interval = {
                    "lower": _finite(interval.low),
                    "upper": _finite(interval.high),
                    "level": request.parameters.confidence_level,
                }
            except ValueError:
                confidence_interval = {
                    "lower": None,
                    "upper": None,
                    "level": request.parameters.confidence_level,
                }
        else:
            outcome = stats.spearmanr(x, y)
            coefficient = _finite(outcome.statistic)
            p_value = _finite(outcome.pvalue)
            confidence_interval = {
                "lower": None,
                "upper": None,
                "level": request.parameters.confidence_level,
            }
    for warning in captured:
        output_warnings.append(f"SCIPY_WARNING:{warning.category.__name__}")
    if coefficient is None or p_value is None:
        raise ValueError("External statistical output was non-finite")
    payload = {
        "coefficient": coefficient,
        "p_value": p_value,
        "confidence_interval": confidence_interval,
        "effective_n": len(x),
        "missing_n": int(len(scoped) - len(x)),
        "x_column_id": str(request.columns[0].column_id),
        "y_column_id": str(request.columns[1].column_id),
        "alternative": "two-sided",
    }
    output_warnings.append("CORRELATION_DOES_NOT_SUPPORT_CAUSAL_INFERENCE")
    return EngineOutput(
        effective_n=len(x),
        assumptions=assumptions,
        warnings=output_warnings,
        results=[
            ResultDTO(
                result_key="correlation",
                result_type=AnalysisResultType.CORRELATION.value,
                is_primary=True,
                payload=payload,
            )
        ],
    )
