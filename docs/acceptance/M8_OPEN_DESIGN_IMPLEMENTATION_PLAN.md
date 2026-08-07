# M8 Open Design Implementation Plan

Date: 2026-08-06
Milestone: M8 Research Orchestrator Agent Panel
Open Design stage: 1 complete
Stage boundary: Preview plus Stage/Run/Plan/Timeline main panel only

## 1. Entry And Recovery Baseline

| Fact | Recorded value |
| --- | --- |
| formal repository | `D:/桌面/Recas/reca` |
| branch | `feat/m2-research-literature` |
| HEAD | `3f8219c321b4850576fbf7ab5af844752b1f6e87` |
| upstream | `origin/feat/m2-research-literature` |
| migration head | `0019_m8_agent_runtime.py`; single intended M8 head after `0018` |
| Open Design workspace | formal repository in place; no second worktree created |
| entry gate | `M8_OPEN_DESIGN_HANDOFF.md`: `READY_FOR_OPEN_DESIGN=YES` |
| protected worktree state | Codex-owned M8 Stage 0-3 tracked and untracked changes present; preserved |

Recovery method: retain the current branch and HEAD, do not reset, clean, stash or
checkout protected paths, and restore only the Open Design files listed in section
6 from the recorded Stage-1 diff. No commit, tag or push was created.

## 2. Controlled Read-Only Input Manifest

The formal repository was used directly, so source and destination are identical.
These files remained read-only to Open Design.

| Input | Bytes | SHA-256 |
| --- | ---: | --- |
| `frontend/package.json` | 3,625 | `317456200e2a07c9716b18fd8a2d1baf15809cdfd04f492b5b0f0954756a5f5a` |
| `frontend/openapi.json` | 870,258 | `4a5b2f0ae92de431f4f73032880e67f8bca47301d48cd917c7959f4b2d6998a8` |
| `agent-workspace/model.ts` | 3,354 | `c7197fcc15774c01719bb3e8880e24c77c4ab4d8bc18e31d43046e30f597e7af` |
| `agent-workspace/ui/contracts.ts` | 1,030 | `0e823610deace90fa95b617894000ebfeca8d7f596d6d1baeb9dc9775e841914` |
| `agent-workspace/fixtures/index.ts` | 17,382 | `d09aa88d84fb3346b28a4d81518d0642b9d63286c1bf3735155375d4e595b01c` |
| `agent-workspace/route-contract.ts` | 1,534 | `01e63f44c0f644d4dcd8ecdade3d23132cbd9380daad4058d4437cdd6dd702ed` |
| `check-m8-fixtures.test.ts` | 4,003 | `3762d3091e636ca81e573235cf575d8fbf527dc46a174526381b573188555ac8` |
| `M8_OPEN_DESIGN_HANDOFF.md` | 5,948 | `c5beef4df88cf1b635d594e0781bfa2f79aa44d9e4814d459d7e0aad7fe1b9f5` |

Generated, adapter, mapper, query, mutation and Container inputs were inspected
only for ownership and import-boundary confirmation. They were not imported by
the pure UI or modified by Open Design.

## 3. Fixture And Information Architecture Plan

Execution-time catalog: 54 typed fixtures.

- Run/main states: loading, empty, error, forbidden, create, permission, route,
  read-only, planning, running, waiting, resume-pending and terminal runs.
- Tool/Approval/Failure states: retained for Stage 2 Inspector work; Stage 1 only
  shows safe Tool selection summaries and separate-object boundary guidance.
- Responsive states: desktop 1440x900, tablet 1024x768, mobile 390x844; Light and
  Dark are passed to the real visual root.
- Stage 1 priority set: 24 fixtures named in the stage prompt, with six selected
  for representative screenshots.

Desktop uses a compact Plan / Timeline / read-only Run Inspector layout. Tablet
removes the persistent Inspector and exposes it through a Sheet. Mobile uses
Run / Plan / Timeline / Tools surface tabs and shows one primary surface at a
time. Container queries, rather than viewport media queries, own this behavior so
the panel remains correct inside the project shell and the scaled Design Preview.

## 4. Visual And Scientific Semantics

- `AGENT_SUGGESTION`: Agent suggestion badge and suggestion wording.
- `SYSTEM_FACT`: neutral server-owned fact.
- `DETERMINISTIC_RESULT`: deterministic Service result, never model computation.
- `USER_CONFIRMATION`: low-risk user intent, never Formal Approval.
- `FORMAL_APPROVAL`: external ApprovalRecord fact; no approve/reject control.
- Unknown permissions/status, stale snapshot, schema invalid, injection blocked,
  route fallback and resume-pending remain visible and fail closed.
- Loading preserves Header plus three-pane first-screen geometry.
- Disabled commands expose a visible reason in addition to tooltip/accessible name.
- Direct structured Workspace navigation remains visible in every ready state.

`M8-ISSUE-0012` is represented by `AGENT_RESUME_PENDING`: the message field is
disabled and the UI does not claim that the runtime resumed or any side effect
succeeded.

## 5. Props, Events And Local UI State

Frozen production entry: `AgentWorkspace` consuming `AgentWorkspaceProps`.

Events emitted only as intent: `create-run`, `send-message`, `cancel-run`,
`refresh`, `open-source`, `open-approval`, `retry-or-restart`. Stage 1 exercises
create, send, cancel availability, refresh and retry availability; Stage 2 owns
the full source/approval/tool interaction surfaces.

Permitted local state: active surface, selected ToolCall, disclosure, textarea
draft, create/cancel Dialog and Inspector Sheet. It does not store permissions,
run/plan/tool status, Approval, Job, source validity, retryability or snapshot
freshness. Preview Event Log records action, text length, booleans and masked IDs;
it never records goal/message text, summaries or source metadata.

## 6. Open Design Changes

- `frontend/src/features/agent-workspace/ui/AgentWorkspace.tsx`
- `frontend/src/features/agent-workspace/ui/agent-workspace.css`
- `frontend/src/features/agent-workspace/ui/index.ts`
- `frontend/src/design-preview/DesignPreviewWorkbench.tsx`
- `docs/acceptance/M8_OPEN_DESIGN_IMPLEMENTATION_PLAN.md`
- `docs/acceptance/M8_OPEN_DESIGN_ISSUE_REGISTER.md`

No shared visual primitive required modification. No API, generated, adapter,
model, mapper, query, mutation, Container, fixture, route or backend file was
modified by Open Design.

## 7. Stage-1 Verification

| Check | Result |
| --- | --- |
| `bun run --cwd frontend check:m8-fixtures` | PASS: 6 tests, 42 expects |
| `bun run --cwd frontend check:ui-boundaries` | PASS: 4 tests and clean scan |
| `bun run --cwd frontend check:production-mocks` | PASS: 6 tests and clean scan |
| `bun run --cwd frontend format:check` | PASS: 307 files |
| `bun run --cwd frontend lint` | PASS: 311 files |
| `bun run --cwd frontend build` | PASS: TypeScript and Vite production build |
| Stage-1 browser smoke | PASS: 6 screenshots, 4 interaction checks, 0 console errors |

Browser evidence:
`D:/OPenDesign/2ab278d1-4474-4a10-b954-777fc8bc8b77/output/playwright/qa/m8-stage1/`

Representative cases: planning desktop Light, structured-plan tablet Dark,
waiting-user-input tablet Dark, long-content mobile Light,
permissions-unknown mobile Dark and resume-pending mobile Light. Root horizontal
overflow was zero in all six cases.

The generated root preview passes the standalone HTML contract: no external
scripts, stylesheets or iframes; the root precedes the inline bundle; and the
Agent Workspace is present in the bundle. The optional Open Design image export
could not render the 3.29 MB data URL and returned `ERR_INVALID_URL`; this is
retained as a host-export validation risk rather than a product console error.

## 8. Remaining Stage Boundary

## 9. Stage-2 Delivery

Stage 2 completes the Tool/Model/Job/Approval/Source Inspector without changing
the frozen ViewModel or Event boundary.

- Tool list: name/version, category, confirmation requirement, raw/known status,
  FactKind, retryability, error and linked-object summary.
- Tool Inspector: server-safe input/output summaries, suggestion/prohibited
  integrity notices, independent JobProgress, Formal Approval, Source and
  ModelInvocation sections.
- Formal actions: `open-source`, `open-approval` and `retry-or-restart` remain
  intent-only and require the authoritative workspace capability plus current
  object state. Stale, denied, invalidated, unknown and hash-mismatch cases fail
  closed with a visible reason.
- Responsive behavior: desktop keeps Timeline as the primary surface and swaps
  Plan for the Tool list; tablet/mobile use the four-surface switch and a Radix
  Inspector Sheet with focus trap, Escape and focus restore.
- Safety semantics: provider degradation does not hide existing facts; prompt
  injection content is never disclosed; denied sources remain anonymous;
  Tool/Job/Approval completion is never merged into a single success state.

Stage-2 browser evidence:
`D:/Open Design/resources/app/prebundled/output/playwright/qa/m8-stage2/`.
Eight representative screenshots and seven focused interactions passed with no
root overflow or console errors. Reduced motion computed to `0.01ms` for the M8
Inspector Sheet.

The catalog still lacks a fixture combining a retryable ToolCall with
`capabilities.retryOrRestart.allowed=true`; the Inspector therefore renders the
safe disabled state and does not fabricate a positive retry intent.

Stage 3 remains responsible for the complete 54 fixture x 3 viewport x 2 theme
matrix, complete keyboard interaction coverage and final Codex handoff.

`OPEN_DESIGN_STAGE_2=COMPLETE`

`OPEN_DESIGN_STAGE_1=COMPLETE`

`OPEN_DESIGN_STAGE_RESULT=PASS`

`READY_FOR_CODEX_INTEGRATION=YES`

`PRODUCTION_INTEGRATION_COMPLETE=YES`

`NEXT_STAGE_EXECUTED=NO`

## 10. Stage-3 Full Acceptance

Stage 3 stopped feature expansion and completed concentrated Open Design fixes,
the full typed-fixture matrix, complete focused interactions and the formal
Codex handoff.

Resolved shared UI roots:

- the loading surface now inherits the active shared visual theme;
- the Agent Preview surface provides a definite `height: 100%` basis, keeping
  loading, ready and failure first-screen geometry stable;
- direct structured navigation remains visible during loading;
- workspace retry/restart now uses an intent-only confirmation Dialog;
- Create, Cancel and Retry Dialogs explicitly restore focus after Preview parent
  rerenders;
- the Event Log no longer records the fixed provider-independent mode field.

Full geometry and theme evidence:

- execution-time catalog: 54 fixtures;
- combinations: 54 fixtures x 3 viewports x 2 themes = 324;
- result: 324 PASS, 0 FAIL, 0 console errors;
- screenshots: 324, indexed by `screenshot-index.tsv`;
- browser: Microsoft Edge `151.0.4129.59` through an isolated local CDP session.

Focused interaction evidence: 62 PASS, 1 typed-fixture gap and 0 console errors.
The gap is the missing positive `cancelRun.allowed=true` fixture; cancellation
remains visibly disabled and no local Dialog or success state is fabricated.

All protected manifest hashes recorded in section 2 remain unchanged. Complete
frontend gates passed: format, lint, M8 fixtures 6/6, UI boundary 4/4,
production mocks 6/6, generated-client consistency, TypeScript/Vite build and
`git diff --check`.

Evidence:
`D:/Open Design/resources/app/prebundled/output/playwright/qa/m8-stage3/`.

`OPEN_DESIGN_STAGE_3=COMPLETE`

`OPEN_DESIGN_STAGE_RESULT=PASS`

`READY_FOR_CODEX_INTEGRATION=YES`

`PRODUCTION_INTEGRATION_COMPLETE=YES`

`NEXT_STAGE_EXECUTED=NO`

Stage-4 Codex reacceptance resolved the two retained fixture gaps with four
Codex-owned fixtures, 57 fixture assertions and two focused browser tests. The
historical Stage-3 matrix remains 54 x 3 x 2; the current catalog contains 58
fixtures and is authorized for production integration.
