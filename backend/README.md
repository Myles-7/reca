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

## Ownership

| Area | Responsibility |
| --- | --- |
| `domain/` | RECA policies and value objects; never third-party SDK models |
| `modules/` | Domain-owned project, literature, data, analysis, manuscript, evidence and export modules |
| `services/` | All business authority, transactions, state transitions, approval and provenance |
| `repositories/` | Project-scoped persistence and pgvector queries |
| `adapters/` | External APIs, multiple implementations, complex conversion, offline substitution and isolation boundaries |
| `workers/` | Celery execution mechanics; Job/ProcessingRun remain database authority |
| `tools/` | Deterministic tools and separate Agent Tool wrappers over Services |
| `agents/` | M1 Prompt manifest governance and M8 single-Orchestrator runtime |
| `shared/` | Small cross-cutting primitives only |

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
