# RECA M2 Exit Gate Report

This report records the M2-11 Exit Gate result. It is acceptance evidence, not
a product or API authority. `NOT RUN` is not success, and Recorded, cached,
degraded, and Live evidence remain explicitly distinct.

## Result

```text
Exit Gate: FAIL
Milestone status: READY_FOR_FINAL_COMMIT_VERIFICATION
Assessment date: 2026-08-03 (Asia/Shanghai), Stage 9 complete
Branch: feat/m2-research-literature
Baseline HEAD: ac6447c081c881fedb818525871a8bd100410cb5
M1 baseline tag: m1-complete
Migration head: 0012_document_upload
```

M2 cannot yet be marked complete because the final repair commit lacks
commit-scoped clean-checkout evidence. Stage 9 full-suite and production
vertical gates pass. The prior route-absent conclusion was `DOC_STALE`.

## Open Issues

| ID | Severity | Exit impact | Status | Remaining work |
| --- | --- | --- | --- | --- |
| `M2-ISSUE-0001` | HIGH | BLOCKS | OPEN | Create the final repair commit, verify Prompt LF and manifest hashes from a fresh checkout of that exact commit, and record the real commit SHA and clean-room results. |
| `M2-ISSUE-0008` | LOW | NON-BLOCKING | OPEN | `@babel/core <=7.29.0` has a development-only arbitrary file-read advisory. No patched 7.x release is available; a Babel 8 migration is deferred as a separate build-chain upgrade. |

The authoritative details, safe degradation rules, and resolution evidence are
maintained in [M2_ISSUE_REGISTER.md](./M2_ISSUE_REGISTER.md).

## Exit Gate Matrix

| Gate | Result | Evidence |
| --- | --- | --- |
| Ruff | PASS | Complete backend lint gate passed. |
| Strict Mypy | PASS | 80 source files checked successfully. |
| Full backend tests | PASS | 248 passed, 2 opt-in Live tests skipped. |
| Empty database migration | PASS | Clean-room upgrade reached `0012_document_upload`. |
| Repeated migration | PASS | Re-running upgrade at head passed. |
| Alembic metadata consistency | PASS | `alembic check` reported no new upgrade operations. |
| OpenAPI generated consistency | PASS | Checked-in OpenAPI and generated frontend client are consistent. |
| Frontend format | PASS | Format check passed. |
| Frontend lint | PASS | Lint passed. |
| Frontend build | PASS | Production build passed. |
| UI ownership boundary guard | PASS | Pure UI boundaries reject API, query, controller, and container imports. |
| Production mock guard | PASS | Production code does not import typed fixtures or test mocks. |
| Playwright | PASS | 114 tests passed on isolated port 5186. |
| Production Open Design vertical E2E | PASS | Stage 9 deterministic browser flow crossed production Routes, generated client/adapter, real API/database/object storage, Job/Worker, DocumentPage text, and refresh recovery. |
| Compose clean-room | PASS | Isolated build, services, persistence, recovery, database/no-database tests, Playwright, and secret checks passed. |
| Python dependency audit | PASS | No known vulnerabilities reported. |
| Node dependency audit | PASS WITH LOW ADVISORY | Only `M2-ISSUE-0008`; it is development-only and non-blocking. |
| Live OpenAlex compatibility smoke | NOT RUN in Stage 9 | Prior opt-in compatibility evidence remains historical; deterministic Recorded acceptance is the hard gate. |
| Live GROBID compatibility smoke | NOT RUN in Stage 9 | Prior opt-in compatibility evidence remains historical; deterministic Recorded acceptance is the hard gate. |
| Separate Celery broker/process delivery | NOT RUN | Handler lifecycle integration passed; an independent Celery delivery acceptance run was not performed. |

Clean-room evidence run:

```text
reca-m0-acceptance-20260803-073400 (external temporary evidence)
```

## Safety and Contract Outcome

- Project-scoped no-disclosure, DOI-first deduplication, candidate/record
  separation, immutable PDF Artifact binding, stable page numbering, and
  GROBID no-fallback failure behavior passed their focused and complete gates.
- Server-projected `allowed_actions`, generated client, ViewModels, Loadable
  states, mappers, queries, mutations, containers, and typed fixtures are
  present for the M2 frontend boundary.
- Unknown states fail closed and high-risk operations remain disabled.
- No temporary Codex-owned pure UI was created to bypass Open Design ownership.
- No EvidenceSpan, OCR, complete literature matrix, ten-field extraction, or
  M8 Agent orchestration was introduced.

## Decision

The verified backend, migration, provider, document-processing, contract, and
frontend integration layers are acceptable within their stated execution
paths. `M2-ISSUE-0010` is RESOLVED and the production vertical is PASS. The
overall M2 Exit Gate remains FAIL solely until `M2-ISSUE-0001` has genuine
commit-scoped clean-checkout evidence from an authorized final commit.
