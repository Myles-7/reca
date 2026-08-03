# RECA M2 Exit Gate Report

This report records the M2-11 Exit Gate result. It is acceptance evidence, not
a product or API authority. `NOT RUN` is not success, and Recorded, cached,
degraded, and Live evidence remain explicitly distinct.

## Result

```text
Exit Gate: PASS
Milestone status: COMPLETION APPROVED
Assessment date: 2026-08-03 (Asia/Shanghai), Stage E complete
Branch: feat/m2-research-literature
Implementation HEAD: ac34ef95a546c71fe9a08bd3e98f4a1b1db115fd
M1 baseline tag: m1-complete
Migration head: 0012_document_upload
```

M2 is complete. The final implementation SHA passed detached fresh-checkout
Prompt LF/hash, clean-room, and production vertical gates. The prior
route-absent conclusion was `DOC_STALE`.

## Open Issues

| ID | Severity | Exit impact | Status | Remaining work |
| --- | --- | --- | --- | --- |
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
| Playwright | PASS | Fresh clean-room passed 114 tests on isolated port 15174. |
| Production Open Design vertical E2E | PASS | Fresh implementation checkout passed 1/1 through production Routes, generated client/adapter, real API/database/object storage, Job/Worker, DocumentPage text, and refresh recovery. |
| Compose clean-room | PASS | Fresh implementation checkout passed isolated build, locked dependency install, services, persistence, recovery, backend tests, Playwright, and secret checks. |
| Python dependency audit | PASS | No known vulnerabilities reported. |
| Node dependency audit | PASS WITH LOW ADVISORY | Only `M2-ISSUE-0008`; it is development-only and non-blocking. |
| Live OpenAlex compatibility smoke | NOT RUN in Stage 9 | Prior opt-in compatibility evidence remains historical; deterministic Recorded acceptance is the hard gate. |
| Live GROBID compatibility smoke | NOT RUN in Stage 9 | Prior opt-in compatibility evidence remains historical; deterministic Recorded acceptance is the hard gate. |
| Separate Celery broker/process delivery | NOT RUN | Handler lifecycle integration passed; an independent Celery delivery acceptance run was not performed. |

Clean-room evidence run:

```text
implementation SHA: ac34ef95a546c71fe9a08bd3e98f4a1b1db115fd
clean-room: reca-m2-stagee-cleanroom-20260803-081709
production vertical: reca-m2-stagee-vertical-20260803-082115
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
frontend integration layers satisfy the M2 Exit Gate. `M2-ISSUE-0001` and
`M2-ISSUE-0010` are RESOLVED; `M2-ISSUE-0008` remains an explicit LOW,
non-blocking deferral. M3 Entry is ALLOWED within the frozen handoff boundary.
