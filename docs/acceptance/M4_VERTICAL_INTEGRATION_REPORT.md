# M4 Stage 5 Vertical Integration Report

```text
Milestone: M4
Stage: 5
Assessment date: 2026-08-04 (Asia/Shanghai)
Result: PASS_WITH_ISSUES
Final M4 Exit Gate executed: NO
```

## Scope And Evidence Boundary

Stage 5 registered the single production route `/projects/$projectId/data`, connected the accepted
Data Workspace through generated client, adapter, query/mutation and Container layers, and built a
real M4 API/worker vertical test. No fixture is imported by the production route.

Evidence types are deliberately separated:

- `REAL`: FastAPI `TestClient`, formal services, PostgreSQL, API envelopes, worker dispatcher and
  deterministic worker execution in an isolated Compose database named `reca_m4_stage5_test`.
- `MOCK TRANSPORT`: focused Playwright uses schema-shaped API responses to exercise the production
  Route/Container/browser behavior. It is not counted as real domain success.
- `FIXTURE`: Open Design fixtures were not used for Stage 5 production success evidence.

## Production Integration

- Registered `/projects/$projectId/data` without adding another product shell.
- Search keys: `dataset`, `version`, `qualityRun`, `plan`, `approval`, `job`, `compareWith`, `view`.
- Invalid UUIDs and unknown views are ignored safely.
- QualityRun, CleaningPlan and Approval deep links restore their formal upstream Version/Dataset.
- Cross-project and cross-Dataset/Version/Run/Plan/Approval relationships return a no-disclosure
  style 404 error.
- Selection events update URL state; command success updates URL only from returned server IDs.
- Mutations invalidate/refetch the workspace cache. No optimistic business success was added.
- `view` is URL-restorable UI state. It is not persisted as a domain fact.
- DatasetColumn confirmation now explicitly sends `confirmation_status=CONFIRMED` or
  `UNCONFIRMED`; setting a type alone no longer masquerades as formal review.

The backend still has no Dataset version-history collection or standalone DataTransformation detail
read. The Workspace therefore does not invent either projection. See `M4-ISSUE-0015`.

## Real Vertical Chain

Test: `backend/tests/integration/test_m4_vertical_demo.py`.

Input:

```text
file: m4-stage5.csv
media type: text/csv
bytes: 394
sha256: 8c127e55f619b16d641787e4784d16a496733a86575d193b5073482ed89e4964
storage: isolated in-memory ObjectStorage adapter used by formal Artifact services
database: real PostgreSQL, isolated reca_m4_stage5_test
worker: formal Job claim and deterministic quality/transformation worker functions
```

Observed state chain:

```text
Project CREATED
-> CSV Dataset + Original DatasetVersion AVAILABLE
-> Dataset identity lock 1 -> 2
-> DatasetColumn UNCONFIRMED -> CONFIRMED
-> DataQualityRun/Job accepted -> COMPLETED
-> masked sensitive Issue plus quality Issues persisted
-> CleaningPlan DRAFT -> READY after deterministic Preview
-> execute before Approval rejected with APPROVAL_REQUIRED
-> Approval PENDING -> APPROVED
-> Transformation/Job accepted once; duplicate Idempotency-Key replayed
-> Transformation/Job COMPLETED
-> derived DatasetVersion AVAILABLE with parent/source lineage
-> Dataset current pointer moved to derived Version
-> target quality recheck persisted
-> pairwise parent/child comparison returned formal lineage
```

The source Artifact bytes and SHA-256 remain unchanged. HTTP `202 Accepted` is not treated as
completion; the test waits for the worker and verifies persisted terminal Job, Transformation,
DatasetVersion and comparison facts.

## Focused Coverage

Backend focused suite: `11/11 PASS`.

```text
backend/tests/api/routes/test_datasets.py
backend/tests/api/routes/test_data_quality.py
backend/tests/api/routes/test_cleaning.py
backend/tests/integration/test_m4_vertical_demo.py
```

This covers CSV upload/hash/preview, XLSX multi-sheet and hidden-sheet acknowledgement, stale
If-Match, duplicate Idempotency-Key, Viewer/Reviewer/Owner permissions, outsider 404, failed Job
facts, stale worker parameters, unapproved execution and deterministic lineage. Editor capability is
covered by the same project action matrix used by the production mapper; a separate pixel role
matrix was not added in Stage 5.

Frontend focused suite: `10/10 PASS`.

```text
frontend/tests/projects-m4-data-workspace-contracts.spec.ts
frontend/tests/projects-m4-production-route.spec.ts
```

It covers search validation, refresh, view persistence, approval-only restoration, cross-Dataset
rejection, formal field-confirmation payload, 390px root overflow and representative Light/Dark
production Route rendering. Production build passes.

Screenshots, using mock transport against the production Route:

```text
D:/桌面/Recas/output/playwright/qa/m4-stage5/production-route-mobile-light.png
D:/桌面/Recas/output/playwright/qa/m4-stage5/production-route-mobile-dark.png
```

Both are 390px viewport evidence with zero page-root horizontal overflow. They are visual evidence,
not proof of backend completion.

## Issues

- `M4-ISSUE-0016` HIGH, resolved: frontend omitted formal DatasetColumn confirmation status.
- `M4-ISSUE-0017` LOW, resolved: focused Cleaning test used an unscoped global Version assertion.
- `M4-ISSUE-0014` HIGH, open: M4 response models remain incomplete in OpenAPI; adapter runtime
  checks remain the temporary fail-closed boundary.
- `M4-ISSUE-0015` MEDIUM, open: version-history and Transformation-detail read models are absent.

No new Secret disclosure, cross-project disclosure, optimistic success, source Artifact mutation or
destructive migration issue was observed.

## Stage Decision

```text
M4_STAGE_5_RESULT=PASS_WITH_ISSUES
PRODUCTION_ROUTE_INTEGRATION=PASS
REAL_API_VERTICAL_E2E=PASS
FOCUSED_PLAYWRIGHT=PASS
M4_EXIT_GATE_EXECUTED=NO
READY_FOR_M4_STAGE_6=YES
NEXT_STAGE_EXECUTED=NO
```
