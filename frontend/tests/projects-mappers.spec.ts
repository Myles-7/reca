import { expect, test } from "@playwright/test"

import type {
  ApprovalPublic,
  ProjectMemberPublic,
  ProjectOverviewPublic,
} from "../src/api/adapter"
import {
  mapApproval,
  mapMembers,
  mapOverview,
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
})

test("workspace permissions come only from the current user's projection", () => {
  const owner = mapMembers(M1_CONTRACT_MOCK.members, "user-1")
  const viewer = mapMembers(M1_CONTRACT_MOCK.members, "user-2")
  expect(owner.permissions.canManageMembers).toBe(true)
  expect(owner.permissions.canUploadArtifact).toBe(true)
  expect(viewer.permissions.canManageMembers).toBe(false)
  expect(viewer.permissions.canUploadArtifact).toBe(false)
})
