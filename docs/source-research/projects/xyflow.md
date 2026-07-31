# xyflow / React Flow source research

Document version: `1.0.0`

Document status: `Conditional Approval`

Research status: `PLANNED`

Last researched: 2026-07-31

Phase summary: [Manuscript, citation and frontend research](../../archive/open-source-research/OPEN_SOURCE_RESEARCH_PHASE_4_MANUSCRIPT_FRONTEND.md)

## Upstream

| Field | Verified value |
| --- | --- |
| Repository | <https://github.com/xyflow/xyflow> |
| Default branch | `main` |
| Pinned research commit | `360f5b13e2bc6899ea06b4be1a49b068d86926cf` |
| Research commit date | 2026-07-29 |
| Latest React package | `@xyflow/react` `12.11.2` |
| License | MIT |
| License file | `LICENSE` |
| Main language | TypeScript |
| React peer range | React/React DOM `>=17` at the research commit |
| Test framework | Playwright E2E, package type/lint/build checks |
| Maintenance status | Active; repository was not archived at the research commit |

## Repository structure

| Path | Purpose |
| --- | --- |
| `packages/react/` | React Flow component, store, hooks, nodes and edges |
| `packages/system/` | framework-independent geometry, drag, zoom and graph types |
| `examples/` | React/Svelte examples and interaction patterns |
| `tests/playwright/` | node, edge, pane, toolbar and prop E2E tests |
| `packages/react/src/types/` | Node, Edge, instance and serialization types |

## Core capabilities

React Flow renders typed Nodes and Edges, handles pan/zoom/selection, supports
custom node/edge components, handles/ports, minimap/controls/panels and emits
controlled node/edge changes. `toObject()` can serialize nodes, edges and
viewport for UI restoration.

## Layout

React Flow positions and interacts with nodes but is not a complete automatic
graph-layout authority. Hierarchical or force layout normally requires a
separate algorithm such as Dagre or ELK, or RECA-computed coordinates. Layout
coordinates are presentation state and must not be confused with evidence
relationships.

## Large graphs

Large evidence graphs need server-side subgraph queries, clustering/filtering,
progressive expansion and careful custom-node rendering. Viewport culling and
memoized node/edge components help, but sending an entire project graph to the
browser is not a scalable access-control or performance strategy.

## Interaction and serialization

Node selection, viewport, expansion, position and temporary edge edits are UI
state. Serialization can restore a view, but RECA should persist only a versioned
view configuration if the product needs it. A React Flow JSON object is not an
EvidenceGraphSnapshot or domain contract.

## Evidence graph boundary

```text
backend evidence graph = authority
React Flow = visualization
```

Backend Services create and validate ClaimEvidenceLink, project scope,
invalidation and graph queries. React Flow receives an authorized projection and
emits navigation/filter/selection intents. It cannot create evidence truth by
drawing an edge.

## Tests

Upstream Playwright tests cover nodes, edges, pane behavior, props and toolbar
interactions. RECA needs graph projection tests, click-through to source objects,
stale/invalidation visuals, denied nodes, large-graph limits, keyboard navigation,
mobile read-only fallback and proof that drag/connect actions cannot persist a
ClaimEvidenceLink without the normal Service path.

## RECA current state

React Flow is planned for M7 evidence-chain visualization. It is not installed
or implemented by this research phase.

## Recommended integration mode

`DIRECT_DEPENDENCY` on `@xyflow/react`.

Use RECA-owned custom nodes, edges and a projection mapper. An Adapter is not
needed for the component library; the backend graph API is the real authority
boundary.

## What to reuse

- React component and controlled Node/Edge model;
- custom nodes/edges, viewport controls and selection;
- geometry/interaction utilities and Playwright test ideas;
- UI serialization for optional view restoration.

## What not to reuse

- React Flow JSON as backend graph truth;
- client-created edges as persisted ClaimEvidenceLink;
- full-graph loading without project-scoped query limits;
- positions as scientific semantics;
- an automatic layout dependency before graph size/shape is measured.

## Domain boundary

```text
project-scoped backend graph query
-> RECA graph projection DTO
-> React Flow nodes/edges
-> navigation, selection and view-state events
```

All relationship writes, confirmations and invalidations return through existing
APIs and Services.

## Milestone

- M7: evidence graph visualization and export/readiness inspection.
- M8: Agent may navigate the same backend graph through tools; the UI library
  does not change Agent timing or authority.

## Risks

- client edges being mistaken for formal evidence;
- large graphs overwhelming browser/layout;
- inaccessible custom nodes and edge-only semantics;
- stale graph projections hiding invalidated evidence;
- view serialization leaking data outside project scope.

## Validation spike

Render a synthetic 500-node project-scoped graph with progressive expansion,
custom claim/evidence nodes and stale-edge styles. Test source navigation,
keyboard access, mobile fallback, denied-node omission and rejection of direct
client edge persistence.

## Attribution requirements

Preserve the MIT notice for redistributed code. Record the exact package version.
Copied examples or customizations derived from upstream require path/Commit and
modification records.

## Update strategy

Pin a released package and keep projection DTOs RECA-owned. Upgrade only after
graph interaction, accessibility, performance and authority-boundary tests pass.
