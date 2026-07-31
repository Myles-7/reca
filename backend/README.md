# RECA Backend

The backend is a modular FastAPI monolith. M0 provides authentication, health,
configuration, observability, Alembic, Celery/Valkey, PostgreSQL/pgvector,
MinIO and GROBID service foundations. ResearchProject, Artifact, ApprovalRecord,
formal Job, literature, data, manuscript and Agent business flows remain
milestone work unless repository code proves otherwise.

## Commands

Run from the repository root:

```bash
uv sync --frozen
uv run ruff format --check backend
uv run ruff check backend
uv run mypy backend/app
uv run pytest backend/tests -m no_database
uv run alembic upgrade head
```

The only migration directory is `backend/app/alembic/`. The only Celery App is
`app.core.celery:celery_app`; M0 registers only the side-effect-free
`reca.health_ping` task.

## Current and planned ownership

Only `api/`, `core/`, `adapters/`, `workers/`, `cli/` and `alembic/` currently
have tracked implementation. The other rows define milestone boundaries and do
not claim that their directories or business flows already exist.

| Area | Status | Responsibility |
| --- | --- | --- |
| `domain/` | Planned | RECA policies and value objects; never third-party SDK models, queue states or Agent sessions |
| `modules/` | Planned | Domain-owned project, literature, data, analysis, manuscript, evidence and export modules; each capability has one owning module |
| `services/` | Planned | All business authority, permissions, transactions, state transitions, approval, provenance, invalidation and audit |
| `repositories/` | Planned | Project-scoped persistence and pgvector queries; external objects are converted before persistence |
| `adapters/` | Present | External APIs, multiple implementations, complex conversion, offline substitution and isolation boundaries |
| `workers/` | Present | Celery execution mechanics; Job/ProcessingRun remain database authority and tasks call Services |
| `tools/` | Planned | Deterministic tools and separate Agent Tool wrappers over Services; no arbitrary Python, Shell or SQL |
| `agents/` | Planned | M1 Prompt manifest governance and M8 single-Orchestrator runtime; SDK Session/Trace are not business state or audit |
| `shared/` | Planned | Small cross-cutting IDs, time helpers, errors, DTO primitives and logging context only |

## Open-source integration

Stable scientific libraries may be called directly inside a Service when their
objects do not leak into the domain. PyAlex and other external APIs use a
Provider/Adapter. GROBID remains an independent service. Selected PaperQA or
ARS assets require provenance-controlled Vendor placement and must not appear
unattributed in ordinary modules.

PaperQA output is candidate evidence, ASReview output is ranking advice,
Pandera failures are normalized quality issues, statsmodels Summary is not an
AnalysisResult, and SDK Session/Trace are not project state or audit records.

Read [the architecture](../docs/ARCHITECTURE.md),
[integration modes](../docs/decisions/ADR-002-OPEN-SOURCE-INTEGRATION-MODES.md)
and the relevant [source record](../docs/source-research/) before adding or
upgrading a third-party capability.

## Module guides

- [Adapters](./app/adapters/README.md)
- [Workers](./app/workers/README.md)

Planned package boundaries remain in the ownership table until their milestone
creates real implementation. Do not create README-only directories to mirror the
future architecture.
