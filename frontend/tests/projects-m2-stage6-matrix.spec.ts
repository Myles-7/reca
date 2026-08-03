import { expect, test } from "@playwright/test"

import { documentFixtures } from "../src/features/documents/fixtures"
import { literatureFixtures } from "../src/features/literature/fixtures"
import { projectWorkspaceFixtures } from "../src/features/projects/fixtures"
import { queryPlanFixtures } from "../src/features/query-plan/fixtures"
import { researchQuestionFixtures } from "../src/features/research-question/fixtures"

const modules = [
  {
    id: "query-plan",
    label: "Query Plan",
    navigationIndex: 1,
    representativeFixtureId: "ready",
    fixtures: queryPlanFixtures,
  },
  {
    id: "literature",
    label: "Literature",
    navigationIndex: 2,
    representativeFixtureId: "ready",
    fixtures: literatureFixtures,
  },
  {
    id: "document",
    label: "Document",
    navigationIndex: 3,
    representativeFixtureId: "grobid-completed",
    fixtures: documentFixtures,
  },
  {
    id: "research-question",
    label: "Research Question",
    navigationIndex: 4,
    representativeFixtureId: "ready",
    fixtures: researchQuestionFixtures,
  },
  {
    id: "project-workspace",
    label: "Project Workspace",
    navigationIndex: 5,
    representativeFixtureId: "ready",
    fixtures: projectWorkspaceFixtures,
  },
] as const

const viewports = [
  { id: "desktop", width: 1440, height: 900 },
  { id: "tablet", width: 1024, height: 768 },
  { id: "mobile", width: 390, height: 844 },
] as const

const themes = ["light", "dark"] as const

for (const module of modules) {
  for (const viewport of viewports) {
    for (const theme of themes) {
      test(`${module.label} fixtures fit ${viewport.width}x${viewport.height} ${theme}`, async ({
        page,
      }, testInfo) => {
        test.setTimeout(120_000)
        await page.setViewportSize(viewport)
        await page.goto("/design-preview.html")
        await page
          .getByRole("navigation")
          .getByRole("button")
          .nth(module.navigationIndex)
          .click()

        const segments = page.locator(".preview-segment")
        await segments
          .nth(0)
          .getByRole("button")
          .nth(theme === "light" ? 0 : 1)
          .click()
        await segments
          .nth(1)
          .getByRole("button")
          .nth(viewports.indexOf(viewport))
          .click()

        const fixtureSelect = page.locator(".preview-field select")
        const productSurface = page.locator(
          `.preview-product-surface[data-module="${module.id}"]`,
        )

        for (const fixture of module.fixtures) {
          await fixtureSelect.selectOption(fixture.id)
          await expect(productSurface).toBeVisible()
          const workspaceRoot = productSurface.locator(":scope > *").first()
          await expect(workspaceRoot).toBeVisible()

          const overflow = await page.evaluate(() => {
            const surface = document.querySelector(
              ".preview-product-surface",
            ) as HTMLElement | null
            const workspace = surface?.firstElementChild as HTMLElement | null
            return {
              page:
                document.documentElement.scrollWidth -
                document.documentElement.clientWidth,
              surface: surface ? surface.scrollWidth - surface.clientWidth : 1,
              workspace: workspace
                ? workspace.scrollWidth - workspace.clientWidth
                : 1,
            }
          })
          expect(overflow, `${module.id}/${fixture.id}`).toEqual({
            page: 0,
            surface: 0,
            workspace: 0,
          })

          if (
            fixture.id === module.representativeFixtureId &&
            viewport.id === "desktop" &&
            theme === "light"
          ) {
            await workspaceRoot.screenshot({
              path: testInfo.outputPath(`${module.id}-representative-pass.png`),
            })
          }
        }
      })
    }
  }
}

test("Project Dialog traps focus and restores the transfer trigger", async ({
  page,
}) => {
  await page.goto("/design-preview.html")
  await page.getByRole("navigation").getByRole("button").nth(5).click()
  await page
    .locator('[data-od-id="project-workspace"] nav button')
    .nth(1)
    .click()

  const trigger = page
    .getByRole("button", { name: "Transfer ownership" })
    .first()
  await trigger.click()
  const dialog = page.getByRole("dialog")
  await expect(dialog).toBeVisible()
  expect(
    await dialog.evaluate((element) =>
      element.contains(document.activeElement),
    ),
  ).toBe(true)

  const focusable = dialog.locator(
    'button:not([disabled]), input:not([disabled]), [role="combobox"]:not([aria-disabled="true"])',
  )
  const last = focusable.last()
  await last.focus()
  await page.keyboard.press("Tab")
  await expect(focusable.first()).toBeFocused()
  await focusable.first().focus()
  await page.keyboard.press("Shift+Tab")
  await expect(last).toBeFocused()

  await page.keyboard.press("Escape")
  await expect(dialog).toBeHidden()
  await expect(trigger).toBeFocused()
})

test("Document Sheet manages focus and honors reduced motion", async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: "reduce" })
  await page.setViewportSize({ width: 1024, height: 768 })
  await page.goto("/design-preview.html")
  await page.getByRole("navigation").getByRole("button").nth(3).click()
  await page.locator(".preview-field select").selectOption("grobid-completed")
  await page
    .locator(".preview-segment")
    .nth(1)
    .getByRole("button")
    .nth(1)
    .click()

  const trigger = page.locator(".document-tablet-controls button").first()
  await trigger.click()
  const sheet = page.getByRole("dialog")
  await expect(sheet).toBeVisible()
  await expect(sheet.getByRole("heading").first()).toBeFocused()
  const reducedMotion = await sheet.evaluate((element) => {
    const style = getComputedStyle(element)
    return {
      animationName: style.animationName,
      transitionSeconds: Number.parseFloat(style.transitionDuration),
    }
  })
  expect(reducedMotion.animationName).toBe("none")
  expect(reducedMotion.transitionSeconds).toBeLessThanOrEqual(0.00001)

  const focusable = sheet.locator(
    "button:not([disabled]), [href], input:not([disabled])",
  )
  const first = focusable.first()
  const last = focusable.last()
  await last.focus()
  await page.keyboard.press("Tab")
  expect(
    await sheet.evaluate((element) => element.contains(document.activeElement)),
  ).toBe(true)
  await first.focus()
  await page.keyboard.press("Shift+Tab")
  expect(
    await sheet.evaluate((element) => element.contains(document.activeElement)),
  ).toBe(true)

  await page.keyboard.press("Escape")
  await expect(sheet).toBeHidden()
  await expect(trigger).toBeFocused()
})

test("selection stays local and Event Log records intent without success", async ({
  page,
}) => {
  await page.goto("/design-preview.html")
  await page.getByRole("navigation").getByRole("button").nth(2).click()

  const candidate = page.locator(".literature-row--candidate").first()
  const selectCandidate = candidate.locator(".literature-row__select")
  await selectCandidate.click()
  await expect(selectCandidate).toHaveAttribute("aria-pressed", "true")
  await expect(page.locator(".preview-event-log li")).toHaveCount(0)

  await candidate.locator(".literature-row__action button").click()
  await expect(page.locator(".preview-event-log li")).toHaveCount(1)
  await expect(page.locator(".preview-event-log li strong")).toHaveText(
    "import-candidates",
  )
  await expect(candidate).toBeVisible()
  await expect(selectCandidate).toHaveAttribute("aria-pressed", "true")
})

test("retry entry is present only for a retryable load error", async ({
  page,
}) => {
  await page.goto("/design-preview.html")
  await page.getByRole("navigation").getByRole("button").nth(1).click()
  const fixtureSelect = page.locator(".preview-field select")
  await fixtureSelect.selectOption("load-error")
  const retry = page.locator(".reca-query-plan-workspace button").first()
  await expect(retry).toBeEnabled()
  await retry.click()
  await expect(page.locator(".preview-event-log li strong")).toHaveText("retry")

  await fixtureSelect.selectOption("forbidden")
  await expect(page.locator(".reca-query-plan-workspace button")).toHaveCount(0)
})
