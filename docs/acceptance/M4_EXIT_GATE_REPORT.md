# M4 Exit Gate Report

Date: 2026-08-04
Owner: Codex
Migration head: `0014_m4_data_quality`

## Decision

```text
M4_EXIT=PASS
M4_COMPLETION=APPROVED
M5_ENTRY=ALLOWED
NEXT_STAGE_EXECUTED=NO
```

No BLOCKER, CRITICAL or unresolved HIGH issue remains. M4-ISSUE-0004, 0014 and 0015 were closed
with implementation and regression evidence. Deferred LOW issues are listed in the completion
report and do not relax M4 invariants.

## Concentrated Repairs

- Added explicit OpenAPI-visible response DTOs for all M4 Dataset, Quality and Cleaning success
  responses, with correct 200/201/202 status contracts.
- Added formal project-scoped Dataset version-history and DataTransformation detail reads.
- Regenerated `frontend/openapi.json` and the Hey API client; generated operation responses are no
  longer operation-level `unknown`.
- Connected version history and Transformation reads through adapter, query and mapper boundaries;
  added same-project, Dataset, Version, Plan and Job relationship checks.
- Removed production `integrationPending` messages and retained fail-closed future-enum behavior.
- Added API/OpenAPI, no-disclosure, lineage and production-route regression coverage.
- Removed direct `JSONResponse` returns from eleven M4 command handlers so declared response models
  now validate and serialize runtime success payloads, not only OpenAPI schemas.
- Added the persisted nullable `DataTransformation.log_artifact_id` to the formal read projection,
  generated client and M5 provenance handoff without inventing a log Artifact when none exists.
- Applied the repository Ruff formatter to the M4/shared Python baseline and fixed the stale M4
  fixture guard that still expected Stage 5 integration to be incomplete.

## Gate Evidence

| Gate | Result |
| --- | --- |
| Ruff format/check | PASS, 184 Python files formatted and clean |
| mypy | PASS, 108 source files |
| complete `no_database` | PASS, 134 passed, 2 skipped |
| real PostgreSQL backend | PASS, 347 passed, 2 skipped |
| M4 API/OpenAPI/vertical focused set | PASS, 13 passed |
| empty DB upgrade + repeat | PASS |
| `alembic check` | PASS, no new operations |
| unique migration head | PASS, `0014_m4_data_quality` |
| frontend format/lint | PASS, 245/248 files |
| generated client consistency | PASS, 4 generated files |
| fixture/boundary/mock guards | PASS, M3 5/5, M4 8/8, boundary 4/4, mocks 6/6 |
| production frontend build | PASS, 2331 modules |
| complete shell Playwright | PASS, 148 passed, 1 skipped |
| M4 fixture acceptance | PASS, desktop/tablet/390, Light/Dark |
| isolated clean-room | PASS, 39 recorded steps |
| real MinIO/Worker/restart/persistence | PASS in clean-room |
| repository/container Secret scans | PASS |
| Python dependency audit | PASS |
| Bun dependency audit | PASS_WITH_LOW_ADVISORY, one LOW only |
| license/Notices policy | PASS |
| `git diff --check` | PASS; line-ending warnings only |

Clean-room evidence is stored outside the repository at:

```text
D:/桌面/Recas/output/m4-stage6-cleanroom-review-final
```

The two backend skips are opt-in live-service cases; the dedicated M4 real PostgreSQL vertical test,
Worker execution and clean-room MinIO path passed. The one Playwright skip is the opt-in real M3
vertical chain; all M0-M4 shell regression tests executed and passed.

## Exit Assertions

1. CSV and XLSX uploads preserve immutable original Artifact bytes and SHA-256 identity; multi-sheet
   selection is persisted, bounded and explicit for hidden sheets.
2. Dataset, Version, Column, Quality, Plan, Approval and Transformation state transitions are
   enforced by service authorization, row locks, constraints and allowed actions.
3. Quality rule identity and implementation metadata are versioned and reproducible; golden tests
   cover missingness, duplication, type/category/range/extreme/unit/date and sensitive candidates.
4. Cleaning actions use a strict deterministic whitelist. Code, SQL, shell, URL and arbitrary
   expression fields are rejected. Preview and AI suggestion have no execution authority.
5. Approval freshness, project scope, source Version availability and all hashes are revalidated
   before execution.
6. Success creates exactly one derived Artifact and AVAILABLE DatasetVersion with parent lineage;
   failure, dispatch failure, cancellation, retry and concurrent replay do not create an AVAILABLE
   half-product or duplicate formal Version.
7. CSV formula values are escaped on export, XLSX parsing disables links/formulas, and damaged or
   over-limit inputs fail with explicit errors.
8. Sensitive preview values remain masked and model invocation metadata records that sensitive
   values were not sent.
9. Production Data Workspace completes upload through version comparison with refresh/deep-link,
   mobile, Light/Dark, keyboard and focus behavior intact.
10. M0-M3 regression suites pass.

## Repository Audit

The worktree remains intentionally dirty with pre-existing M3/M4 source and documentation. No
tracked file was changed by clean-room acceptance. Untracked `output/`, `.playwright-cli/` and
`frontend/.tanstack/` paths contain screenshots/tool metadata, not database, object-store or user
dataset payloads; they were not deleted because the workspace already contained user-owned output.
