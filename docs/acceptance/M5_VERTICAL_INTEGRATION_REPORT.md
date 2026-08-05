# M5 Vertical Integration Report

Date: 2026-08-05
Scope: M5 production Workspace and deterministic Analysis/Figure vertical

```text
PRODUCTION_ROUTE_WIRED=YES
REAL_VERTICAL_COMPLETED=YES
OPEN_DESIGN_READY_FOR_CODEX_INTEGRATION=YES
STAGE_RESULT=PASS
NEXT_STAGE_EXECUTED=NO
```

## Entry And Design Evidence

- Formal branch/HEAD: `feat/m2-research-literature` / `25a4fe6ea7acac6e95af25563bca5a2c0a6b1acd`.
- Migration head: sole `0016_m5_figures`; `0015_m5_analysis` was not rewritten.
- The isolated Open Design worktree was resynchronized with 53 formal fixtures and current protected
  contracts. Its acceptance runner passed 318 combinations with zero failures, warnings or console
  errors, produced 18 screenshots and published `READY_FOR_CODEX_INTEGRATION=YES`.
- The five accepted UI/CSS files were mechanically synchronized into the formal feature without
  moving API, mapper, query, mutation, Container or Route ownership into UI code.

## Production Integration

- One production route is wired at `/projects/$projectId/analysis`.
- All frozen deep-link keys are parsed through `route-contract.ts`; invalid UUIDs safely fall back and
  same-project relationships are revalidated by the query layer without object disclosure.
- `AnalysisWorkspaceContainer` loads only generated-client/adapter facts and rechecks event capability
  before mutations. Successful mutations update URL selection from server responses; Artifact download
  uses the returned server URL.
- Production source contains no fixture or Preview import and `integrationPending` is empty.

## Real Backend Vertical

The isolated PostgreSQL suite executes the formal Dataset upload/confirmation input through Analysis
and Figure services and Worker handlers. It verifies approval freshness, SHA-256 input checks,
idempotent replay, deterministic Result/Artifact creation, Figure confirmation and downloads,
no-disclosure, invalidation and failure compensation.

Stage 5 additionally verifies hard Worker loss: common stale recovery atomically moves Job,
ProcessingRun and the AnalysisRun or FigureRenderRun to `FAILED` with `JOB_TIMEOUT`. No Result, Figure
or Code Artifact is created for the lost attempt, and terminal completed facts are not downgraded.

## Browser Evidence

- Focused production Route: 5/5 passed across desktop 1440, tablet 820 and mobile 390 viewports.
- Covered deep-link restore and refresh, invalid parameter fallback, project 404 fail-closed behavior,
  Light/Dark surfaces, keyboard focus and zero root horizontal overflow.
- Complete shell Playwright: 159 passed, 1 opt-in live-service case skipped.
- UI boundary, production mock, M3/M4/M5 fixture and generated-client guards all pass.

## Outcome

The previous Stage 4 blockers `M5-ISSUE-0012`, `0013`, `0015` and `0016` are resolved. HTTP 202,
preview events and fixture state were not used as business-completion evidence.
