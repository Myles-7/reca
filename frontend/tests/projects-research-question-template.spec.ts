import { expect, type Page, test } from "@playwright/test"

import type {
  CurrentResearchQuestionEnvelope,
  ResearchQuestionVersionPublic,
} from "../src/api/adapter"
import { researchQuestionReadyFixture } from "../src/features/research-question/fixtures"
import { mapResearchQuestion } from "../src/features/research-question/mappers"
import {
  researchQuestionHref,
  researchQuestionRoute,
} from "../src/features/research-question/model"
import {
  canExecuteResearchQuestionEvent,
  executeResearchQuestionEvent,
  type ResearchQuestionMutationPort,
} from "../src/features/research-question/mutations"
import {
  loadResearchQuestion,
  validateResearchQuestionProjection,
} from "../src/features/research-question/queries"

const meta = { request_id: "request-rq", schema_version: "1.0" }

function version(
  overrides: Partial<ResearchQuestionVersionPublic> = {},
): ResearchQuestionVersionPublic {
  return {
    id: "version-2",
    research_question_id: "question-1",
    project_id: "project-1",
    version_number: 2,
    raw_input: "How does AI use relate to learning engagement?",
    normalized_question:
      "What is the association between AI use and learning engagement?",
    research_object: "Teacher education students",
    population: "Undergraduate teacher education students",
    context: "Higher education",
    independent_variables: ["AI use"],
    dependent_variables: ["Learning engagement"],
    control_variables: [],
    research_goal: "RELATE",
    relationship_type: "ASSOCIATION",
    method_preference: null,
    time_scope: null,
    region_scope: null,
    language_scope: null,
    resource_constraints: null,
    ethical_constraints: null,
    uncertainties: null,
    source_model_invocation_id: null,
    status: "DRAFT",
    created_by: "user-1",
    created_at: "2026-08-01T03:20:00Z",
    is_current: true,
    allowed_actions: [
      "research_question.edit",
      "research_question.create_version",
      "research_question.mark_ready",
    ],
    pending_approval_id: null,
    pending_approval_status: null,
    ...overrides,
  }
}

function currentEnvelope(
  currentVersion: ResearchQuestionVersionPublic | null = version(),
): CurrentResearchQuestionEnvelope {
  return {
    data: {
      question: currentVersion
        ? {
            id: "question-1",
            project_id: "project-1",
            status: "DRAFT",
            current_version_id: currentVersion.id,
            created_by: "user-1",
            created_at: "2026-08-01T03:00:00Z",
            updated_at: "2026-08-01T03:20:00Z",
            current_version: currentVersion,
          }
        : null,
      allowed_actions: currentVersion ? [] : ["research_question.create"],
      capability_availability: {
        research_question: "AVAILABLE",
        ai_parse: "NOT_AVAILABLE",
        query_plan: "NOT_AVAILABLE",
        literature: "NOT_AVAILABLE",
      },
    },
    meta,
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

test("mapper uses server actions and fails closed for unknown states", () => {
  expect(researchQuestionRoute).toBe("/projects/$projectId/research-question")
  expect(researchQuestionHref("project-1")).toBe(
    "/projects/project-1/research-question",
  )
  const unknown = version({
    status:
      "FUTURE_RESEARCH_QUESTION_STATE" as ResearchQuestionVersionPublic["status"],
    allowed_actions: [
      "research_question.create_version",
      "research_question.mark_ready",
      "research_question.request_confirmation",
    ],
  })
  const mapped = mapResearchQuestion({
    current: currentEnvelope(unknown),
    versions: [unknown],
  })
  expect(mapped.question).toMatchObject({
    knownStatus: false,
    tone: "degraded",
    permissions: {
      canEdit: false,
      canCreateVersion: false,
      canMarkReady: false,
      canRequestConfirmation: false,
    },
  })
  expect(mapped.capabilities).toEqual({
    researchQuestion: "AVAILABLE",
    aiParse: "NOT_AVAILABLE",
    queryPlan: "NOT_AVAILABLE",
    literature: "NOT_AVAILABLE",
  })
})

test("mapper keeps unknown capability values distinct from unavailable", () => {
  const current = currentEnvelope()
  current.data.capability_availability.ai_parse = "FUTURE_CAPABILITY_STATE"
  const mapped = mapResearchQuestion({ current, versions: [version()] })

  expect(mapped.capabilities.aiParse).toBe("UNKNOWN")
  expect(mapped.capabilities.literature).toBe("NOT_AVAILABLE")
})

test("query and mutation boundaries preserve generated API facts", async () => {
  const calls: unknown[] = []
  const current = currentEnvelope()
  const loaded = await loadResearchQuestion("project-1", {
    getCurrent: async (projectId) => {
      calls.push(["get-current", projectId])
      return current
    },
    listVersions: async (questionId) => {
      calls.push(["list-versions", questionId])
      return { data: [version()] }
    },
  })
  expect(loaded.question?.currentVersionId).toBe("version-2")

  const port: ResearchQuestionMutationPort = {
    create: async (projectId, event) =>
      calls.push(["create", projectId, event]),
    saveVersion: async (event) => calls.push(["save-version", event]),
    markReady: async (event) => calls.push(["mark-ready", event]),
    requestConfirmation: async (event) =>
      calls.push(["request-confirmation", event]),
  }
  await executeResearchQuestionEvent(
    "project-1",
    { action: "create", input: { rawInput: "Initial idea" } },
    port,
  )
  await executeResearchQuestionEvent(
    "project-1",
    {
      action: "mark-ready",
      input: { versionId: "version-2", reason: "Reviewed" },
    },
    port,
  )
  expect(calls.map((call) => (call as unknown[])[0])).toEqual([
    "get-current",
    "list-versions",
    "create",
    "mark-ready",
  ])
})

test("Open Design fixtures cover degraded and pending approval UI states", async ({
  page,
}) => {
  const apiRequests: string[] = []
  page.on("request", (request) => {
    if (request.url().includes("/api/")) apiRequests.push(request.url())
  })
  await page.goto("/research-question-preview.html")
  await expect(page.locator("main[data-fixture-id]")).toHaveAttribute(
    "data-fixture-id",
    "ready",
  )
  await page.getByRole("combobox", { name: "Fixture" }).click()
  await page.getByRole("option", { name: "Degraded" }).click()
  await expect(
    page.locator('.rq-workspace [data-tone="unknown"]'),
  ).toBeVisible()
  await expect(page.locator(".rq-button").nth(1)).toBeDisabled()

  await page.getByRole("combobox", { name: "Fixture" }).click()
  await page.getByRole("option", { name: "Pending confirmation" }).click()
  await expect(page.getByText(/PENDING/).first()).toBeVisible()
  await expect(page.locator(".rq-button").nth(2)).toBeDisabled()
  expect(apiRequests).toEqual([])
})

test("mobile long-content, keyboard, and degraded fixtures remain safe", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 })
  const apiRequests: string[] = []
  page.on("request", (request) => {
    if (request.url().includes("/api/")) apiRequests.push(request.url())
  })
  await page.goto("/research-question-preview.html")

  await page.keyboard.press("Tab")
  const fixtureTrigger = page.getByRole("combobox", { name: "Fixture" })
  await expect(fixtureTrigger).toBeFocused()
  const focusStyle = await fixtureTrigger.evaluate((element) => {
    const style = getComputedStyle(element)
    return { boxShadow: style.boxShadow, outlineStyle: style.outlineStyle }
  })
  expect(
    focusStyle.boxShadow !== "none" || focusStyle.outlineStyle !== "none",
  ).toBe(true)
  await page.keyboard.press("Enter")
  await expect(
    page.getByRole("option", { name: "Ready", exact: true }),
  ).toBeFocused()
  await page.keyboard.press("ArrowDown")
  await expect(page.getByRole("option", { name: "Loading" })).toBeFocused()
  await page.keyboard.press("Enter")
  await expect(page.locator("main[data-fixture-id]")).toHaveAttribute(
    "data-fixture-id",
    "loading",
  )
  await expect(page.locator(".rq-capability-list")).toHaveCount(0)

  await fixtureTrigger.click()
  await page.getByRole("option", { name: "Error" }).click()
  await expect(page.locator(".rq-capability-list")).toHaveCount(0)

  await fixtureTrigger.click()
  await page.getByRole("option", { name: "Long content" }).click()
  const overflow = await page.evaluate(() => ({
    viewport: document.documentElement.clientWidth,
    document: document.documentElement.scrollWidth,
    body: document.body.scrollWidth,
  }))
  expect(overflow.document).toBeLessThanOrEqual(overflow.viewport)
  expect(overflow.body).toBeLessThanOrEqual(overflow.viewport)

  await fixtureTrigger.click()
  await page.getByRole("option", { name: "Degraded" }).click()
  await expect(page.locator(".rq-button").nth(1)).toBeDisabled()
  await expect(page.locator(".rq-button").nth(2)).toBeDisabled()
  await expect(page.locator(".rq-button").nth(0)).toBeDisabled()
  expect(
    await page.locator("form input, form textarea").evaluateAll((fields) =>
      fields.every((field) => {
        const input = field as HTMLInputElement
        return input.disabled || input.readOnly
      }),
    ),
  ).toBe(true)
  expect(apiRequests).toEqual([])
})

test("formal route loads and mutates through the Research Question API", async ({
  page,
}) => {
  let currentVersion = version()
  await page.route("**/api/v1/**", async (route) => {
    const request = route.request()
    const path = new URL(request.url()).pathname
    if (path === "/api/v1/projects/project-1/research-question") {
      return route.fulfill({ json: currentEnvelope(currentVersion) })
    }
    if (path === "/api/v1/research-questions/question-1/versions") {
      return route.fulfill({ json: { data: [currentVersion], meta } })
    }
    if (
      path === "/api/v1/research-question-versions/version-2/ready" &&
      request.method() === "POST"
    ) {
      expect(request.headers()["idempotency-key"]).toBeTruthy()
      expect(request.postDataJSON()).toEqual({ reason: null })
      currentVersion = version({
        status: "READY",
        allowed_actions: [
          "research_question.create_version",
          "research_question.request_confirmation",
        ],
      })
      return route.fulfill({ json: { data: currentVersion, meta } })
    }
    return route.abort()
  })

  await authenticate(page)
  await page.goto("/projects/project-1/research-question")
  await expect(
    page.getByRole("heading", { name: "Research question" }),
  ).toBeVisible()
  await expect(
    page.locator('.rq-capability-list [data-tone="neutral"]'),
  ).toHaveCount(3)
  await expect(
    page.locator('.rq-capability-list [data-tone="info"]'),
  ).toHaveCount(1)
  await page.locator(".rq-button").nth(1).click()
  await expect.poll(() => currentVersion.status).toBe("READY")
  await expect(page.locator(".rq-button").nth(2)).toBeEnabled()
})

test("formal route keeps conflict pending and server controlled", async ({
  page,
}) => {
  const currentVersion = version()
  await page.route("**/api/v1/**", async (route) => {
    const request = route.request()
    const path = new URL(request.url()).pathname
    if (path === "/api/v1/projects/project-1/research-question") {
      return route.fulfill({ json: currentEnvelope(currentVersion) })
    }
    if (path === "/api/v1/research-questions/question-1/versions") {
      return route.fulfill({ json: { data: [currentVersion], meta } })
    }
    if (
      path === "/api/v1/research-question-versions/version-2/ready" &&
      request.method() === "POST"
    ) {
      await new Promise((resolve) => setTimeout(resolve, 500))
      return route.fulfill({
        status: 409,
        json: {
          error: {
            code: "RESEARCH_QUESTION_VERSION_CONFLICT",
            message: "Research question version is stale.",
            request_id: "request-rq-conflict",
            retryable: false,
          },
        },
      })
    }
    return route.abort()
  })

  await authenticate(page)
  await page.goto("/projects/project-1/research-question")
  const markReady = page.locator(".rq-button").nth(1)
  await markReady.click()
  await expect(markReady).toBeDisabled()
  await expect(page.getByRole("alert")).toContainText(
    "Research question version is stale.",
  )
  await expect(page.getByRole("alert")).toContainText("request-rq-conflict")
  await expect(page.getByText("草稿").first()).toBeVisible()
  await expect(markReady).toBeEnabled()
})

test("ready fixture remains a typed Open Design input", () => {
  expect(researchQuestionReadyFixture.content.state).toBe("ready")
})

test("Research Question container guard requires known permission projection", () => {
  const content = researchQuestionReadyFixture.content
  expect(content.state).toBe("ready")
  if (content.state !== "ready") return
  const markReady = {
    action: "mark-ready",
    input: { versionId: content.data.currentVersionId, reason: null },
  } as const
  expect(canExecuteResearchQuestionEvent(content.data, false, markReady)).toBe(
    true,
  )
  expect(
    canExecuteResearchQuestionEvent(
      { ...content.data, permissionsKnown: false },
      false,
      markReady,
    ),
  ).toBe(false)
  expect(
    canExecuteResearchQuestionEvent(null, true, {
      action: "create",
      input: { rawInput: "Initial question" },
    }),
  ).toBe(true)
  expect(
    canExecuteResearchQuestionEvent(null, true, {
      action: "create",
      input: { rawInput: "   " },
    }),
  ).toBe(false)
  expect(
    canExecuteResearchQuestionEvent(content.data, false, {
      action: "mark-ready",
      input: { versionId: "version-outside-projection", reason: null },
    }),
  ).toBe(false)
  expect(
    canExecuteResearchQuestionEvent(content.data, false, {
      action: "save-version",
      input: {
        questionId: content.data.questionId,
        basedOnVersionId: "version-stale",
        changeReason: "Stale view",
        fields: content.data.fields,
      },
    }),
  ).toBe(false)
})

test("Research Question route projection rejects cross-project identities", () => {
  const current = currentEnvelope()
  const versions = [version()]
  expect(() =>
    validateResearchQuestionProjection("project-1", current, versions),
  ).not.toThrow()
  if (!current.data.question) return
  const mismatch = {
    ...current,
    data: {
      ...current.data,
      question: { ...current.data.question, project_id: "project-2" },
    },
  }
  expect(() =>
    validateResearchQuestionProjection("project-1", mismatch, versions),
  ).toThrow(/does not match this project route/)
})

test("Research Question rejects a mismatched current projection before loading versions", async () => {
  const mismatch = currentEnvelope()
  if (!mismatch.data.question) return
  mismatch.data.question.project_id = "project-2"
  let versionLoads = 0
  await expect(
    loadResearchQuestion("project-1", {
      getCurrent: async () => mismatch,
      listVersions: async () => {
        versionLoads += 1
        return { data: [version()] }
      },
    }),
  ).rejects.toThrow(/does not match this project route/)
  expect(versionLoads).toBe(0)
})
