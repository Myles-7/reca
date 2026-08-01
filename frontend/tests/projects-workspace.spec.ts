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
  },
}

const meta = { request_id: "request-test", schema_version: "1.0" }
const pagination = { page: 1, page_size: 100, total: 1, total_pages: 1 }

async function installAuthenticatedMocks(page: Page) {
  await page.addInitScript(() =>
    localStorage.setItem("access_token", "test-token"),
  )
  const projects = [M1_CONTRACT_MOCK.project]
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
        ...M1_CONTRACT_MOCK.project,
        id: "project-2",
        name: body.name,
      }
      projects.push(created)
      return route.fulfill({ status: 201, json: { data: created, meta } })
    }
    if (path === "/api/v1/projects/project-1") {
      return route.fulfill({ json: { data: M1_CONTRACT_MOCK.project, meta } })
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
      return route.fulfill({
        json: {
          data: [
            {
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
              allowed_actions: [
                "project.manage_members",
                "artifact.upload",
                "job.retry",
                "job.cancel",
              ],
            },
          ],
          pagination,
          meta,
        },
      })
    }
    if (path.endsWith("/artifacts"))
      return route.fulfill({
        json: {
          data: [],
          pagination: { ...pagination, total: 0, total_pages: 0 },
          meta,
        },
      })
    if (path.endsWith("/jobs"))
      return route.fulfill({
        json: {
          data: [],
          pagination: { ...pagination, total: 0, total_pages: 0 },
          meta,
        },
      })
    if (path.endsWith("/approvals"))
      return route.fulfill({
        json: {
          data: [],
          pagination: { ...pagination, total: 0, total_pages: 0 },
          meta,
        },
      })
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
