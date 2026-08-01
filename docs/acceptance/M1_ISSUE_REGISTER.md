# RECA M1 Issue Register

This file is the M1 implementation evidence and issue ledger. It is not a
Requirement, Contract, product authority, or replacement for the M1 milestone
and testing authorities.

## Baseline

```text
Stage: M1-0
Branch: feat/m1-foundation
Contract Freeze commit: 482fbcbe2dbc92578561b5b71d9c778ca16b012e
Contract Freeze tag: m1-contract-freeze-approved
Migration script head: 0002_enable_pgvector_extension
Initialized: 2026-07-31
```

## Vocabulary

Severity uses the existing repository values:

```text
BLOCKER
CRITICAL
HIGH
MEDIUM
LOW
```

Status uses the existing repository values:

```text
OPEN
RESOLVED
```

Issue IDs are allocated sequentially when a real M1 implementation issue is
first recorded:

```text
M1-ISSUE-0001
M1-ISSUE-0002
...
```

## Summary

| Severity | Open | Resolved |
| --- | ---: | ---: |
| BLOCKER | 0 | 0 |
| CRITICAL | 0 | 0 |
| HIGH | 2 | 1 |
| MEDIUM | 2 | 4 |
| LOW | 0 | 0 |

Exit Gate classification after M1-7 repair:

| Classification | Issues |
| --- | --- |
| Blocks M1 Exit Gate | None |
| Does not block M1 Exit Gate | None outside the accepted/deferred set below |
| Accepted risk / deferred P0-Full | `M1-ISSUE-0001`, `M1-ISSUE-0002`, `M1-ISSUE-0004`, `M1-ISSUE-0007` |

## Active Issues

| ID | Stage | Severity | Status | Area | Summary | Blocks current subtask | Blocks M1 Exit Gate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M1-ISSUE-0001 | M1-1 | HIGH | OPEN | Project delete contract | The required second-confirmation transport for project soft delete is not defined. | NO, delete remains deferred | NO |
| M1-ISSUE-0002 | M1-1 | HIGH | OPEN | Superuser override | Several public operations allow an audited administrative override but do not define how the required reason is supplied. | NO, unsupported overrides remain disabled | NO |
| M1-ISSUE-0003 | M1-1 | MEDIUM | RESOLVED | Audit request ID | The AuditLog model authority said UUID while the approved M0 request-ID boundary accepts validated opaque strings such as `trace-123`. | NO | NO |
| M1-ISSUE-0004 | M1-2 | MEDIUM | OPEN | Artifact URL/session TTL | Artifact upload and authorized-download responses require expiration timestamps, but the approved contract gives examples without a normative TTL. | NO | NO |
| M1-ISSUE-0005 | M1-2 | HIGH | RESOLVED | Artifact browser download | Browser-facing signed URLs now use a separately configured public MinIO endpoint. | NO | NO |
| M1-ISSUE-0006 | M1-2 | MEDIUM | RESOLVED | Backend database regression suite | Legacy tests and isolated test mounts now match approved M0 behavior. | NO | NO |
| M1-ISSUE-0007 | M1-3 | MEDIUM | OPEN | Job event retention | SSE requires short-term replay and heartbeat but does not freeze cache TTL, history length, or one heartbeat interval. | NO | NO |
| M1-ISSUE-0008 | M1-5 | MEDIUM | RESOLVED | Backend strict typing | Repo-wide strict Mypy now passes without broad ignores. | NO | NO |
| M1-ISSUE-0009 | M1-8 | MEDIUM | RESOLVED | Ruff import classification | Linux CI inferred a different first-party import boundary for one Artifact API test. | NO | NO |

The open M0 LOW disclosures remain in
[M0_ISSUE_REGISTER.md](./M0_ISSUE_REGISTER.md). They may be referenced by M1
regression evidence but are not copied into this register.

## Required Issue Record

Each future issue entry must include:

```text
ID
Stage
Severity
Status
Area
Summary
Evidence
Affected requirement/contract
Impact
Safe workaround / deferred behavior
Blocks current subtask: YES/NO
Blocks M1 Exit Gate: YES/NO
Suggested repair
Resolution evidence
```

## Resolved Issues

`M1-ISSUE-0003`, `M1-ISSUE-0005`, `M1-ISSUE-0006`, and
`M1-ISSUE-0008` were resolved during M1-7. Evidence is recorded in each detailed
entry below.

## Detailed Issues

### M1-ISSUE-0001

- ID: M1-ISSUE-0001
- Stage: M1-1
- Severity: HIGH
- Status: OPEN
- Area: Project delete contract
- Summary: `DELETE /api/v1/projects/{project_id}` requires a second confirmation,
  but the public contract does not define a confirmation field, header, token, or
  challenge flow.
- Evidence: `PROJ-P0-008` requires second confirmation while the Project API only
  states that the request may include a deletion reason.
- Affected requirement/contract: `PROJ-P0-008`; Project API section 14.8.
- Impact: Implementing the destructive command would require inventing a public
  request contract.
- Safe workaround / deferred behavior: Do not register the delete route. Continue
  create, read, update, archive, restore, membership, authorization, and audit work.
- Classification: Accepted risk / deferred P0-Full.
- Owner: Product/API.
- Deferred target: P0-Full project lifecycle contract clarification.
- Blocks current subtask: NO; project delete remains outside the registered API.
- Blocks M1 Exit Gate: NO; M1 completion section 9.13 does not require public
  project deletion.
- Suggested repair: Freeze one explicit second-confirmation request contract and
  its replay/concurrency behavior before implementation.
- Resolution evidence: Not resolved; deferral is explicit and the undefined route
  remains unregistered.

### M1-ISSUE-0002

- ID: M1-ISSUE-0002
- Stage: M1-1
- Severity: HIGH
- Status: OPEN
- Area: Superuser administrative override
- Summary: Security requires every superuser override to carry an audit reason,
  but member add/remove and project read/archive/restore operations have no public
  reason transport.
- Evidence: Security Controls section 4.1 and the Project authorization contract
  require actor, project, target, request_id, reason, outcome, and AuditLog. Only
  ProjectMember role update/ownership transfer currently has a reason field.
- Affected requirement/contract: Project authorization section 14.0; ProjectMember
  sections 14A.2-14A.4; Security Controls section 4.1.
- Impact: Automatically treating `is_superuser` as membership would bypass the
  required auditable policy boundary.
- Safe workaround / deferred behavior: Do not automatically bypass membership.
  Permit the explicitly reasoned ProjectMember PATCH override only; other public
  operations use normal membership authorization until the contract is frozen.
- Classification: Accepted risk / deferred P0-Full.
- Owner: Security/API.
- Deferred target: P0-Full administrative recovery and override contract.
- Blocks current subtask: NO; unsupported overrides remain disabled.
- Blocks M1 Exit Gate: NO; M1 requires project isolation, not a comprehensive
  superuser recovery surface.
- Suggested repair: Freeze a single administrative-override command/header and
  reason schema, including denied-attempt audit behavior and read no-disclosure.
- Resolution evidence: Not resolved; membership remains mandatory except for the
  already reasoned and audited member mutation path.

### M1-ISSUE-0003

- ID: M1-ISSUE-0003
- Stage: M1-1
- Severity: MEDIUM
- Status: RESOLVED
- Area: Audit request ID persistence
- Summary: AuditLog declares `request_id` as UUID, while the approved M0 request
  boundary accepts validated opaque IDs such as `trace-123`.
- Evidence: `RequestObservabilityMiddleware` preserves bounded client IDs and M0
  regression tests explicitly use `trace-123`; the foundation data model says UUID.
- Affected requirement/contract: AuditLog model; M0/M1 error compatibility and
  request observability baseline.
- Impact: A PostgreSQL UUID column would reject valid approved request IDs and lose
  audit association.
- Safe workaround / deferred behavior: Persist the already validated request ID as
  a bounded 64-character string without changing response behavior.
- Blocks current subtask: NO.
- Blocks M1 Exit Gate: NO.
- Suggested repair: Amend the AuditLog field type to an opaque bounded request-ID
  string, or tighten the M0 request-ID contract through a separately approved change.
- Resolution evidence: `FOUNDATION_AND_PROJECT_MODELS.md` now defines AuditLog and
  ModelInvocation `request_id` as a validated opaque `String(64)`, matching the
  implemented model, migration, and M0 request observability tests. The isolated
  clean-room request-ID check passed in evidence
  `D:\Temp\User\reca-m0-acceptance-20260801-033102`.

### M1-ISSUE-0004

- ID: M1-ISSUE-0004
- Stage: M1-2
- Severity: MEDIUM
- Status: OPEN
- Area: Artifact upload and download expiration
- Summary: The Artifact contract requires `expires_at` for upload sessions and
  authorized downloads, but specifies example timestamps rather than a normative
  duration or configuration field.
- Evidence: Project API sections 14B.2 and 14B.6 show approximately 30-minute
  upload and 5-minute download windows without freezing those values as rules.
- Affected requirement/contract: Artifact API sections 14B.2, 14B.3 and 14B.6.
- Impact: Implementations can agree on lifecycle and authorization while choosing
  different expiration durations.
- Safe workaround / deferred behavior: Use the approved examples as the M1
  implementation defaults: 30 minutes for upload sessions and 5 minutes for
  authorized downloads. Do not expose these values as a new public setting.
- Classification: Accepted risk / deferred P0-Full.
- Owner: Backend/Platform.
- Deferred target: P0-Full deployment configuration and operational tuning.
- Blocks current subtask: NO.
- Blocks M1 Exit Gate: NO; response expiration remains explicit and the internal
  defaults are covered by Artifact tests.
- Suggested repair: Freeze the two TTL durations or name existing Settings fields
  that own them in a future incremental contract clarification.
- Resolution evidence: Not resolved; bounded M1 defaults are implemented without
  adding an unapproved public setting.

### M1-ISSUE-0005

- ID: M1-ISSUE-0005
- Stage: M1-2
- Severity: HIGH
- Status: RESOLVED
- Area: Artifact authorized-download delivery
- Summary: The authorized-download contract permits a signed object URL or a
  backend stream, but the standard Compose configuration signs the internal-only
  `http://minio:9000` endpoint and publishes no browser-reachable MinIO port.
- Evidence: `docker-compose.yml` configures `MINIO_ENDPOINT=http://minio:9000` for
  the API and does not publish the MinIO service; the implemented download
  projection signs that configured endpoint as required by the current adapter.
- Affected requirement/contract: Artifact API section 14B.6; File Model and Agent
  Security authorized-download rules; M1 Artifact frontend acceptance.
- Impact: Authorization, audit, and signature generation work inside the Compose
  network, but the returned URL cannot deliver the object to a browser in the
  standard deployment.
- Safe workaround / deferred behavior: No workaround remains.
- Blocks current subtask: NO.
- Blocks M1 Exit Gate: NO.
- Suggested repair: Freeze either a browser-reachable object-storage public
  endpoint distinct from the internal endpoint, or a backend-streaming download
  transport with explicit authorization and replay semantics.
- Resolution evidence: `MINIO_ENDPOINT` remains the private API/Worker endpoint;
  `MINIO_PUBLIC_ENDPOINT` is used only to sign and return browser-facing URLs.
  Compose binds MinIO to loopback, adapter/config regression tests pass, and the
  complete clean-room including MinIO persistence and 139 database tests passed
  in `D:\Temp\User\reca-m0-acceptance-20260801-033102`.

### M1-ISSUE-0006

- ID: M1-ISSUE-0006
- Stage: M1-2
- Severity: MEDIUM
- Status: RESOLVED
- Area: Backend database regression suite
- Summary: Several legacy Auth/User tests expect FastAPI `detail` responses even
  though the approved M0 application handler returns the M0 `error` envelope;
  additional tests expect the local-only private route in `ENVIRONMENT=test` and
  incomplete SMTP patches to enable email.
- Evidence: The pre-repair isolated full database run reported 20 failures while
  119 tests passed. A detached worktree at approved baseline `482fbcb` reproduced the same
  classes of failures before M1 production changes. The required isolated M0
  clean-room and the M1 affected regression suites pass.
- Affected requirement/contract: M0 error compatibility strategy; backend test
  environment contract; M1 final regression gate.
- Impact: Resolved; the aggregate database suite is now an isolated acceptance
  step and matches the approved M0 compatibility behavior.
- Safe workaround / deferred behavior: No workaround remains.
- Blocks current subtask: NO.
- Blocks M1 Exit Gate: NO.
- Suggested repair: Align legacy test assertions and environment fixtures with the
  approved M0 compatibility behavior, then make the aggregate database suite a
  required final M1 regression command.
- Resolution evidence: Auth/User tests now assert the approved M0 error envelope,
  email delivery is mocked at the service boundary, the private route remains
  unavailable in `ENVIRONMENT=test`, and repository-level environment fixtures are
  mounted read-only. `backend-database-tests` passed with 139 tests and
  `backend-tests` passed with 43 tests in clean-room evidence
  `D:\Temp\User\reca-m0-acceptance-20260801-033102`.

### M1-ISSUE-0007

- ID: M1-ISSUE-0007
- Stage: M1-3
- Severity: MEDIUM
- Status: OPEN
- Area: Job SSE event retention
- Summary: The approved SSE contract requires short-term event replay and suggests
  a 15-30 second heartbeat, but does not freeze a cache TTL, retained event count,
  or one normative heartbeat interval.
- Evidence: Common Job/SSE sections 13.5 and 13.6 define replay behavior and the
  history-miss response without specifying retention parameters.
- Affected requirement/contract: M1 Job/SSE foundation; `Last-Event-ID` reconnect;
  frontend stale/degraded behavior.
- Impact: Correct implementations can differ in how long reconnect remains
  resumable before returning `job.resync_required`.
- Safe workaround / deferred behavior: Use internal M1 defaults of 200 events, one
  hour TTL, and 15-second heartbeat. Keep PostgreSQL detail polling authoritative
  and do not expose a new public Settings field without contract approval.
- Classification: Accepted risk / deferred P0-Full.
- Owner: Backend/Platform.
- Deferred target: P0-Full operational tuning and deployment settings.
- Blocks current subtask: NO.
- Blocks M1 Exit Gate: NO; polling remains authoritative and reconnect/history
  miss behavior is contract-tested independently of the tuning values.
- Suggested repair: Freeze minimum retention and heartbeat requirements or assign
  ownership to named existing deployment settings in an incremental clarification.
- Resolution evidence: Not resolved; the internal defaults are bounded and tested,
  and no public compatibility promise is inferred from them.

### M1-ISSUE-0008

- ID: M1-ISSUE-0008
- Stage: M1-5
- Severity: MEDIUM
- Status: RESOLVED
- Area: Backend strict typing
- Summary: Repo-wide `mypy app` reports 18 errors in eight existing M0 and
  M1-1 through M1-4 modules. The new M1-5 `app/agents` and ModelInvocation model
  pass strict Mypy independently.
- Evidence: The final M1-5 audit reports `no-any-return` in existing MinIO,
  Project, Artifact, Approval, and Job helpers; untyped Celery decorators; and
  two unused ignores in Job events. `mypy app/agents app/models.py` passes.
- Affected requirement/contract: M1 final backend quality and Exit Gate; no
  ModelInvocation or PromptContract behavior is affected.
- Impact: Resolved; the accumulated backend now passes repo-wide strict Mypy.
- Safe workaround / deferred behavior: No workaround remains.
- Blocks current subtask: NO.
- Blocks M1 Exit Gate: NO.
- Suggested repair: Resolve the 18 typed-return/decorator/unused-ignore findings
  during the M1 final repair slice, grouped by their owning modules.
- Resolution evidence: Typed JSON decoding, storage reads, and Celery task
  registration were repaired without broad ignores. `python -m mypy app` reports
  `Success: no issues found in 56 source files`; Ruff and the complete clean-room
  also pass.

### M1-ISSUE-0009

- ID: M1-ISSUE-0009
- Stage: M1-8
- Severity: MEDIUM
- Status: RESOLVED
- Area: Ruff import classification
- Summary: Remote `backend-quality` reported `I001` for the Artifact API test
  import block while Ruff 0.15.20 passed the same commit on Windows and in a
  Linux container.
- Evidence: GitHub Actions run `30678477391`, jobs `91310476956` and
  `91311764292`, consistently reported the same import-classification failure at
  `backend/tests/api/routes/test_artifacts.py:1`; local Ruff 0.15.20 and a Linux
  Ruff 0.15.20 container did not reproduce it.
- Affected requirement/contract: M1 remote backend quality gate; no public or
  domain contract is affected.
- Impact: Resolved; first-party import classification no longer depends on
  runner path or environment inference.
- Safe workaround / deferred behavior: No workaround remains.
- Blocks current subtask: NO.
- Blocks M1 Exit Gate: NO.
- Suggested repair: Explicitly configure the existing `app` and `tests`
  first-party packages for Ruff isort without changing enabled rules or ignores.
- Resolution evidence: `backend/pyproject.toml` now declares both packages in
  `known-first-party`; Ruff 0.15.20 passes the full backend tree and the Artifact
  API test in the repository's supported local and Linux environments.
