# M7 Open Design Implementation Plan

Date: 2026-08-06 (Asia/Shanghai)
Stage: Open Design Stage 3
Status: COMPLETED AND REACCEPTED

```text
OPEN_DESIGN_STAGE_RESULT=PASS
READY_FOR_CODEX_INTEGRATION=YES
PRODUCTION_INTEGRATION_COMPLETE=NO
NEXT_STAGE_EXECUTED=NO
```

## 13. Stage 3 Full Acceptance

Stage 3 stopped feature expansion, added visible disabled reasons across Link, Audit, Export,
Approval/Job and download commands, then completed full fixture and interaction acceptance.

Execution-time fixture count was 62. All 372 combinations passed:

```text
62 fixtures x 3 viewports x 2 themes = 372 PASS / 0 FAIL
```

The focused interaction suite completed 29 checks with zero console errors. It covered view and
initialView projection, React Flow controls, table fallback, Link Dialogs, Audit/AI separation,
Readiness and Approval, download intent, pending/conflict authority, fail-closed states, Manifest,
reduced motion and the 500-node fixture.

The remaining gaps are Codex-owned and protected from UI repair:

- Audit-associated Job projection;
- immutable Package history array;
- allowed retry/cancel fixture combinations;
- `link-suggested` confirm capability combination.

Because these gaps block complete production wiring or Stage 3 interaction evidence, readiness
remains false even though all independently testable pure UI combinations pass.

## 14. Contract Reacceptance

Codex subsequently added the Audit Job projection, immutable paginated Package history,
retry/cancel fixtures and the allowed Suggested-Link confirmation combination. Open Design
revalidated those changes without altering backend, generated, adapter, model, mapper, query,
mutation, Container, Route or fixture ownership boundaries.

Current evidence:

- M7 fixture guard: 8 tests, 125 assertions PASS;
- corrected-contract Design Preview Playwright: 4/4 PASS;
- real 1440x900, 1024x768 and 390x844 viewport representatives: PASS, root overflow 0;
- format 293 files, lint 297 files, boundaries, production mocks, generated client, Stage-4 Route
  contract and production build: PASS;
- current Vite development Preview: PASS.

No unresolved Open Design integration blocker remains. Production integration and M7 Exit remain
Codex-owned later facts.

```text
OPEN_DESIGN_STAGE_RESULT=PASS
READY_FOR_CODEX_INTEGRATION=YES
PRODUCTION_INTEGRATION_COMPLETE=NO
NEXT_STAGE_EXECUTED=NO
```

## 1. Recovery Baseline

| Fact | Observed value |
| --- | --- |
| Formal repository | `D:\桌面\Recas\reca` |
| Formal branch | `feat/m2-research-literature` |
| Formal HEAD | `951d872aa3567c2393e5ae7cad2b1900b55999d4` |
| Upstream | `origin/feat/m2-research-literature` |
| Formal worktree state | M7 Codex Stage 0-3 changes present and intentionally left dirty |
| Migration head | `0018_m7_evidence_export.py` in the formal untracked M7 input |
| Handoff | `READY_FOR_OPEN_DESIGN=YES` |
| Design worktree | `D:\桌面\Recas\reca-m7-open-design` |
| Design branch | `design/m7-evidence-workspace` |
| Design baseline | same HEAD `951d872aa3567c2393e5ae7cad2b1900b55999d4` |
| Recovery | Reopen the design worktree; do not reset, clean, stash or overwrite the formal M7 worktree |

The formal worktree was not modified during implementation. Frozen Codex inputs were copied into
the isolated worktree with matching SHA-256 values. Final Open Design-owned files are synchronized
back only after verification.

## 2. Controlled Input Manifest

All destination hashes matched their source hashes at synchronization time.

| Input | Bytes | SHA-256 |
| --- | ---: | --- |
| `bun.lock` | 111337 | `0df40be2e328c4277e3cb9f4ec7e457759e5579f395e66ce88d662509dce1121` |
| `frontend/package.json` | 3554 | `903829f0d26ef0c2ea3c3563c194dcc786022d6031470d862fd2dace67022d04` |
| `frontend/openapi.json` | 932514 | `c94111d0fb758a9aeec534fbcb4232c86b12f3c4d12d6d791c89faa99e068230` |
| `frontend/src/api/adapter/index.ts` | 73477 | `eff37ac2636dd24f18205319970a8488d78b181790a106f8119fa28d0106a5ad` |
| `frontend/src/api/generated/index.ts` | 79767 | `995d727d8deeb9731c1bf5c259084e5d6061d5bcaa39152ea07b3b3e1f15068d` |
| `frontend/src/api/generated/sdk.gen.ts` | 173205 | `9d531e19de10b74400ef558e62081d12ae7946a5affa5a0a57a4506cb06c0cc8` |
| `frontend/src/api/generated/types.gen.ts` | 376790 | `03f23d85075b62961465c2707b2eaf2fda03e27dc1686690fbf1404d996ef022` |
| `frontend/scripts/check-m7-fixtures.test.ts` | 6539 | `6716d5e37ab0fde483698176677b53e1d5eed648f9e7a34ad71e4ef4445f6557` |
| `evidence-workspace/model.ts` | 7767 | `e7a28326bf22e7d1781c40f4e5eb52de0c847ede9846d17cb0f87d8c7b8ae585` |
| `evidence-workspace/mappers.ts` | 22550 | `a2bcaccb839bc8a0f9f0644c0ea98fb82e18dff26292c5d5516bf079ad31ce96` |
| `evidence-workspace/queries.ts` | 5536 | `8d359445391fb1251c48d6f79a1cf0fde1d9be8005121c9132c587699d57f09a` |
| `evidence-workspace/mutations.ts` | 6869 | `304ec3ccddf4b42a53dd6fa7d3e037748e984caf18884cf68ad597ed66057d8d` |
| `evidence-workspace/route-contract.ts` | 1602 | `4fc264ff25a3f5b7d9843375098f232081f361103d7cbb6f5a7f95124e96a457` |
| `evidence-workspace/containers/EvidenceWorkspaceContainer.tsx` | 2238 | `b478618c055d671f32d92d04fa28fb237189a4472d5599e1d2b41a9207639b2f` |
| `evidence-workspace/fixtures/index.ts` | 26042 | `4508caccbf7e30a621a165fbe5e336f92ea2627bfe0a69d7682880dd0aa54306` |
| `evidence-workspace/ui/contracts.ts` | 1944 | `2d54a7278486aeb30938dfa4995739ed558e356530e10ea7fcb968d7fc6fb606` |

The handoff and Codex M7 plan/issue documents were also copied with identical hashes and retained
as read-only authority inputs.

## 3. Ownership Boundary

Open Design-owned implementation:

- `frontend/src/features/evidence-workspace/ui/EvidenceWorkspace.tsx`
- `frontend/src/features/evidence-workspace/ui/evidence-workspace.css`
- `frontend/src/features/evidence-workspace/ui/index.ts`
- the M7 display branch in `frontend/src/design-preview/DesignPreviewWorkbench.tsx`
- this plan and `M7_OPEN_DESIGN_ISSUE_REGISTER.md`

Codex-protected inputs were not edited: backend, package/lock, OpenAPI/generated/adapter, model,
mapper, query, mutation, route, Container, fixtures, `ui/contracts.ts` and the fixture guard.
No production Route, API call, optimistic business state, Commit, Tag or Push was created.

## 4. Fixture Grouping

The 62 frozen fixtures are grouped for the staged UI without copying or rewriting facts:

| Group | Count | Coverage |
| --- | ---: | --- |
| Graph, edge, Link and evidence scope | 13 | empty through full chains; contradict/qualify; suggested/invalidated/unknown; denied/missing/stale |
| Completeness | 6 | satisfied, missing, restricted, conflicted, unknown, not applicable |
| Audits | 7 | queued, running degraded, review, insufficient, conflicted, failed, unknown |
| Graph scale and access | 5 | partial cursor, 500 nodes, permissions unknown, read-only, route fallback |
| Export readiness | 6 | ready, license blocker, sensitive warning, missing, invalidated, unknown |
| Export state | 7 | draft through cancelled |
| Approval | 5 | pending, approved, stale, rejected, expired |
| Package and Manifest | 4 | tampered, unavailable, version history, long restricted paths |
| Transport, responsive and long content | 9 | mutation pending/conflict, 3 descriptors, long content, loading, empty, error |

Stage 1 implements Graph, Claims and Completeness. Audits and Exports retain truthful navigation
surfaces only; their full contents and interactions remain Stage 2.

## 5. Information Architecture And Local State

- Header: project identity, graph completeness/degradation/permission state, refresh intent.
- Left pane: Claim queue with local search and risk filtering.
- Main pane: React Flow Graph or complete Node/Edge table fallback; Claims and Completeness.
- Inspector: selected Node, Edge or stored Link facts; tablet/mobile opens the same content in a
  Radix Dialog surface.
- Local-only state: view, graph/table mode, selection, filters, React Flow positions/pan/zoom,
  Dialog drafts and Inspector visibility.
- Formal Events emitted in Stage 1: `create-evidence-link`, `confirm-evidence-link`,
  `invalidate-evidence-link`, `expand-graph-node`, `refresh-graph`, `refresh`.
- No Event changes fixture facts. Invalidation requires a reason; Dialog close and submit both
  leave the formal Link status unchanged until server projection changes.

## 6. Graph Decisions

- `canvasNodes` and `canvasEdges` are the only canvas source; connect/reconnect remain disabled.
- Stored Link edges and derived provenance edges use text, icons, accessible labels and distinct
  rendering, not color alone.
- Partial, cursor, degraded, scope notices and limitations stay visible above the canvas/table.
- The 500-node fixture uses compact default nodes, React Flow visible-element rendering and
  progressive server facts; it does not create client scientific relationships.
- Node and Edge tables expose type, relation, source kind, status, risk, scope and stale/
  invalidated facts. Rows are keyboard selectable and open the same Inspector.
- Denied scope creates only the anonymous scope notice already present in the fixture; no denied
  row, object ID or count is synthesized.

## 7. Responsive And Accessibility Decisions

- Desktop: stable three-pane layout with independent pane scrolling.
- Tablet: left + main surfaces; Inspector is available through a focus-managed Dialog.
- Mobile: a single main surface; desktop panes are not compressed into 390px.
- Visible focus, icon plus text status, named controls and keyboard table rows are present.
- Radix Dialog provides focus trap, Escape and trigger focus restoration.
- Component CSS includes `prefers-reduced-motion` handling.
- Long Claim text, UUID/hash metadata and limitations wrap or scroll inside owned panes.

## 8. Stage 1 Verification

Commands completed:

```text
bun run --cwd frontend check:m7-fixtures            PASS (7 tests, 104 expects)
bun run --cwd frontend check:ui-boundaries          PASS
bun run --cwd frontend check:production-mocks       PASS
bun run --cwd frontend build                        PASS
bunx tsc -p frontend/tsconfig.build.json --noEmit   PASS
```

Browser evidence:

- 5 representative screenshots: desktop Graph Light, tablet partial Graph Dark, mobile denied
  Graph Light, tablet conflicted Completeness Light and mobile long Claim Dark.
- Matrix metrics: 5/5 PASS, no root horizontal overflow, no clipped non-canvas controls and zero
  console errors.
- Interaction smoke: Table keyboard selection, permissions unknown fail-closed, Dialog Escape/
  focus restore/state authority and `graph-large-500` non-empty selection all PASS.
- `graph-large-500`: projected 500 nodes; 488 visible DOM nodes under React Flow virtualization;
  selection opened the same Inspector; zero console errors.

Evidence paths:

- `output/playwright/qa/m7-stage1/results.json`
- `output/playwright/qa/m7-stage1/interactions.json`
- `output/playwright/qa/m7-stage1/screenshots/`
- root Open Design artifact: `reca-live-design-preview.html`

## 9. Stage Boundary

Stage 2 and Stage 3 were not executed. Audits, Exports, Approval, Job, Manifest and Package remain
out of Stage 1. Production integration and readiness remain false until the later gates complete.

```text
OPEN_DESIGN_STAGE_RESULT=PASS
HISTORICAL_READY_FOR_CODEX_INTEGRATION=NO
PRODUCTION_INTEGRATION_COMPLETE=NO
NEXT_STAGE_EXECUTED=NO
```

## 10. Stage 2 Implementation

Stage 2 replaced the Audits and Exports boundary surfaces without changing frozen ViewModels,
fixtures, Events, Container, Route, API, mapper, query or mutation code.

Implemented views and interactions:

- Audits: execution status and deterministic outcome remain separate; queued/running state,
  provider degradation, source/result hashes, rule set, limitations and safe structured findings
  are visible. `requestAiExplanation` remains an input option and does not mutate the outcome.
- Export Readiness: all six frozen `ReproPackageInput` fields, blocker/warning hierarchy,
  candidate include status, license, sensitive, redistribution, exclusion and snapshot/rule-set
  facts are displayed. License prohibitions remain hard blockers even after acknowledgement.
- Formal state chain: Export, Approval, Job and Package are shown as separate server facts.
  Approval confirmation uses formal `exportId` and `approvalId`; stale/expired/rejected states,
  pending submissions, retryability and cancel capability fail closed.
- Manifest and Package: identity, immutable current version, schema, file count, size, SHA-256,
  file metadata, runtime dependencies, service images, limitations and `agentLogs=NOT_AVAILABLE`
  are read-only. Tampered/unavailable packages cannot emit download intent.
- Dialogs: Approval, cancel-reason, Manifest and Inspector use named controls and focus-managed
  surfaces. Manifest additionally owns a capture-phase Escape fallback for the embedded Preview.
- Responsive: desktop keeps the main surface dominant; tablet opens details in Dialog/Sheet;
  mobile exposes one primary view and promotes tampered/unavailable risk above configuration.

Local-only Stage 2 state:

- AI explanation checkbox and ReproPackage configuration draft;
- Approval/Manifest/cancel Dialog visibility, cancel reason and temporary copy feedback;
- no local Approval, readiness, Export, Job, Manifest, Package or download success state.

Newly exercised Events:

- `run-claim-audit`, `run-export-readiness`, `request-export-confirmation`,
  `create-repro-package`, `retry-job`, `cancel-job`, `download-repro-package`.
- Retry/cancel Events are implemented but the frozen fixture set does not expose an allowed
  capability combination, so Stage 2 cannot truthfully exercise their submission path.

## 11. Stage 2 Verification

```text
bun run --cwd frontend check:m7-fixtures       PASS (7 tests, 104 expects)
bun run --cwd frontend check:ui-boundaries     PASS
bun run --cwd frontend check:production-mocks  PASS
bun run --cwd frontend lint                    PASS (289 files)
bun run --cwd frontend build                   PASS
```

Focused browser acceptance:

- 6 representative screenshots across 1440/1024/390 and Light/Dark;
- Audit unknown fail-closed and AI request/outcome authority PASS;
- license hard blocker, Approval Dialog Escape/focus restore/state authority PASS;
- Manifest Sheet table, root overflow=0, Escape/focus restore PASS;
- tampered download and permissions unknown fail-closed PASS;
- reduced motion computed animation duration `1e-05s`; console errors 0.

Evidence paths:

- `output/playwright/qa/m7-stage2/interactions.json`
- `output/playwright/qa/m7-stage2/screenshots/`
- root Open Design artifact: `reca-live-design-preview.html`

## 12. Stage 2 Boundary

Stage 3, full fixture matrix, production Route/API integration, backend/Worker/MinIO, Commit, Tag
and Push were not executed. Contract gaps are recorded in the Issue Register and delivery draft.

```text
OPEN_DESIGN_STAGE_RESULT=PASS_WITH_GAPS
HISTORICAL_READY_FOR_CODEX_INTEGRATION=NO
PRODUCTION_INTEGRATION_COMPLETE=NO
NEXT_STAGE_EXECUTED=NO
```
