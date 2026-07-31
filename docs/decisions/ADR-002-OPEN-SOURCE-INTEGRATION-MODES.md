<a id="adr-002-open-source-integration-modes"></a>

# ADR-002: Standardize open-source integration modes

ADR ID: `ADR-002-OPEN-SOURCE-INTEGRATION-MODES`

## Status

Accepted on 2026-07-31

Documentation status: `APPROVED FOR M1 DEVELOPMENT`

Decision version: `1.0.1`

Current amendment: 2026-07-31

## Context

RECA has researched 26 upstream projects. A recommendation must distinguish an installed package, an independent service, copied source, a resource snapshot, a design reference, and a deferred option. Treating every mention as an implementation would produce false provenance and unclear ownership.

## Decision

The project-level decision matrix uses only these modes:

```text
ALREADY_INTERNALIZED_BASELINE
DIRECT_DEPENDENCY
DIRECT_DEPENDENCY_WITH_PROVIDER
ADAPTER_INTEGRATION
INDEPENDENT_SERVICE
ISOLATED_SERVICE
SELECTIVE_VENDOR
FULL_VENDOR
FORK
GIT_SUBMODULE
RESOURCE_SNAPSHOT
DESIGN_REFERENCE
DEVELOPMENT_ONLY
DEFERRED
DO_NOT_USE
```

The mode is a governance classification, not proof of implementation. Actual incorporation also requires an implementation status, pinned adopted version, license evidence, repository paths, attribution, fallback, and acceptance evidence as defined by [ADR-008](./ADR-008-IMPLEMENTATION-METADATA.md).

Direct integration is allowed for stable, narrow libraries when an abstraction would cost more than it protects. An Adapter or provider is required when an external API is replaceable, third-party objects could leak into the domain, offline substitution is required, or a license/security boundary needs isolation.

No integration mode may bypass RECA Services, project authorization, immutable originals, version lineage, deterministic formal results, approval rules, or audit records.

## Alternatives considered

- Require an Adapter for every upstream: rejected because it adds ceremony without consistent isolation value.
- Treat all researched projects as planned dependencies: rejected because research is not adoption.
- Permit ad hoc integration labels: rejected because cross-document comparison becomes unreliable.

## Consequences

- Every upstream has one normalized recommendation and one owner.
- Research records remain distinct from third-party incorporation records.
- Vendor, Fork, Submodule, and resource snapshots require path-level provenance.
- The root license remains `PENDING_GOVERNANCE_DECISION`; it does not override third-party licenses.

## Change record

| Version | Date | Status | Change |
| --- | --- | --- | --- |
| 1.0.0 | 2026-07-31 | Accepted / Conditional Approval documentation | Recorded the original decision and its RECA authority boundaries |
| 1.0.1 | 2026-07-31 | Accepted / APPROVED FOR M1 DEVELOPMENT documentation | Synchronized the documentation approval state; decision content and integration facts are unchanged |

## References

- [Open-Source Integration Master Plan](../source-research/OPEN_SOURCE_INTEGRATION_MASTER_PLAN.md)
- [ADR-008 implementation metadata](./ADR-008-IMPLEMENTATION-METADATA.md)
- [Third-Party Notices](../../THIRD_PARTY_NOTICES.md)
