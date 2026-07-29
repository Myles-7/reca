import { expect, test } from "@playwright/test"

test("home and system status use the running API", async ({
  page,
  request,
}) => {
  const apiBaseUrl = process.env.API_BASE_URL ?? "http://127.0.0.1:8000"
  for (const endpoint of ["live", "ready", "dependencies"]) {
    const response = await request.get(
      `${apiBaseUrl}/api/v1/health/${endpoint}`,
    )
    expect(
      response.ok(),
      `${endpoint} endpoint should be reachable`,
    ).toBeTruthy()
  }
  await page.goto("/")
  await expect(page.getByRole("heading", { name: "RECA" })).toBeVisible()
  await page.goto("/system-status")
  await expect(
    page.getByRole("heading", { name: "System status" }),
  ).toBeVisible()
  await expect(page.getByText("Dependencies")).toBeVisible()
})
