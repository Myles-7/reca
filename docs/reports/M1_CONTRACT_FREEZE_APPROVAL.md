# M1 Contract Freeze Approval

Project: `RECA 0.1 Competition Edition`

Decision: `APPROVED`

Approved by: Project Owner

Approval date: 2026-07-31

## Approved Scope

- M1 Contract Freeze and M1 Contract Amendment completed by the final audit;
- ProjectMember, Artifact, ApprovalRecord, AuditLog, Job, ProcessingRun,
  ModelInvocation, idempotency, Project Overview, and frontend-facing projection
  contracts;
- documentation-only consistency corrections and contract examples.

This approval permits M1 production implementation after this approval is
recorded as a Git baseline. It does not state that M1 has been implemented or
accepted, and it does not authorize M2, M4, or M8 business implementation.

## Stable Identifier Delta

```text
Requirement IDs: 181 -> 181
Requirement IDs added: 0
Requirement IDs removed: 0
Requirement IDs renamed: 0
Acceptance IDs changed: 0
Milestone IDs changed: 0
ADR IDs changed: 0

API path identifiers: 236 -> 242
API path identifiers added: 6
API path identifiers removed: 0
API path identifiers renamed: 0
Formal METHOD + path operations added: 12
Formal METHOD + path operations removed: 0
```

The six added API path identifiers are:

```text
/api/v1/artifact-uploads/{upload_id}/content
/api/v1/projects/{project_id}/artifacts
/api/v1/projects/{project_id}/audit-logs
/api/v1/projects/{project_id}/jobs
/api/v1/projects/{project_id}/members
/api/v1/projects/{project_id}/members/{member_id}
```

The twelve added METHOD + path operations are:

```text
GET    /api/v1/projects/{project_id}/members
POST   /api/v1/projects/{project_id}/members
PATCH  /api/v1/projects/{project_id}/members/{member_id}
DELETE /api/v1/projects/{project_id}/members/{member_id}
GET    /api/v1/projects/{project_id}/artifacts
POST   /api/v1/projects/{project_id}/artifacts/uploads
PUT    /api/v1/artifact-uploads/{upload_id}/content
POST   /api/v1/projects/{project_id}/artifacts/uploads/{upload_id}/complete
GET    /api/v1/artifacts/{artifact_id}
GET    /api/v1/artifacts/{artifact_id}/download
GET    /api/v1/projects/{project_id}/jobs
GET    /api/v1/projects/{project_id}/audit-logs
```

No existing formal API path or operation is removed or renamed.

## Intentional Semantic Amendments

### Project Ownership

Every Project has exactly one active OWNER. The current OWNER cannot be directly
removed, self-removed, or ordinarily demoted. Ownership transfer is explicit and
atomic through the frozen ProjectMember update command: it updates the successor,
the previous owner, `ResearchProject.owner_id`, and the append-only
`PROJECT_OWNERSHIP_TRANSFERRED` AuditLog in one transaction. No successor is
selected implicitly.

### Job Retry

`Job` is one logical asynchronous work item and `ProcessingRun` is one execution
attempt. Retry preserves the same Job, increments `retry_count`, and creates a
new ProcessingRun when the Worker starts the new attempt. This clarifies the
approved baseline, which required a new ProcessingRun but did not freeze whether
the Job identity changed. No formal M1 Job data exists, so migration
compatibility is not applicable.

## Creation And Runtime Boundaries

- ApprovalRecord has no generic create API; the owning domain Service creates it.
- Job has no generic create API; a job-producing domain command Service creates it.
- M1 does not fabricate a FORMAL_APPROVAL consumer.
- ModelInvocation and Prompt governance persistence are in M1.
- Provider integration, Agents SDK, Agent runtime, orchestration, and M2/M4/M8
  business capabilities remain out of scope.

## Change Guard

```text
Production code changed: NO
Migration changed: NO
Dependencies changed: NO
Lockfiles changed: NO
Generated client changed: NO
Docker/Compose changed: NO
CI changed: NO
```

The historical annotated tags `docs-m1-approved` and
`open-design-integration-approved` remain unchanged. The annotated tag
`m1-contract-freeze-approved` marks this exact incremental approval baseline.

## Approval Effect

```text
M1 Contract Freeze: APPROVED
M1 Contract Amendment: APPROVED
M1 production implementation entry: ALLOWED AFTER BASELINE IS RECORDED
M1 implementation status at approval: NOT STARTED
```
