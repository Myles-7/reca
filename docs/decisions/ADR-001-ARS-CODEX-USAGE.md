<a id="adr-001-ars-codex-usage"></a>

# ADR-001: Use ARS-Codex as a non-runtime research reference

ADR ID: `ADR-001-ARS-CODEX-USAGE`

## Status

Accepted

## Date

2026-07-30

## Decision owners

RECA Team

## Scope

RECA 0.1 Competition Edition

## Source record

[`docs/source-research/academic-research-skills-codex.md`](../source-research/academic-research-skills-codex.md)

## Context

ARS-Codex packages mature academic-research workflow prompts, routing rules,
human checkpoints, integrity protocols, schemas, deterministic validators, and
test corpora. Its default product form is a Codex Skill and prompt-driven
workflow suite, not a Web backend with database-owned domain state.

RECA requires persisted project facts, immutable artifacts, versioned domain
objects, service-enforced authorization and approval, deterministic statistics,
allowlisted Agent tools, and complete auditability. RECA is currently at M0:
these business capabilities are approved in design documents but are not yet
implemented in the running product.

The upstream snapshot uses CC BY-NC 4.0. It is not an unreviewed runtime or
wholesale source-copy dependency for a competition project that may later be
distributed or commercialized.

## Decision

RECA uses the fixed ARS-Codex snapshot
`f8d6b061efe98564a3f554c917fce66dcef6ca54` only as:

1. a research source for academic-workflow decomposition;
2. a reference for routing, checkpoint, integrity, and degradation concepts;
3. a source of ideas for RECA-owned schemas, prompts, fixtures, and tests.

RECA will not:

1. add ARS-Codex as a runtime, build, package, container, or deployment
   dependency;
2. make Agent sessions or Material Passports the source of business truth;
3. import multi-role prompts as independently stateful product Agents;
4. let model output replace deterministic statistics, figures, hashes,
   document parsing, or version checks;
5. copy prompts, schemas, scripts, or test corpora wholesale;
6. enable external cross-model content transfer without a separate provider,
   data-classification, consent, and audit decision.

All adopted ideas must be independently expressed through RECA-owned domain
models, services, policies, prompts, schemas, tests, and user interfaces.

## Alternatives considered

### Install ARS-Codex as a runtime dependency

- Benefit: fast access to its workflow prompts.
- Rejected: product behavior would depend on a Codex installation and
  conversation state rather than RECA's database, authorization, and API
  contracts.

### Copy upstream prompts and scripts into RECA

- Benefit: lower short-term authoring effort.
- Rejected: CC BY-NC 4.0 obligations and future distribution uncertainty;
  copied content would also bypass RECA's own contracts and cross-platform
  testing requirements.

### Use a free multi-Agent team as the product core

- Benefit: mirrors upstream role naming.
- Rejected: duplicated context, conflicting state, hard-to-audit approvals,
  and unstable demonstration behavior. RECA retains one orchestrator with
  prompt modes and allowlisted tools.

### Store workflow state in an Agent session or Material Passport

- Benefit: simple conversational continuation.
- Rejected: sessions are not durable, queryable, project-authorized business
  state. RECA uses a read-only derived context snapshot instead.

## Architectural mapping

```text
ARS-Codex concept
    ↓ independent RECA specification
RECA domain/service contract
    ↓ authorization + approval + version checks
Allowlisted deterministic tool or model task
    ↓ schema validation + audit
Persisted RECA result
```

The Material Passport concept maps only to a read-only,
database-regenerable `ProjectContextSnapshot`. It must never become a second
writeable source of truth.

The ARS router maps to a future `StageResolver` inside RECA's single
`ResearchOrchestrator`. The resolver uses persisted project state and service
queries, not conversation memory.

## Timing

- M1: implement Project, Artifact, Approval, Job, audit, isolation, and
  degradation foundations. Do not implement the Agent runtime.
- M2–M7: implement and test the deterministic research capabilities and
  evidence chain.
- M8: implement context snapshots, stage resolution, RECA-owned prompt
  contracts, allowlisted tools, and the single orchestrator.

Agent schemas may be designed earlier, but no Agent may execute formal side
effects before the corresponding service and approval contracts are complete.

## Consequences

### Positive

- RECA gains mature workflow and test ideas without coupling product behavior
  to a Codex installation or conversation session.
- Database state, approvals, deterministic computation, and evidence lineage
  remain authoritative.
- Prompts and schemas evolve with RECA's own versioning and golden tests.
- The upstream non-commercial license does not silently enter the runtime
  dependency graph.

### Cost

- RECA independently authors and validates every adopted prompt, schema,
  policy, and test fixture.
- Pattern adoption waits for the relevant RECA domain object and service.
- Upstream improvements require periodic manual review rather than automatic
  package upgrades.

### Risk controls

- Pin every research review to a source commit.
- Record each adopted pattern and its RECA owner.
- Use clean-room wording and implementation.
- Run similarity and license review before release if any direct reuse is
  proposed.
- Do not add ARS-Codex to `THIRD_PARTY_NOTICES.md` merely for idea-level
  research; add the appropriate notice and license material if direct
  copyrightable content is ever incorporated or distributed.

## Revisit triggers

Revisit this ADR if:

- RECA proposes direct code, prompt, schema, or fixture reuse;
- the upstream license changes;
- RECA's distribution or commercial model changes;
- an officially supported API/runtime integration becomes necessary;
- M8 requirements materially change the single-orchestrator architecture.
