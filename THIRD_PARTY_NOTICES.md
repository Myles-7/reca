# Third-Party Notices

## Registration template

Use this template when a dependency, independent service, Fork, Vendor, Git Submodule or selective copy is actually incorporated. Do not create an attribution entry from research intent alone.

```text
Project:
Repository:
Upstream Commit/Tag:
License:
License file:
Integration mode:
Status:
Copied paths:
Modified paths:
Modification summary:
Attribution location:
Special restrictions:
Commercialization review:
```

ARS-Codex is not listed as incorporated content because repository inspection at the Phase 11 review baseline found no ARS-Codex Prompt, code, script, test or other asset. This review adds no such content. Its research and reuse decision remains recorded in the corresponding source-research document and ADR.

`Status` is restricted to the following vocabulary:

```text
ALREADY_INTEGRATED
RESEARCHED
PLANNED
VENDORED
SELECTIVELY_COPIED
DIRECT_DEPENDENCY
INDEPENDENT_SERVICE
```

Use `ALREADY_INTEGRATED` for the incorporation index when repository evidence exists, and use the more specific incorporation status when a future entry needs to distinguish `VENDORED`, `SELECTIVELY_COPIED`, `DIRECT_DEPENDENCY` or `INDEPENDENT_SERVICE`. `Integration mode` may use the architecture decision vocabulary and is not a status. Research records and recommendations alone remain `RESEARCHED` or `PLANNED`.

## Incorporation status index

`ALREADY_INTEGRATED` means that repository evidence exists for a package,
service, resource or imported source baseline. It does not mean that every
planned RECA business capability for that project is implemented.

| Project | Repository | Adopted Commit/Tag/Version | Integration mode | Status | Evidence |
| --- | --- | --- | --- | --- | --- |
| Full Stack FastAPI Template | <https://github.com/fastapi/full-stack-fastapi-template> | `c9e70d65c74f7adda417fc8de0757207ff77514c` | `SELECTIVE_COPY` / internalized baseline | `ALREADY_INTEGRATED` | Imported source, source record and preserved MIT license |
| Celery | <https://github.com/celery/celery> | `5.5.3` | `DIRECT_DEPENDENCY` | `ALREADY_INTEGRATED` | `backend/pyproject.toml`, `uv.lock`, Worker entrypoint |
| Valkey | <https://github.com/valkey-io/valkey> | image `8.1.7-alpine` | `INDEPENDENT_SERVICE` | `ALREADY_INTEGRATED` | `docker-compose.yml`; M0 service foundation only |
| pgvector | <https://github.com/pgvector/pgvector> | image `0.8.2-pg17` | `INDEPENDENT_SERVICE` | `ALREADY_INTEGRATED` | `docker-compose.yml` and initialization script; M0 extension foundation only |
| GROBID | <https://github.com/grobidOrg/grobid> | image `lfoppiano/grobid:0.8.2`, digest `sha256:cab12863cab26c818479dbcb6a4f09922ed6caeedfbbf59ef957f52d7195a85d` | `INDEPENDENT_SERVICE` | `ALREADY_INTEGRATED` | M2 bounded parsing Adapter, immutable TEI Artifact and RECA Converter |
| TanStack Table | <https://github.com/TanStack/table> | `@tanstack/react-table@8.21.3` | `DIRECT_DEPENDENCY` | `ALREADY_INTEGRATED` | `frontend/package.json` and `bun.lock`; feature adoption remains milestone-scoped |
| PyAlex | <https://github.com/J535D165/pyalex> | `0.21` / `v0.21` / `875c708cbb6e449feebc46d2a7a26af8ed8b2fdd` | `DIRECT_DEPENDENCY_WITH_PROVIDER` | `DIRECT_DEPENDENCY` | `backend/pyproject.toml`, `uv.lock`, Provider and Recorded tests |
| pypdf | <https://github.com/py-pdf/pypdf> | `6.14.2` | `DIRECT_DEPENDENCY` | `DIRECT_DEPENDENCY` | Explicit low-confidence page-text fallback |
| defusedxml | <https://github.com/tiran/defusedxml> | `0.7.1` | `DIRECT_DEPENDENCY` | `DIRECT_DEPENDENCY` | Secure parsing boundary for untrusted GROBID TEI |
| Pandera | <https://github.com/unionai-oss/pandera> | `0.32.1` / `v0.32.1` | `DIRECT_DEPENDENCY` | `DIRECT_DEPENDENCY` | M4 P0 dataframe validation runtime; RECA-owned Run/Issue normalization remains authoritative |
| pandas | <https://github.com/pandas-dev/pandas> | `3.0.5` / `v3.0.5` | `DIRECT_DEPENDENCY` | `DIRECT_DEPENDENCY` | Deterministic in-process CSV/dataframe parsing used behind RECA-owned contracts |
| openpyxl | <https://foss.heptapod.net/openpyxl/openpyxl> | `3.1.5` | `DIRECT_DEPENDENCY` | `DIRECT_DEPENDENCY` | XLSX structure/value reader constrained to read-only, data-only and no-link mode |

## M4 data quality runtime dependencies

- Project: Pandera
- Repository: <https://github.com/unionai-oss/pandera>
- Upstream Commit/Tag: released tag `v0.32.1`; research commit `85cc2a16b2110d4c4b8cc7f956aab94bc53716f6`
- License: MIT
- License file: upstream `LICENSE.txt`; package metadata/registry distribution
- Integration mode: `DIRECT_DEPENDENCY`
- Status: `DIRECT_DEPENDENCY`
- Copied paths: none
- Modified paths: none in upstream source
- Modification summary: Pandera failures are normalized into RECA-owned `DataQualityRun` and `DataQualityIssue`; library-native objects do not enter database or API contracts
- Attribution location: this notice, `backend/pyproject.toml`, `uv.lock`, `docs/source-research/projects/pandera.md` and `docs/decisions/ADR-004-DATA-STATISTICS-STACK.md`
- Special restrictions: the pandas extra is mandatory; validation must use `lazy=True`, bounded failure samples and `inplace=False`; no second P0 validation runtime
- Source of truth: RECA ruleset ID/version/hash, DatasetVersion, Run/Issue and ProcessingRun metadata
- Fallback: fail the quality Job with a stable RECA error; never invent counts or silently switch to AI/GX
- Acceptance tests: Python 3.14 compatibility, lazy failure normalization, input immutability, deterministic ordering, mixed/nullable/custom checks and measured fixture performance
- Upgrade requirement: rerun the M4 Spike, golden normalization tests and dependency audit before changing Pandera, pandas or NumPy resolution
- Commercialization review: normal MIT dependency attribution; RECA root license remains pending
- Reviewed at: 2026-08-04

- Project: pandas
- Repository: <https://github.com/pandas-dev/pandas>
- Upstream Commit/Tag: released tag `v3.0.5`
- License: BSD-3-Clause
- License file: upstream `LICENSE`; package metadata/registry distribution
- Integration mode: `DIRECT_DEPENDENCY`
- Status: `DIRECT_DEPENDENCY`
- Copied paths: none
- Modified paths: none in upstream source
- Modification summary: used only behind RECA parsing, preview, deterministic transformation and Pandera boundaries
- Attribution location: this notice, `backend/pyproject.toml` and `uv.lock`
- Special restrictions: DataFrame objects are process-local implementation details; parsing remains subject to byte/row/column/cell limits
- Fallback: reject the Job with a stable file/data error; never publish a partial DatasetVersion
- Acceptance tests: CSV BOM/delimiter/formula-prefix cases, dtype/mixed-value cases, memory/time bounds and input immutability
- Upgrade requirement: rerun M4 CSV/XLSX golden, Pandera compatibility and performance tests
- Commercialization review: normal BSD-3-Clause attribution; RECA root license remains pending
- Reviewed at: 2026-08-04

- Project: openpyxl
- Repository: <https://foss.heptapod.net/openpyxl/openpyxl>
- Upstream Commit/Tag: released version `3.1.5`
- License: MIT
- License file: upstream `LICENCE.rst`; package metadata/registry distribution
- Integration mode: `DIRECT_DEPENDENCY`
- Status: `DIRECT_DEPENDENCY`
- Copied paths: none
- Modified paths: none in upstream source
- Modification summary: reads XLSX workbook structure and cached values with `read_only=True`, `data_only=True`, `keep_links=False`
- Attribution location: this notice, `backend/pyproject.toml` and `uv.lock`
- Special restrictions: formulas are never executed; external links are never fetched; ZIP ratio, expanded bytes, sheet count, row/column and cell limits are enforced before publication
- Fallback: preserve the original Artifact, fail the pending DatasetVersion and expose a stable parse error without an AVAILABLE partial version
- Acceptance tests: hidden/multiple worksheets, formula and external-reference cells, damaged/oversized/zip-bomb workbooks and measured streaming reads
- Upgrade requirement: rerun the M4 workbook security Spike and golden fixtures before changing versions
- Commercialization review: normal MIT dependency attribution; RECA root license remains pending
- Reviewed at: 2026-08-04

## M2 document parsing dependencies

- GROBID: Apache-2.0 independent service. No GROBID source or model asset is
  copied into RECA. The fixed spike PDF and live TEI are not committed.
- pypdf 6.14.2: BSD-3-Clause direct dependency used only for visibly degraded
  page-level extraction; it does not create sections, coordinates or evidence.

## M3 evidence viewer dependency

- `pdfjs-dist` 6.2.108: Apache-2.0 direct frontend dependency. RECA uses the
  released display API and the matching `pdf.worker.min.mjs` asset only for
  authorized PDF rendering, page navigation and evidence highlighting. PDF.js
  output is never treated as authoritative EvidenceSpan truth. The supported
  fallback is server-provided page text with page-number/context display and no
  synthesized coordinates.
- defusedxml 0.7.1: Python Software Foundation License direct dependency used
  to reject unsafe XML constructs at the TEI conversion boundary.
- grobid-client-python: researched at commit
  `161e0f45189c8592b2e2c58e9638cc6218bc75fb`; not installed and no source copied.

## Full Stack FastAPI Template

- Project: Full Stack FastAPI Template
- Repository: <https://github.com/fastapi/full-stack-fastapi-template>
- Upstream Commit/Tag: `c9e70d65c74f7adda417fc8de0757207ff77514c`; one commit after `0.10.0`
- License: MIT
- License file: upstream `LICENSE`; preserved snapshot below
- Integration mode: `SELECTIVE_COPY`, represented in the master plan as `ALREADY_INTERNALIZED_BASELINE`
- Status: `ALREADY_INTEGRATED`
- Copied paths: controlled initial backend, frontend, deployment and test foundation; exact historical file list is represented by the import snapshot and repository history
- Modified paths: RECA has materially specialized the imported tree across backend, frontend, deployment and test paths
- Modification summary: upstream example business functionality was removed or replaced with RECA-specific M0 foundations
- Attribution location: this notice and `vendor/licenses/full-stack-fastapi-template-LICENSE.txt`
- Special restrictions: do not overwrite the specialized RECA tree with a whole upstream snapshot; local `upstream-lab` is not a runtime dependency
- Commercialization review: normal MIT attribution review; RECA root license remains pending
- Import date: 2026-07-29
- Git history retained in RECA: No

The original upstream license and copyright notice are preserved at:

`vendor/licenses/full-stack-fastapi-template-LICENSE.txt`

The production application must not depend on the local `upstream-lab` directory.

## TanStack Table

- Project: TanStack Table
- Repository: <https://github.com/TanStack/table>
- Upstream Commit/Tag: adopted package `@tanstack/react-table@8.21.3`; research Commit `d66b39f01e23eeb4e2befc7777194104967212d3`
- License: MIT
- License file: upstream `LICENSE`; package metadata/registry distribution
- Integration mode: `DIRECT_DEPENDENCY`
- Status: `ALREADY_INTEGRATED`
- Copied paths: none
- Modified paths: none in upstream source
- Modification summary: package is locked as a frontend dependency; RECA workbench usage remains milestone-scoped
- Attribution location: this notice, package manifest and lockfile
- Special restrictions: table selection and client state do not create RECA approvals or business decisions
- Commercialization review: normal MIT dependency review

## PyAlex

- Project: PyAlex
- Repository: <https://github.com/J535D165/pyalex>
- Upstream Commit/Tag: adopted package `pyalex==0.21`; tag `v0.21` and research Commit `875c708cbb6e449feebc46d2a7a26af8ed8b2fdd`
- License: MIT; Copyright (c) 2022 Jonathan de Bruin
- License file: upstream `LICENSE`; package metadata/registry distribution
- Integration mode: `DIRECT_DEPENDENCY_WITH_PROVIDER`
- Status: `DIRECT_DEPENDENCY`
- Copied paths: none; the Recorded OpenAlex fixture is RECA-authored and sanitized rather than copied PyAlex source
- Modified paths: none in upstream source
- Modification summary: PyAlex is used only to encode Works queries; RECA-owned `httpx` and Recorded transports own timeout, bounded retry, offline behavior and response conversion
- Attribution location: this notice, `backend/pyproject.toml`, `uv.lock` and `docs/source-research/projects/pyalex.md`
- Special restrictions: PyAlex objects cannot enter ORM, API or frontend contracts; OpenAlex documents its complete dataset as CC0, while API service terms and linked full-text rights remain separate reviews
- Source of truth: RECA QueryPlan, Provider DTOs and later Literature Search Service records
- Fallback: explicit sanitized Recorded OpenAlex response; never reported as live
- Acceptance tests: `backend/tests/adapters/test_literature.py`
- Commercialization review: normal MIT dependency attribution; OpenAlex service/data rights remain separate; RECA root license remains pending
- Reviewed at: 2026-08-01

## M0-02 Compose infrastructure images

| Image | Fixed version | License verification status | RECA usage |
| --- | --- | --- | --- |
| `pgvector/pgvector` | `0.8.2-pg17` | Verified: PostgreSQL License | PostgreSQL with the `vector` extension installed during empty-volume initialization. |
| `valkey/valkey` | `8.1.7-alpine` | Verified: BSD-3-Clause | Internal cache and future task-broker persistence foundation. |
| `minio/minio` | `RELEASE.2025-04-22T22-12-26Z` | Verified: AGPL-3.0-only; deployment use requires project review before distribution | Internal S3-compatible object-storage foundation. |
| `lfoppiano/grobid` | `0.8.2` | Verified: Apache-2.0 upstream GROBID; image packaging provenance recorded | Internal scholarly-document processing service foundation; no parsing workflow is enabled in M0-02. |
| `python` | `3.14.3-slim-bookworm` | Verified: Python Software Foundation License | API container base image. |
| `ghcr.io/astral-sh/uv` | `0.9.26` | Verified: MIT/Apache-2.0 | API dependency installation during container build. |
| `oven/bun` | `1.2.22` | Verified: MIT | Frontend build and preview container base image. |

Image digests are intentionally not recorded because this task validates the
published tags at build time; the fixed tags must not be replaced with `latest`.

## M0-05 worker dependencies

| Dependency | Fixed version | License verification status | RECA usage |
| --- | --- | --- | --- |
| `celery[redis]` | `5.5.3` | Verified: BSD-3-Clause / New BSD | The sole controlled task-worker runtime; M0 registers only `reca.health_ping`. |
| `redis` | `5.2.1` | Verified: MIT | Celery's Redis-compatible transport for the existing Valkey broker and short-lived task result backend. |

Celery is necessary because the approved architecture specifies a Celery worker.
The existing Valkey service is the compatible broker alternative; no additional
queue service is introduced. The Redis transport adds a small pure-Python client
dependency, while Celery brings its documented task-queue dependency set. Neither
package is used to store RECA business facts.

## M0-07 CI supply-chain tooling

| Dependency | Fixed version | License verification status | RECA usage |
| --- | --- | --- | --- |
| `pip-audit` | `2.9.0` | Verified: Apache-2.0 | Locked CI-only Python dependency vulnerability audit. |

`pip-audit` makes Python vulnerability scanning reproducible. The alternative
is a hosted external scanner; the locked local CLI avoids a provider integration.
It adds only CI/development audit tooling and transitive metadata libraries, not
application or container runtime dependencies.

## Researched or planned projects not incorporated

The following rows are planning metadata, not dependency, service, Vendor,
Submodule, resource-copy or runtime claims. No license snapshot is added for
these projects by this documentation task.

| Project | Research Commit | License | Recommended mode | Status | Incorporation evidence |
| --- | --- | --- | --- | --- | --- |
| pgvector-python | `60739dfd6cb9d674f32afa4184d43e6aff9dfbcf` | MIT | `DIRECT_DEPENDENCY` | `PLANNED` | None |
| grobid-client-python | `161e0f45189c8592b2e2c58e9638cc6218bc75fb` | Apache-2.0 | `SELECTIVE_VENDOR` | `RESEARCHED` | None; experiment required |
| PDF.js | `a80897dc9a2eb80c474717b683a4153f5b628ac7` | Apache-2.0 | `DIRECT_DEPENDENCY` | `ADOPTED` | `pdfjs-dist` 6.2.108 in `frontend/package.json` and `bun.lock`; matching worker loaded from the package URL |
| PaperQA2 | `d7675d7b7eddeb3535e8c260399c5bbeeb818c50` | Apache-2.0 | `SELECTIVE_VENDOR` | `RESEARCHED` | None; experiment required |
| ASReview | `d3e863c94e1945ace7848b6ca5bcf2fb1eecbdb5` | Apache-2.0 | `DIRECT_DEPENDENCY_WITH_PROVIDER` | `RESEARCHED` | None; experiment required |
| SciPy | `420a778219f6db170f0fda8dcda4add8a32fd1d6` | BSD-3-Clause plus bundled licenses | `DIRECT_DEPENDENCY` | `PLANNED` | None |
| statsmodels | `d3187f844d196de1760829820a7c872a6d6ebb1d` | BSD-3-Clause | `DIRECT_DEPENDENCY` | `PLANNED` | None |
| Matplotlib | `faf5d100aed23d3271245c2e800ea47f86dd858b` | Matplotlib license plus bundled licenses/fonts | `DIRECT_DEPENDENCY` | `PLANNED` | None |
| DVC | `f74c1c0e709de61f571905802bc0c75035dc6ef2` | Apache-2.0 | `DEVELOPMENT_ONLY` | `RESEARCHED` | None |
| Great Expectations | `33614cd70a407f8b9589fa2cf5f1cb1d7d0723aa` | Apache-2.0 | `DESIGN_REFERENCE` | `RESEARCHED` | None |
| python-docx | `e45454602b53e8e572b179ccf1c91093ec9f4ed7` | MIT | `DIRECT_DEPENDENCY` | `PLANNED` | None |
| CSL Styles | `1de508b010b2643c8b13b082947f1054bc33357f` | CC BY-SA 3.0; selected file rights require review | `RESOURCE_SNAPSHOT` | `PLANNED` | None; no styles copied |
| citeproc-js | `cc9153c45293af878de08cafddbefe6ea150c380` | CPAL/AGPL metadata conflict unresolved | `DEFERRED` | `RESEARCHED` | None |
| xyflow / React Flow | `360f5b13e2bc6899ea06b4be1a49b068d86926cf` | MIT | `DIRECT_DEPENDENCY` | `PLANNED` | None |
| Zotero | `4ec5ba9c279841b09231db82a61e30bd9e7dc6ef` | AGPL-3.0 plus third-party notices | `DESIGN_REFERENCE` | `RESEARCHED` | None; no source/assets copied |
| Zotero Web Library | `556d0bf6b1b48fa8402a91afa62b15533b713013` | AGPL-3.0 | `DESIGN_REFERENCE` | `RESEARCHED` | None; no source/assets copied |
| OpenAI Agents SDK | `0ffa36840cb812488738f6fc5be3d3a1f51397b7` | MIT | `DIRECT_DEPENDENCY` | `PLANNED` | None; M8 only |
| ARS-Codex | `f8d6b061efe98564a3f554c917fce66dcef6ca54` | CC BY-NC 4.0; file/upstream review required | `SELECTIVE_VENDOR` | `RESEARCHED` | None; `NONCOMMERCIAL_INTENT_DECLARED`, experiment and attribution review required |

The RECA root license remains `PENDING_GOVERNANCE_DECISION`. No future root
license may be used to erase or replace third-party license obligations.
