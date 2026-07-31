# Pandera source research

Document version: `1.0.0`

Document status: `Conditional Approval`

Last researched: 2026-07-31

Phase summary: [Data, statistics and reproducibility research](../../reports/OPEN_SOURCE_RESEARCH_PHASE_3_DATA.md)

## Upstream

| Field | Verified value |
| --- | --- |
| Repository | <https://github.com/unionai-oss/pandera> |
| Default branch | `main` |
| Pinned research commit | `85cc2a16b2110d4c4b8cc7f956aab94bc53716f6` |
| Research commit date | 2026-07-30 |
| Latest release/tag | `v0.32.1` |
| License | MIT |
| License file | `LICENSE.txt` |
| Main language | Python |
| Minimum runtime | Python `>=3.10`; pandas extra requires NumPy `>=1.24.4` and pandas `>=2.1.1` at the research commit |
| Dependency manifests | `pyproject.toml`, `setup.py`, `requirements.txt`, `environment.yml` |
| Container/service requirements | None; in-process validation library |
| Test framework | Pytest, nox and ASV benchmarks |
| CI workflows | package tests, lint/type checks, documentation and release workflows |
| Maintenance status | Active; repository was not archived at the research commit |

The default branch is research evidence, not the version RECA should install.
Implementation must select a released version compatible with RECA's Python,
pandas and NumPy pins.

## Repository structure

| Path | Purpose |
| --- | --- |
| `pandera/api/` | schema, component, check and model APIs |
| `pandera/backends/` | pandas and other dataframe-engine validation backends |
| `pandera/engines/` | data-type engines and coercion behavior |
| `pandera/errors.py` | schema and aggregated validation errors |
| `pandera/extensions.py` | custom check registration |
| `tests/` | unit, integration and backend behavior tests |
| `asv_bench/` | DataFrame and Series validation benchmarks |
| `docs/` | usage, data types, checks, lazy validation and extensions |

## Core capabilities

- `DataFrameSchema`, `Column`, `Index` and model-style schemas.
- Explicit data types, nullable/coercion controls and column presence/order rules.
- Built-in and custom `Check` objects at column and dataframe scope.
- Lazy validation that aggregates failures in `SchemaErrors`.
- Structured `failure_cases` for check, column, index and failing-value detail.
- Configurable `n_failure_cases` for bounded diagnostic samples.
- pandas integration plus additional dataframe backends that RECA does not need
  to expose in P0.

## Relevant modules

P0 needs the pandas path only. RECA should wrap `DataFrameSchema`, data types,
`Check`, lazy validation and `SchemaErrors` behind a deterministic Data Quality
Service. Custom scientific rules belong in Git-managed RECA rule factories,
not in routers, ad hoc notebook code or modifications to Pandera internals.

## Dependencies

Pandera's base and optional extras support multiple dataframe ecosystems. RECA
should install only the pandas-compatible extra needed by the selected release.
Adding Polars, Spark, Ibis or other backends without a requirement would expand
the dependency and test surface without improving the M4 closed loop.

## Tests

Upstream Pytest coverage exercises schemas, coercion, data types, checks, lazy
errors, custom extensions and backend-specific behavior. ASV benchmarks cover
common schema shapes. RECA still needs golden datasets for missing values,
duplicates, mixed types, ranges, category inconsistency, constant columns,
extreme values and sensitive-field heuristics.

## Performance

Validation cost grows with dataframe size, check count and the amount of failure
detail materialized. RECA should bound upload rows/columns, use lazy validation
to produce one coherent run, cap retained failure examples, and benchmark the
exact M4 rule set. Full failing rows need not be duplicated into every issue.

## RECA current state

Pandera is planned in M4 as a deterministic quality tool. It is not currently a
formal P0 runtime dependency. `DataQualityRun`, `DataQualityIssue`,
`DatasetVersion`, approval and version lineage remain RECA-owned.

## Recommended integration mode

`DIRECT_DEPENDENCY` as the sole P0 dataframe validation runtime.

Use a small RECA validation boundary that accepts an immutable DatasetVersion,
loads a bounded dataframe, selects a versioned rule set, invokes Pandera and
normalizes results. A broad third-party Adapter framework is unnecessary, but
Pandera objects must not become API, database or frontend contracts.

## Rule-set versioning

Each `DataQualityRun` should record at least:

- RECA rule-set ID, semantic version and content hash;
- selected checks and normalized parameters;
- Pandera, pandas, NumPy and Python versions;
- input DatasetVersion and content hash;
- lazy/coercion settings and failure-sample cap;
- code/template revision used for normalization.

Changing rules creates a new rule-set version and a new run. It does not mutate
prior issues or the input DatasetVersion.

## FailureCase mapping

Normalize every actionable Pandera failure into a RECA `DataQualityIssue`:

| Pandera detail | RECA interpretation |
| --- | --- |
| schema/check identifier | stable RECA rule ID and rule-set version |
| column/index | affected field or record locator |
| check text/number | normalized rule parameters |
| failure case | bounded example value, redacted when sensitive |
| error category | RECA issue type and severity mapping |

One aggregate rule failure may create one issue with counts and bounded samples,
rather than one database row per bad cell. Preserve raw Pandera error detail as
diagnostic provenance, subject to size and privacy controls.

## What to reuse

- schema/data-type declaration and coercion controls;
- built-in and registered custom checks;
- lazy aggregation and structured failure cases;
- upstream edge-case and performance-test ideas;
- bounded failure samples for usable reports.

## What not to reuse

- Pandera schemas as stable API or persistence formats;
- automatic coercion that silently changes the original dataset;
- backend-specific objects in domain models;
- Pandera check names as the only stable scientific rule identity;
- a second P0 validation authority alongside Great Expectations.

## Domain boundary

```text
immutable DatasetVersion
-> RECA versioned rule set
-> Pandera lazy validation
-> normalized counts and bounded FailureCases
-> DataQualityRun / DataQualityIssue
-> optional CleaningPlan suggestion
```

Pandera detects candidate quality issues. Only approved RECA transformations
create a new DatasetVersion; validation never overwrites source data.

## Milestone

- M4: primary deterministic validation runtime and rule-set provenance.
- M5: reuse validated types/quality status as analysis preconditions.

## Risks

- implicit coercion can look like source-data modification;
- library upgrades can change data-type and failure-report behavior;
- unbounded failure materialization can exhaust memory or leak sensitive data;
- custom rules can become scattered and unversioned;
- Pandera and Great Expectations can drift if both execute the same P0 rules.

## Validation spike

Pin a compatible release and run representative CSV/XLSX-derived dataframes
through eager and lazy validation. Verify type behavior, nulls, mixed values,
custom dataframe checks, bounded failure samples, deterministic normalization,
memory use and exact conversion to `DataQualityIssue` without modifying input.

## Attribution requirements

Preserve the MIT license and copyright notice when distributing copied code.
Record the exact package version and research/adoption Commit. Any selectively
copied test or documentation text requires path-level source and modification
records.

## Update strategy

Pin a released Pandera/pandas/NumPy combination. Upgrade only after replaying
golden validation results, failure normalization and performance thresholds.
Rule-set versions remain independent of library versions.
