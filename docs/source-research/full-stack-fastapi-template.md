# Full Stack FastAPI Template source research

Document version: `2.0.1`

Document status: `APPROVED FOR M1 DEVELOPMENT`

Research status: `ALREADY_INTEGRATED`

Last researched: 2026-07-31

Last updated: 2026-07-31

Phase summary: [Foundation runtime research](../archive/open-source-research/OPEN_SOURCE_RESEARCH_PHASE_1_FOUNDATION.md)

## Upstream

| Field | Verified value |
| --- | --- |
| Repository | <https://github.com/fastapi/full-stack-fastapi-template> |
| Default branch | `master` |
| Pinned research commit | `546f18469c30fb1748da21f044189f2f83639ea6` |
| Research commit date | 2026-07-30T19:46:08Z |
| RECA import commit | `c9e70d65c74f7adda417fc8de0757207ff77514c` |
| Latest release | `0.10.0`, published 2026-01-23 |
| License | MIT |
| License file | `LICENSE` |
| Main language | TypeScript according to GitHub; repository is TypeScript/Python |
| Minimum runtime | Current backend manifest: Python `>=3.14,<4.0`; Bun is used but no minimum Bun version is declared in `package.json` |
| Dependency manifests | `pyproject.toml`, `backend/pyproject.toml`, `package.json`, `frontend/package.json`, `uv.lock`, `bun.lock` |
| Container/service requirements | Docker Compose; PostgreSQL; optional Traefik, Adminer and Mailcatcher development/deployment services |
| Test framework | Pytest and Playwright |
| CI workflows | Backend tests, Playwright, Compose tests, pre-commit, Zizmor, deployment and release-support workflows |
| Maintenance status | Active; default-branch commit observed on 2026-07-30; repository not archived |

The previous source record said the RECA import commit was 186 commits after
`0.10.0`. Direct Git verification shows it is **one commit after** the tag. The
current research commit is one additional commit after the RECA import commit.
This document corrects the provenance count without changing incorporated code.

The upstream `LICENSE` blob at the RECA import commit is
`f11987b50cfa15ae4f99d4c559137458c87d7a69`. The preserved RECA snapshot at
`vendor/licenses/full-stack-fastapi-template-LICENSE.txt` has the same Git blob
hash, so the current license snapshot is complete for that upstream root file.

## Repository structure

| Path | Purpose |
| --- | --- |
| `backend/app/` | FastAPI application, SQLModel models, authentication, routes, CRUD and migrations |
| `backend/tests/` | Pytest API, CRUD, startup and utility tests |
| `frontend/src/` | React/Vite application, generated client, routes and UI components |
| `frontend/tests/` | Playwright authentication, administration and item-flow tests |
| `.github/workflows/` | Quality, test, Compose, security-analysis and deployment automation |
| `compose*.yml` | Local, staging and production-oriented Compose topology |
| `.copier/`, `copier.yml` | Template generation and update machinery |
| `scripts/`, `hooks/` | Client generation, tests, formatting and project hooks |
| `development.md`, `deployment.md` | Local development and Traefik-based deployment guidance |

## Core capabilities

- FastAPI backend with SQLModel, PostgreSQL and Alembic.
- JWT authentication, password recovery, user settings and superuser flows.
- React/Vite/TypeScript frontend with TanStack Router and Query.
- Generated OpenAPI client workflow.
- Pytest backend coverage and Playwright browser acceptance tests.
- Docker images and Compose-based local/deployment topology.
- Traefik, Adminer, Mailcatcher and staging/production deployment examples.
- Copier-based project generation and upstream template update support.

## Relevant modules

The retained foundation is the authentication/user shell, FastAPI application
setup, SQLModel/Alembic baseline, React application shell, generated-client
workflow, test tooling, Docker build pattern and quality tooling.

The upstream demonstration `Item` model, CRUD routes, UI, generated API surface
and tests are not RECA domain capabilities and were intentionally removed.

## Dependencies

The current upstream research commit uses a newer dependency set than RECA's
fixed M0 baseline. Examples include FastAPI, SQLModel, React, Vite, TanStack,
Playwright and Python 3.14 constraints. Those versions are research evidence,
not an instruction to update RECA dependencies.

The template also assumes services and deployment choices that RECA does not
inherit automatically, including PostgreSQL 18, Traefik, Adminer, Mailcatcher,
Sentry and upstream-specific deployment workflows.

## Tests

Upstream tests cover login, users, private routes, the example Item feature,
backend startup, browser authentication, password reset, administration and
item CRUD. CI includes dedicated backend, Playwright and Docker Compose runs.

RECA retained the useful testing foundation and replaced template-specific Item
coverage with M0 health, migration, Worker, system-status and clean-room tests.

## Operational requirements

The upstream project expects Python, Bun, PostgreSQL and Docker Compose. Its full
deployment path additionally assumes Traefik, public DNS/TLS configuration,
GitHub environments and deployment secrets. Those deployment assumptions are
not part of RECA Competition Edition merely because the template contains them.

## RECA current state

RECA already incorporated a controlled file-level baseline from
`c9e70d65c74f7adda417fc8de0757207ff77514c` using `SELECTIVE_COPY`. Git history,
upstream `.env`, caches, build output, IDE files and runtime data were excluded.

Tracked-tree comparison against that fixed source shows material RECA
specialization:

- `backend/app/`: 18 common files remain identical, 12 are changed, six
  upstream-only paths include Item routes and upstream migrations, and 22
  RECA-only paths include health, Celery, Worker, adapter, module and smoke code;
- `backend/tests/`: Item tests were removed and migration, health, Settings and
  Worker tests were added;
- `frontend/src/`: Item routes/components were removed, while the RECA shell,
  system status, generated/adapter boundary and module placeholders were added;
- `frontend/tests/`: Item coverage was replaced by system-shell and Compose
  status coverage.

RECA also replaced the upstream migration history with the accepted M0
migration baseline, introduced pgvector/Valkey/MinIO/GROBID/Worker services,
and established six required CI checks plus clean-room acceptance.

## Recommended integration mode

`ALREADY_INTERNALIZED_BASELINE`

This is stronger and more precise than recommending a new Fork or Vendor. RECA
already owns a specialized internal baseline with recorded provenance. It must
not be replaced by a fresh generated template or a whole-tree upstream copy.

## What to reuse

- Security and bug fixes selected file by file.
- Useful authentication improvements after compatibility review.
- Build, test and generated-client workflow improvements that preserve RECA's
  Bun, OpenAPI and clean-room contracts.
- Small frontend accessibility or dependency-maintenance improvements.
- Documentation or deployment ideas when they fit Competition Edition.

## What not to reuse

- Whole-repository replacement or Copier regeneration over the current tree.
- Upstream Item model, routes, UI, migrations or generated Item client.
- Upstream `.env`, production secrets, Traefik topology or deployment workflows
  without a separate RECA decision.
- Automatic dependency or lock-file replacement.
- Any upstream migration that overwrites RECA's accepted Alembic history.
- Any upstream authentication change that bypasses current API contracts,
  project isolation or M0 regression gates.

## Domain boundary

The template remains engineering provenance, not a business-domain authority.
RECA owns ResearchProject, Artifact, ApprovalRecord, Job, ProcessingRun,
EvidenceSpan, DatasetVersion, AnalysisRun and manuscript contracts. Upstream
models, DTOs, routes and generated client output cannot redefine them.

## Milestone

The imported foundation belongs to `M0 COMPLETED`. Selective upstream review is
maintenance work and must not be presented as a new M1 product capability.

## Risks

- Whole-tree updates could restore deleted Item behavior or corrupt migrations.
- Current upstream runtime versions can move faster than the RECA tested stack.
- Authentication and generated-client changes can create broad regressions.
- Deployment examples can introduce unnecessary competition complexity.
- The old 186-commit provenance statement was inaccurate and is corrected here.

## Validation spike

Before adopting any upstream change:

1. compare the exact upstream Commit and selected paths;
2. review migrations, API routes, Settings and authentication separately;
3. regenerate the OpenAPI client only through the RECA workflow;
4. run the six required CI checks;
5. run clean-room acceptance for Compose, migration, Settings, generated-client
   or infrastructure changes;
6. update the source record and modification summary in the same PR.

No validation spike was executed in this documentation-only phase.

## Attribution requirements

- Preserve the MIT license snapshot and Sebastian Ramirez attribution.
- Keep the upstream repository and fixed source Commit in this record.
- Record every newly copied path and modification.
- Do not describe template-derived foundation code as entirely original RECA
  work.

## Update strategy

Track upstream releases and security fixes, but synchronize by reviewed patch or
small selected path. Never use whole-tree overwrite, automatic Copier update or
lock-file replacement against the specialized RECA repository.

## Change record

| Version | Date | Status | Change |
| --- | --- | --- | --- |
| 2.0.0 | 2026-07-31 | Conditional Approval | Recorded the research evidence, recommendation and RECA authority boundaries |
| 2.0.1 | 2026-07-31 | APPROVED FOR M1 DEVELOPMENT | Synchronized documentation approval; research status and integration facts are unchanged |
