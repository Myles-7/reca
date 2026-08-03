import { expect, test } from "@playwright/test"

import type {
  ApprovalPublic,
  ArtifactPublic,
  JobPublic,
  ProjectMemberPublic,
  ProjectOverviewPublic,
  ProjectPublic,
} from "../src/api/adapter"
import {
  mapApproval,
  mapArtifact,
  mapArtifactList,
  mapJob,
  mapMembers,
  mapOverview,
  mapProject,
} from "../src/features/projects/mappers"

const M1_CONTRACT_MOCK = {
  overview: {
    project_id: "project-1",
    current_stage: "INTENT",
    module_availability: {
      literature: "NOT_AVAILABLE",
      dataset: "NOT_AVAILABLE",
      analysis: "DEGRADED",
    },
    current_research_question: null,
    foundation_counts: {
      members: 2,
      artifacts: 0,
      jobs_active: 0,
      approvals_pending: 0,
      audit_events: 3,
    },
    counts: { literature_total: 99, datasets: 88, analysis_runs: 4 },
    pending_actions: [],
    evidence_completeness: null,
    recent_activity: [],
  } satisfies ProjectOverviewPublic,
  members: [
    {
      id: "member-1",
      project_id: "project-1",
      user: { id: "user-1", email: "owner@example.com", full_name: "Owner" },
      role: "OWNER",
      joined_at: "2026-08-01T00:00:00Z",
      removed_at: null,
      allowed_actions: ["project.manage_members", "artifact.upload"],
    },
    {
      id: "member-2",
      project_id: "project-1",
      user: { id: "user-2", email: "viewer@example.com", full_name: "Viewer" },
      role: "VIEWER",
      joined_at: "2026-08-01T00:00:00Z",
      removed_at: null,
      allowed_actions: [],
    },
  ] satisfies ProjectMemberPublic[],
}

test("M2+ unavailable capabilities never expose misleading zero or counts", () => {
  const overview = mapOverview(M1_CONTRACT_MOCK.overview)
  expect(
    overview.capabilities.find((item) => item.key === "literature")?.value,
  ).toBeNull()
  expect(
    overview.capabilities.find((item) => item.key === "dataset")?.value,
  ).toBeNull()
  expect(
    overview.capabilities.find((item) => item.key === "analysis")?.value,
  ).toBeNull()
  expect(overview.researchQuestion).toBeNull()
  expect(overview.evidenceCompleteness).toBeNull()
  expect(
    overview.capabilities.find((item) => item.key === "analysis")?.tone,
  ).toBe("degraded")
})

test("approval pending and stale states remain server-derived projections", () => {
  const approval = {
    id: "approval-1",
    project_id: "project-1",
    approval_type: "RESEARCH_QUESTION_CONFIRMATION",
    target_object_type: "ResearchQuestion",
    target_object_id: "question-1",
    requester: { type: "USER", id: "user-1" },
    requested_at: "2026-08-01T00:00:00Z",
    status: "PENDING",
    decision: null,
    payload_hash: "a".repeat(64),
    payload_snapshot: null,
    impact_summary: null,
    expires_at: null,
    supersedes_approval_id: null,
    items: [],
    allowed_actions: ["approval.approve"],
    created_at: "2026-08-01T00:00:00Z",
  } satisfies ApprovalPublic
  expect(mapApproval(approval).stale).toBe(false)
  expect(mapApproval(approval).allowedActions.has("approval.approve")).toBe(
    true,
  )
  expect(mapApproval({ ...approval, status: "SUPERSEDED" }).stale).toBe(true)
  const unknown = mapApproval({
    ...approval,
    status: "FUTURE_APPROVAL_STATE",
  })
  expect(unknown.tone).toBe("degraded")
  expect(unknown.allowedActions.size).toBe(0)
})

test("workspace permissions come only from formal envelope actions", () => {
  const owner = mapMembers(M1_CONTRACT_MOCK.members, "user-1", [
    "project.manage_members",
    "artifact.upload",
  ])
  const viewer = mapMembers(M1_CONTRACT_MOCK.members, "user-2", [])
  const unknown = mapMembers(M1_CONTRACT_MOCK.members, "user-1", null)
  expect(owner.permissions.permissionsKnown).toBe(true)
  expect(owner.permissions.canManageMembers).toBe(true)
  expect(owner.permissions.canUploadArtifact).toBe(true)
  expect(viewer.permissions.canManageMembers).toBe(false)
  expect(viewer.permissions.canUploadArtifact).toBe(false)
  expect(unknown.permissions.permissionsKnown).toBe(false)
  expect(unknown.permissions.canManageMembers).toBe(false)
})

test("project and Artifact writes require known status and formal actions", () => {
  const project = {
    id: "project-1",
    owner_id: "user-1",
    name: "Projection test",
    description: null,
    discipline: null,
    research_direction: null,
    project_type: "RESEARCH",
    current_stage: "INTENT",
    status: "ACTIVE",
    expected_completion_date: null,
    resource_constraints: null,
    ethical_constraints: null,
    lock_version: 1,
    created_at: "2026-08-01T00:00:00Z",
    updated_at: "2026-08-01T00:00:00Z",
    permissions: { can_update: true, can_delete: true },
    allowed_actions: ["project.read", "project.update", "project.delete"],
  } satisfies ProjectPublic
  expect(mapProject(project)).toMatchObject({
    knownStatus: true,
    permissionsKnown: true,
    canUpdate: true,
    canDelete: true,
  })
  expect(
    mapProject({
      ...project,
      status: "FUTURE_PROJECT_STATE" as ProjectPublic["status"],
    }),
  ).toMatchObject({ knownStatus: false, canUpdate: false, canDelete: false })

  const artifact = {
    id: "artifact-1",
    project_id: "project-1",
    artifact_type: "OTHER",
    filename: "record.bin",
    original_filename: "record.bin",
    mime_type: "application/octet-stream",
    size_bytes: 10,
    sha256: "a".repeat(64),
    source_artifact_id: null,
    is_original: true,
    is_immutable: true,
    status: "AVAILABLE",
    created_by: "user-1",
    created_at: "2026-08-01T00:00:00Z",
    deleted_at: null,
    allowed_actions: ["artifact.download"],
  } satisfies ArtifactPublic
  expect(mapArtifactList([artifact], ["artifact.upload"])).toMatchObject({
    permissionsKnown: true,
    canUpload: true,
  })
  expect(mapArtifactList([artifact], null)).toMatchObject({
    permissionsKnown: false,
    canUpload: false,
  })
})

test("unknown artifact and job states degrade without dangerous actions", () => {
  const artifact = {
    id: "artifact-1",
    project_id: "project-1",
    artifact_type: "OTHER",
    filename: "future.bin",
    original_filename: "future.bin",
    mime_type: "application/octet-stream",
    size_bytes: 10,
    sha256: "a".repeat(64),
    source_artifact_id: null,
    is_original: true,
    is_immutable: true,
    status: "FUTURE_ARTIFACT_STATE",
    created_by: "user-1",
    created_at: "2026-08-01T00:00:00Z",
    deleted_at: null,
    allowed_actions: ["artifact.download"],
  } as unknown as ArtifactPublic
  const job = {
    id: "job-1",
    project_id: "project-1",
    task_type: "DOCUMENT_PARSE",
    resource_type: "Artifact",
    resource_id: "artifact-1",
    status: "FUTURE_JOB_STATE",
    progress_percent: 50,
    current_step: null,
    total_steps: null,
    completed_steps: null,
    retry_count: 1,
    max_retries: 3,
    retryable: true,
    current_processing_run_id: null,
    created_at: "2026-08-01T00:00:00Z",
    started_at: null,
    completed_at: null,
    error: null,
    result: null,
  } as unknown as JobPublic

  expect(mapArtifact(artifact)).toMatchObject({
    tone: "warning",
    canDownload: false,
  })
  expect(mapJob(job)).toMatchObject({
    tone: "degraded",
    active: false,
    retryable: false,
  })
})
