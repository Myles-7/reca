# statsmodels source research

Document version: `1.0.0`

Document status: `Conditional Approval`

Last researched: 2026-07-31

Phase summary: [Data, statistics and reproducibility research](../../reports/OPEN_SOURCE_RESEARCH_PHASE_3_DATA.md)

## Upstream

| Field | Verified value |
| --- | --- |
| Repository | <https://github.com/statsmodels/statsmodels> |
| Default branch | `main` |
| Pinned research commit | `d3187f844d196de1760829820a7c872a6d6ebb1d` |
| Research commit date | 2026-07-30 |
| Latest release/tag | `v0.14.6` |
| License | BSD-3-Clause |
| License files | `LICENSE.txt`, `COPYRIGHTS.txt` |
| Main language | Python, Cython and C |
| Minimum runtime | Python `>=3.10` at the research commit |
| Dependency manifests | `pyproject.toml`, `requirements.txt`, Meson files |
| Core dependencies | NumPy, SciPy, pandas, Patsy, packaging; Formulaic support is present in current source |
| Container/service requirements | None; in-process statistical library |
| Test framework | Pytest with extensive external-reference fixtures |
| CI workflows | multi-platform package tests, lint, docs, wheels and release workflows |
| Maintenance status | Active; repository was not archived at the research commit |

## Repository structure

| Path | Purpose |
| --- | --- |
| `statsmodels/regression/linear_model.py` | OLS, linear-model results and covariance behavior |
| `statsmodels/formula/` | formula API and design-matrix integration |
| `statsmodels/stats/` | diagnostics, tests, effect and covariance helpers |
| `statsmodels/stats/diagnostic.py` | residual and specification diagnostics |
| `statsmodels/stats/outliers_influence.py` | influence and outlier measures |
| `statsmodels/regression/tests/` | regression behavior and reference-result tests |
| `examples/`, `docs/` | usage examples, generated summaries and API guidance |

## Core capabilities

For M5, statsmodels supplies ordinary least squares, fitted result objects,
coefficients, covariance, standard errors, confidence intervals, residuals,
predictions and diagnostics. It also exposes rich textual summaries intended for
human inspection.

## Relevant modules

`OLS`, `RegressionResults` and `OLSResults` are the primary P0-Full surface.
Useful diagnostics include Jarque-Bera, Breusch-Pagan and influence/outlier
helpers, but each diagnostic must be explicitly selected and interpreted by the
AnalysisPlan. RECA should not expose an arbitrary statsmodels-method picker.

## Formula API

Formula syntax is convenient, but it can hide categorical encoding, intercepts,
interaction expansion, missing-row removal and column order. If formulas are
allowed, persist:

- original formula text and parser/backend version;
- variable-role mapping and categorical reference levels;
- expanded design-matrix column names and order;
- exact included-row identity/effective N;
- contrast/encoding choices and missing-data behavior.

For the P0 simple-linear-regression path, an explicit design matrix may be
easier to validate and reproduce than a general formula interface.

## Missing data

The model default can be `missing="none"`, leaving NaNs to produce unusable
results. `missing="drop"` can silently change the sample. RECA should validate
missingness before fitting and use explicit `raise` or a reviewed preprocessing
policy. Any excluded rows and effective N belong in `AnalysisResult` provenance.

## Result objects

Stable documented attributes such as parameters, standard errors, p-values,
confidence intervals, residual diagnostics, degrees of freedom and fit measures
should be normalized into RECA fields. Do not parse HTML/text tables.

```text
statsmodels textual Summary
!=
RECA AnalysisResult
```

`Summary` may be retained as a display/debug Artifact. It is neither a durable
schema nor the source of formal values.

## Dependencies

statsmodels depends on a compatible NumPy/SciPy/pandas stack and formula
libraries. RECA should pin this numerical set together and avoid optional
features outside the approved M5 method list.

## Tests

Upstream regression tests compare results against R, Stata, Gretl and other
reference fixtures and cover fitting, covariance, prediction, missing data and
summary output. RECA needs an independent simple-regression golden set covering
known coefficients, confidence intervals, perfect/near-perfect fits, constants,
missing rows, leverage and repeated-run equality.

## Operational requirements

- approved immutable input version and explicit design matrix;
- pinned numerical and formula dependency versions;
- stored method/options, included rows and diagnostics;
- no untrusted pickles or model objects loaded from user files;
- bounded Worker resources and structured warning capture.

## RECA current state

statsmodels is planned in M5 for deterministic regression. It is not implemented
by this research. `AnalysisPlan`, `AnalysisRun`, `AnalysisResult`, approval and
invalidation remain RECA-owned.

## Recommended integration mode

`DIRECT_DEPENDENCY`

Use a method-specific RECA StatisticalEngine function for simple linear
regression. A generic Adapter is unnecessary, but normalization is mandatory so
statsmodels objects, formulas and summaries never become stable contracts.

## What to reuse

- OLS fitting and documented numerical result attributes;
- confidence intervals, covariance and selected diagnostics;
- external-reference and edge-case testing approaches;
- optional textual Summary as a non-authoritative diagnostic Artifact.

## What not to reuse

- textual or HTML Summary as `AnalysisResult`;
- pickled fitted objects as the sole reproducibility record;
- silent missing-row dropping;
- arbitrary formula/model execution selected by user or model text;
- every available diagnostic as an automatic P0 requirement.

## Domain boundary

```text
APPROVED AnalysisPlan + DatasetVersion
-> RECA design-matrix and missing-data validation
-> statsmodels OLS fit
-> documented attributes and warnings
-> immutable RECA AnalysisResult
-> optional Summary Artifact
```

## Milestone

- M5 P0-Full: `SIMPLE_LINEAR_REGRESSION`.
- Later milestones may add methods only through formal scope and contract review.

## Risks

- formula expansion or missing handling changing effective data silently;
- summary text drifting between releases/locales;
- result objects being serialized instead of normalized;
- diagnostics being interpreted as automatic proof of model validity;
- version mismatch across NumPy, SciPy, pandas and statsmodels.

## Validation spike

Fit one explicit-design and one formula model against golden data. Compare
coefficients, standard errors, p-values, CIs, predictions, residual diagnostics
and included rows. Force missing/constant/near-singular cases, verify warnings,
and prove that structured output does not depend on Summary formatting.

## Attribution requirements

Preserve BSD-3-Clause and copyright notices for distributed code. Record the
exact package version. Copied test data or external reference fixtures require
their own provenance and license check.

## Update strategy

Pin statsmodels with its tested numerical stack. Upgrades must replay golden
regression fixtures and compare structured attributes, row inclusion, warnings
and formula expansion. Summary formatting changes alone do not require a domain
migration because Summary is non-authoritative.
