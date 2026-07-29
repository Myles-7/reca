# RECA M0 Clean-room Acceptance Report

## Execution context

- Date: 2026-07-29 (Asia/Shanghai)
- Branch and commit at start: `codex/m0-continuous` / `7154bc57a7606d2da8655f25d148d3680631ab80`
- Baseline: `pre-m0-baseline` remains unchanged.
- Compose project: `reca_m0_acceptance`.
- OS: Windows 11 10.0.26200, 64-bit.
- Host capacity: Intel Core i7-14650HX (16 cores / 24 logical processors),
  31.73 GiB physical memory.
- Docker / Compose: 29.5.2 (`79eb04c`) / v5.1.4.
- Python / Bun / uv: 3.13.13 / 1.2.22 / 0.9.26.
- Evidence directory: `D:\Temp\User\reca-m0-acceptance-20260729-201049`.
  It contains command-specific, non-secret logs. The temporary `.env` was
  deleted during cleanup.

## Isolation and inputs

The script creates random, one-run-only secrets outside the repository, leaves
model and OpenAlex keys empty, uses ports 18000 and 15173, and runs only
`docker compose --project-name reca_m0_acceptance ... down -v`. It does not
read a developer `.env`, remove default volumes, or run a global Docker prune.

| Input | SHA-256 |
|---|---|
| `pyproject.toml` | `368A87524CDAC5B688B73D6F7927E59F5C001E5CB590A8F440F87ED08104B99D` |
| `uv.lock` | `2435720EC3535549A7D082ADDE5128A8BC3B284622B44723C97EDD4E982A76AB` |
| `package.json` | `1945E1C804FB8EF8866D0A53DF7D6A63DC15B6231FA04068ED4579E6F19B2FA9` |
| `bun.lock` | `1D92BE3E6DF0E27DE7958640FACDA26EDD390B153CF5D016A68E27D889BC1BAA` |

## Results

| Check | Result | Exit code | Evidence / issue |
|---|---|---:|---|
| Git status, tool versions, lock hashes | PASS | 0 | acceptance logs |
| License/source, no `latest`, no upstream path | PASS | 0 | acceptance logs |
| `docker compose ... config -q` | PASS | 0 | acceptance logs |
| API, Worker, Frontend image build | FAIL | 1 | M0-ISSUE-0002 |
| PostgreSQL, Valkey, MinIO, GROBID startup and health | NOT_RUN | 0 | blocked by image build |
| Empty and repeated Alembic migrations; pgvector | NOT_RUN | 0 | blocked by image build |
| live, ready, dependencies, request ID | NOT_RUN | 0 | blocked by image build |
| Worker ping and `health_ping` | NOT_RUN | 0 | blocked by image build |
| MinIO private bucket write/read | NOT_RUN | 0 | blocked by image build |
| Frontend home and system-status | NOT_RUN | 0 | blocked by image build |
| Restart and persistence checks | NOT_RUN | 0 | blocked by image build |
| Container log secret scan | NOT_RUN | 0 | no containers were created |
| Backend no-database tests | PASS | 0 | `26 passed, 49 deselected` |
| Frontend format, lint, production build | PASS | 0 | acceptance logs |
| Playwright shell suite | PASS | 0 | `6 passed` |
| Repository secret scan | PASS | 0 | acceptance logs |
| Python `pip-audit` | PASS | 0 | no known vulnerabilities |
| Node `bun audit` | FAIL | 1 | M0-ISSUE-0004, 31 findings |

## Failure evidence and limitations

`docker compose build api worker frontend` failed while obtaining OAuth tokens
from `https://auth.docker.io/token` for fixed `python:3.14.3-slim-bookworm` and
`oven/bun:1.2.22` images. This is a real external registry connectivity issue,
not a substitute-container result. GROBID was not replaced with a stub.

The existing locked Node dependency tree remains vulnerable: `bun audit`
reported 31 advisories (2 critical, 16 high, 11 moderate, 2 low). The audit is
left failing; no suppression or wholesale dependency upgrade was applied.

## Conclusion

**M0-FIX REQUIRED.** A provisional M0 PASS cannot be issued: isolated runtime
services, migrations, pgvector, Worker, MinIO, front-end runtime, and restart
persistence could not be observed, and the Node supply-chain gate fails.
Resolve M0-ISSUE-0002 and M0-ISSUE-0004, then rerun the same acceptance script
from a Docker Hub-reachable environment before final review.

## M0-FIX re-verification

On 2026-07-29, the fixed Python and Bun base images were pulled and the isolated
acceptance run completed real container checks. Image build, infrastructure
startup, empty and repeated Alembic upgrades, API live/ready/dependencies,
request ID, restart persistence, backend checks, frontend build, Playwright,
repository secret scan, and Python audit passed. `bun audit` is reduced to one
LOW Babel 7 advisory; no compatible Babel 7 fix exists for the installed
TanStack Router plugin, and forcing Babel 8 was verified to break its compiler.
Worker ping and the MinIO SigV4 private-object probe remain failed acceptance
steps and require final review before M0 can be declared PASS.
