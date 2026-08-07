# M8 To M9 Handoff

Date: 2026-08-07
Handoff state: approved

`M9_ENTRY=ALLOWED`

This document authorizes M9 entry only. It does not execute M9.

## Frozen Runtime

- SDK: exact `openai-agents==0.19.1`; one `ResearchOrchestrator`.
- Prompt: `research-orchestrator@1.0.0`, content hash
  `5791889f134335fdc00737ba2fb3092d7dfd62ed0310c1d99ba3a37dcfa766b0`.
- ToolRegistry: `m8.1`; enabled Tool schemas are version `1.0`.
- Migration head: `0019_m8_agent_runtime`.
- AgentRun, ToolCall, ModelInvocation, AuditLog, Job and ApprovalRecord are the
  durable authorities. Session and Trace are optional mechanics/telemetry only.
- Raw SDK RunState is not persisted. Durable resume uses an append-only minimized
  deterministic-rebuild checkpoint bound to SDK/registry/prompt/snapshot/Tool/
  Approval versions and hashes.

## Tool And Approval Boundary

- Enabled and tested: `get_project_state`, `get_pending_approvals`,
  `retrieve_evidence`, `profile_dataset`, `apply_approved_transformations`.
- Other formal names remain static metadata with `enabled=false` and an explicit
  unavailable reason until a tested accepted Service wrapper exists.
- FORMAL_APPROVAL execution requires an external same-project ApprovalRecord and
  fresh actor, scope, payload, status, version, hash and snapshot validation in
  the Worker. Agent self-approval remains zero.
- Unknown, missing, expired, stale, rejected, foreign, invalidated or mismatched
  facts fail closed. Duplicate callbacks/deliveries cannot duplicate output.
- No dynamic registration, generic API/HTTP caller, arbitrary URL, Shell, Python,
  SQL, filesystem, ApplyPatch, MCP discovery/server or hosted execution is allowed.

## Model, Data And Trace Boundary

- M9 may use Mock/Recorded/offline modes. Live requires explicit credential,
  approved data scope and cost authorization; Recorded must never be labeled Live.
- Prompt/Schema/source policy enforces requested/max/effective access and treats
  PDF, DOCX, data and Tool output instructions as untrusted content.
- Model text is suggestion/explanation only. Official statistics, EvidenceSpan,
  Claim, version, hash, Approval and scientific facts remain deterministic facts.
- Trace sensitive payload is off. Prompt text, source body, complete Tool args/
  results, provider tokens, signed URLs and sensitive inputs must not be stored or
  rendered in Session, Trace, logs, screenshots or frontend state.

## Frontend And Fallback

- Production route: `/projects/$projectId/agent` inside the existing project shell.
- Safe deep-links cover run/tool/source/approval/job/view IDs and fail closed.
- UI distinguishes suggestion, system fact, deterministic result, confirmation
  and formal Approval; server projection/refetch remains authoritative.
- `READY_FOR_CODEX_INTEGRATION=YES` and
  `PRODUCTION_INTEGRATION_COMPLETE=YES`.
- All M1-M7 structured workspaces remain directly usable when Agent/provider/Tool
  operation is disabled, degraded or failed.

## M9 Rules And Evidence

M9 may use isolated fixtures and recordings, including the M8 Recorded vertical
pattern, but must not fabricate Live provider behavior, Approval, Job, domain
output or successful side effect. It must not widen the Tool allowlist, weaken
project isolation/Approval/injection controls, enable arbitrary execution, persist
raw RunState, permit self-approval, modify scientific facts or replace structured
workspaces.

Retained non-blockers: optional Live smoke not run; Babel LOW advisory retained;
ARS remains `NO_COPY_FOR_M8_CORE`; disabled Tools require later typed wrappers.

`M8_EXIT=PASS`

`M8_COMPLETION=APPROVED`

`M9_ENTRY=ALLOWED`

`NEXT_STAGE_EXECUTED=NO`
