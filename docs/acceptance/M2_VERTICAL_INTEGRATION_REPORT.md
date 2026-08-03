# RECA M2 Vertical Integration Report

This report records M2-10 integration evidence. It is not a product authority
and does not replace the M2 milestone, formal child contracts, or Issue
Register. `PASS` means the named path was executed with the stated evidence;
`NOT RUN` is not treated as success. Recorded, cached, degraded, and Live paths
remain explicitly distinct.

## Baseline

```text
Stage: M2-10
Branch: feat/m2-research-literature
Implementation HEAD: 87e0f4ae27448b422b49c6354a188925a51e5cd7
M1 baseline tag: m1-complete
Migration head: 0012_document_upload
Acceptance date: 2026-08-03 (Asia/Shanghai), Stage E fresh-checkout refresh
```

M2-10 added no migration. Stage 9 subsequently activated and vertically tested
the Open Design pages through the accepted M2 domain, API, Adapter, Worker,
Artifact, Approval, Audit, generated-client, mapper, and Container boundaries.

## Vertical Chain

```text
research idea
-> RECORDED structured candidate Artifact
-> explicit user-created version
-> Approval-backed confirmation
-> QueryPlan
-> RECORDED OpenAlex/PyAlex search
-> cached search reuse
-> candidate import and DOI deduplication
-> PDF upload and immutable Artifact binding
-> RECORDED GROBID TEI conversion
-> stable DocumentPage text and parse status
```

## Result Matrix

| Capability | Result | Execution path | Evidence and limitation |
| --- | --- | --- | --- |
| Alembic upgrade through `0012` | PASS | Real PostgreSQL | Full backend acceptance ran against the migrated database; M2-10 adds no migration. |
| Research idea creation API | PASS | Real API and database | Project-scoped ResearchQuestion and first version were persisted. |
| Structured candidate | PASS | RECORDED, degraded | Governed Scoping Job produced a Schema-valid immutable MODEL_OUTPUT Artifact; it did not directly change domain state. |
| User edit and new version | PASS | Real API and database | Candidate fields were explicitly submitted by the user as a new version. |
| Approval confirmation | PASS | Real API and database | Existing Approvals API confirmed the ready version; no parallel confirmation endpoint was added. |
| QueryPlan | PASS | Real API and database | Confirmed-version reference, Chinese and English terms, boolean query, and filters were persisted. |
| Literature search | PASS | RECORDED OpenAlex/PyAlex, degraded | Registered Worker handler produced one candidate with Recorded provenance; it is not represented as Live retrieval. |
| Search cache reuse | PASS | Cache of RECORDED result, degraded | Second identical run reports `cache_hit=true` and its source run; original degraded provenance remains visible. |
| Candidate import | PASS | Real API and database | Explicit selection created a formal LiteratureRecord separate from the search candidate. |
| DOI import and deduplication | PASS | Real API and database | Importing the same DOI returned the existing project-scoped LiteratureRecord. |
| PDF upload and Artifact binding | PASS | Real generated PDF and test object storage | PDF validation, SHA-256, original immutable Artifact, Document, and LiteratureRecord link were exercised. |
| GROBID conversion | PASS | RECORDED TEI, degraded acceptance path | Registered parse Worker stored and converted fixed TEI with stable pages; this row is not Live GROBID evidence. |
| pypdf fallback | PASS | Deterministic fallback test, LOW confidence and degraded | Focused test verifies fallback behavior without fabricated sections or coordinates. |
| Page text and parse status | PASS | Real database | Two stable DocumentPage rows and `COMPLETED` / `GROBID` / HIGH projections were verified. |
| Cross-project no-disclosure | PASS | Real API and database | Outsider reads for version, plan, search, literature, document, and page return `404 RESOURCE_NOT_FOUND`. |
| Worker handler integration | PASS | Real Job claim, ProcessingRun, registered handler, completion | Scoping, search, and parse handlers executed through Job lifecycle services. |
| Separate Celery broker/process delivery | NOT RUN | None | Handler integration is covered, but independent Celery process delivery was not executed. |
| Frontend generated client and mapper contract | PASS | Playwright contract tests | Loadable, mapper, permissions, Recorded/degraded, unknown-state, and event projections are covered. |
| Production Open Design vertical page | PASS | Production browser, real API/database/object storage and registered Worker handlers | Stage 9 passed QueryPlan, Literature, and Document navigation, server-ID routing, `searchRunId`/`jobId` refresh recovery, cache provenance, immutable upload, parse completion, and DocumentPage text without network interception. |
| Live OpenAlex compatibility smoke | PASS | LIVE external service | Opt-in test returned one real Work with `transport_mode=LIVE` and `degraded=false`. This is compatibility evidence, not deterministic scientific acceptance. |
| Live GROBID compatibility smoke | PASS | LIVE local service | Opt-in test parsed a real generated PDF and returned TEI plus a version. |
| GROBID Compose readiness | PASS | Real container | Recreated pinned GROBID container reached `healthy` with the Bash TCP probe. Functional parsing remains separately tested. |

## Verification

```text
M2 vertical API/database/Worker integration: 1 passed
Vertical GROBID plus pypdf fallback focus: 2 passed
Full backend suite: 248 passed, 2 opt-in Live tests skipped
Clean-room no-database suite: 73 passed, 2 skipped
Live OpenAlex smoke, explicitly enabled: 1 passed
Live GROBID smoke, explicitly enabled: 1 passed
Frontend Playwright suite: 114 passed
Stage 9 production vertical browser: 1 passed
Clean-room Playwright suite: 114 passed
Frontend production build: PASS
UI ownership boundary guard: PASS
Production mock/fixture guard: PASS
Integration Ruff: PASS
Strict Mypy (80 source files): PASS
Alembic metadata check: PASS
```

The two default skips are the opt-in Live OpenAlex and Live GROBID tests. They
were also run separately with their environment gates enabled and passed. Mock
success is not used as business acceptance anywhere in this report.

## API, Migration, and Security

- API contract coverage spans ResearchQuestion versions, existing Approval,
  QueryPlan, search runs/results, Literature import/DOI, Document upload/parse,
  and page reads using the unified M1 envelope and project authorization.
- M2-10 introduces no database migration; the tested head remains
  `0012_document_upload`.
- Cross-project identifiers fail closed with no-disclosure `404` responses.
- Recorded Scoping, OpenAlex, and GROBID inputs remain explicitly marked and do
  not impersonate Live service results.
- Frontend permissions come from explicit server projections and unknown states
  remain disabled. Production Routes inject Open Design-owned views through the
  frozen Containers; fixtures are not production data sources.

## Issues and Exit Status

- `M2-ISSUE-0011` is RESOLVED: the unsupported GROBID `curl` healthcheck was
  replaced by an image-supported Bash TCP probe and revalidated with Live parse.
- `M2-ISSUE-0001` is RESOLVED: detached fresh checkout of implementation SHA
  `87e0f4ae27448b422b49c6354a188925a51e5cd7` passed Prompt LF/hash,
  clean-room, and this production vertical.
- `M2-ISSUE-0010` is RESOLVED: route activation, browser vertical, full
  Playwright, and clean-room requirements pass.
- The remaining OPEN `M2-ISSUE-0008` is LOW and non-blocking; its exact scope
  remains governed by [M2_ISSUE_REGISTER.md](./M2_ISSUE_REGISTER.md). The M2
  Exit Gate is PASS.

M2 production vertical integration is PASS within the explicit Recorded, cache,
degraded, and Live boundaries above. Separate Celery-process delivery remains
NOT RUN and is not represented as handler-lifecycle success.
