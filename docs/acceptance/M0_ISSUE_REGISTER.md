# RECA M0 Issue Register

## Summary

| Severity | Open | Resolved |
|---|---:|---:|
| BLOCKER | 0 | 0 |
| CRITICAL | 0 | 0 |
| HIGH | 1 | 0 |
| MEDIUM | 0 | 0 |
| LOW | 1 | 1 |

## Active Issues

| ID | Stage | Severity | Status | Area | Summary | M0 Blocked |
|---|---|---|---|---|---|---|
| M0-ISSUE-0002 | M0-02 | HIGH | OPEN | Container registry network | Docker Hub OAuth endpoint was unreachable, blocking image builds and service startup. | Yes |
| M0-ISSUE-0003 | M0-01 | LOW | OPEN | GitHub integration | GitHub CLI is unavailable, so the Draft PR could not be created or updated automatically. | No |

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
- Resolved commit: Pending M0-06 commit.
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
  service container was created.

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

## Resolved Issues

M0-ISSUE-0001 is retained above with its complete resolution history.
