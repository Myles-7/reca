# grobid-client-python source research

Document version: `1.0.0`

Document status: `Conditional Approval`

Research status: `EXPERIMENT_REQUIRED`

Last researched: 2026-07-31

Phase summary: [Literature and evidence research](../../archive/open-source-research/OPEN_SOURCE_RESEARCH_PHASE_2_LITERATURE.md)

## Upstream

| Field | Verified value |
| --- | --- |
| Repository | <https://github.com/grobidOrg/grobid-client-python> |
| Default branch | `master` |
| Pinned research commit | `161e0f45189c8592b2e2c58e9638cc6218bc75fb` |
| Latest release/tag | `v0.1.5` |
| License | Apache-2.0 |
| License file | `LICENSE` |
| Main language | Python |
| Minimum runtime | Unresolved: the inspected `pyproject.toml` does not declare `requires-python` |
| Dependency manifests | `pyproject.toml`, `requirements.txt` |
| Container/service requirements | Reachable GROBID REST service |
| Test framework | Pytest |
| CI workflows | `ci-build.yml`, `ci-release.yml` |
| Maintenance status | Active; repository was not archived at the research commit |

## Repository structure

| Path | Purpose |
| --- | --- |
| `grobid_client/client.py` | HTTP client and processing behavior |
| `grobid_client/grobid_client.py` | CLI and batch orchestration |
| `config.json` | server, batch, coordinate, sleep and timeout defaults |
| `tests/` | configuration, concurrency, retry and conversion tests |
| `resources/` | sample inputs/configuration |

## Core capabilities

The client wraps `processFulltextDocument`, `processHeaderDocument`,
`processReferences` and related service calls. It supports batch directory
processing, configurable concurrency through `ThreadPoolExecutor`, coordinates,
timeouts and retry/sleep behavior for a busy `503` service. The default server
is `http://localhost:8070`; CLI concurrency is configurable and commonly starts
around ten workers.

## Relevant modules

`grobid_client/client.py` contains the reusable transport behavior;
`grobid_client/grobid_client.py` contains CLI and batch-directory concerns that
should mostly remain outside RECA.

## Dependencies

Dependencies are dynamically loaded from `requirements.txt`. Adoption must pin
the resolved HTTP/CLI dependency set and verify it against RECA's Python runtime;
the upstream manifest currently leaves the minimum Python version unresolved.

## Output organization

The batch workflow writes outputs such as `document.grobid.tei.xml` beside or
under output directories. It also includes TEI-to-JSON/Markdown conveniences.
Those are useful for experiments but conflict with RECA's immutable Artifact,
object-storage key and database-lineage model. Some convenience conversions are
lossy and cannot replace the RECA converter.

## Configuration and retries

Configuration covers server URL, batch size, coordinates, sleep time and
timeout. Upstream handles service-busy `503` responses with sleep/retry. RECA
must bound attempts, classify other failures, connect retries to Job attempts
and avoid parallel requests exceeding the pinned GROBID service capacity.

## Tests

Upstream tests cover configuration precedence, output-directory creation,
concurrent processing, `503` retry and TEI conversions. RECA can reuse these
test patterns, especially transport behavior, but must replace filesystem
assumptions with Artifact/Worker tests.

## Operational requirements

- Worker-only network access to the GROBID service;
- explicit server/version compatibility;
- concurrency lower than or equal to measured service capacity;
- bounded timeout/retry and cancellation checks;
- response bytes stored as a TEI Artifact before conversion;
- no dependence on local batch output paths.

## RECA current state

The Python client is not installed. RECA has a GROBID healthcheck only and no
formal M2 client/converter implementation.

## Recommended integration mode

`SELECTIVE_COPY` is preferred for the small, validated HTTP/concurrency behavior.
`DIRECT_DEPENDENCY` remains acceptable if package maintenance and API fit are
confirmed during the spike. In either mode, expose a RECA-owned client interface
and keep the upstream batch filesystem model out of the domain.

## What to reuse

- request parameter construction for official endpoints;
- multipart transport and coordinate options;
- bounded concurrency pattern;
- `503` busy handling and associated tests;
- configuration precedence ideas.

## What not to reuse

- directory crawling as the production ingestion model;
- output filenames or directories as Artifact identity;
- lossy JSON/Markdown conversion as canonical parsing;
- client-created project state or status;
- unbounded retry or concurrency defaults.

## Domain boundary

The client only transports an immutable PDF Artifact to GROBID and returns raw
TEI bytes plus HTTP metadata. A separate RECA converter owns:

```text
TEI
-> validated converter DTO
-> DocumentPage
-> DocumentChunk
-> LiteratureReference
```

Neither the client nor its output folders create RECA objects directly.

## Milestone

M2, together with the pinned GROBID service and converter.

## Risks

- client release lag versus current GROBID service;
- thread count overwhelming the service;
- retry policy duplicating Worker retries;
- local filesystem assumptions leaking into object storage;
- lossy conversion hiding TEI details needed for evidence validation.

## Validation spike

Compare direct `httpx` transport with the pinned client package for one header,
full-text and references request; test `503`, timeout, corrupt PDF and coordinate
options. Choose the smaller maintained surface. Verify TEI bytes are stored once
and conversion is performed only by the RECA converter.

## Attribution requirements

Preserve Apache-2.0 license and required notices for copied or redistributed
client code. For `SELECTIVE_COPY`, record source paths, pinned Commit and local
modifications in source research and third-party notices.

## Update strategy

Track the client and server as a compatibility pair. If selective code remains
small, review upstream transport fixes periodically rather than mirroring the
whole repository.
