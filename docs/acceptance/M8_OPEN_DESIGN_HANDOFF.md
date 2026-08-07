# M8 Open Design Handoff

Date: 2026-08-07
From: Open Design
To: Codex M8 integration stages

`OPEN_DESIGN_STAGE_RESULT=PASS`

`READY_FOR_CODEX_INTEGRATION=YES`

`PRODUCTION_INTEGRATION_COMPLETE=YES`

`NEXT_STAGE_EXECUTED=NO`

## 1. Frozen Visual Entry

Codex must consume the existing export without rewriting its controller boundary:

- `frontend/src/features/agent-workspace/ui/index.ts`
- named export: `AgentWorkspace`
- prop type: `AgentWorkspaceProps`
- visual extension: `AgentWorkspaceVisualProps`
- surfaces: `run`, `plan`, `timeline`, `tools`

Required props are `content`, `pendingAction`, `mutationError`, `onRetry`,
`onEvent`, optional controlled `selectedToolCallId` and
`onToolSelectionChange`. `initialSurface` and `onSurfaceChange` are optional UI
composition inputs and do not carry business state.

## 2. Frozen Responsive Structure

- desktop: Plan or Tools at left, Timeline/Run primary at center, read-only
  Inspector at right;
- tablet: one selected primary surface plus Inspector Sheet;
- mobile: Run/Plan/Timeline/Tools segmented navigation, exactly one primary
  surface and Inspector Sheet;
- Header, blockers, disabled reasons and direct structured navigation remain
  visible at every breakpoint;
- each pane owns its internal scroller; the page and Workspace roots do not
  scroll horizontally.

The Workspace visual root is `.m8-agent-workspace.reca-visual-refresh` and must
remain inside the existing shared `VisualThemeProvider`. Light/Dark are passed to
the real visual root; loading must not hard-code a theme.

## 3. Frozen Events

The component emits intent only:

- `create-run`: non-empty goal, fixed `PLAN_AND_EXPLAIN`, allowToolCalls;
- `send-message`: waiting-user-input plus allowed capability;
- `cancel-run`: only after allowed capability and confirmation Dialog;
- `refresh`: explicit refresh command;
- `open-source`: only an available server-projected object type and ID;
- `open-approval`: only a safe formal Approval record;
- `retry-or-restart`: only an allowed workspace capability and confirmation
  Dialog.

No event changes fixture, Run, ToolCall, ModelInvocation, Job, Approval, source,
permission, snapshot or domain state locally. Pending prevents duplicate intent.

## 4. Local UI State

Allowed local state is limited to surface/tab, selected Tool context, expanded
long content, draft text, Dialog/Sheet open state, filter/display preferences and
focus restoration targets.

The UI must never persist or derive permissions, lifecycle status, plan status,
Tool result, Job progress, Approval validity, source validity, retryability,
snapshot freshness, durable resume or scientific result success.

## 5. Frozen Scientific And Safety Semantics

FactKind presentation remains:

- `AGENT_SUGGESTION`: AI suggestion, not adopted fact;
- `SYSTEM_FACT`: authoritative system projection;
- `DETERMINISTIC_RESULT`: deterministic Service result, not Agent calculation;
- `USER_CONFIRMATION`: human decision/confirmation;
- `FORMAL_APPROVAL`: formal Approval record.

AgentRun, ToolCall, ModelInvocation, Job and Approval remain separate objects.
Tool completed never implies Job completed; Approval approved never implies Tool
completed or Agent resumed; provider degraded never hides existing facts.

The following remain fail-closed with visible reasons: resume pending, unknown
status, unknown permissions, read-only, route fallback, stale snapshot/source/
Approval, denied/missing/invalidated source, Tool denial/prohibition, schema
invalid, prompt injection blocked and non-retryable failure. Blocked prompt text
and denied-source identity are never disclosed.

## 6. Preview And Fixture Isolation

`agentWorkspaceFixtures`, fixture names, viewport/theme controls, design status,
Event Log and `integration pending` are Preview-only. Production modules must not
import fixtures or the Design Preview.

Preview Event Log allowlists event metadata. It stores action, text lengths,
allowToolCalls and masked IDs where applicable. It does not store goal/message
text, Tool summaries, Prompt, Trace, ModelInvocation payload, source metadata or
full identifiers.

## 7. Acceptance Evidence

- 54 fixtures x 3 viewports x 2 themes = 324/324 PASS;
- 324 matrix screenshots, zero root overflow failures;
- 62 focused interaction/accessibility checks PASS;
- one positive cancel fixture gap;
- console errors: 0;
- complete frontend gates: PASS;
- browser: Microsoft Edge 151.0.4129.59.

Report:
`docs/acceptance/M8_OPEN_DESIGN_ACCEPTANCE_REPORT.md`.

Evidence:
`D:/Open Design/resources/app/prebundled/output/playwright/qa/m8-stage3/`.

## 8. Protected Paths

Open Design did not modify:

- `frontend/src/api/**`, generated or adapter code;
- production routes;
- `agent-workspace/model.ts`, mappers, queries, mutations or containers;
- `agent-workspace/ui/contracts.ts`;
- `agent-workspace/fixtures/**` or fixture guard;
- backend, SDK, Worker, migration, cache or Approval resume implementation.

The controlled Stage-1 input hashes still match at Stage-3 completion.

## 9. Codex Ownership And Reacceptance

Codex Stage 4 remains responsible for Route/Container injection, deep-link
behavior, API and cache connection, permission recheck and real vertical E2E.
Stage 5 remains responsible for Exit work including durable Approval resume.

Codex resolved M8-OD-0001 and M8-OD-0005 with authoritative positive and pending
fixtures, a stricter deterministic retry guard, 6/6 fixture checks with 57
assertions, and two focused Playwright reacceptance tests. Cancel and Retry emit
one masked intent, retain server-projected facts, restore focus and disable
duplicate pending submission. `READY_FOR_CODEX_INTEGRATION=YES` is approved.

`M8-ISSUE-0012` does not invalidate the pure UI rendering: resume pending is
safe and disabled. It remains a backend/M8 Exit limitation and must not be hidden
or simulated during integration.

No production integration, M8 Exit Gate, commit, tag or push has been performed.
