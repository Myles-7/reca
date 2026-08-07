# M8 Implementation Plan

Date: 2026-08-06
Milestone: M8 Research Orchestrator Agent
Current stage: 5 complete; M8 Exit passed
Stage decision: `PASS_WITH_ISSUES`

## 1. Repository Baseline

| Fact | Observed |
| --- | --- |
| repository | `D:/桌面/Recas/reca` |
| branch | `feat/m2-research-literature` |
| HEAD | `3f8219c321b4850576fbf7ab5af844752b1f6e87` |
| upstream | `origin/feat/m2-research-literature` |
| ahead/behind at entry | 0 / 0 |
| worktree at entry | clean; no tracked diff or untracked files |
| migration head | `0018_m7_evidence_export` |
| next migration | `0019_m8_agent_runtime` |
| Python | 3.14.2 |
| Pydantic / FastAPI | 2.13.4 / 0.139.0 |
| Celery / redis client | 5.5.3 / 5.2.1 |
| M7 entry decision | `M8_ENTRY=ALLOWED` |

No user or Open Design modifications were present at stage entry. No reset,
clean, stash operation, destructive checkout, commit, tag or push was used.

## 2. M7 Consumption Boundary

M8 may consume authorized project-scoped projections for Claims, evidence links,
graphs, completeness, audits, readiness, Exports, Jobs, Approvals, packages,
Manifests and Artifacts. Every Tool execution must reload project membership,
source scope, current status, version, hash, invalidation and Approval facts.
Unknown, missing, stale, foreign, invalidated or hash-mismatched facts fail closed.

M8 cannot create ACTIVE evidence links, modify completeness, approve its own
Export, skip readiness, rewrite packages or turn suggestions into scientific fact.
The retained Babel advisory remains visible as `M8-ISSUE-0007`.

## 3. Stage-0 Gap Audit

- Existing: Git-managed Prompt manifest; Mock/Recorded/Live ModelInvocation
  governance; Project, membership, ApprovalRecord, AuditLog, Job and ProcessingRun;
  M1-M7 Services, API, Worker and structured workspaces.
- Missing by design at entry: AgentRun and ToolCall tables/Services; Context builder;
  StageResolver; versioned ToolRegistry; ResearchOrchestrator; Agent API; Agent panel.
- ModelInvocation is an existing table from migration 0007. M8 will add nullable
  AgentRun/ToolCall links plus usage/latency/redaction fields; it will not rebuild it.
- The authoritative Tool names are those in `AGENT_TOOL_CONTRACTS.md`. Roadmap
  names such as `start_literature_search` and `execute_approved_cleaning_plan`
  are summaries and will not become duplicate stable Tool names.

## 4. SDK Decision

Decision: pin `openai-agents==0.19.1` as the minimal direct dependency.

Evidence:

- installed and imported under Python 3.14.2;
- disposable fake-model Spike: 6 passed;
- exactly one `ResearchOrchestrator`, two read-only fake Service Tools;
- strict Function Tool schemas and Pydantic structured output passed;
- max turns, timeout, cancellation, provider failure and invalid output passed;
- input, output, Tool input and Tool output guardrails tripped as expected;
- usage maps to request/input/output/total ModelInvocation fields;
- Session deletion did not alter synthetic Project/AgentRun facts;
- formal Tool paused and resumed only after an external valid Approval projection;
- foreign, rejected and stale/hash-mismatched Approval projections did not resume;
- no handoff, Agent-as-tool, MCP server, hosted tool or arbitrary execution registered.

Mandatory adapter policy:

- always construct `RunConfig(trace_include_sensitive_data=False)`; SDK 0.19.1
  defaults this field to true;
- do not persist raw RunState. Persist only an encrypted/minimized, expiring,
  SDK/registry/prompt/schema-version-bound resume payload if stage 2 proves needed;
- invalidate resume state on version, project, actor, Approval, payload hash,
  snapshot or registry drift;
- no SDK object crosses the `agent_runtime` internal boundary;
- SDK removal falls back to existing direct structured model tasks and M1-M7 pages.

No optional SDK extras were requested. The SDK core package has an unavoidable
`mcp` transitive dependency; production configuration and registry exposure stay zero.

## 5. ARS Decision

Decision: `NO_COPY_FOR_M8_CORE`.

The synthetic claim-verification comparison found identical Schema validity,
source retention, conflict transparency and prompt-injection blocking, while the
ARS checkpoint concept increased estimated prompt tokens. No ARS Prompt, code,
workflow, script, test corpus or runtime was copied. Any later proposal requires
exact paths, fixed commit, file-level license/attribution, modification record,
commercialization review and a new measurable benefit.

## 6. Frozen Runtime Contract

1. **Topology**: one `ResearchOrchestrator`; no P0 handoff, Agent-as-tool or free
   multi-Agent topology.
2. **SDK**: exact 0.19.1; minimal dependency; Session is continuity only; Trace is
   minimized telemetry only; RunState is untrusted resumable mechanics; usage is
   copied into ModelInvocation; removal preserves direct structured workflows.
3. **Migration**: one additive `0019_m8_agent_runtime`, down revision 0018; creates
   AgentRun/ToolCall and extends ModelInvocation. No production table in stage 0.
4. **AgentRun**: project/user scoped, type fixed to RESEARCH_ORCHESTRATOR for P0;
   statuses `CREATED, PLANNING, WAITING_USER_INPUT, WAITING_APPROVAL, CALLING_TOOL,
   REVIEWING, COMPLETED, FAILED, CANCELLED`; terminal history immutable.
5. **ToolCall**: append-only audit record; statuses `REQUESTED, WAITING_APPROVAL,
   RUNNING, COMPLETED, FAILED, DENIED, CANCELLED`; terminal guard; registry version,
   redacted input/output summaries and hashes; Idempotency, Job and Approval links.
6. **ModelInvocation**: extend existing table with nullable AgentRun/ToolCall links,
   token input/output/total, request count, latency and redaction policy version.
   Retry creates a new invocation.
7. **Messages/resume**: persist user-message safe summary/hash and assistant safe
   structured summary as append-only Agent events or minimal supporting rows;
   never default-store full sensitive conversation. Resume state is encrypted,
   expiring, version-bound and disposable, not the sole audit record.
8. **ProjectContextSnapshot**: read-only projection with schema version, revision,
   project, stage, source object versions, artifacts, approvals, blockers, allowed
   actions, generated time and canonical SHA-256. AgentRun stores safe metadata only.
9. **StageResolver**: deterministic Service/projection facts first; output stage,
   blockers, approvals, allowed next actions, candidate Tool names, reason codes and
   source versions. Golden matrix covers empty, RQ, literature, data, quality,
   analysis, figure, manuscript, claim/evidence/export and unknown/stale/denied.
10. **ToolRegistry**: immutable code registry metadata includes stable name/version,
    strict input/output schema, risk, approval class, data access, timeout, max calls,
    allowed stages, permissions, preconditions and handler.
11. **Tool availability**: a Tool is enabled only when a tested Service or explicit
    read-only projection exists. Missing or unsafe mappings return stable fail-closed
    `TOOL_UNAVAILABLE`/precondition errors and never use a generic caller.
12. **Policies**: Guardrail, ToolPolicy, ApprovalGate, ModelDataPolicy and source
    resolver are server-owned. Untrusted documents remain content. requested/max/
    effective data access is enforced and audited.
13. **Wrapper boundary**: wrappers receive typed actor/project context, never a DB
    Session; they do not call Routers or trust model-provided IDs/status/version/hash.
14. **Async**: AgentRun execution uses the existing Worker/Job authority when latency
    exceeds request budget. Cancel is cooperative; retry/resume reloads authority;
    duplicate requests and deliveries cannot duplicate formal side effects.
15. **API**: project-scoped create plus run/tool detail, message and cancel endpoints;
    Envelope responses; no-disclosure 404; Idempotency-Key for mutations; version/
    If-Match where mutable input is involved; no ToolCall public mutation.
16. **Frontend route**: one project-scoped Agent panel inside the existing project
    shell, recommended `/projects/$projectId/agent`; no second product shell and no
    dependency of M1-M7 pages on Agent availability.
17. **Frontend contract**: generated client -> adapter -> query/mutation -> Container
    -> pure View. ViewModel distinguishes suggestion, system fact, deterministic
    result, user confirmation and formal Approval. Unknown/permission uncertainty
    removes write actions. Typed fixtures are preview-only and guarded from production.
18. **Provider modes**: Mock and Recorded are deterministic and explicitly labeled;
    Live requires complete Settings credentials and approved data scope. Missing live
    credentials degrade visibly and do not fail offline M8 tests.
19. **Tests**: focused unit/DB/Worker, StageResolver golden, Tool contract, approval,
    replay, injection, schema smuggling, loop/timeout/cancel, trace/session redaction,
    API/no-disclosure, browser/fixture and clean-room gates scale by stage.
20. **Exit/M9**: M8 exit requires no arbitrary execution, cross-project access,
    self-approval, sensitive leakage or unaudited Tool/model calls; all exit blockers
    resolved; direct pages intact. M9 entry additionally requires stable recorded/
    offline behavior, dependency/license evidence and truthful provider reporting.

## 7. Formal Tool-to-Service Freeze

`READY` means an accepted Service/projection exists but still needs an M8 wrapper.
`BUILD_PROJECTION` means stage 1 must build a read-only projection. `GAP` means the
Tool remains disabled until a safe Service contract is completed.

| Tool group | Stable Tools | Existing authority | Stage-0 result |
| --- | --- | --- | --- |
| project/approval | `get_project_state`, `get_pending_approvals` | projects overview, approvals list; snapshot absent | BUILD_PROJECTION / READY |
| RQ/query | `get_research_question`, `parse_research_question`, `generate_query_plan` | research question Service/scoping; query plan Service/generation | READY |
| literature | `list_project_literature`, `get_literature_record`, `search_literature`, `verify_literature_record`, `suggest_literature_decision` | literature list/detail/search/import; no standalone verify/suggestion Service | READY except verify/suggestion GAP |
| documents/evidence | `parse_document`, `extract_literature_fields`, `get_literature_matrix`, `retrieve_evidence`, `summarize_evidence_set`, `generate_topic_candidates` | document parse; extraction/matrix; evidence summary/topic jobs; candidate retrieval wrapper absent | READY except retrieve GAP |
| datasets/quality | `get_dataset_profile`, `get_dataset_version`, `profile_dataset` | dataset/version and data-quality run Services | READY |
| cleaning | `suggest_cleaning_plan`, `preview_cleaning_plan`, `apply_approved_transformations` | cleaning create/preview/Approval/execute Services | READY; suggestion wrapper must stay candidate-only |
| analysis | `get_analysis_plan`, `get_analysis_result`, `suggest_analysis_plan`, `validate_analysis_assumptions`, `run_descriptive_statistics`, `run_group_comparison`, `run_correlation`, `run_simple_linear_regression` | analysis plan/validate/Approval/run/result Services; suggestion Service absent | READY except suggestion GAP; execution dispatches by approved method |
| figures | `get_figure`, `recommend_figure`, `render_figure` | figure get/recommend/confirmation/render Services | READY |
| manuscript | `get_manuscript_issues`, `check_manuscript`, `suggest_manuscript_issues` | manuscript check/issue Services; model suggestion Service absent | READY except suggestion GAP |
| claim/graph | `get_claim_evidence_graph`, `audit_claim` | evidence graph projection and audit/readiness Services | READY; dedicated wrapper/projection required |
| export | `get_export_readiness`, `export_repro_package` | deterministic readiness and formal Approval/Job export Service | READY; export always revalidates Approval/hash |

Forbidden registry count must remain zero for Shell, Python, SQL, filesystem,
ApplyPatch, generic HTTP, arbitrary URL, dynamic import, MCP discovery/server,
hosted execution, self-approval, original overwrite and formal result modification.

## 8. Stage Plan

| Stage | Scope | Status |
| --- | --- | --- |
| 0 | entry audit, SDK/ARS Spike, contract freeze | COMPLETE: PASS_WITH_ISSUES |
| 1 | migration, AgentRun/ToolCall, snapshot, resolver, registry, base policies | COMPLETE: PASS_WITH_ISSUES |
| 2 | one Orchestrator, wrappers, ApprovalGate, pause/resume, Worker | COMPLETE: PASS_WITH_ISSUES |
| 3 | Agent API/OpenAPI/frontend contracts/fixtures/Open Design handoff | COMPLETE: PASS_WITH_ISSUES |
| 4 | production UI integration and vertical E2E issue collection | COMPLETE: PASS_WITH_ISSUES |
| 5 | centralized fixes, full Exit Gate and M9 handoff | COMPLETE: PASS_WITH_ISSUES |

Next authorized input: M8 stage 5 prompt only.

## 9. Stage-0 Verification Record

| Command/check | Result |
| --- | --- |
| Python 3.14 import and dependency resolution for `openai-agents==0.19.1` | PASS |
| SDK + ARS disposable Spikes | PASS, 6 passed |
| Prompt manifest baseline plus Spikes | PASS, 12 passed |
| existing ModelInvocation DB baseline | NOT COMPLETED, bounded command timed out at 120 seconds; `M8-ISSUE-0011` |
| Ruff check for Spike files | PASS |
| Ruff format check for Spike files | PASS after formatting |
| `uv lock --check` | PASS, 153 packages resolved |
| dependency/source/license/notice consistency | PASS focused inspection |
| `git diff --check` | PASS |

Stage 0 changes dependencies and documentation only. It creates no migration,
database table, Agent API/OpenAPI/generated client or frontend route/component.

`M8_STAGE_0=COMPLETE`

`M8_STAGE_RESULT=PASS_WITH_ISSUES`

`NEXT_STAGE_EXECUTED=NO`

## 13. Stage-4 Implementation Record

Stage 4 reaccepted Open Design, registered the single project-scoped production
Agent route and completed focused browser/runtime integration. It did not run the
Stage-5 Exit Gate or implement missing side-effect wrappers/durable Approval
resume.

- Resolved `M8-OD-0001` and `M8-OD-0005` with four typed fixtures and stricter
  retry authorization; `READY_FOR_CODEX_INTEGRATION=YES`.
- Added `/projects/$projectId/agent`, Container injection, generated-adapter
  create/message/cancel transport, server-driven Run restoration, safe route
  fallback and static source/Approval navigation.
- Preserved the existing shell and direct M1-M7 workspaces; production imports no
  fixtures or Design Preview code.
- Fixed loading/ready Hook ordering and closed action Dialogs only after changed
  authoritative Run projections.
- Recorded runtime contracts passed; the real PostgreSQL/Celery/Valkey
  side-effect/Approval E2E was then completed in Stage 5.

| Stage-4 command/check | Result |
| --- | --- |
| M8 fixture guard | PASS, 6/6 and 59 assertions |
| UI boundary / production mock guards | PASS, 4/4 and 6/6 |
| frontend format/lint/build | PASS, 2522 modules |
| focused Open Design + production browser | PASS, 4/4 |
| SDK/Policy/Worker/OpenAPI focused pytest | PASS, 23/23 |
| PostgreSQL Agent API + Service pytest | NOT COMPLETED, 30-second timeout |
| Alembic heads | PASS, single `0019_m8_agent_runtime` |
| full Exit/clean-room/Live provider | NOT RUN by stage boundary |

Stage-4 migration/API/dependency boundary: no migration, API path, OpenAPI or
dependency change was added in Stage 4. Production frontend routing and test
coverage changed; the existing Stage-1 migration and Stage-3 six API paths remain
unchanged.

Next authorized input: M8 Stage 5 centralized issue repair and complete Exit/M9
Entry gates.

`M8_STAGE_4=COMPLETE`

`M8_STAGE_RESULT=PASS_WITH_ISSUES`

`NEXT_STAGE_EXECUTED=NO`

## 12. Stage-3 Implementation and Stage-1/2 Recovery Review

Stage 3 registered the single authoritative Agent API surface and froze the
frontend business/design boundary. It did not register a production frontend
route, build the visual Agent panel, run browser vertical E2E, or execute stage 4.

- Added six formal endpoints: project-scoped create, run detail, message,
  ToolCall list/detail and cancel. Mutations require `Idempotency-Key`; create,
  message and cancel return 202 for accepted facts only. Reads use no-disclosure
  project authorization.
- Added strict public DTOs with raw status plus `known_status`, allowed actions,
  disabled reasons, safe event summaries, bounded snapshot summary, and separate
  AgentRun/ToolCall/ModelInvocation/Job/Approval/source links. Raw prompt,
  RunState, Session, trace, provider internals and complete Tool args/results are
  absent.
- Recovered two interrupted Stage-1-to-3 contracts: aligned public goal/message
  limits with the 500-character safe persistence schema, and made AgentEvent/
  AgentRun mutation plus shared idempotency record use one transaction so a
  process interruption cannot append a duplicate message on replay.
- Kept provider execution mode server-owned: the public business contract accepts
  only `PLAN_AND_EXPLAIN`; Recorded/Live selection is not a user or UI capability.
- Regenerated the FastAPI OpenAPI document and all four Hey API generated client
  files through the formal generator, then added the hand-written AgentRunsApi
  adapter for headers, errors, messages, cancellation and pagination.
- Added `agent-workspace` ViewModel, mapper, query, mutation, controller hook,
  route/deep-link contract, Props/Events and 54 typed fixtures. Suggestions,
  facts, deterministic results, user confirmations and formal Approvals remain
  distinct. Unknown permissions/status and stale sources clear write capability.
- Added the M8 fixture semantic guard and reused the production-mock and UI
  ownership guards. Fixtures import no adapter/query/mutation/container and no
  production data path imports fixtures.
- Published `M8_OPEN_DESIGN_HANDOFF.md` with protected/editable paths, information
  architecture, fail-closed semantics, responsive/accessibility acceptance and
  `READY_FOR_OPEN_DESIGN=YES`.

Stage-3 boundary: no new migration revision or dependency; `0019` remains the
single head. API/OpenAPI/generated/adapter and frontend business contracts changed;
the production route and complete visual panel remain stage 4 only.

| Stage-3/recovery command/check | Result |
| --- | --- |
| Ruff check/format and mypy for affected Agent Service/API | PASS, 3 typed source files |
| Stage 1-2 migration/Registry/Policy/SDK/Worker plus M8 OpenAPI no-database tests | PASS, 31 passed |
| Agent API path/header/schema/security contract | PASS, 6 paths and 4 focused tests |
| Alembic source heads and offline SQL | PASS, single `0019_m8_agent_runtime` |
| formal OpenAPI/generated-client flow | PASS, 152 total paths and 4 generated files |
| frontend format/lint/type/Vite production build | PASS |
| M8 fixture semantic guard | PASS, 54 fixtures / 6 tests / 42 assertions |
| production mock guard | PASS, 6 tests; clean scan |
| UI ownership boundary guard | PASS, 4 tests; clean scan |
| focused PostgreSQL Agent API + AgentRun/ToolCall Service tests | NOT COMPLETED, bounded 30-second timeout; `M8-ISSUE-0011` |
| Playwright/production Agent route/vertical E2E/clean-room/full Exit Gate | NOT RUN by stage boundary |

`M8_STAGE_3=COMPLETE`

`M8_STAGE_RESULT=PASS_WITH_ISSUES`

`NEXT_STAGE_EXECUTED=NO`

## 11. Stage-2 Implementation Record

Stage 2 added the production-owned SDK boundary and Worker execution path without
registering any API, OpenAPI schema, generated client or frontend surface.

- Added one `ResearchOrchestrator` only, driven by the Git-managed
  `research-orchestrator@1.0.0` PromptContract and strict structured output.
  Runtime assertions require empty handoffs/MCP servers and reject prohibited or
  unknown Tool registration.
- Added a RECA-owned SDK adapter with deterministic input/output/Tool guardrails,
  max turns, overall timeout/cancel propagation, exception normalization,
  `trace_include_sensitive_data=False`, correlation metadata and usage capture.
- Added explicitly labeled Mock/Recorded deterministic models and an opt-in Live
  OpenAI-compatible provider. Missing Live credentials fail with
  `MODEL_PROVIDER_UNAVAILABLE`; no provider or scientific result is fabricated.
- Added typed Function Tool wrappers for `get_project_state`,
  `get_pending_approvals` and `retrieve_evidence`. The Service gateway owns fresh
  Session creation, actor/project reload, stage-1 ToolPolicy and ToolCall/Audit
  reconciliation; no SDK Agent/Tool receives a database Session.
- `retrieve_evidence` now maps to the accepted native project-scoped retrieval
  Service. Returned source text is bounded and marked as untrusted content while
  source IDs/hashes and limitations are preserved.
- Added AgentRun execution reconciliation to ModelInvocation and safe AgentEvent
  summaries, including usage, redaction metadata and explicit degradation that
  preserves direct structured-workspace fallback.
- Added `AGENT_ORCHESTRATION` to the existing Job/Worker boundary, same-project
  AgentRun/Job association, minimal queue identity, explicit handler registration,
  worker-side actor/run/job revalidation and terminal failure/cancel handling.
- SDK resume bindings cover SDK/registry/prompt/project/actor/snapshot drift and
  in-memory approval state is never logged or persisted. Stage 5 replaced the
  earlier gap with deterministic rebuild and a typed FORMAL_APPROVAL wrapper;
  the Worker still does not persist raw SDK RunState.

Stage-2 boundary: `0019` additionally includes the Agent orchestration Job enum and
AgentRun Job FK; no new migration revision, API or frontend change. No stage-2
dependency/lock change was required; the existing locked SDK and pytest-asyncio
were synchronized into the local backend virtual environment only.

| Stage-2 command/check | Result |
| --- | --- |
| Ruff check and format check for affected Agent/Worker/tests | PASS |
| focused mypy and ty for Agent runtime/Worker | PASS, 12 source files |
| Prompt/Agent/runtime/SDK focused no-database tests | PASS, 32 passed / 11 deselected |
| single Orchestrator / strict Tool / trace / usage assertions | PASS |
| injection, prohibited capability, loop, timeout, invalid output and stale resume negatives | PASS |
| stage-0 SDK approval/session/trace Spike rerun | PASS, 5 SDK Spike tests in aggregate set |
| Worker handler registration and Mock/Recorded determinism | PASS |
| missing Live credential degradation | PASS |
| `pip check` | PASS, no broken requirements |
| Alembic offline SQL and single source head | PASS, `0019_m8_agent_runtime` |
| focused PostgreSQL AgentRun/ToolCall/ModelInvocation tests | NOT COMPLETED, bounded 30-second timeout |
| OpenAPI/generated/frontend/Playwright/clean-room/full Exit Gate | NOT RUN by stage boundary |

`M8_STAGE_2=COMPLETE`

`M8_STAGE_RESULT=PASS_WITH_ISSUES`

`NEXT_STAGE_EXECUTED=NO`

## 10. Stage-1 Implementation Record

Stage 1 implemented only the SDK-independent database/domain foundation. No
ResearchOrchestrator was run, no Agent API or frontend route was registered, and
no stage-2 wrapper/Worker integration was started.

- Added additive migration `0019_m8_agent_runtime`: `agent_runs`, `tool_calls`,
  append-only safe-summary `agent_events`, nullable same-project correlations on
  AuditLog/ModelInvocation, and usage/latency/redaction fields on the existing
  ModelInvocation table. The migration does not rebuild M1-M7 tables and refuses
  a lossy downgrade when M8 history exists.
- Added row-locked AgentRun/ToolCall Services with idempotency mismatch detection,
  terminal guards, new-record retries, no-disclosure lookup and safe AuditLog
  projections. Formal resume requires an approved same-project external
  ApprovalRecord and matching payload hash.
- Added authorized ProjectContextSnapshot construction, canonical hashing,
  stale/rebuild checks and deterministic StageResolver coverage for all ten
  existing ProjectStage values plus degraded/denied/hash-mismatch cases.
- Frozen exactly 40 stable Tool names. Final Stage-5 availability enables five
  tested typed wrappers: `get_project_state`, `get_pending_approvals`,
  `retrieve_evidence`, `profile_dataset` and `apply_approved_transformations`.
  The other 35 retain metadata but fail closed. Prohibited execution/MCP/generic
  capabilities are absent.
- Added SDK-independent ToolPolicy, ApprovalGate, ModelDataPolicy, source/hash and
  schema validation, untrusted-content boundaries, limits and trace redaction.

Stage-1 boundary: migration added; API/OpenAPI/generated client/frontend unchanged;
no new stage-1 dependency; no production SDK Orchestrator or Worker registered.

| Stage-1 command/check | Result |
| --- | --- |
| Ruff check/format for affected files | PASS |
| focused mypy and ty | PASS, 8 source files |
| Agent/Prompt/runtime no-database focused tests | PASS, 23 passed / 11 deselected |
| Registry / StageResolver / policy negative matrix | PASS, 40 formal Tools / 0 prohibited registered / 10 stages |
| migration Python compile and Alembic offline SQL to 0019 | PASS |
| Alembic source heads | PASS, single `0019_m8_agent_runtime` |
| focused PostgreSQL AgentRun/ToolCall tests | NOT COMPLETED, bounded 30-second timeout |
| online 0018 upgrade/repeat/check/downgrade and ModelInvocation history | NOT RUN, PostgreSQL unavailable and Docker daemon absent |
| SDK orchestration/frontend/Playwright/clean-room/full Exit Gate | NOT RUN by stage boundary |

`M8_STAGE_1=COMPLETE`

`M8_STAGE_RESULT=PASS_WITH_ISSUES`

`NEXT_STAGE_EXECUTED=NO`

## 14. Stage-5 Exit Review Record

Stage 5 stopped feature expansion, repaired the remaining durable resume and
Approval-bound side-effect gaps, and ran the complete repository clean-room Gate.

- Enabled five tested typed wrappers, including `profile_dataset` and the formal
  `apply_approved_transformations` side effect; 35 other formal names remain
  versioned but fail closed until typed wrappers exist.
- Added missing 0019 indexes, preserved JSON object constraints with SQL NULL,
  made database guard tests transaction-safe and removed transport request IDs
  from the AgentRun business idempotency hash.
- Eliminated migration typing diagnostics without changing migration history.
- Added a minimized append-only deterministic-rebuild checkpoint. Raw SDK
  RunState, Prompt body and complete Tool args/results are not persisted.
- Added external ApprovalRecord-bound Agent Worker resume, Cleaning Service
  execution, DataTransformation Worker reconciliation and final server-fact summary.
- Verified the production Agent route, typed fixtures, deep-link fallback,
  accessibility checks and direct M1-M7 workspace availability.
- Verified rejected Approval, duplicate Approval callback and duplicate Worker
  delivery create no unauthorized or duplicate formal side effect.

| Stage-5 Gate | Result |
| --- | --- |
| Ruff format/check, strict mypy and ty | PASS; mypy 161 source files, ty zero diagnostics |
| complete no-database suite | PASS, 253 passed / 3 skipped / 236 deselected |
| clean-room PostgreSQL suite | PASS, 489 passed / 3 skipped |
| empty/repeated migration, Alembic check, single head | PASS, `0019_m8_agent_runtime` |
| Worker/Celery/Valkey/MinIO, API restart/persistence | PASS |
| frontend format/lint/generated/build and guards | PASS; fixture 6/6 with 59 assertions |
| full isolated Playwright | PASS, 169 passed / 2 skipped; focused flaky rerun 3/3 |
| Secret scans and Python dependency audit | PASS |
| Bun dependency audit | PASS with retained LOW Babel advisory `M8-ISSUE-0007` |
| optional authorized Live provider smoke | NOT RUN; no approved credential/data/cost boundary |
| durable resume after process loss | PASS, deterministic rebuild; no raw SDK RunState |
| governed Data Quality -> Job -> Approval -> resume chain | PASS, Recorded model plus real API/Service/Worker facts |

The frozen M8 product Exit contract is satisfied. Recorded model behavior is
reported truthfully, while all Approval, Job, transformation, DatasetVersion and
audit facts are produced by real Services and Workers.

Next authorized input: M9 stage prompt. M9 was not executed in this stage.

`M8_EXIT=PASS`

`M8_COMPLETION=APPROVED`

`M9_ENTRY=ALLOWED`

`M8_STAGE_RESULT=PASS_WITH_ISSUES`

`NEXT_STAGE_EXECUTED=NO`
