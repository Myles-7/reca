# M5 Open Design Handoff

Date: 2026-08-05
Owner: Codex

```text
READY_FOR_OPEN_DESIGN=YES
```

The Analysis and Figure contracts are executable and frozen for Open Design. `M5-ISSUE-0006` and
`M5-ISSUE-0008` are resolved by additive migration `0016_m5_figures`, formal Figure DTO/API/Worker
transport, generated client operations, stable ViewModels and typed fixtures.

## Workspace Information Architecture

Use one project-scoped Workspace and no second Figure shell:

```text
/projects/$projectId/analysis
  Plan
  Assumptions
  Runs
  Results
  Figures
```

The route began as the frozen Stage 3 contract and is now the single production route. Deep-link keys are `dataset`,
`version`, `analysisPlan`, `analysisRun`, `analysisResult`, `approval`, `job`, `figurePlan`, `figure`,
`renderRun` and `view`. Only UUIDs and known views parse. Project membership and object relationships
are revalidated by queries; mismatch returns no-disclosure `RESOURCE_NOT_FOUND`.

## Ownership

Open Design may modify only:

```text
frontend/src/features/analysis-workspace/ui/**
```

Codex-protected paths:

```text
backend/**
frontend/openapi.json
frontend/src/api/generated/**
frontend/src/api/adapter/**
frontend/src/features/analysis-workspace/model.ts
frontend/src/features/analysis-workspace/mappers.ts
frontend/src/features/analysis-workspace/queries.ts
frontend/src/features/analysis-workspace/mutations.ts
frontend/src/features/analysis-workspace/containers/**
frontend/src/features/analysis-workspace/route-contract.ts
frontend/src/features/analysis-workspace/fixtures/**
frontend/src/routes/**
```

Breaking Props/Event/ViewModel requests require Codex review and matching mapper/fixture tests.

## Executable Contracts

- ViewModel: `frontend/src/features/analysis-workspace/model.ts`
- Props/Event: `frontend/src/features/analysis-workspace/ui/contracts.ts`
- Typed fixtures: `frontend/src/features/analysis-workspace/fixtures/index.ts`
- Route/deep links: `frontend/src/features/analysis-workspace/route-contract.ts`

Props expose a `Loadable<AnalysisWorkspaceViewModel>`, pending action, normalized mutation error,
retry command, user-intent Event callback and optional route view callback. Events cover AnalysisPlan
create/update/validate/approval/run, Run invalidate, Job retry/cancel, Figure planning/rendering/
confirmation/download, suggestion and interpretation intent.

An Event is never evidence of success. Preview handlers may record the Event and payload only. They
must not alter Props to approved, completed, confirmed or downloadable. Production state changes only
after server response and invalidation/refetch.

## State Matrix

Typed fixtures cover loading, empty, ready, error, forbidden, read-only, permissions unknown,
degraded, unknown/future status, unconfirmed columns, quality warnings, sensitive acknowledgement,
Plan lifecycle, assumption outcomes, queued/running/completed/failed/invalidated Analysis, P0-Must
structured results, P0-Full group comparison/regression, long decimals/N/labels, and
desktop/tablet/mobile light/dark representatives. Figure fixtures use formal FigurePlan,
FigureRenderRun, Figure, validation issue and PNG/SVG/PDF/Code Artifact projections with
`transportAvailable=true`; failed rendering is represented on FigureRenderRun, not invented as a
Figure status.

## Business Facts

UI may keep only local presentation state such as selected tab, panel expansion, focus, sorting,
display rounding, draft form values and dismissed non-business hints.

UI must not derive or locally change:

- permissions, allowed actions, retryability or object existence;
- Plan/Run/Figure/Approval/Job status;
- approval freshness, payload/hash equality or version consistency;
- assumption outcome, effective N, p value, CI, effect, coefficient or significance;
- Figure validation, confirmation, Artifact availability or download authority;
- deterministic result, AI suggestion and AI interpretation equivalence.

`permissionsKnown=false`, `knownStatus=false`, absent allowed action, stale Approval and hash/version
mismatch all disable the associated control with the supplied reason.
Sensitive columns render masked values; fixtures contain no real user or research data.

## Interaction Baseline

- Desktop, tablet and mobile layouts must keep the same single Workspace semantics.
- Light and dark themes use existing tokens from `frontend/DESIGN.md` and `frontend/src/index.css`.
- All actions require keyboard access, visible focus and stable disabled reasons.
- Reduced motion disables nonessential transitions; progress must remain understandable without motion.
- Unknown and forbidden states must not reveal whether a referenced object exists.
- Long IDs, hashes, column labels, warnings and captions wrap or truncate with an accessible full-value
  affordance; sensitive values never use such an affordance.

## Production Integration Completed

- Open Design implemented only `ui/**`; its resynchronized acceptance passed 318 combinations and
  published `READY_FOR_CODEX_INTEGRATION=YES`.
- Codex synchronized the accepted UI, wired the protected Route/Container, and retained generated
  client, adapter, query, mutation and business safety ownership.
- Focused production browser, PostgreSQL Figure vertical, hard Worker-loss recovery and the complete
  Stage 5 Exit Gate pass. Preview still records Events only and never simulates server success.

```text
READY_FOR_OPEN_DESIGN=YES
READY_FOR_CODEX_INTEGRATION=YES
PRODUCTION_INTEGRATION=PASS
NEXT_STAGE_EXECUTED=NO
```
