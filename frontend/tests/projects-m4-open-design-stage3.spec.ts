import { mkdir } from "node:fs/promises"
import path from "node:path"
import { expect, type Page, test } from "@playwright/test"

import { dataWorkspaceFixtures } from "../src/features/data-workspace/fixtures"

const viewports = [
  { id: "desktop", width: 1440, height: 900, previewIndex: 0 },
  { id: "tablet", width: 1024, height: 768, previewIndex: 1 },
  { id: "mobile", width: 390, height: 844, previewIndex: 2 },
] as const

const themes = [
  { id: "light", previewIndex: 0 },
  { id: "dark", previewIndex: 1 },
] as const

const screenshotDir = path.resolve(
  process.env.RECA_M4_SCREENSHOT_DIR ??
    "../output/playwright/qa/m4-open-design-stage3",
)

async function openDataWorkspace(page: Page) {
  await page.goto("/design-preview.html")
  await page
    .getByRole("navigation", { name: "设计预览模块" })
    .getByRole("button", { name: "Data Workspace", exact: true })
    .click()
  const product = page.locator(
    '.preview-product-surface[data-module="data-workspace"]',
  )
  await expect(product).toBeVisible()
  return product
}

async function configurePreview(
  page: Page,
  viewport: (typeof viewports)[number],
  theme: (typeof themes)[number],
) {
  await page.setViewportSize({ width: viewport.width, height: viewport.height })
  const segments = page.locator(".preview-segment")
  await segments.nth(0).getByRole("button").nth(theme.previewIndex).click()
  await segments.nth(1).getByRole("button").nth(viewport.previewIndex).click()
}

async function chooseFixture(page: Page, fixtureId: string) {
  const select = page.locator(".preview-field select")
  await select.selectOption(fixtureId)
  await expect(select).toHaveValue(fixtureId)
}

async function chooseWorkspaceView(page: Page, name: string) {
  await page
    .getByRole("navigation", { name: "数据工作台视图" })
    .getByRole("button", { name, exact: true })
    .click()
}

for (const viewport of viewports) {
  for (const theme of themes) {
    test(`M4 full fixture matrix fits ${viewport.width}x${viewport.height} ${theme.id}`, async ({
      page,
    }) => {
      test.setTimeout(180_000)
      const errors: string[] = []
      const apiRequests: string[] = []
      page.on("console", (message) => {
        if (message.type() === "error") errors.push(message.text())
      })
      page.on("pageerror", (error) => errors.push(error.message))
      page.on("request", (request) => {
        if (request.url().includes("/api/")) apiRequests.push(request.url())
      })

      const product = await openDataWorkspace(page)
      await configurePreview(page, viewport, theme)
      const fixtureSelect = page.locator(".preview-field select")

      for (const fixture of dataWorkspaceFixtures) {
        await fixtureSelect.selectOption(fixture.id)
        await expect(product).toBeVisible()
        const workspace = product.locator(":scope > *").first()
        await expect(workspace).toBeVisible()
        await expect(workspace).toHaveAttribute("data-theme", theme.id)

        const result = await page.evaluate(() => {
          const productSurface = document.querySelector(
            '.preview-product-surface[data-module="data-workspace"]',
          ) as HTMLElement | null
          const workspaceRoot =
            productSurface?.firstElementChild as HTMLElement | null
          const previewTables = Array.from(
            productSurface?.querySelectorAll(
              ".m4-preview-scroller, .m4-columns-scroller, .m4-ops-table-scroll",
            ) ?? [],
          ) as HTMLElement[]
          return {
            pageOverflow:
              document.documentElement.scrollWidth -
              document.documentElement.clientWidth,
            surfaceOverflow: productSurface
              ? productSurface.scrollWidth - productSurface.clientWidth
              : 1,
            workspaceOverflow: workspaceRoot
              ? workspaceRoot.scrollWidth - workspaceRoot.clientWidth
              : 1,
            workspaceHeight: workspaceRoot?.getBoundingClientRect().height ?? 0,
            internalTableOverflow: previewTables.some(
              (element) => element.scrollWidth > element.clientWidth,
            ),
          }
        })

        expect(result.pageOverflow, fixture.id).toBe(0)
        expect(result.surfaceOverflow, fixture.id).toBe(0)
        expect(result.workspaceOverflow, fixture.id).toBe(0)
        expect(result.workspaceHeight, fixture.id).toBeGreaterThan(300)
      }

      expect(apiRequests).toEqual([])
      expect(errors).toEqual([])
    })
  }
}

test("quality filters and selection remain local", async ({ page }) => {
  await openDataWorkspace(page)
  await chooseWorkspaceView(page, "质量")
  const eventCount = page.locator(".preview-event-log li")
  await expect(eventCount).toHaveCount(0)

  const filters = page.locator(".m4-quality-filters select")
  await filters.nth(0).selectOption({ index: 1 })
  await expect(eventCount).toHaveCount(0)
  await filters.nth(0).selectOption({ index: 0 })

  await page.locator(".m4-issue-name").first().click()
  await expect(eventCount).toHaveCount(0)
  await expect(
    page.locator(".m4-quality-table tr[data-selected='true']"),
  ).toHaveCount(1)
})

test("long content stays within the root and scrolls only inside the field table", async ({
  page,
}) => {
  await openDataWorkspace(page)
  await chooseFixture(page, "long-content")
  await chooseWorkspaceView(page, "字段")
  const result = await page.evaluate(() => {
    const root = document.querySelector(
      '[data-od-id="m4-data-workspace"]',
    ) as HTMLElement | null
    const scroller = document.querySelector(
      ".m4-columns-scroller",
    ) as HTMLElement | null
    return {
      rootOverflow: root ? root.scrollWidth - root.clientWidth : 1,
      tableOverflow: scroller ? scroller.scrollWidth - scroller.clientWidth : 0,
    }
  })
  expect(result.rootOverflow).toBe(0)
  expect(result.tableOverflow).toBeGreaterThan(0)
})

test("ignore dialog requires a reason, traps focus and restores the trigger", async ({
  page,
}) => {
  await openDataWorkspace(page)
  await chooseWorkspaceView(page, "质量")
  const trigger = page.getByRole("button", { name: "忽略并说明原因" })
  await trigger.click()

  const dialog = page.getByRole("dialog", { name: "忽略 Issue" })
  await expect(dialog).toBeVisible()
  const reason = dialog.getByLabel("忽略原因")
  await expect(reason).toBeFocused()
  await expect(
    dialog.getByRole("button", { name: "提交忽略原因" }),
  ).toBeDisabled()

  const focusable = dialog.locator(
    "button:not([disabled]), input:not([disabled]), textarea:not([disabled]), [href]",
  )
  await focusable.last().focus()
  await page.keyboard.press("Tab")
  expect(
    await dialog.evaluate((element) =>
      element.contains(document.activeElement),
    ),
  ).toBe(true)
  await focusable.first().focus()
  await page.keyboard.press("Shift+Tab")
  expect(
    await dialog.evaluate((element) =>
      element.contains(document.activeElement),
    ),
  ).toBe(true)

  await page.keyboard.press("Escape")
  await expect(dialog).toBeHidden()
  await expect(trigger).toBeFocused()
})

test("ignore intent is sanitized and does not mutate the formal Issue", async ({
  page,
}) => {
  await openDataWorkspace(page)
  await chooseWorkspaceView(page, "质量")
  const originalStatus = await page
    .locator(".m4-quality-table tbody tr")
    .first()
    .locator("td")
    .last()
    .innerText()

  await page.getByRole("button", { name: "忽略并说明原因" }).click()
  const dialog = page.getByRole("dialog", { name: "忽略 Issue" })
  await dialog.getByLabel("忽略原因").fill("该缺失值属于预先登记的结构性缺失。")
  await dialog.getByRole("button", { name: "提交忽略原因" }).click()
  await expect(dialog).toBeHidden()

  const event = page.locator(".preview-event-log li").first()
  await expect(event.getByRole("strong")).toHaveText("ignore-issue")
  await expect(event.locator("pre")).toContainText('"kind": "text"')
  await expect(event.locator("pre")).not.toContainText("结构性缺失")
  await expect(
    page.locator(".m4-quality-table tbody tr").first().locator("td").last(),
  ).toHaveText(originalStatus)
})

test("upload draft stays local and the Event Log excludes file content", async ({
  page,
}) => {
  const errors: string[] = []
  page.on("pageerror", (error) => errors.push(error.message))
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text())
  })
  await openDataWorkspace(page)
  const title = page.locator('[data-od-id="dataset-title"]')
  const originalTitle = await title.innerText()
  await page
    .getByRole("button", { name: /上传数据集/ })
    .first()
    .click()
  const dialog = page.getByRole("dialog", { name: "上传科研数据集" })
  await expect(dialog).toBeVisible()
  const fileInput = dialog.locator('input[type="file"]')
  await fileInput.setInputFiles({
    name: "stage3-bounded.csv",
    mimeType: "text/csv",
    buffer: Buffer.from("participant,score\nmasked,18\n"),
  })
  const nameInput = dialog.getByLabel(/数据集名称/)
  await nameInput.fill("阶段 3 本地上传草稿")
  await expect(title).toHaveText(originalTitle)
  await dialog.getByRole("button", { name: /提交上传/ }).click()

  expect(errors).toEqual([])
  await expect(page.locator(".preview-event-log li")).toHaveCount(1)
  await dialog.getByRole("button", { name: "关闭", exact: true }).click()
  await expect(dialog).toBeHidden()
  const event = page.locator(".preview-event-log li").first()
  await expect(event.getByRole("strong")).toHaveText("upload-dataset")
  const summary = event.locator("pre")
  await expect(summary).toContainText("stage3-bounded.csv")
  await expect(summary).not.toContainText("participant,score")
  await expect(title).toHaveText(originalTitle)
})

test("unknown permissions fail closed with visible reasons", async ({
  page,
}) => {
  await openDataWorkspace(page)
  await chooseFixture(page, "permissions-unknown")
  await chooseWorkspaceView(page, "质量")
  const runQuality = page.getByRole("button", { name: /运行质量检查/ })
  await expect(runQuality).toBeDisabled()
  await expect(runQuality).toHaveAttribute("aria-label", /权限状态未知/)
  await expect(
    page.getByText("权限状态未知，所有写操作已安全关闭。"),
  ).toBeVisible()
})

test("mobile inspector Sheet traps focus, restores focus and disables motion", async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: "reduce" })
  await page.setViewportSize({ width: 1440, height: 900 })
  await openDataWorkspace(page)
  await configurePreview(page, viewports[2], themes[0])

  const trigger = page
    .getByRole("navigation", { name: "移动端主要表面" })
    .getByRole("button", { name: "详情" })
  await trigger.click()
  const sheet = page.getByRole("dialog", { name: "上下文检查器" })
  await expect(sheet).toBeVisible()
  expect(
    await sheet.evaluate((element) => element.contains(document.activeElement)),
  ).toBe(true)
  const motion = await sheet.evaluate((element) => {
    const style = getComputedStyle(element)
    return {
      animation: style.animationName,
      transition: Number.parseFloat(style.transitionDuration),
    }
  })
  expect(motion.animation).toBe("none")
  expect(motion.transition).toBeLessThanOrEqual(0.00001)

  await page.keyboard.press("Escape")
  await expect(sheet).toBeHidden()
  await expect(trigger).toBeFocused()
})

test("pending actions prevent duplicate submissions", async ({ page }) => {
  await openDataWorkspace(page)
  await chooseFixture(page, "upload-pending")
  const upload = page.getByRole("button", { name: /上传数据集/ }).first()
  await expect(upload).toBeDisabled()
  await expect(page.locator(".preview-event-log li")).toHaveCount(0)

  await chooseFixture(page, "transform-failed")
  await chooseWorkspaceView(page, "清洗")
  const retry = page.getByRole("button", { name: "重试 Job" })
  await expect(retry).toBeEnabled()
  await retry.click()
  await expect(page.locator(".preview-event-log li strong").first()).toHaveText(
    "retry-job",
  )
  await expect(page.getByText("FAILED", { exact: true }).first()).toBeVisible()
})

test("XLSX hidden worksheet uses the corrected capability and explicit acknowledgement", async ({
  page,
}) => {
  await openDataWorkspace(page)
  await chooseFixture(page, "xlsx-worksheets")
  const hiddenWorksheet = page
    .locator('[data-od-id="worksheet-selector"]')
    .getByRole("button", { name: /Archive/ })
  await expect(hiddenWorksheet).toBeEnabled()
  await hiddenWorksheet.click()
  const dialog = page.getByRole("dialog", { name: "确认选择隐藏工作表" })
  await expect(dialog).toBeVisible()
  await dialog.getByRole("button", { name: "确认选择" }).click()
  const event = page.locator(".preview-event-log li").first()
  await expect(event.getByRole("strong")).toHaveText("select-worksheet")
  await expect(event.locator("pre")).toContainText('"acknowledgeHidden": true')
})

test("typed CleaningPlan editor emits an update intent without changing Plan state", async ({
  page,
}) => {
  await openDataWorkspace(page)
  await chooseFixture(page, "plan-draft")
  await chooseWorkspaceView(page, "清洗")
  const originalStatus = await page
    .locator('[data-od-id="cleaning-plan-summary"]')
    .textContent()
  await page.getByRole("button", { name: "编辑计划" }).click()
  const dialog = page.getByRole("dialog", { name: "编辑 CleaningPlan" })
  await expect(dialog).toBeVisible()
  await expect(dialog.locator(".m4-plan-editor-actions > div")).toHaveCount(2)
  await dialog.getByRole("button", { name: "保存计划" }).click()
  const event = page.locator(".preview-event-log li").first()
  await expect(event.getByRole("strong")).toHaveText("update-plan")
  await expect(event.locator("pre")).not.toContainText("Control")
  expect(
    await page.locator('[data-od-id="cleaning-plan-summary"]').textContent(),
  ).toBe(originalStatus)
})

test("version comparison intent is gated by the formal parent Version", async ({
  page,
}) => {
  await openDataWorkspace(page)
  await chooseWorkspaceView(page, "版本")
  const compare = page.getByRole("button", { name: "与父版本比较" })
  await expect(compare).toBeEnabled()
  await compare.click()
  await expect(
    page.locator(".preview-event-log li").first().getByRole("strong"),
  ).toHaveText("compare-versions")
})

test("representative Stage 3 screenshots", async ({ page }) => {
  test.setTimeout(120_000)
  await mkdir(screenshotDir, { recursive: true })

  const cases = [
    { fixture: "ready", view: "质量", name: "quality-completed" },
    { fixture: "approval-stale", view: "清洗", name: "approval-stale" },
    { fixture: "transform-running", view: "清洗", name: "transform-running" },
    { fixture: "transform-failed", view: "清洗", name: "transform-failed" },
    { fixture: "long-content", view: "数据", name: "long-content" },
  ] as const

  for (const viewport of [viewports[0], viewports[2]]) {
    for (const theme of themes) {
      await page.setViewportSize({ width: 1440, height: 900 })
      await openDataWorkspace(page)
      await configurePreview(page, viewport, theme)
      for (const item of cases) {
        await chooseFixture(page, item.fixture)
        await chooseWorkspaceView(page, item.view)
        const workspace = page.locator('[data-od-id="m4-data-workspace"]')
        await expect(workspace).toBeVisible()
        await page.evaluate(
          ({ width, height }) => {
            document.getElementById("m4-stage3-screenshot-clone")?.remove()
            const source = document.querySelector(
              '[data-od-id="m4-data-workspace"]',
            )
            if (!(source instanceof HTMLElement)) return
            const clone = source.cloneNode(true) as HTMLElement
            clone.id = "m4-stage3-screenshot-clone"
            Object.assign(clone.style, {
              position: "fixed",
              inset: "0",
              zIndex: "9999",
              width: `${width}px`,
              height: `${height}px`,
              minHeight: "0",
              overflow: "hidden",
            })
            document.body.append(clone)
          },
          { width: viewport.width, height: viewport.height },
        )
        await page.screenshot({
          path: path.join(
            screenshotDir,
            `${item.name}-${viewport.width}x${viewport.height}-${theme.id}.png`,
          ),
          clip: {
            x: 0,
            y: 0,
            width: viewport.width,
            height: viewport.height,
          },
        })
        await page.evaluate(() =>
          document.getElementById("m4-stage3-screenshot-clone")?.remove(),
        )
      }
    }
  }
})
