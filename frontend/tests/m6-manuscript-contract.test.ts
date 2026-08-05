import { describe, expect, test } from "bun:test"

import {
  type ManuscriptIssuePublic,
  ManuscriptsApi,
  type ManuscriptVersionPublic,
  ProjectsApi,
} from "../src/api/adapter"
import { manuscriptWorkspaceFixtures } from "../src/features/manuscript-workspace/fixtures"
import {
  mapIssue,
  mapVersion,
} from "../src/features/manuscript-workspace/mappers"
import { loadManuscriptWorkspace } from "../src/features/manuscript-workspace/queries"
import { parseManuscriptWorkspaceSearch } from "../src/features/manuscript-workspace/route-contract"

const uuid = "00000000-0000-4000-8000-000000000001"
const hash = "a".repeat(64)

describe("M6 manuscript adapter projections", () => {
  test("unknown version status keeps the raw value and closes actions", () => {
    const value = {
      id: uuid,
      manuscript_id: uuid,
      project_id: uuid,
      version_number: 1,
      parent_version_id: null,
      artifact_id: uuid,
      version_type: "ORIGINAL",
      source_transformation_id: null,
      status: "FUTURE_VERSION_STATE",
      source_hash: hash,
      parse_snapshot: null,
      created_by: null,
      created_at: "2026-08-05T00:00:00Z",
      invalidated_at: null,
      invalidation_reason: null,
      allowed_actions: ["manuscript_version.download"],
    } as unknown as ManuscriptVersionPublic

    const mapped = mapVersion(value)
    expect(mapped.status).toBe("FUTURE_VERSION_STATE")
    expect(mapped.knownStatus).toBeFalse()
    expect(mapped.allowedActions.size).toBe(0)
  })

  test("high-risk issue is never projected as auto-fixable", () => {
    const value = {
      id: uuid,
      project_id: uuid,
      manuscript_check_run_id: uuid,
      manuscript_version_id: uuid,
      issue_type: "SAMPLE_SIZE_MISMATCH",
      severity: "HIGH",
      section_name: null,
      paragraph_index: 1,
      table_index: null,
      locator: { paragraph: 1 },
      original_text: "N = 184",
      normalized_reference: null,
      reason: "Mismatch",
      suggestion: "Review formal evidence",
      finding_hash: hash,
      confidence: "HIGH",
      auto_fixable: true,
      status: "OPEN",
      lock_version: 1,
      decision_reason: null,
      decided_by: null,
      source_model_invocation_id: null,
      created_at: "2026-08-05T00:00:00Z",
      resolved_at: null,
      invalidated_at: null,
      allowed_actions: ["manuscript_issue.accept"],
      evidence: [],
    } as ManuscriptIssuePublic

    expect(mapIssue(value).autoFixable).toBeFalse()
  })
})

test("route parser drops invalid and unknown deep links", () => {
  expect(
    parseManuscriptWorkspaceSearch({
      manuscript: "not-a-uuid",
      version: uuid,
      view: "future-view",
    }),
  ).toEqual({
    manuscript: undefined,
    version: uuid,
    checkRun: undefined,
    issue: undefined,
    transformation: undefined,
    audit: undefined,
    claim: undefined,
    view: undefined,
  })
})

const fixture = (fixtureId: string) => {
  const value = manuscriptWorkspaceFixtures.find(
    (item) => item.id === fixtureId,
  )
  expect(value).toBeDefined()
  if (!value || value.content.state !== "ready")
    throw new Error(`${fixtureId} must be a ready fixture`)
  return value
}

describe("M6 semantic fixture contract", () => {
  test("check lifecycle changes status, progress, retryability and actions", () => {
    const queued = fixture("check-queued").content
    const failed = fixture("check-failed-retryable").content
    if (queued.state !== "ready" || failed.state !== "ready") return
    expect(queued.data.checkRun?.status).toBe("QUEUED")
    expect(queued.data.job?.progress).toBe(0)
    expect(queued.data.capabilities.cancelJob.allowed).toBeTrue()
    expect(failed.data.checkRun?.status).toBe("FAILED")
    expect(failed.data.job?.retryable).toBeTrue()
    expect(failed.data.capabilities.retryJob.allowed).toBeTrue()
  })

  test("evidence and approval fixtures preserve fail-closed facts", () => {
    const denied = fixture("evidence-denied").content
    const stale = fixture("approval-stale").content
    if (denied.state !== "ready" || stale.state !== "ready") return
    expect(denied.data.selectedIssue?.evidence[0].readScope).toBe("DENIED")
    expect(denied.data.selectedIssue?.evidence[0].excerpt).toBeNull()
    expect(stale.data.transformation?.approvalStale).toBeTrue()
    expect(stale.data.capabilities.executeFixPlan.allowed).toBeFalse()
  })

  test("Props fixtures expose independent pending and mutation error states", () => {
    expect(fixture("upload-pending").pendingAction).toBe("upload-manuscript")
    expect(fixture("audit-pending").pendingAction).toBe("start-revision-audit")
    expect(fixture("mutation-conflict").mutationError?.conflict).toBeTrue()
    expect(
      fixture("mutation-retryable-error").mutationError?.retryable,
    ).toBeTrue()
  })

  test("unknown and permissions-unknown fixtures close formal actions", () => {
    const unknown = fixture("unknown-version-status").content
    const permissions = fixture("permissions-unknown").content
    if (unknown.state !== "ready" || permissions.state !== "ready") return
    expect(unknown.data.selectedVersion?.knownStatus).toBeFalse()
    expect(unknown.data.selectedVersion?.allowedActions.size).toBe(0)
    expect(unknown.data.capabilities.startCheck.allowed).toBeFalse()
    expect(permissions.data.permissionsKnown).toBeFalse()
    expect(permissions.data.manuscript).toBeNull()
    expect(
      Object.values(permissions.data.capabilities)
        .filter((value) => typeof value === "object")
        .every((value) => !value.allowed),
    ).toBeTrue()
  })
})

test("project discovery drives no-manuscript and refresh recovery", async () => {
  const originalProject = ProjectsApi.get
  const originalDiscovery = ManuscriptsApi.discover
  let active = false
  ProjectsApi.get = (async () => ({
    data: {
      id: uuid,
      allowed_actions: ["manuscript.upload", "manuscript.read"],
    },
    meta: {},
  })) as typeof ProjectsApi.get
  ManuscriptsApi.discover = (async () => ({
    data: active
      ? {
          state: "ACTIVE",
          current_manuscript: {
            id: uuid,
            project_id: uuid,
            title: "Recovered",
            current_version_id: null,
            status: "ACTIVE",
            lock_version: 1,
            created_by: null,
            created_at: "2026-08-05T00:00:00Z",
            updated_at: "2026-08-05T00:00:00Z",
            invalidated_at: null,
            invalidation_reason: null,
            allowed_actions: ["manuscript.read"],
          },
          current_version: null,
          manuscripts: [],
          versions: [],
        }
      : {
          state: "NONE",
          current_manuscript: null,
          current_version: null,
          manuscripts: [],
          versions: [],
        },
    meta: {},
  })) as typeof ManuscriptsApi.discover
  try {
    const emptyState = await loadManuscriptWorkspace(uuid, {})
    expect(emptyState.discoveryState).toBe("NONE")
    expect(emptyState.manuscript).toBeNull()
    expect(emptyState.capabilities.uploadManuscript.allowed).toBeTrue()
    active = true
    const refreshed = await loadManuscriptWorkspace(uuid, {})
    expect(refreshed.discoveryState).toBe("ACTIVE")
    expect(refreshed.manuscript?.title).toBe("Recovered")
  } finally {
    ProjectsApi.get = originalProject
    ManuscriptsApi.discover = originalDiscovery
  }
})

test("project discovery rejects cross-project data without disclosure", async () => {
  const originalProject = ProjectsApi.get
  const originalDiscovery = ManuscriptsApi.discover
  ProjectsApi.get = (async () => ({
    data: { id: uuid, allowed_actions: ["manuscript.read"] },
    meta: {},
  })) as typeof ProjectsApi.get
  ManuscriptsApi.discover = (async () => ({
    data: {
      state: "ACTIVE",
      current_manuscript: {
        id: uuid,
        project_id: "00000000-0000-4000-8000-000000000099",
        title: "Unrelated",
        current_version_id: null,
        status: "ACTIVE",
        lock_version: 1,
        created_by: null,
        created_at: "2026-08-05T00:00:00Z",
        updated_at: "2026-08-05T00:00:00Z",
        invalidated_at: null,
        invalidation_reason: null,
        allowed_actions: ["manuscript.read"],
      },
      current_version: null,
      manuscripts: [],
      versions: [],
    },
    meta: {},
  })) as typeof ManuscriptsApi.discover
  try {
    await expect(loadManuscriptWorkspace(uuid, {})).rejects.toMatchObject({
      status: 404,
      code: "MANUSCRIPT_WORKSPACE_ROUTE_MISMATCH",
    })
  } finally {
    ProjectsApi.get = originalProject
    ManuscriptsApi.discover = originalDiscovery
  }
})
