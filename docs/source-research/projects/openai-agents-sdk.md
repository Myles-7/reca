# OpenAI Agents SDK source research

Document version: `1.0.0`

Document status: `Conditional Approval`

Last researched: 2026-07-31

Phase summary: [Agent SDK and ARS workflow research](../../reports/OPEN_SOURCE_RESEARCH_PHASE_5_AGENT.md)

## Upstream

| Field | Verified value |
| --- | --- |
| Repository | <https://github.com/openai/openai-agents-python> |
| Default branch | `main` |
| Pinned research commit | `0ffa36840cb812488738f6fc5be3d3a1f51397b7` |
| Commit date | `2026-07-31T14:23:33+09:00` |
| Latest release/tag | `v0.19.1` |
| Package version | `openai-agents==0.19.1` |
| License | MIT |
| License file | `LICENSE` |
| Main language | Python |
| Minimum runtime | Python `>=3.10` |
| Dependency manifest | `pyproject.toml`; resolved development lock in `uv.lock` |
| Test framework | Pytest, pytest-asyncio, pytest-mock, pytest-xdist, coverage and integration tests |
| CI workflows | `tests.yml`, docs, issue automation, publish and release workflows |
| Maintenance status | Active; repository was not archived and the pinned commit was current during research |

Research links use the pinned commit so later upstream changes do not silently
change this evidence record.

## Repository structure

| Path | Purpose |
| --- | --- |
| `src/agents/agent.py` | Agent configuration, tools, handoffs, output type and `Agent.as_tool()` |
| `src/agents/run.py` | `Runner`, model/tool loop, streaming, limits and resume behavior |
| `src/agents/tool.py` | Function, hosted, MCP, shell and patch tool definitions and approval hooks |
| `src/agents/guardrail.py` | Input and output guardrails |
| `src/agents/tool_guardrails.py` | Tool input/output guardrails |
| `src/agents/handoffs/` | Handoff contracts, history filtering and transfer behavior |
| `src/agents/memory/` | Session implementations and storage integrations |
| `src/agents/run_state.py` | Serializable paused-run state and approve/reject operations |
| `src/agents/run_context.py` | Application context wrapper, usage and run-scoped approvals |
| `src/agents/usage.py` | Request and token accounting |
| `src/agents/tracing/` | Traces, spans, processors and exporters |
| `src/agents/mcp/` | Local MCP servers, hosted MCP conversion, filtering and approvals |
| `src/agents/models/` | OpenAI and provider model interfaces |
| `src/agents/exceptions.py` | SDK exception taxonomy |
| `examples/` | Basic, tool, HITL, handoff, MCP, memory, research and realtime examples |
| `tests/` | 296 Python test files at the research commit |
| `integration_tests/` | 26 Python integration-test files at the research commit |
| `docs/` | Agent, Runner, Tool, HITL, Session, tracing, MCP and pattern guides |

## Core capabilities

### Agent

`Agent` binds instructions, model selection, tools, MCP servers, handoffs,
input/output guardrails and an optional structured `output_type`. It is runtime
configuration, not a durable business aggregate.

For RECA, one SDK `Agent` should represent the controlled
`ResearchOrchestrator`. Prompt text must come from the Git-managed RECA Prompt
manifest rather than becoming unversioned strings scattered through Agent
constructors.

### Runner

`Runner.run`, `run_sync` and `run_streamed` execute the model/tool loop. The loop
continues until final output, interruption, configured error or `max_turns`.
`Runner` is a useful execution engine, but it does not decide RECA project stage,
authorization, source validity or whether a result is a formal business fact.

RECA must invoke it only after `StageResolver`, `ProjectContextSnapshotBuilder`,
`PromptRegistry`, `ToolPolicy`, `ApprovalPolicy` and `ModelDataPolicy` have
produced the allowed run configuration.

### Function Tool

The SDK can derive a strict JSON-compatible tool schema from typed Python
functions. `function_tool` also supports timeouts, error formatting, enablement
and `needs_approval`.

RECA mapping is deliberately one-to-one:

```text
existing RECA Tool name
-> SDK FunctionTool public name
-> validated Tool arguments
-> existing application Service
-> existing Tool result Schema
-> ToolCall audit record
```

The wrapper must not expose ORM Sessions, arbitrary network access, filesystem
access or a generic command executor. It must not rename an existing Tool or
invent a second tool contract.

### Handoff and Agent-as-tool

Handoff transfers conversation and answer ownership to another Agent. By
contrast, `Agent.as_tool()` runs a bounded nested Agent and returns its result to
the manager Agent. Both are technically supported, but neither is needed for
RECA Competition Core.

RECA should keep handoffs out of P0. They add a second ownership surface for
context, policy and final responses and work against the existing single
orchestrator decision. If a later narrow specialist is justified, prefer a
manager-owned `Agent.as_tool()` experiment before conversation handoff, and
require a separate architecture decision.

### Guardrails

The SDK supports input, output, tool-input and tool-output guardrails with
tripwires. These are useful as defense-in-depth for schema conformance,
disallowed content, data-scope checks and model-output screening.

Guardrails are not substitutes for Service authorization, database constraints,
deterministic statistical validation or ApprovalRecord. A guardrail can stop a
run; it cannot create a trustworthy scientific fact merely by passing.

### Session

SDK Sessions manage conversation history across runs. Available implementations
and optional storage integrations can reduce manual transcript plumbing.

An SDK Session cannot replace `ResearchProject`, project membership, versions,
Artifact lineage, approvals or milestone state. Conversation history may be
deleted, summarized, truncated or stored by a provider, whereas RECA business
state must be queryable and authoritative in the database.

Recommended boundary:

```text
SDK Session ID -> optional operational reference on AgentRun
ResearchProject ID -> authoritative RECA project scope
ProjectContextSnapshot -> regenerated read-only run input
```

### Context

`RunContextWrapper` carries application context, usage and run-scoped approval
decisions into tools, handoffs and guardrails. RECA should place only minimal,
non-secret execution references in this context, such as project ID, actor ID,
AgentRun ID and snapshot hash.

It should not embed a writable Project object, database Session, model secret or
unredacted whole-project snapshot. Serialized `RunState` can include application
context, so anything placed here must be treated as persisted/transmitted data.

### Tracing

The SDK emits traces and spans for Agents, model calls, tools, guardrails,
handoffs and custom operations. Custom processors can export elsewhere, and
`trace_include_sensitive_data` can suppress some model/tool payload content.

SDK traces are operational telemetry only. They cannot replace:

- `AuditLog`, which records accountable business actions;
- `AgentRun`, which records the governed orchestration run;
- `ToolCall`, which records each allowlisted tool execution;
- `ModelInvocation`, which records Prompt version, data access and usage.

Trace payloads may include prompts, user inputs, model outputs, tool arguments,
tool results, guardrail data, handoff data, error text and metadata. RECA should
default to sensitive-data exclusion, avoid exporting raw evidence/full datasets,
use a stable correlation ID rather than business payloads, and apply retention
and access rules independently of the SDK default exporter.

### Usage

The SDK aggregates request count, input/output tokens, cached tokens, reasoning
tokens and per-request usage entries. RECA should copy provider-returned usage
into the corresponding `ModelInvocation`, along with model/provider, Prompt
version, invocation timestamps and requested/max/effective data-access levels.

`Usage` on a run context is convenient aggregation, but individual
`ModelInvocation` rows remain necessary because one AgentRun may make multiple
model calls with different prompts, tools, data scopes or failures.

### Human in the loop

Function tools can declare `needs_approval=True` or a call-sensitive approval
function. A pending decision interrupts the run; `RunState.approve` or
`RunState.reject` records an SDK runtime decision and the original top-level run
can resume.

RECA should map approval as follows:

| RECA policy | SDK behavior | RECA authority |
| --- | --- | --- |
| `NONE` | Tool runs after ordinary policy checks | ToolPolicy and Service |
| `LIGHT_CONFIRMATION` | Application confirmation before tool adoption | Existing confirmation UX/audit |
| `FORMAL_APPROVAL` | Interrupt, create/verify version-bound ApprovalRecord, then resume | ApprovalRecord and Service |
| `PROHIBITED` | Tool is absent from Agent tool list | Tool whitelist |

SDK approval state is not itself a sufficient ApprovalRecord. On resume, RECA
must re-check actor, project, target version, expiry and current object state.

### Structured output

`output_type` can use Pydantic-compatible types and structured model outputs.
This is a strong fit for RECA's existing AI Schema contracts. The generated SDK
schema must be compared with the registered RECA Schema; successful parsing does
not authorize a database write, promote a candidate to evidence, or validate a
statistical value.

### MCP and hosted tools

The SDK supports local MCP servers, hosted MCP tools and hosted execution tools.
These interfaces widen the execution and data-transfer boundary. RECA should not
enable arbitrary MCP discovery or general hosted Shell/ApplyPatch tools in P0.

An MCP/hosted capability may be considered only when it maps to an existing
allowlisted RECA Tool, has explicit server/tool filtering, fixed data access,
approval behavior, timeout/degradation semantics and auditable output. Provider
tool results remain candidates until RECA Service validation completes.

### Error handling

The inspected exception taxonomy includes `MaxTurnsExceeded`,
`ModelBehaviorError`, `ModelRefusalError`, `ToolTimeoutError`, MCP cancellation,
input/output guardrail tripwires and tool guardrail tripwires. Run configuration
also supports tool-not-found and tool-error formatting.

RECA should translate these into existing AgentRun, ToolCall, ModelInvocation and
DegradationRecord semantics. Errors must not be flattened into a successful
final answer. Retrying must preserve idempotency and must not repeat a completed
side effect merely because a model response was lost.

## Dependencies

Required package dependencies at `v0.19.1` include:

- `openai>=2.45.0,<3`;
- `pydantic>=2.12.2,<3`;
- `griffelib>=2,<3`;
- `typing-extensions>=4.12.2,<5`;
- `requests>=2,<3`;
- `websockets>=15,<17`;
- `mcp>=1.19,<2` for supported Python versions.

Optional extras cover voice, visualization, alternative model layers, SQLAlchemy,
Redis, encryption, MongoDB, sandbox providers and durable orchestrators. RECA
should start with the smallest core dependency set. Sandbox, voice, realtime,
durable-workflow and nonessential Session backends are outside the M8 P0 spike.

## Tests

The upstream test suite covers core run loops, tools, approvals, RunState
serialization, guardrails, handoffs, sessions, MCP, tracing, models, realtime,
voice and sandbox integrations. Tests use fake models and fake MCP servers for
deterministic unit coverage, plus a separate integration-test tree.

RECA should reuse testing ideas rather than copy upstream tests blindly:

- fake model scripts for deterministic tool-call sequences;
- approval interruption, rejection and resume cases;
- malformed structured output and unexpected tool calls;
- trace sensitive-data exclusion;
- usage reconciliation with ModelInvocation;
- handoff absence in the P0 configuration;
- retry/idempotency around Service side effects;
- cancellation and degradation propagation.

## Operational requirements

- server-side Python runtime with model-provider credentials;
- outbound model-provider access or an explicit recorded/mock mode;
- persistent RECA AgentRun/ToolCall/ModelInvocation records;
- optional short-term Session store, never the business database replacement;
- trace export disabled or minimized until privacy review;
- bounded turns, tool timeouts and cancellation handling;
- stable SDK version and Prompt/Tool definitions for paused-run resume;
- separate worker execution if Agent runs exceed request latency budgets.

## RECA current state

OpenAI Agents SDK is currently only `PLANNED_M8`. No package dependency,
runtime Agent, Session store, tracing exporter, handoff or hosted tool is present
as a result of this research phase.

RECA already defines the authoritative pieces the SDK must consume:

- one `ResearchOrchestrator`;
- deterministic `StageResolver`;
- database-derived `ProjectContextSnapshot`;
- Git-managed Prompt manifest established in M1;
- existing Agent Tool contracts and Service boundaries;
- `AgentRun`, `ToolCall`, `ModelInvocation`, `AuditLog` and `ApprovalRecord`;
- requested/max/effective model data-access semantics;
- explicit degradation records.

## Recommended integration mode

```text
DIRECT_DEPENDENCY at M8
+ RECA-owned orchestration adapter/configuration layer
+ one ResearchOrchestrator
+ existing Function Tool wrappers
+ RECA database audit authority
+ handoffs disabled for P0
```

This is a research recommendation, not an implementation claim or dependency
approval.

## What to reuse

- Runner model/tool loop and streaming result surface;
- typed Function Tools wrapping existing Services;
- structured output integration with registered RECA Schemas;
- input/output/tool guardrails as defense-in-depth;
- HITL interruption and serializable RunState for formal approval waits;
- Usage extraction for ModelInvocation;
- correlation-oriented tracing with sensitive content excluded;
- fake-model and deterministic orchestration test patterns;
- bounded error taxonomy and explicit degradation handling.

## What not to reuse

- free multi-Agent topology as RECA business architecture;
- conversation handoffs in Competition Core;
- SDK Session as ResearchProject or workflow authority;
- SDK traces as AuditLog or ToolCall authority;
- arbitrary Shell, Python, SQL, ApplyPatch or filesystem tools;
- unrestricted MCP discovery or hosted tool execution;
- SDK tool names that differ from existing RECA Tool contracts;
- model output as EvidenceSpan, formal statistics or final approval;
- full sensitive ProjectContextSnapshot in context, session or traces.

## Domain boundary

```text
RECA database and Services
  -> StageResolver / ProjectContextSnapshot / policies
  -> PromptContract + existing Tool registry
  -> OpenAI Agents SDK Runner
  -> candidate structured output / requested tool call
  -> RECA Schema + Service + approval + audit
  -> authoritative RECA state
```

The SDK owns orchestration mechanics inside one run. RECA owns identity,
authorization, project state, versions, evidence semantics, scientific truth,
approval and durable audit.

## Milestone

| Work | Milestone |
| --- | --- |
| Prompt manifest, AI Schemas, ModelInvocation and golden tests | M1 and subsequent feature milestones |
| Deterministic domain Services and Tool contracts | M1-M7 |
| SDK dependency and controlled orchestrator runtime | M8 |
| Offline/degradation and release validation | M8-M9 |

M1 governance is a prerequisite, not an early Agent runtime. M8 consumes the
Prompt contracts and deterministic capabilities established earlier.

## Risks

- rapidly evolving SDK behavior and paused-state compatibility;
- trace/session leakage of prompts, evidence or sensitive project content;
- duplicated authority if Session or Trace records are treated as domain state;
- hidden side effects from hosted or MCP tools;
- retrying non-idempotent tools after partial failures;
- schema drift between SDK-generated types and RECA contracts;
- adding handoffs because the SDK supports them rather than because RECA needs them;
- dependency expansion through unused optional extras.

## Validation spike

Before M8 implementation approval, build a disposable spike that:

1. installs the pinned SDK in an isolated branch/environment;
2. creates exactly one Orchestrator with two read-only existing Tool wrappers;
3. uses a fake model to force a deterministic tool-call sequence;
4. validates structured output against an existing RECA Schema;
5. records one AgentRun, ToolCall and ModelInvocation correlation chain;
6. proves SDK Session deletion does not affect ResearchProject state;
7. proves traces omit prompt/tool payloads when sensitive data is disabled;
8. interrupts one formal-approval tool and resumes only after a valid ApprovalRecord;
9. rejects stale/foreign-project approval on resume;
10. verifies no Shell, SQL, Python, ApplyPatch, unrestricted MCP or handoff is exposed;
11. measures cancellation, timeout, max-turn and provider-failure degradation;
12. confirms no stable API, Schema, Tool, Enum or milestone identifier changes.

## Attribution requirements

MIT permits dependency use, modification and redistribution subject to retaining
the copyright and permission notice in copies or substantial portions. If RECA
later vendors or selectively copies SDK code, record the pinned Commit, copied
paths, modifications and attribution in the third-party ledger. Ordinary package
dependency adoption still requires the normal dependency/source record.

## Update strategy

- pin an exact package version in the implementation PR;
- review release notes and migration guidance before every upgrade;
- run the RECA orchestration/approval/golden suite against the candidate version;
- do not resume serialized RunState across an untested SDK/Agent definition change;
- keep SDK-specific objects behind the M8 orchestration module;
- retain a removal path that falls back to direct provider calls for existing
  non-Agent M2/M3 model tasks;
- update this source record and attribution in the same PR as adoption.

## Sources

- [Repository at pinned commit](https://github.com/openai/openai-agents-python/tree/0ffa36840cb812488738f6fc5be3d3a1f51397b7)
- [Package manifest](https://github.com/openai/openai-agents-python/blob/0ffa36840cb812488738f6fc5be3d3a1f51397b7/pyproject.toml)
- [Agent implementation](https://github.com/openai/openai-agents-python/blob/0ffa36840cb812488738f6fc5be3d3a1f51397b7/src/agents/agent.py)
- [Runner implementation](https://github.com/openai/openai-agents-python/blob/0ffa36840cb812488738f6fc5be3d3a1f51397b7/src/agents/run.py)
- [Tool implementation](https://github.com/openai/openai-agents-python/blob/0ffa36840cb812488738f6fc5be3d3a1f51397b7/src/agents/tool.py)
- [Human-in-the-loop guide](https://github.com/openai/openai-agents-python/blob/0ffa36840cb812488738f6fc5be3d3a1f51397b7/docs/human_in_the_loop.md)
- [Tracing guide](https://github.com/openai/openai-agents-python/blob/0ffa36840cb812488738f6fc5be3d3a1f51397b7/docs/tracing.md)
- [MCP guide](https://github.com/openai/openai-agents-python/blob/0ffa36840cb812488738f6fc5be3d3a1f51397b7/docs/mcp.md)
- [MIT license](https://github.com/openai/openai-agents-python/blob/0ffa36840cb812488738f6fc5be3d3a1f51397b7/LICENSE)
