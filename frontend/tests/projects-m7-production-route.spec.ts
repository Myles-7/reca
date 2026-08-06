import { expect, type Page, test } from "@playwright/test"

const projectId = "11111111-1111-4111-8111-111111111117"
const userId = "10101010-1010-4010-8010-101010101017"

const meta = { request_id: "m7-route", schema_version: "1.0" }

async function registerM7Routes(page: Page) {
  await page.addInitScript(() =>
    localStorage.setItem("access_token", "m7-production-route-token"),
  )
  await page.route("**/api/v1/users/me", (route) =>
    route.fulfill({
      json: {
        id: userId,
        email: "m7-owner@example.com",
        is_active: true,
        is_superuser: false,
        full_name: "M7 Owner",
      },
    }),
  )
  await page.route(`**/api/v1/projects/${projectId}`, (route) =>
    route.fulfill({
      json: {
        data: {
          id: projectId,
          name: "M7 evidence project",
          project_type: "RESEARCH",
          status: "ACTIVE",
          owner_id: userId,
          allowed_actions: ["evidence.read", "export.readiness"],
        },
        meta,
      },
    }),
  )
  await page.route("**/api/v1/claims/unavailable-claim", (route) =>
    route.fulfill({
      status: 404,
      json: {
        error: {
          code: "RESOURCE_NOT_FOUND",
          message: "The requested resource is unavailable.",
          retryable: false,
        },
        meta,
      },
    }),
  )
  await page.route(
    `**/api/v1/projects/${projectId}/evidence-graph**`,
    (route) =>
      route.fulfill({
        json: {
          data: {
            nodes: [
              {
                id: "CLAIM:22222222-2222-4222-8222-222222222227",
                node_type: "CLAIM",
                object_id: "22222222-2222-4222-8222-222222222227",
                label: "Authorized claim projection",
                raw_status: "ACTIVE",
                known_status: true,
                risk: "LOW",
                invalidated: false,
                stale: false,
                source_kind: "DOMAIN",
                detail_intent: "claim",
                allowed_actions: ["evidence.read"],
                limitations: [],
                lane: "claims",
                rank: 0,
              },
            ],
            edges: [],
            completeness: {},
            partial: false,
            next_cursor: null,
            limitations: [],
            scope: { project_id: projectId },
          },
          meta,
        },
      }),
  )
}

test("M7 production route fails closed for an inaccessible deep link", async ({
  page,
}) => {
  await registerM7Routes(page)
  await page.goto(
    `/projects/${projectId}/evidence?claim=unavailable-claim&view=graph`,
  )

  await expect(page.locator('[data-od-id="evidence-workspace"]')).toBeVisible()
  await expect(page.locator(".m7-route-band")).toBeVisible()
  await expect(
    page.locator('[data-od-id="evidence-graph-canvas"]'),
  ).toBeVisible()
  await expect(
    page.locator(".react-flow__node", {
      hasText: "Authorized claim projection",
    }),
  ).toBeVisible()
  await expect(page.locator(".react-flow__handle.connectable")).toHaveCount(0)

  await page.locator(".m7-mode-switch button").nth(1).click()
  await expect(
    page.locator('[data-od-id="evidence-graph-table-fallback"]'),
  ).toBeVisible()
})

test("M7 production route stays bounded and keyboard reachable at 390px", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await registerM7Routes(page)
  await page.goto(`/projects/${projectId}/evidence`)

  await expect(page.locator('[data-od-id="evidence-workspace"]')).toBeVisible()
  expect(
    await page.evaluate(
      () =>
        document.documentElement.scrollWidth -
        document.documentElement.clientWidth,
    ),
  ).toBe(0)
  await page.keyboard.press("Tab")
  await expect(page.locator(":focus")).toBeVisible()
})
