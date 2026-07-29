# RECA M0 Issue Register

## Summary

| Severity | Open | Resolved |
|---|---:|---:|
| BLOCKER | 0 | 0 |
| CRITICAL | 0 | 0 |
| HIGH | 0 | 4 |
| MEDIUM | 0 | 0 |
| LOW | 2 | 3 |

## Active Issues

| ID | Stage | Severity | Status | Area | Summary | M0 Blocked |
|---|---|---|---|---|---|---|
| M0-ISSUE-0006 | M0-FIX | LOW | OPEN | Node supply chain | A low-severity Babel 7 advisory has no compatible fixed release for the current TanStack Router plugin. | No |
| M0-ISSUE-0008 | M0-FINAL-REVIEW-2 | HIGH | RESOLVED | CI core gates | Required PR CI now passes on the reviewed commit. | No |
| M0-ISSUE-0009 | M0-FINAL-REVIEW-2 | LOW | OPEN | Frontend local test command | The generic `bun run test` command cannot start the inherited Playwright server on Windows because `cmd.exe` cannot resolve Bun. | No |

## Detailed Issues

### M0-ISSUE-0001

- Detected stage: M0-01
- Severity: LOW
- Status: RESOLVED
- Area: Local frontend toolchain
- Summary: Bun remains unavailable for host-side frontend checks.
- Evidence: M0-06 installed fixed Bun `1.2.22` without changing project
  dependency constraints, then ran the locked install, production build, Biome
  check, and the six-case Playwright shell suite.
- Reproduction: `bun --version`, `bun install --frozen-lockfile`, and `bun run build`.
- Impact: Resolved; host-side frontend verification is available.
- Safe workaround: Not required.
- Root cause: Local development runtime previously did not include Bun.
- Planned resolution: Completed in M0-06.
- Resolution target: M0-06
- Related tests: `bun install --frozen-lockfile`, `bun run build`, `bunx biome check`, and `bun run test:shell`.
- Related files: `package.json`, `bun.lock`.
- Introduced commit: `5bd3be0`
- Resolved commit: `656eec6238d7ec895bb9a0525f160ac609e4e0e7`.
- Resolution evidence: Bun `1.2.22`; six Playwright tests passed; production build and Biome check passed.
- Notes: The local Bun installation is a workstation tool only; no project dependency version or lockfile changed.

### M0-ISSUE-0002

- Detected stage: M0-02
- Severity: HIGH
- Status: RESOLVED
- Area: Container registry network
- Summary: Docker could not obtain an OAuth token from Docker Hub, so API and
  frontend base images could not be pulled or built.
- Evidence: `docker compose build` failed with `auth.docker.io` TCP 443
  connection timeout. `docker compose up -d` exceeded two minutes before any
  service container was created.
- Reproduction: Run `docker compose build` in the current workstation.
- Impact: API/frontend build, infrastructure startup, health checks, volume
  persistence, M0-05 migration execution, and Celery integration tests cannot
  be accepted in this environment.
- Safe workaround: Use a network that can reach Docker Hub or a vetted internal
  registry mirror containing the same fixed image references.
- Root cause: External registry authorization endpoint is unreachable from the
  current environment.
- Planned resolution: Re-run the exact Compose test sequence when registry
  access is restored; do not replace fixed images with mocks or `latest` tags.
- Resolution target: M0-FIX
- Related tests: `docker compose build`, `up -d`, `ps`, `logs`, `restart`,
  Alembic upgrade, pgvector query, Celery inspect ping, and Celery task dispatch.
- Related files: `docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile`.
- Introduced commit: `8ba4a1e`.
- Resolved commit: `fix(m0): resolve consolidated M0 issues` (stage-close commit).
- Resolution evidence: M0-FIX pulled the fixed Python and Bun base images and
  clean-room acceptance passed image build, PostgreSQL, Valkey, MinIO, GROBID,
  empty and repeated migrations, and API dependency readiness.
- Notes: M0-05 retried `docker compose up -d postgres valkey api worker`; it
  failed again at Docker Hub OAuth for `python:3.14.3-slim-bookworm` before any
  service container was created. M0-07 also retried
  `docker compose build api worker frontend`; Docker Hub OAuth timed out for
  both `python:3.14.3-slim-bookworm` and `oven/bun:1.2.22`.
  M0-08 clean-room acceptance retried the isolated build on 2026-07-29 and
  received the same Docker Hub OAuth timeout. No `reca_m0_acceptance` service
  container was started, and its scoped resources were cleaned up.

### M0-ISSUE-0003

- Detected stage: M0-01
- Severity: LOW
- Status: RESOLVED
- Area: GitHub integration
- Summary: GitHub CLI is not installed in the current environment.
- Evidence: The initial environment lacked `gh`; on 2026-07-29 the authenticated
  GitHub CLI created Draft PR #1 for `codex/m0-continuous` to `main`.
- Reproduction: Run `gh --version` in the repository shell.
- Impact: Resolved; the PR now exists and remains Draft pending a passing review.
- Safe workaround: Not required.
- Root cause: Local toolchain omission, later remedied in the review environment.
- Planned resolution: Completed in M0-FINAL-REVIEW-2.
- Resolution target: M0-FINAL-REVIEW-2
- Related tests: `gh auth status`.
- Related files: `docs/development/M0_CONTINUOUS_EXECUTION.md`.
- Introduced commit: `5fe2da6`
- Resolved commit: `docs(m0): complete second final M0 review` (this review
  stage-close commit).
- Resolution evidence: `gh pr create --repo Myles-7/reca --base main --head
  codex/m0-continuous --draft` returned
  `https://github.com/Myles-7/reca/pull/1`.
- Notes: The earlier unrelated Node-audit text was a ledger transcription error;
  that evidence belongs to M0-ISSUE-0004 and M0-ISSUE-0006.

### M0-ISSUE-0004

- Detected stage: M0-07
- Severity: HIGH
- Status: RESOLVED
- Area: Node supply chain
- Summary: `bun audit` reports 31 vulnerabilities, including two critical and
  sixteen high findings, in the locked frontend dependency tree.
- Evidence: `bun audit` reports vulnerable transitive packages including `tar`,
  `handlebars`, `postcss`, and a direct advisory for
  `@hey-api/openapi-ts` `0.73.0`.
- Reproduction: Run `bun audit` at the repository root after `bun install --frozen-lockfile`.
- Impact: The new `security-supply-chain` gate correctly fails until vulnerable
  locked dependencies are updated and verified.
- Safe workaround: None. Do not suppress advisories or use an ignore list.
- Root cause: M0-01 retained upstream frontend dependency versions; multiple
  advisories have since been published for direct and transitive packages.
- Planned resolution: Review compatible fixed versions, regenerate the frontend
  client if required, update the lockfile deliberately, and rerun the complete
  frontend quality and security suite.
- Resolution target: M0-FIX
- Related tests: `bun audit`, `scripts/ci/security-smoke.sh`, and the GitHub
  `security-supply-chain` job.
- Related files: `frontend/package.json`, `bun.lock`, and
  `.github/workflows/m0-quality.yml`.
- Introduced commit: `5bd3be0` (imported dependency baseline).
- Resolved commit: `834382ec4b2854956dc20d7dfe8e3fdcf3e3c8d2`.
- Resolution evidence: M0-FIX updated direct, transitive, and generator
  dependencies deliberately; `bun audit` now reports only the separately
  tracked LOW Babel 7 advisory in M0-ISSUE-0006.
- Notes: The CI security gate remains required and fails on the remaining LOW
  advisory without an ignore list. Its additional false-positive `.env.example`
  failure is tracked separately by M0-ISSUE-0008.

### M0-ISSUE-0005

- Detected stage: M0-08
- Severity: LOW
- Status: RESOLVED
- Area: Clean-room acceptance tooling
- Summary: The first acceptance-script execution used APIs and command forms
  incompatible with Windows PowerShell 5 and its path handling.
- Evidence: The first run failed at `RandomNumberGenerator.Fill`, a Windows
  glob passed to `rg`, and an incorrectly rooted Playwright command. The final
  rerun passed tool/version, source-policy, backend, frontend, Playwright, and
  repository-secret checks.
- Reproduction: Run `./scripts/m0-acceptance.ps1` in Windows PowerShell 5.
- Impact: The initial script could not provide a clean acceptance result; no
  production application path, container resource, or secret was affected.
- Safe workaround: Use the corrected script, which relies on
  `RandomNumberGenerator.Create()`, Git pathspecs, and the frontend-local
  Playwright command.
- Root cause: The initial cross-platform draft assumed newer PowerShell APIs
  and Unix-style glob behaviour.
- Planned resolution: Completed in M0-08.
- Resolution target: M0-08
- Related tests: PowerShell parser check, `bash -n scripts/m0-acceptance.sh`,
  and the final `./scripts/m0-acceptance.ps1` run.
- Related files: `scripts/m0-acceptance.ps1`, `scripts/m0-acceptance.sh`.
- Introduced commit: M0-08 working tree before the final acceptance rerun.
- Resolved commit: `test(m0-08): add clean environment acceptance` (stage-close commit).
- Resolution evidence: Final clean-room run at 2026-07-29T20:10+08:00 passed
  all independent checks and reported only the pre-existing Docker Hub and Node
  supply-chain failures.
- Notes: This history is retained because the protocol requires failed test
  executions to be recorded even when a low-risk tooling repair is immediate.

### M0-ISSUE-0006

- Detected stage: M0-FIX
- Severity: LOW
- Status: OPEN
- Area: Node supply chain
- Summary: `bun audit` retains one LOW advisory for Babel 7 used by the
  TanStack Router plugin.
- Evidence: All 31 prior advisories were removed; forcing the available Babel 8
  release caused the router compiler to fail at runtime.
- Reproduction: `bun audit`.
- Impact: CI security audit remains non-green for this low-severity finding.
- Safe workaround: None without disabling the router compiler or suppressing
  the audit, neither of which is acceptable.
- Root cause: No compatible fixed Babel 7 release is published.
- Planned resolution: Upgrade the router plugin when it supports Babel 8.
- Resolution target: M1 dependency maintenance.
- Related tests: `bun audit`, frontend build, Playwright shell suite.
- Related files: `package.json`, `bun.lock`, `frontend/package.json`.
- Introduced commit: `fix(m0): resolve consolidated M0 issues` (stage-close commit).
- Resolved commit: Not resolved.
- Resolution evidence: Not available.
- Notes: LOW only; it does not reopen the closed M0 HIGH supply-chain issue.

### M0-ISSUE-0007

- Detected stage: M0-FINAL-REVIEW
- Severity: HIGH
- Status: RESOLVED
- Area: Clean-room acceptance
- Summary: The worker and private-MinIO blockers are repaired, but the required
  clean-room entry point is still non-passing.
- Evidence: `D:\Temp\User\reca-m0-acceptance-20260729-210538` records PASS for
  `worker-ping`, `worker-health-ping`, `minio-private-write-read`, restart, and
  persistence. It records FAIL for `pgvector` because the PowerShell command
  loses SQL quoting, and FAIL for the retained LOW `bun audit` advisory.
- Reproduction: `./scripts/m0-acceptance.ps1` after images are available.
- Impact: The Worker and MinIO-specific evidence now passes, but the full
  clean-room script exits 1 and cannot satisfy the M0 exit criterion.
- Safe workaround: None; no mock Worker or public bucket is acceptable.
- Root cause: The former worker root-owned tmpfs and MinIO literal `\\n` SigV4
  canonical-request defects were repaired in `1e6a8e3`. The remaining failure
  is an acceptance-script quoting defect plus the documented LOW audit result.
- Planned resolution: Correct the pgvector command with an argument-safe smoke
  probe and establish explicit non-blocking LOW-audit reporting without
  suppressing it; rerun the full script.
- Resolution target: M0-FIX-3.
- Related tests: Worker inspect ping, `health_ping`, MinIO private write/read.
- Related files: `docker-compose.yml`, `backend/app/core/celery.py`, `scripts/m0-acceptance.ps1`.
- Introduced commit: `834382ec4b2854956dc20d7dfe8e3fdcf3e3c8d2`.
- Resolved commit: `fix(m0): repair clean-room and CI blockers` (stage-close
  commit).
- Resolution evidence: `scripts/m0-acceptance.ps1` run
  `reca-m0-acceptance-20260729-215418` records PASS for pgvector, Worker ping,
  registered task, `health_ping`, MinIO authenticated write/read, anonymous
  denial, restart persistence, cleanup, and every blocking step. The only
  advisory is explicitly `PASS_WITH_LOW_ADVISORY` for M0-ISSUE-0006.
- Notes: The run uses the isolated `reca_m0_acceptance` project and random,
  unlogged credentials. The former PowerShell quoting and MinIO coverage gaps
  are closed.

### M0-ISSUE-0008

- Detected stage: M0-FINAL-REVIEW-2
- Severity: HIGH
- Status: RESOLVED
- Area: CI core gates
- Summary: The remote M0 workflow at run `30454226516` fails four required jobs
  on the current repair checkpoint.
- Evidence: `gh run view 30454226516 --log-failed` shows: security smoke treats
  `.env.example` as tracked `.env`; frontend client generation removes the
  output directory on a clean Linux runner; migration smoke uses
  `ci@example.invalid`, which Pydantic rejects; and compose smoke curls API
  before readiness, receiving connection reset.
- Reproduction: `gh run view 30454226516 --repo Myles-7/reca --log-failed`.
- Impact: Required CI core checks are not passing; M0 cannot be merged.
- Safe workaround: None. Do not disable failing checks or use
  `continue-on-error`.
- Root cause: CI script correctness and readiness handling defects.
- Planned resolution: Apply minimal script fixes, rerun the same pinned CI
  workflow, and retain the LOW Babel audit as a visible risk rather than a
  suppressed failure.
- Resolution target: M0-FIX-3.
- Related tests: `scripts/ci/security-smoke.sh`,
  `scripts/ci/frontend-quality.sh`, `scripts/ci/migration-smoke.sh`, and
  `scripts/ci/compose-smoke.sh`.
- Related files: `.github/workflows/m0-quality.yml`, `scripts/ci/`, and
  `frontend/openapi-ts.config.ts`.
- Introduced commit: `1e6a8e34741ebdd402ba1994106d7cd0d2b2cf95` verification.
- Resolved commit: `e975b67184f40c31d048d49780d9917a6f62dcc9`.
- Resolution evidence: Pull-request run `30467938346` for the resolved commit
  passed all required jobs: backend-quality, frontend-quality, migration-test,
  compose-smoke, security-supply-chain, and e2e-smoke.
- Notes: The concurrent push run `30467933944` is stalled during dependency
  installation, but it has the same head SHA and is not the completed PR
  required-check result.

### M0-ISSUE-0009

- Detected stage: M0-FINAL-REVIEW-2
- Severity: LOW
- Status: OPEN
- Area: Frontend local test command
- Summary: The default frontend Playwright command is not Windows-portable.
- Evidence: `bun run --cwd frontend test` fails before tests begin with
  `'bun' is not recognized as an internal or external command` from the
  inherited Playwright `webServer` command.
- Reproduction: `bun run --cwd frontend test` in Windows PowerShell.
- Impact: The dedicated, Windows-aware shell configuration passes all six M0
  browser checks; CI E2E has a separate Compose configuration. This is a local
  developer-experience failure, not evidence of a passing generic command.
- Safe workaround: `bun run --cwd frontend test:shell`.
- Root cause: `frontend/playwright.config.ts` runs `bun run dev` through
  Windows `cmd.exe` without resolving the Bun executable.
- Planned resolution: Make the default config use the same platform-safe
  executable resolution as the shell config, preserving CI behavior.
- Resolution target: M1 developer-experience maintenance or M0-FIX-3 if the
  CI repair touches Playwright configuration.
- Related tests: `bun run --cwd frontend test` and `bun run --cwd frontend
  test:shell`.
- Related files: `frontend/playwright.config.ts`.
- Introduced commit: M0-01 imported frontend test configuration.
- Resolved commit: Not resolved.
- Resolution evidence: Not available.
- Notes: This issue is not used to reduce the severity of the current HIGH
  clean-room or CI failures.

## Resolved Issues

M0-ISSUE-0001 is retained above with its complete resolution history.
