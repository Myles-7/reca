# RECA M0 Final Review

## Verdict

PASS

## M1 Entry Decision

ALLOWED

## Reviewed Commit

`e975b67184f40c31d048d49780d9917a6f62dcc9` on `codex/m0-continuous`.

## Baseline and Checkpoints

`pre-m0-baseline` exists and was not modified. All checkpoints from
`m0-01-checkpoint` through `m0-fix-2-checkpoint` exist. `main` remains at
`5bd3be0`; `m0-complete` does not exist.

## Review History

| Review | Commit | Verdict | Main Reason |
|---|---|---|---|
| Initial final review | `834382e...` | FAIL | Worker and MinIO passing evidence was missing. |
| Final review 2 | `1e6a8e3...` | FAIL | Worker/MinIO now pass, but clean-room and required CI gates still fail. |

## Git and Scope

The branch is clean before this review-report update. Source scanning found no
M1 `ResearchProject`, `ProjectMember`, `Artifact`, `ApprovalRecord`,
`ProcessingRun`, `LiteratureRecord`, `DatasetVersion`, `AnalysisRun`, or Claim
model. No Agent, formal Job state machine, research seed data, or business
workspace was found. The continuous branch has not been merged to `main`.

## Infrastructure

`docker compose --env-file .env.example config -q` passes. The isolated
acceptance project built and started API, Worker, frontend, PostgreSQL+pgvector,
Valkey, MinIO, and the real fixed GROBID image. Compose uses fixed image tags,
separate edge/internal networks, scoped volumes, and no runtime
`upstream-lab` path. No critical `latest` reference was found.

## Backend

Backend format, Ruff, mypy, and the no-database M0 suite pass: 26 passed and
49 database-dependent template tests deselected. Health, request-ID, structured
error, configuration, OpenAPI, and Worker-unit tests are present. The isolated
run passed `/live`, `/ready`, `/dependencies`, and request-ID propagation.

## Configuration and Secrets

The typed Settings implementation supports local/test/demo/production and has
production validation and redaction tests. Static scans found no tracked `.env`
other than `.env.example`, private-key pattern, or AWS-key pattern. Python audit
passes with `PYTHONUTF8=1`; this environment setting avoids a Windows console
decoding limitation in the audit tool.

## Database and Migration

The isolated run passed empty-database migration and the repeated migration.
`/health/ready` and `/health/dependencies` reported PostgreSQL and pgvector as
HEALTHY. However, the separate required pgvector acceptance step failed before
connecting because its PowerShell inline Python command lost its SQL quotes
(`SyntaxError`). It is therefore not independent pgvector-command PASS evidence.

## Worker and Queue

Worker repair evidence is PASS:

| Check | Result | Evidence |
|---|---|---|
| Container / Celery app | PASS | Isolated worker starts with the non-root tmpfs ownership fix. |
| `inspect ping` | PASS | `worker-ping.log`: one node returned `pong`. |
| `health_ping` execution | PASS | `worker-health-ping.log` exited 0 after result retrieval and schema assertion. |
| Restart recovery | PASS | Isolated restart/persistence step exited 0. |
| Secret logging | PASS | Container-log secret scan exited 0. |

The task is registered as `reca.health_ping`, has soft/time limits, uses Valkey
as broker/result backend, and does not create M1 business state.

## MinIO Private Object Verification

PASS for the repaired smoke probe. The clean-room MinIO step creates a bucket,
writes and reads a small authenticated private object, and exits 0. The prior
SigV4 canonical-request newline error is absent. Restart/persistence and log
secret scans also pass. The current script does not itself emit a separate
anonymous-denial assertion, so that requirement remains part of the incomplete
clean-room acceptance rather than a confirmed PASS.

## Frontend

The generated-client CI-equivalent command, format/lint, direct TypeScript
check (`bunx tsc -p frontend/tsconfig.build.json --noEmit`), production build,
and six-case shell Playwright suite pass. The initial home, login, 404, and
system-status shell show no fabricated research metrics. The generic
`bun run test` command fails on Windows because the inherited Playwright config
launches `bun` through `cmd.exe`, which cannot resolve it; the dedicated shell
config is Windows-aware and passes. This is recorded as a review limitation,
not a successful default-test result.

## CI and Testing

Remote CI was independently checked through authenticated GitHub CLI. Workflow
run [`30454226516`](https://github.com/Myles-7/reca/actions/runs/30454226516)
for the reviewed commit is FAIL, not merely unverified:

| Job | Result | Evidence |
|---|---|---|
| backend-quality | PASS | Remote run completed successfully. |
| frontend-quality | FAIL | Fresh Linux generation leaves `frontend/src/client` absent before the trim script. |
| migration-test | FAIL | `ci@example.invalid` is rejected as a reserved email by Settings validation. |
| compose-smoke | FAIL | API curl occurs before readiness and receives connection reset. |
| e2e-smoke | NOT_RUN | Skipped because compose-smoke failed. |
| security-supply-chain | FAIL | Security script treats tracked `.env.example` as a forbidden `.env` file. |

The Actions are pinned to full SHAs and no critical `continue-on-error` or
`|| true` suppression was found. `bun audit` reports one retained LOW Babel 7
advisory; it has not been suppressed and is tracked as M0-ISSUE-0006.

## Security

No live secret, root project license, upstream `.git`, upstream `.env`, Docker
socket mount, user-home mount, key file, or local absolute upstream runtime
path was found. The acceptance script creates random test credentials at runtime
and removes its scoped Compose project. The remaining Node advisory is LOW but
still causes the current acceptance-script exit code to be nonzero.

## Open Source and Provenance

The readonly upstream HEAD is `c9e70d65c74f7adda417fc8de0757207ff77514c`.
`vendor/licenses/full-stack-fastapi-template-LICENSE.txt`,
`THIRD_PARTY_NOTICES.md`, and
`docs/source-research/full-stack-fastapi-template.md` exist. No root `LICENSE`
was created. Build/source policy scanning found no `latest` or `upstream-lab`
runtime dependency.

## Documentation Integrity

The approved product, architecture, data-model, API-contract, test, security,
and roadmap documents remain present and were not rewritten. This report and
the issue register correct prior evidence inconsistencies without modifying
approved requirements.

## Clean-Room Acceptance

The 2026-07-29 isolated run used project `reca_m0_acceptance`, generated an
unlogged random secret file, used scoped cleanup, and did not use the
developer's Compose volumes. Evidence is retained under
`D:\Temp\User\reca-m0-acceptance-20260729-210538`.

| Check group | Result |
|---|---|
| Build, startup, migrations, API health, frontend pages, restart/persistence | PASS |
| Worker ping and real `health_ping` result | PASS |
| MinIO authenticated private write/read | PASS |
| pgvector standalone acceptance command | FAIL (PowerShell quoting defect) |
| Node audit | FAIL (one tracked LOW advisory) |
| Overall script exit | FAIL (1) |

This is a complete execution with retained evidence, but not a clean-room PASS.

## Issue Register Summary

| Severity | Open | Resolved |
|---|---:|---:|
| BLOCKER | 0 | 0 |
| CRITICAL | 0 | 0 |
| HIGH | 2 | 2 |
| MEDIUM | 0 | 0 |
| LOW | 2 | 3 |

## Findings

| ID | Severity | Area | Evidence | Required Action |
|---|---|---|---|---|
| M0-ISSUE-0007 | HIGH | Clean-room | Isolated worker/MinIO PASS, but pgvector probe and final exit FAIL. | Correct the acceptance pgvector invocation and rerun full clean-room. |
| M0-ISSUE-0008 | HIGH | CI gates | Remote run 30454226516 has four core job failures. | Repair CI scripts; rerun all required jobs. |
| M0-ISSUE-0006 | LOW | Node supply chain | `bun audit` has one Babel 7 advisory. | Upgrade only when Router supports a safe compatible version. |
| M0-ISSUE-0009 | LOW | Frontend developer experience | Generic Windows Playwright command cannot resolve Bun. | Make default Playwright webServer platform-safe. |

## M0 Exit Criteria

| Criterion | Result | Evidence |
|---|---|---|
| OPEN BLOCKER/CRITICAL/HIGH = 0 | FAIL | M0-ISSUE-0007 and M0-ISSUE-0008 remain HIGH OPEN. |
| Worker inspect ping and health task | PASS | Clean-room logs. |
| MinIO authenticated private put/get | PASS | Clean-room log. |
| MinIO anonymous denial | NOT_RUN | No standalone assertion in the reviewed entry point. |
| Clean-room final exit | FAIL | Script exit code 1. |
| Empty/repeated migration | PASS | Clean-room migration logs. |
| pgvector | FAIL | Standalone acceptance command syntax failure. |
| Frontend functional checks | PASS | CI-equivalent build and shell Playwright. |
| Secret/license/provenance | PASS | Static checks and source review. |
| CI core checks | FAIL | Current remote workflow failure. |
| No M1 scope / no upstream runtime dependency | PASS | Source and policy scans. |

## Remaining Risks

The Babel 7 LOW advisory remains visible and unsuppressed. More importantly,
the two open HIGH issues block M0 because the clean-room exit and multiple
required CI jobs are not passing.

## Merge Decision

DO NOT MERGE. Draft PR [#1](https://github.com/Myles-7/reca/pull/1) exists and
must remain Draft/Open. `m0-complete` must not be created. Execute a focused
M0-FIX-3 for M0-ISSUE-0007 and M0-ISSUE-0008, then repeat independent review.

## Third Review Revalidation

### Review History

| Review | Commit | Verdict | Main Reason |
|---|---|---|---|
| Initial review | `834382e...` | FAIL | Worker and MinIO evidence was incomplete. |
| Second review | `2528373...` | FAIL | Clean-room and required CI remained incomplete. |
| Third review | `e975b67...` | PASS | Latest-head clean-room and required PR CI pass. |

### Latest Evidence

The fresh isolated acceptance run at
`D:\Temp\User\reca-m0-final-20260729-235219` exited `0`. It passed empty and
repeat migrations, pgvector, API health/request ID, Worker inspect and task,
MinIO private write/read/anonymous denial/persistence, frontend pages,
Playwright, two API restart recoveries, and repository/container scans.

Pull-request workflow `30467938346`, on this exact SHA, passed
backend-quality, frontend-quality, migration-test, compose-smoke,
security-supply-chain, and e2e-smoke. The stale concurrent push workflow is
not used as required-check evidence.

### Issue Register Summary

| Severity | Open | Resolved |
|---|---:|---:|
| BLOCKER | 0 | 0 |
| CRITICAL | 0 | 0 |
| HIGH | 0 | 4 |
| MEDIUM | 0 | 0 |
| LOW | 2 | 3 |

### Remaining Risks

M0-ISSUE-0006 remains an explicit LOW Babel 7 advisory with no compatible
patch. M0-ISSUE-0009 remains a LOW Windows developer-experience issue. Neither
changes the validated M0 runtime, security, or exit criteria.

### Merge Decision

PASS: mark PR #1 ready and merge only after its required checks remain green;
then create the annotated `m0-complete` tag on updated `main`.
