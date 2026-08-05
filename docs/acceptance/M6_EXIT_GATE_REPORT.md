# M6 Exit Gate Report

Date: 2026-08-05  
Stage: 5  
Owner: Codex

## Decision

```text
M6_EXIT=PASS_WITH_ISSUES
M6_COMPLETION=APPROVED
M7_ENTRY=ALLOWED
```

All previously blocking issues are resolved with focused code changes and regression
evidence. The remaining host-only PostgreSQL runner limitation is non-gating because
the authoritative in-network migration runner completed the full migration check.
No M7 functionality was added.

## Verified

- DOCX security preflight focused coverage and M6 golden parser checks passed for
  the implemented boundary, including macro, traversal, symlink, nested archive,
  external relationship and resource-limit rejection cases.
- M6 golden: 1 passed. M6 OpenAPI: 5 passed. Manuscript no-database tests: 7 passed,
  1 skipped. Full no-database backend baseline: 195 passed, 3 skipped, 221 deselected.
- Frontend generated-client consistency, M6 contract guards, UI boundary and
  production-mock guards, TypeScript and Vite build passed in the accepted Stage 3.5
  batch. `alembic heads` reports the single head `0017_m6_manuscripts`.
- `git diff --check` passed. The two focused Ruff formatting failures were repaired
  and rechecked successfully.

## Gate Gaps

- The host-only PostgreSQL test process still cannot connect reliably on Windows;
  Compose-network migration verification passed `upgrade head`, repeated upgrade,
  and `alembic check`. This remains a documented non-gating environment limitation.
- Full real longitudinal browser E2E remains a documented limitation; the production
  M6 route is registered and the generated/adapter/query/Container/build guards pass.
- `mypy`/`ty` still report existing cross-module/SQLModel and migration diagnostics;
  these were recorded as verification limitations, not suppressed.
- The Windows shell security script could not invoke `uv` from bash; no security
  pass was inferred from that failed harness.

## Scope Integrity

Original Artifacts and Versions were not overwritten. No commit, tag or push was
created. Evidence Graph, ClaimEvidenceLink, ReproPackage, Agent and Demo scope were
not implemented.

`NEXT_STAGE_EXECUTED=NO`
