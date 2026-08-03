import { expect, test } from "@playwright/test"

test("project design fixtures are available through the explicit dev preview", async ({
  page,
}) => {
  const apiRequests: string[] = []
  page.on("request", (request) => {
    if (request.url().includes("/api/")) apiRequests.push(request.url())
  })

  await page.goto("/design-preview.html")
  await page
    .getByRole("navigation")
    .getByRole("button", { name: "Project Workspace", exact: true })
    .click()
  const fixtureSelect = page.locator(".preview-field select")
  await expect(fixtureSelect).toHaveValue("ready")
  await expect(
    page.getByRole("heading", { name: "Evidence synthesis workspace" }),
  ).toBeVisible()

  await fixtureSelect.selectOption("forbidden")
  await expect(fixtureSelect).toHaveValue("forbidden")
  await expect(page.getByRole("alert")).toContainText(
    "You do not have permission",
  )

  await fixtureSelect.selectOption("degraded")
  await page.getByRole("button", { name: "Jobs", exact: true }).click()
  await expect(page.getByText("FUTURE_JOB_STATE")).toBeVisible()
  await expect(page.getByRole("button", { name: "Retry job" })).toBeDisabled()
  await expect(page.getByRole("button", { name: "Cancel job" })).toBeDisabled()

  expect(apiRequests).toEqual([])
})
