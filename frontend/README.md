# RECA Frontend

The frontend is a React, Vite and strict TypeScript research workbench. Bun is
the repository's package manager and script runner.

## Commands

Run from the repository root:

```bash
bun install --frozen-lockfile
bun run --cwd frontend dev
bun run --cwd frontend format:check
bun run --cwd frontend lint
bun run --cwd frontend build
bun run --cwd frontend generate-client
bun run --cwd frontend check-generated-client
bun run --cwd frontend test:shell
```

## Current and planned boundaries

- `src/api/generated/` is generated from OpenAPI and is never hand-edited.
- `src/api/adapter/` maps generated DTOs and errors into stable frontend-facing forms.
- `src/features/` owns workflow UI but never becomes the source of business state.
- `src/shared/` contains narrowly reusable primitives without domain workflow ownership.

`src/app/` is the planned boundary for routing, global providers and application
shell composition. `src/vendor-integrations/` is the planned boundary for thin,
approved third-party UI wrappers and attribution notes. Neither directory should
exist only as a placeholder; create it when a milestone adds real implementation.
Feature-owned PDF, table, graph and citation integrations must keep upstream
types behind RECA view models and record package version, license, fallback and
acceptance evidence. Copied source or assets require separate Vendor provenance.

TanStack Table provides headless tables, PDF.js is planned for authorized PDF
display and evidence navigation, and React Flow is planned for evidence-graph
visualization. Table selection is not approval, PDF.js coordinates are not
EvidenceSpan truth, and React Flow edges are not ClaimEvidenceLink authority.

Zotero and Zotero Web Library are UX and exchange-format references only. Do not
copy their AGPL source or assets without a separate reviewed decision.

Read [the architecture](../docs/ARCHITECTURE.md),
[workbench ADR](../docs/decisions/ADR-006-RESEARCH-WORKBENCH-UX.md) and the
relevant [source record](../docs/source-research/) before adding or upgrading a
third-party frontend capability.

## Module guides

- [API integration](./src/api/README.md)
- [Feature ownership](./src/features/README.md)
- [Shared primitives](./src/shared/README.md)

Application-composition and Vendor-integration directories are created only
when their milestones add tracked implementation, not as README-only placeholders.
