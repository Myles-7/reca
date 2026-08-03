import { expect, type Page, test } from "@playwright/test"

const M1_CONTRACT_MOCK = {
  user: {
    id: "user-1",
    email: "owner@example.com",
    is_active: true,
    is_superuser: false,
    full_name: "Project Owner",
  },
  project: {
    id: "project-1",
    owner_id: "user-1",
    name: "Evidence Review",
    description: "M1 integration workspace",
    discipline: "Medicine",
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
    permissions: { can_update: true, can_delete: false },
    allowed_actions: ["project.read", "project.update"],
  },
}

const meta = { request_id: "request-test", schema_version: "1.0" }
const pagination = { page: 1, page_size: 100, total: 1, total_pages: 1 }

const approvalFixture = {
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
}

type WorkspaceMockOptions = {
  projectCanDelete?: boolean
  lifecycleDelayMs?: number
  memberAllowedActions?: string[]
  memberForbidden?: boolean
  memberPostDelayMs?: number
  includeViewerMember?: boolean
  approvals?: Array<Record<string, unknown>>
  approvalConflict?: boolean
  approvalPostDelayMs?: number
  artifacts?: Array<Record<string, unknown>>
  jobs?: Array<Record<string, unknown>>
}

async function installAuthenticatedMocks(
  page: Page,
  options: WorkspaceMockOptions = {},
) {
  await page.addInitScript(() =>
    localStorage.setItem("access_token", "test-token"),
  )
  const project = {
    ...M1_CONTRACT_MOCK.project,
    permissions: {
      ...M1_CONTRACT_MOCK.project.permissions,
      can_delete:
        options.projectCanDelete ??
        M1_CONTRACT_MOCK.project.permissions.can_delete,
    },
    allowed_actions: [
      "project.read",
      "project.update",
      ...(options.projectCanDelete ? ["project.delete"] : []),
    ],
  }
  const projects = [project]
  await page.route("**/api/v1/**", async (route) => {
    const request = route.request()
    const url = new URL(request.url())
    const path = url.pathname
    if (path === "/api/v1/users/me")
      return route.fulfill({ json: M1_CONTRACT_MOCK.user })
    if (path === "/api/v1/projects" && request.method() === "GET") {
      return route.fulfill({ json: { data: projects, pagination, meta } })
    }
    if (path === "/api/v1/projects" && request.method() === "POST") {
      expect(request.headers()["idempotency-key"]).toBeTruthy()
      const body = request.postDataJSON()
      const created = {
        ...project,
        id: "project-2",
        name: body.name,
      }
      projects.push(created)
      return route.fulfill({ status: 201, json: { data: created, meta } })
    }
    if (path === "/api/v1/projects/project-1") {
      return route.fulfill({ json: { data: project, meta } })
    }
    if (path === "/api/v1/projects/project-1/archive") {
      if (options.lifecycleDelayMs) {
        await new Promise((resolve) =>
          setTimeout(resolve, options.lifecycleDelayMs),
        )
      }
      project.status = "ARCHIVED"
      return route.fulfill({ json: { data: project, meta } })
    }
    if (path.endsWith("/overview")) {
      return route.fulfill({
        json: {
          data: {
            project_id: "project-1",
            current_stage: "INTENT",
            module_availability: {
              research_question: "NOT_AVAILABLE",
              literature: "NOT_AVAILABLE",
              dataset: "NOT_AVAILABLE",
              evidence: "NOT_AVAILABLE",
            },
            current_research_question: null,
            foundation_counts: {
              members: 1,
              artifacts: 0,
              jobs_active: 0,
              approvals_pending: 0,
              audit_events: 1,
            },
            counts: { literature_total: null, datasets: null },
            pending_actions: [],
            evidence_completeness: null,
            recent_activity: [],
          },
          meta,
        },
      })
    }
    if (path.endsWith("/members")) {
      if (options.memberForbidden) {
        return route.fulfill({
          status: 403,
          json: {
            error: {
              code: "PROJECT_ACCESS_DENIED",
              message: "Access denied",
              request_id: "request-members-forbidden",
              retryable: false,
            },
          },
        })
      }
      const owner = {
        id: "member-1",
        project_id: "project-1",
        user: {
          id: "user-1",
          email: "owner@example.com",
          full_name: "Project Owner",
        },
        role: "OWNER",
        joined_at: "2026-08-01T00:00:00Z",
        removed_at: null,
        allowed_actions: options.memberAllowedActions ?? [
          "project.manage_members",
          "artifact.upload",
          "job.retry",
          "job.cancel",
        ],
      }
      const viewer = {
        id: "member-2",
        project_id: "project-1",
        user: {
          id: "user-2",
          email: "viewer@example.com",
          full_name: "Project Viewer",
        },
        role: "VIEWER",
        joined_at: "2026-08-01T00:00:00Z",
        removed_at: null,
        allowed_actions: [],
      }
      if (request.method() === "POST") {
        if (options.memberPostDelayMs) {
          await new Promise((resolve) =>
            setTimeout(resolve, options.memberPostDelayMs),
          )
        }
        return route.fulfill({
          status: 201,
          json: { data: viewer, meta },
        })
      }
      return route.fulfill({
        json: {
          data: options.includeViewerMember ? [owner, viewer] : [owner],
          allowed_actions: options.memberAllowedActions ?? [
            "project.manage_members",
            "artifact.upload",
            "job.retry",
            "job.cancel",
          ],
          pagination,
          meta,
        },
      })
    }
    if (path.endsWith("/artifacts"))
      return route.fulfill({
        json: {
          data: options.artifacts ?? [],
          allowed_actions: options.memberAllowedActions ?? ["artifact.upload"],
          pagination: {
            ...pagination,
            total: options.artifacts?.length ?? 0,
            total_pages: options.artifacts?.length ? 1 : 0,
          },
          meta,
        },
      })
    if (path.endsWith("/jobs"))
      return route.fulfill({
        json: {
          data: options.jobs ?? [],
          pagination: {
            ...pagination,
            total: options.jobs?.length ?? 0,
            total_pages: options.jobs?.length ? 1 : 0,
          },
          meta,
        },
      })
    if (path.endsWith("/approvals"))
      return route.fulfill({
        json: {
          data: options.approvals ?? [],
          pagination: {
            ...pagination,
            total: options.approvals?.length ?? 0,
            total_pages: options.approvals?.length ? 1 : 0,
          },
          meta,
        },
      })
    if (path === "/api/v1/approvals/approval-1/approve") {
      if (options.approvalPostDelayMs) {
        await new Promise((resolve) =>
          setTimeout(resolve, options.approvalPostDelayMs),
        )
      }
      if (options.approvalConflict) {
        return route.fulfill({
          status: 409,
          json: {
            error: {
              code: "APPROVAL_PAYLOAD_STALE",
              message: "Approval payload is stale.",
              request_id: "request-approval-conflict",
              retryable: false,
            },
          },
        })
      }
      return route.fulfill({
        json: {
          data: { ...approvalFixture, status: "APPROVED" },
          meta,
        },
      })
    }
    if (path.endsWith("/audit-logs"))
      return route.fulfill({
        json: {
          data: [
            {
              id: "audit-1",
              project_id: "project-1",
              actor: {
                type: "USER",
                id: "user-1",
                display_name: "Project Owner",
              },
              action: "PROJECT_CREATED",
              target: {
                type: "ResearchProject",
                id: "project-1",
                label: "Evidence Review",
              },
              outcome: "SUCCEEDED",
              reason: null,
              request_id: "request-test",
              created_at: "2026-08-01T00:00:00Z",
            },
          ],
          pagination,
          meta,
        },
      })
    return route.fulfill({
      status: 404,
      json: {
        error: { code: "NOT_FOUND", message: "Not found" },
        request_id: "request-test",
      },
    })
  })
}

test("project list creates a project through the generated-client path", async ({
  page,
}) => {
  await installAuthenticatedMocks(page)
  await page.goto("/projects")
  await expect(page.getByRole("heading", { name: "Projects" })).toBeVisible()
  await page.getByRole("button", { name: "New project" }).click()
  await page.getByLabel("Name").fill("New M1 Project")
  await page.getByRole("button", { name: "Create", exact: true }).click()
  await expect(
    page.getByRole("heading", { name: "New M1 Project" }),
  ).toBeVisible()
})

test("project list keeps loading and empty states explicit", async ({
  page,
}) => {
  await page.addInitScript(() =>
    localStorage.setItem("access_token", "test-token"),
  )
  await page.route("**/api/v1/users/me", (route) =>
    route.fulfill({ json: M1_CONTRACT_MOCK.user }),
  )
  await page.route("**/api/v1/projects*", async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 500))
    await route.fulfill({
      json: {
        data: [],
        pagination: { ...pagination, total: 0, total_pages: 0 },
        meta,
      },
    })
  })
  await page.goto("/projects")
  await expect(page.getByText("Loading projects")).toBeVisible()
  await expect(page.getByText("No projects are available.")).toBeVisible()
})

test("workspace exposes M1 projections and explicit unavailable semantics", async ({
  page,
}) => {
  await installAuthenticatedMocks(page)
  await page.goto("/projects/project-1")
  await expect(
    page.getByRole("heading", { name: "Evidence Review" }),
  ).toBeVisible()
  await page.getByRole("tab", { name: "Overview" }).focus()
  await page.keyboard.press("ArrowRight")
  await expect(page.getByRole("tab", { name: "Members" })).toHaveAttribute(
    "data-state",
    "active",
  )
  await page.getByRole("tab", { name: "Overview" }).click()
  await expect(page.getByText("Not available").first()).toBeVisible()
  await page.getByRole("tab", { name: "Members" }).click()
  await expect(page.getByText("Project Owner").first()).toBeVisible()
  await page.getByRole("tab", { name: "Artifacts" }).click()
  await expect(page.getByText("No artifacts have been uploaded.")).toBeVisible()
  await page.getByRole("tab", { name: "Jobs" }).click()
  await expect(
    page.getByText("No jobs have been created by M1 domain services."),
  ).toBeVisible()
  await page.getByRole("tab", { name: "Approvals" }).click()
  await expect(
    page.getByText("No approval requests require attention."),
  ).toBeVisible()
  await page.getByRole("tab", { name: "Audit" }).click()
  await expect(
    page.getByText("PROJECT CREATED", { exact: false }),
  ).toBeVisible()
})

test("cross-project forbidden response remains visible and does not log out", async ({
  page,
}) => {
  await page.addInitScript(() =>
    localStorage.setItem("access_token", "test-token"),
  )
  await page.route("**/api/v1/users/me", (route) =>
    route.fulfill({ json: M1_CONTRACT_MOCK.user }),
  )
  await page.route("**/api/v1/projects/forbidden*", (route) =>
    route.fulfill({
      status: 403,
      json: {
        error: { code: "PROJECT_ACCESS_DENIED", message: "Access denied" },
        request_id: "request-forbidden",
      },
    }),
  )
  await page.goto("/projects/forbidden")
  await expect(page.getByRole("alert")).toContainText(
    "You do not have access to this project.",
  )
  await expect(page).toHaveURL(/projects\/forbidden/)
  expect(await page.evaluate(() => localStorage.getItem("access_token"))).toBe(
    "test-token",
  )
})

test("member controls remain derived from the current user's server permissions", async ({
  page,
}) => {
  await installAuthenticatedMocks(page, {
    memberAllowedActions: [],
    includeViewerMember: true,
  })
  await page.goto("/projects/project-1")
  await page.getByRole("tab", { name: "Members" }).click()

  await expect(page.getByText("Project Viewer")).toBeVisible()
  await expect(page.getByRole("button", { name: "Add member" })).toHaveCount(0)
  await expect(
    page.getByRole("button", { name: "Transfer ownership" }),
  ).toHaveCount(0)
  await expect(
    page.getByRole("button", { name: "Remove Project Viewer" }),
  ).toHaveCount(0)
})

test("project lifecycle remains hidden without the server permission", async ({
  page,
}) => {
  await installAuthenticatedMocks(page)
  await page.goto("/projects/project-1")

  await expect(page.getByRole("button", { name: "Archive" })).toHaveCount(0)
})

test("project lifecycle preserves pending state and refreshes after success", async ({
  page,
}) => {
  await installAuthenticatedMocks(page, {
    projectCanDelete: true,
    lifecycleDelayMs: 700,
  })
  await page.goto("/projects/project-1")
  await page.getByRole("button", { name: "Archive" }).click()

  await expect(page.getByRole("button", { name: "Archive" })).toBeDisabled()
  await expect(page.getByRole("button", { name: "Restore" })).toBeVisible()
})

test("member submission keeps the existing pending state", async ({ page }) => {
  await installAuthenticatedMocks(page, { memberPostDelayMs: 700 })
  await page.goto("/projects/project-1")
  await page.getByRole("tab", { name: "Members" }).click()
  await page.getByLabel("User ID").fill("user-2")
  await page.getByRole("button", { name: "Add member" }).click()

  await expect(page.getByRole("button", { name: "Add member" })).toBeDisabled()
  await expect(page.getByRole("button", { name: "Add member" })).toBeEnabled()
})

test("member query forbidden state remains visible inside the workspace", async ({
  page,
}) => {
  await installAuthenticatedMocks(page, { memberForbidden: true })
  await page.goto("/projects/project-1")
  await page.getByRole("tab", { name: "Members" }).click()

  await expect(page.getByRole("alert")).toContainText("Access denied", {
    timeout: 10_000,
  })
  await expect(page).toHaveURL(/projects\/project-1/)
})

test("approval submission disables only the pending approval actions", async ({
  page,
}) => {
  await installAuthenticatedMocks(page, {
    approvals: [approvalFixture],
    approvalPostDelayMs: 700,
  })
  await page.goto("/projects/project-1")
  await page.getByRole("tab", { name: "Approvals" }).click()
  await page.getByRole("button", { name: "Approve" }).click()

  await expect(page.getByRole("button", { name: "Approve" })).toBeDisabled()
  await expect(page.getByRole("button", { name: "Approve" })).toBeEnabled()
})

test("unknown artifact and job states remain degraded and non-actionable", async ({
  page,
}) => {
  await installAuthenticatedMocks(page, {
    artifacts: [
      {
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
      },
    ],
    jobs: [
      {
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
      },
    ],
  })
  await page.goto("/projects/project-1")

  await page.getByRole("tab", { name: "Artifacts" }).click()
  await expect(page.getByText("FUTURE_ARTIFACT_STATE")).toBeVisible()
  await expect(
    page.getByRole("button", { name: "Download future.bin" }),
  ).toBeDisabled()

  await page.getByRole("tab", { name: "Jobs" }).click()
  await expect(page.getByText("FUTURE_JOB_STATE")).toBeVisible()
  await expect(page.getByRole("button", { name: "Retry job" })).toBeDisabled()
  await expect(page.getByRole("button", { name: "Cancel job" })).toBeDisabled()
})

test("stale approval actions and conflict errors remain server controlled", async ({
  page,
}) => {
  await installAuthenticatedMocks(page, {
    approvals: [
      {
        ...approvalFixture,
        status: "SUPERSEDED",
        allowed_actions: [],
      },
    ],
  })
  await page.goto("/projects/project-1")
  await page.getByRole("tab", { name: "Approvals" }).click()

  await expect(page.getByText("SUPERSEDED")).toBeVisible()
  await expect(page.getByRole("button", { name: "Approve" })).toBeDisabled()
  await expect(page.getByRole("button", { name: "Reject" })).toBeDisabled()
  await expect(
    page.getByRole("button", { name: "Cancel approval" }),
  ).toBeDisabled()

  await page.unroute("**/api/v1/**")
  await installAuthenticatedMocks(page, {
    approvals: [approvalFixture],
    approvalConflict: true,
  })
  await page.reload()
  await page.getByRole("tab", { name: "Approvals" }).click()
  await page.getByRole("button", { name: "Approve" }).click()
  await expect(page.getByRole("alert")).toContainText(
    "Approval payload is stale.",
  )
})
