import { expect, test } from "@playwright/test"

test("renders a 500-node controlled graph and disables connect persistence", async ({
  page,
}) => {
  await page.goto("/tests/spikes/m7-react-flow-spike.html")
  await expect(page.getByTestId("flow-spike")).toBeVisible()
  await expect(page.locator(".react-flow__node")).toHaveCount(500)
  await expect(page.locator(".react-flow__edge")).toHaveCount(499)
  await expect(page.getByTestId("claim-node")).toHaveCount(500)
  await expect(page.locator(".react-flow__handle.connectable")).toHaveCount(0)
  await page
    .locator(".react-flow__node")
    .first()
    .evaluate((node) => (node as HTMLElement).click())
  await expect(page.locator(".react-flow__node.selected")).toHaveCount(1)

  const metrics = await page.evaluate(() => ({
    heap: performance.memory?.usedJSHeapSize ?? 0,
    transfer: performance
      .getEntriesByType("resource")
      .reduce(
        (sum, entry) => sum + (entry as PerformanceResourceTiming).transferSize,
        0,
      ),
  }))
  expect(metrics.heap).toBeLessThan(256 * 1024 * 1024)
  expect(metrics.transfer).toBeLessThan(5 * 1024 * 1024)
})

test("supports keyboard focus and a narrow viewport without overflow", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto("/tests/spikes/m7-react-flow-spike.html")
  await expect(page.getByTestId("mobile-table")).toBeVisible()
  await expect(page.getByTestId("flow-spike")).toBeHidden()
  await expect(page.locator("body")).toHaveJSProperty("scrollWidth", 390)
})
