# RECA M2 Completion Report

This report records M2 completion evidence. Product, data-model, API,
state-machine, security, and milestone documents remain authoritative.

## Decision

```text
M2_EXIT_GATE=PASS
M2_IMPLEMENTATION=COMPLETION_APPROVED
M3_ENTRY=ALLOWED
implementation_sha=87e0f4ae27448b422b49c6354a188925a51e5cd7
migration_head=0012_document_upload
assessment_date=2026-08-03 Asia/Shanghai
```

## Completed Scope

- Confirmed ResearchQuestionVersion through QueryPlan, Recorded literature
  search/cache, candidate import, DOI deduplication, immutable PDF Artifact,
  Document, DocumentPage, DocumentChunk, parser and Job/ProcessingRun lineage.
- Production Research Question, Query Plan, Literature, and Document Routes use
  the generated client/adapter and server-projected permissions/actions.
- Project isolation, no-disclosure, idempotency, optimistic concurrency,
  approval, audit, upload/parse separation, retryability, and fail-closed
  unknown behavior are preserved.

## Commit-Scoped Evidence

- Detached fresh checkout Prompt assets: LF PASS; manifest/hash tests 6/6 PASS.
- Clean-room `reca-m2-stagee-final-cleanroom-20260803-083258`: all functional,
  migration, backend, frontend, Playwright 114/114, Secret, and Python audit
  gates PASS; Node audit PASS WITH LOW ADVISORY.
- Production vertical `reca-m2-stagee-final-vertical-20260803-083618`: 1/1 PASS
  through production Routes, real API/PostgreSQL/MinIO, registered Worker
  handlers, refresh recovery, immutable upload, parse, and DocumentPage text.
- Stage D full backend: 248 passed, 2 opt-in Live tests skipped; strict mypy and
  Ruff passed; migration head and metadata check passed.

## Accepted Non-Blocking Limitations

- `M2-ISSUE-0008` remains OPEN/LOW for the development-only Babel advisory.
- Independent Celery broker/process delivery of a domain handler was NOT RUN;
  registered handler lifecycle and clean-room Worker health passed.
- Recorded, Cache, Degraded, and Live remain distinct. Live compatibility
  evidence is not the deterministic M2 gate.

## Scope Boundary

M2 does not implement LiteratureExtraction, the fixed ten fields,
EvidenceSpan, LiteratureDecision, TopicCandidate, the literature matrix,
PDF.js evidence highlighting, OCR, evidence-set analysis, or a formal Agent.
Those items remain governed by M3 or later milestone contracts.
