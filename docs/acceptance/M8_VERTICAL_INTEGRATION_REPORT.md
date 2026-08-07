# M8 Vertical Integration Report

Date: 2026-08-07
Stage: M8 Stage 5 remediation and final acceptance

## Decision

`M8_STAGE_RESULT=PASS_WITH_ISSUES`

`NEXT_STAGE_EXECUTED=NO`

## Runtime Identity

- SDK: `openai-agents==0.19.1`.
- provider mode: `RECORDED`; not Live.
- Prompt: `research-orchestrator@1.0.0`.
- Registry: `m8.1`.
- migration head: `0019_m8_agent_runtime`.
- route: `/projects/$projectId/agent`.

## Real Governed Chain

The isolated PostgreSQL test runs the real API, SDK Runner, ToolRegistry,
Services and Worker handlers with a recording dispatcher and in-memory object
storage. IDs are random test UUIDs and are not retained in this report.

`Project -> dataset upload -> AgentRun -> profile_dataset -> Data Quality Job ->
CleaningPlan preview -> external Approval -> deterministic rebuild resume ->
apply_approved_transformations -> DataTransformation Job -> new DatasetVersion ->
final server-fact Agent summary`.

The initial ModelInvocation remains truthfully correlated to AgentRun only; the
final summary invocation is created after the ToolCall exists and is correlated
to both. ToolCall, Job, Approval and output links remain immutable/audited.

## Failure And Replay Evidence

- Rejected Approval transitions ToolCall to `DENIED`, AgentRun to `FAILED`, and
  creates no DataTransformation.
- A duplicate Approval callback reuses one idempotent resume Job.
- Duplicate Agent/DataTransformation Worker delivery is unclaimed and creates no
  second formal DatasetVersion or transformation Job.
- Policy tests reject expired/stale/foreign/hash-mismatched Approval, prohibited
  Tools, schema smuggling, prompt injection and Agent self-approval.
- Checkpoint field allowlist proves no Prompt body, raw SDK state, full Tool args,
  Authorization value or Secret is persisted.
- Session/Trace are not business authorities; direct M1-M7 workspaces remain usable.

## Verification

| Gate | Result |
| --- | --- |
| final clean-room PostgreSQL | PASS, 489 passed / 3 skipped |
| no-database | PASS, 253 passed / 3 skipped / 236 deselected |
| full Playwright | PASS, 169 passed / 2 skipped |
| Ruff / strict mypy / ty | PASS; mypy 161 source files |
| frontend generated/guards/fixtures/build | PASS; 6/6 fixture tests, 59 assertions, 2539 modules |
| empty/repeated migration and one head | PASS, `0019_m8_agent_runtime` |
| Worker/Celery/Valkey/MinIO/restart/persistence | PASS |
| Secret scans / Python audit | PASS |
| Bun audit | retained one LOW Babel advisory |
| Live provider | NOT RUN; no approved credential/data/cost boundary |

Evidence directory: `D:/Temp/User/reca-m0-acceptance-20260807-121523`.

`READY_FOR_CODEX_INTEGRATION=YES`

`PRODUCTION_INTEGRATION_COMPLETE=YES`
