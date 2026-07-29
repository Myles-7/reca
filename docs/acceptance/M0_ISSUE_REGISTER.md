# RECA M0 Issue Register

## Summary

| Severity | Open | Resolved |
|---|---:|---:|
| BLOCKER | 0 | 0 |
| CRITICAL | 0 | 0 |
| HIGH | 2 | 0 |
| MEDIUM | 0 | 0 |
| LOW | 1 | 2 |

## Active Issues

| ID | Stage | Severity | Status | Area | Summary | M0 Blocked |
|---|---|---|---|---|---|---|
| M0-ISSUE-0002 | M0-02 | HIGH | OPEN | Container registry network | Docker Hub OAuth endpoint was unreachable, blocking image builds and service startup. | Yes |
| M0-ISSUE-0003 | M0-01 | LOW | OPEN | GitHub integration | GitHub CLI is unavailable, so the Draft PR could not be created or updated automatically. | No |
| M0-ISSUE-0004 | M0-07 | HIGH | OPEN | Node supply chain | Locked frontend dependency tree has disclosed critical and high vulnerabilities. | Yes |

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
- Status: OPEN
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
- Resolved commit: Not resolved.
- Resolution evidence: Static Compose configuration succeeds; M0-05 also
  passed Alembic offline SQL generation and a direct `health_ping` unit call.
  Runtime evidence is pending registry access.
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
- Status: OPEN
- Area: GitHub integration
- Summary: GitHub CLI is not installed in the current environment.
- Evidence: `gh --version` returned command-not-found.
- Reproduction: Run `gh --version` in the repository shell.
- Impact: The required Draft pull request was not created automatically.
- Safe workaround: Create or update the Draft PR from a GitHub CLI-enabled
  environment without modifying branch history.
- Root cause: Local toolchain omission.
- Planned resolution: M0-FIX or release-environment preparation.
- Resolution target: M0-FIX
- Related tests: `gh auth status`.
- Related files: `docs/development/M0_CONTINUOUS_EXECUTION.md`.
- Introduced commit: `5fe2da6`
- Resolved commit: Not resolved.
- Resolution evidence: Not available.
- Notes: The continuous branch and checkpoint tags were pushed successfully.

### M0-ISSUE-0004

- Detected stage: M0-07
- Severity: HIGH
- Status: OPEN
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
- Resolved commit: Not resolved.
- Resolution evidence: Not available.
- Notes: The CI job remains required and intentionally fails rather than hiding
  the advisories. M0-08 reran `bun audit` and reproduced the same 31 findings;
  no ignore list or automatic dependency upgrade was introduced.

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

## Resolved Issues

M0-ISSUE-0001 is retained above with its complete resolution history.
