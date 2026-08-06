# M7 Implementation Plan

Date: 2026-08-06
Stage: 5
Status: M7 EXIT APPROVED; M8 ENTRY ALLOWED

## Recovery Baseline

| Fact | Observed value |
| --- | --- |
| Branch | `feat/m2-research-literature` |
| HEAD | `951d872aa3567c2393e5ae7cad2b1900b55999d4` |
| Upstream | `origin/feat/m2-research-literature` |
| Entry worktree | Clean, no untracked files before M7 Stage 0 |
| Migration head | single head `0017_m6_manuscripts` |
| M7 Entry | `ALLOWED` by M6 Completion, Exit Gate and To-M7 Handoff |
| Retained limitation | Windows host-only PostgreSQL runner is unreliable; Compose-network migration verification is authoritative |
| No authorization | No commit, tag, push, stash, reset, clean or destructive checkout |

Current Stage-0 changes are limited to the React Flow dependency/lock, explicit Spike tests,
third-party metadata, and the two M7 acceptance documents. No prior user or Open Design
modification was present in this worktree. Separate Open Design worktrees were not merged.

## Snapshot Differences And Decisions

1. The milestone says M7 migration status `COMPLETE`, but repository fact is a single `0017`
   head and no M7 tables. Treat it as documentation metadata; Stage 1 owns additive `0018`.
2. The milestone lists `audit_results` under M7, but M6 `0017` already owns the table. Stage 1
   extends it compatibly and never recreates it.
3. The full data model uses relation `PRODUCED_BY`; the roadmap summary says `PRODUCED`.
   Canonical persisted/API enum is `PRODUCED_BY`; the summary alias is rejected.
4. Existing `AuditResult.status` is execution state, while the full model uses status for audit
   outcome. Retain execution status and add separate nullable `outcome`.
5. Current AuditResult requires M6 before/after versions. Make these nullable only for non-revision
   audits, add target/source snapshots, and enforce type-dependent database CHECKs.
6. React 19.2.7, Vite 8.1.5 and TypeScript 5.9.3 are newer than the research snapshot. Browser
   Spike passed with exact `@xyflow/react` 12.11.2; no layout library is added.
7. Default host Python is 3.13 while the project requires 3.14. Stage-0 ZIP tests used the repo
   venv. This is `M7-ISSUE-0001` and does not alter contracts.

## Scope Freeze

### Competition Core / P0-Must

- Same-project Claim-to-evidence links with explicit resolvers and fail-closed validation.
- Authorized graph projection, completeness checklist, deterministic Claim audit and invalidation
  propagation with retained history.
- Deterministic export readiness, version-bound Approval, immutable ReproPackage, canonical
  Manifest, safe deterministic ZIP, verified Artifact and download.
- Single later production route: `/projects/$projectId/evidence`.

### P0-Full

- Model-assisted explanation of evidence strength, limitations and semantic drift after the
  deterministic result exists. Provider degradation remains visible.
- Broader audit interpretation and presentation refinements that do not change graph truth,
  completeness, readiness, Approval or hashes.

### Explicitly Not Done

- Neo4j, generic knowledge graph, citation network, blockchain or client graph authority.
- Automatic layout dependency by default; backend lane/rank hints are sufficient initially.
- Re-distribution of prohibited PDFs/data, default sensitive inclusion, or fabricated Agent logs.
- M8 Agent runtime/tools and M9 demo exceptions.

## Planned File Map

| Area | Planned location |
| --- | --- |
| Models/enums | `backend/app/models.py` |
| Migration | `backend/app/alembic/versions/0018_m7_evidence_export.py` |
| Link/graph schemas | `backend/app/evidence_graph/schemas.py` |
| Resolver registry | `backend/app/evidence_graph/resolvers.py` |
| Link service | `backend/app/evidence_graph/service.py` |
| Graph projector | `backend/app/evidence_graph/projector.py` |
| Completeness | `backend/app/evidence_graph/completeness.py` |
| Auditors | `backend/app/evidence_graph/auditors.py` |
| Invalidation | `backend/app/evidence_graph/invalidation.py` |
| Graph/API router | `backend/app/api/routes/evidence_graph.py` |
| Export schemas/service | `backend/app/exports/schemas.py`, `service.py` |
| Readiness/collector | `backend/app/exports/readiness.py`, `collector.py` |
| Manifest/ZIP | `backend/app/exports/manifest.py`, `packager.py` |
| Worker handlers | existing `backend/app/workers/jobs.py` registry plus domain handlers |
| Golden fixtures | `backend/tests/golden/m7_evidence_export/v1/` |
| Frontend feature | `frontend/src/features/evidence-workspace/` |
| Production route | `frontend/src/routes/_layout/projects.$projectId_.evidence.tsx` |

Stage 0 does not create any planned production path above.

## ClaimEvidenceLink Contract

- Evidence types: `LITERATURE_RECORD`, `EVIDENCE_SPAN`, `DATASET_VERSION`,
  `DATA_TRANSFORMATION`, `ANALYSIS_PLAN`, `ANALYSIS_RUN`, `ANALYSIS_RESULT`, `FIGURE`,
  `MANUSCRIPT_VERSION`, `APPROVAL`, `AUDIT_RESULT`.
- Relations: `SUPPORTED_BY`, `CONTRADICTED_BY`, `DERIVED_FROM`, `TRANSFORMED_FROM`,
  `ANALYZED_BY`, `PRODUCED_BY`, `VISUALIZED_AS`, `CONFIRMED_BY`, `AUDITED_BY`,
  `INVALIDATED_BY`.
- Strength: `STRONG`, `MODERATE`, `WEAK`, `UNKNOWN`.
- Status: `SUGGESTED`, `ACTIVE`, `REJECTED`, `INVALIDATED`.
- AI/model provenance may only create `SUGGESTED`. `ACTIVE` requires an allowed user command
  and Service revalidation. Invalidated links remain append-only history.
- Canonical identity is project + claim + evidence type/id + relation. Active duplicates do not
  form parallel edges. Idempotency is project-scoped.
- Composite project foreign keys, `lock_version >= 1`, 64-hex source hashes, timestamps and
  status-dependent confirmation/invalidation CHECKs are required.
- Claim-to-source relations use support/contradict/derive/audit/confirm. Domain lineage edges
  are projected from formal FKs and are not stored as ClaimEvidenceLink.

## Evidence Resolver Freeze

Each type has an explicit resolver reading a fixed model/table and returning a minimal authorized
`EvidenceReference`: project, type/id, raw/known status, immutable version/hash, stale/invalidated,
safe label/detail intent, restrictions and allowed actions.

| Type | Required authority checks |
| --- | --- |
| LiteratureRecord | project, decision/state, source identity, restrictions |
| EvidenceSpan | parent record/document, locator/version, span hash, valid source |
| DatasetVersion | immutable version/Artifact, availability, sensitivity/license |
| DataTransformation | input/output versions, approval and completion state |
| Analysis Plan/Run/Result | completed state, input versions and result hash |
| Figure | immutable figure/version, source result and Artifact hash |
| ManuscriptVersion | immutable version/Artifact hash and invalidation state |
| Approval | type, decision, target/snapshot/hash, expiry/staleness |
| AuditResult | execution/outcome, target/source snapshots and invalidation |

Unknown types/statuses, hash mismatch, denied scope, cross-project or invalidated sources fail
closed. Client table, project, status, hash and detail URL are never trusted.

## Graph Projection Freeze

- Query supports project root, depth, node type/risk/invalidated filters, opaque cursor and limit.
  Default depth 2, max depth 4, default 200 nodes, hard max 500 nodes.
- Nodes expose stable `type:id`, raw status, `known_status`, risk, stale/invalidated, source kind,
  safe label, detail intent, limitations and server allowed actions.
- Edges expose stable origin-qualified ID, relation, stored/derived kind, raw/known status, risk
  and invalidation. Stable sort is type, object ID, relation and edge ID.
- Stored edges come only from ClaimEvidenceLink. Derived edges come from approved domain FKs,
  ArtifactRelation and Approval/Audit target snapshots.
- Denied objects are omitted without count/name leakage. A generic scope limitation may indicate
  partial projection without identifying hidden objects.
- Limits return `partial=true`, `next_cursor` and limitations; truncation is never complete.
- `lane`/`rank` hints are presentation only. React Flow position, drag, connect and `toObject()`
  never become scientific relationships.

## Completeness Freeze

Server checklist v1 covers Claim source, located original evidence when applicable, current
dataset version, completed analysis result, figure lineage, required confirmation and current
audit. States: `SATISFIED`, `MISSING`, `STALE`, `RESTRICTED`, `CONFLICTED`,
`NOT_APPLICABLE`, `UNKNOWN`. It is not a scientific quality score. Restricted/unknown never
become missing proof or satisfied. Output includes rule version, scope, limitations and actions.

## Audit Compatibility Freeze

- Execution status remains `QUEUED`, `RUNNING`, `COMPLETED`, `FAILED`, `CANCELLED`.
- Outcome is separate: `VERIFIED`, `NEEDS_REVIEW`, `INSUFFICIENT_EVIDENCE`,
  `SOURCE_INCOMPLETE`, `CONFLICTED`, `DATA_MISMATCH`, `FIGURE_MISMATCH`,
  `OVERCLAIM_RISK`, `REJECTED_BY_USER`, `INVALIDATED`.
- M6 `REVISION_DRIFT_AUDIT` retains before/after version IDs/hashes and existing findings.
- Other audit types require target type/id and canonical source snapshot/hash, without a false
  manuscript version pair.
- Competition Core includes the eight model finding codes plus invalidated source, unknown status
  and evidence hash mismatch codes.
- AI can explain but cannot change deterministic outcome, confirm Claims, create active links or
  modify completeness. Provider failure is explicit degradation.

## Invalidation Freeze

LiteratureRecord, EvidenceSpan, DatasetVersion, AnalysisResult, Figure, Approval, AuditResult,
ManuscriptVersion and Claim invalidation call a shared hook. It re-queries facts, invalidates
affected active links, moves Claims to review-required state, records source type/id/version/hash,
path, reason, rule version/time, and appends AuditLog. It never deletes history or modifies prior
packages. Replays are idempotent. Reconciliation rebuilds from database facts, ignores event
actor/project/hash claims, bounds cycles/depth, and fails closed on unknown relations.

## Export And Approval Freeze

- Export states: `DRAFT -> VALIDATING -> NEEDS_CONFIRMATION|QUEUED -> PACKAGING -> COMPLETED`,
  with terminal `FAILED`/`CANCELLED`. Job accepted, Packaging, Artifact AVAILABLE, Export
  COMPLETED and package download remain different facts.
- Scope is canonical JSON with lock version, readiness audit/snapshot/hash, object versions,
  include decisions and policy/schema versions. Same Idempotency-Key returns the same Export.
- `EXPORT_CONFIRMATION` binds exact scope/readiness/item hashes. Stale/expired/rejected Approval
  or changed source/hash fails closed. Approval cannot override prohibited redistribution.
- Prohibited => metadata/reference only; restricted => metadata-only unless policy permits;
  sensitive => excluded by default and requires scope plus formal Approval; missing/invalidated/
  unconfirmed/unknown => blocker or explicit exclusion, never silent inclusion.
- ExportItem statuses are `INCLUDED`, `EXCLUDED`, `METADATA_ONLY`, `REFERENCE_ONLY`, `BLOCKED`,
  `MISSING`, with reason, unique canonical path, source version/hash and restriction metadata.

## Manifest, README And ZIP Freeze

- ReproPackage has monotonic package version, ZIP Artifact, Manifest Artifact, canonical package
  hash and immutable history. Finalize only after staging bytes/hash verification in one DB
  transaction. Failure cleans/quarantines staging and exposes no AVAILABLE package.
- Manifest `reca.repro-manifest.v1` is UTF-8 canonical JSON with sorted keys and compact separators.
  It records every file path/size/SHA-256/type/source/license/sensitive/redistribution state plus
  actual lock, runtime, image digest, adopted upstream/vendor, prompt, rule, engine, citation,
  config and source versions. Research-only projects are not adoption metadata.
- `manifest.json` cannot contain its own SHA-256 without a self-referential fixed point. The
  Manifest `files` array covers every other ZIP member; Manifest integrity is authoritative
  through the separate immutable `ArtifactType.MANIFEST` row and its verified object hash.
- README is generated only from actual members and approved deterministic analysis entry points,
  data acquisition instructions, hash checks, privacy/license limits and missing items.
  Metadata-only/excluded inputs explicitly say full offline rerun is unavailable.
- Agent logs are `NOT_AVAILABLE` before M8; no fabricated AgentRun is created.
- ZIP paths are normalized POSIX relative names. Reject empty/absolute/drive/backslash/NUL/`..`,
  duplicates, case collisions, depth excess, symlinks/devices and resource excess. Sort entries,
  fix timestamp/mode, reopen, and verify each member against the Manifest.

## Permissions Freeze

| Capability | Viewer | Reviewer | Editor | Owner |
| --- | --- | --- | --- | --- |
| evidence/audit/export read | scoped | yes | yes | yes |
| link create | no | suggestion/review only | yes | yes |
| link confirm/invalidate | no | when allowed | yes | yes |
| audit run | no | yes | yes | yes |
| export readiness | scoped | yes | yes | yes |
| export create/confirm | no | no unless contract grants | yes | yes |
| package download | scoped permission plus verified AVAILABLE Artifact for all roles |

Unknown permissions or a missing allowed action fail closed.

## Frontend/Open Design Ownership Freeze

- Later route: `/projects/$projectId/evidence`; deep links: `claim`, `node`, `link`, `audit`,
  `export`, `package`, `view=graph|claims|audits|exports`.
- Codex owns backend/OpenAPI/generated/adapter/model/mapper/query/mutation/container/route and
  typed fixtures. Open Design owns pure presentation only after Stage 3 readiness.
- ViewModel separates stored/derived edges, raw/known status, permissions, completeness,
  execution/outcome, readiness/Approval/Job/package and partial/degraded states.
- UI events express intent. Mutation success uses server response plus refetch. React Flow connect
  is disabled; formal links use a controlled form/event.
- Fixtures cover empty through 500-node partial graphs, all statuses, denial/unknown, readiness,
  export/package histories, long content, themes and viewports. Readiness requires executable
  types/fixtures and boundary guards, not Markdown alone.

## Stage Dependency And Verification Plan

```text
Stage 0 contracts/dependency Spikes
  -> Stage 1 models + 0018 + resolvers + links + graph + audit + invalidation
  -> Stage 2 readiness + approval + collector + manifest + ZIP + Worker + download
  -> Stage 3 OpenAPI/generated/adapter/ViewModel/fixtures/Open Design handoff
  -> Open Design pure UI acceptance
  -> Stage 4 production route + real API/Worker/MinIO/browser vertical chain
  -> Stage 5 issue closure + full M7 Exit Gate + M8 handoff
```

- Stage 1: model/migration, resolver matrix, link state/idempotency, graph authorization/cursor,
  completeness, audit compatibility and propagation.
- Stage 2: readiness matrix, Approval staleness, export state/concurrency, Manifest/ZIP, MinIO
  atomicity/tamper, download authorization and restricted-data README.
- Stage 3: OpenAPI/generated, adapter/mapper types, fixtures and boundary guards.
- Stage 4: real PostgreSQL/Worker/MinIO/browser longitudinal flow and negatives.
- Stage 5: full backend/PostgreSQL/migration/Worker/MinIO/frontend/Playwright/clean-room,
  security and supply-chain gates. Exit requires one `0018` head and no M8 implementation.

M8 handoff exposes read-only Graph/Claim/Audit/Export DTOs, permissions and allowed actions.
Every future Tool revalidates project, membership, scope, source, status, Approval and hashes.
Stage 0 implements no Tool.

## Stage-0 Spike Evidence

- Exact `@xyflow/react` 12.11.2 is locked and recorded in Notices.
- Vite/Chromium rendered 500 custom nodes and 499 bounded edges; keyboard/narrow viewport checks
  passed; no connectable handles were exposed. No automatic layout package was needed.
- Layout decision: use server lane/rank hints first; reconsider Dagre/ELK only with measured graph
  shapes and a separate license/performance Spike.
- ZIP Spike produced identical bytes/hash on repeat builds, stable paths/order, fixed timestamp and
  regular-file mode, canonical Manifest/README, metadata-only restricted content, reopen checks
  and ZIP Slip negatives.
- Spike files live only under `frontend/tests/spikes` and `backend/tests/spikes`.

## Stage-0 Focused Verification

- React Flow Playwright Spike: 2 passed.
- ZIP/Manifest pytest Spike: 5 passed.
- Frontend TypeScript/Vite production build: passed, 2351 modules transformed.
- Frontend Biome format check: passed, 277 files checked.
- Focused Ruff check/format: passed.
- Alembic heads: `0017_m6_manuscripts (head)` only.
- `git diff --check`: passed; CRLF conversion warnings only for existing repository line-ending policy.

Stage 0 implements no formal M7 endpoint, migration, Worker, export path or production workspace.

## Stage-1 Implementation Result

Implemented the additive `0018_m7_evidence_export` migration on the single `0017` parent. It
creates `claim_evidence_links` and the frozen Stage-2 export structures, extends the existing
`audit_results`, separates execution status from outcome, preserves the strict revision-audit
shape, and adds project, hash, state, path, uniqueness and history constraints. Export write
paths remain absent.

Implemented explicit resolvers for every frozen evidence type; ClaimEvidenceLink create/list/
transition services with relation/type allowlists, project authorization, source/hash/status
revalidation, suggestion-only Reviewer behavior, idempotency, If-Match, retained invalidation and
AuditLog; authoritative graph projection with stored and formal-FK edges, stable IDs/order,
authorization omission, filters, cursor/partial signaling and server layout hints; and the
non-scoring completeness checklist.

Implemented deterministic asynchronous Claim audit using the existing Job/ProcessingRun/Worker
registry. The Worker re-fetches actor, project, Claim, links and sources, writes generalized
AuditResult findings/outcome/limitations/hashes, exposes explicit AI degradation without changing
the deterministic outcome, and never confirms a Claim or creates an ACTIVE edge. M6 revision
audit now also fills generalized outcome/findings/limitations while retaining before/after fields.

Implemented shared invalidation propagation and database reconciliation. Existing DatasetVersion
and AnalysisRun invalidation paths invoke it for directly affected DatasetVersion, AnalysisRun,
AnalysisResult and Figure evidence; links and Claims retain history and AuditLog paths. Current
Literature/Evidence/Manuscript/Claim modules do not expose separate general invalidation commands,
so no artificial endpoint was added; reconciliation covers stale/hash/unknown/unresolvable links
until a future authoritative invalidation entry point calls the same hook.

### Stage-1 Actual Files

- Models/migration: `backend/app/models.py`, `backend/app/alembic/versions/0018_m7_evidence_export.py`.
- Evidence backend: `backend/app/evidence_graph/` and `backend/app/api/routes/evidence_graph.py`.
- Integration: project permissions, API router, Worker registry, M6 revision audit, DatasetVersion
  and AnalysisRun invalidation services.
- Focused tests: `backend/tests/evidence_graph/` and the M7 single-head migration assertion.

### Stage-1 Focused Verification

- Ruff check and format for all affected Stage-1 files: passed.
- `ty check` for evidence_graph, route, Worker and M6 revision-audit integration: passed.
- Stage-1 contract/invalidation plus affected M6 revision rules: 10 passed, 19 deselected.
- Alembic offline PostgreSQL SQL generation from base through `0018`: passed.
- Alembic graph: one head `0018_m7_evidence_export`, directly after `0017_m6_manuscripts`.
- Application imports, Worker registration and API router/OpenAPI construction: passed.
- `git diff --check`: passed; repository CRLF conversion warnings only.
- Compose/PostgreSQL fresh upgrade, repeated upgrade and `alembic check`: not run because the
  Docker Desktop Linux daemon was unavailable; tracked as `M7-ISSUE-0002`.

## Stage-2 Implementation Result

Implemented deterministic `EXPORT_READINESS_AUDIT`, project-scoped candidate enumeration,
license/sensitive/restriction downgrade policy, immutable readiness and candidate hashes, and
formal `EXPORT_CONFIRMATION` payload binding. Viewer/Reviewer can read/check/download but cannot
create or confirm; Editor/Owner can create and confirm. Approval decisions use a domain-specific
permission and a post-commit Job dispatch callback so the Approval, Export, Job, audit and
idempotency state commit before queue visibility.

Implemented Export create/detail, ReproPackage detail/download APIs and the existing Job/Worker
integration for `REPRO_PACKAGE_EXPORT`. The Worker re-queries project membership, requester,
approver, Approval snapshot, source status/hash/scope and candidate policy before packaging.
Failure marks Export failed and removes or quarantines uploaded objects; completed package,
Manifest and ExportItem history is append-only.

Implemented the package collector, canonical Manifest, truthful `README_REPRODUCE`, stable ZIP
path/order/timestamp/mode, member/count/size/depth/compression limits, reopen verification and
Artifact download/hash verification. Unknown/restricted PDFs and datasets are metadata-only,
sensitive content is excluded by default, unverified model output is metadata-only, and M8 Agent
logs are explicitly `NOT_AVAILABLE`.

### Stage-2 Actual Files

- Export backend: `backend/app/exports/`, `backend/app/api/routes/exports.py`.
- Integration: project permissions, Approval post-commit handler, API router/error envelope,
  Worker registry, Settings limits, and the Stage-1 ExportItem composite-FK model correction.
- Focused tests: `backend/tests/exports/` plus the retained ZIP/Manifest Spike.

### Stage-2 Focused Verification

- Ruff and `ty` for Stage-2 backend/routes/tests: passed after focused fixes.
- Stage-2 no-database policy/ZIP/Manifest/model/OpenAPI/Worker tests: 22 passed; 8 database tests
  deselected by the explicit `no_database` filter.
- Alembic offline PostgreSQL SQL generation: passed; one `0018_m7_evidence_export` head after
  `0017_m6_manuscripts`.
- Static migration head test and storage adapter test: 2 passed.
- Database-backed Export service test attempted but timed out waiting for PostgreSQL. Docker
  Desktop Linux daemon and real MinIO/Worker verification remain unavailable and are tracked as
  `M7-ISSUE-0002` and `M7-ISSUE-0003`.

Stage 3 begins only after this recorded backend contract baseline. No frontend visual Workspace,
M8 Agent, production Route integration or final Exit Gate was implemented in Stage 2.

`STAGE_RESULT=PASS_WITH_ISSUES`

`NEXT_STAGE_EXECUTED=NO`

## Stage-3 Implementation Result

Hardened the M7 OpenAPI response contracts and added read endpoints for generalized AuditResult
and individual ClaimEvidenceLink. Re-exported `frontend/openapi.json` and regenerated the client;
generated files were not manually edited. The adapter now exposes one EvidenceGraph and one Export
surface for Graph, links, Claim Audit, readiness, Export, package and download operations.

Created the RECA-owned `evidence-workspace` business contract: model, mapper, route/search draft,
queries, mutations, injected Container, UI Props/Events and typed fixtures. Backend DTOs are mapped
before React Flow-friendly props; connect/reconnect are disabled, unknown enums and permissions fail
closed, denied evidence produces anonymous scope notices, completeness is categorical/non-scoring,
and Audit execution/outcome and readiness/Export/Approval/Job/package facts remain distinct.

Deep-link resources are individually fetched and revalidated for project and relationship
consistency. Inaccessible or mismatched selections fall back to the authorized default graph
without existence disclosure. The production `/projects/$projectId/evidence` Route remains
unregistered as required. Server mutations use Idempotency-Key/If-Match through the adapter and
invalidate/refetch; the deterministic readiness response is retained in query state after refetch
because no standalone readiness GET exists.

Added more than 60 typed fixture states and an executable seven-test/104-assertion semantic guard,
including a representative 500-node partial graph, non-connectable canvas, permissions/unknown/
no-disclosure, completeness, Audit degradation, readiness/Approval/Export/package/Manifest,
transport, viewport and theme boundaries. Created `M7_OPEN_DESIGN_HANDOFF.md` with frozen ownership,
accessibility, responsive, Preview and READY gates.

### Stage-3 Actual Files

- OpenAPI/backend contract: `backend/app/api/routes/evidence_graph.py`,
  `backend/app/api/routes/exports.py`, `backend/app/main.py`, `frontend/openapi.json` and generated
  client output.
- Frontend integration contract: `frontend/src/api/adapter/index.ts` and
  `frontend/src/features/evidence-workspace/` excluding any final visual Workspace.
- Contract verification: `frontend/scripts/check-m7-fixtures.test.ts` and the existing generated,
  UI-boundary and production-mock guards.
- Handoff: `docs/acceptance/M7_OPEN_DESIGN_HANDOFF.md`.

### Stage-3 Focused Verification

- Required M7 OpenAPI paths: 10 present; generated client consistency passed.
- Frontend Biome lint and format check, TypeScript/Vite production build: passed.
- M7 fixture semantic guard: 7 passed, 104 assertions; 60+ fixtures.
- UI ownership boundary: 4 tests plus repository scan passed.
- Production mock boundary: 6 tests plus repository scan passed.
- Backend Ruff check/format and `ty` for evidence/export routes, services and tests: passed.
- Stage-1/2 no-database evidence/export/ZIP focused suite: 30 passed, 8 database tests deselected.
- Alembic graph: one `0018_m7_evidence_export` head. `git diff --check`: passed.
- PostgreSQL/Worker/MinIO and production browser E2E remain pending under M7 issues 0002/0003.

Stage 3 did not execute Open Design, register the production Route, run Stage 4/browser E2E, run
the full Exit Gate or implement M8 Agent behavior.

`STAGE_RESULT=PASS_WITH_ISSUES`

`READY_FOR_OPEN_DESIGN=YES`

`NEXT_STAGE_EXECUTED=NO`

## Stage-4 Entry Audit And Recovery Plan

Execution-time facts superseded the Stage-3 Codex handoff snapshot: Open Design delivered the pure
UI and acceptance evidence, but its formal acceptance and handoff both state
The original Open Design `READY` decision was `NO`. The visual matrix passed; four Codex-owned gaps remained in Audit
Job projection, immutable Package history, retry/cancel fixtures and Link confirm capability.
This difference is tracked as `M7-ISSUE-0004`.

Stage 4 followed the documented non-READY continuation path: repair those typed contracts and
fixtures, register the single production Route, complete deep-link/mutation/test infrastructure,
and run focused checks that do not require claiming accepted visual integration. The accepted
Workspace and CSS were retained; only the minimum local UI correction needed to consume the new
read-only Audit Job and Package history projections was made.

### Stage-4 Implementation Result

- Added a read-only Audit-to-Job projection without exposing Audit retry/cancel through the Export
  Job controls.
- Added authorized, paginated immutable ReproPackage history and mapped it through generated
  client, adapter, query, ViewModel, typed fixtures and the existing UI.
- Added executable fail-closed fixtures for Link confirmation, retryable failed Export and
  cancellable running Export, with semantic contract assertions.
- Registered `/projects/$projectId/evidence` with claim/node/link/audit/export/package/view search,
  authorized fallback, refresh recovery and server-response-driven mutation navigation.
- Kept React Flow connect persistence disabled and used only the server download URL returned by
  the ReproPackage download response.

### Stage-4 Focused Verification

- Backend evidence/export no-database suite: 30 passed, 3 database tests deselected.
- Backend Ruff and ty for affected evidence/export modules and routes: passed.
- Alembic script graph: single `0018_m7_evidence_export` head.
- Frontend generated check, production-mock guard and UI-boundary guard: passed.
- M7 fixture guard: 8 tests, 125 assertions passed.
- Stage-4 Route contract guard: 2 tests, 13 assertions passed.
- Frontend Biome lint/format and TypeScript/Vite production build: passed.
- Docker Desktop recovery: Compose PostgreSQL, Valkey, MinIO, API, Worker and frontend available.
- Isolated PostgreSQL fresh/repeated upgrade, `alembic check`, single head and focused graph/export
  suite: passed; 33 tests on a unique temporary database.
- Real Worker/MinIO ReproPackage vertical: passed; Export and Job completed, 21 ZIP members and 20
  Manifest payload entries were reopened and hash-verified, then all isolated resources cleaned.
- Focused production Route Playwright: 2 passed with mock API envelopes, covering no-disclosure
  fallback, non-connectable graph projection, table fallback, 390px bounds and keyboard focus.

Real execution found and resolved three local defects: duplicate PostgreSQL enum creation in 0018,
missing adopted lock files in the runtime Worker image, and implicit README integrity/Agent-log
wording. Decisions and evidence are recorded as `M7-ISSUE-0005` through `M7-ISSUE-0007`.

Open Design subsequently revalidated the corrected contracts. The original 372/372 visual matrix,
current 8-test/125-assertion fixture guard and 4/4 corrected-contract browser checks now support
`READY_FOR_CODEX_INTEGRATION=YES`. The complete real-API browser Claim-to-Export chain, Stage 5,
the complete Exit Gate and M8 were not executed.

`STAGE_RESULT=PASS_WITH_ISSUES`

`READY_FOR_CODEX_INTEGRATION=YES`

`NEXT_STAGE_EXECUTED=NO`

## Stage-5 Exit Decision

Stage 5 stopped feature expansion and repaired shared root causes through `M7-ISSUE-0023`. The
final clean-room run at `D:\Temp\User\reca-m0-acceptance-20260806-150804` passed backend,
PostgreSQL, migrations, Worker, MinIO, frontend, Playwright, security and supply-chain checks.
The isolated real-browser chain at `D:\Temp\User\reca-m7-real-browser-20260806-151321` also
passed Claim -> Graph -> Readiness -> Approval -> Job -> ReproPackage -> authorized download.

The complete `ty` command now passes with zero diagnostics after root-cause corrections that
preserve SQLAlchemy timezone behavior and make existing union/configuration/logging boundaries
explicit. No checker weakening or broad ignore was adopted.

`STAGE_RESULT=PASS`

`M7_EXIT=PASS`

`M7_COMPLETION=APPROVED`

`M8_ENTRY=ALLOWED`

`NEXT_STAGE_EXECUTED=NO`
