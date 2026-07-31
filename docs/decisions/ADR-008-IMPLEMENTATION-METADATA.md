<a id="adr-008-implementation-metadata"></a>

# ADR-008: Require implementation and provenance metadata for upstream adoption

ADR ID: `ADR-008-IMPLEMENTATION-METADATA`

## Status

Accepted on 2026-07-31

Documentation status: `Conditional Approval`

## Context

Research Commits capture evaluation evidence, but they are not automatically the versions installed in RECA. Package, image, service, Vendor, Fork, Submodule, and resource adoption need a consistent record that separates research intent from repository fact.

## Decision

Every actual adoption records, as applicable:

```text
project
repository
research_commit
upstream_commit_or_tag
license
license_file
integration_mode
status
copied_paths
modified_paths
modification_summary
attribution_location
special_restrictions
commercialization_review
source_of_truth
fallback
acceptance_tests
reviewed_by
reviewed_at
```

Source-research lifecycle status must be exactly one of:

```text
RESEARCHED
RECOMMENDED
EXPERIMENT_REQUIRED
PLANNED
ALREADY_INTEGRATED
REJECTED
```

`ALREADY_INTEGRATED` requires repository evidence such as a manifest/lock entry, Compose image/service, Submodule, Vendor/resource path, or retained imported source. It does not imply that all planned business capability is complete. Research-only or planned projects must not receive incorporation notices that imply use.

`THIRD_PARTY_NOTICES.md` is the human-readable adoption and research registry. License snapshots under `vendor/licenses/` are added only when the repository actually contains content whose license must accompany it. A research record or planned dependency alone does not justify copying a license file.

## Alternatives considered

- Use only package manifests: rejected because they do not cover copied resources, services, upstream Commits, modifications, or special restrictions.
- Copy every researched license in advance: rejected because it falsely suggests incorporation and creates stale snapshots.
- Treat the research Commit as the install pin: rejected because runtime compatibility may require a released version or image digest.

## Consequences

- Adoption PRs can be audited without inferring facts from prose.
- License and attribution records remain proportional to actual repository content.
- The root license remains `PENDING_GOVERNANCE_DECISION` and cannot cover special-license files by implication.

## References

- [Master plan](../source-research/OPEN_SOURCE_INTEGRATION_MASTER_PLAN.md)
- [ADR-002 integration modes](./ADR-002-OPEN-SOURCE-INTEGRATION-MODES.md)
- [Third-Party Notices](../../THIRD_PARTY_NOTICES.md)
