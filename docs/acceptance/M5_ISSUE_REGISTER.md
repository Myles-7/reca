# M5 Issue Register

Date: 2026-08-05
Owner: Codex

Final Stage 5 audit: all registered M5 issues are resolved. No unresolved issue blocks the M5 Exit
Gate or M6 Entry; retained LOW platform/supply-chain constraints are documented in the completion and
handoff reports.

## M5-ISSUE-0001

```yaml
stage: 0
severity: LOW
status: RESOLVED
area: dependency-spike/environment
authoritative_requirement: Verify the released numerical and rendering stack in the Python 3.14 Worker-compatible image.
observed_behavior: The first Debian fonts-noto-cjk download failed from the HTTP mirror before package installation.
evidence: apt reported a connection failure fetching fonts-noto-cjk_20220127+repack1-1_all.deb.
root_cause: Transient Debian mirror/network transport failure, not a package or runtime incompatibility.
affected_files:
  - backend/Dockerfile
  - docs/acceptance/M5_IMPLEMENTATION_PLAN.md
blocks_current_stage: false
blocks_m5_exit_gate: false
blocks_m6_entry: false
safe_continuation: Retry through HTTPS with bounded apt retries, then continue all independent numerical checks.
resolution: HTTPS plus Acquire::Retries=5 succeeded; the font package installed and CJK/missing-font rendering checks passed.
focused_verification: Worker-compatible image rendered all five chart types to PNG/SVG/PDF with Noto CJK and repeat-identical hashes.
security_or_scientific_integrity_impact: None; no result or Artifact was accepted during the failed download.
```

## M5-ISSUE-0002

```yaml
stage: 0
severity: MEDIUM
status: RESOLVED
area: contracts/state-machines
authoritative_requirement: Plan approval semantics, execution progress and repeat runs must remain distinct facts.
observed_behavior: The historical AnalysisPlan state list includes QUEUED/RUNNING/COMPLETED while the same document recommends keeping run state entirely on AnalysisRun.
evidence: STATE_MACHINES_AND_INVARIANTS sections 35-36 and the M5 Stage 0 prompt.
root_cause: Legacy combined-state documentation retained beside a newer recommended implementation note.
affected_files:
  - docs/data-model/STATE_MACHINES_AND_INVARIANTS.md
  - docs/acceptance/M5_IMPLEMENTATION_PLAN.md
blocks_current_stage: false
blocks_m5_exit_gate: false
blocks_m6_entry: false
safe_continuation: Apply the document's explicit recommended split and preserve APPROVED Plan semantics.
resolution: Frozen AnalysisPlan without execution states; AnalysisRun owns QUEUED through terminal/invalidation states.
focused_verification: Stage 1 table-driven transition tests and repeated-run service tests are required.
security_or_scientific_integrity_impact: Prevents stale approval ambiguity and prevents a repeat run from rewriting approval meaning.
```

## M5-ISSUE-0003

```yaml
stage: 0
severity: MEDIUM
status: RESOLVED
area: contracts/figure-render-run
authoritative_requirement: FigureRenderRun and Figure must be separate, with explicit retry/cancel/failure atomicity.
observed_behavior: The milestone requires FigureRenderRun but the data-model chapter does not define its complete fields or status enum.
evidence: M5_ANALYSIS_AND_FIGURES section 13.3/13.7 versus DATA_ANALYSIS_AND_FIGURE_MODELS chapter 17.
root_cause: The detailed model document specifies FigurePlan/Figure/Issue but leaves the required run object implicit.
affected_files:
  - docs/roadmap/milestones/M5_ANALYSIS_AND_FIGURES.md
  - docs/data-model/DATA_ANALYSIS_AND_FIGURE_MODELS.md
  - docs/acceptance/M5_IMPLEMENTATION_PLAN.md
blocks_current_stage: false
blocks_m5_exit_gate: false
blocks_m6_entry: false
safe_continuation: Define FigureRenderRun additively from the authoritative Job/ProcessingRun lifecycle without changing public scope.
resolution: Section 6 freezes fields, constraints and statuses parallel to AnalysisRun while keeping Figure lifecycle independent.
focused_verification: Stage 2 migration, transition, retry/cancel and atomic Artifact finalize tests are required.
security_or_scientific_integrity_impact: Prevents a render attempt or HTTP 202 from being misrepresented as a completed/confirmed Figure.
```

## M5-ISSUE-0004

```yaml
stage: 0
severity: LOW
status: RESOLVED
area: local-tooling/alembic
authoritative_requirement: Record and later verify the unique migration head and database migration health.
observed_behavior: No local uv/Alembic executable was available at Stage 0 start, so database-backed alembic heads/check was not run locally.
evidence: Stage 1 used python -m uv 0.9.26 plus the Python 3.14.3 focused Docker image; Alembic reported 0015_m5_analysis as the sole head and current database revision.
root_cause: Host PATH/tool environment differs from the repository's Docker/uv runtime.
affected_files:
  - backend/app/alembic/versions/0014_m4_data_quality.py
  - uv.lock
  - docs/acceptance/M5_IMPLEMENTATION_PLAN.md
blocks_current_stage: false
blocks_m5_exit_gate: false
blocks_m6_entry: false
safe_continuation: Use structural revision-chain evidence in Stage 0 and the pinned uv container for lock checks; defer database-backed Alembic validation to Stage 1 focused migration tests and Stage 5 full gate.
resolution: Stage 1 resolved the host entry through python -m uv and a pinned Docker image, verified one head, upgraded PostgreSQL through 0014 and 0015, and confirmed current=0015_m5_analysis. The clean empty-database repeat-upgrade remains a Stage 5 gate rather than this tooling issue.
focused_verification: python -m uv alembic heads; Docker alembic upgrade head; Docker alembic current; structural contiguous-chain tests.
security_or_scientific_integrity_impact: None; migration execution was transactional and the resulting head matched the tracked revision chain.
```

## M5-ISSUE-0005

```yaml
stage: 0
severity: LOW
status: RESOLVED
area: dependency-lock/tooling
authoritative_requirement: Synchronize the tracked uv workspace lock with uv 0.9.26 on Python 3.14.
observed_behavior: Running the standalone distroless ghcr.io/astral-sh/uv:0.9.26 image could not discover libc/common binaries.
evidence: uv reported that /bin/sh, /usr/bin/env, /bin/dash and /bin/ls were unavailable for managed-Python discovery.
root_cause: The standalone uv image is intentionally minimal and did not provide the OS probes needed by this Docker Desktop execution path.
affected_files:
  - pyproject.toml
  - backend/pyproject.toml
  - uv.lock
blocks_current_stage: false
blocks_m5_exit_gate: false
blocks_m6_entry: false
safe_continuation: Use the same pinned uv 0.9.26 binaries copied into python:3.14.3-slim-bookworm, matching the formal backend Dockerfile pattern.
resolution: The Python-based uv image resolved 133 packages, updated root uv.lock, and lock --check completed successfully.
focused_verification: Formal api/worker Docker builds succeeded and the worker imported all selected packages at the pinned versions.
security_or_scientific_integrity_impact: None; the uv binary version and lock inputs remained fixed and no dependency fallback was used.
```

## M5-ISSUE-0006

```yaml
stage: 1
severity: LOW
status: RESOLVED
area: migration/figure-scope
authoritative_requirement: Stage 0 froze nine M5 core tables in 0015, while the explicit Stage 1 prompt requires only the five Analysis models and forbids Figure implementation.
observed_behavior: Implementing all nine tables in Stage 1 would advance Figure schema before Stage 2; implementing five means the Stage 0 single-migration filename no longer contains every planned Figure table.
evidence: M5 Stage 1 model list versus M5_IMPLEMENTATION_PLAN.md section 6 and the Stage 2 "remaining migration models" instruction.
root_cause: The phased prompt is more specific and later than the Stage 0 aggregate migration sketch.
affected_files:
  - backend/app/alembic/versions/0015_m5_analysis_figures.py
  - backend/app/models.py
  - docs/acceptance/M5_IMPLEMENTATION_PLAN.md
blocks_current_stage: false
blocks_m5_exit_gate: true
blocks_m6_entry: true
safe_continuation: Keep 0015 as the single Analysis head and add FigurePlan/FigureRenderRun/Figure/FigureValidationIssue in one additive Stage 2 migration without editing 0015 after release.
resolution: Stage 2 added the four Figure tables in additive revision 0016_m5_figures, extended only the required existing enums, and retained 0015 unchanged.
focused_verification: Structural Alembic tests report one contiguous 0016_m5_figures head; SQLModel and migration guards verify same-project constraints and CodeArtifact exactly-one-owner semantics.
security_or_scientific_integrity_impact: None in Stage 1; no Figure object or Artifact is represented as implemented.
```

## M5-ISSUE-0007

```yaml
stage: 1
severity: MEDIUM
status: RESOLVED
area: worker/recovery
authoritative_requirement: Worker loss must not leave a completed business fact and stale attempts must be reconciled deterministically.
observed_behavior: Normal failure and explicit cancellation synchronize AnalysisRun, but a hard Worker loss after RUNNING may leave AnalysisRun RUNNING until the common stale-Job recovery executes; that recovery has no domain callback yet.
evidence: Analysis Worker commits RUNNING before deterministic execution; common Job recovery owns stale heartbeat failure independently of AnalysisRun.
root_cause: Existing Job recovery has no registered domain lifecycle callback API.
affected_files:
  - backend/app/analysis/service.py
  - backend/app/jobs/service.py
  - backend/app/workers/jobs.py
blocks_current_stage: false
blocks_m5_exit_gate: true
blocks_m6_entry: true
safe_continuation: Treat Job/ProcessingRun and absent Result/Artifact as authoritative; RUNNING AnalysisRun is not a completed result and all consumers fail closed unless status is COMPLETED.
resolution: Common fail_job now synchronizes queued/running/cancel-requested AnalysisRun and FigureRenderRun domain states before the shared transaction commits. Terminal domain facts are not downgraded and no second scheduler was introduced.
focused_verification: Real PostgreSQL API tests claim Analysis and Figure Jobs, expire their heartbeat, run common recovery, and assert Job/ProcessingRun/domain Run FAILED with JOB_TIMEOUT and zero new Result/Figure/CodeArtifact.
security_or_scientific_integrity_impact: Scientific integrity remains fail-closed because no Result or formal Artifact is finalized; operational status requires reconciliation before M5 Exit.
```

## M5-ISSUE-0008

```yaml
stage: 3
severity: HIGH
status: RESOLVED
area: openapi/figure-prerequisite
authoritative_requirement: Open Design must receive formal Figure DTOs, status/action projections and OpenAPI transport without guessing business facts.
observed_behavior: M5 Stage 2 was not executed; FigurePlan, FigureRenderRun, Figure, FigureValidationIssue, Figure API and generated client operations do not exist.
evidence: Current migration head is 0015_m5_analysis; OpenAPI contains Analysis paths but no Figure paths or schemas.
root_cause: The user advanced from completed Stage 1 directly to Stage 3, while Stage 3 depends on the Figure backend normally delivered by Stage 2.
affected_files:
  - backend/app/models.py
  - backend/app/api/main.py
  - frontend/openapi.json
  - frontend/src/features/analysis-workspace/model.ts
  - frontend/src/features/analysis-workspace/fixtures/index.ts
  - docs/acceptance/M5_OPEN_DESIGN_HANDOFF.md
blocks_current_stage: false
blocks_m5_exit_gate: true
blocks_m6_entry: true
safe_continuation: Use only the generated Figure transport, server-projected status/actions/stale facts and typed fixtures; keep production route wiring for Stage 4.
resolution: Stage 2 delivered Figure models/0016/renderer/Artifact/API/Worker contracts. Stage 3 regenerated OpenAPI/client, added FiguresApi, formal mappers/capabilities/queries/mutations and replaced every transport placeholder.
focused_verification: Generated client reports four files; Figure SDK paths exist; TypeScript/build, mapper/fixture, UI-boundary and production-mock guards pass; handoff readiness is YES.
security_or_scientific_integrity_impact: Prevents UI fixtures or local state from being misrepresented as a rendered, validated or confirmed scientific Figure.
```

## M5-ISSUE-0012

```yaml
stage: 2
severity: LOW
status: RESOLVED
area: focused-test/local-postgresql
authoritative_requirement: Run the focused real Figure API/Worker/Artifact vertical without expanding to the Stage 5 full PostgreSQL Gate.
observed_behavior: The focused test process waited more than 90 seconds for the local PostgreSQL fixture and produced no test output, so it was terminated by exact process ID.
evidence: backend/tests/api/routes/test_figures.py was collected but the local run emitted no result before the bounded termination; all no-database engine/renderer/migration/OpenAPI/Worker registration tests completed normally.
root_cause: Local PostgreSQL test service or connection fixture was unavailable/unresponsive; no application assertion failed.
affected_files:
  - backend/tests/api/routes/test_figures.py
  - docs/acceptance/M5_IMPLEMENTATION_PLAN.md
blocks_current_stage: false
blocks_m5_exit_gate: true
blocks_m6_entry: true
safe_continuation: Continue Stage 3 contract refresh from the structurally verified backend; retain the real vertical test for the Stage 5 PostgreSQL/Worker/MinIO Gate or rerun when the focused database service is available.
resolution: Stage 5 isolated clean-room provided an available PostgreSQL fixture and completed the Figure API/Worker/Artifact vertical without a hang.
focused_verification: The full real PostgreSQL suite passed 380 tests; the Figure vertical verified replay, exactly four render outputs, confirmation, download, no-disclosure, stale Worker recovery and failure compensation.
security_or_scientific_integrity_impact: No scientific fact was accepted from the interrupted run. Unit and contract paths remain fail-closed, and no formal Figure is created before complete Artifact finalization.
```

## M5-ISSUE-0009

```yaml
stage: 3
severity: LOW
status: RESOLVED
area: openapi-generation/local-tooling
authoritative_requirement: Regenerate the client from the current FastAPI OpenAPI document using the repository generator.
observed_behavior: Windows PowerShell did not support utf8NoBOM, uv run could not remove the retained Linux-style .venv/lib64 entry, and one retry used a bind-mount-relative output path that did not exist.
evidence: Set-Content rejected utf8NoBOM; uv 0.9.26 reported access denied removing the retained workspace .venv/lib64 link; the first formatting retry used a missing bind-relative OpenAPI path before the corrected repository-root bind succeeded.
root_cause: Windows PowerShell encoding capability and a cross-platform retained virtual-environment artifact, not an application or schema failure.
affected_files:
  - frontend/openapi.json
  - frontend/src/api/generated/
blocks_current_stage: false
blocks_m5_exit_gate: false
blocks_m6_entry: false
safe_continuation: Use the already pinned Python 3.14 backend image with bind-mounted current source and local-only placeholder settings, then run the normal frontend generator.
resolution: Docker generated current OpenAPI successfully; bun run generate-client produced four generated files and the generated-client check passed.
focused_verification: OpenAPI includes all nine Analysis operations plus approval_stale and AnalysisRun allowed_actions; generated client check reports four files.
security_or_scientific_integrity_impact: None; no secret or production data was used and generated content came from current source.
```

## M5-ISSUE-0010

```yaml
stage: 3
severity: LOW
status: RESOLVED
area: frontend/fixture-guard
authoritative_requirement: The focused fixture guard must verify stale Approval coverage without false negatives.
observed_behavior: The first static assertion searched for a literal approvalStale true property, while the typed fixture expresses the state through planStatus(APPROVED, true).
evidence: check:m5-fixtures initially reported 3 pass and 1 fail; the typed Playwright contract test independently confirmed the stale guard behavior.
root_cause: The source-scanning assertion targeted an implementation spelling rather than the typed fixture builder invocation.
affected_files:
  - frontend/scripts/check-m5-fixtures.test.mjs
blocks_current_stage: false
blocks_m5_exit_gate: false
blocks_m6_entry: false
safe_continuation: Update only the static assertion to recognize the typed builder form and retain the runtime contract test.
resolution: Guard now checks planStatus("APPROVED", true); all four fixture checks pass.
focused_verification: bun run check:m5-fixtures; focused M5 contract test for stale Approval run guard.
security_or_scientific_integrity_impact: None; the production mutation guard remained fail-closed throughout.
```

## M5-ISSUE-0011

```yaml
stage: 3
severity: MEDIUM
status: RESOLVED
area: frontend/analysis-plan-update
authoritative_requirement: AnalysisPlan PATCH must send only the strict update schema and must not attempt to rewrite immutable research-question or DatasetVersion identity.
observed_behavior: The initial mutation adapter reused the create payload, which structurally included research_question_version_id and dataset_version_id and would be rejected by the extra-forbid backend update schema.
evidence: Stage 3 final contract audit compared AnalysisPlanCreate and AnalysisPlanUpdate after TypeScript build; TypeScript structural assignment did not flag the extra runtime keys.
root_cause: Create and update share most fields, but using one serialized object ignored the strict runtime boundary.
affected_files:
  - frontend/src/features/analysis-workspace/mutations.ts
  - frontend/tests/projects-m5-analysis-workspace-contracts.spec.ts
blocks_current_stage: false
blocks_m5_exit_gate: false
blocks_m6_entry: false
safe_continuation: Introduce a dedicated typed apiPlanUpdate serializer and add a focused assertion for excluded immutable keys.
resolution: PATCH now serializes only AnalysisPlanUpdate fields; create-only identity fields are absent.
focused_verification: Focused M5 contract test asserts both immutable keys are absent and the method remains correctly projected.
security_or_scientific_integrity_impact: Prevents ambiguous or rejected attempts to rebind an approved scientific plan to a different question or data version.
```

## M5-ISSUE-0013

```yaml
stage: 4
severity: HIGH
status: RESOLVED
area: frontend/open-design-integration-gate
authoritative_requirement: Production Route and Container integration may begin only after the Open Design acceptance handback declares READY_FOR_CODEX_INTEGRATION=YES.
observed_behavior: The isolated Open Design Stage 3 delivered the complete Analysis/Figure UI and passed 276/276 visual combinations, but its authoritative Acceptance Report still declares READY_FOR_CODEX_INTEGRATION=NO because the Codex-owned contract guard and fixture combinations were incomplete at handback time.
evidence: The isolated Open Design acceptance report originally recorded PASS_WITH_GAPS, READY_FOR_CODEX_INTEGRATION=NO and a 5/6 protected contract guard. The formal repository then passed the corrected guard 6/6 and supplied the missing additive fixtures for the accepted rerun.
root_cause: Open Design completed before the formal Figure transport assertion, route metadata and lifecycle/download fixture matrix were refreshed by Codex.
affected_files:
  - frontend/src/features/analysis-workspace/ui/**
  - frontend/src/routes/**
  - docs/acceptance/M5_OPEN_DESIGN_ACCEPTANCE_REPORT.md
  - docs/acceptance/M5_VERTICAL_INTEGRATION_REPORT.md
blocks_current_stage: true
blocks_m5_exit_gate: true
blocks_m6_entry: true
safe_continuation: Complete and verify Codex-owned contracts, fixtures, Container guards, route parsing and test infrastructure. Do not copy the isolated UI, create a replacement page, wire the production Route or claim browser/vertical success until Open Design republishes READY_FOR_CODEX_INTEGRATION=YES.
resolution: The isolated Open Design worktree was resynchronized with the formal contracts and 53 fixtures. Its acceptance runner passed 318 combinations with zero failures, warnings or console errors and published READY_FOR_CODEX_INTEGRATION=YES. The accepted UI was then synchronized into the formal route.
focused_verification: Isolated M5 Open Design report records PASS/YES and 18 screenshots; the formal production route passes focused desktop/tablet/390, Light/Dark, keyboard, deep-link and no-disclosure browser tests.
security_or_scientific_integrity_impact: Prevents an unaccepted visual build or stale fixture semantics from being exposed as a production scientific Workspace.
```

## M5-ISSUE-0014

```yaml
stage: 4
severity: HIGH
status: RESOLVED
area: frontend/container-event-guard
authoritative_requirement: Container must revalidate permissionsKnown, knownStatus, allowed action, concurrency identity, DatasetVersion, Approval/hash, Run/Result/Figure relationships, retryability and Artifact scope immediately before every Event.
observed_behavior: The Stage 3 mutation guard checked the aggregate capability and primary object ID, but did not independently fail closed on several stale status, approval hash, DatasetVersion, Job retryability, blocking Figure issue, masked Artifact or read-scope combinations.
evidence: Focused Stage 4 review of frontend/src/features/analysis-workspace/mutations.ts and the Open Design M5-OD-0005 fixture gap.
root_cause: Stage 3 froze the transport and capability projection before Stage 4 production hardening and real interaction coverage.
affected_files:
  - frontend/src/features/analysis-workspace/mutations.ts
  - frontend/src/features/analysis-workspace/fixtures/index.ts
  - frontend/tests/projects-m5-analysis-workspace-contracts.spec.ts
  - frontend/scripts/check-m5-fixtures.test.mjs
blocks_current_stage: false
blocks_m5_exit_gate: false
blocks_m6_entry: false
safe_continuation: Keep the strengthened browser guard as defense in depth; Service authorization and state validation remain authoritative and must still reject stale requests.
resolution: Guards now require current known DatasetVersion and columns, matching current Analysis Approval payload hash, valid Job state/retryability, matching Figure relationships, nonblocking known validation issues, and AVAILABLE unmasked hashed Artifacts within read scope. Seven additive fixtures cover the missing lifecycle combinations.
focused_verification: M5 fixture guard 4/4, focused Playwright contract guard 6/6 and strict TypeScript compile pass.
security_or_scientific_integrity_impact: Prevents stale approval, unknown status, invalid job lifecycle, blocking Figure issues or unavailable Artifact content from being presented as an executable user action.
```

## M5-ISSUE-0015

```yaml
stage: 4
severity: LOW
status: RESOLVED
area: frontend/generated-format
authoritative_requirement: Affected frontend format and lint checks must pass without manually editing generated OpenAPI/client content.
observed_behavior: Full frontend Biome format and lint checks reject frontend/openapi.json because the Stage 3 generated file currently uses CRLF. All five Stage 4-owned TypeScript/test files pass focused Biome check unchanged.
evidence: bun run format:check and bun run lint both stop at frontend/openapi.json and print only line-ending normalization; generated-client check still reports four valid files.
root_cause: The Windows OpenAPI generation path retained CRLF while the repository Biome formatter expects LF.
affected_files:
  - frontend/openapi.json
blocks_current_stage: false
blocks_m5_exit_gate: true
blocks_m6_entry: true
safe_continuation: Keep generated content unchanged in Stage 4, use focused Biome checks for the modified files and normalize generation output through the repository generator before the Stage 5 frontend Gate.
resolution: The generated OpenAPI document was normalized through Biome after official regeneration; no generated schema content was manually changed.
focused_verification: Full frontend format and lint pass, and check-generated-client reports the expected four generated files.
security_or_scientific_integrity_impact: None; schema content and generated-client consistency pass, and no scientific value is changed.
```

## M5-ISSUE-0016

```yaml
stage: 4
severity: LOW
status: RESOLVED
area: frontend/local-dependency-layout
authoritative_requirement: The standard frontend production build command must resolve the locked Vite runtime.
observed_behavior: bun run build completes TypeScript but cannot find frontend/node_modules/vite/bin/vite.js. The same locked Vite 8.1.5 exists in root node_modules and the production build passes when invoked directly from that location.
evidence: Standard build reports MODULE_NOT_FOUND for frontend/node_modules/vite/bin/vite.js; bunx tsc passes and node ../node_modules/vite/bin/vite.js build completes 2331 transformed modules.
root_cause: The local frontend/node_modules tree is incomplete and shadows normal workspace dependency resolution; the root locked dependency installation is intact.
affected_files:
  - frontend/node_modules
  - node_modules
blocks_current_stage: false
blocks_m5_exit_gate: true
blocks_m6_entry: true
safe_continuation: Use the root locked Vite binary for this focused Stage 4 build. Restore the standard Bun workspace dependency layout before the Stage 5 frontend Gate without changing lock versions.
resolution: The locked Bun workspace dependencies were restored with a forced frozen install; the Windows workspace Vite shim is a local ignored junction to the exact root locked package and changes no dependency version.
focused_verification: Standard bun run build passes in both the formal worktree and isolated clean-room; generated, boundary, production-mock and fixture guards also pass.
security_or_scientific_integrity_impact: None; the fallback uses the exact locked local Vite version and no remote or unpinned dependency.
```

## M5-ISSUE-0017

```yaml
stage: 5
severity: LOW
status: RESOLVED
area: tests/collection
authoritative_requirement: The complete no-database suite must collect without module identity collisions.
observed_behavior: tests/analysis/test_engine.py and the existing tests/data_quality/test_engine.py were imported as the same top-level test_engine module.
evidence: The first complete no-database run stopped during collection with an import-file mismatch.
root_cause: The new M5 analysis test directory lacked a package marker.
affected_files:
  - backend/tests/analysis/__init__.py
blocks_current_stage: false
blocks_m5_exit_gate: false
blocks_m6_entry: false
safe_continuation: Add the package marker without renaming or weakening either test module.
resolution: Added the Analysis test package marker.
focused_verification: Complete no-database suite passes 165 tests with 2 opt-in skips.
security_or_scientific_integrity_impact: None; all original assertions remain enabled.
```

## M5-ISSUE-0018

```yaml
stage: 5
severity: MEDIUM
status: RESOLVED
area: figure/api-response
authoritative_requirement: FigurePlan creation must return the complete declared response after the transaction commits.
observed_behavior: The first real PostgreSQL Gate raised FastAPI ResponseValidationError because the committed SQLAlchemy object was expired and model_dump returned only the appended allowed_actions field.
evidence: First clean-room database run passed 379 tests and failed the Figure create response validation with required fields missing.
root_cause: create_plan did not refresh the persisted FigurePlan after commit before serialization.
affected_files:
  - backend/app/figures/service.py
  - backend/tests/api/routes/test_figures.py
blocks_current_stage: false
blocks_m5_exit_gate: false
blocks_m6_entry: false
safe_continuation: Refresh the same persisted row; do not synthesize response fields in the Router.
resolution: Figure service refreshes the committed FigurePlan before DTO mapping.
focused_verification: Real PostgreSQL Figure vertical and complete backend suite pass.
security_or_scientific_integrity_impact: Preserves server-persisted status/hash/version fields as the only response truth.
```

## M5-ISSUE-0019

```yaml
stage: 5
severity: LOW
status: RESOLVED
area: figure/artifact-test
authoritative_requirement: Figure tests must prove exactly four new render outputs and complete cleanup on failed finalize without ignoring the source Dataset Artifact.
observed_behavior: Two assertions hard-coded total storage size as four even though the test storage already contained the uploaded Dataset source object.
evidence: Success produced five total objects and failure compensation retained the same five historical objects.
root_cause: The focused test confused total object count with the render delta.
affected_files:
  - backend/tests/api/routes/test_figures.py
blocks_current_stage: false
blocks_m5_exit_gate: false
blocks_m6_entry: false
safe_continuation: Compare the successful render against its pre-render count and failed render against its exact pre-failure key set.
resolution: Assertions now require a +4 success delta and an unchanged key set after failed finalize.
focused_verification: Real PostgreSQL suite passes 380 tests and retains strict failure compensation checks.
security_or_scientific_integrity_impact: Strengthens proof that render failure neither leaves half-products nor deletes immutable historical inputs.
```

## M5-ISSUE-0020

```yaml
stage: 5
severity: LOW
status: RESOLVED
area: backend/static-quality
authoritative_requirement: Full backend Ruff format/check and Mypy must pass at M5 Exit.
observed_behavior: Aggregate static checks found two formatting/import-order differences and a renderer return annotation using plt.Figure, which Mypy could not resolve.
evidence: Initial full static run reported app/api/main.py, tests/conftest.py and app/figures/renderer.py only.
root_cause: Earlier stages ran affected subsets and Matplotlib exposes Figure through matplotlib.figure for static typing.
affected_files:
  - backend/app/api/main.py
  - backend/app/figures/renderer.py
  - backend/tests/conftest.py
blocks_current_stage: false
blocks_m5_exit_gate: false
blocks_m6_entry: false
safe_continuation: Apply the repository formatter and use the public Matplotlib Figure type without changing renderer behavior.
resolution: Formatted the two files and annotated _draw with matplotlib.figure.Figure.
focused_verification: Ruff reports 205 files formatted/clean and Mypy reports 120 source files clean.
security_or_scientific_integrity_impact: None; rendering behavior and deterministic outputs are unchanged.
```
