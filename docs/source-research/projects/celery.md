# Celery source research

Document version: `1.0.0`

Document status: `Conditional Approval`

Research status: `ALREADY_INTEGRATED`

Last researched: 2026-07-31

Phase summary: [Foundation runtime research](../../archive/open-source-research/OPEN_SOURCE_RESEARCH_PHASE_1_FOUNDATION.md)

## Upstream

| Field | Verified value |
| --- | --- |
| Repository | <https://github.com/celery/celery> |
| Default branch | `main` |
| Pinned research commit | `7c5d9a62d90c685bd0e1ae002d66ae40980b2847` |
| Research commit date | 2026-07-27T20:09:39+06:00 |
| Latest release | `v5.6.3`, published 2026-03-26 |
| License | Code: BSD-3-Clause; rendered `docs/` content: CC BY-SA 4.0 |
| License file | `LICENSE` |
| Main language | Python |
| Minimum runtime | Research source `setup.py`: Python `>=3.10`; the 5.6 README lists Python 3.9-3.13 and says 5.7 moves to 3.10+ |
| Dependency manifests | `setup.py`, `setup.cfg`, `pyproject.toml`, `requirements/`, `tox.ini` |
| Container/service requirements | A supported message broker; optional result backend; upstream integration tests use multiple external services |
| Test framework | Pytest, coverage and tox; unit, integration, smoke and benchmark suites |
| CI workflows | Python package, integration, smoke, lint, Docker, CodeQL and Semgrep workflows |
| Maintenance status | Active; default-branch activity observed on 2026-07-30; repository not archived |

The default branch and latest release are not identical snapshots. The research
commit reports `5.6.2` in `celery/__init__.py`, while the latest release tag is
`v5.6.3`. RECA currently pins `celery[redis]==5.5.3`; this phase does not update
that dependency.

The inspected `SECURITY.md` contains vulnerability-reporting contacts but its
supported-version table stops at 5.4.x. It is therefore not sufficient by itself
to decide support for 5.5/5.6; an upgrade must also review current release notes,
PyPI metadata and GitHub advisories.

## Repository structure

| Path | Purpose |
| --- | --- |
| `celery/app/`, `celery/apps/` | Application object and command/application setup |
| `celery/worker/`, `celery/concurrency/` | Worker lifecycle, pools and execution |
| `celery/backends/` | Result backend implementations |
| `celery/canvas.py` | Signatures, chains, groups, chords, maps and chunks |
| `celery/signals.py` | Task, worker, logging and lifecycle signals |
| `celery/events/` | Runtime events and monitoring state |
| `docs/` | User guides, configuration, routing, Canvas and operations |
| `examples/` | Broker, framework and task examples |
| `t/unit`, `t/integration`, `t/smoke` | Test suites |
| `docker/`, `helm-chart/` | Upstream development and deployment assets |

## Core capabilities

- `Celery` App configuration and task registry.
- Task declaration, serialization, routing, time limits and acknowledgment.
- Explicit retry with backoff, jitter and retry limits.
- Queue and exchange routing through Kombu.
- Canvas primitives: signatures, chain, group, chord, map and chunks.
- Worker lifecycle, pools, remote control, revoke and shutdown behavior.
- Optional result backends and event streams.
- Signals around publish, task execution, Worker lifecycle and logging.

## Relevant modules

RECA needs a single App, explicit task registration, JSON-only messages,
per-task time limits, retry classification, delivery metadata, queue routing and
minimal lifecycle signals for logging/heartbeat. Canvas is potentially useful
for fan-out or ordered processing, but only when RECA persists the workflow and
can resume it independently of Celery's transient graph state.

## Dependencies

Core dependencies include Billiard, Kombu, Vine, Click, python-dateutil and
timezone support. The Redis-compatible transport/backend adds the `redis`
dependency family. Broker and backend compatibility must be verified against
the exact RECA Celery and Valkey versions, not inferred from latest upstream.

## Tests

Upstream uses Pytest and tox across unit, integration and smoke suites. The test
matrix exercises Python versions, brokers/backends, concurrency pools, Docker
services, documentation checks and packaging. RECA should reuse the behavioral
ideas, not copy the entire upstream integration matrix into Competition Edition.

## Operational requirements

- Reachable broker and, if enabled, result backend.
- Stable task names and compatible serialization.
- Worker process management and graceful shutdown.
- Time limits, retry bounds and result expiration.
- Broker visibility/delivery behavior understood for the chosen transport.
- Monitoring sufficient to distinguish dispatch, execution and domain outcome.

Celery does not officially support Microsoft Windows as a production Worker
platform. RECA avoids relying on a native Windows Worker by running the accepted
Compose Worker and currently uses the `solo` pool for the M0 environment.

## RECA current state

RECA already uses `celery[redis]==5.5.3` as a direct dependency. The sole App is
`app.core.celery:celery_app`; the only M0 task is `reca.health_ping`. Current
configuration is JSON-only, UTC, bounded by soft/hard time limits, uses
`worker_prefetch_multiplier=1`, expires results after 300 seconds and currently
has `task_acks_late=False`.

The database-owned `Job` and `ProcessingRun` models remain planned business
authorities. The current Celery smoke task is not evidence that the formal Job
workflow is implemented.

## Recommended integration mode

`DIRECT_DEPENDENCY`

Keep Celery as the sole task-worker runtime. A generic third-party Adapter is not
needed. RECA should expose a small internal dispatch Service/repository boundary
that creates database state first, sends the task after commit, records the
Celery task ID and handles dispatch failure.

## What to reuse

- One App and explicit task modules.
- Bound tasks and explicit retry only for classified transient failures.
- Backoff/jitter and bounded retry counts.
- Task routes when resource isolation becomes necessary.
- Soft/hard time limits and Worker lifecycle hooks.
- Signals for telemetry that cannot change domain truth.
- Stamped headers or task metadata for `job_id`, project context and tracing,
  after checking message-data minimization.

## What not to reuse

- Celery events or result backend as the source of formal Job status.
- `PENDING` as proof that a task exists; it also means an unknown task ID.
- `SUCCESS` as proof that business validation, approval or artifact persistence
  succeeded.
- `REVOKED` as proof of `CANCELLED`; an executing task may continue unless it is
  forcibly terminated.
- Force termination as the normal cancellation mechanism. Upstream describes
  `terminate` as an administrator last resort because it kills a Worker child.
- Unpersisted Canvas graphs as the only record of a research workflow.
- Automatic retry of invalid schemas, permission errors, invalidated versions
  or unapproved plans.

## Domain boundary

Database state is authoritative:

1. create the business object and `Job` in one transaction;
2. commit;
3. dispatch Celery work;
4. mark `DISPATCH_FAILED` if publishing fails;
5. Worker reloads Job and input versions, acquires a lock and creates or updates
   `ProcessingRun`;
6. domain completion is committed before Celery transport success is treated as
   operationally finished.

Celery states are transport telemetry only:

| Celery state | RECA interpretation |
| --- | --- |
| `PENDING` | Unknown/not yet observed; never a formal Job state |
| `RECEIVED`, `STARTED` | Worker telemetry; may support heartbeat only |
| `RETRY` | Attempt-level event; Job retry counters and reason remain in DB |
| `SUCCESS` | Task function returned; domain output must still be verified |
| `FAILURE` | Execution exception; map through RECA error classification |
| `REVOKED` | Delivery/execution control signal; not confirmed cancellation |
| `IGNORED` | Celery result handling choice; not a business outcome |

## Queue decision

Competition Edition does not need multiple logical queues before contention is
observed. Keep one queue through early milestones. Before CPU-heavy analysis or
model tasks coexist with document I/O, validate a small split by resource class,
for example `io`, `compute` and `model`, with explicit routing and Worker limits.
Do not create queues solely to mirror every Job type.

## Milestone

- `M0 COMPLETED`: Worker/App/broker smoke foundation.
- `M1`: establish database-owned Job dispatch and idempotency boundary.
- `M2-M8`: add tasks incrementally; consider queue isolation only when measured.

## Risks

- Duplicate delivery and retry can produce duplicate outputs without idempotency.
- Force cancellation can terminate the wrong work in a reused Worker process.
- Result-backend expiry can be confused with missing business state.
- Canvas/chord recovery can be weaker than database-owned orchestration.
- Celery/Redis-client/Valkey compatibility can drift across upgrades.
- RECA Python 3.14 support must be verified for the exact pinned Celery release.
- The repository security support table is stale relative to the latest release.

## Validation spike

Before formal Job tasks ship, test:

- dispatch after database commit and `DISPATCH_FAILED` compensation;
- duplicate message delivery with the same idempotency key;
- transient retry versus permanent failure classification;
- Worker crash before and after output commit;
- cancellation request without force termination;
- result-backend expiry while Job history remains available;
- optional queue routing under one long CPU task and one short I/O task;
- compatibility of the exact Celery, Redis client and Valkey versions.

No queue or task was created in this documentation-only phase.

## Attribution requirements

- Preserve Celery's BSD-3-Clause notice for software distribution.
- Treat copied/rendered upstream documentation separately under CC BY-SA 4.0.
- Record exact package version and upstream source in third-party notices when
  the runtime is upgraded.
- Do not copy examples or documentation without checking their applicable
  license and attribution.

## Update strategy

Stay on a tested release line rather than default-branch HEAD. Upgrade only with
broker compatibility, Python runtime, retry/idempotency and clean-room Worker
tests. Do not align RECA to upstream merely because a newer Celery release exists.
