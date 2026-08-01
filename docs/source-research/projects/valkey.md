# Valkey source research

Document version: `1.0.1`

Document status: `APPROVED FOR M1 DEVELOPMENT`

Research status: `ALREADY_INTEGRATED`

Last researched: 2026-07-31

Last updated: 2026-07-31

Phase summary: [Foundation runtime research](../../archive/open-source-research/OPEN_SOURCE_RESEARCH_PHASE_1_FOUNDATION.md)

## Upstream

| Field | Verified value |
| --- | --- |
| Repository | <https://github.com/valkey-io/valkey> |
| Default branch | `unstable` |
| Pinned research commit | `0bf28b2dab6d21ea278fbaf1517b45e55d9b9c6f` |
| Research commit date | 2026-07-28T20:42:59-07:00 |
| Latest release | `9.1.1`, published 2026-07-21 |
| License | Root project BSD-3-Clause; bundled files use the licenses catalogued in `LICENSES/` |
| License file | `COPYING`; additional SPDX texts under `LICENSES/` |
| Main language | C |
| Minimum runtime | No language runtime; compiled server. Upstream supports Linux, macOS, OpenBSD, NetBSD and FreeBSD |
| Dependency manifests | `Makefile`, `CMakeLists.txt`, vendored/dependency sources under `deps/` |
| Container/service requirements | Standalone Valkey service; network, memory and optional persistence volume |
| Test framework | Tcl/Tclx integration suites, module/API tests, Sentinel/Cluster tests and C/C++ unit tests |
| CI workflows | Core CI, daily/weekly matrices, sanitizers, Valgrind, TLS, CodeQL, Coverity, REUSE and provenance checks |
| Maintenance status | Active; latest stable release and default-branch activity observed in July 2026; repository not archived |

The default branch is explicitly an unreleased development branch. Its
`VALKEY_VERSION` is the placeholder `255.255.255`, and its release notes warn
against production use. Research metadata is pinned to that branch HEAD, but any
runtime recommendation must use a stable tagged image. RECA currently uses
`valkey/valkey:8.1.7-alpine`; this phase does not update it.

## Repository structure

| Path | Purpose |
| --- | --- |
| `src/` | Server, command, networking, persistence, cluster and module code |
| `deps/` | Bundled third-party dependencies |
| `tests/unit`, `tests/integration` | Core command and integration tests |
| `tests/sentinel`, `tests/modules`, `tests/rdma` | Specialized service and module tests |
| `design-docs/` | Feature and protocol design documents |
| `utils/` | Build, benchmark, cluster and operational utilities |
| `valkey.conf`, `sentinel.conf` | Reference configuration |
| `.github/workflows/` | Broad correctness, security, provenance and release automation |
| `LICENSES/`, `REUSE.toml` | File-level license catalog and REUSE metadata |

## Core capabilities

- In-memory key/value and data-structure operations.
- Redis protocol compatibility used by Celery's Redis transport.
- Pub/Sub and keyspace notification mechanisms.
- Expiry/TTL and bounded cache patterns.
- RDB snapshots and AOF persistence.
- Replication, Sentinel and Cluster modes.
- ACL, protected mode, TLS build options and command restrictions.

## Relevant modules

RECA needs only a small subset: Celery broker operations, short-lived result
backend entries, cache keys, optional distributed locks, rate-limit counters and
ephemeral SSE/event support. Sentinel, Cluster, modules, RDMA and advanced
replication are not Competition Edition requirements.

## Dependencies

Valkey is built with Make or experimental CMake and includes bundled dependency
sources. Optional TLS requires OpenSSL development libraries; optional systemd,
RDMA and alternate allocators add platform dependencies. Container use avoids
building these features inside RECA.

Root code is BSD-3-Clause, but the upstream repository contains files under
Apache-2.0, BSD-2-Clause, BSD-3-Clause, BSL-1.0, CC0-1.0, ISC, MIT and Zlib
licenses. Whole-source Vendor or Fork work would require file-level REUSE review.

## Tests

Upstream runs unit, integration, module API, Sentinel, Cluster, TLS, sanitizer,
Valgrind and cross-platform suites. RECA needs compatibility and failure tests
for its actual Celery/cache usage, not the full upstream server test matrix.

## Operational requirements

For Competition Edition, the minimum practical boundary is:

- private Compose network with no public management exposure;
- a stable tagged image, never the `unstable` branch artifact;
- health checking and bounded container resources;
- current AOF persistence retained until a deliberate broker-recovery test says
  it is unnecessary;
- TTL on result/cache/event keys;
- key namespaces or logical database separation for broker, result and cache
  roles when collision or cleanup risk appears;
- an eviction policy that does not silently discard broker data;
- database-backed recovery for every formal Job and business result.

TLS, Sentinel, Cluster and high-availability topology are not required for the
trusted local/school competition environment unless deployment scope changes.

## RECA current state

RECA runs `valkey/valkey:8.1.7-alpine` as an internal Compose service with
`--appendonly yes`. Celery uses a Redis-compatible URL. Valkey currently supports
infrastructure and smoke behavior; it is not a formal business data store.

## Recommended integration mode

`INDEPENDENT_SERVICE`

Retain one stable Valkey service for Competition Edition. No general Valkey
Adapter is needed. Celery owns broker/backend protocol use; RECA cache/lock code
should use narrow infrastructure helpers so keys, TTL and failure behavior stay
centralized.

## What to reuse

- Broker transport through the existing Celery integration.
- Short-lived result entries with expiration.
- Cache entries that can always be regenerated.
- Bounded locks that protect idempotent database operations.
- Pub/Sub only for ephemeral hints or live updates where replay is unnecessary.
- AOF/RDB operational behavior only as recovery support, not business authority.

## What not to reuse

- Valkey as the only store for Job, ProcessingRun, ApprovalRecord, permissions,
  AuditLog, AnalysisResult or Artifact lineage.
- Pub/Sub as a durable event log or SSE replay source.
- Cache presence/absence as proof of formal success or failure.
- Unbounded locks without token ownership and expiry.
- Cluster, Sentinel or advanced modules before a measured requirement.
- Default-branch `unstable` builds in the competition runtime.

## Domain boundary

PostgreSQL remains authoritative. A task can be redispatched from database state
after Valkey loss. A cache miss causes recomputation. A lock loss causes a
database state/idempotency recheck. A Pub/Sub message may improve latency but
cannot be required to reconstruct formal state.

## Milestone

- `M0 COMPLETED`: internal service, AOF and Celery smoke foundation.
- `M1`: define key ownership, TTL and database recovery behavior with Job.
- Later milestones: introduce caches/locks only for measured workflows.

## Risks

- Broker, result backend and cache roles can interfere under one memory budget.
- Eviction or expiry can look like task loss if the database boundary is weak.
- AOF reduces some restart loss but does not guarantee business completion.
- Pub/Sub drops messages for disconnected consumers.
- Celery's Redis client compatibility may lag or differ from Valkey releases.
- Pulling the `unstable` branch or floating tags would make demos less repeatable.

## Validation spike

Before formal asynchronous workflows rely on Valkey, test:

- exact Celery/Redis-client/Valkey version compatibility;
- restart during queued and running tasks with current AOF settings;
- recovery from deleted result keys while Job remains intact;
- cache TTL and namespace cleanup;
- lock expiry during a long task and duplicate delivery;
- Pub/Sub disconnect behavior if used for SSE hints;
- memory pressure without silent broker-key eviction.

No Valkey configuration or image was changed in this documentation-only phase.

## Attribution requirements

- Preserve the BSD-3-Clause notice for the root project.
- Record the exact image tag and repository in third-party notices.
- If source is copied, Forked or Vendored, preserve `COPYING`, `LICENSES/`,
  SPDX headers and REUSE metadata for differently licensed files.
- Do not describe inherited Redis/Valkey work as wholly original.

## Update strategy

Follow stable release tags only. Upgrade the container together with Celery
transport compatibility and restart/recovery tests. Do not track the `unstable`
branch, and do not adopt Cluster/Sentinel merely because upstream supports them.

## Change record

| Version | Date | Status | Change |
| --- | --- | --- | --- |
| 1.0.0 | 2026-07-31 | Conditional Approval | Recorded the research evidence, recommendation and RECA authority boundaries |
| 1.0.1 | 2026-07-31 | APPROVED FOR M1 DEVELOPMENT | Synchronized documentation approval; research status and integration facts are unchanged |
