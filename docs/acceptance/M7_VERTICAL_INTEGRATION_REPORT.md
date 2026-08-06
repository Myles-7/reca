# M7 Stage-4 Vertical Integration Report

Date: 2026-08-06
Stage: 4
Branch: `feat/m2-research-literature`
HEAD: `951d872aa3567c2393e5ae7cad2b1900b55999d4`
Upstream: `origin/feat/m2-research-literature`
Migration head: `0018_m7_evidence_export`

## Entry Decision

Stage 4 originally entered while Open Design's `READY` decision was `NO`, so the run
completed only independent production Route infrastructure, focused mock-browser verification and
real backend PostgreSQL/Worker/MinIO integration. Open Design subsequently reaccepted the corrected
contracts and now states `READY_FOR_CODEX_INTEGRATION=YES`; the full real-API browser
Claim-to-Export chain is still not claimed by this report.

Docker Desktop became available during continuation. This supersedes the earlier unavailable
snapshot and resolves the environment portions of `M7-ISSUE-0002` and `M7-ISSUE-0003`.

## Implemented Integration Surface

- Single production Route: `/projects/$projectId/evidence`.
- Search contract: `claim`, `node`, `link`, `audit`, `export`, `package`, `view`.
- Generated/adapter/query/mutation/Container chain remains the only production API path.
- Query relationship checks fail closed to the authorized default without existence disclosure.
- React Flow receives server projection and exposes no connectable handles in focused browser use.
- ReproPackage download uses the authorized server URL and verifies Artifact bytes before response.
- Worker image contains the adopted `/app/uv.lock` and `/app/bun.lock` files.

## Focused Evidence

| Verification | Result |
| --- | --- |
| Backend evidence/export no-database tests | 30 passed, 3 deselected |
| Real PostgreSQL evidence/export suite | 33 passed |
| Fresh and repeated upgrade | PASS to `0018_m7_evidence_export` |
| Alembic check and heads | no drift; one 0018 head |
| Manifest/readme focused tests | 3 passed |
| Real Worker/MinIO ReproPackage vertical | 1 passed |
| Stage-4 Route contract guard | 2 tests, 13 assertions PASS |
| Focused production Route Playwright | 2 passed, mock backend responses |
| Frontend generated/boundary/fixture/build checks | PASS from Stage-4 focused baseline |

The real service runner used a unique PostgreSQL database, Valkey databases 9 and 10, a dedicated
temporary Celery Worker and the Compose MinIO service. Cleanup removed the Worker, force-dropped
the database, flushed both Valkey databases and deleted the package and Manifest objects.

## Real Export Evidence

- Project: `540bd132-a06c-4e9d-a2e7-3786fa577fed`
- Export: `187d88c2-8a31-46df-b65d-c8c5b3566cf2`
- Job: `b6ff05e8-dc46-49a8-8307-f06373cd1910`
- ReproPackage: `0504b850-92d7-4648-b3fa-5e2c69920cc8`
- ZIP Artifact: `45da1170-c218-47be-bdc4-f8698e498167`
- Manifest Artifact: `7c46ab07-17b3-4423-8a8a-29e53271fee9`
- ZIP SHA-256: `6fc1464fe660a2462370377685143e83419be007c2c884009aca0e86ed240b34`
- ZIP members: 21, stable sorted order
- Manifest payload files: 20, each reopened and checked for exact size and SHA-256
- Required members verified: `manifest.json`, `README_REPRODUCE.md`,
  `12_environment/locks/uv.lock`, `12_environment/locks/bun.lock`
- Final Export and Job status: `COMPLETED`; package download authorization succeeded

The package contained no reviewed deterministic analysis entrypoint, so an analysis rerun was not
fabricated. README truthfully states that no reviewed entrypoint is included, explicitly describes
SHA-256 verification and records `Agent logs: NOT_AVAILABLE` until M8.

No Claim, ClaimEvidenceLink, source, invalidation or Claim Audit IDs were created in this focused
Export-only runner. Those portions of the full browser longitudinal chain remain pending after the
Open Design READY gate. No screenshots are claimed; the focused browser test used production
Route/Container/UI with mocked API envelopes and verified no-disclosure fallback, table fallback,
non-connectable graph projection, 390px root bounds and keyboard focus.

## Remaining Boundary

1. Open Design revalidation is complete and `READY_FOR_CODEX_INTEGRATION=YES`.
2. Run the accepted visual Workspace against real API data through the complete
   Claim/Link/Graph/Audit/invalidation/readiness/Approval/Export/download browser chain.
3. Stage 5 remains responsible for the complete PostgreSQL, Worker/MinIO, Playwright, clean-room,
   security and supply-chain Exit Gate.

`STAGE_RESULT=PASS_WITH_ISSUES`

`READY_FOR_CODEX_INTEGRATION=YES`

`NEXT_STAGE_EXECUTED=NO`
