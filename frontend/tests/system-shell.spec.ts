import { expect, type Page, test } from "@playwright/test"

const dependencies = [
  ["api", "HEALTHY"],
  ["postgres", "HEALTHY"],
  ["pgvector", "HEALTHY"],
  ["valkey", "DEGRADED"],
  ["worker", "UNKNOWN"],
  ["minio", "UNAVAILABLE"],
  ["grobid", "DEGRADED"],
  ["model", "UNCONFIGURED"],
  ["openalex", "UNCONFIGURED"],
] as const

async function mockHealth(page: Page) {
  await page.route("**/api/v1/health/live", async (route) => {
    await route.fulfill({ json: { status: "HEALTHY", service: "api" } })
  })
  await page.route("**/api/v1/health/ready", async (route) => {
    await route.fulfill({
      json: { status: "HEALTHY", dependencies: [] },
    })
  })
  await page.route("**/api/v1/health/dependencies", async (route) => {
    await route.fulfill({
      json: {
        dependencies: dependencies.map(([name, status]) => ({
          name,
          status,
          detail: `${name} test status`,
        })),
      },
    })
  })
}

test("home presents the engineering foundation without business metrics", async ({
  page,
}) => {
  await page.goto("/")

  await expect(page.getByRole("heading", { name: "RECA" })).toBeVisible()
  await expect(page.getByText("Research Evidence Chain Agent")).toBeVisible()
  await expect(page.getByText("研证链 AI")).toBeVisible()
  await expect(page.getByText(/engineering foundation phase/i)).toBeVisible()
  await expect(page.getByText("Environment:")).toBeVisible()
  await expect(page.getByText("Demo Mode:")).toBeVisible()
  await expect(
    page.getByRole("link", { name: /view system status/i }),
  ).toBeVisible()
  await expect(
    page.getByText(/project count|literature count|dataset count/i),
  ).toHaveCount(0)
})

test("login route remains available", async ({ page }) => {
  await page.goto("/login")
  await expect(
    page.getByRole("heading", { name: /login to your account/i }),
  ).toBeVisible()
  await expect(page.getByLabel("Email")).toBeVisible()
})

test("system status displays generated-client health data with textual states", async ({
  page,
}) => {
  await mockHealth(page)
  await page.goto("/system-status")

  await expect(
    page.getByRole("heading", { name: "System status" }),
  ).toBeVisible()
  await expect(page.getByLabel("API live: HEALTHY")).toBeVisible()
  await expect(page.getByLabel("Valkey: DEGRADED")).toBeVisible()
  await expect(page.getByLabel("MinIO: UNAVAILABLE")).toBeVisible()
  await expect(page.getByLabel("Model: UNCONFIGURED")).toBeVisible()
  await expect(page.getByLabel("Worker: UNKNOWN")).toBeVisible()
  await expect(page.getByText("Environment:")).toBeVisible()
  await expect(page.getByText("Demo Mode:")).toBeVisible()
})

test("system status keeps a loading state and handles API failures", async ({
  page,
}) => {
  await page.route("**/api/v1/health/live", async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 300))
    await route.fulfill({ json: { status: "HEALTHY", service: "api" } })
  })
  await page.route("**/api/v1/health/ready", (route) =>
    route.fulfill({
      status: 503,
      json: {
        error: { code: "UNAVAILABLE", message: "redacted" },
        request_id: "test",
      },
    }),
  )
  await page.route("**/api/v1/health/dependencies", (route) =>
    route.abort("failed"),
  )
  await page.goto("/system-status")

  await expect(page.getByText("Loading dependency status")).toBeVisible()
  await expect(
    page.getByText(/health information could not be loaded/i),
  ).toBeVisible()
  await expect(page.getByLabel("PostgreSQL: UNAVAILABLE")).toBeVisible()
})

test("system status handles a server error without a crash", async ({
  page,
}) => {
  await page.route("**/api/v1/health/live", (route) =>
    route.fulfill({
      status: 503,
      json: {
        error: { code: "UNAVAILABLE", message: "redacted" },
        request_id: "test",
      },
    }),
  )
  await page.route("**/api/v1/health/ready", (route) =>
    route.fulfill({
      status: 503,
      json: {
        error: { code: "UNAVAILABLE", message: "redacted" },
        request_id: "test",
      },
    }),
  )
  await page.route("**/api/v1/health/dependencies", (route) =>
    route.fulfill({
      status: 503,
      json: {
        error: { code: "UNAVAILABLE", message: "redacted" },
        request_id: "test",
      },
    }),
  )
  await page.goto("/system-status")

  await expect(
    page.getByText(/API reported a server error/i).first(),
  ).toBeVisible()
  await expect(page.getByLabel("API live: UNAVAILABLE")).toBeVisible()
})

test("404 and keyboard navigation are accessible", async ({ page }) => {
  await page.goto("/404")
  await expect(page.getByText("Page not found")).toBeVisible()
  await page.getByRole("link", { name: "Go home" }).press("Enter")
  await expect(page.getByRole("heading", { name: "RECA" })).toBeVisible()

  await page.getByRole("link", { name: "RECA" }).focus()
  await expect(page.getByRole("link", { name: "RECA" })).toBeFocused()
  await page.keyboard.press("Tab")
  await expect(
    page.getByRole("link", { name: "System status", exact: true }),
  ).toBeFocused()
})
