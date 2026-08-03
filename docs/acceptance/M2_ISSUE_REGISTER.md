# RECA M2 Issue Register

This file is the M2 implementation evidence and issue ledger. It is not a
Requirement, Contract, product authority, or replacement for the M2 milestone
and testing authorities.

## Baseline

```text
Stage: M2-0
Branch: feat/m2-research-literature
M1 baseline commit: ac6447c
M1 baseline tag: m1-complete
Migration script head: 0007_model_invocation_governance
Initialized: 2026-08-01 10:46:25 +08:00 (Asia/Shanghai)
```

Baseline authorities read for M2-0:

- [Implementation Roadmap](../IMPLEMENTATION_ROADMAP.md)
- [M2 Research and Literature milestone](../roadmap/milestones/M2_RESEARCH_AND_LITERATURE.md)
- [Delivery Workflow](../roadmap/DELIVERY_WORKFLOW.md)
- [M1 Issue Register](./M1_ISSUE_REGISTER.md)

Protected pre-existing and concurrent frontend ownership-boundary work:

```text
frontend/package.json
frontend/design-preview.html
frontend/research-question-preview.html
frontend/scripts/check-production-mocks.mjs
frontend/scripts/check-production-mocks.test.mjs
frontend/scripts/check-ui-boundaries.mjs
frontend/scripts/check-ui-boundaries.test.mjs
frontend/src/design-preview/
frontend/src/features/projects/ProjectWorkspacePage.tsx
frontend/src/features/projects/cache.ts
frontend/src/features/projects/containers/
frontend/src/features/projects/fixtures/
frontend/src/features/projects/mappers.ts
frontend/src/features/projects/model.ts
frontend/src/features/projects/mutations.ts
frontend/src/features/projects/ui/
frontend/src/features/research-question/
frontend/tests/projects-cache.spec.ts
frontend/tests/projects-fixtures.spec.ts
frontend/tests/projects-mappers.spec.ts
frontend/tests/projects-mutations.spec.ts
frontend/tests/projects-workspace.spec.ts
docs/development/M2_FRONTEND_FEATURE_TEMPLATE.md
scripts/ci/frontend-quality.sh
```

These paths are owned by the in-progress frontend boundary task. M2 work must
read and preserve their local state, avoid parallel rewrites of shared entry
points, and integrate through frozen ViewModel, Props, and Event contracts.

## M2 Execution Baseline

Dependency order:

```text
ResearchQuestion domain and versions
-> ResearchQuestion API and Approval integration
-> ResearchQuestion scoping and QueryPlan
-> Literature Provider and deterministic normalization
-> Literature search, import, DOI, and deduplication
-> Document and Artifact binding
-> GROBID conversion, pypdf fallback, Worker, and Job
-> frontend integration
-> M2 end-to-end acceptance and issue repair
```

Parallel boundaries:

- ResearchQuestion domain work may proceed independently from the OpenAlex and
  PDF parser research spikes after each task reads its authority package.
- OpenAlex/PyAlex Provider work may proceed independently from Document parsing
  until Literature import or metadata matching joins the flows.
- GROBID/pypdf conversion may proceed independently from frontend PDF.js
  research; neither may define EvidenceSpan truth in M2.
- Open Design may implement pure M2 UI from frozen typed fixtures while Codex
  implements backend, generated client, adapter, mapper, query, mutation, and
  container layers.
- Alembic heads, generated clients, route trees, adapter entry points, shared
  tokens, and shared layout files must have one active owner at a time.

## Stage Evidence

### M2-1 ResearchQuestion Domain and Migration

```text
Migration head: 0008_research_question_domain
Empty database upgrade: PASS
Repeated upgrade head: PASS
Data-bearing downgrade to 0007 and re-upgrade: PASS
ResearchQuestion domain tests: 12 passed
ResearchQuestion, Approval, and Project regression: 24 passed
Ruff: PASS
Strict mypy: PASS
```

The migration and domain enforce project-scoped identities, immutable version
content, unique version numbers, current-version integrity and Approval-backed
confirmation. AI output status remains separate from domain status.

### M2-2 ResearchQuestion API and Confirmation

```text
ResearchQuestion domain and API tests: 17 passed
ResearchQuestion, Approval, and Project regression: 41 passed
Full backend suite: 150 passed, 7 known Prompt CRLF failures
Ruff: PASS
Strict mypy: 60 source files PASS
OpenAPI required operations: PASS
Generated client consistency: PASS (4 files)
Frontend production build: PASS
ResearchQuestion frontend boundary tests: 5 passed
git diff --check: PASS
```

Coverage includes OWNER, EDITOR, REVIEWER and VIEWER behavior; cross-project
no-disclosure; stale bases and `If-Match`; idempotent replay and payload
conflict; immutable confirmed versions; stale and expired Approval behavior;
AuditLog evidence; and confirmation through the existing Approvals API. No
ResearchQuestion `/confirm` endpoint is registered. The OpenAPI/client
synchronization preserves the concurrent frontend ownership boundary.

### M2-3 ResearchQuestion AI Scoping

```text
Scoping migration revision: 0009_rq_scoping_job
Prompt manifest and hash validation: PASS
M2-3 focused migration, Schema, Service, and API tests: 20 passed
Full backend suite after Prompt EOL repair: 180 passed
```

Scoping uses governed ModelInvocation, Job, ProcessingRun and immutable
MODEL_OUTPUT Artifact records. Recorded mode only succeeds for reviewed golden
input; unmatched input, missing provenance and invalid Schema degrade without
changing ResearchQuestion domain state.

### M2-4 QueryPlan

```text
Migration head: 0010_query_plan_domain
Empty and repeated database upgrade: PASS
Downgrade to 0009 and re-upgrade: PASS
QueryPlan Schema, Service, generation, and API tests: 10 passed
Related backend regression: 94 passed
Full backend suite: 180 passed
Ruff and strict mypy (79 source files): PASS
OpenAPI generated client consistency and frontend build: PASS
UI ownership and production mock guards: PASS (10 tests)
```

QueryPlan supports project-scoped create/read/update with `If-Match`, bilingual
terms, provider-neutral boolean queries and year/language/type/OA filters.
Optional AI generation is Recorded-only, preserves OA preference, records
Prompt and ModelInvocation provenance, and never chooses or calls OpenAlex.

### M2-5 OpenAlex / PyAlex Provider

```text
Adopted dependency: pyalex 0.21
Upstream tag/Commit: v0.21 / 875c708cbb6e449feebc46d2a7a26af8ed8b2fdd
Integration mode: DIRECT_DEPENDENCY_WITH_PROVIDER
Provider and transport tests: 13 passed
Live spike: HTTP 200; two cursor pages; PyAlex/direct HTTP first Work matched
Forced timeout, 429, offline and malformed response tests: PASS
Third-party object leakage test: PASS
No-database regression: 62 passed
Full backend suite on empty migrated PostgreSQL: 193 passed
Ruff and strict mypy (80 source files): PASS
Locked dependency audit: no known vulnerabilities; local `app` package skipped as non-PyPI
```

The frozen boundary uses PyAlex only for Works query encoding. RECA `httpx`
owns explicit timeout and bounded retry; OpenAlex JSON is converted immediately
to internal DTOs with raw snapshot hash and normalization version. Recorded mode
is explicit and degraded. M2-5 creates no migration, business record, search-run
API, cache or frontend contract. No new issue was opened in this stage.

### M2-6 Literature Search, DOI, and Deduplication

```text
Migration head: 0011_literature_search
Empty database upgrade through 0011: PASS
Repeated upgrade, downgrade to 0010, and re-upgrade: PASS
Literature normalization, API, cache, import, DOI, and deduplication tests: 9 passed
M2-5 Provider, QueryPlan, and migration regression: 34 passed
Full backend suite: 203 passed
Ruff and strict mypy (74 source files): PASS
OpenAPI generated client consistency: PASS (4 files)
Frontend TypeScript, production build, mock guard, and UI ownership guard: PASS
Locked dependency audit: no known vulnerabilities; local `app` package skipped as non-PyPI
```

Search candidates and formal `LiteratureRecord` rows are persisted separately.
DOI uniqueness is project-scoped, title similarity never performs an automatic
merge, stale cache use is explicit and degraded, and Provider failure without a
cache creates zero candidates and zero formal records. Search and import remain
project-authorized, audited, idempotent, and no-disclosure across projects.

### M2-7 Document and PDF Upload

```text
Migration head: 0012_document_upload
Empty database upgrade through 0012: PASS
Repeated upgrade, downgrade to 0011, and re-upgrade: PASS
Document upload, validation, binding, isolation, and constraint tests: 12 passed
Document and Literature focused regression: 21 passed
Full backend suite: 216 passed
Ruff and strict mypy (91 source files): PASS
OpenAPI generated client consistency and frontend production build: PASS
Production mock and UI ownership boundary guards: PASS
Locked dependency audit: no known vulnerabilities; local `app` package skipped as non-PyPI
git diff --check: PASS
```

Document upload streams through a temporary staging file, verifies the safe
filename, declared MIME, PDF header, 50 MB limit, server-computed SHA-256,
trailing EOF and explicit encryption markers, then reuses the M1 Artifact
initiate, transfer and complete lifecycle. Original Artifacts remain immutable;
duplicate content receives a distinct Artifact and storage key with explicit
duplicate metadata. Document and LiteratureRecord remain separate and their
optional binding is project-scoped. M2-7 creates no parse Job, page content,
chunks, OCR, EvidenceSpan or extraction result.

### M2-8 GROBID, TEI Converter, and pypdf Fallback

```text
Migration head: 0012_document_upload (no new migration required)
Pinned GROBID image: lfoppiano/grobid:0.8.2
Pinned image digest: sha256:cab12863cab26c818479dbcb6a4f09922ed6caeedfbbf59ef957f52d7195a85d
Real fixed-PDF spike: HTTP 200; cold 14.49s; warm coordinate parse 2.97s
Direct httpx Adapter selected; grobid-client-python not installed
pypdf 6.14.2 and defusedxml 0.7.1 incorporated
M2-8 Adapter, Converter, fallback, API and Worker tests: 21 passed
Ruff focused gate: PASS
Strict mypy: 80 source files PASS using a clean isolated cache
Full backend suite: 241 passed
OpenAPI generated client consistency and frontend production build: PASS
Production mock and UI ownership boundary guards: PASS
Compose configuration and limited GROBID startup: PASS
Locked dependency audit: no known vulnerabilities; local app package skipped as non-PyPI
git diff --check: PASS
```

The implementation retains raw TEI as an immutable `application/tei+xml`
Artifact, converts only namespace-valid page-addressable TEI, replaces pages
and chunks only after successful conversion, and records pypdf as LOW-confidence
degraded page text with no fabricated sections or coordinates. Existing Job
claims prevent duplicate Worker delivery; independent document failures are
isolated. The approved M2 contract now explicitly reuses `JobStatus` for
`Document.parse_status`, so the conservative implementation no longer relies on
an undocumented lifecycle assumption.

### Stage 8 Repair Revalidation

```text
Migration graph head: 0012_document_upload (single head)
Empty and repeated database upgrade: PASS
0008 -> 0009 -> 0008 -> 0009: PASS
Data-bearing 0009 downgrade refusal: PASS
Focused ModelInvocation, Scoping, ResearchQuestion and Project tests: 28 passed
Isolated migration runtime test: 1 passed
Full backend database suite: 173 passed
Compose full backend suite: 246 passed, 2 skipped
Backend no-database suite: 73 passed, 2 skipped
Ruff and strict mypy (93 source files): PASS
Alembic metadata parity check: no new upgrade operations
Frontend format, lint, guards, generated client and build: PASS
Playwright shell, including mobile/long-content/keyboard/degraded: 48 passed
Python dependency audit: no known vulnerabilities
Node dependency audit: one LOW development-tool advisory
Compose acceptance: PASS
Compose resource cleanup: PASS
git diff --check: PASS
```

The Research Question capability projection keeps AI Parse, QueryPlan and
Literature explicitly `NOT_AVAILABLE` for this UI slice. Loading, failed and
unknown projections remain `UNKNOWN` and fail closed. Typed fixtures and design
preview evidence do not constitute production feature completion.

### Contract/Projection Batch B

| Gap | Authoritative source | M2 decision | Safe default |
| --- | --- | --- | --- |
| QueryPlan permission knowledge and creation | Required `QueryPlanPublic.allowed_actions` and `research_question_version_id`; no formal `query_plan.create` capability exists | Detail permissions IMPLEMENTED; create `BLOCKED_BY_CONTRACT` | Update/generate require known status and permissions; create remains rejected by the detail guard. |
| Literature Job retry | `LiteratureSearchRunPublic.job_id`, matching `JobPublic.retryable`, and project-scoped `ProjectPublic.allowed_actions` | IMPLEMENTED | Retry requires a matching failed Search Run/Job, `retryable=true`, known project status, and formal `job.retry`; every missing fact fails closed. |
| Document LiteratureRecord association | Project-scoped `LiteratureRecord.document_id` relationship owned by Document service | IMPLEMENTED as read-only `literature_record_id` | Missing association maps to `null` and is displayed as unbound. |
| Existing ResearchQuestion permissions | Required current `ResearchQuestionVersionPublic.allowed_actions` | IMPLEMENTED | Unknown permission projection disables save, mark-ready, and confirmation intent. |
| Project, Member, and Artifact actions | Existing role action matrix plus project/member/artifact service authorization | IMPLEMENTED as required response `allowed_actions` | Unknown entity state or permission envelope preserves reads and disables writes. |

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

Issue IDs are allocated sequentially when a real M2 implementation issue is
first recorded:

```text
M2-ISSUE-0001
M2-ISSUE-0002
...
```

## Continuous Execution Rule

A non-blocking issue is recorded and implementation continues. A locally
blocking issue keeps the unsafe route or capability unregistered, unavailable,
or explicitly degraded while independent M2 work continues. A global blocker
prevents an M2 completion decision but does not authorize guessing a Contract,
weakening project isolation, fabricating literature or evidence, or lowering a
test gate.

All open issues are reviewed in the final M2 repair stage. An issue remains
`OPEN` until its resolution evidence has been verified.

## Summary

| Severity | Open | Resolved |
| --- | ---: | ---: |
| BLOCKER | 0 | 0 |
| CRITICAL | 0 | 0 |
| HIGH | 0 | 5 |
| MEDIUM | 0 | 4 |
| LOW | 1 | 1 |

Exit Gate classification:

| Classification | Issues |
| --- | --- |
| Blocks M2 Exit Gate | None |
| Does not block M2 Exit Gate | `M2-ISSUE-0008` |

## Active Issues

| ID | Stage | Severity | Status | Area | Summary | Blocks current subtask | Blocks M2 Exit Gate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M2-ISSUE-0008 | Stage 8 repair | LOW | OPEN | Node development dependency advisory | `@babel/core` has one LOW arbitrary file-read advisory through the TanStack router build plugin. | NO | NO |

The open M0 and M1 disclosures remain in their original registers. They may be
referenced by M2 regression evidence but are not copied into this register.

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
Blocks M2 Exit Gate: YES/NO
Suggested repair
Resolution evidence
```

## Resolved Issues

| ID | Stage | Severity | Resolution |
| --- | --- | --- | --- |
| M2-ISSUE-0001 | M2-0 / M2-11 | HIGH | Implementation SHA `ac34ef95a546c71fe9a08bd3e98f4a1b1db115fd` preserves Prompt LF in a detached fresh checkout; manifest/hash tests, clean-room, and production vertical E2E pass. |
| M2-ISSUE-0003 | M2-3 | HIGH | The Alembic revision ID was shortened and empty/repeated migration tests pass. |
| M2-ISSUE-0007 | Stage 8 repair | HIGH | AuditLog now has a project-scoped formal ModelInvocation foreign key and Scoping provenance tests pass. |
| M2-ISSUE-0010 | M2-9 | HIGH | Production routes, generated-client/container integration, refresh recovery, full Playwright, clean-room, and production vertical gates pass. |
| M2-ISSUE-0011 | M2-10 | HIGH | GROBID healthcheck uses an image-supported Bash TCP probe; the recreated container is healthy and the Live PDF smoke passes. |
| M2-ISSUE-0002 | Stage 8 final repair | MEDIUM | SQLModel metadata now represents the inherited Approval audit FK and active OWNER partial unique index; `alembic check` is clean. |
| M2-ISSUE-0004 | Stage 8 final repair | MEDIUM | The approved M2 contract freezes QueryPlan to DRAFT with explicit lock_version and If-Match semantics. |
| M2-ISSUE-0005 | Stage 8 final repair | MEDIUM | The approved M2 contract defines SearchRun JobStatus reuse, candidate separation, cache and degraded response facts. |
| M2-ISSUE-0006 | Stage 8 final repair | MEDIUM | The approved M2 contract defines Document parse_status as the explicit JobStatus mapping already enforced by the service. |
| M2-ISSUE-0009 | M2-11 | LOW | `httpx2==2.9.1` is locked for tests; rebuilt clean-room suites run without the Starlette TestClient deprecation warning. |

## Detailed Issues

### M2-ISSUE-0001

- ID: M2-ISSUE-0001
- Stage: M2-0 / M2-11
- Severity: HIGH
- Status: RESOLVED
- Area: Prompt asset line endings
- Summary: Raw Prompt byte hashing made Prompt identity depend on checkout line
  endings, so a Windows CRLF checkout could disagree with the LF manifest hash.
- Evidence: The original Windows worktree hash differed from the manifest even
  though the logical Prompt text was unchanged. The loader previously hashed
  `path.read_bytes()` without canonicalization.
- Affected requirement/contract: M1 Prompt governance baseline; inherited
  backend quality regression gate.
- Impact: Prompt governance and ModelInvocation creation could fail solely due
  to platform checkout behavior.
- Safe workaround / deferred behavior: None required. Canonical hashing and
  exact Git LF attributes are both committed and verified.
- Blocks current subtask: NO.
- Blocks M2 Exit Gate: NO.
- Suggested repair: Freeze Prompt text assets to LF through a repository EOL
  rule or formally define canonical hash normalization, then verify clean
  checkout behavior on Windows and Linux.
- Resolution evidence: `prompt_content_hash` canonicalizes CRLF and lone CR to
  LF before SHA-256, the formal Prompt contract records that rule, and
  `.gitattributes` forces both Prompt text and the manifest to LF. Detached
  fresh checkout of implementation SHA
  `ac34ef95a546c71fe9a08bd3e98f4a1b1db115fd` reported `i/lf w/lf` for every
  Prompt asset; Prompt manifest/hash tests passed 6/6. Clean-room run
  `reca-m2-stagee-cleanroom-20260803-081709` and production vertical run
  `reca-m2-stagee-vertical-20260803-082115` passed.

### M2-ISSUE-0002

- ID: M2-ISSUE-0002
- Stage: M2-1
- Severity: MEDIUM
- Status: RESOLVED
- Area: Alembic metadata parity
- Summary: `alembic check` reports two inherited M1 constraints as removal
  operations because the database migration facts are not represented in
  SQLModel metadata.
- Evidence: Against a clean database upgraded through
  `0010_query_plan_domain`, Alembic reports only
  `fk_audit_logs_approval_id_approval_records` and
  `uq_project_members_active_owner`; it reports no M2-1 table, enum, index,
  check, unique, or foreign-key drift for M2-1 through M2-4.
- Affected requirement/contract: Migration review and future autogenerate
  safety; inherited M1 Approval audit and active OWNER invariants.
- Impact: A future developer using Alembic autogenerate without review could
  receive incorrect removal operations for two required M1 constraints.
- Safe workaround / deferred behavior: Continue using reviewed explicit
  migrations. Do not accept generated constraint removals. M2-1 migration
  smoke, constraints, empty upgrade and repeated upgrade remain valid.
- Blocks current subtask: NO; the M2-1 migration itself has no detected drift.
- Blocks M2 Exit Gate: NO; required constraints remain present and enforced in
  PostgreSQL.
- Suggested repair: Represent the Approval audit foreign key and active OWNER
  partial unique index in SQLModel metadata, then rerun `alembic check` against
  a clean upgraded database.
- Resolution evidence: `AuditLog.__table_args__` now represents
  `fk_audit_logs_approval_id_approval_records` with `ON DELETE RESTRICT`, and
  `ProjectMember.__table_args__` represents `uq_project_members_active_owner`
  with the existing PostgreSQL predicate. Metadata contract tests and database
  negative tests reject unknown Approval references and a second active OWNER.
  Against a database upgraded through `0012_document_upload`, `alembic check`
  reports `No new upgrade operations detected`.

### M2-ISSUE-0003

- ID: M2-ISSUE-0003
- Stage: M2-3
- Severity: HIGH
- Status: RESOLVED
- Area: Alembic revision identifier length
- Summary: The initial M2-3 revision identifier exceeded the inherited
  `alembic_version.version_num varchar(32)` boundary.
- Evidence: Empty-database upgrade reached the 0009 migration body, then failed
  while storing `0009_research_question_scoping_job` with PostgreSQL
  `StringDataRightTruncation`.
- Affected requirement/contract: M2-3 migration delivery and the inherited
  empty/repeated migration gate.
- Impact: No clean database could advance beyond 0008 even though the enum DDL
  itself was reversible.
- Safe workaround / deferred behavior: The uncommitted revision and migration
  file were both renamed to `0009_rq_scoping_job` before a shared baseline was
  established.
- Blocks current subtask: YES at discovery; resolved before M2-4 domain work.
- Blocks M2 Exit Gate: YES until resolved.
- Suggested repair: Keep every future Alembic revision identifier at or below
  32 characters and assert the boundary in migration contract tests.
- Resolution evidence: Empty upgrade, repeated upgrade, 0010 downgrade to
  `0009_rq_scoping_job` and re-upgrade all pass. An isolated data-bearing test
  also verifies that downgrade is rejected while Scoping Job rows exist, then
  succeeds after cleanup; the migration contract test explicitly asserts the
  revision length and single-head graph. Compose independently passes empty and
  repeated upgrades through `0012_document_upload`.

### M2-ISSUE-0007

- ID: M2-ISSUE-0007
- Stage: Stage 8 repair
- Severity: HIGH
- Status: RESOLVED
- Area: Scoping audit provenance
- Summary: Scoping attempted to pass `model_invocation_id` to `AuditLog`, but
  the SQLModel and database table had no formal field or relationship, allowing
  the provenance fact to be silently discarded.
- Evidence: Before repair, candidate audits could only retain the invocation ID
  inside `after_snapshot`; `AuditLog.model_fields` did not contain
  `model_invocation_id`, and no queryable foreign key connected the audit row to
  `model_invocations`.
- Affected requirement/contract: M2 Scoping provenance and the append-only
  audit chain across Job, ProcessingRun, ModelInvocation, Artifact and AuditLog.
- Impact: A Scoping outcome could not be reliably queried or relationally
  validated against the ModelInvocation that produced it.
- Safe workaround / deferred behavior: None. JSON snapshots remain a sanitized
  summary and are not treated as a substitute for the formal relationship.
- Blocks current subtask: YES at discovery; resolved by this repair.
- Blocks M2 Exit Gate: YES until resolved.
- Suggested repair: Add a nullable indexed AuditLog field with a project-scoped
  foreign key to ModelInvocation, write it for success and failure audits, and
  reject cross-project associations.
- Resolution evidence: Migration `0009_rq_scoping_job` adds
  `model_invocation_id`, `ix_audit_logs_model_invocation_id`, and
  `fk_audit_logs_model_invocation_project` with `ON DELETE RESTRICT`. SQLModel
  metadata matches the new relationship. Focused ModelInvocation, Scoping,
  Research Question and Project database tests report `28 passed`; the full
  database suite reports `168 passed`; the isolated migration runtime test
  reports `1 passed`; Compose reports `240 passed`; and `alembic check` reports
  no drift for this field.

### M2-ISSUE-0004

- ID: M2-ISSUE-0004
- Stage: M2-4
- Severity: MEDIUM
- Status: RESOLVED
- Area: QueryPlan lifecycle and optimistic-lock contract
- Summary: `LITERATURE_AND_EVIDENCE_MODELS` declares required QueryPlan
  `status: Enum`, while `PROJECT_RESEARCH_AND_LITERATURE_API` requires
  `If-Match: "1"`; neither authority defines the status values or the public
  resource revision field.
- Evidence: Repository-wide searches of formal, non-archive product, data-model,
  state-machine and API documents find no QueryPlan status value list and no
  QueryPlan `lock_version`/revision definition.
- Affected requirement/contract: QueryPlan persistence and PATCH concurrency
  contract.
- Impact: Implementing a multi-state lifecycle or naming a revision field
  beyond the demonstrated token would invent contract semantics.
- Safe workaround / deferred behavior: M2-4 exposes only the conservative
  editable `DRAFT` state and reuses the accepted M1 `lock_version` pattern for
  `If-Match`. No confirmation, activation, invalidation or retrieval state is
  inferred. Unknown future states remain unsupported.
- Blocks current subtask: NO; create/read/update/generate are safe within the
  DRAFT-only boundary and all relevant tests pass.
- Blocks M2 Exit Gate: YES; the formal model/API documents should be amended or
  the conservative implementation explicitly approved before final M2 PASS.
- Suggested repair: Define the QueryPlan lifecycle values, transition rules,
  public revision field and ETag/If-Match semantics in the formal model and API
  child contracts, then align migration and OpenAPI if required.
- Resolution evidence: The approved data-model and API contracts now define
  M2 `QueryPlanStatus` as DRAFT-only, expose `lock_version`, require matching
  `If-Match`, increment the version after successful updates, restrict AI
  generation to DRAFT and fail closed for unknown states. API tests cover
  missing, malformed and stale preconditions; the full database suite and
  Compose acceptance pass.

### M2-ISSUE-0005

- ID: M2-ISSUE-0005
- Stage: M2-6
- Severity: MEDIUM
- Status: RESOLVED
- Area: Literature search run, candidate, cache, and degraded response contract
- Summary: The formal product and API documents require search candidates to
  remain separate from formal `LiteratureRecord` rows and require cached or
  degraded results to be visibly marked, but they do not define the complete
  `LiteratureSearchRun.status` values, candidate response fields, cache
  freshness fields, or degraded response shape.
- Evidence: Repository-wide searches of the formal non-archive Literature
  product, data-model, state-machine, API and M2 milestone documents define the
  separation and safety behavior but provide no complete field list or status
  transition table for search runs and candidates.
- Affected requirement/contract: Literature search persistence, result listing,
  cache provenance, degraded behavior, and generated OpenAPI responses.
- Impact: Inventing a new lifecycle Enum or treating cache metadata as a formal
  scientific state would create unsupported contract semantics.
- Safe workaround / deferred behavior: M2-6 reuses the existing `JobStatus`
  lifecycle, keeps candidate/cache fields internal and minimal, preserves the
  original `fetched_at`, and explicitly returns `cache_hit`, `cache_stale`,
  `degraded`, `limitations`, and Provider `error_code`. Unknown states fail
  closed; Provider failure without a cache creates zero candidates and records.
- Blocks current subtask: NO; the conservative boundary is deterministic,
  project-scoped, tested, and does not fabricate literature.
- Blocks M2 Exit Gate: YES; the formal child contracts should define or approve
  the response fields and lifecycle before final M2 PASS.
- Suggested repair: Define the SearchRun lifecycle, public candidate fields,
  cache freshness semantics, degraded/error fields, pagination and filtering in
  the formal Literature model and API child contracts, then align OpenAPI and
  migrations if required.
- Resolution evidence: The approved data-model and API contracts now define
  SearchRun status as the server-owned `JobStatus`, the required cache,
  degraded, limitation, Provider error and fetched-at facts, and the public
  candidate fields. They preserve Candidate/LiteratureRecord separation and
  explicitly prohibit records on Provider failure without cache. Server-owned
  `allowed_actions` now project role- and state-safe search/import/DOI/upload
  capabilities, including no import action for an already imported candidate
  and no upload action for an already bound record. Zero-fabrication tests
  verify that Provider failure without usable cache creates neither candidates
  nor formal LiteratureRecords. Generated OpenAPI, backend tests, frontend
  contract tests and Compose acceptance pass.

### M2-ISSUE-0006

- ID: M2-ISSUE-0006
- Stage: M2-7
- Severity: MEDIUM
- Status: RESOLVED
- Area: Document parse lifecycle contract
- Summary: The formal Document model requires `parse_status`, but the product,
  data-model, state-machine, API and M2 milestone authorities do not define its
  Enum values or lifecycle transitions.
- Evidence: Repository-wide searches of the formal non-archive Document and
  Literature authorities identify the field and parser values but no complete
  parse-status value list or transition table.
- Affected requirement/contract: Document persistence, upload response,
  subsequent M2-8 parser execution and generated OpenAPI response fields.
- Impact: Creating a second parse lifecycle or declaring an uploaded PDF parsed
  would invent scientific-processing semantics and could expose unsafe success.
- Safe workaround / deferred behavior: M2-7 reuses the existing `JobStatus`
  vocabulary and creates uploaded Documents in `DRAFT` with parser `NONE`, no
  page count and no parse Job. Unknown future states remain unsupported; scanned
  detection is explicitly conservative and does not imply OCR or parse success.
- Blocks current subtask: NO; upload, Artifact binding, optional LiteratureRecord
  association and project isolation are independent of parse execution.
- Blocks M2 Exit Gate: YES; the formal child contracts should define or approve
  the Document parse lifecycle before final M2 PASS.
- Suggested repair: Define parse-status values, transition ownership, Job and
  parser mappings, retry/failure semantics and public response behavior in the
  formal model, state-machine and API child contracts, then align M2-8.
- Resolution evidence: The approved data-model and API contracts now define the
  full M2 `Document.parse_status` mapping to `JobStatus`, upload as DRAFT/NONE,
  pypdf fallback as degraded LOW confidence and unknown-state fail-closed
  behavior. A dedicated no-fallback regression verifies that GROBID failure
  with `allow_fallback=false` does not call pypdf, create pages, write degraded
  success, or claim a parser. Existing upload and parse workflow tests,
  generated OpenAPI, frontend contract tests and Compose acceptance pass.

### M2-ISSUE-0008

- ID: M2-ISSUE-0008
- Stage: Stage 8 repair
- Severity: LOW
- Status: OPEN
- Area: Node development dependency security
- Summary: `bun audit` reports the LOW `GHSA-4x5r-pxfx-6jf8` advisory for
  `@babel/core <=7.29.0`, introduced through `@tanstack/router-plugin`.
- Evidence: The Stage 8 standalone and Compose audits both report one LOW
  arbitrary file-read advisory involving a crafted `sourceMappingURL` comment.
- Affected requirement/contract: Frontend build-tool supply-chain maintenance.
- Impact: The affected package is a development/build dependency and does not
  add a known runtime browser vulnerability, but untrusted source inputs must
  not be processed by the build environment.
- Safe workaround / deferred behavior: Build only reviewed repository source in
  the isolated acceptance environment; do not build untrusted third-party
  source trees. Runtime capabilities remain unaffected.
- Responsible owner: Frontend dependency/tooling owner.
- Blocks current subtask: NO; acceptance permits documented LOW advisories.
- Blocks M2 Exit Gate: NO.
- Suggested repair: Upgrade the TanStack router toolchain or its Babel
  dependency when a lockfile-compatible patched release is available, then
  rerun `bun audit`, build and Playwright.
- Resolution evidence: Not resolved.

### M2-ISSUE-0009

- ID: M2-ISSUE-0009
- Stage: Stage 8 repair / M2-11
- Severity: LOW
- Status: RESOLVED
- Area: Backend test dependency compatibility
- Summary: Backend tests emit a Starlette deprecation warning that the current
  `httpx` TestClient integration should move to `httpx2`.
- Evidence: Before repair, focused and full suites consistently emitted the
  Starlette warning because only legacy `httpx` was installed for TestClient.
- Affected requirement/contract: Future backend test-runner compatibility.
- Impact: A future Starlette release could remove the compatibility fallback and
  break the test client.
- Safe workaround / deferred behavior: None required after repair; production
  `httpx` remains available for application adapters while tests use `httpx2`.
- Responsible owner: Backend dependency/test-infrastructure owner.
- Blocks current subtask: NO.
- Blocks M2 Exit Gate: NO after resolution.
- Suggested repair: Evaluate the supported Starlette/httpx2 migration in a
  dependency maintenance task and rerun the complete backend suite.
- Resolution evidence: `httpx2==2.9.1` is in the backend dev dependency group
  and `uv.lock` includes `httpx2`, `httpcore2` and `truststore`. A transient
  compatibility probe passed before locking. Rebuilt clean-room database tests
  report `247 passed, 2 skipped` with only the expected read-only pytest-cache
  warning and no Starlette TestClient deprecation; no-database tests report
  `73 passed, 2 skipped` without that warning.

### M2-ISSUE-0010

- ID: M2-ISSUE-0010
- Stage: M2-9
- Severity: HIGH
- Status: RESOLVED
- Area: Frontend activation contract and Open Design integration
- Summary: Open Design-owned QueryPlan, Literature, and Document workspaces are
  connected to their frozen containers and registered as production routes.
  Stage 9 has now recorded the complete deterministic production vertical and
  full regression evidence.
- Evidence: The production routes
  `projects.$projectId_.query-plans.$queryPlanId`,
  `projects.$projectId_.literature`, and
  `projects.$projectId_.documents.$documentId` inject the Open Design
  workspaces. Deep-link, refresh, permission, pending, conflict, retry, upload,
  parse, and fail-closed browser coverage passes together with the unified typed
  fixture Preview and ownership/mock guards.
- Affected requirement/contract: M2-9 ownership boundary, Props-in/Events-out,
  unknown-state safety, production route activation and independent Open Design
  integration.
- Impact: Frontend activation is no longer an Exit Gate blocker.
- Safe workaround / deferred behavior: Production routes remain enabled with
  server-projected permissions, route identity checks, exact cache invalidation,
  and unknown-state fail-closed guards. QueryPlan create remains disabled because
  no formal create capability is projected to the detail workspace.
- Blocks current subtask: NO.
- Blocks M2 Exit Gate: NO after resolution.
- Suggested repair: COMPLETED in Stage 9 through deterministic production
  vertical acceptance, full regression, clean-room, and Exit report refresh.
- Resolution evidence: Server-projected actions, generated OpenAPI/client and
  fail-closed Codex integration contracts are complete and pass frontend and
  Compose gates. The QueryPlan, Literature and Document ViewModel, Loadable,
  Props, Events, typed fixture, container injection, route/ID and unknown-state
  handoff is frozen in `M2_FRONTEND_FEATURE_TEMPLATE.md`. QueryPlan creation
  remains inactive without a formal capability. Literature retry is active only
  when the matching Job is formally retryable and project `job.retry` is known.
  Stage 9 production browser acceptance crossed production Routes, generated
  client/adapter, real API, PostgreSQL, MinIO, Job/Worker handlers, refresh
  recovery, and DocumentPage text. Full frontend Playwright passed 114/114 and
  the isolated clean-room Playwright gate passed 114/114.

### M2-ISSUE-0011

- ID: M2-ISSUE-0011
- Stage: M2-10
- Severity: HIGH
- Status: RESOLVED
- Area: GROBID Compose healthcheck
- Summary: The Compose healthcheck used `curl`, which is absent from the pinned
  GROBID image, so a listening and usable GROBID service was reported unhealthy.
- Evidence: Container health logs reported `/bin/sh: curl: not found` while
  Jetty was listening on port 8070. A direct Live adapter parse of a generated
  PDF returned TEI and a GROBID version.
- Affected requirement/contract: M2-8 and M2-10 GROBID runtime readiness,
  Compose orchestration, Worker parsing, and real-service smoke evidence.
- Impact: The false unhealthy state could block dependent service startup and
  make a working parser appear unavailable during acceptance or development.
- Safe workaround / deferred behavior: Direct adapter smoke established parser
  availability while the health probe was repaired. No parser success was
  inferred from health status alone.
- Blocks current subtask: YES at discovery; resolved before M2-10 completion.
- Blocks M2 Exit Gate: YES until resolved.
- Suggested repair: Use a probe supported by the pinned image and continue to
  keep real PDF parsing as separate functional evidence.
- Resolution evidence: `docker-compose.yml` now uses
  `bash -ec 'exec 3<>/dev/tcp/127.0.0.1/8070'`. After forced recreation the
  GROBID container reached `healthy`, and the opt-in Live GROBID test parsed a
  real generated PDF successfully.
