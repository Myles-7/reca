# M8 Open Design Acceptance Report

Date: 2026-08-07
Milestone: M8 Research Orchestrator Agent Panel
Scope: Open Design Stage 3 pure UI acceptance

## Decision

`OPEN_DESIGN_STAGE_RESULT=PASS`

`READY_FOR_CODEX_INTEGRATION=YES`

`PRODUCTION_INTEGRATION_COMPLETE=YES`

`NEXT_STAGE_EXECUTED=NO`

The UI implementation and all executable typed fixtures pass. Codex Stage-4
reacceptance resolved the two positive capability gaps without changing the pure
UI boundary, so production integration may proceed.

## Delivered Visual Entry

- export: `AgentWorkspace`
- module: `frontend/src/features/agent-workspace/ui/index.ts`
- component: `frontend/src/features/agent-workspace/ui/AgentWorkspace.tsx`
- styles: `frontend/src/features/agent-workspace/ui/agent-workspace.css`
- frozen input: `AgentWorkspaceProps`
- optional visual composition inputs: `initialSurface`, `onSurfaceChange`

Props are `content`, `pendingAction`, `mutationError`, `onRetry`, `onEvent`,
`selectedToolCallId` and `onToolSelectionChange`. Events are `create-run`,
`send-message`, `cancel-run`, `refresh`, `open-source`, `open-approval` and
`retry-or-restart`.

Local state is limited to Run/Plan/Timeline/Tools surface selection, selected
Tool context, disclosure, draft text, Dialog/Sheet state and focus restoration.
It never stores or derives permission, Run/Tool/Job/Approval status, source
validity, retryability, snapshot freshness or domain success.

## Fixture Matrix

- fixture count: 54
- viewports: 1440x900, 1024x768, 390x844
- themes: Light and Dark
- combinations: 324
- result: 324 PASS / 0 FAIL
- console errors: 0
- screenshots: 324 matrix images plus one final interaction image

Every combination checks page and Workspace root overflow, real visual theme,
Header/direct navigation, stable first-screen height, responsive visible
surfaces, composer bounds, long text bounds, disabled reasons and semantic labels.
Mobile exposes one primary surface at a time; desktop keeps Timeline primary and
Inspector contextual; tablet/mobile use the Inspector Sheet.

## Semantic Acceptance

Five FactKind values remain visually and textually distinct:
`AGENT_SUGGESTION`, `SYSTEM_FACT`, `DETERMINISTIC_RESULT`,
`USER_CONFIRMATION` and `FORMAL_APPROVAL`.

AgentRun, ToolCall, ModelInvocation, Job and Approval are separate surfaces and
never collapse into one success state. Source available/denied/missing/stale/
invalidated/unknown remain distinct. Approval approved/rejected/expired/stale/
hash mismatch remain distinct. Existing system facts and deterministic results
remain readable during provider degradation.

Unknown status/permissions, route fallback, resume pending, stale Approval/source,
denied source/Tool, schema invalid, injection blocked and non-retryable failure
all fail closed with visible reasons. The blocked injection text is never shown.

## Interaction And Accessibility

- focused checks: 62 PASS, 1 fixture gap
- Create and Retry Dialog: initial focus, forward/backward focus loop, Escape and
  trigger focus restoration PASS
- Cancel: disabled reason PASS; positive Dialog path not executable because the
  catalog has no `cancelRun.allowed=true` fixture
- Inspector Sheet: initial focus, bidirectional loop, Escape and restore PASS
- Tool list: Enter selection and ArrowUp/ArrowDown focus behavior PASS
- surface navigation: selected/current semantics and mobile single-surface PASS
- reduced motion: animation and transition duration compute to `1e-05s`
- visible buttons without accessible names: 0
- pending and mutation error paths do not modify formal fixture state

Event Log records intent only. Goal/message text, server-safe Tool summaries,
full IDs, Prompt, Trace, ModelInvocation payload and source metadata are absent.

## Quality Gates

All required commands passed:

- `bun run --cwd frontend format:check` - 307 files
- `bun run --cwd frontend lint` - 311 files
- `bun run --cwd frontend check:m8-fixtures` - 6/6, 42 expects
- `bun run --cwd frontend check:ui-boundaries` - 4/4 and clean scan
- `bun run --cwd frontend check:production-mocks` - 6/6 and clean scan
- `bun run --cwd frontend check-generated-client` - 4 generated files consistent
- `bun run --cwd frontend build` - TypeScript and Vite PASS
- `git diff --check` - PASS

Browser acceptance used Microsoft Edge `151.0.4129.59` through an isolated local
CDP session. Bun 1.2.22 could not complete the Windows Playwright CDP handshake;
the same scripts passed under Node 25.8.2 without changing assertions.

Matrix script SHA-256:
`2c3c71f5d7d8f63119905e73419f0e8b7f0441f7c5120e636f74f1fac4a4b2e7`.

Interaction script SHA-256:
`12cc28e1cfb5e794102fb407f6407f3b53ae904827f2f448ece09b032238106a`.

## Evidence Index

Evidence root:
`D:/Open Design/resources/app/prebundled/output/playwright/qa/m8-stage3/`.

- `matrix/matrix-results.json`: per-combination metrics
- `matrix/matrix-summary.json`: 324/324 aggregate result
- `interactions/interaction-results.json`: 62 checks and one gap
- `screenshot-index.tsv`: fixture, viewport, theme and screenshot path
- `matrix/<fixture>__<viewport>__<theme>.png`: 324 screenshots

Portable script/result copies:
`D:/桌面/Recas/output/playwright/m8-open-design/`.

## Protection And Remaining Gaps

The Stage-1 controlled manifest hashes remain unchanged for package.json,
openapi.json, model, UI contracts, fixtures, route contract and fixture guard.
Open Design did not modify API, generated client, adapter, mapper, query,
mutation, Container, production Route, backend, Worker or migration paths.

Resolved Codex reacceptance items:

- M8-OD-0001: cancellable and cancel-pending fixtures plus focused browser PASS;
- M8-OD-0005: retryable Tool/retry capability and pending fixtures plus focused
  browser PASS;
- M8-ISSUE-0012 was backend/Exit work at Open Design handback; Stage 5 later
  resolved it with deterministic rebuild while the accepted UI continues to
  display only server-authoritative recovery state;
- production Route, Container, deep-link, API, cache, permission recheck and real
  vertical E2E remain Codex Stage 4/5 ownership.

Open Design itself executed no M8 Exit Gate, backend suite, Worker/Valkey,
Approval resume, clean-room, M9 test, commit, tag or push. Codex Stage 5 later
completed the M8 Exit Gate without changing the accepted UI ownership boundary.

## Stage-4 Codex Reacceptance Addendum

Codex, acting as the authorized acceptance owner, added four Codex-owned typed
fixtures and tightened the deterministic retry guard. `check:m8-fixtures` passed
6/6 with 57 assertions. Two focused Playwright tests passed for Cancel and Retry,
including Dialog focus/Escape restoration, masked single intent, unchanged
business facts and pending duplicate prevention. The original 324-image geometry
matrix remains the Open Design Stage-3 evidence; no visual file changed during
reacceptance.
