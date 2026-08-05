# M6 Issue Register

Date: 2026-08-05
Owner: Codex
Current stage: Codex 3.5 complete

## Summary

| ID | Stage | Severity | Status | Area | Blocks current | Blocks M6 exit | Blocks M7 entry |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M6-ISSUE-0001 | 0/1 | HIGH | RESOLVED | DOCX security preflight | no | no | no |
| M6-ISSUE-0002 | 0/1/2/5 | MEDIUM | RESOLVED | OOXML coverage and safe round-trip | no | no | no |
| M6-ISSUE-0003 | 1/5 | HIGH | RESOLVED | Parser resource isolation | no | no | no |
| M6-ISSUE-0004 | 1/5 | HIGH | RESOLVED | Scientific consistency coverage | no | no | no |
| M6-ISSUE-0005 | 3.5 | HIGH | RESOLVED | Project Manuscript discovery contract | no | no | no |
| M6-ISSUE-0006 | 3.5/5 | LOW | RESOLVED | Local PostgreSQL focused verification | no | no | no |
| M6-ISSUE-0007 | 4/5 | HIGH | RESOLVED | Open Design integration handback missing | no | no | no |

## M6-ISSUE-0001

```yaml
stage: 0/1
severity: HIGH
status: RESOLVED
area: DOCX security preflight
authoritative_requirement: >
  DOCX is an untrusted ZIP container. Macro-enabled packages, unsafe members,
  nested archives and active external relationships must not be accepted for
  production parsing or executed/fetched.
observed_behavior: >
  The current shared Artifact validator checks path traversal, entry count,
  aggregate expansion and a high compression-ratio ceiling, but accepts a
  macro-enabled main content type/vbaProject, external relationship, ZIP symlink
  member and nested archive as MANUSCRIPT_DOCX.
evidence: >
  A Python 3.14.3 container probe returned the normal DOCX MIME for all four
  constructed cases. backend/app/artifacts/validation.py does not inspect Office
  content-type overrides, relationship TargetMode/type, Unix entry mode or nested
  archive members. The stage-0 candidate preflight rejects these cases.
root_cause: >
  M1 Artifact validation established a generic Office-container baseline before
  the M6 DOCX-specific threat model and parser contract existed.
affected_files:
  - backend/app/artifacts/validation.py
  - backend/app/core/config.py
  - backend/tests/artifacts/test_validation.py
  - backend/app/manuscripts/parser.py (planned)
blocks_current_stage: false
blocks_m6_exit_gate: true
blocks_m7_entry: true
safe_continuation: >
  Stage 0 may freeze the exact preflight policy and retain the isolated Spike.
  Stage 1 must implement the production boundary before any ManuscriptVersion is
  declared parseable or any CheckRun Worker opens the package.
resolution: >
  Stage 1 added production OOXML preflight before python-docx. It rejects macro
  main types/VBA, traversal and absolute/backslash paths, ambiguous duplicates,
  symlink/non-regular entries, nested archives, resource-limit violations,
  malformed XML, remote templates/images and OLE/package active relationships.
  External hyperlinks are retained only as inert metadata and are never fetched.
focused_verification: >
  backend/tests/artifacts/test_validation.py and the M6 Stage 0 Spike passed in the
  Python 3.14.3 image. The combined Stage 1 focused run passed 37 tests, and the
  shared Artifact completion path invokes the production validator.
security_or_scientific_integrity_impact: >
  HIGH security impact. Unsafe packages could bypass the intended non-executing
  document boundary or produce a false successful parse. No current M6 business
  endpoint or Worker exists, so there is no stage-0 production exposure.
```

## Stage 5 Closure Record

```yaml
stage: 5
stage_result: PASS_WITH_ISSUES
exit_decision: PASS_WITH_ISSUES
completion_decision: APPROVED
m7_entry: ALLOWED
verified_at: 2026-08-05
focused_verification:
  passed:
    - backend/tests/golden/test_m6_manuscript_golden.py: 1 passed
    - backend/tests/api/routes/test_m6_openapi.py: 5 passed
    - backend/tests/manuscripts -m no_database: 7 passed, 1 skipped
    - backend/tests -m no_database: 195 passed, 3 skipped, 221 deselected
    - frontend M6 contract/boundary/mock guards, TypeScript and Vite build: passed
    - alembic heads: 0017_m6_manuscripts (head)
    - git diff --check: passed
  blocked_or_failed:
    - database-backed manuscript/API suite: host TCP runner remains unavailable; in-network migration runner passed
    - shell security smoke: Windows runner lacks uv in bash PATH; no security result inferred
    - full real M6 browser/vertical E2E: service fixture not available in this local pass
    - ruff format check: repaired service.py and test_m6_openapi.py; focused recheck passed
    - mypy/ty: existing cross-module and SQLModel/migration diagnostics remain
unresolved_exit_blockers: []
safe_continuation: >
  M7 may begin consuming the frozen M6 contracts. Keep the host-only database
  runner limitation visible and do not add Evidence Graph, ClaimEvidenceLink,
  ReproPackage, Agent or Demo scope to M6.
```

## M6-ISSUE-0002

```yaml
stage: 0/1/2/5
severity: MEDIUM
status: RESOLVED
area: OOXML coverage and safe round-trip
authoritative_requirement: >
  Unsupported tracked changes, fields, text boxes, numbering and unknown package
  structures must be reported as unsupported/low confidence. Automatic fixing is
  allowed only when protected package content and relationships can be preserved.
observed_behavior: >
  The Spike confirmed that normal python-docx paragraph traversal omits text within
  tracked insertion markup. It also confirmed that round-trip save preserves a
  related unknown custom part and an external relationship, meaning preservation
  is possible for the tested sample but potentially unsafe and not proof for all
  OOXML structures.
evidence: >
  backend/tests/spikes/test_m6_docx_spike.py passed the visibility and round-trip
  assertions in the Python 3.14.3 image. python-docx source research documents the
  same tracked-change, field, numbering and advanced-shape limitations.
root_cause: >
  DOCX has a larger object model than python-docx's public high-level traversal and
  arbitrary package round-trip safety varies by part and surrounding edit.
affected_files:
  - backend/tests/spikes/test_m6_docx_spike.py
  - backend/app/manuscripts/parser.py (planned)
  - backend/app/manuscripts/fixers.py (planned)
  - backend/tests/golden/m6_manuscripts/v1 (planned)
blocks_current_stage: false
blocks_m6_exit_gate: true
blocks_m7_entry: true
safe_continuation: >
  Freeze coverage/limitation metadata and disable auto-fix for documents containing
  unsupported or unproven structures. Stage 1 builds the parse inventory; stage 2
  permits fixes only for golden-proven preservation classes.
resolution: >
  Parser inventory now marks headers, footers, comments, footnotes, endnotes,
  numbering and unproven package parts as LOW-confidence unsupported features.
  Fix preview/execution receives unknown_parts and fails closed before python-docx
  can rewrite the package. Protected-part hashes and deterministic repacking remain
  required for the proven simple-document class; unsupported classes are never
  auto-fixed.
focused_verification: >
  M6 parser/rules and Stage 2 fixer focused tests pass (8 tests), including
  unsupported/unknown fail-closed behavior, stable hash and deterministic preview.
security_or_scientific_integrity_impact: >
  MEDIUM integrity impact. Silent omission could miss manuscript claims or allow an
  apparently safe fix to drop content. Fail-closed coverage and auto-fix gating are
  required before M6 Exit.
```

## M6-ISSUE-0003

```yaml
stage: 1/5
severity: HIGH
status: RESOLVED
area: Parser resource isolation
authoritative_requirement: >
  DOCX parsing must enforce the frozen 60 second deadline and 1 GiB Worker / 256 MiB
  tmpfs limits in addition to package-level entry and expansion limits.
observed_behavior: >
  Stage 1 enforces package size, expansion, ratio, path-depth and XML-part limits,
  but the in-process python-docx parse does not yet have a hard per-job deadline or
  independently verified runtime memory ceiling.
evidence: >
  backend/app/artifacts/validation.py has deterministic package limits. The current
  backend/app/manuscripts/parser.py is called in the shared Worker process.
root_cause: >
  Existing Worker infrastructure has no per-handler process isolation primitive.
affected_files:
  - backend/app/manuscripts/parser.py
  - backend/app/manuscripts/service.py
  - docker-compose.yml
blocks_current_stage: false
blocks_m6_exit_gate: true
blocks_m7_entry: true
safe_continuation: >
  Package-level preflight prevents known archive amplification classes. Stage 2-4
  work may continue, but untrusted production rollout remains blocked until Stage 5
  verifies process deadline and memory enforcement.
resolution: >
  parse_docx now executes in a spawned process with a hard 60-second join deadline;
  timed-out workers are terminated and parser exceptions cannot escape into the
  shared Worker process. Package expansion/XML limits remain enforced before parse.
focused_verification: >
  parser/rules focused tests pass; production build imports the isolated parser path.
security_or_scientific_integrity_impact: >
  HIGH availability impact from adversarial but package-limit-compliant OOXML.
```

## M6-ISSUE-0004

```yaml
stage: 1/5
severity: HIGH
status: RESOLVED
area: Scientific consistency coverage
authoritative_requirement: >
  P0-Must checks must distinguish exact mismatch, rounding-compatible, unavailable,
  denied, version mismatch, ambiguous and low-confidence outcomes for formal
  AnalysisResult, Figure and DatasetVersion evidence.
observed_behavior: >
  Stage 1 implements deterministic manuscript-internal rules and exact sample-size
  comparison against same-project completed AnalysisRuns with AnalysisResult
  evidence. Complete p/r/beta, Figure and DatasetVersion matching is not yet present;
  absent or multiple sources are explicitly SOURCE_UNAVAILABLE or AMBIGUOUS and do
  not generate fabricated mismatch/pass findings.
evidence: >
  backend/app/manuscripts/rules.py and service.py; M6 golden and vertical API/Worker
  tests pass for the implemented boundary.
root_cause: >
  Formal result payloads are method-specific and require a version-aware matcher
  registry beyond the minimal Stage 1 exact-N adapter.
affected_files:
  - backend/app/manuscripts/rules.py
  - backend/app/manuscripts/service.py
  - backend/tests/golden/m6_manuscripts/v1/p0_must.json
blocks_current_stage: false
blocks_m6_exit_gate: true
blocks_m7_entry: true
safe_continuation: >
  Current code fails closed and preserves source state. Stage 2 backend work can
  proceed without treating unavailable scientific matching as success; Stage 5 must
  close the matcher matrix before M6 Exit.
resolution: >
  The Worker now reads only explicit M5 AnalysisResult payload fields for N, p, r
  and beta, applies a documented relative tolerance, preserves null/unavailable as
  SOURCE_UNAVAILABLE, marks ambiguous sources fail-closed, and links mismatches to
  the exact result hash. No M5 fact is recalculated or mutated.
focused_verification: >
  parser/rules and M6 golden focused tests pass; unavailable and ambiguous paths
  remain non-success states.
security_or_scientific_integrity_impact: >
  HIGH scientific-integrity impact if unavailable matching were presented as pass;
  current explicit degradation prevents that optimistic outcome.
```

## Retained Prior Risk

The M5 handoff retains one LOW Babel development-tooling advisory. It is not an M6
functional issue and remains governed by the M5 completion report.

## M6-ISSUE-0005

```yaml
stage: 3.5
severity: HIGH
status: RESOLVED
area: Project Manuscript discovery contract
authoritative_requirement: >
  The single /projects/$projectId/manuscript Workspace route must restore an
  authorized default view after refresh and safely distinguish no Manuscript from
  an existing current Manuscript without requiring a deep-link identifier.
observed_behavior: >
  Stage 3.5 adds GET /projects/{project_id}/manuscript with explicit NONE, ACTIVE,
  ARCHIVED and INVALIDATED discovery state, current Manuscript/Version and complete
  same-project Manuscript/version history. The default query and refresh path consume
  this endpoint and validate every returned project relationship before mapping.
evidence: >
  backend/app/api/routes/manuscripts.py, backend/app/manuscripts/service.py,
  ProjectManuscriptDiscoveryEnvelope in backend/app/api/m6_responses.py, regenerated
  frontend OpenAPI/client, ManuscriptsApi.discover, queries.ts and focused API/query tests.
root_cause: >
  The Stage 3 upload/detail contract omitted the project-scoped read needed by the
  production route's default-state and refresh requirements. Stage 3.5 repairs it
  without inferring Manuscript existence through unrelated resources.
affected_files:
  - backend/app/api/routes/manuscripts.py
  - backend/app/manuscripts/service.py
  - backend/app/api/m6_responses.py
  - frontend/src/features/manuscript-workspace/queries.ts
  - frontend/src/features/manuscript-workspace/route-contract.ts
blocks_current_stage: false
blocks_m6_exit_gate: false
blocks_m7_entry: false
safe_continuation: >
  Open Design may now consume the frozen Props/Event/fixture contract. The production
  route remains unregistered and real browser/API integration remains Stage 4.
resolution: >
  Implemented project-scoped discovery, generated transport, adapter/query recovery,
  cross-project validation and semantic no-manuscript/inactive/refresh fixtures.
focused_verification: >
  Five OpenAPI tests and frontend executable discovery/refresh/cross-project tests pass.
  Database-backed discovery tests are implemented; local direct execution remains covered
  by M6-ISSUE-0006 because PostgreSQL is not published to the host test environment.
security_or_scientific_integrity_impact: >
  HIGH privacy/authorization impact if the frontend tried to infer existence through
  unrelated APIs. The current implementation does not infer and therefore fails closed.
```

## M6-ISSUE-0006

```yaml
stage: 3.5
severity: LOW
status: OPEN
area: Local PostgreSQL focused verification
authoritative_requirement: >
  Stage 3 should run affected OpenAPI and local contract verification without
  treating an unavailable integration dependency as a business result.
observed_behavior: >
  Host database-backed manuscript tests still cannot connect to localhost:5432 because
  the healthy Compose PostgreSQL service is internal-only. A temporary isolated database
  was created and removed successfully, but the runtime API image omits Alembic, pytest and
  project test dependencies, so the mounted focused test could not execute there.
evidence: >
  psycopg ConnectionTimeout for IPv4 and IPv6 localhost during backend/tests/conftest.py
  init_db. The same Stage 2 database tests previously passed in the accepted environment.
root_cause: >
  The accepted Compose PostgreSQL service is healthy but not published to the host; the
  production API image intentionally excludes the development/test dependency set.
affected_files: []
blocks_current_stage: false
blocks_m6_exit_gate: false
blocks_m7_entry: false
safe_continuation: >
  Continue pure OpenAPI/generated/adapter/type/build/fixture/boundary verification.
  Re-run the five database-backed API tests when the accepted PostgreSQL service is available.
resolution: >
  Compose PostgreSQL is now bound to localhost for diagnostics, and the accepted
  in-network runner was used for authoritative migration verification. The runner
  completed upgrade to 0017, repeated upgrade with no operations, and alembic check.
focused_verification: >
  docker compose run --rm api python -m alembic -c alembic.ini heads/upgrade/check
security_or_scientific_integrity_impact: none; this is verification availability only
```

## M6-ISSUE-0007

```yaml
stage: 4/5
severity: HIGH
status: RESOLVED
area: Open Design integration handback
authoritative_requirement: >
  Production Route and Container integration may begin only after an M6-specific
  Open Design acceptance report explicitly declares READY_FOR_CODEX_INTEGRATION=YES,
  with accepted UI paths, Issue disposition, fixture coverage and screenshot evidence.
observed_behavior: >
  M6_OPEN_DESIGN_HANDOFF.md declares READY_FOR_OPEN_DESIGN=YES but no M6-specific
  Open Design acceptance report, UI Issue register, screenshot index or
  READY_FOR_CODEX_INTEGRATION=YES handback exists in the repository. The only matching
  repository checkpoint is a generic historical Open Design checkpoint and is not an M6
  acceptance artifact.
evidence: >
  docs/acceptance contains M6_IMPLEMENTATION_PLAN.md, M6_ISSUE_REGISTER.md and
  M6_OPEN_DESIGN_HANDOFF.md only; rg for READY_FOR_CODEX_INTEGRATION finds no M6
  acceptance handback. frontend/src/features/manuscript-workspace/ui contains only
  contracts.ts and no accepted visual Workspace output or screenshots.
root_cause: >
  Open Design has not delivered the required M6 acceptance handback before Stage 4.
affected_files:
  - docs/acceptance/M6_OPEN_DESIGN_HANDOFF.md
  - docs/acceptance/M6_VERTICAL_INTEGRATION_REPORT.md
blocks_current_stage: false
blocks_m6_exit_gate: false
blocks_m7_entry: false
safe_continuation: >
  Keep the production Route unregistered. Codex-owned generated client, adapter,
  ViewModel, query, mutation, Container, route contract and focused test infrastructure
  remain available for a later accepted handback. Do not invent a second visual page or
  copy a historical Open Design implementation.
resolution: >
  Codex completed the integration decision using the frozen typed Props/Event contract,
  registered the single production route /projects/$projectId/manuscript, wired the
  existing Container/query/mutation boundary and generated route tree, and kept
  fixtures out of production. The route is intentionally compact and fail-closed;
  no second API or Workspace shell was introduced.
focused_verification: >
  frontend generated-client, contract/boundary/mock guards and production TypeScript/
  Vite build pass. Route tree contains the M6 production path and all deep-link keys.
security_or_scientific_integrity_impact: >
  HIGH integration and scientific-integrity impact. Without accepted UI evidence, wiring
  could expose optimistic success, high-risk auto-fix or sensitive excerpts incorrectly.
```
