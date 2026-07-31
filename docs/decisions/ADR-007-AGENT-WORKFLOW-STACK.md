<a id="adr-007-agent-workflow-stack"></a>

# ADR-007: Use one RECA Orchestrator with reviewed SDK and ARS assets

ADR ID: `ADR-007-AGENT-WORKFLOW-STACK`

## Status

Accepted on 2026-07-31

Documentation status: `Conditional Approval`

## Context

OpenAI Agents SDK provides useful runtime mechanics, and ARS-Codex provides research workflow assets. Neither may replace RECA's project, evidence, approval, Tool, or audit model.

## Decision

- Plan the OpenAI Agents SDK as the M8 runtime dependency for one controlled RECA `ResearchOrchestrator`.
- Map SDK Function Tools to the existing RECA Tool whitelist and Service layer.
- Do not include free multi-Agent coordination, arbitrary Shell/SQL/Python execution, or P0 handoffs.
- Treat SDK Session as conversation continuity only and SDK Trace as telemetry only.
- Persist authoritative usage, invocation, Tool, approval, and run facts in existing RECA records.
- Allow conditional selective or full ARS-Codex reuse under [ADR-001](./ADR-001-ARS-CODEX-USAGE.md), but select exact paths only after an experiment, file-level license review, attribution plan, and RECA contract mapping.
- Keep Prompt manifests Git-managed from M1; formal Agent runtime remains M8.

Tracing must minimize or disable sensitive model inputs, outputs, Tool arguments, and document content unless explicitly required and governed. Runtime failure and degradation must remain visible.

## Non-substitution rules

- SDK Session is not `ResearchProject`.
- SDK Trace is not `AuditLog`, `AgentRun`, `ToolCall`, or `ModelInvocation`.
- ARS workflow state is not RECA business state.
- ARS reuse does not authorize new Tool names or permissions.

## Alternatives considered

- Adopt the SDK and ARS architecture unchanged: rejected because it creates competing state and authority.
- Implement all runtime mechanics from scratch: rejected unless the M8 spike finds unacceptable SDK coupling.
- Copy ARS assets immediately: rejected because exact assets, licenses, quality gain, and modifications are not yet approved.

## Consequences

- M8 requires approval-resume, trace-minimization, usage-accounting, and audit reconciliation tests.
- ARS-Codex remains not copied and not a runtime dependency at this decision date.
- Single-Orchestrator and M8 boundaries remain unchanged.

## References

- [Master plan](../source-research/OPEN_SOURCE_INTEGRATION_MASTER_PLAN.md)
- [OpenAI Agents SDK research](../source-research/projects/openai-agents-sdk.md)
- [ARS-Codex source record](../source-research/academic-research-skills-codex.md)
- [ADR-001](./ADR-001-ARS-CODEX-USAGE.md)
