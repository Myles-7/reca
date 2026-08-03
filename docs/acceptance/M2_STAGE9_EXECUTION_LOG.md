# RECA M2 Stage 9 Execution Log

This log is Stage 9 execution evidence. It does not override product, data-model,
API, state-machine, security, or milestone authorities. Recorded, Cache,
Degraded, and Live results are reported separately; `NOT RUN` is not success.

## Execution Plan

1. Stage A: freeze the current repository facts and the M2-to-M3 input boundary.
2. Stage B: run only new or affected backend, frontend, integration, migration,
   and browser tests.
3. Stage C: repair discovered issues by root cause and rerun focused regressions.
4. Stage D: run complete backend, frontend, migration, Playwright, Compose, and
   clean-room gates; refresh Exit Gate and M3 Entry evidence.

## Start Baseline

```text
started_at: 2026-08-03 Asia/Shanghai
branch: feat/m2-research-literature
HEAD: ac6447c081c881fedb818525871a8bd100410cb5
working_tree: DIRTY; M2 and Open Design work is largely uncommitted/untracked
migration_script_head: 0012_document_upload
running_database_head: 0012_document_upload
production_routes: QueryPlan, Literature, Document registered
```

The complete start `git status --short` was captured in the Stage 9 terminal
evidence. Existing modified and untracked M2 files are preserved; generated
output, `.playwright-cli`, test results, temporary files, logs, secrets, and
runtime data are excluded from delivery.

## Stage A Facts

- QueryPlan, Literature, and Document routers are registered in the backend and
  their production TanStack routes are present in `routeTree.gen.ts`.
- Production routes inject Open Design workspaces through Codex-owned Containers.
- Literature `searchRunId` and Document `jobId` are validated search parameters,
  passed to queries/containers, and updated after accepted server responses, so
  refresh restores the active run/job context.
- QueryPlan detail creation remains `BLOCKED_BY_CONTRACT`; update and generation
  use server-projected actions and optimistic version checks.
- Literature retry requires a matching formal Job with `retryable=true` and the
  project-level `job.retry` action. Document retry follows the same formal Job
  boundary.
- Document `literature_record_id` is validated and associated by the backend
  service; the frontend does not infer a formal LiteratureRecord relationship.
- Production mock and fixture boundary checks are clean. Fixtures remain under
  explicit fixture/test/preview paths and are not imported by production data
  paths.
- The Stage 6 typed-fixture and module-smoke evidence remains applicable as
  historical supporting evidence; Stage 9 will replace stale route conclusions
  with current vertical and full-suite evidence.
- The stable M2 chain is: confirmed ResearchQuestionVersion -> QueryPlan ->
  LiteratureSearchRun/Candidate -> LiteratureRecord -> immutable PDF Artifact ->
  Document -> DocumentPage/DocumentChunk -> parser provenance, Job, and
  ProcessingRun.
- M3-only and not implemented by M2: LiteratureExtraction, the fixed ten fields,
  EvidenceSpan, LiteratureDecision, TopicCandidate, literature matrix, PDF.js
  evidence highlighting, and evidence-set analysis. DocumentPage/Chunk do not
  constitute EvidenceSpan.

## Stage A Verification

| Check | Result | Evidence |
| --- | --- | --- |
| `git diff --check` | PASS | No whitespace errors; line-ending conversion warnings only. |
| generated client check | PASS | Four generated OpenAPI client files verified. |
| UI boundary guard | PASS | 4 tests passed; ownership boundary clean. |
| production mock guard | PASS | 6 tests passed; production paths clean. |
| route/contract focus | PASS | 24 backend route tests passed in a source-mounted Compose test container. |
| Alembic heads/current | PASS | Script and running database both report `0012_document_upload`. |

## Stage B Vertical Acceptance

The deterministic browser path uses an isolated PostgreSQL database and MinIO
bucket, production FastAPI routes, the generated client and adapter, registered
Job/Worker handlers, and Recorded OpenAlex/GROBID inputs. It does not use route
interception or a production seed endpoint to claim success.

| Check | Result | Evidence |
| --- | --- | --- |
| Production browser vertical | PASS | 1 Playwright test passed in 6.7s: login, Project, Research Question versioning/ready/Approval confirmation, QueryPlan update/generate, Recorded search/cache refresh, candidate and DOI import/dedup, PDF Artifact upload, Document parse, GROBID result, DocumentPage text, and refresh recovery. |
| Backend M2 core focus | PASS | 81 tests passed. |
| Roles, approval, jobs, and project negatives | PASS | 27 tests passed. |
| Frontend Route and contract focus | PASS | 42 tests passed. |
| Responsive and accessibility focus | PASS | 34 tests passed, including desktop/mobile, keyboard/focus, and reduced motion. |

Focused backend coverage verifies OWNER/EDITOR/REVIEWER/VIEWER, no-disclosure
and cross-project IDs, stale `If-Match`, idempotency replay/conflict, duplicate
candidate/DOI import, cache/degraded/limitations, provider failure without
record creation, upload/parse separation, Job states and retryability,
GROBID fallback/no-fallback, pypdf LOW degradation, corrupt/encrypted/scanned
files, stable pages/chunks, and unknown fail-closed behavior. DocumentChunk is
verified only as a persisted M2 parse product and is never presented as
EvidenceSpan.

## Issues

### M2-S9-001

- stage: A
- severity: MEDIUM
- area: acceptance and frontend handoff documentation
- authoritative_requirement: Current code and current uncommitted authoritative
  child documents take precedence over historical acceptance reports; production
  route and retry facts must be accurate for the Exit Gate.
- observed_behavior: The old Exit/Vertical reports and early checkpoint text still
  say QueryPlan, Literature, and Document production routes are absent. The
  frontend feature template also retains pre-activation statements for routes and
  Literature retry, while later Issue Register/checkpoint sections record them as
  implemented.
- evidence: Backend router registration, generated route tree, three production
  route modules, Stage 7 checkpoint refresh, and 24 passing route tests.
- root_cause: Historical acceptance evidence was not refreshed after Stage 7
  production activation.
- affected_files: `docs/acceptance/M2_EXIT_GATE_REPORT.md`,
  `docs/acceptance/M2_VERTICAL_INTEGRATION_REPORT.md`,
  `docs/acceptance/OPEN_DESIGN_REDESIGN_CHECKPOINT.md`,
  `docs/development/M2_FRONTEND_FEATURE_TEMPLATE.md`.
- blocks_current_path: NO
- safe_continuation: Treat old route-absent rows as `DOC_STALE`; use current code
  and the later Stage 7 evidence until Stage C/D refreshes the reports.
- status: RESOLVED
- resolution: Refreshed Exit/Vertical reports, marked historical checkpoint rows
  `DOC_STALE`, and updated the frontend handoff to current route/retry facts.
- focused_verification: Stage 9 vertical, full Playwright, and clean-room passed.
- exit_gate_impact: Blocks accurate final disposition of `M2-ISSUE-0010`.
- m3_entry_impact: M3 cannot rely on stale route/refresh/retry statements.

### M2-S9-002

- stage: A
- severity: LOW
- area: local backend test command environment
- authoritative_requirement: Tests must run from a reproducible project-owned
  environment; inability to invoke a local tool is not product success or failure.
- observed_behavior: `uv` is unavailable on the Windows PATH and the repository
  `.venv` has no Windows executable. Global Python lacks pytest and Alembic.
- evidence: Direct command failures; the pinned Compose API image contains the
  required Python environment and successfully runs source-mounted tests.
- root_cause: Host-local Python environment is incomplete for this checkout.
- affected_files: None.
- blocks_current_path: NO
- safe_continuation: Run backend tests through the pinned Compose API image with
  the local backend source mounted read-only/equivalently scoped.
- status: DEFERRED
- resolution: Safe LOW deferral; Compose and clean-room provide the reproducible
  project-owned Python environment without dependency mutation.
- focused_verification: 24 route tests passed through Compose.
- exit_gate_impact: None if all required backend gates run in Compose/clean-room.
- m3_entry_impact: Preserve a documented Compose test entry for handoff.

### M2-S9-003

- stage: A
- severity: MEDIUM
- area: SQLModel metadata
- authoritative_requirement: SQLModel metadata must represent each database
  invariant once and remain consistent with Alembic metadata checks.
- observed_behavior: `ProjectMember.__table_args__` declares
  `uq_project_members_active_owner` twice, and `AuditLog.__table_args__`
  declares `fk_audit_logs_approval_id_approval_records` twice.
- evidence: Static inspection of `backend/app/models.py`.
- root_cause: Duplicate insertion during the M1 metadata parity repair.
- affected_files: `backend/app/models.py`.
- blocks_current_path: NO
- safe_continuation: Existing database constraint remains unchanged; remove only
  the duplicate metadata declaration in Stage C and run focused metadata tests.
- status: RESOLVED
- resolution: Removed only the duplicate Index and ForeignKeyConstraint
  declarations; the intended constraints and database schema are unchanged.
- focused_verification: Pending.
- exit_gate_impact: Metadata consistency risk until repaired.
- m3_entry_impact: M3 migrations must start from unambiguous metadata.

### M2-S9-004

- stage: B
- severity: LOW
- area: frontend test server isolation
- authoritative_requirement: Browser acceptance must execute the current source
  and must not reuse stale cached application output.
- observed_behavior: An initial focused frontend run reported 18 failures while
  Playwright reused an older Compose Vite process on port 5173.
- evidence: The same suites passed on isolated ports 5183/5184 (42 route/contract
  tests and 34 responsive/accessibility tests).
- root_cause: Port reuse selected a stale development server, not the current
  source tree.
- affected_files: Test runtime only.
- blocks_current_path: NO
- safe_continuation: Use a unique Stage 9 port and isolated Playwright config.
- status: RESOLVED
- resolution: Stage 9 browser tests use an isolated server/port.
- focused_verification: 76 affected frontend tests passed on isolated ports.
- exit_gate_impact: None after isolated rerun.
- m3_entry_impact: Preserve isolated browser-server startup in regression runs.

### M2-S9-005

- stage: B
- severity: MEDIUM
- area: acceptance Worker dispatcher
- authoritative_requirement: HTTP 202/QUEUED is not completion; test dispatch
  must preserve transaction ordering and the formal Job lifecycle.
- observed_behavior: A synchronous test dispatcher completed a Job before the
  request transaction committed, after which the request path overwrote the
  terminal status with `QUEUED`.
- evidence: Initial vertical run stalled on a completed handler whose Job row was
  subsequently queued.
- root_cause: Acceptance-only dispatcher timing differed from Celery delivery.
- affected_files: `backend/tests/acceptance/m2_stage9_server.py`.
- blocks_current_path: NO
- safe_continuation: Dispatch asynchronously after a short commit-order delay.
- status: RESOLVED
- resolution: The acceptance dispatcher now runs registered handlers
  asynchronously after the request commit boundary.
- focused_verification: Production browser vertical passed with real Job claim,
  ProcessingRun, handler completion, and refresh polling.
- exit_gate_impact: None after focused rerun.
- m3_entry_impact: M3 async acceptance must preserve commit-before-worker order.

### M2-S9-006

- stage: B
- severity: LOW
- area: first-entry frontend navigation
- authoritative_requirement: Navigation must use server-returned IDs; M2 must not
  invent an uncontracted creation surface.
- observed_behavior: QueryPlan detail, Literature active-run, and Document detail
  routes require server IDs. The current UI has no ID-less first-entry route, so
  the deterministic vertical creates the first QueryPlan/SearchRun/Document via
  formal API before navigating through production pages.
- evidence: Stage 9 vertical spec and frozen route contracts.
- root_cause: Creation entry routes are outside the current frozen detail-route
  contract; QueryPlan detail create remains `BLOCKED_BY_CONTRACT`.
- affected_files: `frontend/tests/m2-stage9-vertical.spec.ts`.
- blocks_current_path: NO
- safe_continuation: Use formal API creation and server-returned IDs; do not add
  an M3 or unapproved product surface.
- status: DEFERRED
- resolution: Safe M2 boundary documented; production detail and refresh flows
  are fully exercised after formal creation.
- focused_verification: Vertical browser test passed without route interception.
- exit_gate_impact: LOW disclosed limitation, not a production detail-route gap.
- m3_entry_impact: M3 must not assume an ID-less M2 creation UI exists.

### M2-S9-007

- stage: C
- severity: LOW
- area: focused test database isolation
- authoritative_requirement: Focused tests that assume an empty database must
  run in an isolated migrated database; browser acceptance state is not a test
  fixture for unrelated suites.
- observed_behavior: A focused Literature API test counted 11 candidates instead
  of 1 when pytest was run against the persistent Stage 9 browser database.
- evidence: 38 tests passed and
  `test_search_candidates_remain_separate_until_explicit_import` failed only on
  the pre-existing candidate count.
- root_cause: The command reused `reca_stage9_browser`, which intentionally
  retains the production vertical records for refresh testing.
- affected_files: Test runtime only.
- blocks_current_path: NO
- safe_continuation: Migrate and use a separate `reca_stage9_focus` database for
  focused pytest; preserve the product assertion unchanged.
- status: RESOLVED
- resolution: Migrated and used a separate `reca_stage9_focus` database; the
  product assertion was not changed.
- focused_verification: 39 focused Alembic, QueryPlan, Literature, and Document
  API tests passed in the isolated database.
- exit_gate_impact: None if isolated regression passes.
- m3_entry_impact: Preserve per-suite database isolation in M3 acceptance.

### M2-S9-008

- stage: C
- severity: LOW
- area: browser acceptance CORS configuration
- authoritative_requirement: Browser origins not explicitly configured by the
  server must fail closed; acceptance origins must match the isolated harness.
- observed_behavior: A vertical rerun on ad hoc port 5185 remained on `/login`.
- evidence: Direct login returned 400 and database inspection showed the
  test-only Stage 9 owner was missing. A second run on the configured 5182 origin
  failed identically, ruling out CORS as the root cause.
- root_cause: The earlier focused pytest command accidentally used the persistent
  browser database and its cleanup removed the acceptance user; this is the same
  database-isolation root cause as `M2-S9-007`.
- affected_files: Test runtime only.
- blocks_current_path: NO
- safe_continuation: Restore the test-only owner through the normal application
  `init_db` path, then use port 5182 with `reuseExistingServer=false`.
- status: RESOLVED
- resolution: Restored the isolated test owner through normal `init_db`, kept
  browser pytest on its own database, and reran on the configured origin.
- focused_verification: Production browser vertical passed 1/1 in 6.3s.
- exit_gate_impact: None if the configured-origin rerun passes.
- m3_entry_impact: Keep browser and API origin configuration paired.

### M2-S9-009

- stage: D
- severity: LOW
- area: Stage 9 migration command
- authoritative_requirement: Empty and repeated migrations must run against an
  explicitly created isolated database.
- observed_behavior: The first full-gate command attempted `.Trim()` on an empty
  PowerShell query result, skipped database creation, and Alembic correctly
  failed because `reca_stage9_full` did not exist.
- evidence: PostgreSQL `FATAL: database "reca_stage9_full" does not exist`.
- root_cause: Shell handling of a zero-row scalar result, not migration code.
- affected_files: Test runtime only.
- blocks_current_path: NO
- safe_continuation: Create the uniquely named empty database directly, then run
  upgrade, repeated upgrade, and `alembic check`.
- status: RESOLVED
- resolution: Created the isolated database directly and completed all three
  migration checks.
- focused_verification: Empty upgrade reached `0012_document_upload`, repeated
  upgrade passed, and `alembic check` found no new operations.
- exit_gate_impact: Migration gate remains pending until rerun.
- m3_entry_impact: None after corrected migration verification.

### M2-S9-010

- stage: D
- severity: MEDIUM
- area: Project service/Route typing
- authoritative_requirement: Strict mypy and response-envelope contracts must
  agree on service return arity and server-projected allowed actions.
- observed_behavior: `list_projects` was annotated as a three-tuple while
  returning two values; `list_members` was annotated as a two-tuple while
  returning data, pagination, and allowed actions. Strict mypy reported four
  related errors across service and Route unpacking.
- evidence: Strict mypy errors at `projects/service.py:546,710` and
  `api/routes/projects.py:135,247`.
- root_cause: Return annotations were not updated consistently with the member
  allowed-actions response change.
- affected_files: `backend/app/projects/service.py`.
- blocks_current_path: NO
- safe_continuation: Correct only the two annotations and rerun mypy plus Project
  Route/service tests.
- status: RESOLVED
- resolution: Corrected only the two return annotations.
- focused_verification: Strict mypy passed for 80 source files and 17 focused
  Project service/Route tests passed.
- exit_gate_impact: Backend quality gate blocked until verified.
- m3_entry_impact: M3 must inherit typed server-action envelopes.

### M2-S9-011

- stage: D
- severity: LOW
- area: full backend test container assembly
- authoritative_requirement: Full backend tests must run with the test
  environment and repository files required by cross-layer contract tests.
- observed_behavior: The first full run produced 244 passed, 2 skipped, and 4
  failures: one expected `ENVIRONMENT=test`, while three could not read
  `/app/.env.example` or `/app/frontend/src/shared/environment.ts`.
- evidence: `test_private_user_creation_is_not_exposed_outside_local` and three
  `test_frontend_environment.py` failures; all other tests passed.
- root_cause: The Stage 9 API harness mounts only `backend/` and runs as `local`;
  it was suitable for vertical acceptance but incomplete for repository-level
  backend tests.
- affected_files: Test runtime only.
- blocks_current_path: NO
- safe_continuation: Supply the two repository contract files to the disposable
  container filesystem, set `ENVIRONMENT=test`, and use a fresh migrated DB.
- status: RESOLVED
- resolution: Supplied the repository contract files to the disposable
  container, set `ENVIRONMENT=test`, and reran against a fresh migrated DB.
- focused_verification: Full backend suite passed 248 tests with 2 opt-in Live
  tests skipped; Ruff format/check and strict mypy also passed.
- exit_gate_impact: Full backend gate pending.
- m3_entry_impact: Preserve full-repository mounts in clean-room CI.

### M2-S9-012

- stage: D
- severity: MEDIUM
- area: clean-room Playwright isolation
- authoritative_requirement: Clean-room browser tests must execute the current
  source and must not reuse an unrelated development server.
- observed_behavior: The first clean-room run passed every Compose, migration,
  health, Worker, persistence, frontend, and security step except Playwright;
  Playwright reused port 5173 and ended with 52 passed and 62 failed after 6.6m.
- evidence: Clean-room run `reca-m0-acceptance-20260803-072407` and the
  independent 5186 full run with 114/114 passing.
- root_cause: Both acceptance scripts invoked the shell config without `CI=1`
  or an isolated `RECA_PLAYWRIGHT_PORT`, so its default allowed server reuse.
- affected_files: `scripts/m0-acceptance.ps1`, `scripts/m0-acceptance.sh`.
- blocks_current_path: NO
- safe_continuation: Force `CI=1` and dedicated port 15174 in both scripts, then
  rerun clean-room.
- status: RESOLVED
- resolution: Both acceptance entry points use `CI=1` and dedicated port 15174.
- focused_verification: Clean-room rerun
  `reca-m0-acceptance-20260803-073400` passed Playwright 114/114 and every
  functional/security step.
- exit_gate_impact: Clean-room gate blocked until rerun.
- m3_entry_impact: M3 clean-room must preserve current-source browser isolation.

### M2-S9-013

- stage: D
- severity: MEDIUM
- area: final Exit/M3 handoff documentation
- authoritative_requirement: Before the final commit, Exit status must be
  `READY_FOR_FINAL_COMMIT_VERIFICATION`, M3 status must be
  `PENDING_FINAL_COMMIT`, historical issue states must be marked stale, and
  repository documents must not contain machine-local evidence paths.
- observed_behavior: The initial Stage 9 closeout still used
  `PENDING_M2_EXIT_GATE`, retained a Stage 7 `M2-ISSUE-0010=OPEN` marker, and
  recorded temporary evidence using absolute local paths.
- evidence: Review against `CODEX_M2_STAGE9_CLOSEOUT_PROMPTS.md` section 7.
- root_cause: The first report refresh preceded the final closeout-status rules.
- affected_files: `M2_EXIT_GATE_REPORT.md`, `M2_TO_M3_HANDOFF.md`,
  `M2_STAGE9_EXECUTION_LOG.md`, `OPEN_DESIGN_REDESIGN_CHECKPOINT.md`.
- blocks_current_path: NO
- safe_continuation: Preserve historical facts with `DOC_STALE`, use run IDs,
  and keep M3 explicitly blocked on the authorized final commit.
- status: RESOLVED
- resolution: Statuses, stale markers, evidence references, and reusable M3
  regression commands were corrected.
- focused_verification: Final status scan, PowerShell/Bash acceptance-script
  syntax checks, generated-client/UI/mock guards, and `git diff --check` passed.
- exit_gate_impact: Exit status now accurately identifies the sole commit gate.
- m3_entry_impact: Handoff is ready for Stage E without authorizing M3 early.

## Stage D Final Verification

| Gate | Result | Evidence |
| --- | --- | --- |
| Backend format/lint/type | PASS | Ruff format/check passed; strict mypy passed 80 source files. |
| Full backend | PASS | 248 passed, 2 opt-in Live tests skipped. |
| Migration | PASS | Empty upgrade and repeated upgrade reached `0012_document_upload`; `alembic check` clean. |
| Frontend quality/build | PASS | Format, lint, generated client, UI boundary, production mock guard, and production build passed. |
| Full Playwright | PASS | 114/114 passed on isolated port 5186. |
| Production vertical | PASS | 1/1 passed through production Route/API/database/object storage/Job/Worker and refresh. |
| Clean-room | PASS | All functional steps and Playwright 114/114 passed in external run `reca-m0-acceptance-20260803-073400`. |
| Security audit | PASS WITH DISCLOSURE | Repository/container Secret scans and Python audit passed; Node audit retains only `M2-ISSUE-0008` LOW. |

## End Baseline

```text
ended_at: 2026-08-03 Asia/Shanghai
branch: feat/m2-research-literature
HEAD: ac6447c081c881fedb818525871a8bd100410cb5
working_tree: DIRTY; 60 modified and 75 untracked entries; existing M2/Open Design changes preserved
migration_script_head: 0012_document_upload
verified_database_head: 0012_document_upload
M2_EXIT_GATE=FAIL/READY_FOR_FINAL_COMMIT_VERIFICATION
M3_ENTRY=PENDING_FINAL_COMMIT
```

No commit was created because the user has not explicitly authorized the final
commit. `M2-ISSUE-0010` is resolved; `M2-ISSUE-0001` is the sole blocking Exit
Gate issue. `M2-S9-002` and `M2-ISSUE-0008` are disclosed LOW, non-blocking
deferrals. No M3 business implementation was started.

The dedicated Stage 9 API container and the six explicitly named Stage 9 test
databases were removed after verification. Default project services and user
data were not deleted or reset.

## Stage E Commit-Scoped Verification

### M2-S9-014

- stage: E
- severity: MEDIUM
- area: Prompt checkout integrity
- authoritative_requirement: The final implementation SHA must preserve LF
  Prompt assets and pass manifest/hash tests in a repository-external fresh
  checkout.
- observed_behavior: The first detached worktree from implementation commit
  `ec4949777190a846de45904c20d41a35df9c6510` checked out
  `prompt-manifest.yaml` with CRLF on Windows, while all Prompt text assets
  remained LF.
- evidence: `git ls-files --eol` reported `i/lf w/crlf attr/text=auto` for the
  manifest in fresh run `reca-m2-fresh-20260803-080947`.
- root_cause: `.gitattributes` forced LF for Prompt `*.txt` files but omitted
  the Prompt manifest YAML.
- affected_files: `.gitattributes`.
- blocks_current_path: NO
- safe_continuation: Add an exact manifest LF attribute, create a new
  implementation SHA, and repeat all commit-scoped verification from a new
  detached worktree.
- status: RESOLVED
- resolution: Added an explicit LF rule for
  `backend/app/agents/prompts/prompt-manifest.yaml` and created replacement
  implementation SHA `ac34ef95a546c71fe9a08bd3e98f4a1b1db115fd`.
- focused_verification: Detached fresh checkout reported `i/lf w/lf` for all
  five Prompt assets; manifest/hash tests passed 6/6.
- exit_gate_impact: None; `M2-ISSUE-0001` is RESOLVED.
- m3_entry_impact: None; M3 Entry is ALLOWED.

### M2-S9-015

- stage: E
- severity: HIGH
- area: clean-room frontend dependency isolation
- authoritative_requirement: Commit-scoped clean-room must run only from the
  committed source and locked dependency inputs, without relying on a dirty
  development worktree.
- observed_behavior: Fresh clean-room run
  `reca-m2-stagee-cleanroom-20260803-081231` passed infrastructure, migration,
  API, Worker, persistence, backend, and Secret gates, but frontend quality and
  Playwright failed because Biome, TypeScript, and Playwright were unavailable.
  The same run's Node audit also encountered an external connection refusal.
- evidence: `frontend-tests.log` reported `command not found: biome` and
  `command not found: tsc`; `playwright-shell.log` could not resolve the local
  Playwright CLI.
- root_cause: Both clean-room entry points invoked frontend tools without first
  installing the root `bun.lock` dependency graph. Earlier dirty-worktree runs
  had an existing root `node_modules`, masking the isolation defect.
- affected_files: `scripts/m0-acceptance.ps1`,
  `scripts/m0-acceptance.sh`.
- blocks_current_path: NO
- safe_continuation: Install the exact frozen Bun lock before frontend gates,
  then repeat clean-room and the production vertical from a new implementation
  SHA. Keep Node audit fail-closed and repeat it with the clean-room run.
- status: RESOLVED
- resolution: Added a named `frontend-dependencies` step using
  `bun install --frozen-lockfile` to both acceptance entry points.
- focused_verification: Fresh clean-room run
  `reca-m2-stagee-cleanroom-20260803-081709` passed dependency installation,
  frontend format/lint/build, Playwright 114/114, and all other gates.
- exit_gate_impact: None; clean-room is commit-scoped and reproducible.
- m3_entry_impact: M3 must retain the frozen-lock clean-room install step.

### M2-S9-016

- stage: E
- severity: LOW
- area: production vertical harness invocation
- authoritative_requirement: The production vertical must migrate and seed its
  isolated database through the committed backend prestart entry point.
- observed_behavior: The first harness command used
  `backend/scripts/prestart.sh` inside a container whose working directory was
  already `/app/backend`, so the command returned file not found before any
  migration ran.
- evidence: Fresh vertical run `reca-m2-stagee-vertical-20260803-082115` first
  reported `backend/scripts/prestart.sh: No such file or directory`.
- root_cause: Host-relative and container-working-directory-relative paths were
  mixed in the one-off acceptance command.
- affected_files: Runtime command only.
- blocks_current_path: NO
- safe_continuation: Invoke the committed entry point as
  `bash scripts/prestart.sh` in the same isolated Compose project.
- status: RESOLVED
- resolution: Corrected the one-off command without changing repository code;
  empty migration through `0012_document_upload` and initial user creation
  completed before the API started.
- focused_verification: Production vertical E2E passed 1/1 in 7.9 seconds; the
  named API container and isolated Compose volumes were removed afterward.
- exit_gate_impact: None.
- m3_entry_impact: M3 acceptance commands must distinguish host and container
  working directories.

## Stage E Final Verification

| Gate | Result | Evidence |
| --- | --- | --- |
| Implementation commit | PASS | `ac34ef95a546c71fe9a08bd3e98f4a1b1db115fd` on `feat/m2-research-literature`. |
| Detached fresh checkout | PASS | Repository-external worktree created directly from the implementation SHA. |
| Prompt LF/hash | PASS | Five assets were LF; manifest/hash tests passed 6/6. |
| Commit-scoped clean-room | PASS | Run `reca-m2-stagee-cleanroom-20260803-081709`; Playwright 114/114 and all functional/security gates passed, with the disclosed LOW Node advisory. |
| Production vertical | PASS | Run `reca-m2-stagee-vertical-20260803-082115`; 1/1 passed through production Route/API/database/object storage/Job/Worker and refresh. |
| Scoped cleanup | PASS | Dedicated API container and `reca_m2_stagee_vertical` containers, networks, and volumes removed; default project untouched. |

```text
stage_e_completed_at: 2026-08-03 Asia/Shanghai
branch: feat/m2-research-literature
implementation_sha: ac34ef95a546c71fe9a08bd3e98f4a1b1db115fd
migration_head: 0012_document_upload
M2_EXIT_GATE=PASS
M3_ENTRY=ALLOWED
```

`M2-ISSUE-0001`, `M2-ISSUE-0010`, `M2-S9-014`, `M2-S9-015`, and
`M2-S9-016` are RESOLVED. `M2-ISSUE-0008` and `M2-S9-002` remain explicit
LOW, non-blocking disclosures. No M3 business implementation was started.

### M2-S9-017

- stage: E
- severity: HIGH
- area: generated route tree and clean-room repository integrity
- authoritative_requirement: A commit-scoped clean-room must use the locked
  generator output and must finish without changing tracked repository files.
- observed_behavior: After the first PASS clean-room on implementation SHA
  `ac34ef95a546c71fe9a08bd3e98f4a1b1db115fd`, the detached worktree contained
  a tracked rewrite of `frontend/src/routeTree.gen.ts` with the same routes but
  generator-normalized ordering.
- evidence: `git status --short` reported the route tree modified; its diff was
  108 insertions and 108 deletions. The original clean-room only captured Git
  status before build and therefore did not fail on the post-build drift.
- root_cause: The committed generated route tree did not match the exact locked
  TanStack generator output, and both acceptance scripts lacked a final tracked
  worktree cleanliness assertion.
- affected_files: `frontend/src/routeTree.gen.ts`,
  `scripts/m0-acceptance.ps1`, `scripts/m0-acceptance.sh`.
- blocks_current_path: YES
- safe_continuation: Commit the deterministic generated output, add a final
  tracked-tree gate to both scripts, and repeat clean-room from the replacement
  implementation SHA.
- status: IN_PROGRESS
- resolution: Generated output and final Git-status gates prepared; verification
  pending.
- focused_verification: Pending replacement-SHA clean-room.
- exit_gate_impact: The prior clean-room result remains functional evidence but
  cannot be the final repository-integrity evidence.
- m3_entry_impact: M3 Entry remains contingent on the replacement clean-room.
