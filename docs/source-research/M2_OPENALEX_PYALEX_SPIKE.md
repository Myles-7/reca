# M2 OpenAlex / PyAlex Spike

Document version: `1.0.0`

Stage: `M2-5`

Executed: 2026-08-01 (Asia/Shanghai)

## Inputs

- PyAlex release: `0.21`
- Upstream tag: `v0.21`
- Upstream Commit: `875c708cbb6e449feebc46d2a7a26af8ed8b2fdd`
- PyAlex license: MIT
- OpenAlex endpoint: `https://api.openalex.org/works`
- Recorded fixture: `backend/tests/fixtures/openalex/works_recorded.json`

The tag Commit, research Commit and upstream `main` Commit were identical when
the spike ran. The upstream package metadata declares Python `>=3.8` and runtime
dependencies on `requests` and `urllib3`.

## Comparison

The live comparison used one Works keyword query with publication-date,
language and work-type filters, a two-record page and explicit cursor traversal.

| Check | PyAlex 0.21 | Direct HTTP | Result |
| --- | --- | --- | --- |
| Query and nested filter encoding | `Works.search/filter/select` | Explicit query parameters | Equivalent request and first Work ID |
| Cursor page 1 | `get(per_page=2, cursor="*")` | `per-page=2&cursor=*` | Both returned two Works and `next_cursor` |
| Cursor page 2 | `Paginator` can advance internally | Caller supplies returned cursor | Direct request returned a distinct second page |
| Timeout | No timeout is passed by `BaseOpenAlex._get_from_url` | Explicit connect/read timeout | Direct controlled transport required |
| Retry / 429 | Global retry settings and internal `requests.Session` | Per-provider bounded policy | RECA transport is easier to bound and test |
| Response objects | Dict-like `pyalex.api.Work` | Plain JSON | Both require RECA Schema conversion |
| Offline replay | No built-in reviewed recording boundary | Transport substitution | RECA Recorded transport required |

The live direct request returned HTTP 200 in approximately 2.7 seconds. Two
cursor pages returned two records each. PyAlex and direct HTTP returned the same
first Work ID for the equivalent query. The forced timeout, offline, 429 retry,
terminal 429 and malformed JSON cases are deterministic `httpx.MockTransport`
tests; no production endpoint or external rate limit was intentionally abused.

## Frozen Boundary

Adopt `DIRECT_DEPENDENCY_WITH_PROVIDER` with this boundary:

```text
RECA LiteratureQueryPlanDTO
-> PyAlex 0.21 query/filter/select encoding only
-> RECA-owned httpx transport with explicit timeout and bounded retry
-> OpenAlex JSON Schema validation
-> RECA LiteratureRecordDTO + raw response snapshot/hash
```

PyAlex network calls, paginator sessions and `OpenAlexEntity` objects do not
cross the Provider boundary. The configured OpenAlex base URL, API key and
contact email remain backend-only. Recorded mode is selected explicitly by the
caller and returns `degraded=true` plus a user-visible limitation; it is never
reported as live data.

## Normalization

Provider normalization version is `openalex-work-v1`. It covers OpenAlex Work
ID, DOI, title, publication date/year, authors and institutions, primary source,
abstract inverted index, topics, open-access state and candidate locations. The
full reviewed response remains a JSON snapshot with a canonical SHA-256 hash.
Unexpected extra OpenAlex fields are ignored by the stable DTO conversion, while
missing required response structure or invalid required Work fields fail closed
as `SCHEMA_CHANGED` without returning partial candidates.

## License And Rights

PyAlex 0.21 is MIT licensed. OpenAlex's official developer documentation states
that the complete OpenAlex dataset is available under CC0. API authentication,
pricing and service terms remain operational constraints, and CC0 metadata does
not grant rights to linked publisher PDFs, TEI or other full text. No upstream
source file is copied or modified; attribution is recorded in
`THIRD_PARTY_NOTICES.md`, the package manifest and lockfile. Candidate URLs are
not permission or evidence truth.

## Limitations

- This slice does not create `LiteratureSearchRun`, `LiteratureRecord`, cache or
  public API objects.
- Search Service selection, persistence, DOI deduplication and cache ownership
  remain later M2 slices.
- Provider retries only GET requests and are bounded; there is no unbounded
  pagination or automatic fallback.
- The committed recording is sanitized and contains synthetic author identity,
  identifiers and URLs. It proves replay and normalization behavior, not current
  OpenAlex availability.
