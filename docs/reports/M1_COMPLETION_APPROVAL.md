# M1 Completion Approval

Project: `RECA 0.1 Competition Edition`

Decision: `APPROVED FOR M1 COMPLETION`

Approved by: Project Owner

Approval date: 2026-08-01

## Approved Implementation Scope

- ResearchProject and ProjectMember;
- project authorization and isolation;
- Artifact and ArtifactRelation;
- Approval foundation and append-only AuditLog;
- Job, ProcessingRun, idempotency, and SSE foundation;
- Git-managed Prompt manifest;
- ModelInvocation persistence and requested/max/effective data-access governance;
- M1 frontend integration through the generated-client and ViewModel boundary.

M1 does not implement ResearchQuestion, LiteratureRecord, OpenAlex/PyAlex or
GROBID business workflows, DatasetVersion/CleaningPlan, formal model-provider
execution, Agents SDK, ResearchOrchestrator, or other M2, M4, or M8 capability.

## Acceptance Evidence

```text
Migration head: 0007_model_invocation_governance
Fresh migration: PASS
Repeat upgrade: PASS
Database tests: 139 passed
Backend no-database tests: 43 passed
Frontend tests: 13 passed
M0 clean-room: PASS
Exit code: 0
Evidence: D:\Temp\User\reca-m0-acceptance-20260801-033854
Final pre-commit rerun: D:\Temp\User\reca-m0-acceptance-20260801-093426
Final standard M0 entry rerun: D:\Temp\User\reca-m0-acceptance-20260801-093849
Requirement IDs: 181 -> 181
Open M1 Exit-Gate blockers: 0
```

Ruff, Mypy, frontend format/lint/build, generated-client consistency,
production-mock guard, project isolation, Artifact immutability, Approval
history, Job retry/cancel/SSE, Worker, Storage, security scans, and the six M0
required-CI-equivalent local gates passed before this approval was recorded.

## Accepted Deferred Issues

The Project Owner accepts the following issues as non-blocking P0-Full work.
They remain `OPEN` in the M1 Issue Register and are not represented as resolved:

- `M1-ISSUE-0001`: Project delete second-confirmation contract;
- `M1-ISSUE-0002`: broader superuser override transport;
- `M1-ISSUE-0004`: configurable Artifact upload/download TTL;
- `M1-ISSUE-0007`: configurable SSE retention and heartbeat.

Their documented disabled behavior, authorization restrictions, and bounded M1
defaults remain in force. This approval does not expand M1 into P0-Full.

## Approval Effect

```text
M1 implementation: APPROVED
M1 local Exit Gate: PASS
M0 clean-room: PASS
M1 completion finalization: AUTHORIZED
```

This approval does not claim that the four deferred issues are resolved and does
not state that M2, M4, or M8 has started. M2 and M4 production development may
begin only after required remote CI passes, the approved M1 implementation is
merged into `origin/main`, and the immutable `m1-complete` baseline is recorded.
