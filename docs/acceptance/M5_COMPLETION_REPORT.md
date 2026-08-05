# M5 Completion Report

Date: 2026-08-05

## Completion

M5 is complete. The repository now provides:

- approved, version-bound AnalysisPlan workflows with optimistic concurrency and stale-hash rejection;
- deterministic descriptive, Pearson, Spearman, independent/paired two-group and simple OLS methods;
- immutable structured AnalysisResult plus system Code/Log Artifact provenance;
- five fixed Figure templates with validation, confirmation and PNG/SVG/PDF/Code Artifact lineage;
- atomic Worker execution, idempotency, cancellation, retry, stale-loss reconciliation and invalidation;
- generated OpenAPI client, fail-closed ViewModel/capabilities and one production Analysis Workspace;
- accepted desktop/tablet/mobile, Light/Dark and keyboard behavior.

## Verification Summary

```text
backend_full=380 passed, 2 skipped
backend_no_database=165 passed, 2 skipped
frontend_playwright=159 passed, 1 skipped
m5_production_browser=5 passed
open_design=53 fixtures, 318 combinations, 18 screenshots
clean_room=39 steps, 38 PASS + 1 accepted LOW advisory, 0 FAIL
migration_head=0016_m5_figures
production_integration=PASS
real_m5_vertical=PASS
```

## Retained Low Risk

- Bun audit reports one LOW `@babel/core` development-tooling advisory with no compatible locked
  remediation. It does not affect backend scientific execution; monitor before accepting untrusted
  source-map build input.
- Deterministic Figure comparison is structural/numeric rather than cross-platform byte equality.
  The production image freezes Noto CJK, Agg, template/style metadata and bounded dimensions.
- The two backend skips and one Playwright skip are opt-in external live-service cases; dedicated
  PostgreSQL, Worker, MinIO and M5 production browser paths passed in clean-room.

## Delivery State

Stages 0-5 completed without changing Git history. The user subsequently authorized this M5 closeout
to create and push a focused completion commit and `m5-complete` tag. Commit and tag identifiers are
reported from Git after creation rather than embedded circularly in the commit that creates them.

Historical UI/test output and Open Design process snapshots were moved to an external closeout archive;
reproducible caches and build products were removed from the working area without using `git clean`,
reset, destructive checkout or history rewriting.

```text
M5_COMPLETION=APPROVED
M6_ENTRY=ALLOWED
NEXT_STAGE_EXECUTED=NO
```
