# TanStack Table source research

Document version: `1.0.0`

Document status: `Conditional Approval`

Research status: `ALREADY_INTEGRATED`

Last researched: 2026-07-31

Phase summary: [Manuscript, citation and frontend research](../../reports/OPEN_SOURCE_RESEARCH_PHASE_4_MANUSCRIPT_FRONTEND.md)

## Upstream

| Field | Verified value |
| --- | --- |
| Repository | <https://github.com/TanStack/table> |
| Default branch | `beta` |
| Pinned research commit | `d66b39f01e23eeb4e2befc7777194104967212d3` |
| Research commit date | 2026-07-30 |
| Research-head package | `@tanstack/react-table` `9.0.0-beta.65` |
| Latest stable npm release | `@tanstack/react-table` `8.21.3` |
| License | MIT |
| License file | `LICENSE` |
| Main language | TypeScript |
| Stable peer/runtime | React adapter supports React; npm stable metadata declares Node `>12` for tooling/package |
| Test framework | Vitest workspace, Playwright examples/E2E and TypeScript checks |
| Maintenance status | Active; repository was not archived at the research commit |

The default branch is a v9 beta. RECA's formal architecture names TanStack Table
v8, so implementation should pin the stable v8 line and must not adopt research
HEAD simply because it is newer.

## Repository structure

| Path | Purpose |
| --- | --- |
| `packages/table-core/` | headless table state and row-model logic |
| `packages/react-table/` | React adapter/hooks |
| `examples/react/` | sorting, filtering, selection, editing, pagination and virtualization patterns |
| `tests/e2e/` | example-server/browser harness |
| `docs/` | APIs and guides |

## Core capabilities

TanStack Table is headless: it computes columns, headers, cells, rows and state
but does not prescribe markup or visual design. Stable v8 supports controlled
sorting, global/column filtering, faceting, row selection, pagination, grouping,
expansion, column visibility/order/pinning/sizing and server-side modes.

## Virtualization and editable cells

Virtualization is normally composed with TanStack Virtual rather than owned by
Table itself. Upstream examples cover virtualized rows/columns and infinite
scrolling. Editable cells are an application pattern: the cell UI and mutation
semantics remain user code. RECA must not let an editable cell bypass API,
permissions, optimistic locking or approval.

## RECA workbench mapping

| RECA surface | Useful table behavior |
| --- | --- |
| literature matrix | dense columns, visibility, sorting, filters, selection, virtual rows |
| literature screening | keyboard/row selection, status filters, server pagination |
| data-quality issues | severity/rule filters, faceting, affected-count sorting |
| analysis results | typed columns, grouping and stable display formatting |
| ManuscriptIssue | section/severity/status filters and bulk low-risk selection |
| approval queue | server-owned actions, due/status filters and selection without implicit approval |

## State and server authority

Table sorting/filter/selection/page state is UI state. Dataset, LiteratureRecord,
issue, approval and allowed actions come from backend APIs. Large lists should
use server-side pagination/filter/sort where contract support exists; client
virtualization improves rendering but does not reduce payload size.

## Tests

Upstream examples cover a broad feature matrix. RECA needs focused component and
E2E tests for stable row IDs, selection across pagination, filter reset,
virtualized keyboard access, empty/error/loading states, optimistic mutation
failure and permission-driven action visibility.

## RECA current state

TanStack Table v8 is planned for dense research workbenches. It is not added or
modified by this research phase.

## Recommended integration mode

`DIRECT_DEPENDENCY` on stable `@tanstack/react-table` v8.

Use RECA-owned table components for accessibility, density, error/loading state,
column persistence and API mapping. No Adapter is needed; table row objects must
still be frontend view models rather than domain authority.

## What to reuse

- headless core and React adapter;
- controlled sort/filter/selection/pagination state;
- stable row-ID and server-side operation patterns;
- virtualized-table and editable-cell example ideas;
- upstream type and interaction testing patterns.

## What not to reuse

- v9 beta in Competition Edition without a separate migration decision;
- example mutation logic as production approval behavior;
- client-only filtering for large authoritative datasets;
- row selection as ApprovalRecord or LiteratureDecision;
- a generic “spreadsheet” that permits arbitrary data mutation.

## Domain boundary

TanStack Table renders RECA API/view-model data and emits UI intents. Services
remain responsible for project isolation, version checks, confirmation,
ApprovalRecord and durable state changes.

## Milestone

- M2/M3: literature matrix and screening.
- M4/M5: quality issues and analysis results.
- M6/M7: manuscript issues and approval/export workbenches.

## Risks

- accidentally adopting beta APIs;
- unstable row IDs corrupting selection after pagination/filtering;
- virtualized content reducing accessibility;
- optimistic edits appearing saved after API failure;
- very wide matrices becoming unusable without column presets.

## Validation spike

Build one disposable literature matrix with 10,000 synthetic rows, server-style
pagination, filters, stable selection and virtual rendering. Test keyboard use,
screen-reader labels, mutation failure, permission changes and mobile fallback
against the exact React/Bun/Vite stack.

## Attribution requirements

Preserve the MIT notice for redistributed code. Record the exact stable package
version. Example code copied or materially adapted requires source path, Commit
and modification records.

## Update strategy

Remain on the v8 stable line until a deliberate v9 migration. Replay shared table
component and workbench E2E tests before upgrades.
