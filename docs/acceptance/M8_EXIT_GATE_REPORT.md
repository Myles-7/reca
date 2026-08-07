# M8 Exit Gate Report

Date: 2026-08-07
Milestone: M8 Research Orchestrator Agent
Migration head: `0019_m8_agent_runtime`

## Decision

`M8_EXIT=PASS`

`M8_COMPLETION=APPROVED`

`M9_ENTRY=ALLOWED`

All HIGH M8 Exit/M9 Entry blockers are resolved. M8 provides one governed
ResearchOrchestrator, static typed Tools, durable RECA-owned Approval resume,
audited Worker reconciliation and the production project Agent panel. M9 is
authorized to consume this boundary but was not executed.

## Centralized Remediation

- Added deterministic rebuild resume without persisting SDK RunState. The safe
  append-only checkpoint contains only version/hash/ID/expiry metadata.
- Enabled typed `profile_dataset` and `apply_approved_transformations` wrappers;
  all other unavailable formal Tools remain disabled and fail closed.
- Bound the cleaning side effect to an external same-project ApprovalRecord,
  payload hash, static Registry version and fresh database snapshot.
- Revalidated actor/project/source/status/version/hash/Approval in the Agent and
  DataTransformation Workers; duplicate callbacks and deliveries are idempotent.
- Reconciled AgentRun, ToolCall, ModelInvocation, Job, Approval and output IDs
  without retroactively mutating immutable ModelInvocation correlation.
- Preserved one Orchestrator and zero handoff, Agent-as-tool, MCP, hosted,
  Shell/Python/SQL/filesystem/URL/ApplyPatch/generic HTTP capabilities.

## Complete Gate Evidence

| Gate | Result |
| --- | --- |
| backend Ruff format/check | PASS, 274 files formatted; zero lint errors |
| strict mypy / complete ty | PASS, 161 production source files; zero diagnostics |
| complete no-database | PASS, 253 passed / 3 skipped / 236 deselected |
| PostgreSQL backend | PASS, 489 passed / 3 skipped |
| empty/repeated upgrade and migration tests | PASS |
| migration heads | PASS, one head `0019_m8_agent_runtime` |
| Worker/Celery/Valkey/MinIO and restart/persistence | PASS |
| frontend format/lint/generated/build | PASS, 2539 modules |
| production mock/UI boundary/M8 fixtures | PASS, 6/6, 4/4, 6/6; 59 assertions |
| full Playwright | PASS, 169 passed / 2 skipped |
| repository/container Secret scans | PASS |
| Python dependency audit | PASS, no known vulnerabilities |
| Bun audit | PASS_WITH_LOW_ADVISORY, retained Babel LOW |
| Live provider smoke | NOT RUN; no approved credential/data/cost boundary |

Authoritative clean-room evidence:
`D:/Temp/User/reca-m0-acceptance-20260807-121523`.
Recorded model behavior is reported as Recorded, not Live.

## Exit Assessment

1. Exactly one ResearchOrchestrator and prohibited topology/capability count zero: PASS.
2. SDK Session/Trace/RunState do not replace durable RECA facts: PASS.
3. AgentRun/ToolCall/ModelInvocation scope, state and immutable history: PASS.
4. Database-derived minimized snapshot, canonical hash and stale checks: PASS.
5. Deterministic StageResolver and golden fail-closed behavior: PASS.
6. Static versioned ToolRegistry with no dynamic or similar-name fallback: PASS.
7. Tool/Worker project, permission, source, status, version and hash revalidation: PASS.
8. External ApprovalRecord authority and Agent self-approval count zero: PASS.
9. Duplicate callback/delivery/lost-response idempotency: PASS.
10. Model cannot author official statistics, Evidence, Claim, version or Approval: PASS.
11. Prompt injection/schema smuggling/prohibited Tool requests fail closed: PASS.
12. Trace/session/log/UI sensitive-content redaction: PASS.
13. Provider/tool/schema/timeout degradation is explicit: PASS.
14. Production route/deep-link/mobile/theme/keyboard/focus/reduced motion: PASS.
15. Direct M1-M7 structured workspace fallback remains available: PASS.
16. SDK 0.19.1 notice/source/removal record and ARS no-copy decision: PASS.
17. M0-M7 regression and M9 non-execution: PASS.

## Retained Non-Blocking Limits

- Live provider smoke remains optional and unauthorized in this environment.
- Babel `GHSA-4x5r-pxfx-6jf8` remains a documented LOW advisory.
- ARS decision remains `NO_COPY_FOR_M8_CORE`.
- Formal Tools without a tested Service wrapper remain disabled, not simulated.

`M8_STAGE_RESULT=PASS_WITH_ISSUES`

`NEXT_STAGE_EXECUTED=NO`
