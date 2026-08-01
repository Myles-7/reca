<a id="adr-006-research-workbench-ux"></a>

# ADR-006: Build the research workbench from headless components and authoritative APIs

ADR ID: `ADR-006-RESEARCH-WORKBENCH-UX`

## Status

Accepted on 2026-07-31

Documentation status: `APPROVED FOR M1 DEVELOPMENT`

Decision version: `1.0.1`

Current amendment: 2026-07-31

## Context

RECA needs dense literature, quality, analysis, manuscript, approval, PDF, and evidence-graph workflows. Mature frontend components can accelerate delivery, but client selection and graph state cannot become scientific or authorization truth.

## Decision

- TanStack Table remains the direct dependency for dense tabular workbenches; its current package presence is an integrated foundation, not proof that every workbench exists.
- PDF.js is planned for authorized PDF display and evidence interaction.
- React Flow is planned for evidence-graph visualization and navigation.
- Zotero and Zotero Web Library remain UX/data-exchange design references. Their AGPL source and assets are not copied by this decision.
- Backend APIs and durable RECA objects remain authoritative for filtering, decisions, approvals, evidence edges, versions, and access control.

Frontend libraries consume generated RECA API clients and view models. Third-party DTOs must not leak into public contracts. Table selection is not approval or literature decision; React Flow nodes and edges are projections, not graph authority; PDF viewer coordinates require backend/version validation.

## Alternatives considered

- Fork Zotero or its Web Library: rejected for the current scope because of architecture mismatch and AGPL/source-copy obligations.
- Hand-build all table and graph mechanics: rejected because mature headless components reduce delivery risk.
- Store workflow state only in the browser: rejected because it breaks project authority and auditability.

## Consequences

- Accessibility, large-data behavior, stale-state handling, and authorization tests are required.
- UX references must be independently implemented unless a later license review approves source reuse.
- Existing APIs, Schemas, Requirements, and Acceptance IDs remain unchanged.

## Change record

| Version | Date | Status | Change |
| --- | --- | --- | --- |
| 1.0.0 | 2026-07-31 | Accepted / Conditional Approval documentation | Recorded the original decision and its RECA authority boundaries |
| 1.0.1 | 2026-07-31 | Accepted / APPROVED FOR M1 DEVELOPMENT documentation | Synchronized the documentation approval state; decision content and integration facts are unchanged |

## References

- [Master plan](../source-research/OPEN_SOURCE_INTEGRATION_MASTER_PLAN.md)
- [TanStack Table research](../source-research/projects/tanstack-table.md)
- [React Flow research](../source-research/projects/xyflow.md)
- [Zotero research](../source-research/projects/zotero.md)
- [Zotero Web Library research](../source-research/projects/zotero-web-library.md)
