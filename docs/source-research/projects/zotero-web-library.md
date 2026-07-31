# Zotero Web Library source research

Document version: `1.0.0`

Document status: `Conditional Approval`

Research status: `RECOMMENDED`

Last researched: 2026-07-31

Phase summary: [Manuscript, citation and frontend research](../../archive/open-source-research/OPEN_SOURCE_RESEARCH_PHASE_4_MANUSCRIPT_FRONTEND.md)

## Upstream

| Field | Verified value |
| --- | --- |
| Repository | <https://github.com/zotero/web-library> |
| Default branch | `master` |
| Pinned research commit | `556d0bf6b1b48fa8402a91afa62b15533b713013` |
| Research commit date | 2026-07-28 |
| Latest release/tag | `v1.8.1` |
| License | AGPL-3.0 |
| License file | `COPYING` |
| Main language | JavaScript/React/SCSS |
| Runtime stack | React 19, Redux Toolkit/Redux, Zotero API client, virtualized lists and reader/note modules |
| Test framework | Jest, Testing Library and Playwright |
| Maintenance status | Active; repository was not archived at the research commit |

## Repository structure

| Path | Purpose |
| --- | --- |
| `src/js/component/` | library, item, detail, tag, reader, search and responsive components |
| `src/js/actions/` | API, navigation, item, collection, tag and export actions |
| `src/js/reducers/` | current view and normalized library state |
| `src/js/hooks/`, `src/js/common/` | shared behavior and utilities |
| `src/scss/` | responsive visual system |
| `test/` | component, API fixture and Playwright state tests |

## UX architecture

The Web Library is a single-page application backed by Zotero API calls. It
combines library/collection navigation, a virtualized item list, item detail and
editing panes, tag filtering, search, attachments, notes, reader views and
responsive/touch layouts. State is normalized across Redux reducers/actions and
supports loading, updating and deletion queues.

## Useful UX patterns

- persistent collection/library navigation with clear current scope;
- dense sortable/filterable item list with virtual scrolling;
- detail pane that changes with item, attachment or note type;
- progressive disclosure of attachments, notes, tags and related items;
- desktop multi-pane layout and touch drill-down layout;
- visible read-only/editing state, ongoing operation feedback and error recovery;
- search/tag filters that retain user context.

RECA can independently implement these interaction patterns for its literature
matrix, screening and evidence workbench without copying source, SCSS, icons or
Zotero branding.

## State-management lessons

The repository shows the cost of synchronizing collections, items, tags,
attachments, routes, uploads and optimistic changes. RECA should keep server
state in its chosen query/cache layer and local UI state close to components,
rather than copying Zotero's Redux architecture wholesale. Backend APIs remain
the source of allowed actions and project state.

## Responsive behavior

Desktop can use collection tree, item list and detail pane together. Narrow
screens should use drill-down navigation with a clear back path and preserved
selection/filter context. Dense tables need a deliberate mobile summary view;
shrinking all columns is not a usable responsive strategy.

## Tests

Upstream has Jest/Testing Library coverage for collections, items, tags,
attachments, details, notes, related items, exports and read-only modes, plus
Playwright snapshots/states for desktop and mobile. RECA may reuse scenario ideas,
but copying AGPL fixtures, component code or screenshots requires review.

## RECA current state

The Web Library is not installed, Vendored or copied. RECA's frontend is its own
React/Vite application with generated API clients and domain-specific workflows.

## Recommended integration mode

`DESIGN_REFERENCE`

Do not copy the Web Library source. Independently implement selected information
architecture and interaction patterns using RECA components, TanStack Table and
existing state/API conventions.

## What to reuse

- high-level collection/list/detail workbench organization;
- responsive drill-down and selection-preservation ideas;
- virtual list, loading, read-only and error-state test scenarios;
- progressive attachment/note/tag disclosure patterns.

## What not to reuse

- AGPL React components, reducers, SCSS, icons or fixtures;
- Zotero API state as RECA project state;
- Zotero branding or visual identity;
- the whole Redux architecture without a measured need;
- source copied under the assumption that UI patterns remove AGPL obligations.

## Domain boundary

UX inspiration does not change data ownership. RECA LiteratureRecord,
LiteratureDecision, Artifact, EvidenceSpan, project permissions and approval
remain backend/domain facts. Frontend panes only present and request actions.

## Milestone

- M2/M3: literature matrix, screening and item/PDF detail workbench.
- Later milestones may reuse the same list/detail shell for issues and approvals.

## Risks

- accidental source/SCSS copying from an AGPL application;
- recreating Zotero instead of focusing on RECA's evidence workflow;
- client state diverging from backend allowed actions;
- virtualized lists harming keyboard/screen-reader use;
- mobile navigation losing selection and filter context.

## Validation spike

Prototype an independently implemented desktop three-pane and mobile drill-down
literature workbench using synthetic data. Test collection/filter persistence,
virtual list navigation, item/PDF detail switching, read-only permissions and
error recovery. Do not import upstream source or assets.

## Attribution requirements

Design research should cite the repository in this source record. Any actual
copy requires AGPL-3.0 source availability, copyright/notice retention and
third-party/trademark review. This phase copied nothing.

## Update strategy

Treat the repository as a periodic UX reference, not a package to track. Revisit
only when a concrete workbench problem needs comparison.
