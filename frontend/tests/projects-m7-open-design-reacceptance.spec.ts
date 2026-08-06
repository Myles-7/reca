import { expect, test } from "@playwright/test"

test("M7 Open Design consumes the four corrected integration contracts", async ({
  page,
}) => {
  const consoleErrors: string[] = []
  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text())
  })

  await page.goto("/design-preview.html")
  await page.getByRole("button", { name: "Evidence Workspace" }).click()

  const fixture = page.locator('[data-od-id="preview-toolbar"] select').nth(0)
  const view = page.locator('[data-od-id="preview-toolbar"] select').nth(1)
  await expect(page.locator('[data-od-id="evidence-workspace"]')).toBeVisible()

  await fixture.selectOption("link-suggested")
  await view.selectOption("claims")
  await expect(page.locator(".m7-link-actions button").nth(1)).toBeEnabled()

  await fixture.selectOption("export-failed-retryable")
  await view.selectOption("exports")
  await expect(
    page.locator(".m7-form-actions--chain button").nth(1),
  ).toBeEnabled()

  await fixture.selectOption("export-running-cancellable")
  await view.selectOption("exports")
  await expect(
    page.locator(".m7-form-actions--chain button").nth(2),
  ).toBeEnabled()

  await fixture.selectOption("package-history-versions")
  await expect(page.locator(".m7-package-history article")).toHaveCount(3)
  await expect(
    page.locator('.m7-package-history article[aria-current="true"]'),
  ).toHaveCount(1)

  await fixture.selectOption("graph-full-chain")
  await view.selectOption("audits")
  await expect(page.getByText("Audit Job", { exact: true })).toBeVisible()

  expect(consoleErrors).toEqual([])
})

for (const viewport of [
  { name: "desktop-light", width: 1440, height: 900, themeIndex: 0 },
  { name: "tablet-dark", width: 1024, height: 768, themeIndex: 1 },
  { name: "mobile-light", width: 390, height: 844, themeIndex: 0 },
]) {
  test(`M7 corrected fixtures remain bounded on ${viewport.name}`, async ({
    page,
  }) => {
    await page.goto("/design-preview.html")
    await page.getByRole("button", { name: "Evidence Workspace" }).click()
    const segments = page.locator(
      '[data-od-id="preview-toolbar"] .preview-segment',
    )
    await segments.nth(1).locator("button").nth(viewport.themeIndex).click()

    const fixture = page.locator('[data-od-id="preview-toolbar"] select').nth(0)
    for (const fixtureId of [
      "link-suggested",
      "export-failed-retryable",
      "export-running-cancellable",
      "package-history-versions",
    ]) {
      await page.setViewportSize({ width: 1440, height: 900 })
      await fixture.selectOption(fixtureId)
      await page.setViewportSize({
        width: viewport.width,
        height: viewport.height,
      })
      const workspace = page.locator('[data-od-id="evidence-workspace"]')
      await expect(workspace).toBeVisible()
      expect(
        await page.evaluate(
          () =>
            document.documentElement.scrollWidth -
            document.documentElement.clientWidth,
        ),
      ).toBe(0)
    }
  })
}
