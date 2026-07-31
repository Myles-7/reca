# Open-Source Research Phase 5: Agent SDK and ARS Workflow Assets

Document version: `1.0.0`

Document status: `Conditional Approval`

Last updated: 2026-07-31

## 1. Scope

This phase researched only:

- `openai/openai-agents-python`;
- `Imbad0202/academic-research-skills-codex`.

Research used fixed clones of the current GitHub repositories and inspected
README, licenses, manifests, source trees, Agent/workflow definitions, prompts,
policies, examples, tests, evaluations, scripts, hooks, CI and runtime
assumptions. It also compared the findings with RECA's current architecture,
data model, Agent Tool contracts, M1 governance and M8 roadmap.

No upstream Prompt, code, script, test, fixture or other content was copied.
No formal Agent contract, ADR decision, code, dependency, Compose service, CI,
migration or lock file was changed.

Project records:

- [OpenAI Agents SDK research](../../source-research/projects/openai-agents-sdk.md)
- [ARS-Codex source record](../../source-research/academic-research-skills-codex.md)

## 2. Executive decision

```text
OpenAI Agents SDK
= DIRECT_DEPENDENCY candidate at M8
+ one RECA ResearchOrchestrator
+ existing allowlisted Function Tool wrappers
+ structured output and HITL mechanics
- SDK Session/Trace as business authority
- handoffs in P0
- arbitrary hosted, MCP, Shell, SQL or Python execution

ARS-Codex
= selective ADAPT_AND_VENDOR candidate
+ scoping, claim verification, revision safeguards, prompts and golden tests
+ fixed CC BY-NC 4.0 attribution boundary
- automatic full-runtime adoption
- Material Passport as RECA state
- free multi-Agent topology
- actual copy in this research phase
```

The two projects are complementary: the SDK can provide M8 orchestration
mechanics, while ARS-Codex provides candidate workflow, Prompt, policy and test
assets. Neither project replaces RECA's project, evidence, approval or audit
model.

## 3. Fixed upstream facts

| Project | Default branch | Research commit | Latest release/tag | License | Runtime |
| --- | --- | --- | --- | --- | --- |
| OpenAI Agents SDK | `main` | `0ffa36840cb812488738f6fc5be3d3a1f51397b7` | `v0.19.1` | MIT | Python `>=3.10` |
| ARS-Codex | `main` | `f8d6b061efe98564a3f554c917fce66dcef6ca54` | `v0.1.22` | CC BY-NC 4.0 | Codex Skill/plugin; Python-backed validators and scripts |

Both repositories were active and not archived at the research snapshot. The
ARS root license is recorded from the actual fixed `LICENSE`; GitHub's API did
not provide a reliable SPDX classification for it, so this report uses the
license text rather than guessing from API metadata.

## 4. Decision matrix

| Project | Recommended mode | Runtime state | Milestone | Adapter/boundary | Primary risk |
| --- | --- | --- | --- | --- | --- |
| OpenAI Agents SDK | `DIRECT_DEPENDENCY` plus a RECA-owned orchestration integration layer | Planned, not installed | M8 | Yes at the orchestration boundary; Function Tools preserve existing names and call Services | Session/Trace/hosted tools becoming shadow authority or widening execution |
| ARS-Codex | `ADAPT_AND_VENDOR` selected assets; `DESIGN_REFERENCE` for broad workflows | Research reference; no content copied | M1+ assets, M2-M8 feature integration | Path-level adaptation to Prompt, Project, Approval, Evidence and Tool contracts | CC BY-NC review, context pollution and importing file/multi-role state assumptions |

## 5. OpenAI Agents SDK findings

### 5.1 One RECA Orchestrator

Use exactly one SDK `Agent` as `ResearchOrchestrator`. It receives a deterministic
stage decision and a minimal ProjectContextSnapshot, then can call only the Tools
allowed for that stage. Specialized behavior should initially be Prompt modes,
not separately stateful Agents.

The manager pattern fits RECA better than handoffs. If later experimentation
needs a specialist, `Agent.as_tool()` preserves outer-manager ownership better
than transferring the conversation through a handoff, but either choice requires
a later architecture decision. Handoffs are not P0.

### 5.2 Function Tool mapping

Every SDK Function Tool must preserve one existing RECA Tool contract:

```text
Tool name and input Schema
-> SDK typed wrapper
-> Service authorization and project isolation
-> deterministic/domain implementation
-> existing result Schema
-> ToolCall and related audit records
```

SDK decorators may generate transport schemas but cannot rename Tools or become
the contract authority. Generic database, network, filesystem, Shell, SQL,
Python and patch tools stay outside the whitelist.

### 5.3 Session is not ResearchProject

SDK Sessions solve short-term conversation history and continuation. They do not
model project members, Artifact versions, formal approvals, milestone gates,
EvidenceSpan or data lineage. Session history can be compacted, provider-hosted
or cleared without changing the authoritative ResearchProject.

The only acceptable relationship is an optional operational Session reference
on AgentRun. The database remains authoritative and each run regenerates the
minimal snapshot it needs.

### 5.4 Trace is not RECA audit

SDK tracing is valuable observability, but its lifecycle and payload are not the
same as accountable domain audit. RECA must keep `AuditLog`, `AgentRun`,
`ToolCall` and `ModelInvocation` as authoritative append-oriented records.

Trace data can contain user input, Prompt text, model input/output, tool
arguments/results, handoff content, guardrail data, errors and metadata. Default
RECA configuration should exclude sensitive payloads, use correlation IDs, and
avoid exporting full evidence or datasets. Trace retention and access require an
explicit later implementation decision.

### 5.5 Usage to ModelInvocation

SDK `Usage` exposes request and token totals, cached/reasoning details and
per-request entries. Each actual model request must populate or reconcile one
RECA ModelInvocation with model/provider, Prompt ID/version/hash, timestamps,
status and requested/max/effective data access. AgentRun totals are derived
operational summaries, not replacements for per-invocation records.

### 5.6 Human-in-the-loop and Tool approval

SDK `needs_approval`, interruptions and serializable RunState are suitable
mechanics for pausing a high-risk tool. RECA authority remains the version-bound
ApprovalRecord and Service revalidation.

On resume, RECA must check that the approving actor, project, target object and
target version still match and that the approval is valid. Read-only/candidate
Tools remain automatic; low-risk adoption uses light confirmation; prohibited
capabilities are absent from the tool list.

### 5.7 M1 governance and M8 runtime

M1 creates Prompt manifests, AI Schemas, golden tests, ModelInvocation and model
data-access governance. M2-M7 build the deterministic Services and evidence
contracts. M8 installs and configures the SDK to consume those assets.

This ordering prevents Agent runtime from becoming the place where Tool names,
Prompt versions, approval rules or scientific truth are improvised.

### 5.8 MCP, hosted tools and error handling

MCP and hosted tools remain outside the initial M8 surface unless a specific
server maps to an existing Tool and has fixed filtering, data scope, approvals,
timeouts, degradation and audit. Hosted/local sandbox tools are particularly
incompatible with RECA's prohibition on arbitrary execution.

SDK errors such as max-turn, model behavior/refusal, tool timeout, MCP
cancellation and guardrail tripwires must map to AgentRun/ToolCall/
ModelInvocation failure plus DegradationRecord when applicable. Failure cannot
be reported as formal success, and retry cannot duplicate a completed side
effect.

## 6. ARS-Codex asset decisions

| Asset | Decision | Primary RECA mapping |
| --- | --- | --- |
| `SCOPING` | `ADAPT_AND_VENDOR` | ResearchQuestionVersion and Scoping Schema at M2 |
| `DEEP_RESEARCH` | `ADAPT_AND_VENDOR` | QueryPlan and literature search at M2-M3 |
| `PRISMA` | `DESIGN_REFERENCE` | Literature reporting/checklists, later enhancement |
| `MATERIAL_PASSPORT` | `REWRITE_FOR_RECA` | Artifact lineage and ProjectContextSnapshot at M1-M7 |
| `CLAIM_VERIFICATION` | `ADAPT_AND_VENDOR` | Claim, EvidenceSpan, ClaimEvidenceLink and AuditResult at M6-M7 |
| `MODE_ROUTING` | `REWRITE_FOR_RECA` | deterministic StageResolver at M8 |
| `CHECKPOINT` | `REWRITE_FOR_RECA` | NONE/LIGHT_CONFIRMATION/FORMAL_APPROVAL and project state |
| `REVIEW_REVISION` | `ADAPT_AND_VENDOR` | ManuscriptIssue/Version and re-review at M6-M7 |
| `PAPER_REVIEW` | `DESIGN_REFERENCE` | review rubrics and dissent preservation at M6-M7 |
| `PROMPTS` | `ADAPT_AND_VENDOR` | Git-managed Prompt manifests from M1 onward |
| `POLICY_MARKERS` | `REWRITE_FOR_RECA` | Tool, approval, evidence and degradation policy |
| `TESTS` | `ADAPT_AND_VENDOR` | contract and workflow tests at M1-M9 |
| `GOLDEN_CASES` | `ADAPT_AND_VENDOR` | Prompt/evidence/revision golden tests at M1-M9 |
| `SCRIPTS` | `ADAPT_AND_VENDOR` | reviewed deterministic test/development utilities |
| `HOOKS` | `DO_NOT_USE` | replace desired behavior with explicit RECA CI/jobs/Services |

### 6.1 Exact workflow mapping

| ARS asset | RECA object or module | Milestone | Integration method |
| --- | --- | --- | --- |
| Scoping | ResearchQuestionVersion / Scoping Schema | M2 | selected Prompt/rubric adaptation |
| Deep Research | QueryPlan / literature search | M2-M3 | workflow patterns through existing providers and Services |
| Material Passport | Artifact / provenance / ProjectContextSnapshot | M1-M7 | rewrite onto database facts and derived snapshot |
| Claim Verification | Claim / EvidenceSpan / AuditResult | M6-M7 | selected prompts, schemas and deterministic tests |
| Mode Router | StageResolver | M8 | deterministic rewrite; one Orchestrator |
| Checkpoint | Approval / project state | M1-M8 | risk-based policy mapping, not checkpoint-for-every-step |
| Prompts | Prompt manifest | M1+ | selective Vendor after license/path review |
| Tests | Golden tests | M1-M9 | selected fixtures and validators with provenance |

### 6.2 What cannot be imported unchanged

- Material Passport cannot become a writable business-state source.
- ARS Agent-team language cannot create free multi-Agent RECA state.
- ARS candidate citations cannot become EvidenceSpan without location/source
  validation.
- ARS checkpoint frequency cannot force ApprovalRecord on read-only work.
- ARS Prompt policy markers cannot replace executable Service/policy checks.
- ARS scripts cannot become a generic Shell or Python Tool.
- ARS hooks cannot add invisible runtime behavior.

## 7. Vendor option comparison

| Dimension | Selective `vendor/ars-adapted/` | Full `vendor/academic-research-skills-codex/` |
| --- | --- | --- |
| Effect | Concentrates on visible RECA improvements | Retains maximum upstream breadth |
| Initial speed | Requires asset selection, then faster feature adaptation | Fast snapshot import, slower path to a coherent RECA integration |
| License isolation | Compact copied-path and modification ledger | Strong folder isolation but broad special-license distribution surface |
| Maintenance | Smaller targeted upstream diffs | Large snapshot and validation burden |
| Context pollution | Low | High; broad prompts/docs can duplicate authority |
| Architecture fit | Forces explicit Project/Approval/Evidence mapping | Greater risk of importing file-state and multi-role assumptions |
| Recommendation | Preferred | Deferred unless a measured spike proves material benefit |

Neither directory was created in this phase.

## 8. License and attribution decision

ARS-Codex remains:

```text
usage_intent: NONCOMMERCIAL_INTENT_DECLARED
license: CC BY-NC 4.0 at the fixed snapshot
commercialization_re_review_required: true
```

This is not a legal conclusion that school competition use is NonCommercial.
Before copying, RECA must identify exact paths, re-check root and file/upstream
licenses, preserve author/project attribution, include the license, record the
repository and Commit, mark modifications, isolate special-license coverage and
update third-party notices as applicable.

OpenAI Agents SDK is MIT. Dependency adoption or any source Vendor/copy must
retain the required copyright and permission notice and follow RECA's ordinary
source and modification ledger.

## 9. Recommended validation sequence

### SDK spike at M8

1. Pin `openai-agents==0.19.1` in an isolated implementation branch.
2. Configure one Orchestrator and no handoffs.
3. Wrap two existing read-only RECA Tools.
4. Use a fake model for deterministic call order and structured output.
5. persist AgentRun, ToolCall and ModelInvocation correlation.
6. prove Session removal does not affect ResearchProject.
7. prove sensitive trace payloads are absent.
8. pause/resume one formal approval and reject stale/foreign approvals.
9. test timeout, cancellation, max turns and provider degradation.
10. verify the forbidden execution surface is absent.

### ARS asset spikes

1. M2 Scoping Prompt/rubric against existing Scoping Schema and golden cases.
2. M6-M7 claim verification against supported, absent and conflicting
   EvidenceSpan fixtures.
3. Revision claim-drift/test assets against immutable ManuscriptVersion inputs.
4. Compare quality, token/context cost and maintenance against RECA-native
   baselines before selecting copied paths.

## 10. Risks and unresolved questions

- ARS competition use has declared noncommercial intent but no legal conclusion.
- Exact copied ARS files and any file-level licenses remain undecided.
- SDK v0.x upgrade and RunState serialization compatibility require a pin/test
  policy.
- The initial tracing backend and retention policy remain undecided.
- The need for any Session backend beyond RECA-managed conversation references
  remains unproven.
- Handoff remains deferred; no P0 use case justifies its ownership complexity.
- Full ARS snapshot Vendor remains a candidate only, not the recommendation.
- Actual package/Vendor/Fork incorporation requires a later implementation PR
  and attribution update.

## 11. Contract preservation

This phase changed no Requirement ID, Acceptance ID, API path, Error Code,
Schema name, Agent Tool name, Enum value, milestone or ADR decision.

The following remain unchanged:

- one controlled `ResearchOrchestrator`;
- formal Agent runtime at M8;
- Prompt governance established at M1;
- SDK Session is not business authority;
- ProjectContextSnapshot is minimal, read-only and database-regenerable;
- Tool names and Schemas remain defined by existing RECA contracts;
- model data access retains requested/max/effective levels;
- EvidenceSpan absence is never fabricated;
- formal statistics come only from deterministic programs;
- high-risk writes require the applicable ApprovalRecord;
- Agent cannot self-approve or execute arbitrary code;
- ADR-001's formal decision conclusion is unchanged.

## 12. Phase result

Status: `PASS`

The SDK has a viable, bounded M8 integration path, and ARS-Codex now has an
asset-level map rather than a vague reuse permission. The preferred combined
direction is one RECA Orchestrator implemented with the SDK and selected ARS
Prompt/workflow/test assets adapted behind existing RECA contracts.

## 13. No-code-change confirmation

No backend, frontend, dependency, Compose configuration, CI workflow, migration,
generated client, lock file, Vendor directory, Submodule, upstream source,
Prompt, script, test or fixture was added or modified. Only the two source
research records and this Phase 5 report are in scope.
