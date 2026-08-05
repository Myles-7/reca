import { expect, type Page, test } from "@playwright/test"

const projectId = "11111111-1111-4111-8111-111111111111"

async function authenticate(page: Page) {
  await page.addInitScript(() =>
    localStorage.setItem("access_token", "m5-production-route-token"),
  )
  await page.route("**/api/v1/users/me", (route) =>
    route.fulfill({
      json: {
        id: "10101010-1010-4010-8010-101010101010",
        email: "owner@example.com",
        is_active: true,
        is_superuser: false,
        full_name: "M5 Owner",
      },
    }),
  )
}

async function registerProject(page: Page) {
  await page.route(`**/api/v1/projects/${projectId}`, (route) =>
    route.fulfill({
      json: {
        data: {
          id: projectId,
          name: "M5 analysis project",
          project_type: "RESEARCH",
          status: "ACTIVE",
          owner_id: "10101010-1010-4010-8010-101010101010",
          allowed_actions: [
            "analysis_plan.create",
            "figure.create",
            "job.cancel",
            "job.retry",
          ],
        },
        meta: { request_id: "m5-route", schema_version: "1.0" },
      },
    }),
  )
}

test("M5 production route safely restores views and discards invalid deep links", async ({
  page,
}) => {
  await authenticate(page)
  await registerProject(page)
  await page.goto(
    `/projects/${projectId}/analysis?dataset=not-a-uuid&figure=also-invalid&view=figures`,
  )

  const workspace = page.locator('[data-od-id="analysis-workspace"]')
  await expect(workspace).toBeVisible()
  await expect(
    page.locator('[data-od-id="analysis-figures-workspace"]'),
  ).toBeVisible()

  await page.locator('[data-od-id="analysis-view-plan"]').click()
  await expect(page).toHaveURL(/view=plan/)
  await page.reload()
  await expect(
    page.locator('[data-od-id="analysis-plan-surface"]'),
  ).toBeVisible()
})

test("M5 production route keeps project no-disclosure fail closed", async ({
  page,
}) => {
  await authenticate(page)
  await page.route(`**/api/v1/projects/${projectId}`, (route) =>
    route.fulfill({
      status: 404,
      json: {
        error: {
          code: "RESOURCE_NOT_FOUND",
          message: "The requested resource is unavailable.",
          retryable: false,
        },
        meta: { request_id: "m5-forbidden", schema_version: "1.0" },
      },
    }),
  )

  await page.goto(`/projects/${projectId}/analysis`)
  await expect(page.locator('[data-od-id="analysis-workspace"]')).toBeVisible()
  await expect(page.getByRole("alert")).toBeVisible()
  await expect(
    page.locator('[data-od-id="analysis-plan-surface"]'),
  ).toHaveCount(0)
})

for (const viewport of [
  { name: "desktop", width: 1440, height: 900 },
  { name: "tablet", width: 820, height: 1180 },
  { name: "mobile", width: 390, height: 844 },
]) {
  test(`M5 production route is bounded and keyboard reachable on ${viewport.name}`, async ({
    page,
  }) => {
    await page.setViewportSize(viewport)
    await authenticate(page)
    await registerProject(page)
    await page.goto(`/projects/${projectId}/analysis?view=plan`)

    const workspace = page.locator('[data-od-id="analysis-workspace"]')
    await expect(workspace).toBeVisible()
    expect(
      await page.evaluate(
        () =>
          document.documentElement.scrollWidth -
          document.documentElement.clientWidth,
      ),
    ).toBe(0)

    await page.keyboard.press("Tab")
    await expect(page.locator(":focus")).toBeVisible()

    const darkSurface = await page.evaluate(
      () => getComputedStyle(document.body).backgroundColor,
    )
    await page.evaluate(() => localStorage.setItem("vite-ui-theme", "light"))
    await page.reload()
    await expect(workspace).toBeVisible()
    const lightSurface = await page.evaluate(
      () => getComputedStyle(document.body).backgroundColor,
    )
    expect(lightSurface).not.toBe(darkSurface)
    expect(
      await page.evaluate(
        () =>
          document.documentElement.scrollWidth -
          document.documentElement.clientWidth,
      ),
    ).toBe(0)
  })
}
