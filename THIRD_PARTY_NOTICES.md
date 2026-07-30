# Third-Party Notices

## Registration template

Use this template when a dependency, independent service, Fork, Vendor, Git Submodule or selective copy is actually incorporated. Do not create an attribution entry from research intent alone.

```text
Project:
Repository:
Commit/Tag:
License:
Integration mode:
Copied paths:
Modifications:
Attribution:
Special restrictions:
```

ARS-Codex is not listed as incorporated content because this documentation task copied no ARS-Codex Prompt, code, script, test or other asset. Its research and reuse decision remains recorded in the corresponding source-research document and ADR.

## Full Stack FastAPI Template

- Upstream project: Full Stack FastAPI Template
- Upstream repository: https://github.com/fastapi/full-stack-fastapi-template
- Pinned commit: c9e70d65c74f7adda417fc8de0757207ff77514c
- Nearest release tag: 0.10.0
- Commit relation: 186 commits after 0.10.0
- License: MIT
- Import date: 2026-07-29
- Import method: Controlled source integration from a pinned local snapshot
- Integration mode: `SELECTIVE_COPY`
- Git history retained in RECA: No
- Usage: Initial engineering foundation for RECA
- Planned modifications: Remove upstream example business functionality and replace it with RECA-specific modules

The original upstream license and copyright notice are preserved at:

`vendor/licenses/full-stack-fastapi-template-LICENSE.txt`

The production application must not depend on the local `upstream-lab` directory.

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
