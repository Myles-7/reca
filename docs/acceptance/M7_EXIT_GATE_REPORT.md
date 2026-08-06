# M7 Exit Gate Report

Date: 2026-08-06
Branch: `feat/m2-research-literature`
HEAD before completion commit: `951d872aa3567c2393e5ae7cad2b1900b55999d4`
Migration head: `0018_m7_evidence_export`

## Decision

`M7_EXIT=PASS`

`M7_COMPLETION=APPROVED`

`M8_ENTRY=ALLOWED`

M7 functional, database, browser, security and supply-chain Gates are approved. The complete `ty`
check now passes without blanket ignores or reduced checking.

## Centralized Fixes

- Repaired readiness JSONB persistence for UUID-bearing warnings and blockers.
- Restored formal Approval item coverage from server-projected ApprovalItems.
- Aligned Worker/API MinIO bucket configuration and the authorized browser download network path.
- Repaired M6 Revision Audit compatibility, DOCX degradation, parser payload validation and
  clean-room portability.
- Replaced narrow SQLModel datetime stub mismatches with a timezone-preserving typed helper;
  made cleaning selector/action narrowing and logger/settings typing explicit.
- Made M3 trusted-PDF highlight acceptance wait for an actual completed canvas render.
- Added bounded, fail-explicit Python dependency-audit retries for transient PyPI TLS failures.

## Full Gate Evidence

| Gate | Result |
| --- | --- |
| Ruff format/check | PASS |
| strict mypy | PASS, 148 source files |
| complete `ty` | PASS, 0 diagnostics |
| backend no-database | PASS, 230 passed, 3 skipped, 231 deselected |
| PostgreSQL/Worker/MinIO backend | PASS, 461 passed, 3 skipped |
| empty/repeated upgrade, alembic check | PASS |
| unique migration head | PASS, `0018_m7_evidence_export` |
| frontend format/lint/generated/build/guards | PASS |
| shell Playwright | PASS, 165 passed, 2 skipped |
| M3 PDF render regression | PASS, 6 passed |
| React Flow Spike | PASS, 2 passed |
| real API browser vertical | PASS |
| Secret scans | PASS, repository and container logs |
| Python dependency audit | PASS, no known vulnerabilities found |
| Bun dependency audit | PASS with one retained LOW Babel advisory |
| `git diff --check` | PASS |

Authoritative clean-room evidence:
`D:\Temp\User\reca-m0-acceptance-20260806-150804`

Real-browser evidence:
`D:\Temp\User\reca-m7-real-browser-20260806-151321`

## Exit Requirements

1. Link identity, same-project, status/hash/scope and idempotency: verified by PostgreSQL and API tests.
2. Suggested versus active authority and AI restrictions: verified by service and contract tests.
3. Backend graph authority and disabled React Flow persistence: verified by guards and browser tests.
4. Graph filters, cursor, partial projection, large graph and no-disclosure: verified.
5. Claim source chains through literature, data, analysis, figure, Approval and Audit: verified.
6. Completeness status semantics without scientific scoring: verified.
7. Audit execution/outcome separation and M6 compatibility: verified.
8. Invalidation history, path, idempotency and reconciliation: verified.
9. Readiness license/sensitive/restricted/missing/invalidated/unconfirmed/stale rules: verified.
10. Approval staleness and redistribution prohibition: verified.
11. Export/Job/package concurrency, retry, cancel and atomic failure behavior: verified.
12. Package, Manifest, Artifact and historical Export immutability: verified.
13. ZIP path, member, symlink, duplicate, size and project isolation controls: verified.
14. Manifest member, size, SHA-256, source and policy consistency: verified.
15. Runtime/upstream/prompt/rule/engine/citation adoption truth: verified.
16. Restricted metadata-only and sensitive exclusion defaults: verified.
17. README accuracy and explicit restricted-data limitations: verified.
18. API/OpenAPI/generated/adapter/error/idempotency/no-disclosure consistency: verified.
19. Production Claim-to-Graph-to-Export workspace, mobile, keyboard and table fallback: verified.
20. M0-M6 regressions and absence of M8 Agent implementation: verified.

## Retained Risk

- Bun audit retains the known LOW `@babel/core` advisory `GHSA-4x5r-pxfx-6jf8`.
- Large graphs remain bounded by server depth/node limits and progressive cursors.
- Restricted and sensitive sources remain metadata-only or excluded unless authorized by scope and
  formal Approval.

`STAGE_RESULT=PASS`

`NEXT_STAGE_EXECUTED=NO`
