# PyAlex source research

Document version: `1.0.0`

Document status: `Conditional Approval`

Research status: `PLANNED`

Last researched: 2026-07-31

Phase summary: [Literature and evidence research](../../reports/OPEN_SOURCE_RESEARCH_PHASE_2_LITERATURE.md)

## Upstream

| Field | Verified value |
| --- | --- |
| Repository | <https://github.com/J535D165/pyalex> |
| Default branch | `main` |
| Pinned research commit | `875c708cbb6e449feebc46d2a7a26af8ed8b2fdd` |
| Latest release/tag | `v0.21` |
| License | MIT |
| License file | `LICENSE` |
| Main language | Python |
| Minimum runtime | Python `>=3.8` |
| Dependency manifest | `pyproject.toml` |
| Runtime dependencies | `requests`, `urllib3` |
| Container/service requirements | Network access to OpenAlex; optional API key and contact email |
| Test framework | Pytest |
| CI workflows | Lint, package tests and package publishing |
| Maintenance status | Active; repository was not archived at the research commit |

## Repository structure

| Path | Purpose |
| --- | --- |
| `pyalex/api.py` | Query construction, pagination, requests, retries and entity wrappers |
| `pyalex/` | OpenAlex entity classes and configuration |
| `tests/` | Query, pagination, configuration and entity behavior tests |
| `README.md` | API examples and supported OpenAlex operations |
| `.github/workflows/` | Lint, package test and release automation |

## Core capabilities

PyAlex exposes OpenAlex Works, Authors, Sources, Institutions, Topics,
Publishers, Funders and related entities. It supports search, nested filters,
OR filters, sorting, field selection, grouping, sampling, autocomplete,
semantic search and both page and cursor pagination.

Responses are dict-like `OpenAlexEntity` objects. That convenience is useful at
the provider edge, but it is not a stable persistence or frontend contract.

## Relevant modules

- `Works` is the primary M2 integration surface.
- Filters and search map naturally from a RECA `QueryPlan`.
- Cursor pagination is preferable for reproducible large result traversal.
- Raw response fields are valuable for provenance and later normalization fixes.
- OpenAlex PDF/TEI locations, when present, are candidate acquisition links, not
  proof that RECA may redistribute or trust the content.

## Dependencies

The runtime dependency surface is small: `requests` and `urllib3`. RECA should
use its existing configuration and secret handling for API identity, and should
not add a second general HTTP policy outside the provider.

## API key, rate limiting and retries

PyAlex sends an API key as a Bearer token and can identify the caller through a
`From` email. Default retries are disabled. Retry status codes can be configured;
the inspected defaults include `429`, `500` and `503`, with a small backoff
factor. RECA must set explicit timeouts, bounded retry counts and observable
rate-limit handling rather than inherit silent defaults.

## Normalization and provenance

RECA should normalize at least OpenAlex IDs, DOI, title, publication date,
authors, source, abstract/inverted abstract, concepts/topics, open-access status
and candidate locations. DOI normalization must remove resolver prefixes,
normalize case conservatively and preserve the source value. Author names and
OpenAlex author IDs remain source assertions, not identity proof.

For every search result, retain provider name, request parameters, retrieval
time, OpenAlex entity ID, raw response or a content-addressed raw snapshot, and
normalization version. A normalized `LiteratureRecord` must remain RECA-owned.

## Tests

Upstream Pytest coverage is useful for query construction and response behavior.
RECA additionally needs:

- Recorded tests for representative OpenAlex responses and pagination;
- Offline tests that perform no network calls;
- rate-limit, timeout, malformed response and partial-page tests;
- DOI/author normalization fixtures;
- replay tests proving the same raw response produces the same normalized DTO.

Recorded fixtures must be reviewed for personal data and API credentials before
commit.

## Operational requirements

- Reachable OpenAlex API and explicit contact identity;
- optional API key kept in backend configuration only;
- bounded pagination, timeout and retry policy;
- raw-response retention with size controls;
- deterministic normalization version;
- provider telemetry that cannot change formal literature decisions.

## RECA current state

OpenAlex is planned for M2 literature retrieval. Current formal documents define
`QueryPlan`, search runs and `LiteratureRecord`, but PyAlex is not an installed
runtime dependency and no production provider is implemented by this research.

## Recommended integration mode

`DIRECT_DEPENDENCY + LIGHTWEIGHT_PROVIDER`

Use PyAlex directly inside a narrow OpenAlex provider. The provider accepts
RECA-owned query DTOs and returns RECA-owned candidate DTOs plus raw provenance.
A broad generic Adapter framework is unnecessary, but PyAlex objects must stop
at the provider boundary.

## What to reuse

- query, filter, grouping and cursor-pagination construction;
- authenticated request support and configurable retry transport;
- entity-specific convenience access at the provider edge;
- upstream query behavior tests as design references.

## What not to reuse

- PyAlex entity objects as ORM fields, API responses or frontend state;
- OpenAlex relevance/order as a final screening decision;
- provider metadata as a validated citation without normalization;
- remote PDF/TEI availability as permission or evidence truth;
- unbounded automatic pagination or retry.

## Domain boundary

The provider mapping is:

```text
QueryPlan
-> OpenAlex provider request
-> PyAlex response
-> raw provider snapshot + normalized candidate DTO
-> LiteratureSearchRun result
-> candidate LiteratureRecord creation through RECA Service rules
```

Search results are candidates. They do not create `EvidenceSpan`, screening
decisions or project membership by themselves.

## Milestone

- M2: OpenAlex provider, recorded/offline tests and candidate normalization.
- M3: use selected literature records as inputs to evidence extraction.

## Risks

- API schema or filter behavior drift;
- rate-limit behavior hidden by convenience calls;
- duplicate works caused by DOI/title normalization differences;
- stale or incomplete author/source metadata;
- raw provider objects leaking into stable contracts;
- license/access assumptions inferred from open-access metadata.

## Validation spike

Implement a disposable provider spike that executes one keyword query, one
nested filter, cursor pagination and a forced `429`. Record and replay responses,
normalize DOI/authors, deduplicate a known duplicate and verify that no PyAlex
class crosses the provider boundary.

## Attribution requirements

Preserve the MIT license and copyright notice if code is distributed. Record the
exact package version and repository Commit when adopted. OpenAlex data and
linked full text require their own source and use review.

## Update strategy

Pin a released PyAlex version, monitor OpenAlex API changes, and replay the
recorded contract suite before upgrades. Provider DTOs insulate RECA from minor
library changes without pretending the upstream API is stable forever.
