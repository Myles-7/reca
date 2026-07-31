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

ARS-Codex is not listed as incorporated content because this documentation task copied no ARS-Codex Prompt, code, script, test or other asset. Its research and reuse decision remains recorded in the corresponding source-research document and ADR.

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
| GROBID | <https://github.com/grobidOrg/grobid> | image `lfoppiano/grobid:0.8.2` | `INDEPENDENT_SERVICE` | `ALREADY_INTEGRATED` | `docker-compose.yml`; M0 health integration only |
| TanStack Table | <https://github.com/TanStack/table> | `@tanstack/react-table@8.21.3` | `DIRECT_DEPENDENCY` | `ALREADY_INTEGRATED` | `frontend/package.json` and `bun.lock`; feature adoption remains milestone-scoped |

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

## M0-02 Compose infrastructure images

| Image | Fixed version | License verification status | RECA usage |
| --- | --- | --- | --- |
| `pgvector/pgvector` | `0.8.2-pg17` | Verified: PostgreSQL License plus pgvector MIT | PostgreSQL with the `vector` extension installed during empty-volume initialization. |
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
| PyAlex | `875c708cbb6e449feebc46d2a7a26af8ed8b2fdd` | MIT | `DIRECT_DEPENDENCY_WITH_PROVIDER` | `PLANNED` | None |
| grobid-client-python | `161e0f45189c8592b2e2c58e9638cc6218bc75fb` | Apache-2.0 | `SELECTIVE_VENDOR` | `RESEARCHED` | None; experiment required |
| PDF.js | `a80897dc9a2eb80c474717b683a4153f5b628ac7` | Apache-2.0 | `DIRECT_DEPENDENCY` | `PLANNED` | None |
| PaperQA2 | `d7675d7b7eddeb3535e8c260399c5bbeeb818c50` | Apache-2.0 | `SELECTIVE_VENDOR` | `RESEARCHED` | None; experiment required |
| ASReview | `d3e863c94e1945ace7848b6ca5bcf2fb1eecbdb5` | Apache-2.0 | `DIRECT_DEPENDENCY_WITH_PROVIDER` | `RESEARCHED` | None; experiment required |
| Pandera | `85cc2a16b2110d4c4b8cc7f956aab94bc53716f6` | MIT | `DIRECT_DEPENDENCY` | `PLANNED` | None |
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
