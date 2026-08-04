import { mkdir } from "node:fs/promises"
import path from "node:path"
import { expect, type Page, test } from "@playwright/test"

const projectId = "00000000-0000-4000-8000-000000000401"
const datasetId = "00000000-0000-4000-8000-000000000402"
const versionId = "00000000-0000-4000-8000-000000000403"
const planId = "00000000-0000-4000-8000-000000000406"
const approvalId = "00000000-0000-4000-8000-000000000407"
const transformationId = "00000000-0000-4000-8000-000000000409"
const screenshotDir = path.resolve(
  process.env.RECA_M4_STAGE5_SCREENSHOT_DIR ??
    "../output/playwright/qa/m4-stage5",
)

async function authenticate(page: Page) {
  await page.addInitScript(() =>
    localStorage.setItem("access_token", "m4-production-route-token"),
  )
  await page.route("**/api/v1/users/me", (route) =>
    route.fulfill({
      json: {
        id: "00000000-0000-4000-8000-000000000404",
        email: "owner@example.com",
        is_active: true,
        is_superuser: false,
        full_name: "M4 Owner",
      },
    }),
  )
}

async function registerWorkspaceApi(page: Page, versionDatasetId = datasetId) {
  const meta = { request_id: "m4-route", schema_version: "1.0" }
  await page.route(`**/api/v1/projects/${projectId}`, (route) =>
    route.fulfill({
      json: {
        data: {
          id: projectId,
          allowed_actions: [
            "dataset.upload",
            "dataset.quality.run",
            "dataset.cleaning.plan",
          ],
        },
        meta,
      },
    }),
  )
  await page.route(`**/api/v1/projects/${projectId}/datasets*`, (route) =>
    route.fulfill({ json: { data: [dataset()], meta } }),
  )
  await page.route(`**/api/v1/datasets/${datasetId}`, (route) =>
    route.fulfill({ json: { data: dataset(), meta } }),
  )
  await page.route(`**/api/v1/datasets/${datasetId}/versions`, (route) =>
    route.fulfill({ json: { data: [version(versionDatasetId)], meta } }),
  )
  await page.route(`**/api/v1/dataset-versions/${versionId}`, (route) =>
    route.fulfill({
      json: { data: version(versionDatasetId), meta },
    }),
  )
  await page.route(`**/api/v1/dataset-versions/${versionId}/columns`, (route) =>
    route.fulfill({ json: { data: [column()], meta } }),
  )
  await page.route(
    `**/api/v1/dataset-versions/${versionId}/preview*`,
    (route) =>
      route.fulfill({
        json: {
          data: {
            version_id: versionId,
            offset: 0,
            limit: 20,
            columns: ["score"],
            rows: [{ score: 7 }],
            returned: 1,
            total_rows: 1,
            truncated: false,
          },
          meta,
        },
      }),
  )
  await page.route(`**/api/v1/cleaning-plans/${planId}`, (route) =>
    route.fulfill({
      json: {
        data: {
          id: planId,
          project_id: projectId,
          dataset_version_id: versionId,
          title: "Stage 5 plan",
          rationale: null,
          status: "READY",
          actions: [],
          preview_summary: {
            affected_row_count: 1,
            affected_column_count: 1,
            row_count_before: 1,
            row_count_after: 1,
            warnings: [],
            risk: "LOW",
            ready_for_approval: true,
          },
          preview_hash: "preview-hash",
          affected_row_count: 1,
          affected_column_count: 1,
          source_model_invocation_id: null,
          approval_record_id: approvalId,
          payload_hash: "payload-hash",
          lock_version: 2,
          transformation_id: transformationId,
          job_id: null,
          created_at: "2026-08-04T00:00:00Z",
          updated_at: "2026-08-04T00:00:00Z",
          allowed_actions: ["cleaning_plan.request_approval"],
        },
        meta,
      },
    }),
  )
  await page.route(`**/api/v1/approvals/${approvalId}`, (route) =>
    route.fulfill({
      json: {
        data: {
          id: approvalId,
          project_id: projectId,
          approval_type: "DATA_CLEANING",
          target_object_type: "cleaning_plan",
          target_object_id: planId,
          requester: {
            user_id: "00000000-0000-4000-8000-000000000404",
            display_name: "M4 Owner",
          },
          requested_at: "2026-08-04T00:00:00Z",
          status: "PENDING",
          decision: null,
          payload_hash: "payload-hash",
          payload_snapshot: null,
          impact_summary: null,
          expires_at: null,
          allowed_actions: ["approval.approve"],
        },
        meta,
      },
    }),
  )
  await page.route(
    `**/api/v1/data-transformations/${transformationId}`,
    (route) =>
      route.fulfill({
        json: {
          data: {
            id: transformationId,
            project_id: projectId,
            cleaning_plan_id: planId,
            approval_record_id: approvalId,
            source_dataset_version_id: versionId,
            target_dataset_version_id: null,
            status: "RUNNING",
            action_count: 1,
            affected_row_count: null,
            affected_column_count: null,
            parameters_hash: "parameters-hash",
            output_artifact_id: null,
            processing_run_id: null,
            started_at: "2026-08-04T00:01:00Z",
            completed_at: null,
            error_code: null,
            created_at: "2026-08-04T00:01:00Z",
          },
          meta,
        },
      }),
  )
}

function dataset() {
  return {
    id: datasetId,
    project_id: projectId,
    name: "Stage 5 dataset",
    description: null,
    source_type: "UPLOAD",
    publisher: null,
    source_platform: null,
    source_identifier: null,
    doi: null,
    acquired_at: null,
    license_name: null,
    license_status: "UNKNOWN",
    license_warning: null,
    recommended_citation: null,
    known_limitations: null,
    current_version_id: versionId,
    status: "ACTIVE",
    lock_version: 1,
    permissions: {
      can_update: true,
      can_upload: true,
      can_confirm_columns: true,
    },
    created_at: "2026-08-04T00:00:00Z",
    updated_at: "2026-08-04T00:00:00Z",
  }
}

function version(dataset: string) {
  return {
    id: versionId,
    project_id: projectId,
    dataset_id: dataset,
    version_number: 1,
    parent_version_id: null,
    artifact_id: "00000000-0000-4000-8000-000000000405",
    version_type: "ORIGINAL",
    row_count: 1,
    column_count: 1,
    file_format: "CSV",
    worksheet_manifest: null,
    selected_worksheet_name: null,
    projection_hash: "projection-hash",
    schema_hash: "schema-hash",
    data_hash: "data-hash",
    transformation_id: null,
    status: "AVAILABLE",
    created_at: "2026-08-04T00:00:00Z",
    invalidated_at: null,
    invalidation_reason: null,
  }
}

function column() {
  return {
    id: "00000000-0000-4000-8000-000000000408",
    project_id: projectId,
    dataset_version_id: versionId,
    source_name: "score",
    display_name: null,
    column_order: 0,
    inferred_type: "INTEGER",
    confirmed_type: "INTEGER",
    semantic_role: null,
    unit: null,
    description: null,
    missing_codes: null,
    category_mapping: null,
    is_identifier: false,
    is_sensitive: false,
    confirmation_status: "UNCONFIRMED",
    unique_count: 1,
    missing_ratio: 0,
    example_values: [7],
    inherited_from_column_id: null,
    lock_version: 1,
    created_at: "2026-08-04T00:00:00Z",
    updated_at: "2026-08-04T00:00:00Z",
  }
}

test("M4 production data route restores deep links and view changes", async ({
  page,
}) => {
  await authenticate(page)
  await registerWorkspaceApi(page)
  const url = `/projects/${projectId}/data?dataset=${datasetId}&version=${versionId}&view=versions`
  await page.goto(url)
  await expect(page.locator('[data-od-id="m4-data-workspace"]')).toBeVisible()
  await expect(
    page.locator('.m4-view-content[data-view="versions"]'),
  ).toBeVisible()
  await expect(page.getByLabel("正式版本历史")).toContainText("版本 1")

  await page.locator('[data-od-id="workspace-tabs"] button').first().click()
  await expect(page).toHaveURL(/view=data/)
  await page.reload()
  await expect(page.locator('.m4-view-content[data-view="data"]')).toBeVisible()
})

test("M4 production data route rejects a cross-dataset version", async ({
  page,
}) => {
  await authenticate(page)
  await registerWorkspaceApi(page, "00000000-0000-4000-8000-000000000499")
  await page.goto(
    `/projects/${projectId}/data?dataset=${datasetId}&version=${versionId}`,
  )
  await expect(page.getByRole("alert")).toContainText(
    "does not belong to the selected Dataset",
  )
  await expect(page.locator('[data-od-id="m4-data-workspace"]')).toHaveCount(0)
})

test("M4 approval-only deep link restores its Plan and DatasetVersion", async ({
  page,
}) => {
  await authenticate(page)
  await registerWorkspaceApi(page)
  await page.goto(
    `/projects/${projectId}/data?approval=${approvalId}&view=cleaning`,
  )
  await expect(page.locator('[data-od-id="m4-data-workspace"]')).toBeVisible()
  await expect(
    page.locator('.m4-view-content[data-view="cleaning"]'),
  ).toBeVisible()
  await expect(
    page.locator('[data-od-id="approval-status-panel"]'),
  ).toContainText("PENDING")
  await expect(
    page.locator('[data-od-id="transformation-result-panel"]'),
  ).toContainText("RUNNING")
  await page.reload()
  await expect(
    page.locator('[data-od-id="approval-status-panel"]'),
  ).toContainText("PENDING")
})

test("M4 field confirmation sends the formal confirmation status", async ({
  page,
}) => {
  await authenticate(page)
  await registerWorkspaceApi(page)
  let requestBody: Record<string, unknown> | null = null
  await page.route(
    "**/api/v1/dataset-columns/00000000-0000-4000-8000-000000000408",
    async (route) => {
      requestBody = route.request().postDataJSON() as Record<string, unknown>
      await route.fulfill({
        json: {
          data: {
            ...column(),
            confirmation_status: "CONFIRMED",
            lock_version: 2,
          },
          meta: { request_id: "confirm-column", schema_version: "1.0" },
        },
      })
    },
  )
  await page.goto(
    `/projects/${projectId}/data?dataset=${datasetId}&version=${versionId}&view=columns`,
  )
  await page.locator(".m4-column-name").click()
  await page.getByLabel("Confirm field definition").check()
  await page.locator(".m4-inspector-form").last().getByRole("button").click()
  await expect.poll(() => requestBody?.confirmation_status).toBe("CONFIRMED")
})

test("M4 production route keeps 390px Light and Dark surfaces bounded", async ({
  page,
}) => {
  await mkdir(screenshotDir, { recursive: true })
  await page.setViewportSize({ width: 390, height: 844 })
  await authenticate(page)
  await registerWorkspaceApi(page)
  await page.goto(
    `/projects/${projectId}/data?dataset=${datasetId}&version=${versionId}&view=columns`,
  )
  const workspace = page.locator('[data-od-id="m4-data-workspace"]')
  await expect(workspace).toBeVisible()
  await expect
    .poll(() =>
      page.evaluate(() => document.documentElement.classList.contains("dark")),
    )
    .toBe(true)
  const darkSurface = await page.evaluate(
    () => getComputedStyle(document.body).backgroundColor,
  )
  expect(
    await page.evaluate(
      () =>
        document.documentElement.scrollWidth -
        document.documentElement.clientWidth,
    ),
  ).toBe(0)
  await page.screenshot({
    path: path.join(screenshotDir, "production-route-mobile-dark.png"),
    fullPage: true,
  })

  await page.evaluate(() => localStorage.setItem("vite-ui-theme", "light"))
  await page.reload()
  await expect(workspace).toBeVisible()
  await expect
    .poll(() =>
      page.evaluate(() => document.documentElement.classList.contains("dark")),
    )
    .toBe(false)
  const lightSurface = await page.evaluate(
    () => getComputedStyle(document.body).backgroundColor,
  )
  expect(lightSurface).not.toBe(darkSurface)
  expect(
    await page.evaluate(
      () =>
        document.documentElement.scrollWidth -
        document.documentElement.clientWidth,
    ),
  ).toBe(0)
  await page.screenshot({
    path: path.join(screenshotDir, "production-route-mobile-light.png"),
    fullPage: true,
  })
})
