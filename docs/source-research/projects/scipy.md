# SciPy source research

Document version: `1.0.1`

Document status: `APPROVED FOR M1 DEVELOPMENT`

Research status: `PLANNED`

Last researched: 2026-07-31

Last updated: 2026-07-31

Phase summary: [Data, statistics and reproducibility research](../../archive/open-source-research/OPEN_SOURCE_RESEARCH_PHASE_3_DATA.md)

## Upstream

| Field | Verified value |
| --- | --- |
| Repository | <https://github.com/scipy/scipy> |
| Default branch | `main` |
| Pinned research commit | `420a778219f6db170f0fda8dcda4add8a32fd1d6` |
| Research commit date | 2026-07-30 |
| Latest release/tag | `v1.18.0` |
| License | BSD-3-Clause, with separately listed bundled licenses |
| License files | `LICENSE.txt`, `LICENSES_bundled.txt` |
| Main language | Python, C, C++, Fortran and Cython |
| Minimum runtime | Default branch: Python `>=3.12`, NumPy `>=2.0.0`; select a RECA-compatible release |
| Build/dependency manifests | `pyproject.toml`, Meson files, `requirements/`, `subprojects/` |
| Container/service requirements | None; compiled in-process numerical library |
| Test framework | Pytest and ASV benchmarks |
| CI workflows | multi-platform builds/tests, lint, docs, wheels and release automation |
| Maintenance status | Active; repository was not archived at the research commit |

## Repository structure

| Path | Purpose |
| --- | --- |
| `scipy/stats/` | statistical tests, distributions, correlations and result types |
| `scipy/_lib/` | shared utilities, warnings and array behavior |
| `scipy/stats/tests/` | reference, regression and edge-case tests |
| `benchmarks/benchmarks/stats.py` | statistical performance benchmarks |
| `doc/` | API reference, release notes and statistical guidance |
| `meson.build`, `subprojects/` | compiled build configuration and vendored build inputs |

## Core capabilities

For RECA P0, `scipy.stats` provides independent and paired comparisons,
Pearson/Spearman correlation, distributions, normality checks, variance checks,
confidence intervals and explicit warnings for degenerate inputs.

## P0 method mapping

| RECA analysis | SciPy function | Required RECA controls |
| --- | --- | --- |
| Independent comparison | `scipy.stats.ttest_ind` | alternative, equal-variance choice, missing policy, effective N |
| Paired comparison | `scipy.stats.ttest_rel` | pairing validation, alternative, missing policy, effective N |
| Pearson correlation | `scipy.stats.pearsonr` | constant/near-constant handling and confidence interval method |
| Spearman correlation | `scipy.stats.spearmanr` | rank/tie behavior, missing policy and matrix-output normalization |
| Normality check | `shapiro` or `normaltest` | method selected by AnalysisPlan and sample-size rule |
| Variance homogeneity | `levene` | center choice and group/sample validation |

Descriptive statistics may use NumPy/pandas and selected SciPy functions, but
must be normalized through the same RECA StatisticalEngine boundary.

## Relevant behavior

- `nan_policy` commonly supports `propagate`, `omit` and `raise`; RECA must set
  it explicitly per AnalysisPlan instead of accepting an accidental default.
- result objects expose named statistics and p-values; several expose confidence
  interval helpers. RECA should read documented attributes, not parse repr text.
- `ConstantInputWarning`, `NearConstantInputWarning` and `SmallSampleWarning`
  must become structured method warnings or validation failures.
- resampling and random-distribution operations require an explicit seed/RNG
  record. P0 fixed tests should avoid randomness unless the method requires it.
- array axis and shape behavior must be normalized before persistence.

## Dependencies

SciPy depends tightly on a compatible NumPy and Python range and ships compiled
artifacts. RECA should prefer official wheels for its deployment platforms and
test the exact Python/NumPy/SciPy matrix. Default-branch minimums do not justify
upgrading the application runtime in this research phase.

## Tests

Upstream tests compare reference values and cover `axis`, `nan_policy`, small
samples, constants, alternative hypotheses and result objects. RECA needs an
independent golden set for exact P0 methods, including perfect correlations,
near-zero correlation, missing data, insufficient N, paired mismatch and
warning capture. `benchmarks/benchmarks/stats.py` includes `ttest_ind` coverage.

## Operational requirements

- deterministic input arrays derived from an approved DatasetVersion;
- pinned Python, NumPy and SciPy versions;
- explicit missing, alternative, variance and confidence-interval policies;
- warning capture and stable result normalization;
- bounded Worker time/memory and no untrusted serialized inputs.

## RECA current state

SciPy is planned in M5 as a deterministic statistical tool. No Phase 3 research
change installs it or implements an analysis. `AnalysisPlan`, `AnalysisRun` and
`AnalysisResult` remain RECA-owned.

## Recommended integration mode

`DIRECT_DEPENDENCY`

Call selected `scipy.stats` functions behind small, method-specific RECA
StatisticalEngine functions. A general Adapter is unnecessary; the boundary is
valuable because it freezes input validation, policy, warning mapping and output
shape without exposing SciPy result objects as contracts.

## What to reuse

- tested deterministic implementations for the mapped P0 methods;
- named result attributes and confidence-interval APIs;
- warning classes and edge-case test ideas;
- upstream reference fixtures as comparison sources where licensing permits.

## What not to reuse

- textual repr or tuple position as a persistence contract;
- implicit NaN handling or silent sample-size changes;
- random defaults without stored RNG state;
- arbitrary `scipy.stats` function execution from user/model input;
- library warnings converted into successful, warning-free formal results.

## Domain boundary

```text
APPROVED AnalysisPlan + immutable DatasetVersion
-> RECA input validation and array construction
-> pinned SciPy method
-> structured statistic / p-value / CI / warnings
-> immutable RECA AnalysisResult
```

SciPy computes numbers. RECA owns method eligibility, approval, provenance,
interpretation labels, persistence and invalidation.

## Milestone

- M5 P0-Must: Pearson and Spearman correlation.
- M5 P0-Full: independent and paired two-group comparisons.
- M5 assumptions: normality and variance checks selected by AnalysisPlan.

## Risks

- Python/NumPy/SciPy ABI or wheel incompatibility;
- changed defaults or result-object behavior across versions;
- NaN omission silently changing effective N;
- warnings being dropped during Worker execution;
- misuse of p-values or correlation as causality by downstream explanation.

## Validation spike

Run every mapped method against hand-checkable and independent-reference golden
fixtures. Verify NaN policies, warnings, constants, small samples, CI methods,
effective N, repeated-run equality and structured serialization. Include one
compatibility build on the exact RECA Worker image.

## Attribution requirements

Preserve SciPy's BSD-3-Clause notice and applicable bundled-component notices.
Record exact binary/package versions. Copied fixtures or source require separate
path-level license review; package use alone does not authorize every dataset.

## Update strategy

Pin a compatible released SciPy/NumPy pair. Upgrade only after golden statistics,
warning mappings, wheel availability and result serialization pass unchanged or
an explicit, reviewed migration explains the delta.

## Change record

| Version | Date | Status | Change |
| --- | --- | --- | --- |
| 1.0.0 | 2026-07-31 | Conditional Approval | Recorded the research evidence, recommendation and RECA authority boundaries |
| 1.0.1 | 2026-07-31 | APPROVED FOR M1 DEVELOPMENT | Synchronized documentation approval; research status and integration facts are unchanged |
