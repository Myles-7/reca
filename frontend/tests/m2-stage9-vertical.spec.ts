import { readFile } from "node:fs/promises"
import { expect, type Page, test } from "@playwright/test"

const apiURL = process.env.M2_STAGE9_API_URL ?? "http://127.0.0.1:8001"
const ownerEmail =
  process.env.M2_STAGE9_OWNER_EMAIL ?? "stage9-owner@example.com"
const ownerPassword =
  process.env.M2_STAGE9_OWNER_PASSWORD ?? "stage9-owner-password"

type Envelope<T> = { data: T }

async function login(page: Page) {
  await page.goto("/login")
  await page.getByTestId("email-input").fill(ownerEmail)
  await page.getByTestId("password-input").fill(ownerPassword)
  await page.getByRole("button", { name: /log in/i }).click()
  await expect(page).not.toHaveURL(/\/login$/)
}

async function token(page: Page) {
  const value = await page.evaluate(() => localStorage.getItem("access_token"))
  expect(value).toBeTruthy()
  return value!
}

async function api<T>(
  page: Page,
  method: "GET" | "POST" | "PATCH",
  path: string,
  options: {
    data?: unknown
    headers?: Record<string, string>
    multipart?: Record<
      string,
      string | { name: string; mimeType: string; buffer: Buffer }
    >
    expected?: number
  } = {},
) {
  const response = await page.request.fetch(`${apiURL}${path}`, {
    method,
    data: options.data,
    headers: {
      Authorization: `Bearer ${await token(page)}`,
      ...options.headers,
    },
    multipart: options.multipart,
  })
  expect(response.status(), await response.text()).toBe(options.expected ?? 200)
  return (await response.json()) as Envelope<T>
}

function key(prefix: string) {
  return `${prefix}-${crypto.randomUUID()}`
}

test("production routes complete the deterministic M2 vertical chain", async ({
  page,
}) => {
  test.setTimeout(120_000)
  await login(page)

  const project = await api<{ id: string }>(page, "POST", "/api/v1/projects", {
    expected: 201,
    headers: { "Idempotency-Key": key("project") },
    data: { name: "M2 Stage 9 vertical", project_type: "RESEARCH" },
  })
  const projectId = project.data.id

  await page.goto(`/projects/${projectId}/research-question`)
  await page.locator("#rq-create-raw-input").fill("生成式AI与师范生学习投入")
  await page.getByRole("button", { name: "创建 Research Question" }).click()
  await expect(
    page.locator(".rq-workspace[data-od-id='research-question-workspace']"),
  ).toBeVisible()

  await page
    .getByRole("textbox", { name: /规范化问题/ })
    .fill("生成式AI与师范生学习投入")
  await page.getByRole("textbox", { name: /研究对象/ }).fill("师范生")
  await page.getByRole("textbox", { name: /研究情境/ }).fill("教师教育")
  await page.locator("#rq-change-reason-input").fill("Stage 9 scope review")
  await page.getByRole("button", { name: "保存新版本" }).click()
  await expect(page.locator(".reca-workspace-header__context")).toHaveText(
    "版本 2",
  )
  await page.getByRole("button", { name: "标记为待确认" }).click()
  await expect(page.getByText("待确认", { exact: true }).first()).toBeVisible()
  await page.getByRole("button", { name: "请求确认" }).click()
  await expect(page.getByText(/待确认/).first()).toBeVisible()

  const approvals = await api<{ id: string }[]>(
    page,
    "GET",
    `/api/v1/projects/${projectId}/approvals`,
  )
  const approvalId = approvals.data[0]?.id
  expect(approvalId).toBeTruthy()
  await api(page, "POST", `/api/v1/approvals/${approvalId}/approve`, {
    headers: { "Idempotency-Key": key("approval") },
    data: { decision_reason: "Stage 9 confirmed", item_decisions: [] },
  })
  await page.reload()
  await expect(page.getByText("已确认", { exact: true }).first()).toBeVisible()

  const current = await api<{
    question: { current_version: { id: string } }
  }>(page, "GET", `/api/v1/projects/${projectId}/research-question`)
  const versionId = current.data.question.current_version.id
  const plan = await api<{ id: string; lock_version: number }>(
    page,
    "POST",
    `/api/v1/projects/${projectId}/query-plans`,
    {
      expected: 201,
      headers: { "Idempotency-Key": key("plan") },
      data: {
        research_question_version_id: versionId,
        chinese_terms: ["生成式人工智能", "学习投入"],
        english_terms: ["generative AI", "learning engagement"],
        boolean_query: '("generative AI" OR GenAI) AND "learning engagement"',
        filters: {
          from_year: 2020,
          to_year: 2026,
          languages: ["zh", "en"],
          work_types: ["article"],
          open_access_only: false,
        },
      },
    },
  )
  const planId = plan.data.id
  await page.goto(`/projects/${projectId}/query-plans/${planId}`)
  await expect(page.locator(".reca-query-plan-workspace")).toBeVisible()
  await page.locator("#query-plan-change-reason").fill("Stage 9 query review")
  await page.locator(".query-plan-save-button").click()
  await expect(page.getByText("DRAFT", { exact: true }).first()).toBeVisible()
  await page.locator(".query-plan-primary-action").click()
  await expect
    .poll(async () => {
      const generated = await api<{
        source_model_invocation_id: string | null
      }>(page, "GET", `/api/v1/query-plans/${planId}`)
      return generated.data.source_model_invocation_id
    })
    .not.toBeNull()
  await page.reload()
  await expect(page.getByText("AI 生成", { exact: true }).first()).toBeVisible()

  const firstSearch = await api<{
    search_run: { id: string; status: string }
    job: { id: string }
  }>(page, "POST", `/api/v1/query-plans/${planId}/search-runs`, {
    expected: 202,
    headers: { "Idempotency-Key": key("search") },
    data: { page_size: 25, use_cache: true },
  })
  const firstRunId = firstSearch.data.search_run.id
  expect(firstSearch.data.search_run).toMatchObject({ status: "QUEUED" })
  await expect
    .poll(async () => {
      const result = await api<{ search_run: { status: string } }>(
        page,
        "GET",
        `/api/v1/literature-search-runs/${firstRunId}/results`,
      )
      return result.data.search_run.status
    })
    .toBe("COMPLETED")
  await page.goto(`/projects/${projectId}/literature?searchRunId=${firstRunId}`)
  await expect(page.locator(".reca-literature-workspace")).toBeVisible()
  await expect(page.getByText(/Recorded/i).first()).toBeVisible()
  await page.reload()
  await expect(page).toHaveURL(new RegExp(`searchRunId=${firstRunId}`))

  await page.getByRole("button", { name: "筛选" }).click()
  await page.getByRole("button", { name: "执行检索" }).click()
  await expect(page).not.toHaveURL(new RegExp(`searchRunId=${firstRunId}`))
  const cachedRunId = new URL(page.url()).searchParams.get("searchRunId")
  expect(cachedRunId).toBeTruthy()
  await expect
    .poll(async () => {
      const result = await api<{
        search_run: { status: string; cache_hit: boolean }
      }>(page, "GET", `/api/v1/literature-search-runs/${cachedRunId}/results`)
      return [result.data.search_run.status, result.data.search_run.cache_hit]
    })
    .toEqual(["COMPLETED", true])
  await page.reload()
  await expect(page.getByText(/cache hit/i).first()).toBeVisible()

  const candidateAction = page.locator(
    ".literature-row--candidate .literature-row__action button",
  )
  await candidateAction.click()
  await expect(
    page.getByRole("button", { name: "查看正式记录" }).first(),
  ).toBeVisible()

  const records = await api<Array<{ id: string; doi: string | null }>>(
    page,
    "GET",
    `/api/v1/projects/${projectId}/literature`,
  )
  const literature = records.data[0]
  expect(literature?.doi).toBeTruthy()
  await page.getByRole("button", { name: "筛选" }).click()
  await page.locator("#literature-doi").fill(literature.doi!)
  await page.getByRole("button", { name: "导入 DOI" }).click()
  await expect
    .poll(
      async () =>
        (
          await api<Array<{ id: string }>>(
            page,
            "GET",
            `/api/v1/projects/${projectId}/literature`,
          )
        ).data.length,
    )
    .toBe(1)

  const pdf = await readFile("tests/fixtures/minimal.pdf")
  const upload = await api<{
    document: { id: string; parse_status: string }
    artifact: { is_original: boolean; sha256: string }
  }>(page, "POST", `/api/v1/projects/${projectId}/documents`, {
    expected: 201,
    headers: { "Idempotency-Key": key("document") },
    multipart: {
      document_type: "SCHOLARLY_PDF",
      literature_record_id: literature.id,
      file: {
        name: "minimal.pdf",
        mimeType: "application/pdf",
        buffer: pdf,
      },
    },
  })
  expect(upload.data.document.parse_status).toBe("DRAFT")
  expect(upload.data.artifact.is_original).toBe(true)
  expect(upload.data.artifact.sha256).toMatch(/^[0-9a-f]{64}$/)

  const documentId = upload.data.document.id
  await page.goto(`/projects/${projectId}/documents/${documentId}`)
  await expect(page.locator(".document-workspace")).toBeVisible()
  await page.getByRole("button", { name: "开始解析" }).click()
  await expect(page).toHaveURL(/jobId=/)
  await expect
    .poll(async () => {
      const parsed = await api<{ parse_status: string }>(
        page,
        "GET",
        `/api/v1/documents/${documentId}`,
      )
      return parsed.data.parse_status
    })
    .toBe("COMPLETED")
  await page.reload()
  await expect(page.getByText("解析完成").first()).toBeVisible()
  await expect(page).toHaveURL(/jobId=/)
  await expect(page.getByText("Left column").first()).toBeVisible()
  await expect(page.getByText(/EvidenceSpan/)).toHaveCount(0)
})
