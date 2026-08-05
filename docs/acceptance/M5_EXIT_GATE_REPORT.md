# M5 Exit Gate Report

Date: 2026-08-05
Owner: Codex
Migration head: `0016_m5_figures`

## Decision

```text
M5_EXIT=PASS
M5_COMPLETION=APPROVED
M6_ENTRY=ALLOWED
NEXT_STAGE_EXECUTED=NO
```

No unresolved BLOCKER, CRITICAL, HIGH, MEDIUM or LOW M5 issue remains. Stage 5 closed Worker-loss
reconciliation, the real Figure PostgreSQL vertical, Open Design acceptance, generated formatting and
local dependency layout gaps. The only retained supply-chain item is the accepted LOW Babel advisory.

## Gate Evidence

| Gate | Result |
| --- | --- |
| Ruff format/check | PASS, 205 Python files |
| Mypy | PASS, 120 source files |
| Complete `no_database` | PASS, 165 passed, 2 skipped |
| Real PostgreSQL backend | PASS, 380 passed, 2 skipped |
| M5 statistical/renderer golden | PASS within complete backend suites |
| Empty DB upgrade + repeat | PASS through `0015` and additive `0016` |
| `alembic check` + unique head | PASS; sole `0016_m5_figures` |
| Worker/MinIO/restart/persistence | PASS in isolated clean-room |
| Frontend format/lint/build | PASS; Analysis route bundle 89.38 kB |
| Generated/boundary/mock/fixture guards | PASS; 4 generated files, 4/4 boundary, 6/6 mock, M5 4/4 |
| Focused M5 production browser | PASS, 5/5 desktop/tablet/390 |
| Complete shell Playwright | PASS, 159 passed, 1 skipped |
| Isolated Open Design | PASS, 53 fixtures, 318 combinations, 18 screenshots |
| Isolated clean-room | PASS, 39 steps, no FAIL |
| Secret scans / Python audit | PASS |
| Bun audit | PASS_WITH_LOW_ADVISORY, one LOW only |
| License/Notices/font attribution | PASS |
| `git diff --check` | PASS; line-ending warnings only |

Clean-room evidence was stored in a temporary external evidence directory during execution and is not
part of the Git deliverable. The report records all durable counts and decisions needed for review.

## Exit Assertions

1. Only AVAILABLE DatasetVersion/Artifact inputs with matching hashes and CONFIRMED columns can enter
   deterministic analysis or rendering.
2. AnalysisPlan approval payload/hash freshness, project scope, method registry and immutable input
   identity are revalidated before each Run and again after Worker claim.
3. Six P0 methods match independent golden values and normalize missingness, effective N, constants,
   small samples, ties, pairing, variance, warnings and regression diagnostics.
4. AnalysisResult is immutable and formal numbers come only from StatisticalEngine; no textual Summary,
   user code, formula, SQL, shell or AI-generated number enters the result contract.
5. Job, ProcessingRun and domain Run states reconcile on completion, cancellation, ordinary failure and
   stale Worker recovery. Replay/retry/failure creates no duplicate or half-complete formal output.
6. Five Figure templates use fixed headless Matplotlib configuration and whitelist parameters. PNG,
   SVG, PDF and Code Artifacts finalize atomically and retain environment/font/template hashes.
7. Figure DatasetVersion/Run/Result/caption and displayed numeric facts remain consistent; validation
   issues and stale upstream facts block confirmation or invalidate the Figure without deleting history.
8. OpenAPI/generated/adapter, no-disclosure, allowed actions, deep links and production Workspace are
   integrated without fixture or Preview truth.
9. M0-M4 clean-room, backend and shell browser capabilities remain green.

Ignored local caches, Playwright reports and the pre-existing `output/` tree were audited as generated
or user-owned evidence paths; no database, MinIO volume, uploaded Dataset or Secret was added to Git.
