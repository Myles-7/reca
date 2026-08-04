# RECA M4 Frozen Implementation Plan

```text
Milestone: M4 Data Quality and Versioning
Stage completed by this document: 0 only
Plan status: FROZEN FOR STAGE 1 IMPLEMENTATION
Assessment date: 2026-08-04 (Asia/Shanghai)
M4 business implementation started: NO
Next stage executed: NO
```

## 1. Authority and Entry Decision

Read in stage 0: root `AGENTS.md`; the M3 completion, exit and handoff reports; public roadmap Entry/Exit and M4 status; M4 milestone; product chapters 19-20; data-model chapters 13-15; state-machine invariants; detailed data API chapters 19-20; common idempotency/If-Match/Job/error contracts; CleaningPlanSuggestion and ModelInvocation contracts; file/model security; contract/integration/security tests; ADR-004; Pandera/GX/DVC research; current M3 models, migration 0013, Artifact/Approval/Job/Worker/API/MinIO patterns, generated client, project routes and focused tests.

Current authoritative facts override old snapshots:

- M3 reports `M3_EXIT=PASS`, `M3_COMPLETION=APPROVED`, `M4_ENTRY=ALLOWED`.
- Roadmap still records M4 as `PLANNED`; stage 0 does not change that status.
- The unique migration head is `0013_m3_evidence_matrix`.
- M3 is intentionally uncommitted and must remain intact.
- The root `.venv` is not executable from current Windows PowerShell; stage execution must use a valid explicit uv/Python entry without replacing it.
- Public API details come from `DATA_ANALYSIS_AND_FIGURE_API.md`; milestone endpoint lists are capability summaries.

Stage 1 may begin directly from this plan. Stage 0 makes no claim that any M4 endpoint, table, Job, UI or business workflow exists.

## 2. Non-Destructive Recovery Checkpoint

### 2.1 Git and migration identity before M4 edits

```text
branch: feat/m2-research-literature
HEAD: 0e3c39dde65feaa8f784fd5fcfb1055cb557bb3c
migration head: 0013_m3_evidence_matrix
tracked modified files: 41
untracked files: 80
git diff --stat: 41 files changed, 12154 insertions(+), 4633 deletions(-)
commit/tag/push/stash created: NO
```

Recovery hashes:

```text
backend/app/alembic/versions/0013_m3_evidence_matrix.py d0458cb3cacbb975d957c71a748267671b920d29831c91443a341195a26d71f3
docs/acceptance/M3_COMPLETION_REPORT.md 7868a60d80cfca40d3e106213e02ff29b4a07fe70baafbd626b9f30f7d6155bc
docs/acceptance/M3_EXIT_GATE_REPORT.md 0bfb0234f8221b0ef3592311e55fe1ce8b032c17e5473e86f7d9502140f854bd
docs/acceptance/M3_TO_NEXT_MILESTONES_HANDOFF.md 6eb96d12c221cd066b5b303ce3d485494c9979a44689a3c811623a22c88c6eda
```

### 2.2 M3 tracked modifications present before M4 edits

```text
.env.example
THIRD_PARTY_NOTICES.md
backend/app/agents/prompts.py
backend/app/agents/prompts/prompt-manifest.yaml
backend/app/agents/service.py
backend/app/api/main.py
backend/app/core/config.py
backend/app/main.py
backend/app/models.py
backend/app/projects/service.py
backend/app/workers/jobs.py
backend/tests/agents/test_model_invocation_service.py
backend/tests/agents/test_prompt_manifest.py
backend/tests/alembic/test_migration_runtime.py
backend/tests/alembic/test_migrations.py
backend/tests/conftest.py
backend/tests/core/test_config.py
bun.lock
docker-compose.yml
docs/IMPLEMENTATION_ROADMAP.md
docs/contracts/AI_SCHEMA_CONTRACTS.md
docs/development/FRONTEND_DESIGN_INTEGRATION_RULES.md
docs/source-research/projects/pdfjs.md
frontend/openapi.json
frontend/package.json
frontend/playwright.shell.config.ts
frontend/src/api/adapter/index.ts
frontend/src/api/generated/index.ts
frontend/src/api/generated/sdk.gen.ts
frontend/src/api/generated/types.gen.ts
frontend/src/components/ui/sidebar.tsx
frontend/src/design-preview/DesignPreviewWorkbench.tsx
frontend/src/routeTree.gen.ts
frontend/src/routes/_layout/projects.$projectId_.literature.tsx
frontend/tests/projects-document.spec.ts
frontend/tests/projects-literature.spec.ts
frontend/tests/projects-m2-frontend-contracts.spec.ts
frontend/tests/projects-mappers.spec.ts
frontend/tests/projects-query-plan.spec.ts
frontend/tests/utils/privateApi.ts
scripts/m0-acceptance.ps1
```

### 2.3 M3 untracked files present before M4 edits

The exact untracked snapshot is grouped without changing ownership:

```text
.playwright-cli/page-2026-08-02T09-08-46-952Z.yml
.playwright-cli/page-2026-08-02T09-09-05-324Z.yml
.playwright-cli/page-2026-08-02T09-09-51-427Z.yml
.playwright-cli/page-2026-08-02T09-09-59-202Z.yml
.playwright-cli/page-2026-08-02T09-10-08-464Z.yml
.playwright-cli/page-2026-08-02T09-20-42-016Z.yml
.playwright-cli/page-2026-08-02T09-26-35-771Z.yml
backend/app/adapters/model_provider.py
backend/app/agents/prompts/evidence-set-summary-1.0.0.txt
backend/app/agents/prompts/literature-extraction-1.0.0.txt
backend/app/agents/prompts/topic-candidate-generation-1.0.0.txt
backend/app/alembic/versions/0013_m3_evidence_matrix.py
backend/app/api/routes/evidence.py
backend/app/evidence/__init__.py
backend/app/evidence/analysis.py
backend/app/evidence/extraction.py
backend/app/evidence/locator.py
backend/app/evidence/retrieval.py
backend/app/evidence/review.py
backend/app/evidence/schemas.py
backend/tests/adapters/test_model_provider.py
backend/tests/api/routes/test_evidence.py
backend/tests/api/routes/test_evidence_openapi.py
backend/tests/evidence/test_analysis_schemas.py
backend/tests/evidence/test_analysis_workflow.py
backend/tests/evidence/test_database_constraints.py
backend/tests/evidence/test_extraction_workflow.py
backend/tests/evidence/test_locator.py
backend/tests/evidence/test_models.py
backend/tests/evidence/test_retrieval.py
backend/tests/evidence/test_schemas.py
backend/tests/golden/test_m3_literature_evidence_golden.py
backend/tests/integration/test_m3_vertical_demo.py
docs/acceptance/M3_COMPLETION_REPORT.md
docs/acceptance/M3_EXIT_GATE_REPORT.md
docs/acceptance/M3_IMPLEMENTATION_PLAN.md
docs/acceptance/M3_ISSUE_REGISTER.md
docs/acceptance/M3_OPEN_DESIGN_HANDOFF.md
docs/acceptance/M3_TO_NEXT_MILESTONES_HANDOFF.md
docs/acceptance/M3_VERTICAL_INTEGRATION_REPORT.md
frontend/.tanstack/tmp/095b64cc-91366b6986f606cd430aea1d3827c3fc
frontend/.tanstack/tmp/802c2145-91366b6986f606cd430aea1d3827c3fc
frontend/scripts/check-m3-fixtures.test.mjs
frontend/src/features/evidence-analysis/containers/EvidenceAnalysisContainer.tsx
frontend/src/features/evidence-analysis/fixtures/index.ts
frontend/src/features/evidence-analysis/mappers.ts
frontend/src/features/evidence-analysis/model.ts
frontend/src/features/evidence-analysis/mutations.ts
frontend/src/features/evidence-analysis/queries.ts
frontend/src/features/evidence-analysis/ui/EvidenceAnalysisWorkspace.tsx
frontend/src/features/evidence-analysis/ui/contracts.ts
frontend/src/features/evidence-analysis/ui/evidence-analysis-workspace.css
frontend/src/features/evidence-matrix/containers/EvidenceMatrixContainer.tsx
frontend/src/features/evidence-matrix/fixtures/index.ts
frontend/src/features/evidence-matrix/mappers.ts
frontend/src/features/evidence-matrix/model.ts
frontend/src/features/evidence-matrix/mutations.ts
frontend/src/features/evidence-matrix/queries.ts
frontend/src/features/evidence-matrix/ui/EvidenceMatrixWorkspace.tsx
frontend/src/features/evidence-matrix/ui/PdfEvidenceViewer.tsx
frontend/src/features/evidence-matrix/ui/contracts.ts
frontend/src/features/evidence-matrix/ui/evidence-matrix-workspace.css
frontend/src/features/literature/M3LiteratureWorkspacePage.tsx
frontend/src/features/literature/m3-literature-workspace.css
frontend/src/features/literature/m3-route-contract.ts
frontend/src/features/topic-candidates/containers/TopicCandidatesContainer.tsx
frontend/src/features/topic-candidates/fixtures/index.ts
frontend/src/features/topic-candidates/mappers.ts
frontend/src/features/topic-candidates/model.ts
frontend/src/features/topic-candidates/mutations.ts
frontend/src/features/topic-candidates/queries.ts
frontend/src/features/topic-candidates/ui/TopicCandidatesWorkspace.tsx
frontend/src/features/topic-candidates/ui/contracts.ts
frontend/src/features/topic-candidates/ui/topic-candidates-workspace.css
frontend/tests/m3-stage7-vertical.spec.ts
frontend/tests/projects-m3-evidence.spec.ts
frontend/tests/utils/deferred.ts
frontend/tests/utils/random.ts
tests/golden/m3_literature_evidence/v1/README.md
tests/golden/m3_literature_evidence/v1/manifest.json
```

Rules for every M4 stage: no reset, clean, stash pop, destructive checkout, history rewrite or bulk generated-file overwrite; inspect overlapping M3 edits before each patch; do not remove `.playwright-cli` or `.tanstack` artifacts unless separately authorized.

## 3. Frozen Scope

### 3.1 Competition Core / P0-Must

- CSV and XLSX upload to one immutable original Artifact and one reproducible DatasetVersion projection.
- Multi-sheet workbook listing, explicit persisted selection, preview and DatasetColumn extraction.
- Dataset identity edit, Dataset/Column optimistic locking and project-scoped permissions.
- Deterministic default quality run with concrete evidence for missing, duplicate row/ID, constant, mixed type, category inconsistency, range, extreme-value clue, imbalance clue, suspicious unit/date and possible sensitive fields.
- RECA-owned Run/Issue facts normalized from one Pandera runtime.
- Whitelisted CleaningPlan actions sufficient for the demo: `MARK_MISSING`, `MAP_CATEGORY`, `REPLACE_VALUE`, `CAST_TYPE`, `RENAME_COLUMN`.
- Side-effect-free preview, exact payload approval, Worker revalidation and one idempotent transformation producing a new Artifact and DatasetVersion.
- Re-run quality checks on the target before transformation completion.
- One production project shell at `/projects/$projectId/data`, with upload through lineage and server-restored deep links.
- Golden CSV/XLSX and vertical backend/browser E2E proving the immutable, approved transformation chain.

### 3.2 P0-Full within M4

- Remaining documented quality rules and filters, full version comparison/lineage views, issue acknowledge/ignore lifecycle and bounded evidence drill-down.
- Additional approved operators: `KEEP_ROWS`, `DROP_ROWS`, `IMPUTE_VALUE`, `CONVERT_UNIT`.
- Explicit selection of hidden worksheets with warning/audit, configurable deployment limits up to the documented 100 MB, 100,000 rows and 200 columns after performance Gate.
- AI CleaningPlanSuggestion in Mock/Recorded or configured provider mode using the frozen PromptContract, deterministic recount and redacted input.
- Complete Job/SSE recovery, retry/cancel, mobile/tablet/light/dark/keyboard states and full role matrix.

### 3.3 Explicitly not done

- M5 statistical analysis, SciPy/statsmodels, Figure/Matplotlib, chart UI or any AnalysisPlan.
- M8 Agent runtime, Tool registry/runtime orchestration, arbitrary Python/SQL/Shell/eval/callable/expression.
- GX runtime, DVC runtime, full ETL, XLS/SAV/DTA/RData, macros, external workbook queries or formula evaluation.
- Automatic deletion, imputation, outlier correction, sensitive-data model access, or model-generated formal counts.
- `CREATE_DERIVED_COLUMN` in M4; it is prohibited until a later explicit deterministic expression grammar is approved.

## 4. Frozen Module and Ownership Map

Backend production locations:

```text
backend/app/models.py
backend/app/alembic/versions/0014_m4_data_quality.py
backend/app/datasets/__init__.py
backend/app/datasets/schemas.py
backend/app/datasets/limits.py
backend/app/datasets/parsers.py
backend/app/datasets/service.py
backend/app/data_quality/__init__.py
backend/app/data_quality/schemas.py
backend/app/data_quality/rules.py
backend/app/data_quality/normalization.py
backend/app/data_quality/service.py
backend/app/data_quality/transformations.py
backend/app/data_quality/jobs.py
backend/app/api/routes/datasets.py
backend/app/api/routes/data_quality.py
backend/app/api/main.py
backend/app/workers/jobs.py
backend/app/agents/prompts/prompt-manifest.yaml
backend/app/agents/prompts/cleaning-plan-suggestion-1.0.0.txt
```

Router responsibilities stop at HTTP/multipart parsing, auth context, required headers and response mapping. Dataset/DataQuality Services own permission policy, no-disclosure 404, same-project checks, row locks, state transitions, idempotency, audit, Artifact orchestration and transactions. Worker handlers receive only Job ID and reload Job, project, source version, Plan, current Approval and hashes from PostgreSQL.

Backend tests:

```text
backend/tests/datasets/test_models.py
backend/tests/datasets/test_parsers.py
backend/tests/datasets/test_service.py
backend/tests/datasets/test_database_constraints.py
backend/tests/data_quality/test_rules.py
backend/tests/data_quality/test_normalization.py
backend/tests/data_quality/test_service.py
backend/tests/data_quality/test_transformations.py
backend/tests/api/routes/test_datasets.py
backend/tests/api/routes/test_data_quality.py
backend/tests/api/routes/test_m4_openapi.py
backend/tests/workers/test_m4_jobs.py
backend/tests/golden/test_m4_data_quality_golden.py
backend/tests/integration/test_m4_vertical_demo.py
```

Golden fixtures:

```text
tests/golden/m4_data_quality/v1/README.md
tests/golden/m4_data_quality/v1/manifest.json
tests/golden/m4_data_quality/v1/quality-small.csv
tests/golden/m4_data_quality/v1/workbook-multi-sheet.xlsx
```

Fixtures are RECA-authored synthetic data, fixed by SHA-256, include no real sensitive data, state expected rules/issues/normalization, and are loaded through the same parsers. DVC is not used.

Frontend production locations:

```text
frontend/src/routes/_layout/projects.$projectId_.data.tsx
frontend/src/features/data-workspace/model.ts
frontend/src/features/data-workspace/mappers.ts
frontend/src/features/data-workspace/queries.ts
frontend/src/features/data-workspace/mutations.ts
frontend/src/features/data-workspace/containers/DataWorkspaceContainer.tsx
frontend/src/features/data-workspace/ui/DataWorkspace.tsx
frontend/src/features/data-workspace/ui/contracts.ts
frontend/src/features/data-workspace/ui/data-workspace.css
frontend/src/features/data-workspace/fixtures/index.ts
frontend/tests/projects-m4-data-contracts.spec.ts
frontend/tests/projects-m4-data.spec.ts
frontend/tests/m4-stage5-vertical.spec.ts
frontend/scripts/check-m4-fixtures.test.mjs
```

Generated files remain generator-only. Codex owns route semantics, adapters, queries, mutations, containers, mappers, fixtures and integration tests. Open Design owns UI composition/styles after consuming frozen typed contracts; it may not modify backend, generated, adapter, query, mutation, container or route semantics.

## 5. Migration 0014 Freeze

Migration identity: `revision = "0014_m4_data_quality"`, `down_revision = "0013_m3_evidence_matrix"`; one unique head. It creates exactly the eight M4 core tables and supporting enums. Supporting composite unique constraints may be added to existing referenced tables only when absent and only after non-destructive duplicate preflight.

### 5.1 Tables and principal columns

| Table | Required identity and lifecycle columns |
| --- | --- |
| `datasets` | id, project_id, identity fields from chapter 13, current_version_id, status, lock_version, created_by, created_at, updated_at, deleted_at |
| `dataset_versions` | id, project_id, dataset_id, version_number, parent_version_id, artifact_id, version_type, row/column count, file_format, worksheet_manifest, selected_worksheet_name, projection_hash, schema_hash, data_hash, transformation_id, status, created_by/at, invalidation fields, deleted_at |
| `dataset_columns` | id, project_id, dataset_version_id, source/display name, order, inferred/confirmed type, semantic role, unit/description, missing/category metadata, identifier/sensitive flags, confirmation_status, inherited_from_column_id, lock_version, timestamps |
| `data_quality_runs` | id, project_id, dataset_version_id, ruleset_id, rule_set_version, ruleset_hash, status, issue counts, processing_run_id, timestamps, error_code |
| `data_quality_issues` | id, project_id, run/version/column IDs, rule_code, issue_type, severity, bounded affected counts/rows/evidence, description, suggested actions, approval flag, status, timestamps |
| `cleaning_plans` | id, project_id, dataset_version_id, title/rationale, status, preview summary/hash, affected counts, source_model_invocation_id, approval_record_id, payload_hash, lock_version, creator/timestamps |
| `cleaning_plan_actions` | id, project_id, cleaning_plan_id, action_order, action_type, selector_type, target_columns, row_selector, parameters, reason, source_issue_ids, bounded preview fields, risk_level |
| `data_transformations` | id, project_id, cleaning_plan_id, approval_record_id, source/target version IDs, status, action/affected counts, parameters_hash, output/log Artifact IDs, processing_run_id, timestamps, error_code |

`worksheet_manifest` is bounded JSON containing only worksheet name, ordinal, visibility, estimated rows/columns and warnings. It does not contain cell values. `selected_worksheet_name` and `projection_hash` are immutable once the version leaves CREATING/VALIDATING.

### 5.2 Enums

- Dataset: `ACTIVE`, `ARCHIVED`, `DELETED`.
- DatasetVersion status/type/file format: authoritative values plus `CSV`, `XLSX`.
- DatasetColumn confirmation: `UNCONFIRMED`, `CONFIRMED`, `NEEDS_REVIEW`.
- DataQualityRun: `QUEUED`, `RUNNING`, `COMPLETED`, `FAILED`, `CANCELLED`, `INVALIDATED`.
- DataQualityIssue type/status: authoritative chapter 14 values; severity `HIGH`, `MEDIUM`, `INFO`.
- CleaningPlan: authoritative chapter 15/state-machine values.
- Action type: authoritative list; `CREATE_DERIVED_COLUMN` exists for contract compatibility but Service rejects it in M4.
- Selector type: `ALL_ROWS`, `ISSUE_ROWS`, `VALUE_EQUALS`, `VALUE_IN`, `IS_NULL`, `IS_NOT_NULL`, `NUMERIC_RANGE`.
- DataTransformation: `QUEUED`, `RUNNING`, `COMPLETED`, `FAILED`, `CANCELLED`.

### 5.3 Constraints, indexes and immutability

- Every table has `UNIQUE(id, project_id)` and project-scoped indexes on status/created time.
- `UNIQUE(dataset_id, version_number)`; `UNIQUE(dataset_version_id, source_name)`; `UNIQUE(dataset_version_id, column_order)`; `UNIQUE(cleaning_plan_id, action_order)`; `UNIQUE(cleaning_plan_id)` on DataTransformation.
- Composite FKs enforce project consistency. Parent version references `(project_id, dataset_id, id)` and therefore cannot cross project or Dataset. Dataset current pointer uses `(project_id, id, current_version_id)` to reference `(project_id, dataset_id, id)`.
- DatasetVersion Artifact references `(artifact_id, project_id)`; column/run/issue/plan/action/transformation relationships use composite project FKs. Service separately validates semantic target types for polymorphic Approval/Job references.
- Checks enforce positive version/order/lock values, nonnegative counts, lowercase 64-hex hashes, valid ORIGINAL parent/transformation nullability, non-original parent requirement, invalidation reason/timestamp pairing, COMPLETED transformation target requirement and bounded JSON array sizes where PostgreSQL checks are practical.
- All destructive FKs use `RESTRICT`; actor references may use `SET NULL`. No cascade may erase versions, approvals, transformations or audit evidence.
- DatasetVersion and Action have no generic update service. Per the Stage 1 authority, no fragile cross-table or immutability trigger is added: declarative checks/composite foreign keys protect directly expressible invariants, while Service row locks, absent generic mutation paths and focused integrity tests protect publication, current-pointer and immutable-content transitions.
- Stage 1 migration tests cover empty/repeated upgrade, downgrade only in isolated tests, `alembic check`, unique head, model/table parity and direct SQL constraint attacks.

## 6. Frozen State Machines

- Dataset: `ACTIVE -> ARCHIVED -> ACTIVE`; `ACTIVE|ARCHIVED -> DELETED`. DELETED is terminal and retains versions.
- DatasetVersion: exact authoritative `CREATING -> VALIDATING -> AVAILABLE`; CREATING/VALIDATING -> FAILED; AVAILABLE -> INVALIDATED -> DELETED. FAILED is terminal, never current. DELETED is soft deletion.
- DatasetColumn: starts UNCONFIRMED or NEEDS_REVIEW; a valid user edit can enter CONFIRMED. Inherited semantics start NEEDS_REVIEW. Any upstream schema/name mismatch resets the new version's column to NEEDS_REVIEW; old version columns never change.
- DataQualityRun: `QUEUED -> RUNNING -> COMPLETED|FAILED|CANCELLED`; completed results may become INVALIDATED when their DatasetVersion is invalidated. Retry is the same Job and a new ProcessingRun; a new quality command may create a new Run.
- DataQualityIssue: `OPEN -> ACKNOWLEDGED|PLANNED|IGNORED|INVALIDATED`; `ACKNOWLEDGED -> PLANNED|IGNORED|INVALIDATED`; `PLANNED -> RESOLVED|IGNORED|INVALIDATED`; resolved/ignored issues can only become INVALIDATED.
- CleaningPlan: exact authoritative chapter 34 transition graph. Only DRAFT/NEEDS_INPUT/REJECTED-to-DRAFT content is editable. APPROVED content is immutable. Source invalidation makes DRAFT through APPROVED plans INVALIDATED; execution terminal records remain traceable.
- CleaningPlanAction: no independent status; action rows are immutable outside editable Plan states and are replaced transactionally as an ordered set under If-Match.
- DataTransformation: `QUEUED -> RUNNING -> COMPLETED|FAILED`; QUEUED may cancel. No completed transformation reruns; same idempotency key replays, a new key receives invalid-state conflict.

Unknown states, missing permissions, absent allowed actions, unavailable versions and stale approvals are rejected and rendered fail closed.

## 7. Optimistic Concurrency

- Dataset and DatasetColumn receive `lock_version >= 1`; CleaningPlan also uses the existing common editable-object rule.
- GET responses expose lock version and ETag `"<lock_version>"`.
- PATCH requires exactly one strong If-Match integer ETag. Missing is validation error; stale is `409 RESOURCE_VERSION_CONFLICT` with expected/current versions.
- Service performs permission and project lookup before conflict details to preserve no-disclosure 404.
- Successful update increments once in the same transaction and appends AuditLog. Idempotency-Key is not used for PATCH.
- DatasetVersion is not PATCH-editable. Worksheet selection is a dedicated idempotent command while pending and uses a row lock plus first-selection-wins semantics.

## 8. Upload, Worksheet and Availability Contract

Competition Core limits are frozen conservatively at 25 MiB compressed/upload bytes, 50,000 data rows, 100 columns, 16 worksheets, 32,767 characters per cell, 100:1 ZIP expansion ratio and 250 MiB total expanded workbook bytes. P0-Full may raise file/row/column limits to the documented 100 MB/100,000/200 only after a focused resource test; deployment config may lower them.

Upload lifecycle:

1. Router streams multipart data through the existing Artifact validation/storage service; it never buffers an unbounded body or writes a user filename as a path.
2. Artifact starts UPLOADING and becomes AVAILABLE only after size/hash/MIME/header checks. It is `is_original=true`, immutable and never overwritten.
3. Dataset and Original DatasetVersion CREATING are created in the same domain transaction after a stable Artifact identity exists. Dataset current pointer remains null.
4. CSV detects BOM/encoding from an explicit allowlist (`utf-8`, `utf-8-sig`, then configured legacy fallback), samples a bounded prefix for delimiter among comma/semicolon/tab/pipe, and validates the whole stream against byte/row/column/cell limits. Formula prefixes are preserved as data and marked as export-risk candidates; they are never evaluated.
5. XLSX is preflighted as ZIP, rejects macros/unsupported relationships, path traversal, excessive file count/ratio/expanded bytes, then uses openpyxl with `read_only=True`, `data_only=True`, `keep_links=False`. Formula/external-reference cells yield cached values or null and never trigger network access.
6. For CSV or exactly one visible worksheet, Service may select automatically. Multiple visible worksheets require a persisted selection before validation; hidden worksheets are listed and never auto-selected.
7. Validation extracts bounded preview and DatasetColumns into staging domain data. Only a single transaction can set selected projection, counts/hashes/columns, status AVAILABLE and Dataset.current_version_id. Any failure sets version FAILED and leaves current pointer unchanged.

Formal additive worksheet API amendment:

```text
GET  /api/v1/dataset-versions/{version_id}/worksheets
POST /api/v1/dataset-versions/{version_id}/worksheet-selection
Idempotency-Key: required
body: { worksheet_name, acknowledge_hidden: boolean }
```

The read endpoint returns the persisted manifest and selected projection. Selection is allowed only for XLSX CREATING versions, requires dataset.upload permission, locks the version, validates the name against the manifest, requires `acknowledge_hidden=true` for hidden sheets, audits the choice and dispatches/continues validation. Replay returns the same version/Job; a different payload conflicts. Selection cannot change after VALIDATING/AVAILABLE. Frontend local selection is never authoritative.

Stage 1 additive lifecycle amendment:

```text
POST /api/v1/dataset-versions/{version_id}/invalidate
Idempotency-Key: required
body: { reason: non-empty bounded string }
```

The direct Stage 1 requirement to audit version invalidation controls this missing detailed-API path. The Service requires dataset.update permission, locks the Version and Dataset, permits only AVAILABLE -> INVALIDATED, records the reason/timestamp and audit, and atomically replaces the Dataset current pointer with the latest remaining AVAILABLE version or null. Same-key replay is stable; a new key after invalidation receives an invalid-state conflict.

Preview is a bounded server projection: default 50 rows, maximum 200, selected columns only, cells truncated and sensitive values masked. It never publishes formulas, external URLs, full sensitive values or arbitrary raw examples.

## 9. Version Pointer, Failure, Invalidation and Deletion

- `Dataset.current_version_id` changes only under a Dataset row lock after the candidate version is AVAILABLE and belongs to that Dataset/project.
- Original upload sets the first current pointer. A completed transformation promotes its target exactly once. Concurrent successful promotions serialize; a stale source/plan fails rather than overwriting a newer current pointer unless the Plan explicitly targets a non-current version and the contract permits a branch.
- FAILED versions and incomplete Artifacts remain non-current and non-downloadable as formal results; retry reuses the same Job and either resumes the same staging identity or fails closed.
- INVALIDATED versions remain readable with reason, are excluded from new Plan/analysis creation, invalidate active dependent plans/quality projections and do not rewrite historical results.
- Dataset soft deletion sets Dataset DELETED, retains versions/Artifacts and blocks new writes/download/export according to policy. DatasetVersion DELETED follows INVALIDATED and remains retained. Physical deletion is outside M4.

## 10. Pandera and Quality Rule Contract

Adopted direct versions after current-environment Spike:

```text
Python 3.14.2
pandas 3.0.5
Pandera 0.32.1 with pandas extra
openpyxl 3.1.5
```

Ruleset identity:

- `ruleset_id = RECA_P0_DEFAULT`.
- Initial semantic version `1.0.0`.
- `ruleset_hash = sha256(RECA canonical JSON of sorted rule definitions, parameters, severity and wording version)`.
- DataQualityRun stores ID/version/hash; ProcessingRun metadata stores Python, pandas, NumPy, Pandera, parser/openpyxl and RECA engine versions.
- A ruleset change creates a new semantic version/hash and golden expectations; it never rewrites old Runs.

Pandera runs with `lazy=True`, `inplace=False`; third-party objects never cross the normalization boundary. FailureCases are grouped by rule_code + column + bounded row bucket into RECA Issues. Stable ordering is rule order, column order, normalized row index. Each Issue stores affected count, at most 100 row references, at most 5 masked examples and a truncation flag. Sensitive candidates store shape/pattern evidence, never complete values.

Severity and wording:

| Rule family | Default severity | Required language |
| --- | --- | --- |
| invalid date, duplicate confirmed ID, hard user range, incompatible mixed type | HIGH | observed contract violation; still show evidence and user control |
| missing, duplicate row, category inconsistency, suspicious unit, possible sensitive field | MEDIUM | issue or review required; sensitive values masked |
| constant column, group imbalance, IQR/Z-score extreme candidate | INFO | clue/limitation only; never call an extreme value an error |

Field-name heuristics may propose common age/percentage/privacy rules but cannot delete or formally classify without explicit rule evidence/user confirmation. Quality rules only create Runs/Issues and never modify source data.

## 11. CleaningPlan Action Contract and Hashing

Request schemas are a Pydantic discriminated union by `action_type`; `extra="forbid"` at every level. UUID selectors reference DatasetColumn/Issue objects in the same project/version. Array sizes, mapping size, string size and numeric precision are bounded.

Allowed selectors are the fixed selector enum in section 5. Free predicates, regex programs, lambda/callable, nested boolean expression trees, code, SQL and shell are rejected.

Action parameters:

- MARK_MISSING: target columns + selector; replacement is fixed null.
- MAP_CATEGORY: exactly one target column; bounded literal-to-literal mapping.
- REPLACE_VALUE: target columns + selector + one literal replacement.
- CAST_TYPE: target columns + target type enum + on_invalid `FAIL` or `MARK_MISSING`.
- RENAME_COLUMN: one target column + bounded unique output name.
- KEEP_ROWS/DROP_ROWS: selector only; P0-Full and high-risk approval wording.
- IMPUTE_VALUE: one/more target columns; strategy `CONSTANT`, `MEDIAN` or `MODE`; P0-Full, no model-generated values.
- CONVERT_UNIT: numeric target columns, declared source/target unit and decimal factor; no expression.
- CREATE_DERIVED_COLUMN: always rejected in M4.

Canonical hashing uses a RECA-owned normalization: Pydantic JSON-mode output, Unicode NFC, lowercase UUIDs, UTC timestamps with `Z`, Decimal values as normalized strings, sorted object keys, semantic arrays sorted when order is irrelevant, action arrays preserving `action_order`, UTF-8, no NaN/Infinity, separators `,` and `:`. SHA-256 is lowercase hex.

The Plan approval payload contains schema version, project/Plan/source version IDs, source data/schema/projection hashes, Plan lock version, the complete ordered action union, deterministic preview hash and ruleset identity. Transformation `parameters_hash` adds exact engine versions and output format. Any mutation changes the hash and supersedes prior approval.

## 12. Preview, Approval and Execution

- Preview is a deterministic command with Idempotency-Key but no data/version/Artifact side effect. It may update only Plan preview fields/hash/status through VALIDATING -> READY or NEEDS_INPUT and writes AuditLog.
- Preview uses a copy/staging dataframe, returns bounded masked samples and exact RECA-computed counts. It does not persist transformed data or change source hashes.
- Approval request is `POST /api/v1/cleaning-plans/{id}/approval-requests`. Owning Service creates ApprovalRecord with exact payload snapshot/hash, expiry and target; no generic Approval creation API.
- Only current `APPROVED` ApprovalRecord, correct actor/project/target, not expired/superseded, with payload hash equal to a fresh canonical Plan snapshot, permits execution. Stale becomes `APPROVAL_STALE`; expired becomes `APPROVAL_EXPIRED`; both create no Job/transformation side effect.
- Execute is `POST /api/v1/cleaning-plans/{id}/execute` with Idempotency-Key. One transaction locks Plan/source/Dataset/Approval, revalidates permissions and hashes, creates one DataTransformation QUEUED, one Job QUEUED and the idempotency fact, then dispatches after commit.

Worker execution:

1. Claim the PostgreSQL Job and create a new ProcessingRun attempt.
2. Reload and lock all facts; ignore queue-supplied project/user/version/approval metadata.
3. Recheck source AVAILABLE/not invalidated, project consistency, current Plan/Approval hashes and allowed action schemas.
4. Read immutable source Artifact, apply actions to a copy, enforce limits, compute output/hash/schema/diff and run the target quality rules.
5. Write output to an inaccessible staging object associated with an UPLOADING derived Artifact; verify bytes/hash before publication.
6. In one database transaction finalize Artifact AVAILABLE, target DatasetVersion and columns AVAILABLE, completed target quality Run/Issues, Dataset current pointer, Transformation COMPLETED, Plan COMPLETED, Job result and AuditLog.
7. On failure, mark Transformation/Plan/Job failed according to their state machines, mark a created target version FAILED, leave Dataset current pointer and source untouched, and retain/clean staging material under bounded internal recovery policy.

Unique Plan-to-Transformation and source/Plan hashes prevent duplicate formal versions. Same idempotency key replays the first Job/result; a different key after QUEUED/RUNNING/COMPLETED is an invalid transition.

## 13. AI Suggestion Boundary

Stage 3 adds PromptContract `cleaning-plan-suggestion` version `1.0.0`, schema `CleaningPlanSuggestion` 1.0, source types DatasetVersion/DataQualityIssue/DatasetColumn, zero tools, mandatory human review and fail-closed Schema behavior.

- requested/max/effective access defaults to `METADATA_ONLY`; maximum allowed is `REDACTED_CONTENT` for bounded masked examples. M4 never requests APPROVED_FULL_CONTENT.
- Input includes rules/issues, column metadata, masked bounded examples and allowed action schemas. Sensitive columns contribute no raw examples.
- Model output is a suggestion only. The Service revalidates every union member and same-project ID, rejects prohibited actions, and creates a DRAFT only through an explicit user command.
- Model-provided `expected_effect` numbers are non-authoritative compatibility fields and are never copied into formal preview/counts/approval. Deterministic preview replaces them.
- ModelInvocation persists Prompt/schema/access/source/hash/outcome metadata; default storage excludes raw sensitive input/output. Mock/Recorded never claims live execution.

## 14. API, Permissions and Product Shell

Exact detailed API methods/paths from chapters 19-20 are retained, with these additive clarifications:

- Dataset list/detail/versions, version detail/preview/columns/comparison and Dataset/Column PATCH.
- Worksheet endpoints from section 8.
- Quality start/detail/issues; issue acknowledge/ignore.
- CleaningPlan create, draft PATCH with If-Match, preview POST, approval-requests POST and execute POST.
- All command endpoints that create Job or have side effects require Idempotency-Key; authorization precedes replay lookup.
- Nonmember project resources return no-disclosure `404 RESOURCE_NOT_FOUND`; member without action returns 403.
- OWNER/EDITOR can upload/edit/plan/execute; REVIEWER can read and make formal approval decisions through existing approval.decide; VIEWER reads only. Exact allowed actions are server projections and unknown/missing values disable UI actions.
- 202 means accepted Job only. Upload completion, preview completion, approval button clicks and Job acceptance are never presented as transformation completion.

The single shell is `/projects/$projectId/data`. Frozen search parameters:

```text
tab=overview|preview|columns|quality|plan|versions|lineage
datasetId
versionId
qualityRunId
issueId
planId
jobId
```

The route validates UUIDs/enums, loads project-scoped server truth, and restores the selected resource after refresh. Invalid, stale, cross-project or unavailable IDs fail closed and do not fall back to a different dataset silently.

## 15. Codex/Open Design Contract and Handoff Gate

Stage 4 Codex freezes executable TypeScript ViewModels, props/events, typed fixtures, route/search schema and production mock guard before Open Design integration. Fixtures must import the formal ViewModel types and visibly declare fixture/demo status.

Open Design handoff must cover loading, empty, ready, forbidden, stale, degraded, failed, invalidated, pending approval, Job running/retry/cancel and completed states; desktop/tablet/390px, light/dark, keyboard/focus and long-content overflow. It cannot call API, modify generated/adapter/queries/mutations/containers/routes/backend, or treat selection/buttons as formal state.

Codex integration begins only when the UI consumes frozen contracts, passes design review, contains no parallel product shell, and does not import fixtures in production. Stage 5 owns production queries/mutations, Job recovery, approval execution mapping and E2E.

## 16. Dependency Spike and Adoption Decision

Environment and results:

```text
uv 0.9.26; CPython 3.14.2; isolated temp venv
pandas 3.0.5; Pandera 0.32.1; openpyxl 3.1.5
Pandera lazy failures: 3, stable across two runs, input unchanged
20,000 x 8 CSV: 822,702 bytes; parse 0.0115 s; validation 0.0095 s
DataFrame deep memory: 3,080,132 bytes; tracemalloc peak 4,500,891 bytes
2-sheet/5,000-row XLSX: 145,880 bytes; safe read 0.7053 s; peak 1,314,909 bytes
hidden sheet detected; formula and external-reference cached values null
keep_links=false retained 0 external links; socket guard observed no network access
UTF-8 BOM and semicolon detected; formula prefixes preserved as text/candidates
negative guards rejected row, column, cell, damaged XLSX, 17-sheet and >100:1 ZIP-ratio inputs
```

The benchmark is a compatibility/resource sanity check, not a maximum-load proof. It supports the conservative Competition Core limits in section 8; stage 6 must measure configured maxima.

Decision:

- Adopt and pin pandas 3.0.5, `pandera[pandas]` 0.32.1 and openpyxl 3.1.5. `backend/pyproject.toml`, `uv.lock` and notices are updated in stage 0.
- Do not install GX. Its report taxonomy is useful for rule metadata/evidence/severity wording, but a dry resolution adds 25 packages to the Spike environment and creates a second runtime/source-of-truth risk.
- Do not install DVC. Current golden provenance is three files/11,821 bytes with versioned manifests and SHA assertions; DVC dry resolution would add 90 packages. Git + fixture manifest + hashes already satisfy the current need.
- Rejected alternatives: custom dataframe validator, dual Pandera/GX runtime, DVC-backed business lineage, eager non-streaming workbook loading, or formula-capable spreadsheet engines.

## 17. Stage Dependency and Focused Test Plan

### Stage 1: models, 0014, upload/preview/columns

Depends on this frozen plan. Implement enums/eight tables/migration, parsers, worksheet contract, Dataset/Version/Column Services and API. Run only model, migration, upload/preview/column and Artifact integration focused tests plus static format/type for touched code.

Status: `COMPLETED` on 2026-08-04. Implemented the eight SQLModel mappings and `0014_m4_data_quality`, project-scoped composite constraints, bounded CSV/XLSX parsers, immutable Artifact-backed upload, persisted worksheet manifest/selection, Original DatasetVersion publication, deterministic DatasetColumns, masked bounded preview, Dataset/Column optimistic concurrency, audit and project-isolated APIs. No quality execution, CleaningPlan behavior, transformation Worker, generated client or frontend was started.

Stage 1 verification: empty database upgrade through 0014; isolated 0014 downgrade/re-upgrade; isolated existing-chain 0013 -> 0014 upgrade; `alembic check`; 25 focused parser/API/migration tests; ruff and mypy for touched backend scope. The current repository root Linux-layout `.venv` was left unchanged; checks used a disposable Windows environment and compose containers.

Stage 1 recovery checkpoint: branch `feat/m2-research-literature`; HEAD `0e3c39dde65feaa8f784fd5fcfb1055cb557bb3c`; migration head `0014_m4_data_quality`; migration SHA-256 `a61f9cbf745f781b94997bbbcbc62d91bf034a92fe400800fadd47a6d45744fb`. The two isolated test databases and the Stage 1 temporary Windows environment were removed after verification. Existing M3 uncommitted files remain in place and were not reset, cleaned, stashed or overwritten.

### Stage 2: quality engine, Worker/API/golden

Depends on AVAILABLE immutable versions and columns from stage 1. Implement ruleset/normalization, quality Job/Worker/API and golden fixtures. Run only rules, normalization, Worker, quality API and M4 golden focused tests.

Status: `COMPLETED` on 2026-08-04. Implemented the RECA-owned `RECA_P0_DEFAULT` 1.0.0 registry and canonical content hashes, Pandera lazy/no-coerce normalization boundary, all twelve frozen quality issue families, bounded aggregated locators/examples, sensitive masking, `DATASET_PROFILE` Job/Worker execution, Run/Issue read and review Services/APIs, project permissions, idempotency, audit and failure facts. No CleaningPlan, transformation, frontend or generated client work was started.

Stage 2 contract decision: `DataQualityRun` has no separate scan-options JSON field. The full rule set and the sensitive-detection-excluded selection are therefore distinct canonical RuleSet hashes. API and Worker resolve by exact persisted ID/version/hash, and queue payload is never authoritative. This is recorded as resolved `M4-ISSUE-0011`; 0014 was not changed and no 0015 was created.

Stage 2 verification: isolated empty PostgreSQL upgrade through 0014; 11 focused tests passed across registry/Pandera normalization, immutable input, all rule families, masking/bounds, versioned golden CSV/XLSX, Job/Worker success and storage-hash failure, ProcessingRun metadata, API pagination/filtering, idempotency, OWNER/EDITOR/REVIEWER permissions, no-disclosure and 0014 graph assertions. Ruff and strict Mypy passed for the touched quality/API/Worker/test scope.

Stage 2 recovery checkpoint: branch `feat/m2-research-literature`; HEAD `0e3c39dde65feaa8f784fd5fcfb1055cb557bb3c`; migration head remains `0014_m4_data_quality`; migration SHA-256 remains `a61f9cbf745f781b94997bbbcbc62d91bf034a92fe400800fadd47a6d45744fb`. The isolated Stage 2 database is disposable and must be removed after final verification. Existing M3 and Stage 1 changes were not reset, cleaned, stashed or overwritten.

### Stage 3: Plan/Approval/Transformation/AI suggestion

Depends on stage 2 Run/Issue truth. Implement discriminated actions, preview, approval payload, transformation staging/promotion/recheck and Prompt/ModelInvocation boundary. Run Plan/Approval/Transformation/AI schema and idempotency focused tests.

Status: `COMPLETED` on 2026-08-04. Implemented strict discriminated CleaningPlan actions for `MARK_MISSING`, `MAP_CATEGORY`, `REPLACE_VALUE`, `CAST_TYPE` and `RENAME_COLUMN`; all other enum actions fail with `ACTION_NOT_AVAILABLE`. Added deterministic non-mutating Preview, bounded masked samples, canonical action/preview/approval hashes, If-Match draft updates, formal `CLEANING_PLAN_APPROVAL` resolver/decision integration, idempotent `DATASET_TRANSFORM` Job dispatch, database-revalidating Worker execution, exact-key staging cleanup, immutable derived Artifact and child DatasetVersion promotion, inherited field dictionary, persisted-output quality recheck and server-side version comparison.

Stage 3 AI boundary: added Git-managed `cleaning-plan-suggestion` 1.0.0 PromptContract and strict `CleaningPlanSuggestion` validation. Inputs contain bounded version/column/Issue metadata with example-value fields removed; ModelInvocation effective access is `METADATA_ONLY` under a `REDACTED_CONTENT` maximum. Mock/live provider output passes the same action validator. Invalid output, unavailable provider or unavailable action records a FAILED invocation and creates no Plan, Approval, Job or transformation. Valid output remains an explicit `CANDIDATE` suggestion.

Stage 3 contract decisions: `CREATE_DERIVED_COLUMN`, row-drop/keep, imputation and unit conversion remain unavailable rather than introducing an expression engine (`M4-ISSUE-0012`). Object storage gained exact-key deletion solely so a failed post-upload promotion can remove its own staged generated object (`M4-ISSUE-0013`). 0014 was not modified and no 0015 was created.

Stage 3 verification: disposable PostgreSQL database upgraded from empty through 0014; 34 focused tests passed across action schemas/engine, malicious field rejection, deterministic hashing, formula-safe export, Preview no-side-effects, Approval pending/rejected/stale/expired/cross-project rules, idempotent execution, Worker persisted-fact revalidation, unique derived Artifact/version lineage, source immutability, failed promotion behavior, post-transform quality run, version comparison, Prompt manifest, storage boundary and AI fail-closed paths. Ruff and strict Mypy passed for the affected Cleaning/API/Worker/permission scope. The running user database remained at `0013_m3_evidence_matrix`.

Stage 3 recovery checkpoint: branch `feat/m2-research-literature`; HEAD `0e3c39dde65feaa8f784fd5fcfb1055cb557bb3c`; migration head remains `0014_m4_data_quality`; migration SHA-256 remains `a61f9cbf745f781b94997bbbcbc62d91bf034a92fe400800fadd47a6d45744fb`. Existing M3 and M4 Stage 1/2 modifications were preserved without reset, clean, stash, destructive checkout or migration rewrite.

### Stage 4: frontend contracts and Open Design handoff

Depends on frozen OpenAPI from stages 1-3. Regenerate formally, implement adapter/ViewModel/typed fixtures/route contract and mock guard, then publish handoff. Run generated-client, TypeScript, boundary and fixture-contract tests only.

Status: `COMPLETED WITH OPEN EXIT ISSUES` on 2026-08-04. The formal OpenAPI client was regenerated without hand edits. Added the single `data-workspace` feature with RECA-owned adapter DTO boundary, fail-closed ViewModels/mappers, query/mutation/Container layers, pure Props/Event UI contract, typed fixture matrix, `/projects/$projectId/data` route draft and registration in the existing Design Preview workbench. Production route wiring remains intentionally absent.

Stage 4 contract decision: missing backend response models are recorded as `M4-ISSUE-0014`; adapter envelope checks and structural DTOs are a bounded continuation, not a replacement for formal response DTOs. Missing version-history and Transformation-detail reads are `M4-ISSUE-0015`; navigation events remain intents and unavailable production capabilities stay disabled. Open Design ownership and the exact protected paths are frozen in `M4_OPEN_DESIGN_HANDOFF.md`.

Stage 4 does not alter 0014, backend business behavior, production routes or final visual design. Focused verification comprises generated-client consistency, TypeScript/Vite build, M4 fixture contract, UI boundary and production-mock gates. Full Playwright and clean-room remain Stage 6 work.

```text
M4_STAGE_4_CONTRACTS=PASS
READY_FOR_OPEN_DESIGN=YES
PRODUCTION_INTEGRATION_COMPLETE=NO
STAGE_RESULT=PASS_WITH_ISSUES
NEXT_STAGE_EXECUTED=NO
COMMIT_TAG_PUSH=NO
```

### Stage 5: production shell and vertical integration

Depends on accepted Open Design output and stage 4 contracts. Wire production data, permissions, Job/SSE, approval and deep links; collect issues without broad fixes. Run M4 focused browser tests and one longitudinal E2E only.

### Stage 6: concentrated fixes and Exit Gate

Freeze features; resolve all BLOCKER/CRITICAL/HIGH and all issues blocking M4 Exit/M5 Entry. Then run complete backend no-database/PostgreSQL, migration unique-head/repeat/check, MinIO/Worker/golden/vertical, frontend format/lint/build/generated/boundary, full shell and M4 Playwright, clean-room, Secret/dependency/license audits and `git diff --check`.

M4 Exit requires all milestone completion conditions, zero M5-entry blockers, no source overwrite/approval bypass/partial AVAILABLE version/sensitive leakage/arbitrary action, and explicit remaining LOW/P0-Full limitations. Only stage 6 may set M4 complete or M5 allowed.

## 18. Stage 0 Exit

```text
M4_ENTRY_AUDIT=PASS
M4_PLAN_FROZEN=YES
M4_BUSINESS_IMPLEMENTATION_STARTED=NO
STAGE_RESULT=PASS_WITH_ISSUES
NEXT_STAGE_EXECUTED=NO
COMMIT_TAG_PUSH=NO
```

Open planned issues are implementation obligations for stages 1-5, not reasons to repeat stage 0 research. Any new local fact that invalidates this plan must update this document and the Issue Register before expanding code.
