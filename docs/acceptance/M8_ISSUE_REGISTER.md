# M8 Issue Register

Date opened: 2026-08-06
ID sequence: `M8-ISSUE-0001`

## Active And Resolved Issues

### M8-ISSUE-0001

- stage: 0
- severity: HIGH
- status: RESOLVED
- area: trace/privacy
- requirement: sensitive trace payload must be disabled by default
- observed: OpenAI Agents SDK 0.19.1 defaults `trace_include_sensitive_data` to true
- expected: every RECA run explicitly disables sensitive trace data and tests exported spans
- root_cause: upstream SDK convenience default differs from RECA privacy policy
- affected_files: future `backend/app/agent_runtime/sdk_adapter.py`, Spike and trace tests
- owner: M8 stage 1-2 backend
- blocks_current_stage: NO
- blocks_m8_exit_gate: YES
- blocks_m9_entry: YES
- safe_continuation: keep production runtime unregistered; use explicit false in all Spikes
- resolution: the production RunConfig factory always sets `trace_include_sensitive_data=False`, defaults tracing off, and exports only correlation metadata; SDK trace regression tests pass
- focused_verification: stage-0 collector and stage-2 RunConfig tests contain no user input, Tool args/results or document body
- security/scientific impact: possible sensitive research content disclosure if omitted

### M8-ISSUE-0002

- stage: 0
- severity: HIGH
- status: RESOLVED
- area: ModelInvocation/data model
- requirement: M8 usage and Agent/Tool correlation must extend the existing table
- observed: current ModelInvocation lacks `agent_run_id`, `tool_call_id`, token, latency and redaction policy fields
- expected: additive 0019 migration and compatible Service changes; no table rebuild
- root_cause: M1 intentionally implemented the pre-Agent governance minimum
- affected_files: `backend/app/models.py`, migration 0019, `backend/app/agents/service.py`, tests
- owner: M8 stage 1 backend
- blocks_current_stage: NO
- blocks_m8_exit_gate: YES
- blocks_m9_entry: YES
- safe_continuation: existing M1-M7 ModelInvocation behavior remains authoritative
- resolution: 0019 adds nullable same-project AgentRun/ToolCall links and usage/latency/redaction fields without rebuilding the table; Service accepts scoped correlation and maps completion usage
- focused_verification: model/DDL/offline migration/typing checks pass; online PostgreSQL history verification remains under `M8-ISSUE-0011`
- security/scientific impact: missing audit correlation/usage, not incorrect scientific output

### M8-ISSUE-0003

- stage: 0
- severity: HIGH
- status: RESOLVED
- area: messages/RunState/resume
- requirement: durable conversation/resume must be minimal, safe and separate from business facts
- observed: SDK RunState serializes Tool arguments and call IDs and is coupled to SDK/Agent definitions; no RECA message/resume persistence exists
- expected: append-only safe message summaries plus expiring encrypted version-bound resume state, or a documented no-persist rebuild strategy
- root_cause: supporting persistence was deferred until the real SDK Spike
- affected_files: migration 0019 design, AgentRun Service, SDK adapter, security tests
- owner: M8 stage 1-2 backend
- blocks_current_stage: NO
- blocks_m8_exit_gate: NO after resolution
- blocks_m9_entry: NO after resolution
- safe_continuation: retain deterministic rebuild; never persist raw SDK RunState
- resolution: Stage 5 implemented a RECA-owned deterministic rebuild protocol. The append-only `RUNTIME_CHECKPOINT` stores only SDK/registry/prompt versions, snapshot hash, ToolCall identity/input hash, Approval identity/payload hash and expiry. External Approval creates an idempotent Worker Job; the Worker reloads all authorities and starts a new SDK invocation only for the server-fact summary. Raw SDK RunState, Prompt text and complete Tool arguments/results are never persisted.
- focused_verification: real PostgreSQL vertical test validates checkpoint field allowlist, process-independent Worker resume, rejected Approval denial, duplicate Approval callback idempotency, duplicate Worker delivery, Session-independent facts and two immutable ModelInvocation records
- security/scientific impact: replay, approval spoofing and sensitive persistence risk

### M8-ISSUE-0004

- stage: 0
- severity: HIGH
- status: RESOLVED
- area: Tool-Service mapping
- requirement: every registered Tool must call an accepted Service/projection and fail closed otherwise
- observed: stage 2 production SDK exposure currently has typed wrappers for `get_project_state`, `get_pending_approvals` and `retrieve_evidence`; remaining formal names are not exposed until typed argument/output and side-effect reconciliation are complete
- expected: implement explicit Service/projection contracts or keep those Tools disabled
- root_cause: M1-M7 delivered user/API workflows, not M8 wrapper surfaces
- affected_files: future registry, wrappers, snapshot and affected application Services
- owner: M8 stage 1-2 backend
- blocks_current_stage: NO
- blocks_m8_exit_gate: YES
- blocks_m9_entry: YES
- safe_continuation: register only READY Tools; unavailable Tools return stable fail-closed errors
- resolution: Stage 5 separates formal contract metadata from production availability. Exactly `get_project_state`, `get_pending_approvals`, `retrieve_evidence`, `profile_dataset` and `apply_approved_transformations` are enabled; the other 35 names retain formal metadata and fail closed. No generic caller was added.
- focused_verification: Registry/StageResolver/SDK focused tests; complete no-database 253 passed; clean-room database 489 passed; prohibited and dynamic names remain denied
- security/scientific impact: prevents permission bypass and fabricated provider/scientific results

### M8-ISSUE-0005

- stage: 0
- severity: MEDIUM
- status: OPEN_PARTIAL
- area: provider/settings
- requirement: Live mode must require complete credentials and approved data scope; offline modes remain truthful
- observed: Settings support optional model base URL/key/name, but no M8 live credential is available or required for stage 0
- expected: Mock/Recorded pass without credentials; Live is opt-in, explicit and fully audited
- root_cause: provider credentials are deployment-specific secrets
- affected_files: `backend/app/core/config.py`, future SDK provider adapter and tests
- owner: M8 stage 2/5 backend
- blocks_current_stage: NO
- blocks_m8_exit_gate: NO
- blocks_m9_entry: NO
- safe_continuation: use fake/recorded model; never read developer secrets or call a real provider
- resolution: Mock/Recorded and opt-in Live adapters exist; missing credentials degrade truthfully and are tested. Optional authorized Live smoke remains not run
- focused_verification: no-credential degradation, recorded labeling, optional live smoke only when authorized
- security/scientific impact: external data disclosure/cost risk if live mode is implicit

### M8-ISSUE-0006

- stage: 0
- severity: LOW
- status: RESOLVED
- area: documentation/contracts
- requirement: formal names and links must resolve to current authoritative files
- observed: roadmap summary Tool names differ from AGENT_TOOL_CONTRACTS; some stage prompt descriptions use shortened document/route names
- expected: implementation and future docs use stable Tool names and actual repository paths
- root_cause: roadmap prose predates the finalized detailed Tool contract
- affected_files: M8 plan and future registry/API docs
- owner: M8 documentation
- blocks_current_stage: NO
- blocks_m8_exit_gate: NO
- blocks_m9_entry: NO
- safe_continuation: AGENT_TOOL_CONTRACTS wins; do not create aliases as public Tools
- resolution: stage-0 plan records the authoritative mapping; remaining link cleanup is incremental
- focused_verification: doc-link check and registry-name equality test
- security/scientific impact: tool confusion risk; no current data impact

### M8-ISSUE-0007

- stage: retained from M0-M7
- severity: LOW
- status: OPEN_ACCEPTED
- area: frontend supply chain
- requirement: known dependency advisories remain visible
- observed: retained `@babel/core` advisory `GHSA-4x5r-pxfx-6jf8`
- expected: retain visibility and re-evaluate in the final supply-chain Gate
- root_cause: upstream frontend dependency chain
- affected_files: frontend lock/dependency graph
- owner: project supply-chain maintenance
- blocks_current_stage: NO
- blocks_m8_exit_gate: NO
- blocks_m9_entry: NO
- safe_continuation: no ignore expansion or false clean claim
- resolution: accepted LOW pending compatible upstream update
- focused_verification: Bun audit in stage 5
- security/scientific impact: LOW supply-chain exposure; no scientific semantics impact

### M8-ISSUE-0008

- stage: 0
- severity: LOW
- status: RESOLVED
- area: ARS reuse/license/effect
- requirement: copy ARS assets only after measurable benefit and path-level review
- observed: concept comparison matched native outcomes and increased estimated tokens
- expected: no M8 core copy without a positive measurable delta
- root_cause: RECA M1-M7 contracts already cover the tested checkpoint behavior
- affected_files: ARS source record and stage-0 Spike
- owner: M8 stage 0
- blocks_current_stage: NO
- blocks_m8_exit_gate: NO
- blocks_m9_entry: NO
- safe_continuation: retain RECA-native rules and clean removal path
- resolution: `NO_COPY_FOR_M8_CORE`; zero copied paths and no notice implying incorporation
- focused_verification: `test_m8_ars_effect_spike.py` PASS
- security/scientific impact: avoids unnecessary license/coupling/token surface

### M8-ISSUE-0009

- stage: 0
- severity: MEDIUM
- status: RESOLVED
- area: dependency/tool exposure
- requirement: P0 must expose no MCP discovery/server or hosted execution
- observed: openai-agents core dependency transitively installs `mcp`; no extras were selected
- expected: registry/configuration count for MCP/hosted tools remains zero
- root_cause: MCP is an upstream core package dependency in SDK 0.19.1
- affected_files: dependency lock, future SDK adapter/registry/security tests
- owner: M8 stage 1-5 backend/security
- blocks_current_stage: NO
- blocks_m8_exit_gate: YES
- blocks_m9_entry: YES
- safe_continuation: import only core Agent/Runner/Function Tool APIs; configure no MCP server
- resolution: static registry and production Agent runtime assert zero MCP server/discovery, hosted, arbitrary execution or prohibited Tool registration; the transitive package is not configured or exposed
- focused_verification: dependency remains installed but Agent `mcp_servers=[]`, handoffs empty and prohibited registry intersection is zero
- security/scientific impact: arbitrary external tool/data access if accidentally exposed

### M8-ISSUE-0010

- stage: 0
- severity: MEDIUM
- status: RESOLVED
- area: Agent API/frontend
- requirement: one project-scoped Agent API and panel without a second shell
- observed: stage 4 now provides the single project-scoped production Agent route, generated-adapter Container, safe deep-link fallback, project entry and 58 typed fixtures
- expected: stages 3-4 implement the frozen project-scoped contract after backend authority exists
- root_cause: correct M7 boundary explicitly excluded M8 Agent behavior
- affected_files: future Agent API/OpenAPI/frontend feature and tests
- owner: M8 stage 3-4
- blocks_current_stage: NO
- blocks_m8_exit_gate: YES
- blocks_m9_entry: YES
- safe_continuation: users keep direct access to all M1-M7 structured pages
- resolution: Open Design reacceptance is READY; `/projects/$projectId/agent` is registered in the existing shell, create-run restores its server Run ID, source/Approval links use static safe routes and unrelated deep-links fail closed
- focused_verification: 6 API paths, required mutation headers, 4 generated files, 58 fixtures, frontend build/boundary guards and 4 focused browser tests pass
- security/scientific impact: no current risk; future UI must not fabricate Agent/Approval success

### M8-ISSUE-0011

- stage: 0
- severity: LOW
- status: RESOLVED
- area: focused verification/PostgreSQL
- requirement: run the existing ModelInvocation database baseline in stage 0 when the local database is available
- observed: stage 0 ModelInvocation DB tests timed out at 120 seconds; stage 1 `alembic current` and AgentRun/ToolCall DB tests timed out; stage 3 and stage 4 Agent API plus AgentRun/ToolCall focused PostgreSQL tests timed out at 30 seconds; Docker Desktop daemon is absent while offline Alembic SQL compilation and single-head checks pass
- expected: focused database baseline completes with a pass/fail count
- root_cause: local PostgreSQL fixture/service did not become ready within the bounded stage-0 command
- affected_files: no product file; local test infrastructure and existing ModelInvocation tests
- owner: local PostgreSQL/test infrastructure, rerun before M8 Exit Gate
- blocks_current_stage: NO
- blocks_m8_exit_gate: NO
- blocks_m9_entry: NO
- safe_continuation: retain the M7 PostgreSQL pass as entry evidence and rerun with stage-1 database work
- resolution: Docker Desktop became available during Stage 5. The isolated clean-room gate completed PostgreSQL, Valkey, Celery, MinIO, empty upgrade, repeated upgrade and Alembic drift checks without lowering a timeout or constraint.
- focused_verification: final clean-room `backend-database-tests` PASS, 489 passed / 3 skipped; migration head `0019_m8_agent_runtime`; worker ping and registration PASS
- security/scientific impact: verification gap only; no observed product regression

### M8-ISSUE-0012

- stage: 2
- severity: HIGH
- status: RESOLVED
- area: production Tool coverage / durable approval resume
- requirement: all allowed side-effect Tools must use typed wrappers, external ApprovalRecord revalidation and durable compatible pause/resume
- observed: before remediation, production exposed only three read-only wrappers and had no Approval-bound Worker resume path
- expected: typed wrappers for each enabled side-effect/suggestion Tool, ApprovalRecord-bound Worker resume, encrypted/minimized expiring state or a fully tested safe rebuild protocol, and duplicate/lost-response PostgreSQL tests
- root_cause: the accepted Cleaning Service contract had not yet been adapted to the static Registry and durable Agent Worker reconciliation boundary
- affected_files: `backend/app/agent_runtime/sdk_adapter.py`, `tool_gateway.py`, `orchestrator_service.py`, Worker and focused PostgreSQL/security tests
- owner: M8 stage 5 centralized backend fixes before Exit Gate
- blocks_current_stage: NO
- blocks_m8_exit_gate: NO after resolution
- blocks_m9_entry: NO after resolution
- safe_continuation: keep every other unwrapped formal Tool disabled/fail-closed and retain direct M1-M7 workspaces
- resolution: enabled typed `profile_dataset` and `apply_approved_transformations` wrappers. The side-effect wrapper binds the static Registry version/schema, external same-project ApprovalRecord and payload hash; the Worker reloads actor/project/snapshot/plan/status/hash and calls the existing Cleaning Service. Job/output links reconcile back to ToolCall and AgentRun. No generic Router/API/HTTP adapter was introduced.
- focused_verification: Registry/SDK focused tests plus the real PostgreSQL vertical chain cover approved execution, rejected denial, duplicate Approval callback, duplicate Worker delivery and immutable ModelInvocation/ToolCall history; policy tests cover expired/stale/foreign/hash mismatch and self-approval rejection
- security/scientific impact: prevents approval spoofing, duplicate formal writes and version/hash drift; no unsafe side-effect path is currently exposed

### M8-ISSUE-0013

- stage: 3
- severity: HIGH
- status: RESOLVED
- area: Agent API input/idempotency interruption recovery
- requirement: public user input must match safe persistence limits and duplicate/replayed mutations must not append a second business event after process interruption
- observed: the initial Stage-3 route draft allowed goal/message content longer than Stage-1 `SafeSummary.text`, and `append_agent_event` committed before the shared idempotency record was stored
- expected: HTTP validation and persistence schema agree; message/cancel fact plus idempotency record commit atomically while existing Stage-1/2 callers preserve their default commit behavior
- root_cause: Stage-1 Service methods originally owned their own transaction because no formal Agent API existed; the interrupted Stage-3 draft composed a second API transaction around them
- affected_files: `backend/app/agent_runtime/service.py`, `backend/app/api/m8_responses.py`, `backend/app/api/routes/agent_runs.py`, focused API/OpenAPI tests
- owner: M8 stage 3 backend
- blocks_current_stage: NO
- blocks_m8_exit_gate: NO
- blocks_m9_entry: NO
- safe_continuation: mutation endpoints remain fail-closed and require `Idempotency-Key`; no optimistic frontend success
- resolution: goal/message are bounded to 500 characters; Agent event and cancellation Services accept an optional transaction boundary, and Stage-3 routes flush the fact, store idempotency, then commit once
- focused_verification: Ruff/mypy, required-header/input-limit OpenAPI tests and replay-focused PostgreSQL test added; no-database contracts pass, PostgreSQL execution remains under `M8-ISSUE-0011`
- security/scientific impact: prevents unhandled validation divergence and duplicate user-message facts after interrupted delivery; no scientific result is changed

### M8-ISSUE-0014

- stage: 3
- severity: HIGH
- status: RESOLVED
- area: provider/data-externalization authority
- requirement: provider/session internals and model data externalization policy must remain server-owned and must not become a user or UI capability
- observed: the initial Stage-3 request draft exposed `RECORDED` and `LIVE` beside the business mode `PLAN_AND_EXPLAIN`
- expected: public API expresses the Agent task mode only; deployment/provider selection remains within Settings and authorized runtime/test policy
- root_cause: Stage-2 provider test modes were copied too literally into the first public API draft
- affected_files: `backend/app/api/m8_responses.py`, `backend/app/api/routes/agent_runs.py`, generated OpenAPI/client, frontend Agent event contract and OpenAPI tests
- owner: M8 stage 3 backend/frontend contract
- blocks_current_stage: NO
- blocks_m8_exit_gate: NO
- blocks_m9_entry: NO
- safe_continuation: production API queues the server-owned safe default; optional Live verification remains an explicit authorized backend smoke only
- resolution: `AgentRunCreateRequest.mode` is now the single literal `PLAN_AND_EXPLAIN`; no frontend event or generated type offers provider selection
- focused_verification: OpenAPI asserts the single const mode; generated client, frontend type/build and Stage-2 no-credential degradation tests pass
- security/scientific impact: prevents unreviewed external model calls, cost and project-data disclosure from becoming a client-selected option

### M8-ISSUE-0015

- stage: 4
- severity: HIGH
- status: RESOLVED
- area: Open Design integration entry
- requirement: production UI synchronization requires `READY_FOR_CODEX_INTEGRATION=YES`
- observed: Stage 4 entered with `READY_FOR_CODEX_INTEGRATION=NO` because the authoritative fixture catalog lacked a cancellable non-terminal run and a retryable ToolCall combined with retry/restart capability
- expected: both positive intent paths are represented by typed fixtures, remain fail-closed for foreign/unknown/stale facts, preserve fixture state, and pass focused Open Design revalidation before production route integration
- root_cause: Stage 3 froze negative and partial states but omitted the two combined positive capability states identified as `M8-OD-0001` and `M8-OD-0005`
- affected_files: `frontend/src/features/agent-workspace/fixtures/index.ts`, `frontend/src/features/agent-workspace/mutations.ts`, `frontend/scripts/check-m8-fixtures.test.ts`, Open Design acceptance documents
- owner: M8 stage 4 Codex
- blocks_current_stage: NO after resolution
- blocks_m8_exit_gate: NO
- blocks_m9_entry: NO
- safe_continuation: modify only Codex-owned fixture, event guard, route/deep-link and test infrastructure; do not integrate or alter pure UI before readiness is revalidated
- resolution: four typed fixtures, stricter deterministic retry checks and Codex-owned Open Design reacceptance completed; `READY_FOR_CODEX_INTEGRATION=YES`
- focused_verification: fixture guard 6/6 with 59 assertions plus focused Cancel/Retry Dialog browser 2/2, including pending prevention, masked intent-only logging and unchanged business Props
- security/scientific impact: prevents UI capability projection from authorizing cancellation or repeat execution without matching server facts

### M8-ISSUE-0016

- stage: 4
- severity: HIGH
- status: RESOLVED
- area: production Agent UI loading transition
- requirement: the pure Agent Workspace must render loading/error/empty/ready transitions without violating React Hook ordering
- observed: the first production browser run failed when query loading changed to ready because `useMemo` existed after conditional early returns
- expected: all Hooks execute in a stable order for every `Loadable` state
- root_cause: Open Design used a Hook for a trivial derived three-item list below loading/non-ready returns; the Preview normally remounted fixtures and did not expose the production transition
- affected_files: `frontend/src/features/agent-workspace/ui/AgentWorkspace.tsx`, focused production route browser test
- owner: M8 stage 4 Codex controlled UI synchronization
- blocks_current_stage: NO after resolution
- blocks_m8_exit_gate: NO
- blocks_m9_entry: NO
- safe_continuation: remove the unnecessary memoization without changing visual output or business state
- resolution: replaced the post-conditional `useMemo` with a plain derived constant
- focused_verification: production loading-to-ready and deep-link fallback browser tests rerun without Hook-order console errors
- security/scientific impact: availability defect only; no permission, Approval or scientific fact semantics changed

### M8-ISSUE-0017

- stage: 4
- severity: MEDIUM
- status: RESOLVED
- area: production mutation reconciliation
- requirement: confirmation UI must close only after a changed server AgentRun projection arrives and must not obscure the authoritative result
- observed: create-run returned 202 and restored the new Run deep-link, but the local Create Dialog remained open after the new `run.id` loaded
- expected: action Dialog state is discarded when authoritative `run.id/status` changes; displayed business state comes from the refetched projection
- root_cause: the pure Preview remounted fixtures while the production route preserves the component across search/query transitions
- affected_files: `frontend/src/features/agent-workspace/ui/AgentWorkspace.tsx`, focused production route browser test
- owner: M8 stage 4 Codex controlled UI synchronization
- blocks_current_stage: NO after resolution
- blocks_m8_exit_gate: NO
- blocks_m9_entry: NO
- safe_continuation: observe server Run identity/status only; do not derive success from mutation transport state
- resolution: close Create/Cancel/Retry Dialogs when authoritative Run ID or status changes
- focused_verification: create returns 202, URL restores new Run ID, Dialog closes and the `ACCEPTED` server projection is visible
- security/scientific impact: prevents stale confirmation UI from implying that transport acceptance or a local dialog state is the durable Agent result

### M8-ISSUE-0018

- stage: 4
- severity: HIGH
- status: RESOLVED
- area: real vertical side-effect/Approval chain
- requirement: run the isolated Project -> AgentRun -> read Tool -> Job -> Approval -> resume -> deterministic output chain through PostgreSQL, API, SDK, Celery and Valkey
- observed: before remediation, infrastructure and the production route passed but no truthful approved transformation chain existed
- expected: available PostgreSQL/Celery/Valkey infrastructure plus typed side-effect wrappers and durable Approval-bound resume execute without duplicate facts
- root_cause: production wrapper/resume reconciliation was missing after the Stage 1/3 interruptions
- affected_files: local PostgreSQL/Valkey/Celery environment, `backend/app/agent_runtime/tool_gateway.py`, `orchestrator_service.py`, Worker and vertical tests
- owner: M8 stage 5 centralized backend/verification
- blocks_current_stage: NO; Stage 4 is an integration/problem-collection stage and all independent work is complete
- blocks_m8_exit_gate: NO after resolution
- blocks_m9_entry: NO after resolution
- safe_continuation: use Recorded mode for deterministic model behavior and report it truthfully; domain outputs still come only from real Services/Workers
- resolution: implemented and passed an isolated upload -> Agent profile Tool -> Data Quality Worker -> CleaningPlan preview -> external Approval -> durable Agent resume -> DataTransformation Worker -> new DatasetVersion -> final server-fact summary chain. A second chain proves rejected Approval creates no transformation.
- focused_verification: final clean-room PostgreSQL suite PASS, 489 passed / 3 skipped; no-database 253 passed / 3 skipped; duplicate deliveries are unclaimed and one formal transformation Job/output exists
- security/scientific impact: verification and capability gap; current fail-closed boundary prevents self-approval, duplicate formal writes and fabricated deterministic results

### M8-ISSUE-0019

- stage: 5
- severity: HIGH
- status: RESOLVED
- area: migration/ORM/database test isolation
- requirement: nullable JSON summaries must satisfy database object constraints and guard-negative tests must not poison the shared PostgreSQL session
- observed: `ToolCall.safe_output_summary=None` bound as JSON null and violated `ck_tool_calls_json_objects`; a mismatched append-only error assertion skipped rollback and caused a large cascade
- expected: Python `None` binds as SQL NULL; every intentional DB guard failure rolls back in `finally`
- root_cause: missing `JSONB(none_as_null=True)` and fragile negative-test cleanup
- affected_files: `backend/app/models.py`, `backend/tests/agent_runtime/test_service.py`
- owner: M8 Stage 5
- blocks_current_stage: NO after resolution
- blocks_m8_exit_gate: NO
- blocks_m9_entry: NO
- safe_continuation: keep the object-only database CHECK and append-only/terminal triggers unchanged
- resolution: corrected ORM binding and made all M8 DB guard tests transaction-safe
- focused_verification: clean-room database suite PASS, 489 passed / 3 skipped
- security/scientific impact: prevents invalid JSON state and false cascading failures; no security boundary was relaxed

### M8-ISSUE-0020

- stage: 5
- severity: MEDIUM
- status: RESOLVED
- area: migration/API/browser Gate reliability
- requirement: Alembic drift, Agent create replay and browser Gate results must reflect repository facts
- observed: three model-declared indexes were absent from 0019; AgentRun hash included transport request IDs; Playwright reused an unrelated server on port 5173 and one focus test was flaky under full parallel load
- expected: zero Alembic drift, same business payload replays across request IDs, and browser tests use an isolated port
- root_cause: interrupted Stage 1/3 integration plus non-CI `reuseExistingServer`
- affected_files: `backend/app/alembic/versions/0019_m8_agent_runtime.py`, `backend/app/agent_runtime/service.py`, Stage 5 commands
- owner: M8 Stage 5
- blocks_current_stage: NO after resolution
- blocks_m8_exit_gate: NO
- blocks_m9_entry: NO
- safe_continuation: business payload mismatch remains 409; do not weaken browser assertions
- resolution: added the three indexes, excluded request/correlation transport metadata from the business hash, and ran Playwright on isolated ports
- focused_verification: Alembic check PASS; M8 API replay PASS in 487-test database suite; full browser 169 passed / 2 skipped; flaky focus test 3/3 on rerun
- security/scientific impact: preserves idempotency and migration correctness; no scientific semantics changed

## Stage Summary

- open blocking M8 Exit issues: 0
- non-exit open/accepted issues: 3 (`0005`, `0006`, `0007`)
- resolved issues: 17 (`0001`, `0002`, `0003`, `0004`, `0008`, `0009`, `0010`, `0011`, `0012`, `0013`, `0014`, `0015`, `0016`, `0017`, `0018`, `0019`, `0020`)
- current stage blockers: 0

`M8_EXIT=PASS`

`M8_COMPLETION=APPROVED`

`M9_ENTRY=ALLOWED`

`M8_STAGE_RESULT=PASS_WITH_ISSUES`

`NEXT_STAGE_EXECUTED=NO`
