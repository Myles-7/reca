# RECA M2 to M3 Handoff

```text
M3_ENTRY=PENDING_FINAL_COMMIT
```

## Status and Basis

Stage 9 implementation and full verification are complete, but M3 entry is not
allowed until the authorized final commit and commit-scoped fresh-checkout gates
close `M2-ISSUE-0001`. This document freezes consumable boundaries only; it does
not authorize M3 implementation.

## M2 Migration, API, and Frontend Baseline

- Migration head: `0012_document_upload`.
- Verified worktree baseline: branch `feat/m2-research-literature`, baseline HEAD
  `ac6447c081c881fedb818525871a8bd100410cb5`, with uncommitted M2/Open Design
  changes. Stage E must replace this with the real implementation SHA.
- M2 API resources: ResearchQuestion/Version, QueryPlan,
  LiteratureSearchRun/Candidate, LiteratureRecord, Document, and DocumentPage.
- Production frontend routes: research question, query plan detail, literature
  workspace, and document detail, using the generated client, adapters,
  ViewModels, Containers, and Open Design workspaces.
- Final Stage D evidence: backend 248 passed/2 opt-in Live skipped; frontend and
  clean-room Playwright each passed 114/114; migration and quality gates passed.

## Reusable M2 Entities and Invariants

- A confirmed ResearchQuestionVersion is the stable QueryPlan input.
- Candidate is not LiteratureRecord; import is explicit and project-scoped.
- Document is not LiteratureRecord; their relationship is server-validated.
- Original PDF Artifact is immutable and content-addressed.
- Upload success is not parse success; parsing is Job/Worker owned.
- Unknown state, permission, allowed action, and retryability fail closed.
- Recorded, Cache, Degraded, and Live provenance remain distinct.

## DocumentPage, DocumentChunk, and Provenance

- DocumentPage provides project/document ownership, stable positive page number,
  optional printed label, text, dimensions, and parser metadata.
- DocumentChunk provides project/document ownership, page range, section path,
  deterministic chunk index, content, SHA-256 content hash, and metadata.
- GROBID may provide section/coordinate metadata; pypdf fallback must not invent
  sections, coordinates, or high confidence.
- Job, ProcessingRun, parser type/version, input/parameter hashes, implementation
  metadata, and immutable intermediate Artifact references preserve provenance.
- Page/Chunk fields are M3 inputs, not EvidenceSpan and not verified evidence.

## Artifact, Job, Approval, and Audit Reuse Boundary

- Reuse the M1/M2 project-scoped services and server-projected actions.
- Reuse immutable Artifact storage for source PDF and deterministic intermediates.
- Reuse Job/ProcessingRun for extraction work; do not create a second lifecycle.
- Reuse ApprovalRecord only where the formal M3 contract requires approval.
- Append AuditLog events; never rewrite provenance or scientific history.

## Explicitly Not Implemented in M2

- LiteratureExtraction and LiteratureExtractionField.
- Fixed ten-field extraction.
- EvidenceSpan and verified source ranges.
- LiteratureDecision.
- TopicCandidate and topic generation runs.
- Literature matrix and evidence-set analysis.
- PDF.js EvidenceSpan highlighting.
- OCR and formal Agent orchestration.

## M2 Safe Deferred and Low Issues

- `M2-ISSUE-0008`: LOW development-only Babel advisory, revalidated and
  explicitly disclosed by the Exit Gate.
- Host-local Python tool availability may remain deferred when pinned Compose and
  clean-room verification are complete and reproducible.
- Independent Celery delivery of an M2 domain handler was not run as a separate
  gate. Registered handler Job/ProcessingRun lifecycle and clean-room Worker
  health passed; M3 must not describe that as separate-process domain delivery.

## M3 Must-Preserve Regression Tests

- Project isolation and no-disclosure for every resource and cross-object link.
- Candidate/record and Document/record separation.
- Immutable Artifact binding and content hash verification.
- Confirmed-version -> QueryPlan integrity and optimistic concurrency.
- Cache/Recorded/Degraded/Live provenance separation and zero fabrication.
- Document upload/parse separation, no-fallback behavior, pypdf LOW degradation.
- Stable page numbering, chunk hashes, section/coordinate non-fabrication.
- Formal Job retryability, ProcessingRun provenance, Approval, and Audit behavior.
- Generated-client consistency, production mock guard, UI ownership boundaries,
  route refresh recovery, and unknown-state fail-closed behavior.

## Reusable Verification Commands

```text
docker/Compose project environment: ruff format --check, ruff check, mypy app,
pytest -q, alembic upgrade head (empty and repeated), alembic check
bun run --cwd frontend format:check
bun run --cwd frontend lint
bun run --cwd frontend check-generated-client
bun run --cwd frontend check:ui-boundaries
bun run --cwd frontend check:production-mocks
bun run --cwd frontend build
CI=1 RECA_PLAYWRIGHT_PORT=<isolated-port> bun run --cwd frontend test:shell
PowerShell clean-room: scripts/m0-acceptance.ps1
```

M3 may reuse the existing auth/private API test utilities, Recorded OpenAlex and
GROBID inputs, authorized PDF fixtures, generated client/adapter boundary, and
Job/ProcessingRun test helpers. It must not create a second fixture framework.

## M3 Entry Blockers

- M2 Exit Gate is `FAIL/READY_FOR_FINAL_COMMIT_VERIFICATION`.
- `M2-ISSUE-0001` requires a final commit and clean-checkout evidence; creating
  that commit requires explicit user authorization.
- `M2-S9-002` remains a safe LOW host-tooling deferral because pinned Compose
  and clean-room verification are reproducible.
