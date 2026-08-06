import { expect, test } from "@playwright/test"

const frontendUrl = process.env.RECA_M7_REAL_FRONTEND_URL
const apiUrl = process.env.RECA_M7_REAL_API_URL
const projectId = process.env.RECA_M7_REAL_PROJECT_ID
const claimId = process.env.RECA_M7_REAL_CLAIM_ID
const accessToken = process.env.RECA_M7_REAL_ACCESS_TOKEN

test.skip(
  !frontendUrl || !apiUrl || !projectId || !claimId || !accessToken,
  "Real M7 API acceptance requires an isolated seeded Compose environment.",
)

test("M7 production workspace completes the real Claim to ReproPackage chain", async ({
  page,
  request,
}) => {
  page.on("requestfailed", (failedRequest) => {
    console.log(
      `browser request failed: ${failedRequest.method()} ${failedRequest.url()} ${failedRequest.failure()?.errorText ?? "unknown"}`,
    )
  })
  await page.addInitScript((token) => {
    localStorage.setItem("access_token", token)
  }, accessToken)
  await page.goto(
    `${frontendUrl}/projects/${projectId}/evidence?claim=${claimId}&view=graph`,
  )

  await expect(page.locator('[data-od-id="evidence-workspace"]')).toBeVisible()
  await expect(page.locator(".react-flow__node")).toHaveCount(1)
  await expect(page.locator(".react-flow__handle.connectable")).toHaveCount(0)

  await page.locator(".m7-view-tabs button").nth(3).click()
  const exportActions = page
    .locator(".m7-form-actions")
    .first()
    .locator("button")
  await expect(exportActions.nth(0)).toBeEnabled()
  await exportActions.nth(0).click()
  await expect(page.locator(".m7-readiness-issues")).toBeVisible()
  await expect(exportActions.nth(1)).toBeEnabled()
  await exportActions.nth(1).click()

  await expect(page).toHaveURL(/(?:\?|&)export=[0-9a-f-]+/)
  const exportId = new URL(page.url()).searchParams.get("export")
  expect(exportId).toBeTruthy()

  const confirmationButton = page
    .locator(".m7-form-actions--chain")
    .locator("button")
    .first()
  await expect(confirmationButton).toBeEnabled()
  await confirmationButton.click()
  const submitConfirmation = page.getByRole("button", {
    name: "提交确认意图",
    exact: true,
  })
  await expect(submitConfirmation).toBeEnabled()
  const approvalResponse = await Promise.all([
    page.waitForResponse(
      (response) =>
        response.request().method() === "POST" &&
        response.url().includes("/approvals/") &&
        response.url().endsWith("/approve"),
    ),
    submitConfirmation.click(),
  ]).then(([response]) => response)
  expect(approvalResponse.ok()).toBeTruthy()

  await expect
    .poll(
      async () => {
        const response = await request.get(
          `${apiUrl}/api/v1/exports/${exportId}`,
          {
            headers: { Authorization: `Bearer ${accessToken}` },
          },
        )
        expect(response.ok()).toBeTruthy()
        return (await response.json()).data.status
      },
      { timeout: 90_000 },
    )
    .toBe("COMPLETED")

  const packages = await request.get(
    `${apiUrl}/api/v1/projects/${projectId}/repro-packages?page=1&page_size=10`,
    { headers: { Authorization: `Bearer ${accessToken}` } },
  )
  expect(packages.ok()).toBeTruthy()
  const packageRows = (await packages.json()).data as Array<{ id: string }>
  expect(packageRows).toHaveLength(1)
  const packageId = packageRows[0].id

  await page.goto(
    `${frontendUrl}/projects/${projectId}/evidence?claim=${claimId}&export=${exportId}&package=${packageId}&view=exports`,
  )
  await expect(page.locator(".m7-package-history article")).toHaveCount(1)
  await expect(
    page.locator('.m7-package-history article[aria-current="true"]'),
  ).toHaveCount(1)

  const downloadButton = page
    .locator(".m7-stage-panel")
    .last()
    .locator(".m7-form-actions button")
    .last()
  await expect(downloadButton).toBeEnabled()
  const authorizedDownload = await request.get(
    `${apiUrl}/api/v1/repro-packages/${packageId}/download`,
    { headers: { Authorization: `Bearer ${accessToken}` } },
  )
  expect(authorizedDownload.ok()).toBeTruthy()
  const downloadUrl = (await authorizedDownload.json()).data.download
    .download_url as string
  const objectResponse = await request.get(downloadUrl)
  expect(objectResponse.ok()).toBeTruthy()
  expect((await objectResponse.body()).byteLength).toBeGreaterThan(0)

  const browserObjectResponse = await Promise.all([
    page.waitForResponse(
      (response) =>
        response.url().startsWith(downloadUrl.split("?")[0]) &&
        response.request().method() === "GET",
    ),
    downloadButton.click(),
  ]).then(([response]) => response)
  expect(browserObjectResponse.ok()).toBeTruthy()
})
