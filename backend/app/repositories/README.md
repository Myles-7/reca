# Persistence repositories

Repositories provide project-scoped database access for domain modules. The
pgvector integration belongs below this boundary: every vector query filters by
project and records embedding model, version, dimension and source-text hash.
External library objects are converted before persistence. No formal research
repository is implemented in M0.
