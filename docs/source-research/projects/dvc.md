# DVC source research

Document version: `1.0.0`

Document status: `Conditional Approval`

Last researched: 2026-07-31

Phase summary: [Data, statistics and reproducibility research](../../reports/OPEN_SOURCE_RESEARCH_PHASE_3_DATA.md)

## Upstream

| Field | Verified value |
| --- | --- |
| Repository | <https://github.com/iterative/dvc> |
| Default branch | `main` |
| Pinned research commit | `f74c1c0e709de61f571905802bc0c75035dc6ef2` |
| Research commit date | 2026-07-10 |
| Latest release/tag | `3.67.1` |
| License | Apache-2.0 |
| License file | `LICENSE` |
| Main language | Python |
| Minimum runtime | Python `>=3.9` at the research commit |
| Dependency manifest | `pyproject.toml` |
| Container/service requirements | Git workspace; optional local/cloud remotes and provider-specific dependencies |
| Test framework | Pytest with functional, unit and benchmark support |
| CI workflows | package tests, lint/type checks, integration, docs and release workflows |
| Maintenance status | Active; repository was not archived at the research commit |

## Repository structure

| Path | Purpose |
| --- | --- |
| `dvc/repo/` | repository operations, stages, reproduction and experiments |
| `dvc/stage/` | stage definitions, dependencies, outputs and execution |
| `dvc/remote.py`, `dvc/data/` | remote/cache and data-object handling |
| `dvc/commands/` | CLI commands and argument behavior |
| `dvc/config.py` | repository/global configuration |
| `tests/` | CLI, pipeline, remote, cache, experiment and regression tests |
| `.dvc/`, `.dvcignore` | DVC's own repository metadata in the upstream project |

## Core capabilities

DVC versions large data by content hash, separates metadata from remote content,
defines pipeline stages with dependencies and outputs in `dvc.yaml`, records a
resolved state in `dvc.lock`, reproduces affected stages and tracks experiments
and parameters through a CLI-oriented Git workflow.

## Relevant concepts

- data files or directories represented by content-addressed metadata;
- remotes separated from Git metadata;
- explicit stage commands, `deps`, `outs`, parameters and metrics;
- `dvc.lock` as a resolved pipeline snapshot;
- selective reproduction based on dependency changes;
- experiments as temporary parameter/result branches around a pipeline.

## Dependencies

DVC has a broad dependency surface, including multiple DVC subpackages,
filesystem/provider integrations and Celery-related components. Cloud remotes
add more optional dependencies and credentials. This is disproportionate for a
P0 application runtime whose business lineage is already database-owned.

## Tests

Upstream tests cover repository/CLI behavior, stages, lockfiles, cache, remotes,
reproduction, experiments and failure recovery. RECA can reuse the provenance
and failure-scenario ideas without copying DVC's full repository semantics into
the product.

## Operational requirements

Runtime use assumes a controlled filesystem/Git workspace, DVC metadata, cache,
remote credentials and CLI/process orchestration. Those assumptions do not map
cleanly to project-scoped multi-user application requests or immutable object
storage Artifacts.

## RECA current state

RECA already defines `DatasetVersion`, `Artifact`, `ArtifactRelation`,
`DataTransformation`, `AnalysisPlan`, `AnalysisRun` and `ReproPackage`. DVC is
not installed or required. This research does not create `.dvc`, `dvc.yaml`, a
remote, pipeline or dependency.

## Recommended integration mode

`DEVELOPMENT_ONLY + DESIGN_REFERENCE`

DVC may be an optional developer CLI for curated demo/golden data if a later PR
shows clear value and records the added operational cost. It should not be a P0
application dependency or business-state service.

## Concept mapping

| DVC concept | Useful RECA mapping | Authority boundary |
| --- | --- | --- |
| content hash/cache | DatasetVersion/Artifact SHA-256 and immutable storage | RECA database and object storage remain authoritative |
| stage `deps`/`outs` | DataTransformation input/output lineage | Service validates project, approval and versions |
| `dvc.lock` | ReproPackage manifest snapshot | RECA manifest records runtime and Artifact IDs |
| parameters/experiments | AnalysisPlan and AnalysisRun provenance | approved plan and immutable result remain business facts |
| remote separation | development/demo dataset storage pattern | does not replace MinIO or access control |
| `dvc repro` | reproducible-command design inspiration | Worker executes only whitelisted RECA templates |

## Why DVC is not business truth

DVC state belongs to a repository/workspace/cache and is commonly changed by
CLI operations. It does not natively enforce RECA project isolation,
ApprovalRecord, database transactions, user roles, invalidation propagation,
Artifact relations or API idempotency. A `dvc.lock` entry cannot prove that a
user approved a transformation or that a DatasetVersion is formally available.

```text
RECA DatasetVersion = business truth
DVC metadata = optional development provenance
```

## What to reuse

- content-addressing and explicit dependency/output concepts;
- lock-snapshot and reproducible parameter capture ideas;
- tests for missing outputs, changed dependencies and partial failure;
- optional handling of curated, non-sensitive demo/golden datasets.

## What not to reuse

- DVC state as DatasetVersion or DataTransformation status;
- arbitrary stage commands in the RECA Worker;
- DVC experiments as AnalysisPlan approval or formal results;
- repository remotes as a replacement for project authorization/object storage;
- the full DVC runtime in P0 without a measured developer need.

## Domain boundary

If adopted for development, DVC remains outside the application:

```text
curated development/golden data
<-> optional developer DVC workspace/remote
-> explicit import through normal RECA upload Service
-> Artifact + DatasetVersion + project lineage
```

No DVC metadata crosses into formal domain state without normalization.

## Milestone

- M4/M5 development: optional provenance inspiration or curated fixture tooling.
- M7: lock/manifest ideas may inform ReproPackage design.
- No P0 runtime milestone is recommended.

## Risks

- duplicate truth between DVC metadata and the database;
- arbitrary pipeline commands conflicting with Agent/Worker code restrictions;
- large dependency and remote credential surface;
- developers assuming a Git/DVC hash equals user approval or project ownership;
- demo data licensing/sensitivity hidden behind a remote.

## Validation spike

Only if a concrete fixture-management problem appears, test a disposable DVC
workspace for one public demo dataset and one golden output. Measure setup,
remote/authentication, Windows/Compose ergonomics and CI cost. Confirm that
normal RECA upload produces its own independent DatasetVersion and lineage.

## Attribution requirements

Preserve Apache-2.0 and applicable notices for copied or distributed DVC code.
Record package/CLI versions if adopted. DVC does not grant rights to datasets
stored in a remote; each dataset requires separate provenance and license review.

## Update strategy

Do not add DVC until a bounded developer workflow justifies it. If adopted,
pin the CLI, keep metadata outside product authority, document remote ownership
and revalidate imports after upgrades. Removing DVC must not break RECA lineage.
