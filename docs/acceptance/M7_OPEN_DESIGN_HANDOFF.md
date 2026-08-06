# M7 Open Design Handoff

Date: 2026-08-06 (Asia/Shanghai)
Stage: Open Design reacceptance
Assessment: PASS

```text
READY_FOR_CODEX_INTEGRATION=YES
PRODUCTION_INTEGRATION_COMPLETE=NO
NEXT_STAGE_EXECUTED=NO
```

## 1. Accepted Delivery

- `EvidenceWorkspace` consumes the frozen `EvidenceWorkspaceProps` contract.
- Views remain `graph`, `claims`, `audits`, `exports`.
- Desktop uses three panes, tablet moves details to managed overlays, and mobile exposes one
  primary surface with an accessible table/list graph fallback.
- Light/Dark styling uses existing RECA visual-refresh tokens.
- Preview fixtures and Event Log remain development-only.

## 2. Authority Boundary

- React Flow receives only projected nodes/edges; connect and reconnect are disabled.
- Local state is limited to view, graph mode, selection, filters, forms, overlays and copy feedback.
- Claim/Link/Audit/readiness/Approval/Export/Job/Package/Manifest/hash facts remain server-owned.
- Unknown permission/status, denied scope, stale facts and tampered packages fail closed.
- Event handlers express intent only and do not apply optimistic business success.

## 3. Corrected Contracts

- Audit Job is independently projected and cannot be confused with Export Job controls.
- ReproPackage history is a typed immutable paginated list with selected-version facts.
- Retryable failed and cancellable running Export fixtures exercise the corresponding Events.
- Suggested Link fixture truthfully enables confirmation with formal Link ID and lock version.

`M7-OD-0003` through `M7-OD-0006` are resolved. The current Vite development Preview also passed,
resolving `M7-OD-0002`.

## 4. Acceptance Evidence

- Original visual matrix: 62 fixtures x 3 viewports x 2 themes, 372/372 PASS.
- Original interaction/accessibility suite: 29/29 PASS.
- Corrected-contract Design Preview Playwright: 4/4 PASS.
- Current fixture guard: 8 tests, 125 assertions PASS.
- Format, lint, generated, boundary, mock, Route contract and production build gates: PASS.

## 5. Codex Integration Entry

Codex may now continue the production integration and real longitudinal E2E defined by M7 Stage 4.
It must retain generated-client/adapter boundaries, revalidate every Event against current server
facts, and must not treat this UI READY as Export completion or M7 Exit approval.

```text
OPEN_DESIGN_STAGE_RESULT=PASS
READY_FOR_CODEX_INTEGRATION=YES
PRODUCTION_INTEGRATION_COMPLETE=NO
NEXT_STAGE_EXECUTED=NO
```
