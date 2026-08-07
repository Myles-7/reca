# M8 Open Design Issue Register

Date: 2026-08-07
Current Open Design stage: 3 complete

## M8-OD-0001

- stage: 1
- severity: MEDIUM
- status: RESOLVED
- area: AgentRun cancel capability / fixture coverage
- fixture: all 54; observed directly in `running`
- viewport: all
- theme: all
- authoritative_requirement: cancellation is displayed and exercised only when
  `capabilities.cancelRun.allowed=true`; disabled actions must show the reason
- observed_behavior: no execution-time typed fixture enables `cancelRun`; the
  `running` fixture remains disabled with `RUN_TERMINAL`
- evidence: `rg` over `agent-workspace/fixtures/index.ts`; Stage-1 browser smoke
  `cancel-capability-fail-closed=PASS`
- root_cause: the frozen catalog covers cancellation states but not an allowed
  cancellation intent from a non-terminal run
- affected_files: Codex-protected `frontend/src/features/agent-workspace/fixtures/index.ts`
  and `frontend/scripts/check-m8-fixtures.test.ts`
- owner: CODEX
- blocks_current_stage: NO
- blocks_codex_integration: YES, until the positive interaction can be verified
- blocks_m8_exit: YES, if still absent at Stage 3/Exit
- safe_continuation: keep cancel visibly disabled; do not override fixture
  capabilities or open the Dialog from Preview-only state
- resolution: Codex added `running-cancellable` and `running-cancel-pending` typed
  fixtures; the deterministic event guard requires the current Run ID and server
  capability, and the pure UI remains intent-only
- focused_verification: Stage-4 reacceptance opened the Cancel Dialog, verified
  focus/Escape restoration, one masked Event Log intent, unchanged running facts
  and disabled duplicate submission while pending
- accessibility: disabled reason is visible and included in accessible name
- security_or_scientific_integrity_impact: prevents UI from implying cancellation
  authority or rollback of completed Tool/Job/domain facts

## M8-OD-0002

- stage: 1
- severity: MEDIUM
- status: RESOLVED
- area: responsive layout / embedded preview
- fixture: long-content, permissions-unknown, resume-pending
- viewport: 390x844
- theme: Light and Dark
- authoritative_requirement: mobile root has no horizontal overflow and shows one
  primary surface without hiding blockers or disabled reasons
- observed_behavior: initial viewport media queries saw the outer 1500px Preview
  browser and retained the desktop three-column minimum width inside a 390px panel
- evidence: first browser smoke measured root `scrollWidth=550/490` for the three
  mobile cases; targeted DOM diagnostic identified Header and workspace grid
- root_cause: responsive behavior was bound to browser viewport instead of the
  Agent panel container
- affected_files: `frontend/src/features/agent-workspace/ui/agent-workspace.css`
- owner: OPEN_DESIGN
- blocks_current_stage: NO after resolution
- blocks_codex_integration: NO
- blocks_m8_exit: NO
- safe_continuation: use named container queries for panel breakpoints
- resolution: added `container-type: inline-size`, 1100px tablet and 720px mobile
  container queries; mobile reasons now wrap and command buttons remain accessible
- focused_verification: all six Stage-1 screenshots report
  `scrollWidth===clientWidth`; mobile long-content and security states remain visible
- accessibility: mobile commands retain complete accessible names and tooltips
- security_or_scientific_integrity_impact: resolved; blockers and fail-closed
  reasons no longer require horizontal scrolling

## M8-OD-0003

- stage: 1
- severity: LOW
- status: RESOLVED
- area: Windows Design Preview environment
- fixture: planning
- viewport: desktop
- theme: Light
- authoritative_requirement: use the existing `frontend/design-preview.html`
  development boundary without creating a second frontend project
- observed_behavior: the first Vite process inherited a production `NODE_ENV` and
  the existing Preview guard rejected rendering before product UI mounted
- evidence: browser timeout plus Vite error `The design fixture preview is
  available only in development.`
- root_cause: inherited local process environment, not product code
- affected_files: no repository product file
- owner: OPEN_DESIGN environment
- blocks_current_stage: NO after resolution
- blocks_codex_integration: NO
- blocks_m8_exit: NO
- safe_continuation: launch the existing Preview with explicit development mode
- resolution: restarted the same Vite entry using `NODE_ENV=development` and
  `--mode development`; no guard or configuration was weakened
- focused_verification: Preview rendered, browser smoke passed, console errors 0
- accessibility: no impact
- security_or_scientific_integrity_impact: no product impact; development-only
  fixture boundary remains enforced

## M8-OD-0004

- stage: 2
- severity: HIGH
- status: RESOLVED
- area: responsive Tool surface navigation
- fixture: side-effect-running, approval-hash-mismatch
- viewport: 1024x768 and 1440x900
- theme: Light and Dark
- authoritative_requirement: desktop and tablet must expose the Tool list and
  Inspector without hiding the Timeline, blocker or disabled reason
- observed_behavior: the Stage-1 CSS kept the Tool surface hidden outside the
  mobile breakpoint; Preview local surface selection changed state but did not
  reveal the Tool list
- evidence: first Stage-2 Playwright run resolved a hidden Tool option and timed
  out opening the Inspector Sheet
- root_cause: the four-surface navigation and active-surface CSS were scoped only
  to the mobile container query
- affected_files: `frontend/src/features/agent-workspace/ui/AgentWorkspace.tsx`,
  `frontend/src/features/agent-workspace/ui/agent-workspace.css`
- owner: OPEN_DESIGN
- blocks_current_stage: NO after resolution
- blocks_codex_integration: NO
- blocks_m8_exit: NO
- safe_continuation: use the same local surface state at every breakpoint; keep
  Timeline and Inspector stable on desktop and use a Sheet below 1100px
- resolution: exposed the four-surface switch at all widths, replaced the desktop
  Plan pane with Tool list only when selected, and used single-primary-surface
  behavior for tablet/mobile
- focused_verification: Stage-2 screenshots and Tool keyboard/Sheet focus smoke
  pass at 1440/1024/390 with root overflow 0
- accessibility: explicit Enter/Space activation and ArrowUp/ArrowDown focus
  movement were added to the Tool listbox
- security_or_scientific_integrity_impact: resolved; Tool and disabled states are
  now reviewable without changing formal ToolCall state

## M8-OD-0005

- stage: 2
- severity: MEDIUM
- status: RESOLVED
- area: Tool retry/restart positive fixture coverage
- fixture: tool-failed-retryable, agent-failed
- viewport: all
- theme: all
- authoritative_requirement: Tool retry/restart is enabled only when the Tool is
  retryable and the workspace capability explicitly allows the event
- observed_behavior: `tool-failed-retryable` projects Tool retryability but keeps
  the workspace capability disabled; `agent-failed` enables the workspace
  capability but its ToolCall is not retryable
- evidence: Stage-2 focused fail-closed smoke and fixture catalog review
- root_cause: no typed fixture combines both authoritative conditions
- affected_files: Codex-protected fixture catalog and M8 fixture guard
- owner: CODEX
- blocks_current_stage: NO
- blocks_codex_integration: YES, until the positive path can be verified
- blocks_m8_exit: YES if still absent at final acceptance
- safe_continuation: show the Tool error and retryability, keep the command
  disabled, and display the workspace capability reason
- resolution: Codex added `tool-failed-retry-allowed` and `tool-retry-pending`;
  the deterministic event guard now also requires a known retryable ToolCall and
  retryable AgentRun before emitting the intent
- focused_verification: Stage-4 reacceptance emitted one masked
  `retry-or-restart` intent, retained failed facts and disabled duplicate pending
  submission until new Props
- accessibility: disabled reason is visible and included in the accessible name
- security_or_scientific_integrity_impact: prevents Tool retryability from being
  mistaken for authority to repeat a side effect

## Retained Codex Issues

- `M8-ISSUE-0003`: durable safe resume remains incomplete.
- `M8-ISSUE-0004`: only tested typed Tool wrappers may be exposed.
- `M8-ISSUE-0010`: production project route/panel integration remains Stage 4.
- `M8-ISSUE-0012`: durable Approval resume and side-effect Tool coverage remain
  fail-closed; Stage 1 displays `AGENT_RESUME_PENDING` without simulated success.

## M8-OD-0006

- stage: 3
- severity: HIGH
- status: RESOLVED
- area: theme owner, stable first-screen height and direct navigation
- fixture: all 54; focused on loading, planning and long-content
- viewport: 1440x900, 1024x768, 390x844
- theme: Light and Dark
- authoritative_requirement: loading and ready surfaces must use the real visual
  theme, retain stable first-screen geometry and keep direct structured navigation
  visible
- observed_behavior: loading hard-coded `data-theme=light`, the Agent Preview
  surface supplied only `min-height`, and loading omitted the direct navigation
- evidence: initial Stage-3 matrix reported 218 height failures and six loading
  navigation failures; no runtime or console failures occurred
- root_cause: the visual root bypassed `useVisualTheme` during loading and the
  Preview parent did not provide a definite percentage-height basis
- affected_files: `AgentWorkspace.tsx`, `design-preview-workbench.css`
- owner: OPEN_DESIGN
- blocks_current_stage: NO after resolution
- blocks_codex_integration: NO
- blocks_m8_exit: NO
- safe_continuation: inherit the shared theme and scope the definite Preview
  height only to `data-module=agent-workspace`
- resolution: loading now uses the shared theme and direct link; Agent Preview
  fills the selected 1440/1024/390 canvas
- focused_verification: rerun complete matrix, 324/324 PASS
- accessibility: direct navigation is available during loading
- security_or_scientific_integrity_impact: prevents degraded/loading UI from
  hiding the return path or presenting the wrong theme owner

## M8-OD-0007

- stage: 3
- severity: HIGH
- status: RESOLVED
- area: Dialog confirmation and focus restoration
- fixture: create-available, agent-failed; cancel positive path unavailable
- viewport: desktop, tablet and mobile
- theme: Light and Dark
- authoritative_requirement: create/cancel/retry confirmation surfaces must trap
  focus in both directions, close with Escape and restore the originating control
- observed_behavior: retry emitted directly without confirmation; Create focus
  restoration was lost after the Preview Event Log rerendered its parent
- evidence: focused Stage-3 interaction failures before correction
- root_cause: retry lacked a Dialog and action Dialogs relied only on implicit
  portal focus restoration across a parent rerender
- affected_files: `AgentWorkspace.tsx`
- owner: OPEN_DESIGN
- blocks_current_stage: NO after resolution
- blocks_codex_integration: NO
- blocks_m8_exit: NO
- safe_continuation: store only the trigger element in local UI state; never
  persist Run or capability state
- resolution: added an intent-only Retry Dialog and explicit trigger focus
  restoration for Create, Cancel and Retry
- focused_verification: Create/Retry initial focus, forward/backward loop, Escape
  and restore passed; Cancel stays disabled because its authoritative fixture is absent
- accessibility: resolved for executable typed paths
- security_or_scientific_integrity_impact: retry cannot look like an immediate
  successful restart and completed facts are explicitly not rolled back

## M8-OD-0008

- stage: 3
- severity: MEDIUM
- status: RESOLVED
- area: Preview Event Log data minimization
- fixture: create-available
- viewport: all
- theme: all
- authoritative_requirement: create-run logs only action, goal length and
  allowToolCalls; it never records goal text or extra provider/runtime metadata
- observed_behavior: the fixed `PLAN_AND_EXPLAIN` mode was summarized as a text
  length field
- evidence: focused Event Log assertion
- root_cause: `summarizeAgentEvent` included mode before generic redaction
- affected_files: `DesignPreviewWorkbench.tsx`
- owner: OPEN_DESIGN
- blocks_current_stage: NO after resolution
- blocks_codex_integration: NO
- blocks_m8_exit: NO
- safe_continuation: keep the allowlist explicit per Agent event
- resolution: removed mode from the create-run Event Log summary
- focused_verification: sensitive goal/message, safe summaries and full IDs are
  absent; 62 focused checks pass
- accessibility: no impact
- security_or_scientific_integrity_impact: reduces Preview metadata collection

## Stage Summary

Open Design-owned Stage-3 HIGH/BLOCKER issues: 0 open.
Open Design-owned resolved issues: 6.
Open Codex-owned fixture gaps: 0.
Stage decision after Codex reacceptance: `PASS`.

`READY_FOR_CODEX_INTEGRATION=YES`; M8-OD-0001 and M8-OD-0005 passed focused
contract and browser revalidation on 2026-08-07.
