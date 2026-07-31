<a id="adr-001-ars-codex-usage"></a>

# ADR-001: Adopt ARS-Codex through licensed, effect-first reuse

ADR ID: `ADR-001-ARS-CODEX-USAGE`

## Status

Accepted, amended 2026-07-31

Documentation status: `Conditional Approval`

Decision version: `1.2.0`

## Date

Original decision: 2026-07-30

Current amendment: 2026-07-31

## Decision owners

RECA Team / Project Owner

## Scope

RECA 0.1 Competition Edition

## Source record

[Academic Research Skills Codex source record](../source-research/academic-research-skills-codex.md)

## Change record

| Version | Date | Status | Change |
| --- | --- | --- | --- |
| 1.0.0 | 2026-07-30 | Accepted | Limited ARS-Codex to non-runtime research reference and clean-room reimplementation |
| 1.1.0 | 2026-07-31 | Accepted / Conditional Approval documentation | Replaced blanket copy/runtime prohibitions with licensed effect-first reuse and explicit review gates |
| 1.2.0 | 2026-07-31 | Accepted / Conditional Approval documentation | Formalized selective/full Vendor choices, fixed source, zero-copy state, and the relationship to ADR-007 |

## Context

ARS-Codex packages mature academic-research workflows, routing rules, human
checkpoints, integrity protocols, schemas, deterministic validators, scripts and
test materials. These assets may materially improve RECA's effect, development
speed and demonstration stability.

The original ADR selected research-only, independent reimplementation because
the upstream snapshot uses CC BY-NC 4.0 and RECA's future distribution and
commercialization path was uncertain. That decision protected provenance but
made clean-room reimplementation the default even when licensed reuse could be
more effective.

The project owner has now declared the current intended use as personal
development/use and school-competition demonstration. The recorded purpose
status is:

```text
NONCOMMERCIAL_INTENT_DECLARED
```

This is an intent declaration, not a legal conclusion. This ADR does not claim
that a school competition, prize, sponsorship, public repository, download,
portfolio or hosted deployment is legally NonCommercial under CC BY-NC 4.0.

RECA still requires database-owned business state, immutable artifacts,
versioned domain objects, Service authorization, explicit high-risk approval,
deterministic statistics, allowlisted Tool contracts and auditable failures.
Reuse cannot replace those boundaries.

## Decision

RECA may reuse the fixed ARS-Codex snapshot
`f8d6b061efe98564a3f554c917fce66dcef6ca54` through any reviewed mode supported
by the open-source governance policy:

```text
PACKAGE_DEPENDENCY
INDEPENDENT_SERVICE
FORK
VENDOR
GIT_SUBMODULE
SELECTIVE_COPY
RESEARCH_REFERENCE
CLEAN_ROOM_REIMPLEMENTATION
```

For ARS-Codex specifically, RECA may:

1. selectively copy Prompts;
2. copy workflow templates;
3. copy scripts;
4. copy test structures and test materials;
5. Vendor the whole project;
6. Fork and modify the project;
7. use it as a development-time resource;
8. make it a runtime component after a separate architecture decision.

`CLEAN_ROOM_REIMPLEMENTATION` remains available when license, coupling,
commercialization or maintenance risk makes direct reuse unattractive. It is no
longer mandatory.

The formal project recommendation is conditional `SELECTIVE_VENDOR` for exact
Prompt, workflow, script, policy-marker, test or golden-case paths that show a
measurable RECA benefit. `FULL_VENDOR` is also permitted after a separate
path-level license and packaging review demonstrates that a complete snapshot is
more maintainable and does not introduce incompatible or unidentified content.
Neither mode is authorized as an implementation merely by this ADR.

## Mandatory prerequisites

Before direct copying, Fork, Vendor, Submodule or runtime incorporation:

1. verify the actual license text in the fixed upstream snapshot;
2. preserve CC BY-NC 4.0 and all applicable upstream notices;
3. preserve author and project attribution;
4. record repository, Commit/Tag and copied paths;
5. record modified paths and a modification summary;
6. identify any differently licensed vendored assets, fixtures or upstream projects;
7. keep upstream license coverage distinguishable from the future RECA root license;
8. update `THIRD_PARTY_NOTICES.md` when copyrightable content is actually incorporated or distributed;
9. do not describe upstream contributions as RECA's original work;
10. re-review before commercialization, sponsorship changes, public product deployment or materially different distribution;
11. record reviewer, review date, special restrictions and commercialization-review requirement;
12. obtain a separate architecture decision before runtime integration.

If the actual source has no license or an unknown source chain, it must not be
copied. Mere public availability or ability to Fork is not permission.

## Architecture constraints retained

Licensed reuse does not automatically change RECA's architecture:

- business truth remains in RECA's database, not Agent sessions or Material Passports;
- `ProjectContextSnapshot` remains a read-only, database-regenerable minimal snapshot;
- RECA retains one controlled `ResearchOrchestrator` rather than a free multi-Agent team;
- formal Agent runtime remains scheduled for M8;
- reuse does not automatically permit independently stateful Agents;
- model output cannot replace deterministic statistics, figures, hashes, parsing or version checks;
- writes remain mediated by Service, Schema, project authorization and the applicable confirmation level;
- external cross-model transfer remains separately consented and audited;
- failures and degradation remain user-visible.

Copied material must be adapted to RECA's own:

- ResearchProject and versioned domain state;
- Artifact and DatasetVersion immutability;
- `AUTO_ALLOWED`, `LIGHT_CONFIRMATION`, `FORMAL_APPROVAL` and `PROHIBITED` operation classes;
- EvidenceSpan and ClaimEvidenceLink semantics;
- Prompt manifest and ModelInvocation records;
- allowlisted Agent Tool contracts;
- deterministic calculation and audit requirements.

Direct reuse cannot silently introduce a second source of truth or bypass these
contracts.

## Runtime integration decision

ARS-Codex is not a runtime dependency at the time of this amendment. Runtime
use is permitted in principle only after a separate ADR defines:

- exact component and version;
- integration mode and deployment boundary;
- license/attribution packaging;
- data sent to the component;
- Service, Tool and approval mapping;
- failure, offline and removal strategy;
- testing and upgrade ownership.

Permission to consider runtime use is not evidence that runtime integration has
already occurred.

The M8 runtime relationship is governed by
[ADR-007](./ADR-007-AGENT-WORKFLOW-STACK.md). That ADR preserves one RECA
Orchestrator and does not make ARS-Codex a runtime dependency or permit free
multi-Agent operation.

## Adapter decision

ARS-Codex integration is not required to use a complex Adapter solely because
it is third-party. An Adapter is required when the selected component is an
unstable/replaceable external API, needs multiple implementations or offline
Mocking, would leak third-party objects into the domain layer, or creates a
license/security boundary.

A stable, small-interface library or copied isolated asset may be integrated
directly when that is cheaper to test and maintain. Direct integration still
cannot bypass Service, authorization, evidence, version or approval rules.

## Alternatives considered

### Continue mandatory clean-room reimplementation

Benefit: simplest separation from upstream expression and restrictive license
risk.

Rejected as the default because it discards mature assets, increases duplicated
work and conflicts with the project's effect-first competition objective. It
remains an optional mode.

### Copy without a provenance ledger

Benefit: fastest short-term import.

Rejected because it loses license, attribution, Commit and modification
traceability and could misrepresent third-party contributions as original.

### Import the full Agent architecture unchanged

Benefit: minimal adaptation work.

Rejected because license permission does not make session-owned state, free
multi-Agent coordination or uncontrolled side effects compatible with RECA's
database and evidence architecture.

### Permit runtime integration immediately

Benefit: fastest path to upstream behavior.

Rejected because no exact runtime component, license package, data boundary,
Tool mapping or removal strategy has been approved. A separate ADR is required.

## Consequences

### Positive

- Mature Prompt, workflow, script and test assets can be reused when lawful.
- Fork/Vendor/Selective Copy become legitimate engineering choices.
- Development can prioritize product effect and demo stability.
- Provenance and special-license boundaries remain explicit.
- RECA's trusted research architecture remains authoritative.

### Costs and risks

- CC BY-NC 4.0 use requires purpose and distribution review.
- Copied paths and modifications require ongoing maintenance.
- Upstream assets may contain separately licensed material.
- Commercialization or public productization may require replacement,
  relicensing or removal.
- Runtime use adds architecture, data-transfer and upgrade risk.

## Current incorporation state

At the time of this amendment:

```text
runtime_dependency: false
vendored_into_reca: false
fork_integrated: false
submodule_added: false
copied_content: none
third_party_notice_entry_for_ars: not_required_yet
```

This task changes policy only. It does not copy ARS-Codex Prompt, code, workflow,
script, schema, test or fixture content.

The fixed Commit remains the research and reuse-review baseline. Any later
adoption must record the exact copied paths and must not silently follow an
upstream branch or tag.

## Revisit triggers

Revisit this ADR when:

- a specific path is proposed for copying;
- a Fork, Vendor, Submodule or package/runtime dependency is proposed;
- the upstream license or fixed source changes;
- competition terms, prizes, sponsorship or distribution change;
- RECA moves toward commercialization or public product deployment;
- M8 architecture changes the single-orchestrator or Tool boundary;
- legal/license review produces a different conclusion.
