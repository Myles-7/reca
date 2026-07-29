# RECA M0 Issue Register

## Summary

| Severity | Open | Resolved |
|---|---:|---:|
| BLOCKER | 0 | 0 |
| CRITICAL | 0 | 0 |
| HIGH | 1 | 0 |
| MEDIUM | 1 | 0 |
| LOW | 1 | 0 |

## Active Issues

| ID | Stage | Severity | Status | Area | Summary | M0 Blocked |
|---|---|---|---|---|---|---|
| M0-ISSUE-0001 | M0-01 | MEDIUM | OPEN | Local toolchain | `uv`, Bun, pytest, Ruff, and mypy were unavailable for the imported application checks. | No |
| M0-ISSUE-0002 | M0-02 | HIGH | OPEN | Container registry network | Docker Hub OAuth endpoint was unreachable, blocking image builds and service startup. | Yes |
| M0-ISSUE-0003 | M0-01 | LOW | OPEN | GitHub integration | GitHub CLI is unavailable, so the Draft PR could not be created or updated automatically. | No |

## Detailed Issues

### M0-ISSUE-0001

- Detected stage: M0-01
- Severity: MEDIUM
- Status: OPEN
- Area: Local toolchain
- Summary: The local environment lacks the locked RECA Python and frontend
  toolchains needed to rerun application quality checks.
- Evidence: M0-03 found a standalone `pytest` executable, but its interpreter
  could not import `sqlmodel`; `python -m pytest` selected a different Python
  without pytest. The workstation provides Python 3.13 while the project
  requires Python 3.14 or later. Bun, uv, Ruff, and mypy remain unavailable.
  `python -m compileall -q backend/app backend/tests` completed successfully.
- Reproduction: Run the M0-01 lint, type-check, test, and frontend build
  commands in the current workstation environment.
- Impact: Full M0-01 runtime quality verification remains pending.
- Safe workaround: Run the locked toolchain in CI or a prepared developer
  environment without changing dependency versions.
- Root cause: Local development runtime does not include project tooling.
- Planned resolution: M0-FIX or CI clean-environment verification.
- Resolution target: M0-FIX
- Related tests: Backend format/lint/type/test; frontend install/lint/type/build;
  M0-03 configuration unit tests; M0-04 health and observability tests.
- Related files: `pyproject.toml`, `uv.lock`, `package.json`, `bun.lock`,
  `backend/tests/core/test_config.py`, `backend/tests/api/routes/test_health.py`.
- Introduced commit: `5bd3be0`
- Resolved commit: Not resolved.
- Resolution evidence: Not available.
- Notes: M0-03 and M0-04 added configuration and health tests but did not relax
  the locked Python version or install unpinned tooling to bypass the environment
  limitation. M0-04 syntax compilation completed successfully; its pytest run
  remains blocked before collection by the missing `sqlmodel` dependency.

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
- Impact: API/frontend build, infrastructure startup, health checks, and volume
  persistence tests cannot be accepted in this environment.
- Safe workaround: Use a network that can reach Docker Hub or a vetted internal
  registry mirror containing the same fixed image references.
- Root cause: External registry authorization endpoint is unreachable from the
  current environment.
- Planned resolution: Re-run the exact Compose test sequence when registry
  access is restored; do not replace fixed images with mocks or `latest` tags.
- Resolution target: M0-FIX
- Related tests: `docker compose build`, `up -d`, `ps`, `logs`, `restart`.
- Related files: `docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile`.
- Introduced commit: `8ba4a1e`.
- Resolved commit: Not resolved.
- Resolution evidence: Static Compose configuration succeeds; runtime evidence
  is pending registry access.
- Notes: No containers or persistent volumes were created by the failed launch.

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

No resolved issues recorded.
