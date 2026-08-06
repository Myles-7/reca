# M7 Issue Register

Date: 2026-08-06
Current stage: 5

## Summary

| ID | Stage | Severity | Status | Area | Blocks current | Blocks M7 exit | Blocks M8 entry |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M7-ISSUE-0001 | 0 | LOW | RESOLVED | Windows host Python/PostgreSQL verification | no | no | no |
| M7-ISSUE-0002 | 1 | MEDIUM | RESOLVED | Compose/PostgreSQL migration verification | no | no | no |
| M7-ISSUE-0003 | 2 | MEDIUM | RESOLVED | MinIO/Worker/export integration verification | no | no | no |
| M7-ISSUE-0004 | 4 | HIGH | RESOLVED | Open Design integration entry and Codex contract gaps | no | no | no |
| M7-ISSUE-0005 | 4 | HIGH | RESOLVED | PostgreSQL 0018 enum creation | no | no | no |
| M7-ISSUE-0006 | 4 | HIGH | RESOLVED | Worker image export lock metadata | no | no | no |
| M7-ISSUE-0007 | 4 | LOW | RESOLVED | README integrity and Agent-log wording | no | no | no |
| M7-ISSUE-0008 | 5 | LOW | RESOLVED | Stage-5 backend formatting gate | no | no | no |
| M7-ISSUE-0009 | 5 | MEDIUM | RESOLVED | Export Collector type boundaries | no | no | no |
| M7-ISSUE-0010 | 5 | MEDIUM | RESOLVED | Manuscript parser worker payload typing | no | no | no |
| M7-ISSUE-0011 | 5 | MEDIUM | RESOLVED | Repository-wide ty baseline | no | no | no |
| M7-ISSUE-0012 | 5 | HIGH | RESOLVED | M6 Revision Audit response compatibility | no | no | no |
| M7-ISSUE-0013 | 5 | MEDIUM | RESOLVED | DOCX structure false degradation | no | no | no |
| M7-ISSUE-0014 | 5 | LOW | RESOLVED | M3 downgrade test milestone scope | no | no | no |
| M7-ISSUE-0015 | 5 | LOW | RESOLVED | React Flow Spike server portability | no | no | no |
| M7-ISSUE-0016 | 5 | HIGH | RESOLVED | Worker/API MinIO bucket mismatch | no | no | no |
| M7-ISSUE-0017 | 5 | LOW | RESOLVED | Clean-room test input and endpoint portability | no | no | no |
| M7-ISSUE-0018 | 5 | HIGH | RESOLVED | Export readiness JSON persistence | no | no | no |
| M7-ISSUE-0019 | 5 | HIGH | RESOLVED | Export confirmation item coverage | no | no | no |
| M7-ISSUE-0020 | 5 | HIGH | RESOLVED | Authorized MinIO download network path | no | no | no |
| M7-ISSUE-0021 | 5 | LOW | RESOLVED | xyflow adoption metadata drift | no | no | no |
| M7-ISSUE-0022 | 5 | MEDIUM | RESOLVED | Python dependency audit transient TLS failure | no | no | no |
| M7-ISSUE-0023 | 5 | LOW | RESOLVED | M3 trusted PDF highlight render timing | no | no | no |

## M7-ISSUE-0001

```yaml
stage: 0
severity: LOW
status: RESOLVED
area: Windows host Python/PostgreSQL verification
authoritative_requirement: >
  M7 focused verification must use the repository Python 3.14 environment and database-backed
  migration/service tests must use a reliable PostgreSQL execution path.
observed_behavior: >
  The default host python command resolves to Python 3.13 without pytest, while the project
  requires Python >=3.14. The retained M6 limitation also states that direct host PostgreSQL
  connectivity is unreliable on Windows.
evidence: >
  `python --version` returned 3.13.13 and `python -m pytest` reported no pytest. The repository
  venv executed the M7 ZIP Spike successfully. M6 Exit verified migrations in the Compose network.
root_cause: >
  The interactive shell default is not the repository-managed runtime, and PostgreSQL is not
  reliably published to the host test process in this Windows setup.
affected_files:
  - backend/pyproject.toml
  - docs/acceptance/M6_EXIT_GATE_REPORT.md
  - backend/tests/spikes/test_m7_zip_manifest_spike.py
blocks_current_stage: false
blocks_m7_exit_gate: false
blocks_m8_entry: false
safe_continuation: >
  Use the repository venv for no-database focused tests. Use the authoritative Compose-network
  runner for Stage 1 migration/PostgreSQL verification and record host-only failures separately.
resolution: >
  Kept host execution fail-explicit and used the repository-managed Python environment plus the
  isolated Compose-network PostgreSQL runner. Stage 5 verified the complete database, migration,
  Worker and MinIO paths without treating the unavailable host-default runtime as a pass.
focused_verification: >
  Final clean-room acceptance passed 461 PostgreSQL tests with 3 skips, empty and repeated upgrades,
  alembic check, the single 0018 head, Worker execution and MinIO persistence/recovery.
security_or_scientific_integrity_impact: >
  Low direct impact because no result is inferred from the unavailable host runner. Treating a
  skipped database check as a pass would be unsafe, so later stages must retain explicit evidence.
```

## M7-ISSUE-0002

```yaml
stage: 1
severity: MEDIUM
status: RESOLVED
area: Compose/PostgreSQL migration verification
authoritative_requirement: >
  Stage 1 must verify a fresh PostgreSQL upgrade, repeated upgrade, `alembic check`, database
  constraints and the single migration head using the authoritative Compose-network runner.
observed_behavior: >
  Docker Desktop was initially unavailable. Once restored, the first real upgrade exposed a
  duplicate PostgreSQL enum creation defect; the transaction rolled back cleanly at 0017.
evidence: >
  After correcting the enum helper and two model/migration drift items, an isolated Compose-network
  PostgreSQL database passed fresh upgrade, repeated upgrade, `alembic check`, the single-head
  assertion and the focused evidence-graph/export database suite. The development database reports
  `0018_m7_evidence_export (head)`.
root_cause: >
  The original verification gap was environmental. Real execution then found that explicitly
  created PostgreSQL ENUM references still had `create_type` enabled, plus two SQLModel mappings
  that did not exactly match the frozen migration.
affected_files:
  - backend/app/alembic/versions/0018_m7_evidence_export.py
  - backend/app/models.py
  - backend/app/evidence_graph/
  - backend/app/api/routes/evidence_graph.py
  - backend/tests/evidence_graph/
blocks_current_stage: false
blocks_m7_exit_gate: false
blocks_m8_entry: false
safe_continuation: >
  Continue Stage-4 focused integration using isolated Compose-network databases. Stage 5 still
  owns the complete migration and PostgreSQL Gate; do not replace it with this focused evidence.
resolution: >
  Reused explicitly created ENUMs with `create_type=False`, aligned `Export.project_id` and
  `ReproPackage.total_size_bytes` with migration 0018, and verified the resulting schema on real
  PostgreSQL without stamping or rewriting migrations 0013-0017.
focused_verification: >
  Fresh upgrade, repeated upgrade and `alembic check` passed; one 0018 head remains. A unique
  temporary PostgreSQL database ran `backend/tests/evidence_graph` and `backend/tests/exports` with
  33 passing tests and was then force-dropped.
security_or_scientific_integrity_impact: >
  The failed upgrade was transactional and left no partial M7 schema. Real PostgreSQL verification
  now supports the schema claim; the complete Stage-5 Gate remains independently required.
```

## M7-ISSUE-0003

```yaml
stage: 2
severity: MEDIUM
status: RESOLVED
area: MinIO/Worker/export integration verification
authoritative_requirement: >
  Stage 2 must verify real PostgreSQL, Worker and MinIO packaging, upload/download/hash checks,
  failure cleanup, retry/cancel recovery, historical immutability and cross-project disclosure.
observed_behavior: >
  Docker Desktop was initially unavailable. After recovery, the rebuilt Worker first lacked the
  adopted uv.lock and bun.lock files required by the packager; a real vertical run later exposed
  README wording that did not explicitly name SHA-256 or the Agent-log NOT_AVAILABLE state.
evidence: >
  The corrected Worker image contains both locks. An isolated PostgreSQL/Valkey 9-10/Celery/MinIO
  run created a real Export, completed its Job, downloaded the package, reopened the ZIP, verified
  all Manifest sizes and SHA-256 values, authorized download, and removed both MinIO objects.
root_cause: >
  The original verification gap was environmental. Docker build bind mounts supplied locks to
  `uv sync` without retaining them in the runtime image, and README integrity wording was implicit.
affected_files:
  - backend/app/exports/
  - backend/app/api/routes/exports.py
  - backend/app/workers/jobs.py
  - backend/tests/exports/test_service.py
blocks_current_stage: false
blocks_m7_exit_gate: false
blocks_m8_entry: false
safe_continuation: >
  Continue only focused Stage-4 browser and issue collection. Stage 5 still owns the aggregate
  tamper/failure/retry/cancel/history and clean-room Gate.
resolution: >
  Copied the adopted lock files into the production backend image, made README integrity and
  Agent-log status explicit, and added a real Worker/MinIO export vertical regression test.
focused_verification: >
  Real vertical test passed once: project 540bd132-a06c-4e9d-a2e7-3786fa577fed, Export
  187d88c2-8a31-46df-b65d-c8c5b3566cf2, Job b6ff05e8-dc46-49a8-8307-f06373cd1910,
  ReproPackage 0504b850-92d7-4648-b3fa-5e2c69920cc8, 21 ZIP members, 20 Manifest files and ZIP
  SHA-256 6fc1464fe660a2462370377685143e83419be007c2c884009aca0e86ed240b34.
security_or_scientific_integrity_impact: >
  Package truth was checked against real object bytes and Manifest hashes. No sensitive or Agent
  run data was fabricated; the isolated database, queues, Worker and objects were cleaned.
```

## M7-ISSUE-0004

```yaml
stage: 4
severity: HIGH
status: RESOLVED
area: Open Design integration entry and Codex contract gaps
authoritative_requirement: >
  Codex Stage 4 may use the accepted visual Workspace for full production integration only after
  Open Design explicitly writes READY_FOR_CODEX_INTEGRATION=YES. Audit Job, immutable package
  history, retry/cancel fixtures and Link confirmation must have authoritative typed projections.
observed_behavior: >
  Open Design's initial READY decision was NO because M7-OD-0003 through
  M7-OD-0006 lacked complete Audit Job, Package history and executable action fixtures. Codex
  corrected them and Open Design has now completed formal reacceptance.
evidence: >
  M7_OPEN_DESIGN_ACCEPTANCE_REPORT.md now reports PASS and READY_FOR_CODEX_INTEGRATION=YES. The
  original 372/372 visual matrix remains accepted; current fixture, boundary, mock, generated,
  Route and build gates pass, and corrected-contract Playwright passes 4/4 tests.
root_cause: >
  Stage-3 ViewModel projected only one Export Job, one selected ReproPackage and incomplete action
  fixture combinations. Those Codex-owned gaps are corrected; the remaining blocker is the
  required Open Design reacceptance of the changed typed contract and local UI correction.
affected_files:
  - docs/acceptance/M7_OPEN_DESIGN_ACCEPTANCE_REPORT.md
  - docs/acceptance/M7_OPEN_DESIGN_ISSUE_REGISTER.md
  - frontend/src/features/evidence-workspace/model.ts
  - frontend/src/features/evidence-workspace/mappers.ts
  - frontend/src/features/evidence-workspace/queries.ts
  - frontend/src/features/evidence-workspace/fixtures/index.ts
  - frontend/src/features/evidence-workspace/ui/EvidenceWorkspace.tsx
  - frontend/src/routes/_layout/projects.$projectId_.evidence.tsx
blocks_current_stage: false
blocks_m7_exit_gate: false
blocks_m8_entry: false
safe_continuation: >
  Continue the remaining Stage-4 real production integration and longitudinal browser work using
  the accepted Workspace. Do not treat UI READY as M7 Exit or package completion.
resolution: >
  Added the read-only Audit Job projection, immutable paginated ReproPackage history API and
  ViewModel, executable retry/cancel and Link-confirm fixtures, production Evidence Route,
  server-response deep-link handling, package-history UI consumption and focused guards. Open
  Design revalidated the corrected contracts and explicitly wrote READY_FOR_CODEX_INTEGRATION=YES.
focused_verification: >
  M7 fixture guard passed 8 tests/125 assertions; Stage-4 Route guard passed 2 tests/13 assertions;
  corrected-contract Design Preview Playwright passed 4/4; format 293 files, lint 297 files,
  generated, production-mock, UI-boundary and production build all passed.
security_or_scientific_integrity_impact: >
  Reacceptance confirms retry/cancel target the correct Export Job, Audit Job remains distinct,
  Link confirmation uses formal identity/version and Package history is immutable server data.
```

## M7-ISSUE-0005

```yaml
stage: 4
severity: HIGH
status: RESOLVED
area: PostgreSQL 0018 enum creation
authoritative_requirement: >
  Migration 0018 must upgrade a real PostgreSQL database from 0017, support repeated upgrade and
  pass alembic check without partially created schema objects.
observed_behavior: >
  The first real PostgreSQL upgrade failed because each enum was explicitly created and then the
  table/column DDL attempted to create the same enum again.
evidence: >
  PostgreSQL raised DuplicateObject for evidence_object_type while alembic_version remained at
  0017 and no M7 tables were committed. After the fix, fresh/repeated upgrade and alembic check
  passed against the Compose PostgreSQL service.
root_cause: >
  The enum helper returned a PostgreSQL ENUM with create_type enabled after explicitly creating
  it with checkfirst.
affected_files:
  - backend/app/alembic/versions/0018_m7_evidence_export.py
  - backend/tests/evidence_graph/test_stage1_contracts.py
blocks_current_stage: false
blocks_m7_exit_gate: false
blocks_m8_entry: false
safe_continuation: >
  Continue Stage-4 PostgreSQL/Worker/MinIO/browser verification only after the corrected migration
  passes on the real service. Do not stamp or manually delete enum types.
resolution: >
  Return create_type=False enum references after the helper performs the single explicit checked
  creation, preventing table and column DDL from issuing duplicate CREATE TYPE statements.
focused_verification: >
  Real PostgreSQL upgrade 0017 to 0018, repeated upgrade, alembic current/check and migration
  regression tests passed.
security_or_scientific_integrity_impact: >
  No data was rewritten and the failed transaction rolled back. Fixing the migration preserves
  schema truth instead of bypassing it with a manual stamp.
```

## M7-ISSUE-0006

```yaml
stage: 4
severity: HIGH
status: RESOLVED
area: Worker image export lock metadata
authoritative_requirement: >
  ReproPackage Manifest and README must record the actual adopted Python/Bun locks, and the
  production Worker must package those exact files without fabricating metadata.
observed_behavior: >
  The rebuilt Worker image contained backend/pyproject.toml but not /app/uv.lock or /app/bun.lock,
  while the packager reads both paths during every Export.
evidence: >
  `ls` inside the current Worker reported both lock paths missing. The real Worker/MinIO vertical
  test passed after the Dockerfile copied the repository locks into the image.
root_cause: >
  Docker build bind mounts made lock files available to uv sync but did not retain them in the
  final image filesystem.
affected_files:
  - backend/Dockerfile
  - backend/app/exports/packager.py
blocks_current_stage: false
blocks_m7_exit_gate: false
blocks_m8_entry: false
safe_continuation: >
  Rebuild API and Worker from the current tree, verify both lock files in the image, then run the
  real Worker/MinIO Export flow. Do not replace missing locks with generated placeholders.
resolution: >
  Copy the repository uv.lock and bun.lock into /app in the backend image so runtime metadata and
  packaged lock members reflect the actual adopted dependency state.
focused_verification: >
  Current Worker image lock audit and real PostgreSQL/Worker/MinIO ReproPackage vertical test passed.
security_or_scientific_integrity_impact: >
  The fix prevents a failed Export or falsely described runtime environment. No secret or host
  absolute path is introduced into the package.
```

## M7-ISSUE-0007

```yaml
stage: 4
severity: LOW
status: RESOLVED
area: README integrity and Agent-log wording
authoritative_requirement: >
  README_REPRODUCE must explain package hash verification and explicitly report M8 Agent logs as
  NOT_AVAILABLE without fabricating a run record.
observed_behavior: >
  The first real ZIP passed byte and Manifest validation, but README used the indirect instruction
  "verify against manifest.json" and a prose Agent-log sentence rather than the frozen terms.
evidence: >
  The initial real vertical test reached COMPLETED and downloaded the ZIP, then failed only on the
  missing literal `SHA-256`. Inspection confirmed the Manifest hashes were correct and the README
  truthfully denied Agent logs, but the wording was less explicit than the acceptance contract.
root_cause: >
  Unit tests covered truthful limitations and NOT_AVAILABLE semantics but did not freeze the two
  operator-facing labels used by the longitudinal acceptance test.
affected_files:
  - backend/app/exports/manifest.py
  - backend/tests/integration/test_m7_export_vertical.py
blocks_current_stage: false
blocks_m7_exit_gate: false
blocks_m8_entry: false
safe_continuation: >
  Keep the explicit wording and verify it through both the focused Manifest tests and the real
  downloaded ZIP. Do not add placeholder Agent records.
resolution: >
  README now instructs verification of every member's SHA-256 against manifest.json and states
  `Agent logs: NOT_AVAILABLE until M8; no run record was fabricated.`
focused_verification: >
  Ruff passed, three focused Manifest/redaction tests passed, and the isolated real Worker/MinIO
  vertical test passed with the final downloaded README.
security_or_scientific_integrity_impact: >
  The clearer wording reduces the risk of treating implicit integrity guidance or absent Agent
  execution as stronger reproducibility evidence than the package actually provides.
```

## M7-ISSUE-0008

```yaml
stage: 5
severity: LOW
status: RESOLVED
area: Stage-5 backend formatting gate
authoritative_requirement: >
  The complete M7 Exit Gate requires Ruff format and lint to pass for the backend application and
  test suite before completion can be approved.
observed_behavior: >
  The first Stage-5 Ruff format check reported three files that would be reformatted, so lint and
  type checks were not yet treated as valid final evidence.
evidence: >
  `ruff format --check backend/app backend/tests` identified `backend/app/main.py`,
  `backend/app/models.py`, and `backend/tests/integration/test_m7_export_vertical.py`.
root_cause: >
  Stage-4 changes were functionally verified but the final repository-wide backend formatter gate
  had not been applied after the last integration edits.
affected_files:
  - backend/app/main.py
  - backend/app/models.py
  - backend/tests/integration/test_m7_export_vertical.py
blocks_current_stage: false
blocks_m7_exit_gate: false
blocks_m8_entry: false
safe_continuation: >
  Apply the repository formatter only to the reported files, then rerun backend format, lint and
  type checks before continuing with database and browser gates.
resolution: >
  Applied Ruff formatting only to the three reported files without changing behavior.
focused_verification: >
  Repository-wide backend Ruff format and lint checks passed for 250 files.
security_or_scientific_integrity_impact: >
  No runtime or scientific behavior is changed by the formatter. Keeping the failure visible
  prevents an unverified quality gate from being reported as passing.
```

## M7-ISSUE-0009

```yaml
stage: 5
severity: MEDIUM
status: RESOLVED
area: Export Collector type boundaries
authoritative_requirement: >
  Package collection must preserve explicit domain-object boundaries and pass the strict backend
  type gate before M7 Exit approval.
observed_behavior: >
  Strict mypy found incompatible assignments where the candidate collector reused `version` and
  `figure` names across DatasetVersion, ManuscriptVersion, and Figure lookup branches.
evidence: >
  The Stage-5 mypy run reported two M7 Collector errors at the manuscript and figure lookups. The
  other reported migration errors came from invoking mypy without the backend configuration that
  excludes Alembic and are runner configuration noise, not accepted as passing evidence.
root_cause: >
  Cross-domain local variable reuse made valid runtime branches ambiguous to static analysis and
  weakened the readability of the authority checks.
affected_files:
  - backend/app/exports/collector.py
blocks_current_stage: false
blocks_m7_exit_gate: false
blocks_m8_entry: false
safe_continuation: >
  Use domain-specific local names without changing collection behavior, then rerun Ruff, strict
  mypy, ty, export safety tests, and the complete no-database suite.
resolution: >
  Replaced cross-domain local reuse with `dataset_version`, `manuscript_version`,
  `stored_figure`, and `artifact_figure` variables.
focused_verification: >
  Strict mypy passed 148 source files; focused Export/Manifest safety tests passed as part of a
  20-test focused batch.
security_or_scientific_integrity_impact: >
  The runtime behavior was unchanged, but ambiguous authority-object handling is relevant to
  package integrity. Static proof now needs to confirm that dataset, manuscript, and figure facts
  cannot be mixed accidentally.
```

## M7-ISSUE-0010

```yaml
stage: 5
severity: MEDIUM
status: RESOLVED
area: Manuscript parser worker payload typing
authoritative_requirement: >
  M0-M6 behavior must not regress, strict backend typing must pass, and untrusted asynchronous
  payloads must be validated before they become authoritative domain snapshots.
observed_behavior: >
  Strict mypy found that `parse_docx` returned an untyped multiprocessing queue value directly
  from a function declared to return a manuscript snapshot object.
evidence: >
  The correctly configured Stage-5 mypy run reported `no-any-return` at
  `backend/app/manuscripts/parser.py:136`.
root_cause: >
  The process boundary checked the success flag but did not validate the successful payload's root
  type before returning it to M6 manuscript rules.
affected_files:
  - backend/app/manuscripts/parser.py
  - backend/tests/manuscripts/test_parser_rules.py
blocks_current_stage: false
blocks_m7_exit_gate: false
blocks_m8_entry: false
safe_continuation: >
  Validate that the worker result is a dictionary, reject all other root types, and rerun the
  focused manuscript parser test plus strict backend type and no-database gates.
resolution: >
  Added an explicit dictionary-root validation at the multiprocessing boundary and rejected every
  non-object success payload before manuscript rule evaluation.
focused_verification: >
  The new parser regression passed; the focused manuscript/export batch passed 20 tests and strict
  mypy passed 148 source files.
security_or_scientific_integrity_impact: >
  Rejecting malformed success payloads prevents invalid parser output from entering manuscript
  rule evaluation as if it were a valid authoritative snapshot.
```

## M7-ISSUE-0011

```yaml
stage: 5
severity: MEDIUM
status: RESOLVED
area: Repository-wide ty baseline
authoritative_requirement: >
  Stage 5 explicitly requires a complete ty verification in addition to the established Ruff and
  strict mypy backend quality gates.
observed_behavior: >
  The initial complete ty run reported 104 diagnostics. After root-cause corrections, the same
  complete command reports zero diagnostics.
evidence: >
  Stage 5 ran `ty check app --exclude app/alembic --output-format concise` before and after the
  correction. The final command completed with zero diagnostics.
root_cause: >
  The repository adopted ty as a Stage-5 requested check after multiple milestones had already
  established patterns that mypy accepts but ty's current SQLModel/Pydantic analysis does not.
affected_files:
  - backend/app/models.py
  - backend/app/cleaning/engine.py
  - backend/app/cleaning/service.py
  - backend/app/core/config.py
  - backend/app/core/observability.py
blocks_current_stage: false
blocks_m7_exit_gate: false
blocks_m8_entry: false
safe_continuation: >
  Continue every independent M7 functional, database, browser, clean-room, security, and supply
  chain Gate. Do not add blanket ignores or rewrite historical models solely to satisfy a new
  checker without regression evidence. Reassess exit impact after all other Gates complete.
resolution: >
  Preserved SQLAlchemy timezone behavior through a local typed SQLModel compatibility helper,
  narrowed cleaning selector/action unions with explicit runtime classes, used a typed Settings
  constructor boundary, and replaced the logger marker attribute with a dedicated handler type.
focused_verification: >
  Complete ty passed with zero diagnostics; Ruff format/check, focused cleaning/core/health tests,
  full clean-room PostgreSQL/no-database suites and real M7 browser acceptance passed.
security_or_scientific_integrity_impact: >
  The corrected static boundaries now pass the requested Gate without suppressing diagnostics;
  this reduces the risk of invalid union, configuration or logging assumptions reaching runtime.
```

## M7-ISSUE-0012

```yaml
stage: 5
severity: HIGH
status: RESOLVED
area: M6 Revision Audit response compatibility
authoritative_requirement: >
  AuditResult generalization must preserve strict M6 Revision Audit read/write compatibility and
  must not expose unrelated generalized fields through the frozen M6 response contract.
observed_behavior: >
  Creating a Revision Audit raised a FastAPI ResponseValidationError because `audit_data` spread
  the generalized model dump into `RevisionAuditPublic`, producing ten forbidden extra fields.
evidence: >
  The real PostgreSQL suite failed `test_revision_audit_and_claim_confirmation_backend_closure`
  with extra fields including outcome, findings, limitations, target object, and source snapshot.
root_cause: >
  The M6 serializer used an unrestricted ORM model dump instead of an explicit compatibility
  projection after 0018 added generalized AuditResult columns.
affected_files:
  - backend/app/manuscripts/stage2.py
  - backend/tests/api/routes/test_manuscripts.py
blocks_current_stage: false
blocks_m7_exit_gate: false
blocks_m8_entry: false
safe_continuation: >
  Replace the model spread with the exact frozen M6 fields and rerun Revision Audit API tests plus
  the full PostgreSQL suite.
resolution: >
  Replaced the unrestricted AuditResult model dump with the exact frozen M6 Revision Audit public
  fields, leaving generalized M7 fields available only through the M7 audit contract.
focused_verification: >
  The real PostgreSQL manuscript API suite passed 6 tests, including Revision Audit creation,
  execution, readback, and Claim confirmation closure.
security_or_scientific_integrity_impact: >
  The bug breaks a previously accepted API and could disclose generalized internal audit fields to
  an older client contract. The fix must preserve the M6 shape exactly.
```

## M7-ISSUE-0013

```yaml
stage: 5
severity: MEDIUM
status: RESOLVED
area: DOCX structure false degradation
authoritative_requirement: >
  Manuscript checks must degrade only for structures actually present in the document content and
  M0-M6 accepted manuscript behavior must not regress.
observed_behavior: >
  Plain python-docx documents were classified LOW_CONFIDENCE and blocked from low-risk fixes even
  though no paragraph used numbering.
evidence: >
  Two real PostgreSQL manuscript tests failed because the generated package contained
  `word/numbering.xml`, which was treated as an unsupported structure despite no `<w:numPr>` use.
root_cause: >
  The parser correctly checked `<w:numPr>` usage but also treated the mere existence of the standard
  numbering definition part as an advanced unsupported feature.
affected_files:
  - backend/app/manuscripts/parser.py
  - backend/tests/manuscripts/test_parser_rules.py
blocks_current_stage: false
blocks_m7_exit_gate: false
blocks_m8_entry: false
safe_continuation: >
  Keep actual numbering usage fail-closed, stop degrading on an unused definition part, and rerun
  parser, manuscript API, and complete PostgreSQL tests.
resolution: >
  Removed unused numbering definitions from degradation, added actual direct/style numbering
  detection, and allowed only a structurally validated standard Office bibliography customXml
  triplet. All other customXml remains unknown and blocks auto-fix.
focused_verification: >
  Six parser regressions passed, including actual numbering and unrecognized customXml fail-closed;
  all six real PostgreSQL manuscript API tests passed.
security_or_scientific_integrity_impact: >
  False degradation blocks valid reviewed workflows; removing the false positive must not permit
  genuinely numbered content to bypass unsupported-structure handling.
```

## M7-ISSUE-0014

```yaml
stage: 5
severity: LOW
status: RESOLVED
area: M3 downgrade test milestone scope
authoritative_requirement: >
  Migration tests must verify each milestone's reversible boundary without pretending later
  explicitly irreversible PostgreSQL enum extensions can be crossed safely.
observed_behavior: >
  The M3 runtime test upgraded to current head and then attempted to downgrade through 0017 to
  0012, triggering the intentional 0017 enum-extension guard.
evidence: >
  `test_m3_empty_upgrade_repeat_check_and_safe_downgrade` failed at the explicit 0017 RuntimeError
  after the M3 tables themselves had upgraded successfully.
root_cause: >
  A milestone-local downgrade test used the moving `head` target, so later irreversible migrations
  silently expanded its scope.
affected_files:
  - backend/tests/alembic/test_migration_runtime.py
blocks_current_stage: false
blocks_m7_exit_gate: false
blocks_m8_entry: false
safe_continuation: >
  Test the 0013-to-0012 reversible boundary directly, then upgrade to current head and run Alembic
  drift checks separately.
resolution: >
  Scoped the downgrade portion to 0013 -> 0012, then upgraded twice to current head and ran the
  Alembic drift check without crossing the intentional 0017 enum downgrade guard.
focused_verification: >
  The focused real PostgreSQL migration runtime test passed on an isolated database.
security_or_scientific_integrity_impact: >
  No production schema defect is shown. Correct scoping prevents a false migration failure while
  retaining the explicit irreversible enum guard.
```

## M7-ISSUE-0015

```yaml
stage: 5
severity: LOW
status: RESOLVED
area: React Flow Spike server portability
authoritative_requirement: >
  The 500-node React Flow Spike must be reproducible without relying on an undocumented server
  already listening on a hard-coded port.
observed_behavior: >
  The standalone Playwright config used port 5178 but did not start a server, so its first Stage-5
  invocation failed with connection refused.
evidence: >
  Both Spike cases failed before page assertions. A dedicated Docker Vite server subsequently
  served the actual Spike HTML and both cases passed.
root_cause: >
  The Spike config froze a base URL but provided neither a webServer lifecycle nor an environment
  override for an externally managed isolated server.
affected_files:
  - frontend/tests/spikes/playwright.m7.config.ts
blocks_current_stage: false
blocks_m7_exit_gate: false
blocks_m8_entry: false
safe_continuation: >
  Keep the default 5178 URL while allowing the acceptance runner to provide an explicit base URL;
  always verify the actual Spike DOM rather than accepting an SPA fallback HTTP 200.
resolution: >
  Added `RECA_M7_SPIKE_BASE_URL` support and ran the default 5178 contract against a dedicated,
  scoped Docker Vite container built from the current workspace.
focused_verification: >
  Two Playwright Spike tests passed: 500 nodes/499 edges with connect persistence disabled, and
  keyboard/mobile table fallback without horizontal overflow.
security_or_scientific_integrity_impact: >
  Test-only portability change. It improves evidence reliability and does not alter production
  graph authority or persistence behavior.
```

## M7-ISSUE-0016

```yaml
stage: 5
severity: HIGH
status: RESOLVED
area: Worker/API MinIO bucket mismatch
authoritative_requirement: >
  Worker must revalidate and finalize ReproPackage bytes in the same configured private MinIO
  bucket used by API download verification; COMPLETED may never point to missing object content.
observed_behavior: >
  Clean-room completed the Export and persisted AVAILABLE Artifacts, but the API-side vertical test
  received a 404 downloading the ZIP.
evidence: >
  The isolated environment configured `MINIO_BUCKET=reca-acceptance` for API. Compose omitted
  MINIO_BUCKET from Worker, so Worker used the Settings default `reca`; development passed only
  because both defaults coincidentally matched.
root_cause: >
  Worker Compose environment did not propagate the configured bucket, violating the shared object
  storage boundary across API and asynchronous execution.
affected_files:
  - docker-compose.yml
  - backend/tests/core/test_frontend_environment.py
  - backend/tests/integration/test_m7_export_vertical.py
blocks_current_stage: false
blocks_m7_exit_gate: false
blocks_m8_entry: false
safe_continuation: >
  Propagate the exact MINIO_BUCKET setting to Worker, lock it with a Compose regression test, then
  rerun the focused environment test and clean-room backend database Gate.
resolution: >
  Propagated MINIO_BUCKET to Worker and locked API/Worker object-store parity with a structured
  Compose regression test.
focused_verification: >
  The environment regression passed 5 tests. The final clean-room suite completed the export,
  downloaded the package through the API boundary and passed MinIO persistence/recovery.
security_or_scientific_integrity_impact: >
  High integrity impact: a mismatched bucket can produce a false COMPLETED state whose immutable
  package is not downloadable from the authorized API boundary.
```

## M7-ISSUE-0017

```yaml
stage: 5
severity: LOW
status: RESOLVED
area: Clean-room test input and endpoint portability
authoritative_requirement: >
  Clean-room tests must consume every declared repository input and must assert environment-derived
  endpoints rather than development-only ports.
observed_behavior: >
  After the MinIO bucket fix, clean-room downloaded the ZIP successfully but failed because the
  vertical test expected port 9000 instead of the configured 19000. The new Compose regression
  also could not read docker-compose.yml because the full-test container did not mount it.
evidence: >
  The second clean-room run reported 457 passing backend tests and only these two portability
  failures; the prior missing-object failure was absent.
root_cause: >
  The vertical assertion froze a local public endpoint, and acceptance runners mounted selected
  contract inputs without the Compose file required by the new environment parity test.
affected_files:
  - backend/tests/integration/test_m7_export_vertical.py
  - scripts/m0-acceptance.ps1
  - scripts/m0-acceptance.sh
blocks_current_stage: false
blocks_m7_exit_gate: false
blocks_m8_entry: false
safe_continuation: >
  Assert the adapter's configured public endpoint, mount docker-compose.yml read-only in both
  acceptance runners, and rerun focused format plus clean-room.
resolution: >
  Made the vertical assertion use the configured public endpoint and mounted docker-compose.yml
  read-only in both clean-room acceptance runners.
focused_verification: >
  Final clean-room acceptance passed 461 PostgreSQL tests, migration, Worker/MinIO and restart
  recovery checks with isolated ports and inputs.
security_or_scientific_integrity_impact: >
  Test-only portability issue. Correcting it prevents environment-specific assumptions from hiding
  real storage isolation defects.
```

## M7-ISSUE-0018

```yaml
stage: 5
severity: HIGH
status: RESOLVED
area: Export readiness JSON persistence
authoritative_requirement: >
  EXPORT_READINESS_AUDIT must persist its deterministic candidate, warning, blocker and source
  snapshot facts in PostgreSQL and return a traceable result for real project objects.
observed_behavior: >
  The isolated real API browser Gate received a 500 from readiness-check when an unconfirmed Claim
  produced a warning whose object_id was a UUID.
evidence: >
  Compose API logs from the 2026-08-06 Stage-5 real-browser run show TypeError: Object of type UUID
  is not JSON serializable while flushing AuditResult warnings/findings to JSONB.
root_cause: >
  Candidate models were encoded at the persistence boundary, but blocker and warning dictionaries
  were stored with live Python UUID values in source_snapshot, result and findings.
affected_files:
  - backend/app/exports/readiness.py
  - backend/tests/exports/test_service.py
  - frontend/tests/projects-m7-real-api.spec.ts
  - scripts/m7-real-browser-acceptance.ps1
blocks_current_stage: false
blocks_m7_exit_gate: false
blocks_m8_entry: false
safe_continuation: >
  Normalize all readiness JSONB payload components with jsonable_encoder, verify a real UUID warning
  against PostgreSQL, then rerun the isolated Claim-to-ReproPackage browser chain.
resolution: >
  JSON-normalized readiness candidates, blockers, warnings and limitations at the persistence
  boundary with FastAPI jsonable_encoder.
focused_verification: >
  The real PostgreSQL UUID warning regression passed. The isolated real-browser Claim-to-package
  chain completed readiness, approval, packaging and authorized download.
security_or_scientific_integrity_impact: >
  High integrity and availability impact: a legitimate project warning could prevent readiness and
  packaging entirely, hiding the formal license/sensitive/invalidation decision path behind a 500.
```

## M7-ISSUE-0019

```yaml
stage: 5
severity: HIGH
status: RESOLVED
area: Export confirmation item coverage
authoritative_requirement: >
  Formal EXPORT_CONFIRMATION must cover every server-projected ApprovalItem and cannot be replaced
  by an empty acknowledgement payload.
observed_behavior: >
  The real browser chain received 422 because the production Container submitted an empty
  item_decisions object while the backend requires a decision for every ApprovalItem.
evidence: >
  The isolated real API run reached NEEDS_CONFIRMATION and failed at Approval POST before the
  ViewModel and mutation mapping were corrected.
root_cause: >
  The Stage-3 presentation contract omitted the backend Approval item collection, so the Container
  could not derive complete server-authoritative item decisions.
affected_files:
  - frontend/src/features/evidence-workspace/model.ts
  - frontend/src/features/evidence-workspace/mappers.ts
  - frontend/src/features/evidence-workspace/mutations.ts
  - frontend/src/features/evidence-workspace/fixtures/index.ts
  - frontend/scripts/check-m7-stage4-contracts.test.ts
blocks_current_stage: false
blocks_m7_exit_gate: false
blocks_m8_entry: false
safe_continuation: >
  Project Approval items into the ViewModel, derive explicit ACCEPT decisions from those items and
  keep the UI Event limited to user intent.
resolution: >
  Added typed Approval items and server-projected item decision construction without making the UI
  authoritative for scope or approval state.
focused_verification: >
  Stage-4 contract guard passed 3 tests and 17 assertions; fixture guard passed 8 tests and 125
  assertions; frontend build and the real browser confirmation chain passed.
security_or_scientific_integrity_impact: >
  The repair preserves formal item-level confirmation and prevents a broad or empty acknowledgement
  from being treated as approval.
```

## M7-ISSUE-0020

```yaml
stage: 5
severity: HIGH
status: RESOLVED
area: Authorized MinIO download network path
authoritative_requirement: >
  The browser must be able to reach the authorized presigned package URL while MinIO remains bound
  to loopback and isolated from untrusted networks.
observed_behavior: >
  Packaging completed and direct API authorization succeeded, but the browser could not connect to
  the presigned MinIO URL because MinIO was attached only to an internal-only Compose network.
evidence: >
  docker compose ps exposed no host-published MinIO port until the service joined the edge network.
root_cause: >
  The service had a loopback ports declaration but no non-internal network path through which Docker
  could publish it to the host browser.
affected_files:
  - docker-compose.yml
  - backend/tests/core/test_frontend_environment.py
  - frontend/tests/projects-m7-real-api.spec.ts
  - scripts/m7-real-browser-acceptance.ps1
blocks_current_stage: false
blocks_m7_exit_gate: false
blocks_m8_entry: false
safe_continuation: >
  Attach MinIO to edge and internal networks, retain the 127.0.0.1 binding and verify both service
  health and an authorized object GET in the browser chain.
resolution: >
  Added the edge network to MinIO without broadening the loopback-only host binding.
focused_verification: >
  The structured Compose regression passed 5 tests. The real browser acceptance returned the ZIP
  with HTTP 200 and non-empty bytes through the authorized MinIO URL.
security_or_scientific_integrity_impact: >
  The fix restores authorized download availability without exposing MinIO beyond the local host.
```

## M7-ISSUE-0021

```yaml
stage: 5
severity: LOW
status: RESOLVED
area: xyflow adoption metadata drift
authoritative_requirement: >
  Third-party Notices and source research must describe the dependency version and actual adopted
  production use truthfully.
observed_behavior: >
  The version, source and MIT license were correct, but the adoption note still said the dependency
  was limited to the Stage-0 Spike and not installed in production.
evidence: >
  The production Evidence Workspace imports @xyflow/react 12.11.2 while THIRD_PARTY_NOTICES.md and
  the source research current-state paragraph retained the Stage-0 snapshot wording.
root_cause: >
  Stage-4 production integration did not refresh the earlier research-phase adoption prose.
affected_files:
  - THIRD_PARTY_NOTICES.md
  - docs/source-research/projects/xyflow.md
blocks_current_stage: false
blocks_m7_exit_gate: false
blocks_m8_entry: false
safe_continuation: >
  Update only adoption status and authority-boundary facts; preserve pinned source and license data.
resolution: >
  Recorded production Workspace use and the presentation-only, non-persisting graph boundary.
focused_verification: >
  Repository search confirms @xyflow/react 12.11.2 in package.json, bun.lock, Notices and source
  research with consistent ALREADY_INTEGRATED wording.
security_or_scientific_integrity_impact: >
  No runtime impact. Accurate adoption metadata is required for supply-chain and authority audits.
```

## M7-ISSUE-0022

```yaml
stage: 5
severity: MEDIUM
status: RESOLVED
area: Python dependency audit transient TLS failure
authoritative_requirement: >
  Security audit must complete against the actual dependency set and may not be silently skipped on
  transient network failure.
observed_behavior: >
  Two clean-room pip-audit attempts failed while querying PyPI with TLS unexpected EOF errors.
evidence: >
  The same isolated environment succeeded when retried and reported no known vulnerabilities.
root_cause: >
  The acceptance scripts had no bounded retry around an external PyPI TLS request.
affected_files:
  - scripts/m0-acceptance.ps1
  - scripts/m0-acceptance.sh
blocks_current_stage: false
blocks_m7_exit_gate: false
blocks_m8_entry: false
safe_continuation: >
  Retry only the exact audit command a bounded number of times and retain a nonzero final result.
resolution: >
  Added three bounded retries with short backoff to both acceptance runners; a final failed audit
  still fails the Gate.
focused_verification: >
  Final full clean-room acceptance completed python-security-audit successfully with no known
  vulnerabilities found.
security_or_scientific_integrity_impact: >
  The correction increases audit availability without weakening dependency or vulnerability checks.
```

## M7-ISSUE-0023

```yaml
stage: 5
severity: LOW
status: RESOLVED
area: M3 trusted PDF highlight render timing
authoritative_requirement: >
  Trusted coordinate highlights must be validated after the authorized PDF canvas has actually
  rendered, including concurrent shell acceptance execution.
observed_behavior: >
  Under full parallel Playwright load, assertions sometimes timed out before pdf.js finished
  rendering and therefore observed zero display-only highlights.
evidence: >
  Full shell runs failed at the five-second count assertion; the focused M3 suite passed after
  asserting the explicit data-render-state ready condition before requiring the highlight.
root_cause: >
  The test waited for canvas visibility rather than the asynchronous render completion state.
affected_files:
  - frontend/tests/projects-m3-evidence.spec.ts
blocks_current_stage: false
blocks_m7_exit_gate: false
blocks_m8_entry: false
safe_continuation: >
  Require actual render readiness with a bounded timeout; keep the expected trusted highlight count.
resolution: >
  Added a shared assertion for data-render-state=ready before checking the server-authorized overlay.
focused_verification: >
  The focused M3 evidence suite passed 6 tests and the final shell Playwright Gate passed 165 tests
  with 2 skips.
security_or_scientific_integrity_impact: >
  The stricter acceptance assertion verifies that authoritative evidence coordinates are displayed
  only after the matching PDF page is rendered.
```
## Stage-0 Closed Observations

- React Flow default nodes expose handles even with graph-level connection disabled. The Spike
  uses RECA-owned custom nodes with non-connectable handles. Browser verification passed; this is
  not an open product defect.
- No Open Design M7 output exists in the current worktree. This is expected before Stage 3 and
  does not block Stage 0 or backend Stages 1-2.

`STAGE_RESULT=PASS_WITH_ISSUES`

`NEXT_STAGE_EXECUTED=NO`

## Stage-3 Review

No new Stage-3 defect remains open. OpenAPI/generated/adapter/ViewModel/Props/Event/fixture and
boundary checks passed. The absence of the production Evidence Route, final visual Workspace and
browser E2E is intentional Stage-3 scope, not a defect. `M7-ISSUE-0002` and `M7-ISSUE-0003` remain
open with their existing safe continuation and continue to block M7 Exit/M8 Entry, but do not block
the Open Design pure-UI handoff.

`STAGE_RESULT=PASS_WITH_ISSUES`

`READY_FOR_OPEN_DESIGN=YES`

`NEXT_STAGE_EXECUTED=NO`

## Stage-4 Review

Codex completed every Stage-4 continuation item allowed while Open Design remains not ready:
generated client and adapter synchronization, Audit Job and Package history projections, typed
fixture repairs, query/mapper/Container compatibility, the single production Evidence Route,
deep-link and server-response mutation handling, and focused contract/build infrastructure.

Docker Desktop recovery allowed the isolated PostgreSQL migration suite and the real
Worker/MinIO ReproPackage vertical chain to pass, resolving `M7-ISSUE-0002` and
`M7-ISSUE-0003`. Focused production-Route Playwright passed two mock-browser cases for
no-disclosure fallback, non-connectable graph projection, table fallback, 390px bounds and
keyboard reachability. Open Design has now reaccepted the corrected contracts and written
`READY_FOR_CODEX_INTEGRATION=YES`; the full real-API browser chain remains separate pending work.

`STAGE_RESULT=PASS_WITH_ISSUES`

`READY_FOR_CODEX_INTEGRATION=YES`

`NEXT_STAGE_EXECUTED=NO`

## Stage-5 Final Review

All M7 issues that affected Exit or M8 Entry are resolved. The final clean-room and real-browser
Gates verified the complete graph, audit, export, package and download chain. Complete ty passes
with zero diagnostics; no ignore expansion or checker weakening was used.

`STAGE_RESULT=PASS`

`M7_EXIT=PASS`

`M7_COMPLETION=APPROVED`

`M8_ENTRY=ALLOWED`

`NEXT_STAGE_EXECUTED=NO`
