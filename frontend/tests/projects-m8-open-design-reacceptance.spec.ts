import { expect, test } from "@playwright/test"

async function openAgentPreview(page: import("@playwright/test").Page) {
  await page.goto("/design-preview.html")
  await page.getByRole("button", { name: "Agent Workspace" }).click()
  return page.locator('[data-od-id="preview-toolbar"] select').nth(0)
}

test("M8 cancel intent is confirmed, masked and does not mutate fixture facts", async ({
  page,
}) => {
  const fixture = await openAgentPreview(page)
  await fixture.selectOption("running-cancellable")
  await expect(page.locator('[data-od-id="agent-workspace"]')).toBeVisible()
  const trigger = page.getByRole("button", { name: "取消运行" })
  await expect(trigger).toBeEnabled()
  await trigger.click()

  const dialog = page.locator('[data-od-id="cancel-agent-run-dialog"]')
  await expect(dialog).toBeVisible()
  await expect(dialog).toContainText("不会回滚已完成的 Tool、Job")
  await expect(dialog.locator(":focus")).toHaveCount(1)
  await page.keyboard.press("Escape")
  await expect(dialog).toBeHidden()
  await expect(trigger).toBeFocused()

  await trigger.click()
  await dialog.getByRole("button", { name: "提交取消意图" }).click()
  await expect(page.getByText("cancel-run", { exact: true })).toHaveCount(1)
  await expect(page.getByText(/0000…0010/)).toBeVisible()
  await expect(page.getByText("运行中", { exact: true }).first()).toBeVisible()

  await fixture.selectOption("running-cancel-pending")
  const pendingCancel = page.getByRole("button", {
    name: "取消运行",
    exact: true,
  })
  await expect(pendingCancel).toBeDisabled()
  await expect(pendingCancel).toContainText("取消中")
})

test("M8 retry intent requires a retryable Tool and remains pending until new Props", async ({
  page,
}) => {
  const fixture = await openAgentPreview(page)
  await fixture.selectOption("tool-failed-retry-allowed")
  await expect(page.locator('[data-od-id="agent-workspace"]')).toBeVisible()
  const trigger = page.getByRole("button", { name: "重试" }).first()
  await expect(trigger).toBeEnabled()
  await trigger.click()

  const dialog = page.locator('[data-od-id="retry-agent-run-dialog"]')
  await expect(dialog).toBeVisible()
  await expect(dialog).toContainText("不会由前端回滚或复制")
  await expect(dialog.locator(":focus")).toHaveCount(1)
  await page.keyboard.press("Escape")
  await expect(trigger).toBeFocused()

  await trigger.click()
  await dialog.getByRole("button", { name: "提交重试意图" }).click()
  await expect(page.getByText("retry-or-restart", { exact: true })).toHaveCount(
    1,
  )
  await expect(page.getByText(/goalLength/)).toBeVisible()
  await expect(page.getByText("失败", { exact: true }).first()).toBeVisible()

  await fixture.selectOption("tool-retry-pending")
  const pendingRetry = page.getByRole("button", { name: "重试", exact: true })
  await expect(pendingRetry).toBeDisabled()
  await expect(pendingRetry).toContainText("提交中")
})
