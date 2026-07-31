# Open-Source Research Phase 3: Data, Statistics and Reproducibility

Document version: `1.0.0`

Document status: `Conditional Approval`

Last updated: 2026-07-31

## 1. Scope

This phase researched only:

- `unionai-oss/pandera`;
- `scipy/scipy`;
- `statsmodels/statsmodels`;
- `matplotlib/matplotlib`;
- `iterative/dvc`;
- `great-expectations/great_expectations`.

Research used fixed clones of the actual GitHub repositories and inspected
licenses, manifests, source trees, tests, benchmarks, documentation, CI and
deployment/configuration surfaces. Temporary repositories remained outside the
workspace. This phase changed no formal specification, code, dependency,
Compose service, CI workflow, migration, generated client or lock file.

## 2. Executive decision

```text
Pandera = runtime validation
Great Expectations = design/test reference
SciPy + statsmodels = deterministic statistics
Matplotlib = deterministic rendering
DVC = provenance and development inspiration
RECA DatasetVersion = business truth
```

These are research recommendations, not statements that the projects are now
installed or implemented.

## 3. Decision matrix

| Project | Recommended mode | Category | Runtime status | Milestone | Main boundary/risk |
| --- | --- | --- | --- | --- | --- |
| Pandera | `DIRECT_DEPENDENCY` | `P0_RUNTIME` | Planned, not installed by this phase | M4 | normalize FailureCases; Pandera objects are not domain contracts |
| SciPy | `DIRECT_DEPENDENCY` | `P0_RUNTIME` | Planned, not installed by this phase | M5 | explicit missing/warning policy and structured result mapping |
| statsmodels | `DIRECT_DEPENDENCY` | `P0_RUNTIME` | Planned, not installed by this phase | M5 | textual Summary is not AnalysisResult |
| Matplotlib | `DIRECT_DEPENDENCY` | `P0_RUNTIME` | Planned, not installed by this phase | M5 | fixed templates, fonts and metadata; no user code |
| DVC | `DEVELOPMENT_ONLY + DESIGN_REFERENCE` | `DEVELOPMENT_ONLY` | Not installed | M4/M5 fixtures; M7 inspiration | repository state cannot replace DatasetVersion or approval |
| Great Expectations | `DESIGN_REFERENCE + SELECTIVE_COPY` | `DESIGN_REFERENCE` | Not installed | M4 | must not become a second P0 validation authority |

### P0 runtime

- Pandera for deterministic dataframe schema and quality validation.
- SciPy for selected deterministic comparisons, correlations and assumptions.
- statsmodels for selected deterministic regression.
- Matplotlib for fixed deterministic chart templates.

### Selective reuse

- Great Expectations expectation taxonomy, report organization, failure wording
  and test ideas, with Apache-2.0 attribution when content is copied.
- DVC content-hash, dependency/output and lock-snapshot ideas, implemented in
  RECA-owned lineage and ReproPackage structures.

### Development-only

- Optional DVC CLI for curated, licensed demo or golden datasets, only after a
  concrete workflow shows that the operational cost is worthwhile.

### Design reference

- Great Expectations suite/result/Data Docs separation.
- DVC `deps`/`outs`, lock and reproducible-parameter concepts.

### Do not combine

Do not operate Pandera and Great Expectations as simultaneous P0 validation
authorities. Duplicate runtimes would create conflicting rule identities,
counts, severities, pass/fail results, versions and debugging paths.

## 4. Fixed upstream facts

| Project | Default branch | Research commit | Latest release/tag | License | Default-branch minimum runtime |
| --- | --- | --- | --- | --- | --- |
| Pandera | `main` | `85cc2a16b2110d4c4b8cc7f956aab94bc53716f6` | `v0.32.1` | MIT | Python `>=3.10`; pandas extra has its own NumPy/pandas minimums |
| SciPy | `main` | `420a778219f6db170f0fda8dcda4add8a32fd1d6` | `v1.18.0` | BSD-3-Clause plus bundled licenses | Python `>=3.12`, NumPy `>=2.0.0` |
| statsmodels | `main` | `d3187f844d196de1760829820a7c872a6d6ebb1d` | `v0.14.6` | BSD-3-Clause | Python `>=3.10` |
| Matplotlib | `main` | `faf5d100aed23d3271245c2e800ea47f86dd858b` | `v3.11.1` | Matplotlib license plus bundled licenses | Python `>=3.12`, NumPy `>=2.0` |
| DVC | `main` | `f74c1c0e709de61f571905802bc0c75035dc6ef2` | `3.67.1` | Apache-2.0 | Python `>=3.9` |
| Great Expectations | `develop` | `33614cd70a407f8b9589fa2cf5f1cb1d7d0723aa` | `1.19.1` | Apache-2.0 | Python `>=3.10` |

All six repositories were active and not archived when inspected. Default
branches and releases are different snapshots. Implementation must pin tested
releases compatible with RECA's actual Python/NumPy/pandas runtime rather than
copy these research-head minimums into dependencies.

Detailed records:

- [Pandera](../source-research/projects/pandera.md)
- [SciPy](../source-research/projects/scipy.md)
- [statsmodels](../source-research/projects/statsmodels.md)
- [Matplotlib](../source-research/projects/matplotlib.md)
- [DVC](../source-research/projects/dvc.md)
- [Great Expectations](../source-research/projects/great-expectations.md)

## 5. Pandera decision

Pandera should be the single P0 dataframe validation engine. RECA scientific
rules remain Git-managed RECA definitions with stable rule IDs, versions and
hashes. Pandera supplies schema/check execution and failure detail; it does not
own DataQualityRun, issue severity, API output or business status.

Each run records:

- input DatasetVersion and content hash;
- RECA rule-set ID/version/hash and selected parameters;
- Pandera/pandas/NumPy/Python versions;
- validation/coercion/lazy settings and failure-sample cap;
- normalization/template revision.

### FailureCase to DataQualityIssue

| Source detail | Normalized RECA field/behavior |
| --- | --- |
| schema/check identifier | RECA stable rule ID and rule-set version |
| column/index | affected field and optional record locator |
| check parameters | normalized parameters stored with the run/issue |
| failure value | bounded, privacy-reviewed sample |
| count/aggregation | issue affected count plus bounded examples |
| Pandera category/message | RECA issue type, severity and diagnostic provenance |

One issue should normally aggregate a rule/field failure rather than generate a
database object for every invalid cell. Raw error detail may be stored as a
bounded diagnostic Artifact. Coercion never overwrites the original data.

## 6. Deterministic statistics decision

The approved analysis flow remains:

```text
APPROVED AnalysisPlan
-> immutable DatasetVersion
-> RECA input and assumption validation
-> selected deterministic library function
-> structured numbers, warnings and provenance
-> immutable AnalysisResult
```

### SciPy P0 map

| RECA capability | Deterministic implementation candidate |
| --- | --- |
| Independent comparison | `scipy.stats.ttest_ind` |
| Paired comparison | `scipy.stats.ttest_rel` |
| Pearson | `scipy.stats.pearsonr` |
| Spearman | `scipy.stats.spearmanr` |
| Normality assumption | `scipy.stats.shapiro` or `normaltest`, selected by plan/sample rule |
| Variance assumption | `scipy.stats.levene` |

Every method must set missing-data policy explicitly, record effective N and
capture constant, near-constant and small-sample warnings. Random/resampling
methods, if later approved, require a stored RNG/seed and cannot depend on a
process-global random default.

### statsmodels boundary

Use `OLS`/documented result attributes for the P0-Full simple regression path.
Persist the design matrix or formula expansion, row inclusion, parameter order,
coefficients, covariance/standard errors, p-values, confidence intervals,
diagnostics and dependency versions.

```text
statsmodels textual Summary != RECA AnalysisResult
```

Summary is optional display/debug material only. It must not be parsed into
formal values or used as the stable schema.

## 7. Deterministic rendering decision

Matplotlib should render only fixed RECA chart templates:

| Template | M5 scope |
| --- | --- |
| `SCATTER` | P0-Must |
| `GROUP_COMPARISON` | P0-Must |
| `HISTOGRAM` | P0-Full |
| `BOXPLOT` | P0-Full |
| `CORRELATION_MATRIX` | P0-Full |

Use the headless `Agg` path for Worker rendering and explicitly export PNG, SVG
and PDF. A Figure records template/version, normalized parameters, source IDs,
style, backend, format, dimensions/DPI, dependency versions, output hash and the
actual font file/version/hash. Chinese text requires a pinned, licensed CJK font;
host fallback is not reproducible.

The system-generated plotting code is an Artifact. Every displayed estimate,
confidence interval, error bar or matrix value must agree with the linked
AnalysisResult. Plotting is not a second statistical engine.

For byte-level reproducibility, control timestamps and identifiers through
stable metadata, `SOURCE_DATE_EPOCH` and SVG `svg.hashsalt` where applicable.
Visual/structural golden tests remain necessary across output formats.

## 8. DVC decision

DVC is valuable as a provenance model and, optionally, a developer tool for
curated demo/golden data. It is not an application state store.

| DVC idea | RECA-owned destination |
| --- | --- |
| content hashes | Artifact/DatasetVersion hashes |
| stage dependencies and outputs | DataTransformation lineage |
| `dvc.lock` snapshot | ReproPackage manifest concepts |
| parameters/experiments | AnalysisPlan and AnalysisRun provenance |
| remote separation | optional development fixture storage pattern |

DVC cannot replace DatasetVersion, project isolation, approval, database
transactions, invalidation propagation, Artifact relations or audit. Its CLI
can execute arbitrary pipeline commands, so it must not become a route for
users, models or Agents to execute code.

```text
RECA DatasetVersion = business truth
DVC = optional development provenance
```

No DVC dependency, `.dvc` directory, pipeline or remote is created by Phase 3.

## 9. Great Expectations decision

Great Expectations overlaps Pandera in schema/check validation, but adds Data
Context, Checkpoints, Stores, rendering and deployment concepts. That extra
runtime would duplicate RECA's existing Job, DataQualityRun, issue, Artifact and
report ownership.

Useful selective research assets are:

- expectation taxonomy and readable descriptions;
- suite-level aggregation and validation-result summaries;
- separation of configuration, execution and rendering;
- Data Docs information architecture;
- test naming, failure wording and report UX patterns.

These may be adapted into RECA-owned rules/reports with Apache-2.0 attribution.
Checkpoint, Store, Data Context and Validation Result do not become business
objects. No Great Expectations runtime spike is recommended for P0.

## 10. Cross-project execution chain

```text
Original DatasetVersion (immutable)
-> RECA versioned quality rules
-> Pandera validation
-> DataQualityRun / DataQualityIssue
-> approved CleaningPlan and new DatasetVersion
-> approved AnalysisPlan
-> SciPy / statsmodels deterministic computation
-> immutable AnalysisResult
-> Matplotlib fixed template
-> Figure code + image Artifacts
-> ReproPackage manifest
```

Great Expectations contributes report/test design only. DVC contributes
development/provenance ideas only. Neither appears in the formal runtime chain.

## 11. Scientific and domain boundaries

- Original DatasetVersion is immutable; validation or rendering never modifies it.
- Only an approved CleaningPlan can create a transformed DatasetVersion.
- Only an approved AnalysisPlan can create a formal AnalysisRun/AnalysisResult.
- Formal statistics come only from deterministic programs, never a model.
- Library result objects are normalized; they are not stable API/database DTOs.
- Warnings, missing policies, effective sample sizes and dependency versions are
  part of result provenance.
- Figure values must agree with AnalysisResult and source DatasetVersion.
- DVC/GX state cannot grant approval, availability, project membership or truth.
- No arbitrary user, model or Agent Python/SQL/Shell execution is introduced.

## 12. Validation spikes in recommended order

1. Pin a compatible Pandera/pandas/NumPy set and normalize lazy FailureCases.
2. Benchmark the exact M4 rule set on representative bounded CSV/XLSX data.
3. Run SciPy golden fixtures for Pearson/Spearman and assumption checks.
4. Add independent/paired comparison edge cases for P0-Full.
5. Fit statsmodels simple OLS with explicit design and formula comparison.
6. Render all five Matplotlib templates to PNG/SVG/PDF in the Worker image.
7. Verify CJK font resolution and figure-to-AnalysisResult equality.
8. Prototype a GX-inspired RECA report without installing GX.
9. Evaluate DVC only if curated fixture management becomes a measured problem.

Each spike remains disposable until dependency compatibility, domain boundary,
attribution and golden tests pass.

## 13. Risks and unresolved questions

| Topic | Unresolved implementation question | Disposition |
| --- | --- | --- |
| numerical stack | exact Python/NumPy/pandas/SciPy/statsmodels/Matplotlib compatible pins | resolve in M4/M5 dependency spike |
| Pandera coercion | which checks may coerce only a working copy | explicit rule-set policy; never change original |
| failure volume | issue aggregation and raw diagnostic retention limits | benchmark and privacy review |
| SciPy assumptions | exact sample-size rule for Shapiro versus normaltest | encode in AnalysisPlan/template, not library default |
| formula API | whether P0 uses explicit design matrices only | prefer explicit matrix; validate formula option separately |
| reproducible charts | byte equality across formats/platforms | define per-format hash or structural/image tolerance |
| CJK font | distributable pinned font selection | license and Worker-image decision required |
| DVC | whether fixture volume justifies developer tooling | deferred until measured need |
| Great Expectations | whether report ideas require copied text/code | start with design reference; record any copy explicitly |

None of these questions changes current Requirements, contracts or milestone
scope. They are implementation-spike inputs.

## 14. Attribution and licensing

- Pandera: MIT.
- SciPy and statsmodels: BSD-3-Clause; SciPy also lists bundled licenses.
- Matplotlib: Matplotlib license plus bundled component/font licenses.
- DVC and Great Expectations: Apache-2.0.
- Exact adopted package versions and copied paths must be recorded.
- Copied source, tests, fixtures or documentation require upstream Commit,
  source path, modification summary and applicable notice retention.
- Dataset and font licenses are separate from the software-library license.

No third-party notice was added because this documentation phase copied no
third-party content and introduced no dependency.

## 15. Stable contract preservation

This phase added research prose only:

- Requirement IDs: unchanged.
- Acceptance IDs: unchanged.
- API paths: unchanged.
- Error codes: unchanged.
- Schema names: unchanged.
- Agent Tool names: unchanged.
- Enum values: unchanged.
- Milestone IDs: unchanged.

Terms such as `P0_RUNTIME`, `DEVELOPMENT_ONLY` and `DESIGN_REFERENCE` in this
report are research classifications, not newly adopted API Schema or domain
Enum values.

## 16. No-code-change confirmation

Phase 3 added only six source-research Markdown files and this report. It did not
modify the nine formal entry documents, subordinate specifications, application
code, tests, dependencies, Compose, CI, migrations, generated clients, lock
files or third-party runtime records. It created no DVC metadata and copied no
upstream code, Prompt, script, test, fixture, dataset or font.
