import { expect, type Page, test } from "@playwright/test"

const projectId = "00000000-0000-4000-8000-000000000801"
const runId = "00000000-0000-4000-8000-000000000810"
const badToolId = "00000000-0000-4000-8000-000000000899"
const meta = { request_id: "m8-browser", schema_version: "1.0" }

async function authenticate(page: Page) {
  await page.addInitScript(() =>
    localStorage.setItem("access_token", "m8-production-route-token"),
  )
  await page.route("**/api/v1/users/me", (route) =>
    route.fulfill({
      json: {
        id: "00000000-0000-4000-8000-000000000802",
        email: "owner@example.com",
        is_active: true,
        is_superuser: false,
        full_name: "M8 Owner",
      },
    }),
  )
}

function project() {
  return {
    id: projectId,
    owner_id: "00000000-0000-4000-8000-000000000802",
    name: "M8 production project",
    description: null,
    discipline: null,
    research_direction: null,
    project_type: "RESEARCH",
    current_stage: "EVIDENCE",
    status: "ACTIVE",
    expected_completion_date: null,
    resource_constraints: null,
    ethical_constraints: null,
    lock_version: 3,
    created_at: "2026-08-07T00:00:00Z",
    updated_at: "2026-08-07T00:00:00Z",
    permissions: { can_update: true, can_delete: true },
    allowed_actions: ["project.read"],
  }
}

function run() {
  return {
    id: runId,
    project_id: projectId,
    agent_type: "ResearchOrchestrator",
    status: "CREATED",
    known_status: true,
    lock_version: 1,
    safe_input_summary: {
      kind: "USER_GOAL",
      text: "Review the current project.",
      attributes: {},
    },
    safe_snapshot_summary: { blocking_issue_count: 0 },
    snapshot_hash: "a".repeat(64),
    snapshot_revision: 1,
    snapshot_current: true,
    source_object_versions: {},
    max_turns: 8,
    max_tool_calls: 12,
    turn_count: 0,
    tool_call_count: 0,
    retry_of_agent_run_id: null,
    failure_code: null,
    degradation_code: null,
    retryable: false,
    allowed_actions: ["agent_run.cancel"],
    disabled_reasons: {},
    job: null,
    events: [],
    model_invocations: [],
    created_at: "2026-08-07T00:00:00Z",
    updated_at: "2026-08-07T00:00:00Z",
    completed_at: null,
  }
}

async function registerAgentApi(page: Page) {
  await page.route(`**/api/v1/projects/${projectId}`, (route) =>
    route.fulfill({ json: { data: project(), meta } }),
  )
  await page.route(`**/api/v1/agent-runs/${runId}/tool-calls*`, (route) =>
    route.fulfill({
      json: {
        data: [],
        pagination: {
          page: 1,
          page_size: 100,
          total: 0,
          total_pages: 0,
          has_next: false,
          has_previous: false,
        },
        meta,
      },
    }),
  )
  await page.route(`**/api/v1/agent-runs/${runId}`, (route) =>
    route.fulfill({ json: { data: run(), meta } }),
  )
  await page.route(`**/api/v1/tool-calls/${badToolId}`, (route) =>
    route.fulfill({ status: 404, json: { detail: "Not found" } }),
  )
}

test("M8 production route creates a run through the generated adapter", async ({
  page,
}) => {
  await authenticate(page)
  await registerAgentApi(page)
  await page.route(
    `**/api/v1/projects/${projectId}/agent-runs`,
    async (route) => {
      const request = route.request()
      expect(request.headers()["idempotency-key"]).toBeTruthy()
      expect(await request.postDataJSON()).toEqual({
        goal: "Review the current project.",
        mode: "PLAN_AND_EXPLAIN",
        allow_tool_calls: true,
      })
      await route.fulfill({ status: 202, json: { data: run(), meta } })
    },
  )

  await page.goto(`/projects/${projectId}/agent`)
  await expect(
    page.getByRole("heading", { name: "M8 production project" }),
  ).toBeVisible()
  await page.getByRole("button", { name: "创建运行" }).click()
  await page
    .getByRole("textbox", { name: "目标" })
    .fill("Review the current project.")
  await page.getByRole("button", { name: "提交创建意图" }).click()
  await expect(page).toHaveURL(new RegExp(`run=${runId}`))
  await expect(page.getByText("已受理", { exact: true }).first()).toBeVisible()
})

test("M8 production deep link falls back without disclosing an unrelated ToolCall", async ({
  page,
}) => {
  await authenticate(page)
  await registerAgentApi(page)
  await page.goto(`/projects/${projectId}/agent?run=${runId}&tool=${badToolId}`)
  await expect(page.getByText("已回退到项目 Agent 面板")).toBeVisible()
  await expect(page.getByText(/不会披露目标对象是否存在/)).toBeVisible()
  await expect(
    page.locator('[data-od-id="agent-workspace"]').getByText(badToolId),
  ).toHaveCount(0)
})
