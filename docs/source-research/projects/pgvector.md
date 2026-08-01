# pgvector source research

Document version: `1.0.1`

Document status: `APPROVED FOR M1 DEVELOPMENT`

Research status: `ALREADY_INTEGRATED`

Last researched: 2026-07-31

Last updated: 2026-07-31

Phase summary: [Foundation runtime research](../../archive/open-source-research/OPEN_SOURCE_RESEARCH_PHASE_1_FOUNDATION.md)

## Upstream

| Field | Verified value |
| --- | --- |
| Repository | <https://github.com/pgvector/pgvector> |
| Default branch | `master` |
| Pinned research commit | `4f3d17f6f74fe98adf54df4d016de241eeaae9af` |
| Research commit date | 2026-07-29T12:29:47-07:00 |
| Latest tag | `v0.8.6`, tagged 2026-07-29; no GitHub Release object was published |
| License | PostgreSQL License |
| License file | `LICENSE` |
| Main language | C |
| Minimum runtime | PostgreSQL 13+, declared in `META.json` and README |
| Dependency manifests | `Makefile`, `Makefile.win`, `META.json`, `vector.control`, `Dockerfile` |
| Container/service requirements | PostgreSQL with extension build/install support; shared memory matters for parallel HNSW builds |
| Test framework | PostgreSQL regression tests, TAP/Perl tests and Valgrind runs |
| CI workflows | Linux/PostgreSQL matrix, macOS, Windows, i386 and Valgrind in `build.yml` |
| Maintenance status | Active; `v0.8.6` and default-branch activity observed in July 2026; repository not archived |

The research commit declares extension version `0.8.6`. RECA currently runs
`pgvector/pgvector:0.8.2-pg17`; no upgrade is made in this phase.

No root `SECURITY.md` was present in the inspected Commit. That absence is not a
finding that the project is insecure; it means an upgrade review must inspect
GitHub advisories, release notes and PostgreSQL compatibility directly.

## Repository structure

| Path | Purpose |
| --- | --- |
| `src/` | Vector types, distance functions, HNSW and IVFFlat access methods |
| `sql/` | Extension install and upgrade SQL scripts |
| `test/sql`, `test/expected` | PostgreSQL regression input and expected output |
| `test/t`, `test/perl` | TAP and Perl integration tests |
| `vector.control`, `META.json` | Extension and PGXN metadata |
| `Makefile`, `Makefile.win` | Unix and Windows builds |
| `Dockerfile` | PostgreSQL image builds across supported versions |
| `.github/workflows/build.yml` | Cross-version/platform test matrix |

## Core capabilities

- `vector`, `halfvec`, `bit` and `sparsevec` data types.
- L2, inner-product, cosine, L1, Hamming and Jaccard distance operators.
- Exact nearest-neighbor search without an approximate index.
- HNSW approximate indexes with `m`, `ef_construction` and `ef_search` tuning.
- IVFFlat approximate indexes with training data, `lists` and `probes` tuning.
- Iterative index scans for filtered approximate search.
- Partial indexes, partitioning and normal PostgreSQL filters.

## Relevant modules

RECA primarily needs the `vector(n)` type, cosine or L2 ordering, exact search,
project-scoped filtering and later optional HNSW. `halfvec`, sparse vectors,
binary quantization and hybrid-search examples are future optimization options,
not current requirements.

## Dependencies

pgvector is a PostgreSQL extension. It depends on PostgreSQL server development
headers when built from source. The published Docker approach compiles the
extension into a PostgreSQL base image. RECA already consumes a pinned image, so
it does not need the upstream C toolchain in the application container.

## Tests

Upstream tests extension installation/upgrades, vector types, distance
operators, HNSW, IVFFlat, filtering and platform compatibility across PostgreSQL
13 through current development versions. RECA needs migration, exact-query,
project-filter and index-plan tests against its pinned PostgreSQL image.

## Operational requirements

- `CREATE EXTENSION vector` through controlled migration/bootstrap logic.
- Fixed dimensions for indexed `vector(n)` columns.
- Query operator class aligned with the chosen distance metric.
- Index build memory and time measured on competition hardware.
- `ANALYZE`, vacuum and index maintenance included in operational testing.
- PostgreSQL backup/restore remains sufficient; pgvector is not a separate data
  service or separate source of truth.

## RECA current state

RECA uses `pgvector/pgvector:0.8.2-pg17`. M0 enables the extension and verifies a
minimal vector operation. No research business table, embedding workflow or
approximate index exists yet. Formal architecture requires P0 exact search first.

## Recommended integration mode

`INDEPENDENT_SERVICE`

This label means the existing pinned PostgreSQL service image contains the
extension; pgvector is **not** a new microservice. No application-level pgvector
Adapter is required at the extension boundary. Query construction should remain
inside RECA repositories/Services, potentially using `pgvector-python`.

## What to reuse

- PostgreSQL extension and `vector(n)` type.
- Exact cosine/L2 search for P0.
- Normal SQL `WHERE project_id = ...` filtering.
- HNSW only after dataset-size and recall/latency benchmarks justify it.
- Iterative scans if later approximate search plus filters returns too few rows.
- Extension-version checks during migration and clean-room acceptance.

## What not to reuse

- A separate vector database or duplicated vector truth.
- HNSW/IVFFlat by default on small competition datasets.
- IVFFlat before representative data and recall tuning exist.
- An ANN result without mandatory `project_id` isolation.
- Vector rows without embedding model, version, dimension and source hash/lineage.
- Floating extension versions or untested image updates.

## Search and index decision

P0 should use exact search. It provides perfect recall and is easier to validate
for the expected per-project corpus size. A B-tree index on `project_id` and a
project filter can reduce the candidate set before exact ordering.

HNSW is the first approximate candidate when measured latency requires it. It
has a better speed/recall trade-off than IVFFlat but costs more build time and
memory. With filters, pgvector applies approximate filtering after index scan;
iterative scans or higher `ef_search` may be required. IVFFlat remains deferred
unless build-memory constraints or a large stable corpus make its trade-off
preferable.

## Domain boundary

Every embedding remains attached to a RECA-owned object and version. Minimum
lineage includes `project_id`, source object/version, embedding model, model
version, dimension, text/content hash and ProcessingRun. Changing model,
dimension or source content creates/rebuilds derived embeddings; it does not
overwrite immutable source artifacts.

Queries must always filter by `project_id`. Vector distance is retrieval evidence
for ranking, not proof that a Claim or EvidenceSpan is valid.

## Milestone

- `M0 COMPLETED`: extension installation and smoke.
- `M2-M3`: DocumentChunk embeddings and exact project-scoped retrieval.
- Later only after benchmark: HNSW; IVFFlat remains a second-line option.

## Risks

- Approximate indexes can return too few filtered results.
- Distance operator/operator-class mismatch can silently change ranking.
- Mixed embedding models or dimensions can make results incomparable.
- HNSW build memory can exceed competition hardware limits.
- Extension/image upgrades can break migrations or restore compatibility.
- Treating similarity as evidence truth would violate research semantics.
- Security/support review cannot rely on a repository-local policy file alone.

## Validation spike

Before business use, test against the exact RECA image:

- clean and repeated `CREATE EXTENSION` migrations;
- `vector(n)` insert/query through the selected Python stack;
- exact cosine/L2 results with deterministic fixtures;
- mandatory `project_id` filter and cross-project negative cases;
- model/version/dimension mismatch handling;
- `EXPLAIN` plans and latency at representative project sizes;
- HNSW recall, filtered-result count and memory only if exact search misses its
  latency target;
- backup/restore and extension-version reporting.

No table or index was created in this documentation-only phase.

## Attribution requirements

- Preserve the PostgreSQL License and pgvector copyright notice.
- Record the exact container image tag in third-party notices.
- Record extension and image upgrades with the migration/validation PR.
- If source is copied or a custom image is built, retain the upstream license in
  the distributed image/source bundle.

## Update strategy

Follow stable tags and the matching PostgreSQL image. Upgrade only with migration,
query correctness, restore and clean-room tests. Keep exact search until a
documented benchmark demonstrates the need for an approximate index.

## Change record

| Version | Date | Status | Change |
| --- | --- | --- | --- |
| 1.0.0 | 2026-07-31 | Conditional Approval | Recorded the research evidence, recommendation and RECA authority boundaries |
| 1.0.1 | 2026-07-31 | APPROVED FOR M1 DEVELOPMENT | Synchronized documentation approval; research status and integration facts are unchanged |
