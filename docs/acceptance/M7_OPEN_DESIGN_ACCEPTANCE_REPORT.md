# M7 Open Design Acceptance Report

Date: 2026-08-06 (Asia/Shanghai)
Stage: Open Design reacceptance after Codex contract corrections
Result: PASS

```text
OPEN_DESIGN_STAGE_RESULT=PASS
READY_FOR_CODEX_INTEGRATION=YES
PRODUCTION_INTEGRATION_COMPLETE=NO
NEXT_STAGE_EXECUTED=NO
```

## 1. Accepted Surface

- `frontend/src/features/evidence-workspace/ui/EvidenceWorkspace.tsx`
- `frontend/src/features/evidence-workspace/ui/evidence-workspace.css`
- `EvidenceWorkspace` and `EvidenceWorkspaceVisualProps` from `ui/index.ts`
- Design Preview integration in `DesignPreviewWorkbench.tsx`
- Graph, Claims, Audits and Exports views
- Desktop, tablet, 390px mobile, Light/Dark and table fallback

The UI continues to consume only frozen Props, Events and RECA-owned ViewModels. It does not
persist graph edges, infer completeness/readiness, approve Export, fabricate Job/Package success or
expose denied objects.

## 2. Original Visual Baseline

The accepted Stage-3 baseline remains valid:

| Viewport | Light | Dark | Total |
| --- | ---: | ---: | ---: |
| 390x844 | 62 PASS | 62 PASS | 124 |
| 1024x768 | 62 PASS | 62 PASS | 124 |
| 1440x900 | 62 PASS | 62 PASS | 124 |
| Total | 186 PASS | 186 PASS | 372 PASS |

The original matrix reported zero root horizontal overflow and zero browser console errors. It
covered loading/error/permission/unknown, partial and 500-node graph, table fallback, long content,
readiness/Approval/Job/Package/Manifest and Light/Dark states. Those screenshots remain fixture
Preview evidence and are not production data.

## 3. Corrected Contract Reacceptance

The four former integration blockers now have authoritative typed projection and UI consumption:

- `M7-OD-0003`: Audit-associated Job is projected separately from the Export Job and displayed as
  read-only Audit execution context.
- `M7-OD-0004`: immutable paginated ReproPackage history exposes version identity, Artifact IDs,
  size, SHA-256, selected version and incomplete-page state.
- `M7-OD-0005`: retryable failed Export and cancellable running Export fixtures enable only their
  corresponding server-authorized Event.
- `M7-OD-0006`: `link-suggested` enables formal confirmation with Link ID and lock version.

Focused Design Preview Playwright reacceptance passed 4/4 tests. It exercised all four corrected
contracts and repeated their bounded rendering at real 1440x900, 1024x768 and 390x844 browser
viewports across Light/Dark representatives. Root horizontal overflow was zero. The current Vite
development Preview loaded successfully, resolving the prior non-blocking environment item
`M7-OD-0002`.

## 4. Interaction And Authority

- Link confirmation remains a formal Event; React Flow connect/reconnect cannot create a Link.
- Audit Job and Export Job remain distinct; Audit retry is not fabricated.
- Retry and cancel require known status, capability, retryability/cancellability and Job identity.
- Package history is read-only and preserves immutable versions.
- Mutation success still depends on server response plus invalidation/refetch.
- Unknown permissions/status, stale Approval, denied scope and tampered Package remain fail closed.

## 5. Current Quality Gates

```text
frontend format:check                    PASS (293 files)
frontend lint                            PASS (297 files)
M7 fixture semantic guard               PASS (8 tests, 125 assertions)
UI ownership boundary                    PASS (4 tests + repository scan)
production mock boundary                 PASS (6 tests + repository scan)
generated client consistency             PASS (4 generated files)
Stage-4 Route contract guard             PASS (2 tests, 13 assertions)
TypeScript/Vite production build         PASS
Open Design corrected-contract browser   PASS (4 tests)
```

## 6. Ownership And Remaining Work

Open Design acceptance now permits Codex production integration. Codex still owns the production
Route/Container, real API/cache, permission revalidation, PostgreSQL/Worker/MinIO and longitudinal
browser E2E. This READY does not mean those tasks or the M7 Exit Gate are complete.

No unresolved Open Design BLOCKER, CRITICAL, HIGH or MEDIUM issue remains. No Commit, Tag or Push
was created.

```text
OPEN_DESIGN_STAGE_RESULT=PASS
READY_FOR_CODEX_INTEGRATION=YES
PRODUCTION_INTEGRATION_COMPLETE=NO
NEXT_STAGE_EXECUTED=NO
```
