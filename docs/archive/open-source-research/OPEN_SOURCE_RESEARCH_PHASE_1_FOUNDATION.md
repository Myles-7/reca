# Open-Source Research Phase 1: Foundation Runtime Projects

Document version: `1.0.0`

Document status: `Conditional Approval`

Last updated: 2026-07-31

## 1. Scope

This phase researched only:

- `fastapi/full-stack-fastapi-template`;
- `celery/celery`;
- `valkey-io/valkey`;
- `pgvector/pgvector`;
- `pgvector/pgvector-python`.

Research used shallow clones of the actual GitHub repositories, fixed commits,
GitHub repository/release metadata, repository licenses, manifests, source
trees, tests, documentation, CI, deployment files and security guidance. The
temporary clones were outside the RECA workspace and were not incorporated.

## 2. Decision summary

| Project | Recommended mode | Runtime state | Milestone | Adapter required | Primary risk |
| --- | --- | --- | --- | --- | --- |
| Full Stack FastAPI Template | `ALREADY_INTERNALIZED_BASELINE` | Selected foundation already incorporated | M0 baseline | No | Whole-tree update would overwrite RECA specialization and migrations |
| Celery | `DIRECT_DEPENDENCY` | `5.5.3` present; only health task implemented | M0 foundation, M1+ jobs | No generic Adapter; internal dispatch Service required | Transport states/retries mistaken for domain truth |
| Valkey | `INDEPENDENT_SERVICE` | `8.1.7-alpine` present with AOF | M0 foundation, M1+ support | No generic Adapter; narrow cache/lock helpers | Ephemeral/evicted data mistaken for business truth |
| pgvector | `INDEPENDENT_SERVICE` within PostgreSQL | `0.8.2-pg17` extension smoke only | M0 foundation, M2-M3 retrieval | No extension Adapter; repository query boundary | Premature ANN or missing `project_id` isolation |
| pgvector-python | `DIRECT_DEPENDENCY` | Not installed | Candidate M2, first use M3 | No; keep it inside persistence repositories | Client/server/Alembic compatibility and type leakage |

Recommendations are research decisions, not implementation status. No runtime,
dependency, image, queue, table or index changed in this phase.

## 3. Fixed upstream facts

| Project | Default branch | Research commit | Latest release/tag | License | Maintenance |
| --- | --- | --- | --- | --- | --- |
| Full Stack FastAPI Template | `master` | `546f18469c30fb1748da21f044189f2f83639ea6` | `0.10.0` | MIT | Active |
| Celery | `main` | `7c5d9a62d90c685bd0e1ae002d66ae40980b2847` | `v5.6.3` | BSD-3-Clause code; CC BY-SA 4.0 docs | Active |
| Valkey | `unstable` | `0bf28b2dab6d21ea278fbaf1517b45e55d9b9c6f` | `9.1.1` | BSD-3-Clause root plus file-level licenses | Active |
| pgvector | `master` | `4f3d17f6f74fe98adf54df4d016de241eeaae9af` | `v0.8.6` | PostgreSQL License | Active |
| pgvector-python | `master` | `60739dfd6cb9d674f32afa4184d43e6aff9dfbcf` | `v0.5.0` | MIT | Active |

GitHub API reported Celery and pgvector as `NOASSERTION`/Other. The actual
repository license files resolve the software licenses above. This report does
not rely on API license classification alone.

Security metadata was also treated conservatively: Celery's repository policy
table lags its latest release, while the inspected pgvector and pgvector-python
roots have no separate `SECURITY.md`. Later upgrades must combine repository
files, advisories and release-specific evidence rather than infer support.

## 4. Full Stack FastAPI Template decision

The RECA source Commit is valid, exists upstream and is one Commit after release
`0.10.0`, not 186 Commits after it as the old record stated. The preserved MIT
license file exactly matches the upstream license blob at that Commit.

RECA has materially specialized backend modules, migrations, health/Worker code,
frontend shell, generated/adapter boundary, Compose topology, CI and clean-room
tests. The Item example was removed. The correct strategy is selective review of
small upstream fixes. Regenerating or overlaying the full template is rejected.

Detailed record: [full-stack-fastapi-template.md](../../source-research/full-stack-fastapi-template.md)

## 5. Celery decision

Celery remains the single Worker framework. `Job` and `ProcessingRun` in
PostgreSQL must own business state; Celery task IDs, result entries, events and
states are operational correlation only.

`PENDING` is ambiguous, `SUCCESS` only means the task returned, `REVOKED` does
not prove an executing task stopped, and result expiry is not business history.
Retries are allowed only for classified transient errors and must execute
idempotently. Force termination is an administrator last resort, not the normal
cancel path.

Multiple logical queues are deferred until resource contention is measured. A
small `io`/`compute`/`model` split can be validated before heavy M4/M8 workloads,
but Phase 1 creates no queues.

Detailed record: [celery.md](../../source-research/projects/celery.md)

## 6. Valkey decision

Valkey remains one internal Competition Edition service for Celery broker,
short-lived results and regenerable cache/lock/event support. PostgreSQL remains
authoritative for Job, approvals, permissions, artifacts, results and audits.

The current AOF setting is retained. Stable tags, private networking, TTL,
bounded resources and non-destructive eviction behavior are the minimum useful
competition concerns. Cluster, Sentinel, TLS platforms and enterprise HA do not
become requirements from this research.

The upstream default branch is `unstable` and explicitly not a production
release branch; RECA must never use its placeholder version as a runtime tag.

Detailed record: [valkey.md](../../source-research/projects/valkey.md)

## 7. pgvector decision

P0 uses exact project-scoped vector search. HNSW is evaluated only after a
representative corpus misses its latency target. IVFFlat remains secondary
because it needs representative training data and tuning and offers lower recall
for the expected small/dynamic competition corpus.

Every query requires `project_id`. Every stored embedding requires source
version, model, model version, dimension and content hash/lineage. Similarity is
ranking evidence, not an EvidenceSpan or Claim truth decision.

Detailed record: [pgvector.md](../../source-research/projects/pgvector.md)

## 8. pgvector-python decision

The library is a good direct-dependency candidate for M2/M3 because it supports
SQLAlchemy, SQLModel, Psycopg and Python 3.14 in upstream tests. It should remain
inside infrastructure models/repositories; API, domain and Agent contracts use
RECA-owned DTOs.

A complex Adapter adds little value. A thin repository boundary is still
mandatory for `project_id`, embedding-version compatibility and deterministic
query behavior. Adoption waits for a spike against RECA's exact pgvector
`0.8.2-pg17`, SQLModel, Psycopg and Alembic versions.

Detailed record: [pgvector-python.md](../../source-research/projects/pgvector-python.md)

## 9. Cross-project boundaries

- Full Stack upstream cannot overwrite accepted M0 code or migrations.
- Celery and Valkey cannot own formal business state.
- Celery retry/cancel behavior must be reconciled with database idempotency and
  cancellation state.
- pgvector remains part of PostgreSQL, not a separate vector microservice.
- `project_id` filtering is mandatory before vector results leave persistence.
- Embedding model/version/dimension lineage remains RECA-owned.
- No library convenience bypasses Service, permissions, version or approval.
- Existing M0 versions remain unchanged until an implementation PR validates an
  upgrade.

## 10. Unresolved questions

- Exact compatibility of Celery `5.5.3`, its Redis client and Valkey `8.1.7` for
  all later retry/revoke/result behaviors.
- Whether one queue remains sufficient once M4 analysis and M8 model work run
  concurrently.
- Whether current Valkey broker/result/cache roles need logical DB separation or
  only key namespaces.
- Exact client/server compatibility between pgvector-python `0.5.0` and server
  extension `0.8.2`.
- The representative corpus size and latency threshold that would justify HNSW.
- Whether any new Full Stack upstream security fix warrants selective backport.

These questions require implementation spikes or version-specific review; they
are not blockers for this documentation research result.

## 11. No-code-change confirmation

This phase modified only source-research Markdown and this report. It did not
modify the nine formal entry documents, application code, tests, dependencies,
Compose, CI, migrations, generated clients or lock files. It copied no upstream
code, Prompt, script, fixture or test into RECA.
