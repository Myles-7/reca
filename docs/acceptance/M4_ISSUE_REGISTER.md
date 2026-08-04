# RECA M4 Issue Register

```text
Milestone: M4
Stage: 5
Assessment date: 2026-08-04 (Asia/Shanghai)
Authority: current user instruction, AGENTS.md, M4 local authoritative documents, current repository facts
```

Status vocabulary: `OPEN`, `PLANNED`, `RESOLVED`, `DEFERRED`, `BLOCKED`.

## M4-ISSUE-0001

- stage: `0`
- severity: `MEDIUM`
- status: `RESOLVED`
- area: `local-environment / dependency-spike`
- authoritative_requirement: run the dependency Spike in the current Python 3.14 and uv environment without changing or replacing the user's working environment.
- observed_behavior: `uv` was not exposed as a PowerShell command and the repository root `.venv` is a Linux-layout Python 3.14.3 environment with no Windows executable.
- evidence: `Get-Command uv` returned no command; `.venv/pyvenv.cfg` records `/usr/local/bin`; Astral CPython 3.14.2 and uv 0.9.26 were found under the user profile.
- root_cause: the current PowerShell PATH does not include the installed uv script directory, while the checked workspace environment was created on another platform.
- affected_files: none.
- blocks_current_stage: `false`
- blocks_m4_exit_gate: `false`
- blocks_m5_entry: `false`
- safe_continuation: use the explicit uv executable and CPython 3.14.2 path; create the Spike venv under the OS temp directory; do not alter `.venv`.
- resolution: used `C:/Users/Li Cheng Xin/AppData/Roaming/Python/Python313/Scripts/uv.exe` with Astral CPython 3.14.2 and a temporary isolated venv.
- focused_verification: uv 0.9.26 resolved and installed the selected packages; Python reported 3.14.2; Alembic reported the unique head `0013_m3_evidence_matrix`.
- security_or_data_integrity_impact: none; no repository environment, user data, database, object storage or M3 file was changed.

## M4-ISSUE-0002

- stage: `0`
- severity: `LOW`
- status: `RESOLVED`
- area: `spike-test`
- authoritative_requirement: the Spike must report actual Pandera compatibility and deterministic FailureCase behavior.
- observed_behavior: the first Spike invocation failed before validation because it read `__version__` from `pandera.pandas`.
- evidence: `AttributeError: module 'pandera.pandas' has no attribute '__version__'`.
- root_cause: the version attribute belongs to the top-level `pandera` package, not the pandas API module.
- affected_files: none; the Spike was piped to the temporary interpreter and was never added to the repository.
- blocks_current_stage: `false`
- blocks_m4_exit_gate: `false`
- blocks_m5_entry: `false`
- safe_continuation: import top-level `pandera` for version metadata and retain `pandera.pandas` for dataframe APIs.
- resolution: corrected the temporary Spike and reran all cases successfully.
- focused_verification: lazy validation returned three stable failures, nullable/mixed/custom checks worked, and the source DataFrame remained unchanged.
- security_or_data_integrity_impact: none.

## M4-ISSUE-0003

- stage: `0`
- severity: `HIGH`
- status: `RESOLVED`
- area: `xlsx / dataset-version-contract`
- authoritative_requirement: preserve one immutable workbook Artifact, expose worksheets including hidden state, persist the selected read projection, and never use frontend local state as the formal selection.
- observed_behavior: the product and milestone require worksheet selection, but the current data model and API chapters do not define a persisted worksheet manifest or selection command.
- evidence: `M4_DATA_QUALITY.md` requires DatasetVersion worksheet and frontend worksheet selection; `DATA_ANALYSIS_AND_FIGURE_API.md` has upload/detail/preview but no worksheet-list or selection endpoint.
- root_cause: the workbook selection lifecycle was left implicit when the M4 summary contracts were composed.
- affected_files: planned `backend/app/models.py`, `backend/app/alembic/versions/0014_m4_data_quality.py`, dataset schemas/service/router, generated client, frontend data workspace and focused tests.
- blocks_current_stage: `false`
- blocks_m4_exit_gate: `true`
- blocks_m5_entry: `true`
- safe_continuation: freeze the additive minimum amendment in `M4_IMPLEMENTATION_PLAN.md`; implement it in stages 1 and 4 without adding a ninth core table.
- resolution: DatasetVersion persists the bounded manifest, selected worksheet and projection hash; the read and idempotent selection endpoints are implemented; selection is row-locked and unavailable after publication. Stage 5 registered the production Data Workspace Route and verified refresh/deep-link restoration, while the focused XLSX API test covers visible/hidden worksheet selection and immutable Artifact hash.
- focused_verification: Stage 1 parser/API tests pass for multi-sheet listing, hidden-sheet acknowledgement, persisted selection, no formula/external relationship execution and immutable Artifact hash. Stage 4 generated-client consistency, TypeScript build and fixture contract pass; refresh/deep-link/browser checks remain in Stage 5.
- security_or_data_integrity_impact: high if omitted because a browser-only selection can produce irreproducible previews or bind a DatasetVersion to the wrong worksheet.

## M4-ISSUE-0004

- stage: `0`
- severity: `MEDIUM`
- status: `RESOLVED`
- area: `domain-enums / state-machines`
- authoritative_requirement: all Dataset, DatasetVersion, DatasetColumn, Run/Issue, Plan/Action and Transformation states and transitions must be executable and fail closed.
- observed_behavior: DatasetVersion, CleaningPlan and DataQualityIssue states are defined, but Dataset, DatasetColumn confirmation, DataQualityRun and DataTransformation state vocabularies are not completely enumerated in the current detailed model chapters.
- evidence: targeted searches of `DATA_ANALYSIS_AND_FIGURE_MODELS.md` and `STATE_MACHINES_AND_INVARIANTS.md` found fields without complete local transition tables.
- root_cause: the documents define several fields structurally but defer part of their lifecycle semantics.
- affected_files: planned model enums, migration 0014, state service methods, API projections and parameterized transition tests.
- blocks_current_stage: `false`
- blocks_m4_exit_gate: `false`
- blocks_m5_entry: `false`
- safe_continuation: use the additive, conservative transition tables frozen in `M4_IMPLEMENTATION_PLAN.md`; unknown values and absent allowed actions fail closed.
- resolution: Stages 1-3 implemented every frozen enum and all eight model/migration mappings. Dataset, DatasetVersion, DatasetColumn, DataQualityRun, DataQualityIssue, CleaningPlan and DataTransformation transitions are enforced by service authorization, row locks, database constraints and explicit allowed-action projections. Unknown states and missing actions remain fail closed.
- focused_verification: final Stage 6 review full backend reports 347 passed and 2 skipped. Dataset/Version/Column API tests, quality Worker tests, strict CleaningPlan schema tests, Approval/Transformation integration tests and the real M4 vertical test cover valid and invalid transitions, failed/cancelled/retry behavior, stale approval/hash rejection and absence of AVAILABLE half-products.
- security_or_data_integrity_impact: medium; ambiguous terminal and invalidation states can expose partial versions or permit invalid writes.

## M4-ISSUE-0005

- stage: `0`
- severity: `MEDIUM`
- status: `RESOLVED`
- area: `api-contract-disambiguation`
- authoritative_requirement: stage 1 must implement one exact endpoint set and must not derive behavior from conflicting roadmap shorthand.
- observed_behavior: the milestone summary says `GET .../preview`, `/request-approval`, and a PATCH plan endpoint, while the detailed domain API uses `POST .../preview`, `/approval-requests`, and does not fully specify the plan PATCH body.
- evidence: comparison of `M4_DATA_QUALITY.md` sections 12.8 and `DATA_ANALYSIS_AND_FIGURE_API.md` sections 20.5-20.9.
- root_cause: the milestone endpoint list is a delivery summary and drifted from the detailed API contract.
- affected_files: `docs/acceptance/M4_IMPLEMENTATION_PLAN.md`; later dataset/data-quality routers, OpenAPI and generated client.
- blocks_current_stage: `false`
- blocks_m4_exit_gate: `false`
- blocks_m5_entry: `false`
- safe_continuation: apply the repository authority order: the detailed domain API controls exact methods and paths; the milestone file controls required capability.
- resolution: frozen exact paths are `POST /cleaning-plans/{id}/preview`, `POST /cleaning-plans/{id}/approval-requests`, and `POST /cleaning-plans/{id}/execute`; draft edits use `PATCH /cleaning-plans/{id}` with If-Match as the additive optimistic-lock contract.
- focused_verification: stage 3 OpenAPI contract tests and stage 4 generated-client consistency tests.
- security_or_data_integrity_impact: medium if unresolved because a client could treat a read-like preview or approval request as the wrong command and bypass idempotency/audit expectations.

## M4-ISSUE-0006

- stage: `0`
- severity: `MEDIUM`
- status: `RESOLVED`
- area: `ai-schema / deterministic-counts`
- authoritative_requirement: AI may explain issues and suggest whitelisted actions but cannot calculate formal counts, approve or execute.
- observed_behavior: the current `CleaningPlanSuggestion` example includes `expected_effect.affected_rows` and `row_count_change`, which could be mistaken for formal preview results.
- evidence: `AI_SCHEMA_CONTRACTS.md` section 35.2 compared with the current user instruction and M4 milestone section 12.9.
- root_cause: the suggestion schema includes explanatory estimates without explicitly separating them from deterministic preview authority.
- affected_files: `M4_IMPLEMENTATION_PLAN.md`; later PromptContract, suggestion mapper, API DTO and UI labels.
- blocks_current_stage: `false`
- blocks_m4_exit_gate: `false`
- blocks_m5_entry: `false`
- safe_continuation: retain schema compatibility but treat all model-produced numeric effect fields as non-authoritative; never copy them into Plan preview, Run counts or approval payload.
- resolution: the Service will whitelist actions, discard model effect counts from formal state, run deterministic preview, and expose only RECA-computed counts as formal values.
- focused_verification: stage 3 AI-schema tests inject incorrect model counts and assert that deterministic preview replaces them and the UI never labels them as completed facts.
- security_or_data_integrity_impact: medium scientific-integrity risk if model estimates are presented as measured counts.

## M4-ISSUE-0007

- stage: `0`
- severity: `LOW`
- status: `DEFERRED`
- area: `local-environment / temporary-spike-cleanup`
- authoritative_requirement: Spike artifacts must not become repository runtime data or alter the user's environment.
- observed_behavior: the isolated venv was created under `%TEMP%`, but the execution policy rejected the final recursive `Remove-Item` even after a separate path-boundary check confirmed it is inside `%TEMP%`.
- evidence: resolved target `D:/Temp/User/reca-m4-stage0-spike-20260804`; resolved temp root `D:/Temp/User`; `WITHIN_TEMP=True`; deletion command rejected by tool policy.
- root_cause: the command execution safety layer blocks recursive delete in this session; this is not a repository permission or package failure.
- affected_files: none in the repository; temporary package cache/venv only at the path above.
- blocks_current_stage: `false`
- blocks_m4_exit_gate: `false`
- blocks_m5_entry: `false`
- safe_continuation: leave the isolated temp venv untouched; it is outside all workspace roots, contains only downloaded packages and can be removed by normal OS temp cleanup or a separately authorized environment-maintenance action.
- resolution: deferred cleanup; no bypass attempted.
- focused_verification: `git status` contains no Spike runtime file, and the only M4 stage 0 paths are the two acceptance documents plus dependency manifest/lock/notices.
- security_or_data_integrity_impact: none; no Secret, user dataset, database, object-store content or repository file is present in the temporary venv.

## M4-ISSUE-0008

- stage: `1`
- severity: `MEDIUM`
- status: `RESOLVED`
- area: `xlsx-upload / temporary-file-boundary`
- authoritative_requirement: a valid XLSX upload must pass container preflight and be opened only through the frozen safe openpyxl mode; damaged files must map to a formal file error rather than an unhandled exception.
- observed_behavior: the first Stage 1 focused API run returned an unhandled 500 for a valid multi-sheet XLSX because the Router wrote every bounded upload to `upload.bin`, and openpyxl rejects filesystem paths without a supported workbook suffix before reading them.
- evidence: focused run `tests/datasets/test_parsers.py tests/api/routes/test_datasets.py tests/alembic/test_migrations.py` produced 21 passed and one failure at `openpyxl.reader.excel._validate_archive`; request log showed POST dataset upload status 500.
- root_cause: the temporary filename discarded the already validated display suffix, and the parser did not yet include openpyxl `InvalidFileException` in its damaged-workbook mapping.
- affected_files: `backend/app/api/routes/datasets.py`, `backend/app/datasets/parsers.py`, `backend/tests/api/routes/test_datasets.py`.
- blocks_current_stage: `false`
- blocks_m4_exit_gate: `false`
- blocks_m5_entry: `false`
- safe_continuation: retain the bounded temporary directory and derive only the allowlisted `.csv`/`.xlsx` suffix; continue all non-XLSX work while the focused case is rerun.
- resolution: the Router now preserves only an allowlisted parser suffix, and the parser maps `InvalidFileException` to `INVALID_WORKBOOK`; no user path component is used.
- focused_verification: the same focused parser/API/migration set passed after the fix; final Stage 1 run reports 25 passed including valid multi-sheet selection and damaged workbook rejection.
- security_or_data_integrity_impact: medium availability and error-contract impact; no file content, Secret, database row or object-store data was disclosed or modified incorrectly.

## M4-ISSUE-0009

- stage: `1`
- severity: `LOW`
- status: `RESOLVED`
- area: `local-environment / dependency-runner`
- authoritative_requirement: Stage 1 static and focused checks must run without replacing the repository's existing environment or damaging user changes.
- observed_behavior: Windows `uv run` attempted to use the repository root Linux-layout `.venv` and failed with access/incompatibility errors; one container command that invoked nested `uv run` created a separate incomplete `backend/.venv`.
- evidence: `uv run` reported failure to remove `reca/.venv/lib64`; the generated environment resolved inside the repository at `backend/.venv` and was absent before the command.
- root_cause: the shared workspace contains a Linux-layout root environment while Stage 1 commands run from Windows; nested container `uv run` selected the bind-mounted project path as its environment target.
- affected_files: none; the generated `backend/.venv` directory was removed after a same-shell resolved-path containment check.
- blocks_current_stage: `false`
- blocks_m4_exit_gate: `false`
- blocks_m5_entry: `false`
- safe_continuation: leave the root `.venv` untouched; use `UV_PROJECT_ENVIRONMENT` with a disposable Windows temp path for local static tools and direct compose entrypoint commands for PostgreSQL tests.
- resolution: all static checks ran from a disposable Stage 1 Windows environment; compose checks used the rebuilt locked image; both the accidental workspace environment and the disposable Stage 1 environment were deleted without touching root `.venv`.
- focused_verification: `backend/.venv` and the Stage 1 temp environment no longer exist, root `.venv` was not modified by cleanup, and focused checks completed successfully.
- security_or_data_integrity_impact: none; only downloaded package files were involved, with no Secret, database, object-store or user dataset content.

## M4-ISSUE-0010

- stage: `1`
- severity: `MEDIUM`
- status: `RESOLVED`
- area: `dataset-version-lifecycle / API-contract`
- authoritative_requirement: Stage 1 must audit formal DatasetVersion invalidation and ensure the Dataset current pointer references only an AVAILABLE version.
- observed_behavior: the detailed Dataset API chapter defines version reads but no invalidation command, while the Stage 1 prompt explicitly requires audited version invalidation and the frozen state machine includes AVAILABLE -> INVALIDATED.
- evidence: `DATA_ANALYSIS_AND_FIGURE_API.md` chapter 19 has no DatasetVersion invalidation path; the direct Stage 1 instruction lists version invalidation among formal audited actions.
- root_cause: the lifecycle transition was modeled but omitted from the detailed Dataset endpoint list.
- affected_files: `docs/acceptance/M4_IMPLEMENTATION_PLAN.md`, `backend/app/datasets/schemas.py`, `backend/app/datasets/service.py`, `backend/app/api/routes/datasets.py`, `backend/tests/api/routes/test_datasets.py`.
- blocks_current_stage: `false`
- blocks_m4_exit_gate: `false`
- blocks_m5_entry: `false`
- safe_continuation: use the existing AnalysisRun lifecycle naming convention and the common idempotent command contract; do not add generic DatasetVersion PATCH.
- resolution: added `POST /api/v1/dataset-versions/{version_id}/invalidate` with required Idempotency-Key and bounded reason. Service authorization and row locks precede transition details, invalidation is audited, and a current invalidated version is atomically replaced by the newest remaining AVAILABLE version or null.
- focused_verification: focused API test asserts AVAILABLE -> INVALIDATED, stable replay, audit evidence and removal of the invalidated current pointer.
- security_or_data_integrity_impact: medium data-integrity risk if current pointers can retain invalidated versions or invalidation is unaudited.

## M4-ISSUE-0011

- stage: `2`
- severity: `MEDIUM`
- status: `RESOLVED`
- area: `data-quality-run / persisted-scan-options`
- authoritative_requirement: Worker execution must resolve the exact versioned rule selection from persisted database facts and must not trust queue payload options.
- observed_behavior: the frozen Stage 1 `DataQualityRun` model stores ruleset ID/version/hash but has no separate JSON field for scan options such as sensitive-field detection.
- evidence: review of `backend/app/models.py` and `0014_m4_data_quality.py` found only `ruleset_id`, `rule_set_version` and `ruleset_hash`; Stage 2 requires the Worker to reconstruct the selected rule set without modifying 0014 or adding an unnecessary 0015.
- root_cause: Stage 1 froze rule identity but did not reserve a free-form scan-options field, while the Stage 2 API exposes one bounded option that changes the selected rule list.
- affected_files: `backend/app/data_quality/registry.py`, `backend/app/data_quality/service.py`, focused registry/API/Worker tests, and this plan/register.
- blocks_current_stage: `false`
- blocks_m4_exit_gate: `false`
- blocks_m5_entry: `false`
- safe_continuation: make every executable rule selection a canonical RECA-owned RuleSet identity; persist its content hash and require Worker resolution by exact ID/version/hash. Do not read the option from the queue or infer it from mutable defaults.
- resolution: the full rule set and the sensitive-detection-excluded rule set have distinct canonical content hashes. The API persists the selected hash, and the Worker only executes a registry entry whose ID/version/hash exactly matches; unknown or stale identities fail closed with `QUALITY_RULESET_STALE`.
- focused_verification: registry tests assert distinct stable hashes and exact persisted resolution; API idempotency includes version ID and payload; ProcessingRun metadata records the resolved selected rule IDs and option; Worker tests execute from database identity only.
- security_or_data_integrity_impact: medium if unresolved because a mutable or queue-supplied option could change sensitive-field access or make a historical Run irreproducible.

## M4-ISSUE-0012

- stage: `3`
- severity: `LOW`
- status: `DEFERRED`
- area: `cleaning-actions / competition-core`
- authoritative_requirement: Stage 3 may implement only the Stage 0 frozen Competition Core and must not create a general expression engine for derived columns.
- observed_behavior: `KEEP_ROWS`, `DROP_ROWS`, `IMPUTE_VALUE`, `CONVERT_UNIT` and `CREATE_DERIVED_COLUMN` are present in the shared enum but were not frozen into the M4 Competition Core.
- evidence: `M4_IMPLEMENTATION_PLAN.md` section 11 and the Stage 3 action matrix; focused schema tests cover all five unavailable action types.
- root_cause: the long-term domain vocabulary is intentionally broader than the bounded M4 executable whitelist.
- affected_files: `backend/app/cleaning/schemas.py`, `backend/app/cleaning/service.py`, `backend/tests/cleaning/test_engine_and_schemas.py`.
- blocks_current_stage: `false`
- blocks_m4_exit_gate: `false`
- blocks_m5_entry: `false`
- safe_continuation: parse these values only to return the stable `ACTION_NOT_AVAILABLE` error; never interpret parameters or build an expression/callable runtime.
- resolution: deferred beyond the M4 Competition Core. The common strict discriminator accepts their identity but Service execution rejects them before scope, Preview, Approval or Worker execution.
- focused_verification: parameterized tests assert every unavailable action fails closed; extra code, SQL, expression, callable and URL fields are rejected by `extra="forbid"`.
- security_or_data_integrity_impact: positive security boundary; treating enum presence as executable would create arbitrary-transformation risk.

## M4-ISSUE-0013

- stage: `3`
- severity: `MEDIUM`
- status: `RESOLVED`
- area: `data-transformation / object-storage-staging`
- authoritative_requirement: a failed transformation must not promote an AVAILABLE target and cleanup must be limited to resources staged by that execution.
- observed_behavior: the existing generated-Artifact helper writes immutable bytes before the surrounding database transaction commits, so a later promotion failure could leave an unreferenced object key.
- evidence: review of `create_generated_bytes_artifact` and the Stage 3 Worker transaction showed storage write precedes Artifact/DatasetVersion commit.
- root_cause: object storage and PostgreSQL do not share a transaction coordinator.
- affected_files: `backend/app/adapters/storage.py`, `backend/app/cleaning/service.py`, `backend/tests/api/routes/test_cleaning.py`.
- blocks_current_stage: `false`
- blocks_m4_exit_gate: `false`
- blocks_m5_entry: `false`
- safe_continuation: record only the newly generated object key and issue a best-effort delete on Worker failure; never scan or delete by project prefix.
- resolution: ObjectStorage now exposes exact-key deletion. The Worker tracks only its generated key, deletes it on post-upload failure, then persists FAILED Transformation/Plan/Job facts without changing the source or current pointer.
- focused_verification: Worker tamper test verifies failure leaves one AVAILABLE source version, no target/current mutation and FAILED Job/Transformation; adapter/static checks cover the exact-key deletion boundary.
- security_or_data_integrity_impact: removes bounded storage leakage while preserving immutable source data and avoiding broad deletion authority.

## M4-ISSUE-0014

- stage: `4`
- severity: `HIGH`
- status: `RESOLVED`
- area: `openapi / generated-client / response-contracts`
- authoritative_requirement: formal M4 DTOs, error codes, permissions and allowed actions must generate a stable client; generated files may not be hand-edited and the adapter may normalize but must not invent server facts.
- observed_behavior: Dataset, Data Quality and Cleaning routes generally omit explicit FastAPI `response_model` declarations, so the formal generated client types successful responses as `unknown` or `{ [key: string]: unknown }` despite the runtime returning structured envelopes.
- evidence: regenerated `frontend/openapi.json`; generated types such as `DatasetsUploadDataset...Responses[201]`, Dataset reads, quality reads and cleaning reads are `unknown`/open records; route decorators in `backend/app/api/routes/datasets.py`, `data_quality.py` and `cleaning.py` have no response models.
- root_cause: stages 1-3 implemented runtime response dictionaries without freezing them as OpenAPI-visible Pydantic response DTOs.
- affected_files: `backend/app/api/routes/datasets.py`, `backend/app/api/routes/data_quality.py`, `backend/app/api/routes/cleaning.py`, `frontend/openapi.json`, `frontend/src/api/generated/**`, `frontend/src/api/adapter/index.ts`.
- blocks_current_stage: `false`
- blocks_m4_exit_gate: `false`
- blocks_m5_entry: `false`
- safe_continuation: Stage 4 keeps RECA-owned structural DTOs and envelope-presence checks exclusively in the adapter; mappers treat missing permissions, allowed actions and unknown enums as unavailable/degraded. Open Design consumes only pure ViewModels and fixtures. Stage 5 must not treat unchecked fields as authoritative.
- resolution: Stage 6 added explicit Pydantic response DTOs/envelopes for Dataset, DatasetVersion, DatasetColumn, DataQualityRun/Issue, CleaningPlan, DataTransformation and comparison responses; every M4 route now publishes an explicit success response model and correct 200/201/202 status. OpenAPI and the Hey API client were regenerated through the formal workflow. Adapter envelope checks remain only as bounded runtime defense, while generated shapes are authoritative and mappers still fail closed for future enum values.
- focused_verification: `test_m4_openapi.py` asserts all M4 success responses reference named schemas; generated-client consistency, frontend type/build, adapter/query tests and complete clean-room acceptance pass. Generated success responses are no longer operation-level `unknown`.
- security_or_data_integrity_impact: unchecked transport shapes could otherwise turn missing permission or stale-state fields into optimistic UI behavior; the current adapter/mapper boundary prevents that but is not the final OpenAPI contract.

## M4-ISSUE-0015

- stage: `4`
- severity: `MEDIUM`
- status: `RESOLVED`
- area: `data-workspace / production-read-integration`
- authoritative_requirement: the single Data Workspace must project version selection/comparison/lineage and Transformation/Job state from formal backend facts rather than browser-local state.
- observed_behavior: the backend exposes selected-version reads and pairwise version comparison, but no Dataset version-history list endpoint and no standalone DataTransformation detail endpoint. The production query can only retain navigation intents and project Transformation facts from an execute response or CleaningPlan linkage.
- evidence: current M4 route inventory and generated client contain DatasetVersion get and version-comparison operations but no version collection or Transformation get operation; `loadDataWorkspace` records these capabilities as integration pending.
- root_cause: stages 1-3 focused on upload/current-version and execute-result vertical paths, leaving read aggregation needed by the final workspace shell unspecified.
- affected_files: `backend/app/api/routes/datasets.py`, `backend/app/api/routes/cleaning.py`, `frontend/src/features/data-workspace/queries.ts`, `frontend/src/features/data-workspace/model.ts`, `frontend/src/features/data-workspace/route-contract.ts`.
- blocks_current_stage: `false`
- blocks_m4_exit_gate: `false`
- blocks_m5_entry: `false`
- safe_continuation: retain `select-version` and `compare-versions` as navigation intents, expose integration-pending reasons, and keep production controls disabled when no server capability/fact exists. Typed fixtures may show the intended server projection but must not simulate persistence or success.
- resolution: Stage 6 added `GET /datasets/{dataset_id}/versions` and `GET /data-transformations/{transformation_id}` with project authorization and no-disclosure semantics. The production query consumes both generated operations, verifies project/Dataset/Plan/source-Version/Job relationships, projects formal history and Transformation facts, and removes the integration-pending messages. Selection remains a navigation intent and never mutates current-version truth.
- focused_verification: focused API tests cover ordered history, Viewer read and outsider 404; Transformation detail is checked against completed lineage. Production Playwright verifies deep-link refresh, formal history rendering, cross-Dataset rejection, mobile Light/Dark and field confirmation. Full shell Playwright reports 148 passed and 1 skipped.
- security_or_data_integrity_impact: prevents local selection or stale execute responses from being presented as current lineage/transformation truth.

## M4-ISSUE-0016

- stage: `5`
- severity: `HIGH`
- status: `RESOLVED`
- area: `frontend / dataset-column-confirmation`
- authoritative_requirement: editing and confirming a field must persist the backend DatasetColumn confirmation fact; a displayed confirmed type must not be mistaken for formal confirmation.
- observed_behavior: the accepted Workspace sent `confirmed_type` but omitted `confirmation_status`, so the API returned success while the field remained `UNCONFIRMED`.
- evidence: the first real M4 vertical run received `confirmation_status=UNCONFIRMED` after the column PATCH.
- root_cause: the UI contract projected editable type and sensitivity but omitted the backend's explicit confirmation transition.
- affected_files: `frontend/src/features/data-workspace/ui/contracts.ts`, `ui/DataWorkspace.tsx`, `mutations.ts`, `mappers.ts`, focused production Route test.
- blocks_current_stage: `false`
- blocks_m4_exit_gate: `false`
- blocks_m5_entry: `false`
- safe_continuation: require an explicit confirmation checkbox and send only the backend enum; unknown confirmation states remain fail closed.
- resolution: added typed `UNCONFIRMED | CONFIRMED` intent, explicit UI confirmation, API mapping and known `UNCONFIRMED` projection.
- focused_verification: Playwright intercept asserts `confirmation_status=CONFIRMED`; the real API vertical chain confirms the field and continues through quality, approval and transformation.
- security_or_data_integrity_impact: prevents an unconfirmed inferred field from being presented or consumed as a reviewed formal definition.

## M4-ISSUE-0017

- stage: `5`
- severity: `LOW`
- status: `RESOLVED`
- area: `focused-test / isolation`
- authoritative_requirement: M4 focused tests must compose without assuming an otherwise empty milestone database.
- observed_behavior: the combined Dataset, Quality and Cleaning suite failed because one Cleaning assertion compared every DatasetVersion in the session to its current source version.
- evidence: the first combined focused run reported `10 passed, 1 failed`; unrelated versions created by earlier focused modules appeared in the global query.
- root_cause: the assertion was not scoped to the test's Dataset ID.
- affected_files: `backend/tests/api/routes/test_cleaning.py`.
- blocks_current_stage: `false`
- blocks_m4_exit_gate: `false`
- blocks_m5_entry: `false`
- safe_continuation: scope version assertions to the owned Dataset; do not truncate or reset shared developer data.
- resolution: restricted the assertion to `DatasetVersion.dataset_id == dataset_id`.
- focused_verification: the same combined focused suite passes `11/11` against the isolated Stage 5 PostgreSQL database.
- security_or_data_integrity_impact: none; this was test selection coupling only.

## M4-ISSUE-0018

- stage: `6`
- severity: `LOW`
- status: `DEFERRED`
- area: `frontend dependency advisory`
- authoritative_requirement: dependency audits must have no unresolved critical, high or moderate advisory before M5 entry; LOW advisories may be documented when no compatible locked fix exists.
- observed_behavior: `bun audit` reports GHSA-4x5r-pxfx-6jf8 for transitive `@babel/core <=7.29.0`, reachable through `@tanstack/router-plugin` development tooling.
- evidence: clean-room `node-security-audit.log` reports exactly one LOW advisory and no critical, high or moderate advisory.
- root_cause: the current compatible router-plugin toolchain resolves an affected Babel range; `bun update` has no compatible locked remediation at the time of M4 closeout.
- affected_files: `bun.lock`, upstream frontend build dependencies.
- blocks_current_stage: `false`
- blocks_m4_exit_gate: `false`
- blocks_m5_entry: `false`
- safe_continuation: do not process untrusted source maps in privileged build contexts; monitor the advisory and update the router/Babel toolchain when a compatible release is available.
- resolution: deferred as a documented LOW development-tooling advisory; no production runtime Secret or dataset exposure was observed.
- focused_verification: Python dependency audit passes; repository and container log Secret scans pass; clean-room source/image policy, license records and locked dependency install pass.
- security_or_data_integrity_impact: low and limited to development/build input handling; no M4 runtime data path uses Babel source-map parsing.

## M4-ISSUE-0019

- stage: `6-final-review`
- severity: `HIGH`
- status: `RESOLVED`
- area: `api / runtime-response-validation`
- authoritative_requirement: explicit M4 response DTOs must govern both OpenAPI generation and runtime serialization; command handlers may not bypass response-model validation.
- observed_behavior: eleven Dataset, Quality and Cleaning command handlers declared `response_model` but returned `JSONResponse` directly. FastAPI therefore published the correct schema while skipping runtime response validation and serialization for those commands.
- evidence: final code review of `datasets.py`, `data_quality.py` and `cleaning.py`; FastAPI returns a supplied `Response` without applying the route response model.
- root_cause: Stage 6 hardened the OpenAPI declaration without removing the earlier dynamic-status `JSONResponse` implementation pattern.
- affected_files: M4 route modules, `test_m4_openapi.py`, OpenAPI/generated client and adapter boundary.
- blocks_current_stage: `false`
- blocks_m4_exit_gate: `false`
- blocks_m5_entry: `false`
- safe_continuation: return ordinary envelope dictionaries under fixed decorator status codes so FastAPI validates and serializes every success response; keep direct Response objects only for endpoints whose transport semantics require them.
- resolution: all eleven M4 command handlers now return ordinary typed envelope dictionaries. A focused regression enumerates the command functions and rejects a Response return annotation, while real Dataset/Quality/Cleaning API tests exercise the validated payloads.
- focused_verification: focused M4 API/OpenAPI/vertical set passes 13/13; full backend passes 347/347 executed with 2 opt-in skips; final isolated clean-room passes all 39 steps except the accepted LOW-only Node advisory classification.
- security_or_data_integrity_impact: prevents malformed or incomplete permission, state, lineage and idempotency projections from reaching M5 despite a nominally correct OpenAPI contract.

## M4-ISSUE-0020

- stage: `6-final-review`
- severity: `MEDIUM`
- status: `RESOLVED`
- area: `data-transformation / read-model-provenance`
- authoritative_requirement: the formal Transformation detail projection must preserve available output, log and ProcessingRun provenance without inventing absent artifacts.
- observed_behavior: `DataTransformation.log_artifact_id` existed in persistence but was omitted from `transformation_data`, the response DTO, OpenAPI and the frontend transport DTO.
- evidence: comparison of `DataTransformation` model fields with `m4_responses.py`, `cleaning/service.py` and the generated frontend type.
- root_cause: the Stage 6 standalone Transformation read was assembled from the execution summary projection and missed one nullable provenance field.
- affected_files: `backend/app/cleaning/service.py`, `backend/app/api/m4_responses.py`, `frontend/openapi.json`, generated types, adapter DTO, cleaning API regression and M5 handoff.
- blocks_current_stage: `false`
- blocks_m4_exit_gate: `false`
- blocks_m5_entry: `false`
- safe_continuation: expose the persisted nullable ID exactly as stored; `null` means no separate log Artifact was produced and must not be replaced by the output Artifact or local UI state.
- resolution: added nullable `log_artifact_id` to the service projection, Pydantic DTO, OpenAPI/generated client and frontend adapter contract; the completed Transformation API test asserts the key remains present and honestly null for the current deterministic worker path.
- focused_verification: OpenAPI requires the nullable field, generated-client consistency and production build pass, focused M4 browser contracts pass 10/10, and full shell Playwright passes 148 with 1 opt-in skip.
- security_or_data_integrity_impact: preserves provenance completeness while preventing M5 from assuming that an output Artifact is also a Transformation log.

## Current Gate View

| Issue | Current stage | M4 Exit | M5 Entry |
| --- | --- | --- | --- |
| M4-ISSUE-0001 | clear | clear | clear |
| M4-ISSUE-0002 | clear | clear | clear |
| M4-ISSUE-0003 | clear | clear | clear |
| M4-ISSUE-0004 | clear | clear | clear |
| M4-ISSUE-0005 | clear | clear | clear |
| M4-ISSUE-0006 | clear | clear | clear |
| M4-ISSUE-0007 | clear | clear | clear |
| M4-ISSUE-0008 | clear | clear | clear |
| M4-ISSUE-0009 | clear | clear | clear |
| M4-ISSUE-0010 | clear | clear | clear |
| M4-ISSUE-0011 | clear | clear | clear |
| M4-ISSUE-0012 | clear | clear | clear |
| M4-ISSUE-0013 | clear | clear | clear |
| M4-ISSUE-0014 | clear | clear | clear |
| M4-ISSUE-0015 | clear | clear | clear |
| M4-ISSUE-0016 | clear | clear | clear |
| M4-ISSUE-0017 | clear | clear | clear |
| M4-ISSUE-0018 | clear | clear | clear |
| M4-ISSUE-0019 | clear | clear | clear |
| M4-ISSUE-0020 | clear | clear | clear |

No BLOCKER, CRITICAL, unresolved HIGH, Secret exposure, destructive migration requirement or M5+ scope dependency remains after Stage 6. Deferred LOW issues are `M4-ISSUE-0007`, `M4-ISSUE-0012` and `M4-ISSUE-0018`; none permits M5 to rewrite M4 facts or weakens the Exit Gate.

## Codex Stage 6 Closeout

- stage: `6`
- status: `PASS`
- owner: `Codex`
- decision: `M4_EXIT=PASS`, `M5_ENTRY=ALLOWED`
- migration_head: `0014_m4_data_quality`
- production_integration_complete: `true`

Stage 6 resolved the remaining response-contract, read-model and lifecycle blockers, then passed the
complete repository and isolated clean-room Gates. Final full backend reports `347 passed, 2 skipped`;
complete shell Playwright reports `148 passed, 1 skipped`; all 39 clean-room steps pass except the
explicitly accepted LOW-only Node audit classification. The final details and frozen M5 boundary are
recorded in `M4_EXIT_GATE_REPORT.md`, `M4_COMPLETION_REPORT.md` and `M4_TO_M5_HANDOFF.md`.

## Codex Stage 4.5 Integration Readiness Repair

- stage: `4.5`
- status: `PASS`
- owner: `Codex`
- decision: `CODEX_STAGE_5_ENTRY=ALLOWED`
- production_integration_complete: `false`

Codex synchronized the accepted M4 Data Workspace UI and Stage 3 Playwright suite from the isolated
Open Design worktree by exact SHA-256 match. The formal repository then resolved
`M4-OD-0004/0005/0007/0008/0010/0014` within Codex-owned paths:

- empty projects use a ready zero-dataset ViewModel with formal upload capability;
- XLSX `CREATING` fixtures allow explicit visible/hidden worksheet selection;
- CleaningPlan events use a strict five-variant typed Action projection derived from the backend
  discriminated union, with fail-closed mapping and runtime guards;
- Plan/Approval/Transformation/Job fixture facts and capabilities are state-consistent;
- comparison intent requires a known Version with a formal parent;
- OpenAPI snapshot and adapter formatting no longer block full frontend gates.

Verification in the formal repository:

```text
frontend format:check: PASS
frontend lint: PASS
M4 fixture guard: PASS 8/8
UI boundary guard: PASS 4/4
production mock guard: PASS 6/6
generated client consistency: PASS
production build: PASS
Codex M4 focused contract + browser suite: PASS 22/22
30 fixtures x 3 viewports x Light/Dark: PASS
```

`M4-OD-0009` remains optional non-blocking duplicate-Issue pixel coverage.
`M4-OD-0015` remains a non-blocking Bun/Chinese-path single-file mirror limitation. Neither is a
Stage 5 entry blocker. At Stage 4.5, main milestone `M4-ISSUE-0014` and `M4-ISSUE-0015` remained
open for their original Stage 5/6 production response-model and read-model scope; Stage 4.5 did not
falsely close them.

```text
READY_FOR_CODEX_INTEGRATION=YES
CODEX_STAGE_4_5_RESULT=PASS
CODEX_STAGE_5_ENTRY=ALLOWED
NEXT_STAGE_EXECUTED=NO
```
