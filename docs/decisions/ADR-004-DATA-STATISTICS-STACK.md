<a id="adr-004-data-statistics-stack"></a>

# ADR-004: Use one validation runtime and deterministic statistical libraries

ADR ID: `ADR-004-DATA-STATISTICS-STACK`

## Status

Accepted on 2026-07-31

Documentation status: `Conditional Approval`

## Context

RECA requires reproducible quality checks, statistics, and figures. Running overlapping validation platforms or persisting library-native result objects would create conflicting sources of truth.

## Decision

- Pandera is the planned primary P0 dataframe validation runtime.
- Great Expectations is a design and test reference, not a second P0 runtime.
- SciPy implements supported comparisons, correlations, assumption checks, and distribution functions.
- statsmodels implements supported regression and diagnostics.
- Matplotlib performs deterministic headless rendering from approved RECA inputs.
- DVC is development-only provenance inspiration unless a later measured fixture-management need justifies adoption.
- RECA `DatasetVersion`, `DataQualityRun`, `AnalysisPlan`, `AnalysisResult`, Figure records, Artifacts, and lineage remain authoritative.

Pandera failures, SciPy/statmodels return objects and warnings, and Matplotlib outputs must be normalized into existing RECA contracts. Formal numbers may come only from deterministic program execution with recorded versions, parameters, effective rows, missing-data policy, warnings, seeds where applicable, and hashes.

## Non-substitution rules

- Great Expectations results are not RECA `DataQualityRun` authority.
- DVC state is not `DatasetVersion`.
- statsmodels textual Summary is not `AnalysisResult`.
- Matplotlib output does not independently establish a statistical result.

## Alternatives considered

- Run Pandera and Great Expectations together for P0: rejected because the duplicate rule/runtime authority adds cost and disagreement risk.
- Use model-generated calculations: rejected because formal research numbers require deterministic execution.
- Make DVC user workflow state: rejected because RECA already owns dataset and transformation lineage.

## Consequences

- Compatibility and golden-value spikes precede dependency adoption.
- Library upgrades require deterministic regression evidence.
- No Requirement, API, Schema, enum, or milestone identifier changes.

## References

- [Master plan](../source-research/OPEN_SOURCE_INTEGRATION_MASTER_PLAN.md)
- [Pandera research](../source-research/projects/pandera.md)
- [SciPy research](../source-research/projects/scipy.md)
- [statsmodels research](../source-research/projects/statsmodels.md)
- [Matplotlib research](../source-research/projects/matplotlib.md)
