import { expect, type Page, test } from "@playwright/test"
import { QueryClient } from "@tanstack/react-query"

import type { QueryPlanPublic } from "../src/api/adapter"
import { projectKeys } from "../src/features/projects/queries"
import { invalidateQueryPlanMutation } from "../src/features/query-plan/mutations"
import { queryPlanKeys } from "../src/features/query-plan/queries"
import type { QueryPlanEvent } from "../src/features/query-plan/ui/contracts"
import { createDeferred } from "./utils/deferred"

const meta = { request_id: "request-query-plan", schema_version: "1.0" }

function plan(overrides: Partial<QueryPlanPublic> = {}): QueryPlanPublic {
  return {
    id: "plan-1",
    project_id: "project-1",
    research_question_version_id: "rq-version-1",
    chinese_terms: ["学习投入"],
    english_terms: ["learning engagement"],
    synonyms: { engagement: ["participation"] },
    object_terms: { population: ["teacher education students"] },
    method_terms: { design: ["survey"] },
    boolean_query: '"learning engagement" AND "teacher education"',
    filters: {
      from_year: 2020,
      to_year: 2026,
      languages: ["en", "zh"],
      work_types: ["article"],
      open_access_only: true,
    },
    limitations: ["Provider coverage varies by discipline."],
    source_model_invocation_id: null,
    status: "DRAFT",
    lock_version: 3,
    created_at: "2026-08-01T03:00:00Z",
    updated_at: "2026-08-01T03:20:00Z",
    allowed_actions: [
      "query_plan.read",
      "query_plan.update",
      "query_plan.generate",
    ],
    ...overrides,
  }
}

async function authenticate(page: Page) {
  await page.addInitScript(() =>
    localStorage.setItem("access_token", "test-token"),
  )
  await page.route("**/api/v1/users/me", (route) =>
    route.fulfill({
      json: {
        id: "user-1",
        email: "owner@example.com",
        is_active: true,
        is_superuser: false,
        full_name: "Owner",
      },
    }),
  )
}

function contractError(code: string, message: string, retryable = false) {
  return {
    error: {
      code,
      message,
      request_id: `request-${code.toLowerCase()}`,
      retryable,
    },
  }
}

test("Query Plan deep link and refresh preserve formal identifiers", async ({
  page,
}) => {
  await authenticate(page)
  let loads = 0
  await page.route("**/api/v1/query-plans/plan-1", (route) => {
    loads += 1
    return route.fulfill({ json: { data: plan(), meta } })
  })

  await page.goto("/projects/project-1/query-plans/plan-1")
  const workspace = page.locator(".reca-query-plan-workspace")
  await expect(workspace).toBeVisible()
  await expect(workspace.getByText("plan-1", { exact: true })).toBeVisible()
  await expect(
    workspace.getByText("rq-version-1", { exact: true }),
  ).toBeVisible()
  await expect(
    workspace.getByText("DRAFT", { exact: true }).first(),
  ).toBeVisible()

  await page.reload()
  await expect(workspace).toBeVisible()
  await expect.poll(() => loads).toBe(2)
})

test("Query Plan read-only, forbidden, and unknown projections fail closed", async ({
  page,
}) => {
  await authenticate(page)
  let response:
    | "read-only"
    | "forbidden"
    | "unknown"
    | "permissions-unknown"
    | "route-mismatch" = "read-only"
  await page.route("**/api/v1/query-plans/plan-1", (route) => {
    if (response === "forbidden") {
      return route.fulfill({
        status: 403,
        json: contractError("PROJECT_ACCESS_DENIED", "Access denied."),
      })
    }
    if (response === "permissions-unknown") {
      const { allowed_actions: _allowedActions, ...withoutActions } = plan()
      return route.fulfill({ json: { data: withoutActions, meta } })
    }
    return route.fulfill({
      json: {
        data: plan(
          response === "unknown"
            ? { status: "FUTURE_QUERY_PLAN_STATE" as QueryPlanPublic["status"] }
            : response === "route-mismatch"
              ? { project_id: "project-2" }
              : { allowed_actions: ["query_plan.read"] },
        ),
        meta,
      },
    })
  })

  await page.goto("/projects/project-1/query-plans/plan-1")
  await expect(page.locator(".query-plan-editor input").first()).toBeDisabled()
  await expect(page.locator(".query-plan-primary-action")).toHaveCount(0)

  response = "unknown"
  await page.reload()
  await expect(
    page.locator('.reca-query-plan-workspace [data-tone="unknown"]').first(),
  ).toBeVisible()
  await expect(page.locator(".query-plan-editor input").first()).toBeDisabled()
  await expect(page.locator(".query-plan-primary-action")).toHaveCount(0)

  response = "permissions-unknown"
  await page.reload()
  await expect(page.locator(".query-plan-editor input").first()).toBeDisabled()
  await expect(page.locator(".query-plan-primary-action")).toHaveCount(0)

  response = "forbidden"
  await page.reload()
  await expect(page.getByRole("alert")).toBeVisible()
  await expect(page.locator(".reca-query-plan-workspace button")).toHaveCount(0)

  response = "route-mismatch"
  await page.reload()
  await expect(page.getByRole("alert")).toContainText(
    "does not match this project route",
  )
  await expect(page.locator(".reca-query-plan-workspace button")).toHaveCount(0)
})

test("Query Plan update keeps pending state and refetches after success", async ({
  page,
}) => {
  await authenticate(page)
  let current = plan()
  let loads = 0
  const updateRequest = createDeferred()
  await page.route("**/api/v1/query-plans/plan-1", async (route) => {
    const request = route.request()
    if (request.method() === "PATCH") {
      expect(request.headers()["if-match"]).toBe('"3"')
      expect(request.postDataJSON()).toMatchObject({
        change_reason: "Narrow the publication years",
      })
      await updateRequest.promise
      current = plan({ lock_version: 4, updated_at: "2026-08-01T04:00:00Z" })
      return route.fulfill({ json: { data: current, meta } })
    }
    loads += 1
    return route.fulfill({ json: { data: current, meta } })
  })

  await page.goto("/projects/project-1/query-plans/plan-1")
  await page
    .locator("#query-plan-change-reason")
    .fill("Narrow the publication years")
  const save = page.locator(".query-plan-save-button")
  await save.click()
  await expect(save).toBeDisabled()
  updateRequest.resolve()
  await expect.poll(() => loads).toBe(2)
  await expect(page.getByText("4", { exact: true }).last()).toBeVisible()
})

test("Query Plan update exposes server error and conflict without optimistic success", async ({
  page,
}) => {
  await authenticate(page)
  let failure: "error" | "conflict" = "error"
  await page.route("**/api/v1/query-plans/plan-1", (route) => {
    if (route.request().method() === "PATCH") {
      const conflict = failure === "conflict"
      return route.fulfill({
        status: conflict ? 409 : 503,
        json: contractError(
          conflict ? "OPTIMISTIC_LOCK_CONFLICT" : "QUERY_PLAN_UPDATE_FAILED",
          conflict
            ? "The query plan is stale."
            : "The update service is unavailable.",
          !conflict,
        ),
      })
    }
    return route.fulfill({ json: { data: plan(), meta } })
  })

  await page.goto("/projects/project-1/query-plans/plan-1")
  const reason = page.locator("#query-plan-change-reason")
  await reason.fill("First update attempt")
  await page.locator(".query-plan-save-button").click()
  await expect(
    page.getByText("The update service is unavailable."),
  ).toBeVisible()
  await expect(page.getByText("DRAFT", { exact: true }).first()).toBeVisible()

  failure = "conflict"
  await reason.fill("Second update attempt")
  await page.locator(".query-plan-save-button").click()
  await expect(page.getByText("The query plan is stale.")).toBeVisible()
  await expect(page.getByText("DRAFT", { exact: true }).first()).toBeVisible()
})

test("Query Plan generate is pending, idempotent, and refetches without optimistic success", async ({
  page,
}) => {
  await authenticate(page)
  let loads = 0
  const generateRequest = createDeferred()
  await page.route("**/api/v1/query-plans/plan-1**", async (route) => {
    const request = route.request()
    if (request.method() === "POST") {
      expect(new URL(request.url()).pathname).toBe(
        "/api/v1/query-plans/plan-1/generate",
      )
      expect(request.headers()["idempotency-key"]).toBeTruthy()
      expect(request.postDataJSON()).toEqual({})
      await generateRequest.promise
      return route.fulfill({
        status: 202,
        json: {
          data: {
            id: "job-1",
            project_id: "project-1",
            job_type: "QUERY_PLAN_GENERATION",
            status: "QUEUED",
            progress: 0,
            retryable: false,
            cancelable: true,
            created_by: "user-1",
            created_at: "2026-08-01T04:00:00Z",
            updated_at: "2026-08-01T04:00:00Z",
            started_at: null,
            finished_at: null,
            error: null,
            allowed_actions: ["job.cancel"],
          },
          meta,
        },
      })
    }
    loads += 1
    return route.fulfill({ json: { data: plan(), meta } })
  })

  await page.goto("/projects/project-1/query-plans/plan-1")
  const generate = page.locator(".query-plan-primary-action")
  await generate.click()
  await expect(generate).toBeDisabled()
  await expect(page.getByText("DRAFT", { exact: true }).first()).toBeVisible()
  generateRequest.resolve()
  await expect.poll(() => loads).toBe(2)
  await expect(page.getByText("DRAFT", { exact: true }).first()).toBeVisible()
})

test("Query Plan mutation invalidation is resource exact", async () => {
  const update: QueryPlanEvent = {
    action: "update",
    input: {
      queryPlanId: "plan-1",
      lockVersion: 3,
      changeReason: "Update",
      fields: {
        chineseTerms: [],
        englishTerms: [],
        synonyms: {},
        objectTerms: {},
        methodTerms: {},
        booleanQuery: null,
        filters: {
          fromYear: null,
          toYear: null,
          languages: [],
          workTypes: [],
          openAccessOnly: false,
        },
        limitations: [],
      },
    },
  }
  const generate: QueryPlanEvent = {
    action: "generate",
    input: { queryPlanId: "plan-1" },
  }

  const updateClient = new QueryClient()
  updateClient.setQueryData(queryPlanKeys.detail("project-1", "plan-1"), {})
  updateClient.setQueryData(projectKeys.jobs("project-1"), {})
  updateClient.setQueryData(queryPlanKeys.detail("project-2", "plan-1"), {})
  await invalidateQueryPlanMutation(updateClient, "project-1", "plan-1", update)
  expect(
    updateClient.getQueryState(queryPlanKeys.detail("project-1", "plan-1"))
      ?.isInvalidated,
  ).toBe(true)
  expect(
    updateClient.getQueryState(projectKeys.jobs("project-1"))?.isInvalidated,
  ).toBe(false)
  expect(
    updateClient.getQueryState(queryPlanKeys.detail("project-2", "plan-1"))
      ?.isInvalidated,
  ).toBe(false)

  const generateClient = new QueryClient()
  generateClient.setQueryData(queryPlanKeys.detail("project-1", "plan-1"), {})
  generateClient.setQueryData(projectKeys.jobs("project-1"), {})
  await invalidateQueryPlanMutation(
    generateClient,
    "project-1",
    "plan-1",
    generate,
  )
  expect(
    generateClient.getQueryState(queryPlanKeys.detail("project-1", "plan-1"))
      ?.isInvalidated,
  ).toBe(true)
  expect(
    generateClient.getQueryState(projectKeys.jobs("project-1"))?.isInvalidated,
  ).toBe(true)
})
