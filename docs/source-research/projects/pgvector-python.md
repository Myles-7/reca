# pgvector-python source research

Document version: `1.0.0`

Document status: `Conditional Approval`

Research status: `PLANNED`

Last researched: 2026-07-31

Phase summary: [Foundation runtime research](../../archive/open-source-research/OPEN_SOURCE_RESEARCH_PHASE_1_FOUNDATION.md)

## Upstream

| Field | Verified value |
| --- | --- |
| Repository | <https://github.com/pgvector/pgvector-python> |
| Default branch | `master` |
| Pinned research commit | `60739dfd6cb9d674f32afa4184d43e6aff9dfbcf` |
| Research commit date | 2026-07-06T11:25:13-07:00 |
| Latest tag | `v0.5.0`; the research commit is the tag commit |
| License | MIT |
| License file | `LICENSE.txt` |
| Main language | Python |
| Minimum runtime | Python `>=3.10` |
| Dependency manifest | `pyproject.toml` |
| Container/service requirements | None beyond a PostgreSQL server with pgvector and the application's selected Python driver/ORM |
| Test framework | Pytest and pytest-asyncio; strict typing checks |
| CI workflows | Python 3.10/3.14 matrix, PostgreSQL/pgvector build, Pytest, NumPy/SciPy and type checking |
| Maintenance status | Active; `v0.5.0` released in July 2026; repository not archived |

No root `SECURITY.md` was present in the inspected Commit. This is recorded as
an advisory-review requirement, not as a legal or security conclusion.

## Repository structure

| Path | Purpose |
| --- | --- |
| `pgvector/vector.py`, `halfvec.py`, `sparsevec.py`, `bit.py` | Python value types |
| `pgvector/sqlalchemy/` | SQLAlchemy types and distance expressions |
| `pgvector/psycopg/`, `psycopg2/` | Driver registration and codecs |
| `pgvector/django/`, `peewee/`, `pg8000/`, `asyncpg/` | Other framework/driver integrations |
| `examples/` | RAG, hybrid, sparse, image and model examples |
| `tests/` | Driver, ORM, SQLModel and vector-type tests |
| `.github/workflows/build.yml` | Runtime and typing matrix |

## Core capabilities

- SQLAlchemy `VECTOR`, `HALFVEC`, `BIT` and `SPARSEVEC` column types.
- SQLModel-compatible vector fields.
- Query expressions for L2, maximum inner product, cosine, L1, Hamming and
  Jaccard distance.
- Psycopg 3 sync/async type registration.
- Support for Django, SQLAlchemy, SQLModel, Psycopg, asyncpg, pg8000 and Peewee.
- Python vector value objects with optional NumPy/SciPy interoperation.

## Relevant modules

RECA only needs `pgvector.sqlalchemy.VECTOR` and its distance expressions for
SQLModel/SQLAlchemy. Direct Psycopg registration may be useful for raw driver
operations, but should not be added if SQLAlchemy already handles the required
types. Other ORM integrations are irrelevant to the current stack.

## Dependencies

The core package declares no mandatory runtime dependencies. Frameworks and
drivers are supplied by the application. Development groups exercise asyncpg,
Django, Peewee, pg8000, Psycopg 2/3, SQLAlchemy 2 and SQLModel.

RECA currently uses Python `>=3.14,<4.0`, SQLModel `>=0.0.39,<1.0.0` and
Psycopg 3. The upstream CI explicitly tests Python 3.10 and 3.14 and includes
SQLModel tests, so the candidate is structurally compatible. Exact compatibility
with RECA's pinned versions and pgvector server `0.8.2` still requires a spike.

## Tests

Pytest covers SQLAlchemy, SQLModel, Psycopg 2/3, asyncpg, pg8000, Django, Peewee
and vector value types. CI builds pgvector server `v0.8.4`, tests core behavior
with and without NumPy/SciPy, and runs strict typing tools.

## Operational requirements

There is no separate service. The package runs in the API/Worker Python
environment and requires the PostgreSQL `vector` extension. Migration ownership,
connection registration and query construction must be consistent across API,
Worker and tests.

## RECA current state

`pgvector-python` is not currently a RECA dependency. RECA has SQLModel and
Psycopg and has smoke-tested the server extension, but no ORM vector field or
research embedding query is implemented.

## Recommended integration mode

`DIRECT_DEPENDENCY`

Do not add a complex generic Adapter. Use the maintained SQLAlchemy/SQLModel type
and expression API directly inside the infrastructure model/repository layer.
Expose ordinary RECA DTOs and domain objects above that layer.

## What to reuse

- `VECTOR(dimensions)` for the planned embedding column.
- SQLAlchemy/SQLModel distance expressions.
- Psycopg registration only where raw connections need it.
- Upstream tests as design references for sync/async connection behavior and
  distance operations.
- Type hints and vector conversion behavior.

## What not to reuse

- Django, Peewee, pg8000 or asyncpg integrations without a stack change.
- Upstream RAG/model examples as RECA workflow or evidence authority.
- Third-party `Vector` objects in API schemas or core domain contracts.
- Direct Router or Agent access to SQLAlchemy vector expressions.
- Package addition before server-version, Alembic and Python 3.14 validation.

## Domain boundary

The dependency may appear in SQLAlchemy infrastructure models and repository
queries. Service inputs/outputs should use RECA-owned IDs, embedding metadata and
plain numeric arrays/DTOs. Repositories enforce `project_id`, current object
version and model/version compatibility. API and Agent Tool contracts remain
unchanged.

No separate Adapter is needed because the library is small, stable, replaceable
at the repository boundary and does not need to leak above persistence code.

## Milestone

- Candidate introduction: `M2`, when DocumentChunk embedding persistence starts.
- First query use: `M3`, for project-scoped exact retrieval.
- No need to add it in M1 solely because pgvector exists in M0.

## Risks

- Server extension `0.8.2` may not support every client `0.5.0` feature.
- SQLAlchemy type rendering can affect Alembic autogeneration.
- Connection registration can differ between sync and async drivers.
- Arrays with wrong dimensions or mixed models can fail late.
- Direct library convenience can tempt callers to omit project filters.
- Client query methods can expose approximate-index features before validation.
- Upgrade review must consult advisories because no root security policy file
  was present in the inspected snapshot.

## Validation spike

Before adding the package:

1. install it in an isolated branch without changing formal contracts;
2. declare a temporary SQLModel `VECTOR(n)` test model against RECA's exact
   PostgreSQL/pgvector image;
3. verify Alembic upgrade, downgrade and repeated migration behavior;
4. test Psycopg sync behavior used by the current backend;
5. test exact cosine/L2 expressions and deterministic ordering;
6. reject wrong dimensions and cross-project queries;
7. confirm generated OpenAPI schemas do not expose pgvector-specific objects;
8. run migration, backend and clean-room tests.

No dependency or model was added in this documentation-only phase.

## Attribution requirements

- Preserve the MIT license and Andrew Kane attribution when distributing the
  package or copied source.
- Record the exact package version in third-party notices when adopted.
- If examples or source are copied rather than installed, record copied paths and
  modifications separately.

## Update strategy

Pin a tested release compatible with the server extension and Python runtime.
Upgrade client and server independently only after a compatibility matrix,
migration test and exact-query regression pass.
