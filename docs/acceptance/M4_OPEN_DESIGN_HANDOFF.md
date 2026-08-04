# M4 Open Design Handoff

```text
Milestone: M4 Data Quality and Versioning
Stage: 4
Assessment date: 2026-08-04 (Asia/Shanghai)
Workspace: frontend/src/features/data-workspace
Route draft: /projects/$projectId/data
READY_FOR_OPEN_DESIGN=YES
READY_FOR_CODEX_INTEGRATION=YES
CODEX_STAGE_4_5_RESULT=PASS
PRODUCTION_INTEGRATION_COMPLETE=NO
```

## 1. Handoff Boundary

The single product surface is `DataWorkspace`; Dataset upload/identity/worksheet/preview, field dictionary, quality facts, CleaningPlan/Approval, Transformation/Job and lineage belong to this one workspace. Open Design must not split these into unrelated product entrances or infer server state from navigation, clicks or fixture behavior.

The minimal preview is registered in the existing `frontend/src/design-preview/DesignPreviewWorkbench.tsx`. It is a contract preview only. Events append safe intent summaries and do not change fixtures, approve plans, complete Jobs or persist uploaded files.

## 2. Frozen Paths

Workspace UI entry:

- `frontend/src/features/data-workspace/ui/DataWorkspace.tsx`
- `frontend/src/features/data-workspace/ui/data-workspace.css`
- `frontend/src/features/data-workspace/ui/contracts.ts`

Codex integration surface:

- `frontend/src/features/data-workspace/model.ts`
- `frontend/src/features/data-workspace/mappers.ts`
- `frontend/src/features/data-workspace/queries.ts`
- `frontend/src/features/data-workspace/mutations.ts`
- `frontend/src/features/data-workspace/containers/DataWorkspaceContainer.tsx`
- `frontend/src/features/data-workspace/fixtures/index.ts`
- `frontend/src/features/data-workspace/route-contract.ts`
- `frontend/src/api/adapter/index.ts`
- `frontend/src/api/generated/**`

## 3. Props And Events

`DataWorkspaceWorkspaceProps` contains only:

- `content: Loadable<DataWorkspaceViewModel>`
- `pendingAction`
- `mutationError`
- `onRetry`
- `onEvent`

Frozen user-intent events:

- `upload-dataset`, `select-worksheet`, `update-dataset-identity`, `update-column`
- `select-version`, `compare-versions`
- `run-quality`, `acknowledge-issue`, `ignore-issue`
- `create-plan`, `update-plan`, `preview-plan`, `request-approval`, `execute-plan`
- `retry-job`

Events do not promise success. `select-version` and `compare-versions` are navigation intents pending production route wiring. Buttons must use projected capabilities and `disabledReason`; absence of permission or allowed action is denial, not an invitation to infer.

## 4. ViewModel Facts

The mapper explicitly separates:

- known status from future/unknown status and `permissionsKnown` from granted capability;
- upload/Job acceptance from DatasetVersion `AVAILABLE` and business completion;
- Original/current/parent/invalidated version identity, hashes and persisted lineage;
- inferred type from confirmed type and sensitive candidate from user confirmation;
- quality clues such as extreme values from confirmed errors;
- Preview facts from Approval and Transformation results;
- Approval pending/approved/rejected/expired/stale;
- Job queued/running/completed/failed/retryable.

Unknown enum values use degraded styling and disable writes. No-disclosure errors map to the shared not-found/forbidden presentation without revealing project membership.

## 5. Typed Fixtures

`dataWorkspaceFixtures` covers ready, loading, empty, error, forbidden/no-disclosure, read-only, permissions unknown, upload pending/failure, CSV ready, XLSX visible/hidden worksheet selection, invalidation, quality queued/running/completed/failed/unknown, missing/duplicate/extreme/sensitive issues, Plan draft/needs-input/Preview ready, Approval pending/rejected/stale, If-Match conflict, Transformation queued/running/completed/failed/retryable, future enums, long content, and desktop/tablet/mobile light/dark preview labels.

Fixture data is bounded and synthetic. Masked values remain masked in the UI and Event Log. A fixture showing a completed state is not a mock server and must not be imported into a production route.

## 6. Route Contract Draft

Frozen path: `/projects/$projectId/data`.

Stage 5 production search keys are `dataset`, `version`, `qualityRun`, `plan`, `approval`, `job`, `compareWith` and `view`. Stage 4 deferred registration; Codex Stage 5 has now registered and validated the production route.

## 7. Ownership

Open Design may modify only:

- `frontend/src/features/data-workspace/ui/**` implementation and UI CSS;
- explicitly authorized shared pure display components;
- the M4 display branch of Design Preview without changing its event sanitizer, module controller or fixture semantics.

Codex-protected paths remain:

- model, mappers, queries, mutations, containers, fixtures and `ui/contracts.ts`;
- generated client, adapter, route/search contract and production routes;
- scripts and contract tests;
- backend code and OpenAPI generation.

Open Design must not import generated/adapter/query/mutation/container modules into `ui/**`, add network calls, derive permissions, mutate fixture state to simulate success, or log full rows, sensitive values, file contents or action parameters.

## 8. Known Contract Gaps

- `M4-ISSUE-0014`: M4 backend routes lack explicit response models, leaving many generated responses `unknown`. The adapter validates envelope presence and owns temporary structural DTOs; final OpenAPI hardening is required before M4 Exit.
- `M4-ISSUE-0015`: no formal version-history list or Transformation-detail read endpoint exists. Version navigation and Transformation detail remain integration pending.
- Stage 5 completed Approval/Job loading and route deep-link wiring. Formal version-history and standalone Transformation detail remain Stage 6 work.

## 9. Focused Gate

Required handoff evidence is the formal generated-client consistency check, TypeScript production build, M4 fixture contract, UI ownership boundary and production-mock guard. Full Playwright and clean-room are intentionally deferred by the stage instruction.

```text
READY_FOR_OPEN_DESIGN=YES
READY_FOR_CODEX_INTEGRATION=YES
CODEX_STAGE_4_5_RESULT=PASS
CODEX_STAGE_5_ENTRY=ALLOWED
PRODUCTION_INTEGRATION_COMPLETE=NO
NEXT_STAGE_EXECUTED=NO
```

## 10. Codex Stage 4.5 Readiness Repair

Codex synchronized the accepted Open Design production UI and browser suite into the formal
repository and resolved all issues that blocked Stage 5 entry. The contract now includes a strict
five-variant Cleaning Action projection, corrected empty/XLSX/Plan capabilities and a formal
parent-Version comparison capability. OpenAPI/adapter format drift is also closed.

Codex, rather than Open Design, owns the final revalidation for this handoff. The full 30-fixture,
three-viewport, Light/Dark matrix and focused interaction/contract suite pass `22/22`; format, lint,
fixture, boundary, production-mock, generated-client and build gates all pass.

Remaining `M4-OD-0009` duplicate-Issue pixel coverage and `M4-OD-0015` single-file mirror generation
are explicitly non-blocking. Main milestone issues `M4-ISSUE-0014/0015` still require their planned
Stage 5/6 production API/read-model work and are not represented as completed here.

## 11. Codex Stage 5 Production Integration

Codex registered the single `/projects/$projectId/data` production Route and kept the accepted
Workspace as the injected View. Search validation and restoration now cover Dataset, Version,
QualityRun, CleaningPlan, Approval, Job, comparison and the local Workspace view. Formal relations
are rechecked in the query layer; command success updates URL state only from server response IDs
and then invalidates/refetches the workspace cache.

The real PostgreSQL/API/worker vertical chain passes through upload, identity/field confirmation,
quality, typed CleaningPlan Preview, Approval, Transformation, derived Version and comparison.
Focused production Route Playwright passes, including approval-only refresh, cross-Dataset rejection,
formal confirmation payload and 390px Light/Dark rendering.

`M4-ISSUE-0014` and the remaining read-model portion of `M4-ISSUE-0015` stay open for Stage 6. No
version-history list or Transformation detail is inferred in the browser.

```text
M4_STAGE_5_RESULT=PASS_WITH_ISSUES
PRODUCTION_ROUTE_INTEGRATION=PASS
REAL_API_VERTICAL_E2E=PASS
READY_FOR_M4_STAGE_6=YES
NEXT_STAGE_EXECUTED=NO
```
