# M7 Open Design Issue Register

Date: 2026-08-06 (Asia/Shanghai)
Current stage: Open Design Stage 3

## Summary

| ID | Stage | Severity | Status | Owner | Area | Blocks current stage | Blocks Codex integration | Blocks M7 exit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M7-OD-0001 | 1 | HIGH | RESOLVED | OPEN_DESIGN | single-file preview | NO | NO | NO |
| M7-OD-0002 | 1 | LOW | RESOLVED | CODEX / ENVIRONMENT | Vite dev preview | NO | NO | NO |
| M7-OD-0003 | 2 | MEDIUM | RESOLVED | CODEX | Audit Job projection | NO | NO | NO |
| M7-OD-0004 | 2 | MEDIUM | RESOLVED | CODEX | Package history projection | NO | NO | NO |
| M7-OD-0005 | 2 | MEDIUM | RESOLVED | CODEX | retry/cancel fixture coverage | NO | NO | NO |
| M7-OD-0006 | 3 | MEDIUM | RESOLVED | CODEX | Link confirm fixture capability | NO | NO | NO |
| M7-OD-0007 | 3 | MEDIUM | RESOLVED | OPEN_DESIGN | visible disabled reasons | NO | NO | NO |

## M7-OD-0001

| Field | Value |
| --- | --- |
| stage | 1 |
| severity | HIGH |
| status | RESOLVED |
| area | Open Design single-file preview |
| fixture | all M7 fixtures |
| viewport | all |
| theme | Light / Dark |
| authoritative_requirement | Root HTML must remain fully inline and execute its bundle after `#root`. |
| observed_behavior | Adding React Flow caused Vite to preserve `import.meta` in the main bundle; the existing inliner embedded that bundle as a classic script, so the Preview boot surface timed out. |
| evidence | Browser `SyntaxError: Cannot use 'import.meta' outside a module`; root never mounted. |
| root_cause | `build-reca-open-design-preview.mjs` emitted the inlined Vite entry as `<script>` instead of an inline module. |
| affected_files | Design Files `build-reca-open-design-preview.mjs`, generated `reca-live-design-preview.html` |
| owner | OPEN_DESIGN |
| blocks_current_stage | NO after resolution |
| blocks_codex_integration | NO |
| blocks_m7_exit | NO |
| safe_continuation | Keep the bundle inline and mark only the main inlined bundle `type="module"`; do not add external scripts. |
| resolution | The builder now marks the first inlined main bundle as a module. M7 Preview mounted and all browser checks ran from the rebuilt root HTML. |
| focused_verification | Root HTML contains one inline module, zero external scripts/stylesheets/iframes, and the Preview mounts M7. |

## M7-OD-0002

| Field | Value |
| --- | --- |
| stage | 1 |
| severity | LOW |
| status | RESOLVED |
| area | Vite development preview |
| fixture | startup |
| viewport | desktop |
| theme | system |
| authoritative_requirement | Existing `/design-preview.html` should be available in development and protected from ordinary production use. |
| observed_behavior | The local Vite dev server returned the preview entry but evaluated `import.meta.env.DEV` as false, triggering the existing development-only guard. |
| evidence | Vite client error at `src/design-preview/main.tsx:19`; HTTP 200 entry with no mounted workbench. |
| root_cause | Environment/toolchain behavior was not changed in Open Design-owned code; the approved Open Design static build path works. |
| affected_files | none in production source |
| owner | CODEX / ENVIRONMENT |
| blocks_current_stage | NO |
| blocks_codex_integration | NO |
| blocks_m7_exit | NO |
| safe_continuation | Use the existing Open Design static build (`__RECA_OPEN_DESIGN_STATIC__`) for visual acceptance; retain the development-only guard. |
| resolution | The current authoritative Vite development server loaded `/design-preview.html`, mounted the Evidence Workspace and completed focused browser acceptance. |
| focused_verification | Playwright started Vite on port 15176 and passed all four reacceptance tests against the live development Preview. |

## Stage 1 Conclusion

No unresolved Open Design BLOCKER, CRITICAL, HIGH or MEDIUM issue remains. The LOW environment
issue has a verified approved fallback and does not affect the source build, static artifact,
fixture facts, interactions or later production integration.

```text
OPEN_DESIGN_STAGE_RESULT=PASS
HISTORICAL_READY_FOR_CODEX_INTEGRATION=NO
PRODUCTION_INTEGRATION_COMPLETE=NO
NEXT_STAGE_EXECUTED=NO
```

## M7-OD-0003

| Field | Value |
| --- | --- |
| stage | 2 |
| severity | MEDIUM |
| status | RESOLVED |
| area | Audit retry/cancel Job projection |
| fixture | `audit-failed`, `audit-queued`, `audit-running-degraded` |
| authoritative_requirement | Audit retry/cancel must use the Job associated with the Audit and honor known status, retryability, capability and reason. |
| observed_behavior | `ClaimAuditViewModel` has no Job ID and the workspace exposes one Export Job whose resource is unrelated to the Audit. |
| safe_ui_behavior | Audit status and deterministic outcome render normally; failed Audit shows that no associated Job is projected and keeps retry/cancel disabled. |
| owner | CODEX |
| blocks_current_stage | NO; Stage 2 UI fails closed. |
| blocks_codex_integration | NO |
| blocks_m7_exit | NO |
| required_resolution | Project the associated Audit Job or explicitly freeze that Audit retry/cancel is unsupported. |
| resolution | Added a distinct Audit Job projection and UI display; Export retry/cancel remains bound only to the Export Job. |
| focused_verification | Fixture guard asserts Audit Job identity/task type separation; focused browser reacceptance displays the Audit Job in the Audit view. |

## M7-OD-0004

| Field | Value |
| --- | --- |
| stage | 2 |
| severity | MEDIUM |
| status | RESOLVED |
| area | immutable Package history |
| fixture | `package-history-versions` |
| authoritative_requirement | Package history must expose an immutable version list and current selection. |
| observed_behavior | The fixture projects only the current `packageVersion` plus a scope notice saying earlier versions exist; no version IDs, hashes, sizes or selection target are available. |
| safe_ui_behavior | The current immutable version is shown. Earlier versions are represented as unavailable projection metadata, not fabricated selectable rows. |
| owner | CODEX |
| blocks_current_stage | NO; current Package and Manifest remain usable. |
| blocks_codex_integration | NO |
| blocks_m7_exit | NO |
| required_resolution | Add a typed immutable package history projection with version identity and safe selection facts. |
| resolution | Added a typed paginated history containing immutable IDs, version, Artifact references, size, SHA-256, created time and selected state. |
| focused_verification | Fixture guard asserts three unique versions/hashes and one selection; focused browser reacceptance renders three history rows. |

## M7-OD-0005

| Field | Value |
| --- | --- |
| stage | 2 |
| severity | MEDIUM |
| status | RESOLVED |
| area | retry/cancel interaction fixtures |
| fixture | all Stage 2 Export/Job fixtures |
| authoritative_requirement | Stage 2 and Stage 3 must exercise retry and cancel, including a required cancel reason. |
| observed_behavior | No frozen fixture enables `retryJob` or `cancelJob`; the UI implementation therefore cannot truthfully open and submit the cancel reason Dialog or retry intent under allowed server facts. |
| safe_ui_behavior | Controls remain disabled with server reasons; no fixture or capability is changed by Open Design. |
| owner | CODEX |
| blocks_current_stage | NO; independent interactions and fail-closed behavior passed. |
| blocks_codex_integration | NO |
| blocks_m7_exit | NO |
| required_resolution | Add typed fixtures with known retryable FAILED Job and known cancellable QUEUED/RUNNING Job capability combinations. |
| resolution | Added `export-failed-retryable` and `export-running-cancellable` with mutually correct capabilities and server facts. |
| focused_verification | Fixture guard executes retry/cancel authority checks; focused browser reacceptance confirms the corresponding controls are enabled. |

## Stage 2 Conclusion

All Open Design-owned Stage 2 implementation and focused acceptance checks pass. Three frozen
contract/fixture gaps remain fail-closed and are not repaired in UI code.

```text
OPEN_DESIGN_STAGE_RESULT=PASS_WITH_GAPS
HISTORICAL_READY_FOR_CODEX_INTEGRATION=NO
PRODUCTION_INTEGRATION_COMPLETE=NO
NEXT_STAGE_EXECUTED=NO
```

## M7-OD-0006

| Field | Value |
| --- | --- |
| stage | 3 |
| severity | MEDIUM |
| status | RESOLVED |
| area | Link confirmation interaction fixture |
| fixture | `link-suggested` |
| authoritative_requirement | A known SUGGESTED Link with allowed confirmation capability must exercise `confirm-evidence-link` using formal `linkId` and `lockVersion`. |
| observed_behavior | The fixture changes the Link status and allowedActions but retains base `confirmEvidenceLink.allowed=false`. No frozen fixture supplies a truthfully enabled confirmation combination. |
| safe_ui_behavior | Confirm remains disabled and the server capability reason is visible; no fixture or contract is rewritten by Open Design. |
| owner | CODEX |
| blocks_current_stage | NO; all independent UI checks completed. |
| blocks_codex_integration | NO |
| blocks_m7_exit | NO |
| required_resolution | Add or correct a typed fixture with permissionsKnown, known SUGGESTED status and `confirmEvidenceLink.allowed=true`. |
| resolution | Corrected `link-suggested` to project known SUGGESTED status and formal confirmation capability. |
| focused_verification | Fixture guard executes `confirm-evidence-link` with Link ID and lock version; focused browser reacceptance confirms the control is enabled. |

## M7-OD-0007

| Field | Value |
| --- | --- |
| stage | 3 |
| severity | MEDIUM |
| status | RESOLVED |
| area | disabled action explanation |
| fixture | read-only, permissions unknown, unknown/stale/tampered and capability-disabled states |
| authoritative_requirement | Disabled reasons must be visible and not available only through a tooltip. |
| observed_behavior | Several Stage 1/2 actions used `title` as the only local disabled explanation. |
| root_cause | Shared action surfaces had no compact visible reason element. |
| owner | OPEN_DESIGN |
| resolution | Added a reusable visible disabled-reason row to Link, Audit, Readiness, Approval/Job and Package download surfaces without changing capability evaluation. |
| focused_verification | Stage 3 fail-closed interaction checks confirmed every tested disabled action had a visible reason or authoritative risk/permission notice. |
| blocks_codex_integration | NO |
| blocks_m7_exit | NO |

## Stage 3 Conclusion

All Open Design and Codex-owned contract gaps are resolved. The original 372-combination matrix
and 29 interaction checks remain accepted; current gates and the four-test corrected-contract
browser reacceptance pass. No integration-readiness blocker remains.

```text
OPEN_DESIGN_STAGE_RESULT=PASS
READY_FOR_CODEX_INTEGRATION=YES
PRODUCTION_INTEGRATION_COMPLETE=NO
NEXT_STAGE_EXECUTED=NO
```
