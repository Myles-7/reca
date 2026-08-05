# M6 Implementation Plan

Date: 2026-08-05
Owner: Codex
Stage: M6 Codex Stage 3.5 complete
Status: READY_FOR_OPEN_DESIGN

## 1. Scope And Authority

This plan freezes the M6 implementation contract. Stage 0 does not create M6 domain
tables, endpoints, production Worker handlers or a production Manuscript Workspace.
Current facts take precedence over the development-prompt snapshot.

Authoritative inputs read for this stage include the repository `AGENTS.md`, M5
completion/exit/handoff reports, the implementation roadmap and M6 milestone, product
chapters 23-24, data-model chapters 18-19, manuscript/issue/claim/approval/job state
machines, manuscript/API/AI contracts, testing and security contracts, ADR-005,
python-docx/CSL/citeproc-js/Zotero source research, Notices, and the current backend,
frontend, migrations and tests.

## 2. Recoverable Baseline

```text
repository=D:/桌面/Recas/reca
branch=feat/m2-research-literature
HEAD=23da58ade9d45ec5584ab48785da5fc59f100f9d
upstream=origin/feat/m2-research-literature
ahead=0
behind=0
initial_worktree=clean
initial_untracked=none
migration_head=0016_m5_figures
migration_heads_count=1
M5_EXIT=PASS
M5_COMPLETION=APPROVED
M6_ENTRY=ALLOWED
```

No user or Open Design changes existed at stage entry. Stage 0 created only dependency,
Spike, Notices and acceptance-planning changes. No commit, tag, stash or push was made.

Environment note: the checked-in `.venv` is a Linux Python 3.14.3 environment and is not
directly executable from Windows PowerShell. The approved Docker API/Worker image was
therefore used for dependency and focused-test evidence.

## 3. Entry And Frozen M5 Inputs

M6 may consume only server-revalidated facts:

- same-project, `COMPLETED`, non-invalidated AnalysisRun;
- immutable AnalysisResult including null, effective N, method, parameters, schema,
  environment/code/input/result hashes and warnings;
- same-project `CONFIRMED`, non-invalidated Figure with no blocking validation issue;
- `AVAILABLE` Artifacts whose stored bytes match SHA-256;
- located, authorized EvidenceSpan and formal LiteratureRecord;
- known read scope, permissions and allowed action.

M6 never recomputes or patches M5 numbers, rerenders Figures, converts null to a number,
or upgrades association to causation. Check, fix, audit, claim confirmation, retry and
download boundaries revalidate project, status, invalidation, scope and hashes.

## 4. Delivery Boundary

### 4.1 Competition Core / P0-Must

- immutable DOCX Artifact and ManuscriptVersion ingestion;
- bounded, non-executing DOCX/OOXML parsing with explicit coverage and limitations;
- bidirectional citation/reference checks and project LiteratureRecord comparison;
- deterministic N, p, r, beta, common numeric and Figure consistency checks against
  formal project facts;
- deterministic high-precision causal keyword, sample-scope, terminology, numbering and
  basic-format findings;
- stable version-bound Issue location and same-project evidence;
- user accept/reject decisions without automatic scientific-content mutation;
- allowlisted low-risk fix plan, preview, approval and atomic derived version;
- read-only `MANUSCRIPT_REVISION_AUDIT` / `REVISION_DRIFT_AUDIT`;
- source-located Claim and `CLAIM_CONFIRMATION` Approval flow.

### 4.2 P0-Full

- model-assisted complex qualifier, scope, consensus and new-Claim suggestions;
- broader citation styles only after per-file rights and processor review;
- wider golden corpora, performance coverage and additional supported OOXML features.

Provider unavailability is a visible degradation and never blocks Competition Core.

### 4.3 Explicitly Out Of M6

ClaimEvidenceLink, EvidenceGraphSnapshot/UI, ReproPackage/Export, Agent/Tool runtime,
public full Citation Processor API, citeproc-js runtime, DOC/DOCM/LaTeX/online Word,
complex tracked-change/formula/text-box/chart rewriting, automatic paper generation,
paraphrasing and plagiarism detection remain out of scope. M7 owns evidence graph,
complete audit consumption, propagation and export.

## 5. Dependency Decision And Spike Evidence

| Item | Frozen decision | Evidence |
| --- | --- | --- |
| Python | 3.14.3 API/Worker image | existing Dockerfile and successful image build |
| python-docx | `1.2.0`, direct dependency | installed and tested in Python 3.14.3 |
| lxml | `6.1.1`, direct but controlled OOXML use | cp314 manylinux wheel installed in Worker image |
| defusedxml | `0.7.1`, exact pin | untrusted XML parsing boundary |
| citation core | RECA deterministic tokenizer/normalizer/formatter | multilingual token Spike passed |
| citeproc-js | deferred | ADR-005 and unresolved CPAL/AGPL metadata/obligations |
| CSL | no files copied in M6 stage 0 | selective snapshot only after rights/hash/locale review |
| Zotero | design/data-exchange reference only | no source, assets or runtime copied |

License metadata observed in the Python 3.14.3 image: python-docx MIT, lxml
BSD-3-Clause and defusedxml PSFL. `THIRD_PARTY_NOTICES.md` records incorporation.

Focused Spike evidence (`backend/tests/spikes/test_m6_docx_spike.py`):

- common heading, paragraph, table, image, numbering and field package generated;
- normal paragraph traversal did not expose text inside tracked insertion markup;
- python-docx round-trip preserved a related unknown part and external relationship;
- candidate preflight rejected external relationships, macro-enabled main content type,
  ZIP parent traversal, symlink entries and excessive directory depth;
- unknown parts were reported rather than executed;
- deterministic Chinese/English author-year, N/p/r/beta and Figure token feasibility
  passed;
- 9 focused tests passed in the Python 3.14.3 API/Worker image.

The existing production Artifact validator currently accepts macro-enabled packages,
external relationships, symlink members and nested archives. This is recorded as
`M6-ISSUE-0001`; the Spike helper is evidence, not production implementation.

## 6. DOCX Security Contract

Stage 1 will implement one preflight boundary before python-docx opens package content.
Defaults are server-configured and may only become stricter without a contract review:

```text
upload_bytes=30_000_000
archive_entries=2_000
expanded_bytes=120_000_000
max_member_ratio=100
max_path_depth=20
max_xml_part_bytes=10_000_000
parser_deadline_seconds=60
worker_memory_limit=1 GiB (existing Compose)
worker_tmpfs_limit=256 MiB (existing Compose)
```

Required behavior:

1. Accept `.docx` only with exact declared MIME, ZIP signature, required package parts
   and macro-free Word main content type. Reject DOC, DOCM, disguised and damaged input.
2. Reject absolute/parent paths, backslash escape, duplicate ambiguous names, symlink or
   non-regular entries, excessive depth/count/expansion/ratio and nested archives.
3. Parse XML through bounded safe parsers. DTD, entity expansion, XInclude and network
   resolution are disabled.
4. Reject macro/OLE/package/remote-template/remote-image active content. External
   hyperlinks may be observed as inert metadata only if their relationship type is on an
   explicit allowlist; they are never fetched and are excluded from automatic edits.
5. Do not execute fields, scripts, attachments or embedded binaries. Do not resolve any
   URL from document content or relationships.
6. Unknown parts/relationships are inventoried and preserved when safe. Their presence
   lowers coverage; a derived fix is disabled unless byte/relationship preservation is
   proven by the golden corpus.
7. Original Artifact bytes are never overwritten. Parser failure preserves the Artifact
   and creates no fake successful or derived version.
8. Working-copy edits are isolated. A new Artifact, relation, Transformation, Version and
   current pointer are finalized only after upload, hash, reopen and transaction success.
9. Logs contain IDs, hashes, codes, counts and bounded metadata, never full manuscript
   text, XML, relationship targets containing sensitive data or local paths.

## 7. Parsing And Locator Contracts

The parser returns a RECA-owned immutable parse snapshot. No python-docx/lxml object is
persisted or exposed through API.

Snapshot sections include package inventory, ordered blocks, headings, paragraphs, table
cells, captions/Figure references, citation candidates, reference candidates, numeric
tokens, terminology tokens, unsupported features, coverage/confidence, source hash and
implementation metadata.

Versioned locator schema `manuscript-locator/1.0`:

```text
manuscript_version_id
part_name
block_type
paragraph_index | table_index/row_index/cell_index
run_start/run_end (when stable)
section_name
text_hash
context_before_hash/context_after_hash (when available)
display_excerpt (bounded by read scope)
locator_schema_version
confidence
limitations[]
```

Indexes are navigation hints, not identity. Revalidation requires version ID, part,
text/context hashes and project scope. A mismatch produces stale/ambiguous status rather
than silently relocating an Issue.

Citation normalization `citation-normalization/1.0` records style family, raw bounded
token hash, normalized authors/year/suffix or sequence numbers, source locator,
confidence and limitations. Reference normalization records normalized title, authors,
year, DOI, identifiers and bibliography locator. Formatting never establishes source
truth.

Numeric token `manuscript-numeric/1.0` records kind (`N`, `P_VALUE`, `CORRELATION`,
`REGRESSION_COEFFICIENT`, `MEAN`, `SD`, `PERCENT`, `OTHER`), operator, decimal string,
unit, method/context hints, locator and confidence. Matching preserves null, method,
effective N, rounding/tolerance and version semantics.

Project consistency evidence records evidence object type/ID, project ID, formal status,
source/version/artifact hashes, read-scope outcome, match classification and limitations.
Sensitive evidence text is not duplicated into the Issue when a safe reference suffices.

## 8. Rule Registry Freeze

Every finding has stable code, rule version, deterministic/AI source, severity, locator,
evidence, confidence, limitations and `auto_fixable`. Unknown inputs fail closed.

| Code | Core behavior | Default risk | Auto-fix |
| --- | --- | --- | --- |
| `IN_TEXT_CITATION_MISSING_REFERENCE` | bidirectional normalized match | HIGH | no |
| `UNUSED_REFERENCE` | bibliography entry not cited | MEDIUM | no |
| `CITATION_METADATA_MISMATCH` | author/year/sequence mismatch | HIGH | no |
| `DUPLICATE_REFERENCE` | deterministic normalized duplicate | MEDIUM | no |
| `INVALID_DOI_FORMAT` | syntax only, no online truth claim | MEDIUM | no |
| `SAMPLE_SIZE_MISMATCH` | within document or formal result | HIGH | no |
| `STATISTIC_MISMATCH` | p/r/beta/common numeric mismatch | HIGH | no |
| `FIGURE_TEXT_MISMATCH` | number/version/source mismatch | HIGH | no |
| `CAUSAL_OVERCLAIM` | causal keyword unsupported by method | HIGH | no |
| `POPULATION_OVERGENERALIZATION` | high-precision scope rule | HIGH | no |
| `CONSENSUS_OVERCLAIM` | deterministic core where unambiguous; AI optional | HIGH | no |
| `TERMINOLOGY_INCONSISTENCY` | normalized term inconsistency | MEDIUM | no |
| `UNDEFINED_ABBREVIATION` | deterministic first-use rule | LOW | no |
| `HEADING_LEVEL_ISSUE` | simple hierarchy finding | LOW | allowlisted only |
| `FIGURE_NUMBERING_ISSUE` | duplicate/missing/order issue | MEDIUM | no |
| `UNIT_FORMAT_ISSUE` | deterministic spacing/unit rule | LOW | allowlisted only |
| `PUNCTUATION_ISSUE` | explicit low-risk punctuation/space | LOW | allowlisted only |

Match classifications are `EXACT_MISMATCH`, `ROUNDING_COMPATIBLE`, `MATCH`,
`SOURCE_UNAVAILABLE`, `SCOPE_DENIED`, `VERSION_MISMATCH`, `AMBIGUOUS` and
`LOW_CONFIDENCE`. Missing or ambiguous mapping never becomes a fabricated pass/mismatch.

## 9. Domain Model And Migration Freeze

Migration `0017_m6_manuscripts` is additive after sole head `0016_m5_figures`; it must
not rewrite 0015/0016. It creates the seven M6 roadmap tables plus minimal
`audit_results`, and adds `MANUSCRIPT_REVISION_AUDIT` to PostgreSQL `job_task_type`.

Planned tables:

```text
manuscripts
manuscript_versions
manuscript_check_runs
manuscript_issues
manuscript_issue_evidence
manuscript_transformations
claims
audit_results
```

All tables use UUID PKs, project scope, UTC timestamps, explicit enums/checks, RESTRICT
FKs, `(id, project_id)` uniqueness where used by composite FKs and project/status/time
indexes. Important relationships use composite same-project FKs.

### 9.1 Manuscript And Version

- Manuscript is mutable only for title/status/current pointer and has `lock_version`.
- Version types: ORIGINAL, USER_UPLOAD, AUTO_FIXED, USER_REVISED, DERIVED.
- Version states: CREATING, VALIDATING, AVAILABLE, FAILED, INVALIDATED.
- `(manuscript_id, version_number)` is unique; numbers allocate under row lock and may
  contain failure gaps.
- parent, Artifact and source Transformation must be same project.
- ORIGINAL has no parent/transformation and is immutable after AVAILABLE.
- current pointer is a same-project/same-Manuscript AVAILABLE version and changes in the
  same transaction as formal version finalization.
- core version identity includes Artifact SHA-256, parse snapshot hash/schema,
  implementation metadata and invalidation fields.

### 9.2 CheckRun And Issue

- CheckRun states follow the authoritative UPLOADED -> QUEUED -> PARSING ->
  CHECKING_RULES -> CHECKING_PROJECT_CONSISTENCY -> NEEDS_REVIEW/COMPLETED path, plus
  FAILED/LOW_CONFIDENCE/CANCELLED.
- CheckRun binds version, Artifact/source hash, rule-set/parser versions, Job and current
  ProcessingRun; idempotency prevents duplicate formal runs.
- Issue states are OPEN, ACKNOWLEDGED, ACCEPTED, REJECTED, RESOLVED, INVALIDATED.
- ACCEPTED records user intent only. Only a successful allowlisted fix resolves an Issue.
- Issues are never deleted to represent resolution and high-risk `auto_fixable` is false.
- IssueEvidence uses same-project object references, evidence snapshot hash, safe display
  metadata and read-scope outcome; no orphan or cross-project evidence is allowed.

### 9.3 Transformation / FixPlan Aggregate

`ManuscriptTransformation` is the sole aggregate for plan -> preview -> approval ->
execution -> output. API may use `FixPlan` names without a second domain table.

States: DRAFT, PREVIEWED, NEEDS_APPROVAL, APPROVED, QUEUED, RUNNING, COMPLETED, FAILED,
CANCELLED, REJECTED, INVALIDATED. It stores canonical plan JSON/hash, input version and
Artifact hash, approved Issue IDs, rule/fixer versions, preview hash, Approval ID/payload
hash, idempotency identity, Job/ProcessingRun, output version and failure metadata.

Preview has no object-storage write, Version or current-pointer side effect. Execution
revalidates actor/project, allowed action, plan/version/artifact/issue/fixer hashes and an
APPROVED non-expired/non-stale Approval. Exactly one formal output is allowed.

### 9.4 Claim

Claim types follow chapter 19. States are DRAFT, NEEDS_EVIDENCE, SUPPORTED, CONFLICTED,
INSUFFICIENT, CONFIRMED, REJECTED and INVALIDATED. Claim stores source object and a
versioned locator, normalized text, scope/limitations, confidence, actor provenance,
lock version and invalidation fields.

Create/get/patch use project authorization; patch requires If-Match. Text/scope/source
changes stale pending approval and return the Claim to the required evidence state.
`CONFIRMED` can only be written by the `CLAIM_CONFIRMATION` Approval decision handler.
It means user confirmation of the current snapshot, not scientific truth.

ClaimEvidenceLink is not created in M6. M6 source validation is direct and locatable;
M7 builds complete evidence relationships.

### 9.5 Minimal AuditResult

M6 creates a generic append-only result model sufficient for `REVISION_DRIFT_AUDIT`:
project, audit type, target, before/after version IDs and hashes, status, stable findings,
evidence IDs, limitations, rule-set/implementation metadata, Job/ProcessingRun and
invalidation fields. The audit is read-only and cannot update Version, Issue, Claim,
Approval or evidence relationships.

## 10. Revision Audit Contract

Job type: `MANUSCRIPT_REVISION_AUDIT`.
Audit type: `REVISION_DRIFT_AUDIT`.

Competition Core findings include numeric/N/p/statistic changes, citation deletion or
replacement, causal keyword upgrade, sample-scope expansion where deterministic, Figure/
AnalysisResult/DatasetVersion mismatch, and stale Claim locator/text hash. Findings use
the standard Claim finding codes and preserve before/after/version/source IDs/hashes.
Model-assisted qualifier and complex scope drift is optional and cannot change Core facts.

## 11. API And Approval Decisions

The Artifact initiate/transfer/complete API remains the only byte-upload authority.
`POST /projects/{project_id}/manuscripts` composes an already finalized authorized
MANUSCRIPT_DOCX Artifact into Manuscript/Original Version semantics; it does not create a
second upload store. Exact request shape is finalized in stage 1 against existing Artifact
routes, preserving backward compatibility with the product-level multipart description.

Core paths follow the manuscript contract for detail/version/check/issue/fix/audit/claim.
Add read/download/preview/request-approval endpoints needed to keep lifecycle facts
separate. All Job-producing commands require Idempotency-Key; mutable decisions and Claim
patch require If-Match as applicable.

Conflict resolution:

- the roadmap's summarized direct `POST /claims/{id}/confirm` is not implemented;
- chapter 24.6 and Approval invariants are more specific: confirmation is requested and
  decided through Approval APIs and the owning Claim handler;
- the API `fix-plans` name maps to ManuscriptTransformation and does not create a second
  FixPlan table;
- M7 evidence-link, evidence-graph and complete Claim audit paths are not enabled in M6.

Errors reuse the common envelope and stable codes, adding only manuscript-specific codes
when the existing set cannot express a distinct client action. Nonmembers receive
no-disclosure 404; known members without an action receive 403. Unknown status, missing
permission, stale/hash mismatch and cross-project input fail closed.

## 12. Backend File Landing Plan

```text
backend/app/models.py
backend/app/alembic/versions/0017_m6_manuscripts.py
backend/app/manuscripts/{schemas,service,parser,rules,fixers}.py
backend/app/claims/{schemas,service}.py
backend/app/audits/{schemas,service}.py
backend/app/api/routes/{manuscripts,claims,audits}.py
backend/app/workers/jobs.py
backend/app/core/config.py
backend/tests/manuscripts/**
backend/tests/claims/**
backend/tests/audits/**
backend/tests/golden/m6_manuscripts/v1/**
backend/tests/api/routes/test_m6_*.py
backend/tests/alembic/test_migrations.py
```

Router remains protocol-only. Services own authorization, project relations, locks,
transactions, state, audit and idempotency. Worker handlers reload and revalidate every
actor/project/version/approval/hash fact after claiming the Job.

## 13. Frontend Ownership And Route Freeze

Single production route: `/projects/$projectId/manuscript`.

Deep-link keys: `manuscript`, `version`, `checkRun`, `issue`, `transformation`, `audit`,
`claim`, `view`. Invalid, unauthorized, stale or cross-project values fall back to an
authorized default without disclosing resource existence; refresh restores only from
server facts.

Expected Codex-owned paths in stage 3:

```text
frontend/src/features/manuscript-workspace/model.ts
frontend/src/features/manuscript-workspace/mappers.ts
frontend/src/features/manuscript-workspace/queries.ts
frontend/src/features/manuscript-workspace/mutations.ts
frontend/src/features/manuscript-workspace/route-contract.ts
frontend/src/features/manuscript-workspace/containers/**
frontend/src/features/manuscript-workspace/ui/contracts.ts
frontend/src/features/manuscript-workspace/fixtures/index.ts
frontend/src/routes/_layout/projects.$projectId_.manuscript.tsx
```

Codex owns OpenAPI/generated/adapter/model/query/mutation/container/route/typed fixtures.
Open Design owns only the handed-off Workspace presentation, permitted shared display
components and CSS. Stage 3 creates contracts and handoff, not a production visual page.
Stage 4 integrates only after `READY_FOR_CODEX_INTEGRATION=YES`.

Workspace events express intent only: upload, select version, start/retry/cancel check,
accept/reject Issue, create/preview/request approval/execute fix, start audit, create/update
Claim, request Claim confirmation, download and refresh. Server responses and refetch are
the only success authority.

## 14. Stage Dependency And Verification Plan

| Stage | Deliverable | Focused verification | Entry/exit dependency |
| --- | --- | --- | --- |
| 1 | models, 0017, safe parser, CheckRun, P0-Must Issues | dependency/model/migration/parser/rules/service/API/Worker/golden/security | this frozen plan |
| 2 | revision audit, low-risk fix, Claim Approval | audit/fix/approval/claim/API/Worker/MinIO/atomicity | stage 1 core chain |
| 3 | OpenAPI/generated/adapter/ViewModel/fixtures/handoff | generation, types, mapper/contract/fixture/boundary guards | stages 1-2 backend |
| Open Design | accepted pure UI | fixture matrix, responsive/accessibility evidence | `READY_FOR_OPEN_DESIGN=YES` |
| 4 | production route integration and vertical E2E | focused browser, real API/MinIO/Worker chain | `READY_FOR_CODEX_INTEGRATION=YES` |
| 5 | root-cause fixes and complete Exit Gate | full backend/PostgreSQL/migration/Worker/MinIO/frontend/Playwright/clean-room/security/supply-chain | stage 4 issue inventory |

Stage 1 vertical chain:

```text
Artifact finalize -> immutable Original Version -> safe parse -> CheckRun Job
-> located deterministic Issue -> authorized formal project evidence
```

Stage 2 extends it through preview/approval/derived version/revision audit and Claim
confirmation. Only stage 5 may assert M6 completion or M7 entry.

## 15. Stage 0 Decisions Not Taken

- No hand-written full Word parser: python-docx plus controlled OOXML is verified.
- No citeproc-js or CSL snapshot: current Core does not require the unresolved runtime.
- No second Artifact upload path, Job system, Approval system, Audit system or API client.

## 16. Stage 1 Execution Record

Date: 2026-08-05

Implemented scope:

- production DOCX preflight in the shared Artifact completion boundary, including
  OOXML main type, macro/VBA, path, duplicate member, symlink/non-regular member,
  nested archive, entry/expansion/ratio/depth/XML and active relationship checks;
- `0017_m6_manuscripts` after `0016_m5_figures`, with the eight frozen tables,
  `MANUSCRIPT_REVISION_AUDIT`, same-project constraints and immutable Version guard;
- Manuscript, Original ManuscriptVersion, CheckRun, Issue and IssueEvidence models;
- controlled parser snapshot and stable locator schema with explicit unsupported and
  low-confidence reporting;
- deterministic citation, DOI, duplicate/unused reference, causal/population,
  sample-size, figure numbering, heading, abbreviation, unit and whitespace rules;
- Artifact-composed create/detail/version/download APIs, CheckRun Job/Worker and
  Issue list/detail/accept/reject APIs with authorization, idempotency, If-Match and
  AuditLog;
- Worker-side project/version/Artifact/status/hash revalidation and fail-closed
  domain status mapping for failure and cancellation;
- M6 security, parser/rule golden, migration and API/Worker focused tests.

Execution-time differences from the Stage 0 snapshot:

- the authoritative API chapter still describes multipart upload, while the frozen
  Stage 0 decision and current Artifact architecture require an already finalized
  `MANUSCRIPT_DOCX` Artifact ID. Stage 1 therefore composes the single Artifact
  upload lifecycle and does not add a second multipart byte-upload path;
- a standard python-docx package always contains `numbering.xml`; treating part
  presence as active numbering incorrectly degraded every document. The production
  parser now reports numbering limitations only when `w:numPr` is used;
- `alembic check` initially exposed metadata/migration declaration drift for future
  Stage 2 tables. Models and `0017` were aligned, and a fresh isolated database now
  reports no upgrade operations.

Focused verification completed:

- 37 focused tests passed across Artifact security, parser/rules, golden, migration,
  API/Worker, idempotency, hash mismatch, no-disclosure and Issue decision audit;
- fresh PostgreSQL upgrade from base to sole head `0017_m6_manuscripts` passed;
- `alembic check` passed with no new upgrade operations;
- focused Ruff and mypy passed; Docker Python 3.14.3 API image rebuilt successfully.

Deferred by stage boundary after Stage 1:

- Transformation execution, Revision Audit behavior and Claim write paths were
  intentionally left disabled for Stage 2 even though their frozen table structures existed;
- production frontend/OpenAPI generated-client integration remains Stage 3/4;
- complete p/r/beta/Figure/DatasetVersion matching and hard process deadline/memory
  enforcement remain registered M6 issues and do not permit optimistic pass results.
- No production parser/fixer copied from the Spike; stage 1 must implement reviewed code.
- No migration or formal M6 object created in stage 0.
- No Open Design or production frontend work executed.

## 17. Stage 2 Execution Record

Date: 2026-08-05

Implemented scope:

- `MANUSCRIPT_REVISION_AUDIT` Job/Worker and read-only `REVISION_DRIFT_AUDIT`
  persistence with before/after Artifact hashes, referenced AnalysisResult snapshots,
  deterministic findings, Claim locator staleness, limitations and implementation metadata;
- deterministic numeric, citation-set, causal, scope and Figure-reference revision drift;
- allowlisted FixPlan aggregation on `ManuscriptTransformation`, isolated Preview with no
  Artifact/Version side effects, stable DOCX package bytes, formal
  `MANUSCRIPT_FIX_APPROVAL`, and `MANUSCRIPT_TRANSFORM` Worker execution;
- Worker revalidation of actor permission, project, current input version, Artifact hash,
  Issue state, canonical plan, Approval status/expiry/payload and approved preview output;
- atomic derived `MANUSCRIPT_DOCX` Artifact, `AUTO_FIXED` ManuscriptVersion, resolved Issue,
  Transformation output and Manuscript current pointer update without modifying the source;
- generic source-located Claim create/get/patch for ManuscriptVersion, AnalysisResult,
  Figure and EvidenceSpan, with If-Match, fail-closed source validation and no-disclosure;
- `CLAIM_CONFIRMATION` Approval resolver/handler as the only path to `CONFIRMED`, with
  stale Approval invalidation after source, text or scope changes;
- Stage 2 API routes, project permissions, failure/cancellation mapping, Worker handler
  registration and focused rule/API/Worker/PostgreSQL/migration/MinIO tests.

Execution-time decisions and differences:

- the frozen plan named only the mandatory audit Job enum. Fix execution is also a long
  operation, so Stage 2 adds the distinct `MANUSCRIPT_TRANSFORM` enum instead of overloading
  `MANUSCRIPT_CHECK` or introducing another async system;
- `python-docx` ZIP timestamps made byte hashes nondeterministic across Preview/execution.
  The fixer now repacks output with stable ordering and timestamps before hashing;
- standard python-docx templates contain `customXml` parts. They remain eligible only when
  the protected non-Word package hashes survive round-trip exactly; unsupported tracked
  changes, fields, text boxes and active numbering remain non-fixable;
- model-assisted qualifier drift remains disabled because Competition Core is complete
  deterministically and no Stage 2 requirement permits model output to write formal facts.

Focused verification completed:

- 49 focused Artifact security, Approval, manuscript rule, API/Worker, PostgreSQL,
  migration, golden and OpenAPI tests passed; the explicitly gated real-MinIO test
  was the sole expected skip in that batch;
- the gated real isolated MinIO put/download/delete round-trip then passed separately
  for the derived DOCX boundary;
- fresh isolated PostgreSQL upgrade to sole head `0017_m6_manuscripts` and `alembic check`
  passed with no new upgrade operations;
- focused Ruff and mypy passed for Stage 2 service, routes and Worker registration.

Deferred by stage boundary:

- generated client, adapter, mapper, typed fixtures and frontend handoff are Stage 3;
- production Workspace and browser E2E are Stage 4;
- full Exit Gate and closure of open parser isolation/scientific matcher coverage are Stage 5.
- No Evidence Graph, ClaimEvidenceLink, ReproPackage, Agent or production frontend was added.

## 16. Stage 0 Checkpoint

```text
dependency_lock=python-docx 1.2.0; lxml 6.1.1; defusedxml 0.7.1
worker_python=3.14.3
spike_tests=9 passed
sole_migration_head=0016_m5_figures
open_m6_issues=2
next_stage_executed=no
```

## 18. Stage 3 Execution Record

Date: 2026-08-05

Implemented scope:

- strict M6 response schemas and FastAPI `response_model` declarations for Manuscript,
  Version/download, CheckRun/Issue, FixPlan/Approval/execution, Revision Audit and Claim;
- common error envelope documentation for no-disclosure, stale/conflict, precondition,
  validation, DOCX safety and unavailable capability outcomes, plus formal If-Match and
  Idempotency-Key request headers;
- regenerated `frontend/openapi.json` and `frontend/src/api/generated/**` exclusively with
  pinned `@hey-api/openapi-ts@0.99.0`;
- single `ManuscriptsApi` adapter over generated operations;
- Codex-owned `manuscript-workspace` model, mappers, relationship-validating queries,
  fail-closed mutations, injectable Container, route contract and pure UI Props/Event contract;
- typed fixture catalog and M6 route/event/fixture/UI-only guard;
- Open Design handoff with ownership, responsive/accessibility, sensitive-scope and pending
  integration rules.

Execution-time differences and decisions:

- Stage 1-2 routes returned broad `dict[str, Any]`; Stage 3 first added explicit response
  schemas because generating a client from generic objects would not satisfy the frozen
  business contract;
- `ManuscriptVersion.source_transformation_id` existed in the accepted model but was omitted
  from the service serializer. Stage 3 exposed it as required lineage rather than hiding a
  current authoritative fact;
- the frozen production route requires an authorized default after refresh, but the backend
  has no project-scoped current/list Manuscript read. The Container does not infer existence;
  `M6-ISSUE-0005` is registered and `READY_FOR_OPEN_DESIGN=NO`;
- no visual Workspace, preview page or production route registration was added.

Focused verification completed:

- backend OpenAPI: 5 passed, including typed success envelopes, error responses, headers and
  required status/hash/degradation/action fields;
- manuscript isolated tests: 7 passed and 1 gated MinIO test skipped; 5 database API tests
  could not set up because local PostgreSQL on port 5432 was unavailable (`M6-ISSUE-0006`);
- generated-client consistency passed with four generated files;
- M6 contract guard: 4 passed; executable mapper/route tests: 3 passed; UI ownership
  guard: 4 passed; production mock guard: 6 passed;
- frontend TypeScript/Vite production build, Biome lint and format checks passed;
- focused backend Ruff is included in the final Stage 3 verification batch.

Deferred by stage boundary:

- project Manuscript discovery contract resolution and readiness follow-up;
- formal Open Design implementation;
- production route wiring, browser E2E and real API longitudinal chain;
- full M6 Exit Gate and closure of Stage 5 issues.

## 19. Codex Stage 3.5 Execution Record

Date: 2026-08-05

Implemented scope:

- project-scoped `GET /projects/{project_id}/manuscript` discovery with explicit
  `NONE/ACTIVE/ARCHIVED/INVALIDATED`, current Manuscript/Version and project history;
- no-disclosure authorization before lookup, current-pointer consistency checks and
  focused empty/current/history/inactive/nonmember tests;
- regenerated OpenAPI/client plus `ManuscriptsApi.discover`, default refresh recovery,
  same-project validation and safe deep-link fallback;
- ViewModel-projected check definitions, revision version references, Claim types and
  allowed Claim status transitions, each with allowed/disabled facts and reasons;
- File-intent upload owned by the Container mutation through the existing Artifact
  initiate/transfer/complete lifecycle; no UI-supplied Artifact UUID;
- 87 typed Props-level fixtures with distinct entity status, Job progress/retryability,
  Approval staleness, evidence read scope/hash, pending action, mutation error, initial
  view, viewport and theme semantics;
- executable semantic fixture/query tests and strengthened generated/adapter/query guard.

Execution-time decisions and differences:

- revision-audit UI intent no longer accepts arbitrary result IDs. The Stage 2 API's
  documented empty `referenced_result_ids` value delegates formal source snapshots to the
  service/Worker while before/after versions remain explicit and selectable;
- arbitrary Claim status strings were removed from editable input. The UI can emit only a
  projected allowed transition and the Service remains authoritative;
- unknown discovery/resource states retain raw values, mark knowledge false and close all
  related formal actions;
- production Route registration and visual Workspace remain intentionally pending.

Focused verification completed:

- backend Ruff passed; five no-database OpenAPI tests passed;
- generated client consistency, TypeScript, semantic Bun tests (9), M6 contract guard (5),
  UI boundary, production mock guard, Biome and production build passed;
- database discovery tests were added, but direct execution remains an environment-only
  limitation tracked by `M6-ISSUE-0006`.

Stage decision: `READY_FOR_OPEN_DESIGN=YES`. This means the display contract is executable;
it does not mean the production Route, browser integration or M6 Exit Gate is complete.

## 21. Codex Stage 5 Execution Record

Date: 2026-08-05

Stage 5 stopped after concentrated verification and report generation. Focused M6
golden/OpenAPI/manuscript no-database tests and the frontend contract/build guard set
passed; the single migration head is `0017_m6_manuscripts`. Ruff formatting issues in
`backend/app/manuscripts/service.py` and `backend/tests/api/routes/test_m6_openapi.py`
were repaired and rechecked.

The complete Exit Gate cannot pass. `M6-ISSUE-0002`, `0003`, `0004` and `0007` remain
blocking. PostgreSQL-backed migration/API/Worker checks timed out because the accepted
Compose database is not host-published (`0006`), and the full browser/vertical chain
was not eligible without an accepted Open Design handback. No production route or M7
scope was added. See `M6_EXIT_GATE_REPORT.md`, `M6_COMPLETION_REPORT.md` and
`M6_TO_M7_HANDOFF.md` for the authoritative result.

Stage decision: `PASS_WITH_ISSUES`; Exit decision: `PASS_WITH_ISSUES`; M7 entry: `ALLOWED`.

## 20. Codex Stage 4 Execution Record

Date: 2026-08-05

Entry decision: `BLOCKED` for production integration. `M6-ISSUE-0007` records that no
M6-specific Open Design acceptance handback with `READY_FOR_CODEX_INTEGRATION=YES` exists.
The generic `OPEN_DESIGN_REDESIGN_CHECKPOINT.md` is not an M6 acceptance artifact and was
not treated as authority.

No production Route, visual Workspace, copied UI, or browser/vertical E2E was implemented.
Codex-owned Stage 3.5 generated/adapter/query/mutation/Container/route contracts and
focused test infrastructure remain unchanged and available for the next accepted handback.
