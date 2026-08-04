import { expect, type Page, test } from "@playwright/test"

const ownerEmail = process.env.M3_STAGE7_OWNER_EMAIL ?? ""
const ownerPassword = process.env.M3_STAGE7_OWNER_PASSWORD ?? ""
const projectId = process.env.M3_STAGE7_PROJECT_ID ?? ""
const documentId = process.env.M3_STAGE7_DOCUMENT_ID ?? ""
const extractionId = process.env.M3_STAGE7_EXTRACTION_ID ?? ""
const fieldId = process.env.M3_STAGE7_FIELD_ID ?? ""
const evidenceSpanId = process.env.M3_STAGE7_EVIDENCE_SPAN_ID ?? ""
const summaryId = process.env.M3_STAGE7_SUMMARY_ID ?? ""
const topicRunId = process.env.M3_STAGE7_TOPIC_RUN_ID ?? ""

const configured = [
  ownerEmail,
  ownerPassword,
  projectId,
  documentId,
  extractionId,
  fieldId,
  evidenceSpanId,
  summaryId,
  topicRunId,
].every(Boolean)

async function login(page: Page) {
  await page.goto("/login")
  await page.getByTestId("email-input").fill(ownerEmail)
  await page.getByTestId("password-input").fill(ownerPassword)
  await page.getByRole("button", { name: /log in/i }).click()
  await expect(page).not.toHaveURL(/\/login$/)
}

test("real M3 matrix to PDF, review, analysis and exactly-three topic chain", async ({
  page,
}) => {
  test.skip(
    !configured,
    "Requires a fresh Stage 7 PostgreSQL/API fixture and formal topic read projection.",
  )
  test.setTimeout(120_000)
  await login(page)

  const route = new URLSearchParams({
    view: "matrix",
    documentId,
    extractionId,
    fieldId,
    evidenceSpanId,
    summaryId,
    topicRunId,
  })
  await page.goto(`/projects/${projectId}/literature?${route}`)
  await expect(
    page.getByRole("heading", { name: "Evidence Matrix" }),
  ).toBeVisible()
  await expect(page.locator(".m3-pdf-canvas-wrap canvas")).toBeVisible()
  await expect(page.locator(".m3-pdf-highlight")).toHaveCount(1)
  await page.reload()
  await expect(page).toHaveURL(new RegExp(`extractionId=${extractionId}`))
  await expect(page.locator(".m3-pdf-highlight")).toHaveCount(1)

  await page.getByLabel("Field value").fill("312")
  await page
    .getByLabel("Correction reason")
    .fill("Stage 7 review of the exact server source text.")
  await page.getByRole("button", { name: "Correct" }).click()
  await expect(page.getByLabel("Field value")).toHaveValue("312")
  await page.getByRole("button", { name: "Confirm" }).click()
  await page.getByRole("button", { name: "Verify location" }).click()
  await page.getByRole("button", { name: "Include", exact: true }).click()
  await expect(
    page.getByText("INCLUDED", { exact: true }).first(),
  ).toBeVisible()

  await page.getByRole("button", { name: "Evidence analysis" }).click()
  await expect(
    page.getByRole("heading", { name: "Current Evidence Analysis" }),
  ).toBeVisible()
  await expect(
    page.getByText(/current included literature set/i).first(),
  ).toBeVisible()
  await expect(page.getByText("Counterexample", { exact: true })).toBeVisible()

  await page.getByRole("button", { name: "Topic candidates" }).click()
  await expect(
    page.getByRole("heading", { name: "Topic Candidates" }),
  ).toBeVisible()
  await expect(page.locator(".m3-topic-candidate")).toHaveCount(3)
  await expect(page.getByText(/padded|truncated/i)).toHaveCount(0)
})
