import { expect, type Locator, type Page, test } from "@playwright/test"
import { QueryClient } from "@tanstack/react-query"

import type {
  DocumentPagePublic,
  DocumentPublic,
  JobPublic,
  ProjectPublic,
} from "../src/api/adapter"
import { invalidateDocumentMutation } from "../src/features/documents/mutations"
import { documentKeys } from "../src/features/documents/queries"
import type { DocumentEvent } from "../src/features/documents/ui/contracts"
import { literatureKeys } from "../src/features/literature/queries"
import { createDeferred } from "./utils/deferred"

const meta = { request_id: "request-document", schema_version: "1.0" }

test.use({ viewport: { width: 1440, height: 900 } })

function project(overrides: Partial<ProjectPublic> = {}): ProjectPublic {
  return {
    id: "project-1",
    owner_id: "user-1",
    name: "Document project",
    description: null,
    discipline: null,
    research_direction: null,
    project_type: "RESEARCH",
    current_stage: "LITERATURE",
    status: "ACTIVE",
    expected_completion_date: null,
    resource_constraints: null,
    ethical_constraints: null,
    lock_version: 1,
    created_at: "2026-08-01T00:00:00Z",
    updated_at: "2026-08-01T00:00:00Z",
    permissions: { can_update: true, can_delete: true },
    allowed_actions: ["project.read", "job.read", "job.retry"],
    ...overrides,
  }
}

function document(overrides: Partial<DocumentPublic> = {}): DocumentPublic {
  return {
    id: "document-1",
    project_id: "project-1",
    artifact_id: "artifact-1",
    literature_record_id: null,
    document_type: "SCHOLARLY_PDF",
    parser_type: "NONE",
    parser_version: null,
    parse_status: "DRAFT",
    page_count: null,
    language: null,
    is_scanned: false,
    parse_confidence: "UNKNOWN",
    created_at: "2026-08-01T04:00:00Z",
    updated_at: "2026-08-01T04:00:00Z",
    allowed_actions: ["document.read", "document.upload", "document.parse"],
    ...overrides,
  }
}

function page(
  pageNumber: number,
  overrides: Partial<DocumentPagePublic> = {},
): DocumentPagePublic {
  return {
    document_id: "document-1",
    project_id: "project-1",
    page_number: pageNumber,
    printed_page_label: String(pageNumber),
    text_content: `Server page ${pageNumber} text.`,
    width: 612,
    height: 792,
    parser_metadata: { parser: "GROBID" },
    created_at: "2026-08-01T04:10:00Z",
    ...overrides,
  }
}

function job(overrides: Partial<JobPublic> = {}): JobPublic {
  return {
    id: "job-1",
    project_id: "project-1",
    task_type: "DOCUMENT_PARSE",
    resource_type: "document",
    resource_id: "document-1",
    status: "COMPLETED",
    progress_percent: 100,
    current_step: "Completed",
    total_steps: 4,
    completed_steps: 4,
    retry_count: 0,
    max_retries: 1,
    retryable: false,
    current_processing_run_id: null,
    created_at: "2026-08-01T04:01:00Z",
    started_at: "2026-08-01T04:01:10Z",
    completed_at: "2026-08-01T04:10:00Z",
    error: null,
    result: null,
    ...overrides,
  }
}

async function authenticate(page: Page) {
  await page.addInitScript(() =>
    localStorage.setItem("access_token", "test-token"),
  )
  await page.route("**/api/v1/users/me", (route) =>
    route.fulfill({
      json: {
        id: "user-1",
        email: "owner@example.com",
        is_active: true,
        is_superuser: false,
        full_name: "Owner",
      },
    }),
  )
}

async function routeProject(page: Page, value: () => object = () => project()) {
  await page.route("**/api/v1/projects/project-1", (route) =>
    route.fulfill({ json: { data: value(), meta } }),
  )
}

async function openDetails(page: Page): Promise<Locator> {
  const trigger = page.getByRole("button", { name: "详情" })
  if (await trigger.isVisible()) {
    await trigger.click()
  }
  const inspector = page.locator(".document-inspector:visible").last()
  await expect(inspector).toBeVisible()
  return inspector
}

test("Document deep link and refresh preserve formal document and job identifiers", async ({
  page: browserPage,
}) => {
  await authenticate(browserPage)
  await routeProject(browserPage)
  let detailLoads = 0
  let jobLoads = 0
  await browserPage.route("**/api/v1/documents/document-1**", (route) => {
    const path = new URL(route.request().url()).pathname
    if (path.endsWith("/pages")) {
      return route.fulfill({ json: { data: [page(1)], meta } })
    }
    detailLoads += 1
    return route.fulfill({
      json: {
        data: document({
          parser_type: "GROBID",
          parse_status: "COMPLETED",
          parse_confidence: "HIGH",
          page_count: 1,
          language: "en",
          allowed_actions: ["document.read", "document.upload"],
        }),
        meta,
      },
    })
  })
  await browserPage.route("**/api/v1/jobs/job-1", (route) => {
    jobLoads += 1
    return route.fulfill({ json: { data: job(), meta } })
  })

  await browserPage.goto("/projects/project-1/documents/document-1?jobId=job-1")
  const workspace = browserPage.locator(".document-workspace")
  await expect(workspace).toBeVisible()
  await expect(browserPage).toHaveURL(/document-1\?jobId=job-1/)
  await expect(workspace.getByText("解析完成").first()).toBeVisible()
  await expect(workspace.getByText("GROBID 结构化解析").first()).toBeVisible()
  await expect(workspace.getByText("Server page 1 text.")).toBeVisible()

  await browserPage.reload()
  await expect(workspace).toBeVisible()
  await expect.poll(() => detailLoads).toBe(2)
  await expect.poll(() => jobLoads).toBe(2)
})

test("PDF upload navigates to the server Document without claiming parse success", async ({
  page: browserPage,
}) => {
  await authenticate(browserPage)
  await routeProject(browserPage)
  let currentId = "document-1"
  const uploadRequest = createDeferred()
  await browserPage.route(
    "**/api/v1/projects/project-1/documents",
    async (route) => {
      expect(route.request().headers()["idempotency-key"]).toBeTruthy()
      expect(route.request().headers()["content-type"]).toContain(
        "multipart/form-data",
      )
      await uploadRequest.promise
      currentId = "document-2"
      return route.fulfill({
        status: 201,
        json: {
          data: {
            artifact: { id: "artifact-2" },
            document: document({
              id: "document-2",
              artifact_id: "artifact-2",
              literature_record_id: "record-1",
            }),
          },
          meta,
        },
      })
    },
  )
  await browserPage.route("**/api/v1/documents/document-**", (route) => {
    const path = new URL(route.request().url()).pathname
    const pathSegments = path.split("/")
    const id = pathSegments[pathSegments.length - 1]!
    if (path.endsWith("/pages")) {
      return route.fulfill({ json: { data: [], meta } })
    }
    return route.fulfill({
      json: {
        data: document({
          id,
          artifact_id: id === "document-2" ? "artifact-2" : "artifact-1",
          literature_record_id: id === "document-2" ? "record-1" : null,
        }),
        meta,
      },
    })
  })

  await browserPage.goto("/projects/project-1/documents/document-1")
  await browserPage.getByRole("button", { name: "上传" }).click()
  await browserPage
    .locator('.document-upload-panel input[type="file"]')
    .setInputFiles("tests/fixtures/minimal.pdf")
  await browserPage.getByPlaceholder("仅随上传意图提交").fill("record-1")
  const submit = browserPage.locator(".document-upload-actions button")
  await submit.click()
  await expect(submit).toBeDisabled()
  await expect(browserPage.getByText("草稿").first()).toBeVisible()
  uploadRequest.resolve()
  await expect(browserPage).toHaveURL(/documents\/document-2$/)
  await expect(browserPage.getByText("草稿").first()).toBeVisible()
  await expect(browserPage.getByText("record-1", { exact: true })).toBeVisible()
  expect(currentId).toBe("document-2")
})

test("Parse remains queued and running until refreshed GROBID completion and pages arrive", async ({
  page: browserPage,
}) => {
  await authenticate(browserPage)
  await routeProject(browserPage)
  let status: DocumentPublic["parse_status"] = "DRAFT"
  const parseRequest = createDeferred()
  await browserPage.route("**/api/v1/documents/document-1**", async (route) => {
    const request = route.request()
    const path = new URL(request.url()).pathname
    if (path.endsWith("/parse")) {
      expect(request.headers()["idempotency-key"]).toBeTruthy()
      expect(request.postDataJSON()).toEqual({
        allow_fallback: true,
        extract_coordinates: true,
      })
      await parseRequest.promise
      status = "QUEUED"
      return route.fulfill({
        status: 202,
        json: { data: job({ status: "QUEUED", progress_percent: 0 }), meta },
      })
    }
    if (path.endsWith("/pages")) {
      return route.fulfill({
        json: {
          data:
            status === "COMPLETED"
              ? [
                  page(1),
                  page(2, { text_content: "Methods from server page 2." }),
                ]
              : [],
          meta,
        },
      })
    }
    return route.fulfill({
      json: {
        data: document(
          status === "COMPLETED"
            ? {
                parse_status: status,
                parser_type: "GROBID",
                parser_version: "0.8.2",
                parse_confidence: "HIGH",
                page_count: 2,
                language: "en",
                allowed_actions: ["document.read", "document.upload"],
              }
            : {
                parse_status: status,
                allowed_actions:
                  status === "DRAFT"
                    ? ["document.read", "document.upload", "document.parse"]
                    : ["document.read", "document.upload"],
              },
        ),
        meta,
      },
    })
  })
  await browserPage.route("**/api/v1/jobs/job-1", (route) =>
    route.fulfill({
      json: {
        data: job({
          status,
          progress_percent:
            status === "QUEUED" ? 0 : status === "RUNNING" ? 55 : 100,
          current_step: status,
        }),
        meta,
      },
    }),
  )

  await browserPage.goto("/projects/project-1/documents/document-1")
  const inspector = await openDetails(browserPage)
  await inspector.getByText("允许 fallback").click()
  await inspector.getByText("提取坐标").click()
  if (await browserPage.getByRole("dialog").isVisible()) {
    await browserPage.keyboard.press("Escape")
  }
  const parse = browserPage.locator(
    ".reca-workspace-header__actions .document-button--primary",
  )
  await parse.click()
  await expect(parse).toBeDisabled()
  await expect(parse).toContainText("正在提交")
  await expect(browserPage.getByText("草稿").first()).toBeVisible()
  parseRequest.resolve()
  await expect(browserPage).toHaveURL(/jobId=job-1/)
  await expect(browserPage.getByText("等待解析").first()).toBeVisible()

  status = "RUNNING"
  await browserPage.reload()
  await expect(browserPage.getByText("解析中").first()).toBeVisible()

  status = "COMPLETED"
  await browserPage.reload()
  await expect(browserPage.getByText("解析完成").first()).toBeVisible()
  await expect(browserPage.getByText("GROBID 结构化解析").first()).toBeVisible()
  await expect(browserPage.getByText("HIGH", { exact: true })).toBeVisible()
  await expect(browserPage.getByText("Server page 1 text.")).toBeVisible()
  await browserPage.getByRole("button", { name: "下一页" }).click()
  await expect(
    browserPage.getByText("Methods from server page 2."),
  ).toBeVisible()
})

test("pypdf fallback and scanned output remain LOW confidence degraded projections", async ({
  page: browserPage,
}) => {
  await authenticate(browserPage)
  await routeProject(browserPage)
  await browserPage.route("**/api/v1/documents/document-1**", (route) => {
    const path = new URL(route.request().url()).pathname
    if (path.endsWith("/pages")) {
      return route.fulfill({
        json: {
          data: [page(1, { text_content: "Limited fallback page text." })],
          meta,
        },
      })
    }
    return route.fulfill({
      json: {
        data: document({
          parser_type: "PYPDF",
          parser_version: "6.14.2",
          parse_status: "COMPLETED",
          parse_confidence: "LOW",
          page_count: 1,
          is_scanned: true,
          allowed_actions: ["document.read", "document.upload"],
        }),
        meta,
      },
    })
  })

  await browserPage.goto("/projects/project-1/documents/document-1")
  await expect(browserPage.getByText("pypdf fallback").first()).toBeVisible()
  await expect(
    browserPage.getByText("正在显示 pypdf fallback 结果"),
  ).toBeVisible()
  await expect(browserPage.getByText("扫描型 PDF")).toBeVisible()
  const inspector = await openDetails(browserPage)
  await expect(inspector.getByText("LOW", { exact: true })).toBeVisible()
  await expect(inspector.getByText("是 · 文本可能有限")).toBeVisible()
})

test("Failed retryable, encrypted, and corrupt Jobs obey formal retry gates", async ({
  page: browserPage,
}) => {
  await authenticate(browserPage)
  let failure: "retryable" | "encrypted" | "corrupt" = "retryable"
  let permissionKnown = true
  await routeProject(browserPage, () => {
    const value = project()
    if (permissionKnown) return value
    const { allowed_actions: _allowedActions, ...withoutActions } = value
    return withoutActions
  })
  await browserPage.route("**/api/v1/documents/document-1**", (route) => {
    const path = new URL(route.request().url()).pathname
    if (path.endsWith("/pages")) {
      return route.fulfill({ json: { data: [], meta } })
    }
    return route.fulfill({
      json: {
        data: document({
          parse_status: "FAILED",
          allowed_actions: [
            "document.read",
            "document.upload",
            "document.parse",
          ],
        }),
        meta,
      },
    })
  })
  await browserPage.route("**/api/v1/jobs/job-1**", async (route) => {
    if (route.request().method() === "POST") {
      expect(route.request().headers()["idempotency-key"]).toBeTruthy()
      return route.fulfill({
        json: { data: job({ status: "QUEUED", retryable: false }), meta },
      })
    }
    const retryable = failure === "retryable"
    const code =
      failure === "encrypted"
        ? "PDF_ENCRYPTED"
        : failure === "corrupt"
          ? "PDF_CORRUPT"
          : "GROBID_TIMEOUT"
    return route.fulfill({
      json: {
        data: job({
          status: "FAILED",
          retryable,
          error: { code, message: `${code} server failure.`, retryable },
        }),
        meta,
      },
    })
  })

  await browserPage.goto("/projects/project-1/documents/document-1?jobId=job-1")
  let inspector = await openDetails(browserPage)
  let retry = inspector.getByRole("button", { name: "重试解析" })
  await expect(retry).toBeEnabled()
  await expect(
    inspector.getByText(/GROBID_TIMEOUT server failure/),
  ).toBeVisible()

  failure = "encrypted"
  await browserPage.reload()
  inspector = await openDetails(browserPage)
  retry = inspector.getByRole("button", { name: "重试解析" })
  await expect(retry).toBeDisabled()
  await expect(inspector.getByText(/PDF_ENCRYPTED/)).toBeVisible()

  failure = "corrupt"
  permissionKnown = false
  await browserPage.reload()
  inspector = await openDetails(browserPage)
  retry = inspector.getByRole("button", { name: "重试解析" })
  await expect(retry).toBeDisabled()
  await expect(inspector.getByText(/PDF_CORRUPT/)).toBeVisible()
  await expect(inspector.getByText(/retry permission is unknown/)).toBeVisible()
})

test("Read-only, permissions unknown, and unknown status keep Document writes closed", async ({
  page: browserPage,
}) => {
  await authenticate(browserPage)
  await routeProject(browserPage)
  let mode: "read-only" | "permissions-unknown" | "unknown" = "read-only"
  await browserPage.route("**/api/v1/documents/document-1**", (route) => {
    const path = new URL(route.request().url()).pathname
    if (path.endsWith("/pages")) {
      return route.fulfill({ json: { data: [], meta } })
    }
    const value = document(
      mode === "unknown"
        ? {
            parse_status:
              "FUTURE_DOCUMENT_STATE" as DocumentPublic["parse_status"],
          }
        : { allowed_actions: ["document.read"] },
    )
    if (mode !== "permissions-unknown") {
      return route.fulfill({ json: { data: value, meta } })
    }
    const { allowed_actions: _allowedActions, ...withoutActions } = value
    return route.fulfill({ json: { data: withoutActions, meta } })
  })

  await browserPage.goto("/projects/project-1/documents/document-1")
  await expect(browserPage.getByRole("button", { name: "上传" })).toBeDisabled()
  await expect(
    browserPage.getByRole("button", { name: "开始解析" }),
  ).toBeDisabled()

  mode = "permissions-unknown"
  await browserPage.reload()
  await expect(browserPage.getByText("状态或权限尚未确认")).toBeVisible()
  await expect(browserPage.getByRole("button", { name: "上传" })).toBeDisabled()

  mode = "unknown"
  await browserPage.reload()
  await expect(browserPage.getByText("未知解析状态").first()).toBeVisible()
  await expect(
    browserPage.getByRole("button", { name: "开始解析" }),
  ).toBeDisabled()
})

test("Document page Sheet manages keyboard focus and restores its trigger", async ({
  page: browserPage,
}) => {
  await browserPage.setViewportSize({ width: 1024, height: 768 })
  await authenticate(browserPage)
  await routeProject(browserPage)
  await browserPage.route("**/api/v1/documents/document-1**", (route) => {
    const path = new URL(route.request().url()).pathname
    if (path.endsWith("/pages")) {
      return route.fulfill({ json: { data: [page(1), page(2)], meta } })
    }
    return route.fulfill({
      json: {
        data: document({
          parser_type: "GROBID",
          parse_status: "COMPLETED",
          parse_confidence: "HIGH",
          page_count: 2,
          allowed_actions: ["document.read", "document.upload"],
        }),
        meta,
      },
    })
  })

  await browserPage.goto("/projects/project-1/documents/document-1")
  const trigger = browserPage.getByRole("button", { name: "页面" })
  await trigger.click()
  const dialog = browserPage.getByRole("dialog")
  await expect(dialog).toBeVisible()
  await expect(
    browserPage.getByRole("heading", { name: "页面导航" }),
  ).toBeFocused()
  await browserPage.keyboard.press("Shift+Tab")
  await expect(dialog.locator(":focus")).toHaveCount(1)
  await browserPage.keyboard.press("Escape")
  await expect(dialog).toBeHidden()
  await expect(trigger).toBeFocused()
})

test("Document mutation invalidation stays resource exact", async () => {
  const upload: DocumentEvent = {
    action: "upload",
    input: {
      file: new File(["%PDF-1.4"], "minimal.pdf", {
        type: "application/pdf",
      }),
      documentType: "SCHOLARLY_PDF",
      literatureRecordId: "record-1",
    },
  }
  const parse: DocumentEvent = {
    action: "parse",
    input: {
      documentId: "document-1",
      allowFallback: true,
      extractCoordinates: true,
    },
  }
  const retry: DocumentEvent = {
    action: "retry-job",
    input: { jobId: "job-1" },
  }
  const client = new QueryClient()
  const keys = [
    documentKeys.detail("project-1", "document-1"),
    documentKeys.detail("project-1", "document-2"),
    documentKeys.detail("project-2", "document-1"),
    documentKeys.pages("document-1"),
    documentKeys.pages("document-2"),
    documentKeys.job("job-1"),
    literatureKeys.records("project-1"),
  ] as const
  keys.forEach((key) => client.setQueryData(key, {}))

  await invalidateDocumentMutation(client, "project-1", "document-1", upload, {
    action: "upload",
    documentId: "document-2",
  })
  expect(
    client.getQueryState(documentKeys.detail("project-1", "document-2"))
      ?.isInvalidated,
  ).toBe(true)
  expect(
    client.getQueryState(documentKeys.pages("document-2"))?.isInvalidated,
  ).toBe(true)
  expect(
    client.getQueryState(literatureKeys.records("project-1"))?.isInvalidated,
  ).toBe(true)
  expect(
    client.getQueryState(documentKeys.detail("project-1", "document-1"))
      ?.isInvalidated,
  ).toBe(false)

  await invalidateDocumentMutation(client, "project-1", "document-1", parse, {
    action: "parse",
    jobId: "job-1",
  })
  expect(
    client.getQueryState(documentKeys.detail("project-1", "document-1"))
      ?.isInvalidated,
  ).toBe(true)
  expect(
    client.getQueryState(documentKeys.pages("document-1"))?.isInvalidated,
  ).toBe(true)
  expect(client.getQueryState(documentKeys.job("job-1"))?.isInvalidated).toBe(
    true,
  )
  expect(
    client.getQueryState(documentKeys.detail("project-2", "document-1"))
      ?.isInvalidated,
  ).toBe(false)

  client.setQueryData(documentKeys.detail("project-1", "document-1"), {})
  client.setQueryData(documentKeys.job("job-1"), {})
  await invalidateDocumentMutation(client, "project-1", "document-1", retry, {
    action: "retry-job",
  })
  expect(
    client.getQueryState(documentKeys.detail("project-1", "document-1"))
      ?.isInvalidated,
  ).toBe(true)
  expect(client.getQueryState(documentKeys.job("job-1"))?.isInvalidated).toBe(
    true,
  )
})
