# Third-Party Notices

## Full Stack FastAPI Template

- Upstream project: Full Stack FastAPI Template
- Upstream repository: https://github.com/fastapi/full-stack-fastapi-template
- Pinned commit: c9e70d65c74f7adda417fc8de0757207ff77514c
- Nearest release tag: 0.10.0
- Commit relation: 186 commits after 0.10.0
- License: MIT
- Import date: 2026-07-29
- Import method: Controlled source integration from a pinned local snapshot
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
