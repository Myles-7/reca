# M8 Open Design Delivery Draft

Stage 3 is complete. The formal acceptance report and handoff supersede this
draft; it is retained only as the Stage-2 delivery history.

Date: 2026-08-07
Milestone: M8 Research Orchestrator Agent Panel
Open Design stage: 2 complete; Stage 3 not executed

## Production Visual Entry

- Component: `frontend/src/features/agent-workspace/ui/AgentWorkspace.tsx`
- Export: `AgentWorkspace`
- Props: `AgentWorkspaceProps`
- Styles: `frontend/src/features/agent-workspace/ui/agent-workspace.css`
- Preview adapter: `frontend/src/design-preview/DesignPreviewWorkbench.tsx`

No production Route, Container, API, SDK, query, mutation, generated client,
model, contract or fixture is changed by this delivery.

## Frozen Events

The component emits user intent only:

- `create-run { goal, mode: PLAN_AND_EXPLAIN, allowToolCalls }`
- `send-message { runId, message }`
- `cancel-run { runId }`
- `refresh`
- `open-source { objectType, objectId }`
- `open-approval { approvalId }`
- `retry-or-restart { runId, goal }`

Preview logs only action, text length, booleans and masked identifiers. It does
not record goal/message text, Tool summaries, ModelInvocation data, source
metadata, Approval payload or complete IDs. Events do not mutate fixture state.

## Local UI State

Allowed local state is limited to active surface, selected ToolCall, timeline
disclosure, message/goal draft, Dialog/Sheet state and focus restore references.
It does not store or infer permissions, AgentRun/Tool/Job/Approval status,
retryability, source validity, snapshot freshness or resume success.

## Stage-2 Surfaces

- ToolCall list with keyboard selection and known/unknown status.
- Tool Inspector with server-safe summaries and explicit suggestion/prohibited
  semantics.
- Independent ModelInvocation metadata; token and latency values are not framed
  as scientific quality or cost conclusions.
- Independent JobProgress; Tool and Job completion are not merged.
- Read-only Formal Approval with intent-only navigation and stale/hash mismatch
  blocking.
- Source available/denied/missing/stale/invalidated/unknown with anonymous denied
  disclosure and safe navigation rules.
- Provider degradation, schema invalid, injection blocked, policy denied,
  timeout, cancelled and retryable/non-retryable failures remain distinct.

## Responsive And Accessibility

- Desktop: Tool list replaces the left Plan pane when selected; Timeline remains
  primary and Inspector remains contextual.
- Tablet/Mobile: one primary surface at a time; Inspector uses Radix Sheet.
- Tool list supports Enter/Space activation and ArrowUp/ArrowDown focus movement.
- Sheet initial focus, focus trap, Escape and focus restore passed.
- M8-owned reduced-motion CSS covers the Inspector Sheet and M8 Dialog portals.
- Disabled commands expose visible reasons and accessible names.

## Focused Evidence

Evidence directory:
`D:/Open Design/resources/app/prebundled/output/playwright/qa/m8-stage2/`

- 8 representative screenshots across 1440/1024/390 and Light/Dark.
- 7 focused interactions passed.
- root horizontal overflow failures: 0.
- console errors: 0.
- reduced-motion: animation and transition `0.01ms`.

Quality gates passed: M8 fixtures 6/6, UI boundary 4/4, production mocks 6/6,
targeted Biome and TypeScript. Final full-matrix acceptance remains Stage 3.

## Codex Reacceptance

- Positive Cancel and Retry fixtures, pending duplicate-prevention fixtures and
  focused browser reacceptance now pass.
- At design handback, `M8-ISSUE-0012` remained fail-closed; Stage 5 later
  resolved durable resume. The UI still never infers resume or side-effect
  completion from APPROVED alone.
- Production Route/Container/API/SDK/Worker integration remains Codex-owned and
  is complete under the Stage 5 Exit report.

```text
OPEN_DESIGN_STAGE_RESULT=PASS
READY_FOR_CODEX_INTEGRATION=YES
PRODUCTION_INTEGRATION_COMPLETE=YES
NEXT_STAGE_EXECUTED=NO
```
