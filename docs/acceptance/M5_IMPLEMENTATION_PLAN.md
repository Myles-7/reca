# M5 Implementation Plan

Date: 2026-08-04
Owner: Codex
Status: STAGE 0 CONTRACT FROZEN
Authorized scope: M5 only

## 1. Recovery Baseline

```text
branch=feat/m2-research-literature
HEAD=25a4fe6ea7acac6e95af25563bca5a2c0a6b1acd
upstream=origin/feat/m2-research-literature
ahead=9
behind=0
worktree_at_stage_start=clean
tracked_changes_at_stage_start=none
untracked_at_stage_start=none
migration_head=0014_m4_data_quality
M4_EXIT=PASS
M4_COMPLETION=APPROVED
M5_ENTRY=ALLOWED
```

Recovery commands are `git status --short --branch`, `git diff --name-status`,
`git ls-files --others --exclude-standard`, migration revision/down_revision inspection,
and the focused commands recorded in section 22. No Commit, Tag, Push, stash or runtime-data
copy was created.

Snapshot differences resolved from current facts:

- The M4 Exit report describes its historical worktree as intentionally dirty; the current Stage 0
  worktree was clean. Current Git facts take precedence.
- The local default `python` is 3.13.13, while the application and Worker authority is Python 3.14
  (`requires-python >=3.14` and `python:3.14.3-slim-bookworm`). All compatibility conclusions use
  the Worker runtime, not the local default interpreter.
- No local Alembic executable was available before dependency synchronization. The single head is
  confirmed structurally by `0014_m4_data_quality` and its `down_revision` chain; Stage 5 repeats
  the database-backed `alembic heads/check/upgrade` gate.
- The prompt refers to `backend/uv.lock`, but the tracked uv workspace authority is the repository
  root `uv.lock`; root `pyproject.toml` declares `backend` as a workspace member and Docker binds the
  root lock/project files. Dependency adoption therefore updates root `uv.lock`.
- The generic AnalysisPlan state-machine chapter lists historical run states on the Plan, but its
  own recommended implementation and the M5 Stage 0 authority move execution progress entirely to
  AnalysisRun. This plan freezes the recommended split.
- The data-model chapter names FigureRenderRun without defining its complete fields/statuses. This
  plan supplies the additive M5 implementation contract consistent with Job/ProcessingRun rules.

## 2. Scope Freeze

Competition Core and P0-Must:

- `DESCRIPTIVE_STATISTICS`, `PEARSON_CORRELATION`, `SPEARMAN_CORRELATION`;
- `SCATTER`, `GROUP_COMPARISON`;
- approved Plan -> Job/ProcessingRun -> deterministic Result -> Artifact lineage;
- fixed headless templates, warnings, assumptions, approval freshness, hashes and invalidation;
- one production Analysis Workspace route and a real vertical chain.

P0-Full:

- `INDEPENDENT_TWO_GROUP`, `PAIRED_TWO_GROUP`, `SIMPLE_LINEAR_REGRESSION`;
- `HISTOGRAM`, `BOXPLOT`, `CORRELATION_MATRIX`.

Explicitly not implemented in M5:

- arbitrary methods, multivariable/causal models, user code, SQL, shell, formulas or expressions;
- automatic method selection followed by execution;
- model-generated formal numbers or chart data;
- significance optimization, hidden null results or correlation-as-causation;
- a second Artifact, Approval, Job, Audit, API client, Workspace shell or async lifecycle;
- formal Agent runtime or AI provider integration before M8. M5 only freezes typed suggestion and
  interpretation contracts with an explicit unavailable/degraded state.

## 3. Planned Code Locations

```text
backend/app/analysis/{schemas.py,registry.py,engine.py,service.py,__init__.py}
backend/app/figures/{schemas.py,registry.py,renderer.py,service.py,__init__.py}
backend/app/api/routes/{analysis.py,figures.py}
backend/app/models.py
backend/app/alembic/versions/0015_m5_analysis_figures.py
backend/app/workers/jobs.py
backend/tests/{analysis,figures,golden,api/routes,workers}/...
backend/tests/fixtures/m5_analysis/*.json
frontend/src/features/analysis-workspace/{model.ts,mappers.ts,queries.ts,mutations.ts,route-contract.ts}
frontend/src/features/analysis-workspace/{containers,ui,fixtures}/...
frontend/src/routes/_layout/projects.$projectId_.analysis.tsx
```

The generated client remains generator-owned. Backend router modules handle HTTP/auth context and
response mapping only. Services own permissions, relationships, transactions, idempotency, audit,
locking and transitions. Engines receive normalized RECA-owned values and return domain DTOs only.

## 4. Enum Freeze

```text
AnalysisGoal = DESCRIPTIVE | GROUP_COMPARISON | CORRELATION | SIMPLE_PREDICTION
AnalysisMethod = DESCRIPTIVE_STATISTICS | INDEPENDENT_TWO_GROUP | PAIRED_TWO_GROUP |
                 PEARSON_CORRELATION | SPEARMAN_CORRELATION | SIMPLE_LINEAR_REGRESSION
AssumptionCheckCode = DATA_TYPE | SAMPLE_SIZE | INDEPENDENCE | NORMALITY |
                      VARIANCE_HOMOGENEITY | LINEARITY | OUTLIER_INFLUENCE |
                      PAIRING_VALIDITY | MISSINGNESS | CONSTANT
AssumptionCheckStatus = PASSED | FAILED | WARNING | NOT_APPLICABLE |
                        REQUIRES_USER_CONFIRMATION | UNKNOWN
AnalysisPlanStatus = DRAFT | VALIDATING | NEEDS_INPUT | READY | NEEDS_APPROVAL |
                     APPROVED | REJECTED | INVALIDATED
AnalysisRunStatus = QUEUED | RUNNING | COMPLETED | FAILED | CANCEL_REQUESTED |
                    CANCELLED | INVALIDATED
AnalysisResultType = PRIMARY | DESCRIPTIVE_NUMERIC | DESCRIPTIVE_CATEGORICAL |
                     CORRELATION | GROUP_COMPARISON | REGRESSION | DIAGNOSTIC
FigureChartType = SCATTER | GROUP_COMPARISON | HISTOGRAM | BOXPLOT | CORRELATION_MATRIX
FigurePlanStatus = DRAFT | READY | INVALIDATED | ARCHIVED
FigureRenderRunStatus = QUEUED | RUNNING | COMPLETED | FAILED | CANCEL_REQUESTED |
                        CANCELLED | INVALIDATED
FigureStatus = DRAFT | READY | NEEDS_REVIEW | CONFIRMED | INVALIDATED | ARCHIVED
FigureIssueType = MISSING_AXIS_LABEL | MISSING_UNIT | MISSING_LEGEND |
                  MISSING_CAPTION | UNDEFINED_ERROR_BAR | MISLEADING_AXIS_RANGE |
                  LOW_RESOLUTION | VERSION_MISMATCH | RESULT_MISMATCH
FigureIssueSeverity = ERROR | WARNING | INFO
FigureIssueStatus = OPEN | ACKNOWLEDGED | RESOLVED | INVALIDATED
MissingDataMode = LISTWISE_COMPLETE | PAIRWISE_COMPLETE
AlternativeHypothesis = TWO_SIDED | LESS | GREATER
VarianceMode = EQUAL | WELCH
```

`CONSTANT` is added because the product and golden requirements demand a stable constant-column
fact even though the older model enum omitted it. It is additive and does not change method scope.

## 5. State Machines

AnalysisPlan:

```text
DRAFT -> VALIDATING
VALIDATING -> NEEDS_INPUT | READY
NEEDS_INPUT -> DRAFT
READY -> DRAFT | NEEDS_APPROVAL
NEEDS_APPROVAL -> APPROVED | REJECTED
REJECTED -> DRAFT
APPROVED -> INVALIDATED
```

Only `DRAFT`, `NEEDS_INPUT` and `READY` are editable. Editing clears checks, warnings, canonical
hash and approval reference, increments `lock_version`, and returns to `DRAFT`. Approval never
becomes a run-progress flag; repeated runs preserve the Plan's `APPROVED` meaning.

AnalysisRun and FigureRenderRun:

```text
QUEUED -> RUNNING | CANCEL_REQUESTED
RUNNING -> COMPLETED | FAILED | CANCEL_REQUESTED
CANCEL_REQUESTED -> CANCELLED | FAILED
COMPLETED -> INVALIDATED
```

Failure is terminal for that run. Retry uses the same Job identity under the common Job contract,
creates a new ProcessingRun attempt, and does not create a second domain Run. A new user-requested
analysis with a different Idempotency-Key creates a new AnalysisRun/run_number. Cancellation keeps
logs. Worker failure before finalize creates no Result/Figure and no AVAILABLE output Artifact.

Figure lifecycle:

```text
DRAFT -> READY | NEEDS_REVIEW
READY -> CONFIRMED | INVALIDATED | ARCHIVED
NEEDS_REVIEW -> INVALIDATED
CONFIRMED -> INVALIDATED | ARCHIVED
```

Rendering state belongs to FigureRenderRun, not Figure. A Figure row is inserted only in the same
database finalize transaction that binds all AVAILABLE output Artifacts. Parameter changes create a
new FigurePlan/render/Figure; no image or parameters are overwritten.

## 6. Migration Sequence Freeze

Updated by the explicit Stage 1 scope: `0015_m5_analysis` is one additive revision after
`0014_m4_data_quality` and creates exactly five Analysis tables. Stage 2 must add one new revision
after 0015 for the four Figure tables; it must not rewrite released 0015.

1. `analysis_plans`: project/RQ version/DatasetVersion, method/goal, variable ID arrays,
   missing/filter/parameters JSON, hashes, status, approval, lock_version, timestamps and
   invalidation. Composite FKs enforce project with RQ version, DatasetVersion and Approval.
   Unique `(id, project_id)`; indexes `(project_id,status)`, dataset, RQ version and approval.
2. `analysis_assumption_checks`: project, Plan, code/status, subject key, explanation/evidence,
   blocking flag and timestamp. Composite Plan FK; unique `(analysis_plan_id,check_code,subject_key)`.
3. `analysis_runs`: project, Plan, DatasetVersion, approval, run_number, idempotency key,
   input/parameter/environment hashes, ProcessingRun, Code/Log refs, effective N,
   status/times/error/invalidation. Composite same-project FKs; unique `(analysis_plan_id,run_number)`
   and `(analysis_plan_id,idempotency_key)`; checks run number, hashes and completed snapshot.
4. `analysis_results`: project, Run, result type/key, primary flag, versioned payload, result hash and
   created_at. Composite Run FK; unique `(analysis_run_id,result_key)` plus a partial unique primary
   index. PostgreSQL rejects UPDATE and DELETE after insert.
5. `code_artifacts`: project, immutable Artifact, owning AnalysisRun, template/language/entry,
   dependency snapshot and input/output hash. Composite Artifact/Run FKs; one code record per Run and
   per Artifact.

Stage 2 additive migration creates:
6. `figure_plans`: project, DatasetVersion, optional AnalysisRun, chart/column bindings, parameters,
   canonical/parameter hash, caption, status, lock_version, timestamps/invalidation. Composite FKs;
   unique `(id,project_id)` and indexes on project/status, dataset and analysis run.
7. `figure_render_runs`: project, FigurePlan, DatasetVersion, optional AnalysisRun, Job, run_number,
   idempotency/input/parameter/environment hashes, renderer/style/font/template versions,
   ProcessingRun, status/times/error/invalidation. Same uniqueness and retry semantics as AnalysisRun.
8. `figures`: project, Plan, RenderRun, DatasetVersion, optional AnalysisRun, chart type, PNG/SVG/PDF/
   code Artifacts, caption/parameters/hashes/status/times/invalidation. Composite same-project FKs;
   one Figure per successful RenderRun; all required Artifacts unique to the Figure.
9. `figure_validation_issues`: project, Figure, type/severity/status, evidence/suggestion/timestamps.
   Composite Figure FK; unique `(figure_id,issue_type)` and indexes on figure/status/severity.

Stage 2 also extends `code_artifacts` with a nullable FigureRenderRun owner and an exactly-one-owner
check, preserving every Stage 1 Analysis code row.

All core FKs use `RESTRICT`/`NO ACTION`; no broad cascade. Status/check constraints reject invalid
terminal combinations. Invalidation is additive metadata and preserves all rows and Artifacts.

## 7. Concurrency, Canonical Payloads And Approval

- `If-Match` is required for Plan patches and compares quoted `lock_version`.
- Canonical JSON is UTF-8, object keys sorted, compact separators, Unicode preserved, enum values as
  strings, UUID/date normalized strings, arrays ordered where semantic order matters, and set-like
  ID arrays UUID-sorted after duplicate rejection. Floats are finite IEEE values serialized by the
  project canonical encoder; NaN/Infinity and negative zero are rejected/normalized before hashing.
- Analysis Plan canonical payload contains project/RQ/DatasetVersion IDs and hashes, confirmed
  column identities/roles, method/goal, missing policy, sample filter, parameters, latest quality
  facts/acknowledgements and schema/template versions.
- Approval payload is a versioned snapshot of that canonical payload. Approval execution requires
  type `ANALYSIS_PLAN_APPROVAL`, status APPROVED, same project/target/actor policy and exact payload
  hash; changed content supersedes approval.
- Figure confirmation uses `FIGURE_CONFIRMATION` and hashes Figure ID, RenderRun, DatasetVersion,
  AnalysisRun/Result hashes, parameter/style/font/code/output Artifact hashes and open issues.

## 8. Idempotency And Run Numbers

- Scope follows the common contract: actor, project, method, canonical path and Idempotency-Key.
- Authorization and current-state checks occur before replay lookup.
- Same key + same request hash returns the original Job and domain Run with replay metadata.
- Same key + different hash returns `409 IDEMPOTENCY_CONFLICT`.
- A different key against the same still-APPROVED Plan creates `run_number = max + 1` under a row
  lock and a new AnalysisRun. Job retry keeps Job, AnalysisRun and run_number unchanged and adds a
  ProcessingRun attempt only.

## 9. Hash Chain

```text
Artifact.sha256
-> DatasetVersion.data_hash + schema_hash + projection_hash
-> confirmed DatasetColumn identity/definition hash
-> latest completed DataQualityRun ruleset/input/result hash
-> AnalysisPlan canonical_hash + parameters_hash
-> ApprovalRecord.payload_hash
-> AnalysisRun input_hash + environment_hash + code_hash
-> AnalysisResult result_hash
-> FigurePlan canonical_hash + parameters_hash
-> FigureRenderRun input/environment/style/font/code hashes
-> PNG/SVG/PDF Artifact sha256 + Figure aggregate_hash
```

Every Worker handler re-reads all rows and object bytes, recomputes the applicable chain and fails
closed on mismatch. Queue actor/project/version/approval/hash values are hints only.

## 10. Statistical Policy

- Input limit inherits M4: at most 50,000 rows, 100 dataset columns and 25 MiB source Artifact;
  an AnalysisPlan may reference at most 20 columns. Figures accept at most 50,000 effective points.
- Missing policy is explicit. Listwise uses the union of all method variables. Pairwise is allowed
  only for one pair/correlation or pair-specific descriptive child results. Effective row count and
  excluded count are persisted per result. No implicit library `nan_policy` or statsmodels drop.
- `sample_filter` is a recursive typed whitelist of `AND` clauses over confirmed column UUIDs and
  operations `EQUALS`, `IN`, `IS_NULL`, `IS_NOT_NULL`, `NUMERIC_RANGE`; max 20 predicates, max 100
  values, depth 2. No free text, regex, expression, callable, code, SQL or URL.
- Confidence level defaults to 0.95 and is restricted to `[0.80, 0.99]`. Alternative is explicit and
  defaults to `TWO_SIDED`. Independent comparison requires explicit `EQUAL` or `WELCH`; UI may
  recommend Welch but cannot silently choose after approval. Paired comparison requires a unique,
  non-null confirmed pair ID and exactly one observation per side.
- Numeric descriptive statistics: N, missing, mean, sample SD with `ddof=1`, median, linear-method
  Q1/Q3, min and max. SD is null with a structured warning when effective N < 2.
- Categorical descriptive statistics: effective N, missing, ordered category counts and proportions
  using denominator effective non-missing N; ordering is configured category order then Unicode
  code-point order. Zero denominator yields null proportions and a blocking sample-size failure.
- Pearson uses pairwise finite rows, requires N >= 3 and non-constant inputs, and records Fisher-z CI.
  Spearman uses average ranks for ties, requires N >= 3 and records tie warning; coefficient/p-value
  come from SciPy structured attributes.
- Independent/paired tests persist group/pair effective Ns, mean difference, t, df, p, CI and effect
  information. Simple OLS uses an explicit intercept design matrix, `missing='raise'`, and persists
  coefficients, SE, t, p, CI, R-squared, df, residual diagnostics and exact effective N.

## 11. Assumptions And External Normalization

- `FAILED` blocks approval and run. `UNKNOWN` blocks approval and run. `REQUIRES_USER_CONFIRMATION`
  blocks until a versioned acknowledgement is part of the Plan payload. `WARNING` permits approval
  but remains visible in Plan/Result. `PASSED` and `NOT_APPLICABLE` do not block.
- Required checks are method-registry controlled; missing required check rows fail closed.
- SciPy `ConstantInputWarning` -> `CONSTANT/FAILED`; `NearConstantInputWarning` -> warning requiring
  explicit visibility; small-sample exception/warning -> `SAMPLE_SIZE/FAILED`; non-finite outputs ->
  `EXTERNAL_OUTPUT_INVALID`. Statsmodels singular/rank-deficient design -> failed assumption or run,
  never a partial result. Captured warning class and stable RECA code are stored; raw repr/traceback
  and sensitive values are not.
- No SciPy/statsmodels object is serialized. `Summary` is never called for data extraction and is not
  persisted as a formal result.

## 12. AnalysisResult Contract

- Schema version starts at `analysis-result/1.0`; result keys make one `PRIMARY` and deterministic
  child results unique per Run.
- JSON numbers must be finite. Unavailable values are JSON null plus a stable warning/reason code,
  never numeric strings. Persist full double precision; display rounding is frontend-only.
- Result rows, variables, statistics, CI, effects and hashes are immutable after successful finalize.
  Invalidation adds timestamp/reason to Run/Result projections without deleting or rewriting numbers.
- DatasetVersion invalidation invalidates dependent Runs/Figures. Run invalidation retains Results,
  invalidates dependent Figures, and causes downstream M6 reads to fail closed.

## 13. Figure Contract

- FigurePlan parameters use per-chart strict Pydantic schemas. Shared whitelist: width 4-12 inches,
  height 3-10, DPI 150/300, fixed RECA style ID, title/caption/axis labels with length limits, legend
  boolean/location enum, and approved color-palette IDs. Chart-specific fields are booleans/enums or
  bounded numbers only; unknown keys are rejected.
- Agg is mandatory. Style is a versioned RECA template. Noto CJK from Debian `fonts-noto-cjk` is the
  approved font; font family/file hash is captured. Missing font fails render, with no silent fallback.
- `svg.hashsalt` is fixed. SVG `Date`, PDF CreationDate/ModDate and variable producer timestamps are
  removed/fixed; PNG Software metadata is fixed. Comparison uses semantic manifest + pixel checks for
  PNG and canonicalized SVG/PDF metadata/hash checks, not an assumption that all external encoders are
  byte-identical across upgraded environments.
- Render creates temporary code/PNG/SVG/PDF objects, validates headers/size/dimensions and hashes,
  uploads under pending Artifact states, then atomically marks all AVAILABLE and inserts Figure.
  Any failure quarantines/removes pending storage through existing compensation and creates no Figure.
- Figure DatasetVersion must equal the Plan input. Optional AnalysisRun must be same project, same
  DatasetVersion, COMPLETED and not invalidated. Result-driven plots recompute plotted series/summary
  from immutable inputs and compare against referenced Result hashes before finalize.

## 14. AI Boundary

Typed contracts may expose method suggestions, figure recommendations, assumption explanations,
interpretations and caption drafts. Inputs contain field metadata and deterministic summaries only;
sensitive values are excluded. Outputs carry no approval/execution authority and may not add numbers.
Until a later authorized provider integration, endpoints return an explicit unavailable/degraded
projection; deterministic analysis and figures remain fully usable.

## 15. Frontend Route And Ownership

The single production route is frozen as:

```text
/projects/$projectId/analysis
```

Search keys: `dataset`, `version`, `plan`, `approval`, `run`, `result`, `figurePlan`, `renderRun`,
`figure`, `job`, and `view=plan|assumptions|runs|results|figures`. Invalid UUID/enums are discarded.

Codex owns route semantics, generated client, adapter, queries/mutations, mapper, Container,
ViewModel, typed fixtures, permissions/status mapping and integration tests. Open Design owns `ui/**`
composition/CSS/design-system use only after the Stage 3 handoff. The UI contract uses Props in and
typed Events out; mutations refetch/invalidate after server success and never fabricate success.

Stage 3 READY requires frozen TypeScript ViewModel/Props/Event, all loading/empty/error/forbidden/
degraded/stale states, typed fixture coverage, production guards, route contract and a written handoff.

## 16. Stage Dependency Graph

```text
Stage 0 dependency/contract freeze
  -> Stage 1 models + 0015 + P0-Must analysis vertical
  -> Stage 2 P0-Full + figures + Artifact finalize
  -> Stage 3 OpenAPI/generated + frontend contracts/fixtures + Open Design handoff
  -> Stage 4 Open Design delivery integration + real browser vertical
  -> Stage 5 all issue repair + complete Exit Gate + M6 handoff
```

## 17. Focused Test Plan

- Stage 1: model/migration constraints, analysis schemas/registry/engine, approval/hash/idempotency,
  service/API/Worker and P0-Must golden tests.
- Stage 2: P0-Full golden, FigureRenderer, font/metadata, Artifact atomicity, consistency, retry/cancel,
  service/API/Worker tests.
- Stage 3: OpenAPI/generated consistency, mapper/contract/fixture/type and boundary guards.
- Stage 4: M5 focused Playwright and one real vertical DatasetVersion -> confirmed Figure chain.
- Stage 5: full backend/PostgreSQL/migration/Worker/MinIO/frontend/Playwright/clean-room/security,
  dependency audit, notices/license, secret scan, supply chain and `git diff --check`.

## 18. Golden Fixtures

Repository-owned fixtures are hand-authored with provenance notes and no copied upstream data:
perfect positive/negative/near-zero correlations, Pearson/Spearman divergence, missing/constant/small
N/outlier cases, independent/paired comparisons, known simple OLS, categorical proportions and all
five chart types. Expected values use independent calculation notes and tolerances; exact equality is
required for hashes/status/schema, numeric comparisons use method-specific absolute/relative tolerance.

## 19. Real Vertical Chain

```text
AVAILABLE DatasetVersion + matching AVAILABLE Artifact
-> confirmed columns + completed quality facts
-> AnalysisPlan create/validate
-> formal approval with payload hash
-> AnalysisRun + Job + ProcessingRun
-> deterministic immutable Results + Code/Log Artifacts
-> FigurePlan + RenderRun/Job
-> PNG/SVG/PDF/Code Artifacts + Figure validation
-> FIGURE_CONFIRMATION Approval
-> confirmed downloadable Figure
```

Every boundary revalidates project, permission, allowed action, state, version, approval and hashes.

## 20. Spike Decision

Selected released runtime:

```text
Python 3.14.3
NumPy 2.5.1
pandas 3.0.5
SciPy 1.18.0
statsmodels 0.14.6
Matplotlib 3.11.1
Debian fonts-noto-cjk 1:20220127+repack1-1
backend=Agg
```

All numerical packages resolved as official CPython 3.14 manylinux wheels. Hand-checkable results
covered descriptive statistics, Pearson/Spearman, Welch independent, paired t and explicit-matrix OLS.
Structured OLS extraction did not call or parse Summary. Constant Pearson produced
`ConstantInputWarning` and non-finite output; N=1 raised ValueError. Both are frozen error mappings.

Five chart types rendered to 15 valid files (PNG/SVG/PDF). With fixed metadata and SVG salt, a second
render produced identical hashes for all 15. Noto CJK was discovered and missing-font lookup failed as
expected. Benchmark in the Worker-compatible image:

```text
5,000 rows Pearson+OLS: 0.001138 s
50,000 rows Pearson+OLS: 0.035007 s
process peak RSS after import/render workload: 231,760 KiB (~226 MiB)
```

Competition Core freezes a per-analysis Worker soft target of 30 seconds and hard timeout of 60
seconds, with a 512 MiB container memory target. Import/font-cache startup and multi-format rendering
are tested separately in Stage 2/5. No application Python upgrade was made.

## 21. Key Decisions And Rejected Alternatives

- Direct dependencies behind small RECA protocols: chosen because interfaces are bounded and no
  provider switching is needed. A generic numerical Adapter was rejected as unhelpful abstraction.
- Explicit OLS design matrix: chosen for stable variable order/missing behavior. Formula API rejected
  for P0 because it introduces parsing and implicit encoding.
- Fixed Noto CJK system font: chosen for headless CJK coverage. Silent DejaVu fallback rejected.
- Run state split from Plan/Figure: chosen to preserve approval and repeated-run meaning. Reusing Plan
  status for execution was rejected.
- No AI provider in M5 entry work: deterministic scope does not depend on it; typed degradation is
  sufficient and avoids advancing M8.

## 22. Stage 0 Verification Record

Actual focused checks:

- released-wheel dry run on `python:3.14.3-slim-bookworm`;
- Worker-compatible container numerical/Warning/NaN/effective-N/CI/repeat Spike;
- Agg five-chart PNG/SVG/PDF/CJK/missing-font/metadata/hash Spike;
- normal and 50,000-row time/RSS measurement;
- dependency metadata and Debian font license inspection;
- `uv lock --check`/frozen synchronization and Worker-image import/build checks after edits;
- necessary static/document checks and `git diff --check`.

Stage 0 does not run the full backend, Playwright, PostgreSQL, MinIO or clean-room gates.

## 23. Stage 0 Closeout

Actual modified scope:

```text
backend/pyproject.toml
backend/Dockerfile
uv.lock
THIRD_PARTY_NOTICES.md
docs/acceptance/M5_IMPLEMENTATION_PLAN.md
docs/acceptance/M5_ISSUE_REGISTER.md
```

No formal M5 model, migration, endpoint, Worker handler or frontend Workspace was implemented.
At Stage 0 closeout, `M5-ISSUE-0004` remained open for database-backed migration verification; Stage 1 resolved it with the pinned uv/Docker runtime.

```text
STAGE_RESULT=PASS_WITH_ISSUES
NEXT_STAGE_EXECUTED=NO
```

## 24. Stage 1 Implementation Record

Stage 1 implemented the Analysis-only vertical and did not execute Figure, P0-Full or frontend work.
The later explicit Stage 1 prompt overrode the Stage 0 aggregate nine-table sketch: `0015_m5_analysis`
contains the five Analysis tables, while the four Figure tables move to an additive Stage 2 migration.
This difference is tracked as `M5-ISSUE-0006`; released 0015 must not be rewritten in Stage 2.

Implemented scope:

- enums and SQLModel entities for AnalysisPlan, AnalysisAssumptionCheck, AnalysisRun,
  AnalysisResult and CodeArtifact;
- `0015_m5_analysis` as the sole head after 0014, with same-project composite foreign keys,
  hash/state checks, run/idempotency uniqueness, one-primary-result uniqueness and a PostgreSQL
  trigger rejecting AnalysisResult UPDATE/DELETE;
- strict AnalysisPlan/filter/parameter input schemas and typed public API responses;
- deterministic descriptive numeric/categorical, Pearson and Spearman engine with explicit missing
  policy, effective N, sample SD, linear quartiles, CI, finite-number normalization and warnings;
- blocking confirmation for Pearson linearity, confirmed/sensitive columns and HIGH quality issue
  acknowledgements;
- create/get/If-Match patch/validate/approval/run/detail/results/invalidate APIs;
- ANALYSIS_PLAN_APPROVAL resolver/decision handler, approval hash replay protection and immutable
  APPROVED Plan semantics;
- Job/ProcessingRun/Worker integration with claim-time permission/version/Artifact/hash/approval
  revalidation, fixed system code template, immutable Result and Code/Log Artifacts;
- same-key Run replay, different-key run_number creation, explicit cancellation synchronization,
  failure compensation and domain audit events;
- independent golden fixtures under `backend/tests/golden/m5_analysis/v1`.

Stage 1 decisions:

- `REQUIRES_USER_CONFIRMATION` is approval-blocking until the corresponding typed confirmation is
  present; WARNING remains non-blocking and UNKNOWN fails closed.
- Pairwise descriptive statistics use each column's effective N; COMPLETE_CASE uses one shared row
  set. Pearson/Spearman always use explicit paired finite observations and require N >= 3.
- Result JSON contains numbers or null only; library objects, Summary text, function/module names,
  formulas and executable expressions never cross the engine boundary.
- The existing `.venv` is a Linux-style artifact unusable on Windows. Stage 1 used isolated
  `.venv-m5` plus the pinned Python 3.14.3 Docker runtime and did not modify the retained `.venv`.

Actual focused verification:

```text
32 passed: analysis engine/schema/model/migration/golden/OpenAPI/Worker registration (no database)
1 passed: real PostgreSQL/API/Approval/Worker/Artifact/Result vertical and security negatives
13 passed: affected Approval and Job API regression tests
Ruff: passed on all affected Stage 1 files
Mypy: passed on analysis, API response/router and Worker files
Alembic heads/current: 0015_m5_analysis (single head)
Python 3.14.3 focused Docker image: built successfully
git diff --check: passed
```

The bind-mounted Docker test directory is read-only, so pytest emitted one cache-write warning; it
did not affect test execution. `M5-ISSUE-0007` records the fail-closed hard Worker-loss reconciliation
work reserved for the final recovery gate.

```text
STAGE_RESULT=PASS_WITH_ISSUES
NEXT_STAGE_EXECUTED=NO
```

## 25. Stage 3 Implementation Record

Stage 3 followed current repository facts rather than the original sequential snapshot. Stage 1 is
accepted, but Stage 2 was not executed. Therefore the Analysis transport and frontend ownership
contracts were implemented, while Figure transport remains explicitly unavailable under
`M5-ISSUE-0008`. No Figure backend, production route or visual Workspace was created.

Contract decisions:

- the single future product route remains `/projects/$projectId/analysis`; Stage 3 freezes parsing
  and ownership only, with `productionIntegrationComplete: false`;
- AnalysisPlan now projects server-computed `approval_stale`; AnalysisRun projects formal
  `allowed_actions`, so the browser does not compare approval hashes or infer invalidation rights;
- generated enums are mapped through known-value sets. Future statuses retain their raw value,
  set `knownStatus=false` and disable all mutations;
- `allowed_actions` and project action projections are the only permission inputs. Missing action or
  unknown permissions fail closed;
- deterministic AnalysisResult payload numbers remain numbers/null and AI interpretation remains a
  separate nullable fact;
- Figure types and frozen state families are available to pure UI as document-derived placeholders,
  but every object carries `transportAvailable=false`, permissions are unknown, all Figure actions
  are disabled and no adapter method exists;
- P0-Full group-comparison/regression fixture names record required UI states without fabricating
  formal results; their result collections remain empty until Stage 2 freezes real DTO schemas;
- events express user intent only. Mutation success is accepted only after generated-client response
  plus query invalidation/refetch; fixtures never enter query, mutation, adapter or route code.

Implemented scope:

```text
backend/app/api/m5_responses.py
backend/app/analysis/service.py
frontend/openapi.json
frontend/src/api/generated/**
frontend/src/api/adapter/index.ts
frontend/src/features/analysis-workspace/{model,mappers,queries,mutations,route-contract}.ts
frontend/src/features/analysis-workspace/containers/AnalysisWorkspaceContainer.tsx
frontend/src/features/analysis-workspace/ui/contracts.ts
frontend/src/features/analysis-workspace/fixtures/index.ts
frontend/tests/projects-m5-analysis-workspace-contracts.spec.ts
frontend/scripts/check-m5-fixtures.test.mjs
docs/acceptance/M5_OPEN_DESIGN_HANDOFF.md
```

The OpenAPI generator used the pinned Python 3.14 backend image because the retained Linux-style
`.venv/lib64` blocks Windows `uv run`; `M5-ISSUE-0009` records the resolved local-only workaround.
The first source-scanning fixture assertion was corrected after a focused false negative and is
recorded as resolved `M5-ISSUE-0010`. Final serialization review also split strict PATCH payloads
from create-only identity fields; resolved `M5-ISSUE-0011` records that correction.

Stage 3 verification is limited to generated client, backend OpenAPI registration, mapper/contract/
fixture tests, TypeScript build, UI ownership boundaries, production mock guard and affected static
checks. No production route, full browser suite, real longitudinal E2E or final Exit Gate is run.

```text
READY_FOR_OPEN_DESIGN=NO
STAGE_RESULT=PASS_WITH_ISSUES
NEXT_STAGE_EXECUTED=NO
```

## 26. Stage 2 Recovery Implementation Record

The interrupted Stage 2 was completed additively without rewriting `0015_m5_analysis`.

Implemented scope:

- P0-Full independent two-group, paired two-group and simple linear regression with typed parameters,
  controlled assumptions, finite structured outputs, CI/effect/diagnostic fields and no Summary parsing;
- `0016_m5_figures` with FigurePlan, FigureRenderRun, Figure and FigureValidationIssue, enum extensions,
  same-project foreign keys, hashes/state checks and Analysis/Figure CodeArtifact exactly-one ownership;
- strict five-template FigureRenderer using Agg, Noto CJK fail-closed font discovery, fixed style/hash salt,
  bounded size/DPI, deterministic metadata, closed figures and result-derived comparison CI annotation;
- Figure API, degraded recommendation contract, Job/ProcessingRun Worker handler, confirmation Approval,
  download authorization and DatasetVersion/AnalysisRun invalidation propagation;
- atomic PNG/SVG/PDF/Code Artifact finalization with storage compensation and no formal Figure on failure;
- independent P0-Full golden fixture, five-template renderer tests, migration/model/registration tests and a
  real PostgreSQL API/Worker/Artifact vertical retained for the available database environment.

Focused verification: Ruff and Mypy passed; 47 engine/schema/model/renderer/golden/migration/registration
tests passed. The database-backed Figure vertical waited more than 90 seconds for the local fixture and
was boundedly terminated; `M5-ISSUE-0012` records the environment-only gap.

## 27. Stage 3 Contract Refresh Record

Stage 3 was rerun after Stage 2. OpenAPI and all four generated client files were regenerated through the
repository generator. `FiguresApi`, formal Figure queries/mutations, server-action-driven capabilities,
P0-Full result fixtures and formal FigurePlan/RenderRun/Figure/Artifact fixtures replaced the earlier
fail-closed placeholders. Unknown status/permissions and stale Approval still fail closed.

Focused verification: generated-client check passed; TypeScript compile and Vite production build passed;
M5 fixture, UI-boundary and production-mock guards passed. No production Analysis route, visual Workspace,
Playwright, real browser E2E or Stage 4 work was executed.

```text
READY_FOR_OPEN_DESIGN=YES
STAGE_RESULT=PASS_WITH_ISSUES
NEXT_STAGE_EXECUTED=NO
```

## 28. Stage 4 Entry And Independent Integration Record

Stage 4 inspected both the formal repository and the newer isolated Open Design delivery. The isolated
UI completed its Figure workflow and 276-combination visual matrix, but its authoritative Acceptance
Report explicitly remains `READY_FOR_CODEX_INTEGRATION=NO`. Per the frozen stage rule, Codex did not
copy the unaccepted UI, create a replacement visual page, wire the production route, or run a mocked
browser flow as production evidence. `M5-ISSUE-0013` records the blocking handback gate.

Independent Codex-owned work completed:

- corrected the stale Figure transport contract assertion and FigureRenderRun route metadata;
- expanded the typed fixture catalog from 46 to 53 with pending Approval, allowed Analysis/Figure Job
  lifecycle, mutation conflict, masked Artifact and denied download-scope combinations;
- corrected the pending AnalysisPlan fixture so Plan and Approval lifecycle facts agree;
- strengthened mutation execution guards for current known DatasetVersion/columns, Approval identity and
  payload hash, Job state/retryability, Figure relationships/issues and Artifact state/hash/masking/scope.

Focused contract verification passed. Production Route wiring, focused production Playwright and the
real DatasetVersion -> Analysis -> Figure -> download vertical remain pending a republished exact
`READY_FOR_CODEX_INTEGRATION=YES`; details are in `M5_VERTICAL_INTEGRATION_REPORT.md`.

Affected-file Biome, generated-client, fixture, boundary, production-mock, TypeScript and a production
build using the exact root locked Vite passed. Full frontend format/lint is held by generated OpenAPI CRLF
and the standard build script is held by an incomplete local `frontend/node_modules` tree; these local
Gate gaps are registered as `M5-ISSUE-0015` and `M5-ISSUE-0016` rather than hidden by generated-file churn
or dependency version changes.

```text
STAGE_RESULT=BLOCKED
NEXT_STAGE_EXECUTED=NO
```

## 29. Stage 5 Exit Record

Stage 5 stopped feature expansion and concentrated on the remaining Exit/M6 blockers. Common stale
Job recovery now synchronizes AnalysisRun and FigureRenderRun in the same transaction. Open Design
published an accepted YES handback, the five UI/CSS files were synchronized, and one production route
at `/projects/$projectId/analysis` completed the generated-client/adapter/query/Container boundary.

The first aggregate PostgreSQL runs exposed and resolved a committed FigurePlan refresh defect and two
Artifact test accounting defects. The complete no-database collection package collision and aggregate
Ruff/Mypy findings were also corrected without changing scientific behavior or weakening assertions.

Final verification:

- Ruff format/check: 205 files; Mypy: 120 source files;
- no-database: 165 passed, 2 skipped;
- real PostgreSQL: 380 passed, 2 skipped;
- shell Playwright: 159 passed, 1 skipped;
- focused M5 production route: 5 passed across desktop/tablet/390, Light/Dark and keyboard;
- Open Design: 53 fixtures, 318 combinations, 18 screenshots, zero failures/warnings/errors;
- isolated clean-room: all 39 recorded steps acceptable, with one LOW Bun advisory only;
- sole migration head: `0016_m5_figures`; empty upgrade, repeat and Alembic check pass.

Detailed Exit, completion, vertical and M6 consumption evidence is frozen in the Stage 5 acceptance
reports. No Commit, Tag or Push was created during Stage 5 execution and M6 was not executed. The user
later authorized a separate M5 closeout commit/tag/push after the Entry audit and output cleanup.

```text
M5_EXIT=PASS
M5_COMPLETION=APPROVED
M6_ENTRY=ALLOWED
STAGE_RESULT=PASS
NEXT_STAGE_EXECUTED=NO
```
