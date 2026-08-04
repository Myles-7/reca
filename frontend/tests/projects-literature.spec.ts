import { expect, type Page, test } from "@playwright/test"
import { QueryClient } from "@tanstack/react-query"

import type {
  JobPublic,
  LiteratureCandidatePublic,
  LiteratureRecordPublic,
  LiteratureSearchRunPublic,
  ProjectPublic,
} from "../src/api/adapter"
import { invalidateLiteratureMutation } from "../src/features/literature/mutations"
import { literatureKeys } from "../src/features/literature/queries"
import type { LiteratureEvent } from "../src/features/literature/ui/contracts"
import { createDeferred } from "./utils/deferred"

const meta = { request_id: "request-literature", schema_version: "1.0" }
const pagination = { page: 1, page_size: 100, total: 1, pages: 1 }

test.use({ viewport: { width: 1440, height: 900 } })

function project(overrides: Partial<ProjectPublic> = {}): ProjectPublic {
  return {
    id: "project-1",
    owner_id: "user-1",
    name: "Literature project",
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

function searchRun(
  overrides: Partial<LiteratureSearchRunPublic> = {},
): LiteratureSearchRunPublic {
  return {
    id: "search-1",
    project_id: "project-1",
    query_plan_id: "plan-1",
    provider: "OPENALEX",
    provider_query: { page_size: 25, use_cache: true },
    result_count: 1,
    cache_hit: true,
    cache_stale: false,
    cache_source_run_id: "search-recorded",
    degraded: false,
    limitations: [],
    fetched_at: "2026-08-01T04:00:00Z",
    status: "COMPLETED",
    error_code: null,
    job_id: "job-1",
    created_at: "2026-08-01T03:59:00Z",
    allowed_actions: ["literature_search.read", "literature_search.import"],
    ...overrides,
  }
}

function candidate(
  overrides: Partial<LiteratureCandidatePublic> = {},
): LiteratureCandidatePublic {
  return {
    id: "candidate-1",
    project_id: "project-1",
    search_run_id: "search-1",
    result_order: 1,
    source_identifier: "W123",
    title: "Server candidate",
    abstract: null,
    publication_year: 2026,
    journal_name: "RECA Journal",
    doi: "10.1000/candidate",
    authors_text: "Li; Smith",
    keywords: [],
    work_type: "article",
    open_access_status: "OPEN",
    verification_status: "VERIFIED",
    fetched_at: "2026-08-01T04:00:00Z",
    degraded: false,
    imported_literature_record_id: null,
    allowed_actions: [
      "literature_candidate.read",
      "literature_candidate.import",
    ],
    ...overrides,
  }
}

function record(
  overrides: Partial<LiteratureRecordPublic> = {},
): LiteratureRecordPublic {
  return {
    id: "record-1",
    project_id: "project-1",
    document_id: null,
    source_type: "OPENALEX",
    source_identifier: "W123",
    title: "Formal server record",
    abstract: null,
    publication_year: 2026,
    journal_name: "RECA Journal",
    doi: "10.1000/candidate",
    authors_text: "Li; Smith",
    keywords: [],
    work_type: "article",
    open_access_status: "OPEN",
    verification_status: "VERIFIED",
    current_decision: "UNCERTAIN",
    created_at: "2026-08-01T04:10:00Z",
    updated_at: "2026-08-01T04:10:00Z",
    allowed_actions: ["literature.read", "document.upload"],
    ...overrides,
  }
}

function job(overrides: Partial<JobPublic> = {}): JobPublic {
  return {
    id: "job-1",
    project_id: "project-1",
    task_type: "LITERATURE_SEARCH",
    resource_type: "literature_search_run",
    resource_id: "search-1",
    status: "COMPLETED",
    progress_percent: 100,
    current_step: null,
    total_steps: null,
    completed_steps: null,
    retry_count: 0,
    max_retries: 3,
    retryable: false,
    current_processing_run_id: null,
    created_at: "2026-08-01T03:59:00Z",
    started_at: "2026-08-01T03:59:10Z",
    completed_at: "2026-08-01T04:00:00Z",
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

test("Literature deep link and refresh load recorded candidate and formal record projections", async ({
  page,
}) => {
  await authenticate(page)
  await routeProject(page)
  let resultLoads = 0
  await page.route("**/api/v1/projects/project-1/literature", (route) =>
    route.fulfill({
      json: {
        data: [record()],
        allowed_actions: ["literature.search", "literature.import_doi"],
        pagination,
        meta,
      },
    }),
  )
  await page.route(
    "**/api/v1/literature-search-runs/search-1/results",
    (route) => {
      resultLoads += 1
      return route.fulfill({
        json: {
          data: { search_run: searchRun(), results: [candidate()] },
          pagination,
          meta,
        },
      })
    },
  )
  await page.route("**/api/v1/jobs/job-1", (route) =>
    route.fulfill({ json: { data: job(), meta } }),
  )

  await page.goto("/projects/project-1/literature?searchRunId=search-1")
  const workspace = page.locator(".reca-literature-workspace")
  await expect(workspace).toBeVisible()
  await expect(page).toHaveURL(/searchRunId=search-1/)
  await expect(
    workspace.getByText("Recorded · cache hit").first(),
  ).toBeVisible()
  await expect(workspace.getByText("Server candidate").first()).toBeVisible()
  await workspace.getByRole("tab", { name: /正式文献/ }).click()
  await expect(workspace.getByText("Formal server record")).toBeVisible()

  await page.reload()
  await expect(workspace).toBeVisible()
  await expect.poll(() => resultLoads).toBe(2)
})

test("Literature no-run, read-only, unknown, and provider failure states fail closed", async ({
  page,
}) => {
  await authenticate(page)
  let mode: "no-run" | "read-only" | "unknown" | "provider-failure" = "no-run"
  await routeProject(page)
  await page.route("**/api/v1/projects/project-1/literature", (route) =>
    route.fulfill({
      json: {
        data: [],
        allowed_actions:
          mode === "read-only"
            ? ["literature.read"]
            : ["literature.import_doi"],
        pagination: { ...pagination, total: 0, pages: 0 },
        meta,
      },
    }),
  )
  await page.route(
    "**/api/v1/literature-search-runs/search-1/results",
    (route) =>
      route.fulfill({
        json: {
          data: {
            search_run: searchRun(
              mode === "unknown"
                ? {
                    status:
                      "FUTURE_SEARCH_STATE" as LiteratureSearchRunPublic["status"],
                  }
                : mode === "provider-failure"
                  ? {
                      status: "FAILED",
                      degraded: true,
                      error_code: "OPENALEX_UNAVAILABLE",
                      limitations: ["Provider response was unavailable."],
                      allowed_actions: ["literature_search.read"],
                    }
                  : {},
            ),
            results: [],
          },
          pagination: { ...pagination, total: 0, pages: 0 },
          meta,
        },
      }),
  )
  await page.route("**/api/v1/jobs/job-1", (route) =>
    route.fulfill({ json: { data: job(), meta } }),
  )

  await page.goto("/projects/project-1/literature")
  await expect(page.getByText("无 Search Run").first()).toBeVisible()
  await page.getByRole("button", { name: "筛选" }).click()
  await expect(page.locator("#literature-page-size")).toBeDisabled()
  await expect(page.locator("#literature-doi")).toBeEnabled()

  mode = "read-only"
  await page.reload()
  await page.getByRole("button", { name: "筛选" }).click()
  await expect(page.locator("#literature-doi")).toBeDisabled()

  mode = "unknown"
  await page.goto("/projects/project-1/literature?searchRunId=search-1")
  await expect(
    page.locator('.reca-literature-workspace [data-tone="unknown"]').first(),
  ).toBeVisible()
  await page.getByRole("button", { name: "详情" }).click()
  await expect(page.getByRole("button", { name: "重试任务" })).toBeDisabled()

  mode = "provider-failure"
  await page.reload()
  await expect(page.getByText("Provider failure")).toBeVisible()
  await expect(page.getByText(/OPENALEX_UNAVAILABLE/)).toBeVisible()
})

test("Literature search uses the server run id before navigating and reloading", async ({
  page,
}) => {
  await authenticate(page)
  await routeProject(page)
  await page.route("**/api/v1/projects/project-1/literature", (route) =>
    route.fulfill({
      json: {
        data: [],
        allowed_actions: ["literature.search", "literature.import_doi"],
        pagination: { ...pagination, total: 0, pages: 0 },
        meta,
      },
    }),
  )
  await page.route("**/api/v1/literature-search-runs/*/results", (route) => {
    const pathSegments = new URL(route.request().url()).pathname.split("/")
    const id = pathSegments[pathSegments.length - 2]!
    return route.fulfill({
      json: {
        data: {
          search_run: searchRun({
            id,
            job_id: id === "search-2" ? "job-2" : "job-1",
            cache_hit: false,
            cache_source_run_id: null,
          }),
          results: [
            candidate({
              id: `candidate-${id}`,
              search_run_id: id,
              title: id === "search-2" ? "New server results" : "Old results",
            }),
          ],
        },
        pagination,
        meta,
      },
    })
  })
  await page.route("**/api/v1/jobs/job-*", (route) => {
    const pathSegments = new URL(route.request().url()).pathname.split("/")
    const id = pathSegments[pathSegments.length - 1]!
    return route.fulfill({
      json: {
        data: job({
          id,
          resource_id: id === "job-2" ? "search-2" : "search-1",
        }),
        meta,
      },
    })
  })
  const searchRequest = createDeferred()
  await page.route(
    "**/api/v1/query-plans/plan-1/search-runs",
    async (route) => {
      expect(route.request().headers()["idempotency-key"]).toBeTruthy()
      expect(route.request().postDataJSON()).toEqual({
        page_size: 25,
        use_cache: true,
      })
      await searchRequest.promise
      return route.fulfill({
        status: 202,
        json: {
          data: {
            search_run: searchRun({ id: "search-2", job_id: "job-2" }),
            job: job({
              id: "job-2",
              resource_id: "search-2",
              status: "QUEUED",
            }),
          },
          meta,
        },
      })
    },
  )

  await page.goto("/projects/project-1/literature?searchRunId=search-1")
  await page.getByRole("button", { name: "筛选" }).click()
  const search = page
    .locator(".literature-search-controls form")
    .first()
    .getByRole("button")
  await search.click()
  await expect(search).toBeDisabled()
  await expect(page.getByText("Old results").first()).toBeVisible()
  searchRequest.resolve()
  await expect(page).toHaveURL(/searchRunId=search-2/)
  await expect(page.getByText("New server results").first()).toBeVisible()
})

test("Candidate import and duplicate match become visible only after server reload", async ({
  page,
}) => {
  await authenticate(page)
  await routeProject(page)
  let importedRecordId: string | null = null
  let matchedExisting = false
  let recordsLoads = 0
  let resultsLoads = 0
  await page.route(
    "**/api/v1/projects/project-1/literature**",
    async (route) => {
      const path = new URL(route.request().url()).pathname
      if (path.endsWith("/import")) {
        expect(route.request().headers()["idempotency-key"]).toBeTruthy()
        expect(route.request().postDataJSON()).toEqual({
          search_run_id: "search-1",
          result_ids: ["candidate-1"],
        })
        importedRecordId = "record-1"
        return route.fulfill({
          json: {
            data: {
              imported: [
                {
                  candidate_id: "candidate-1",
                  literature_record_id: "record-1",
                  matched_existing: matchedExisting,
                },
              ],
            },
            meta,
          },
        })
      }
      recordsLoads += 1
      return route.fulfill({
        json: {
          data: importedRecordId ? [record()] : [],
          allowed_actions: ["literature.search", "literature.import_doi"],
          pagination: { ...pagination, total: importedRecordId ? 1 : 0 },
          meta,
        },
      })
    },
  )
  await page.route(
    "**/api/v1/literature-search-runs/search-1/results",
    (route) => {
      resultsLoads += 1
      return route.fulfill({
        json: {
          data: {
            search_run: searchRun(),
            results: [
              candidate({
                imported_literature_record_id: importedRecordId,
                allowed_actions: importedRecordId
                  ? ["literature_candidate.read"]
                  : [
                      "literature_candidate.read",
                      "literature_candidate.import",
                    ],
              }),
            ],
          },
          pagination,
          meta,
        },
      })
    },
  )
  await page.route("**/api/v1/jobs/job-1", (route) =>
    route.fulfill({ json: { data: job(), meta } }),
  )

  await page.goto("/projects/project-1/literature?searchRunId=search-1")
  await page
    .locator(".literature-row--candidate .literature-row__action button")
    .click()
  await expect(
    page.getByRole("button", { name: "查看正式记录" }).first(),
  ).toBeVisible()
  await expect.poll(() => recordsLoads).toBe(2)
  await expect.poll(() => resultsLoads).toBe(2)

  importedRecordId = null
  matchedExisting = true
  await page.reload()
  await page
    .locator(".literature-row--candidate .literature-row__action button")
    .click()
  await expect(
    page.getByRole("button", { name: "查看正式记录" }).first(),
  ).toBeVisible()
})

test("DOI import and deduplication rely on the returned record list", async ({
  page,
}) => {
  await authenticate(page)
  await routeProject(page)
  let imported = false
  let importCalls = 0
  let recordLoads = 0
  await page.route("**/api/v1/projects/project-1/literature**", (route) => {
    const path = new URL(route.request().url()).pathname
    if (path.endsWith("/import-doi")) {
      importCalls += 1
      imported = true
      expect(route.request().headers()["idempotency-key"]).toBeTruthy()
      expect(route.request().postDataJSON()).toEqual({
        doi: "10.1000/duplicate",
      })
      return route.fulfill({
        json: {
          data: record({
            source_type: "DOI_IMPORT",
            doi: "10.1000/duplicate",
            title: "DOI server record",
          }),
          meta,
        },
      })
    }
    recordLoads += 1
    return route.fulfill({
      json: {
        data: imported
          ? [
              record({
                source_type: "DOI_IMPORT",
                doi: "10.1000/duplicate",
                title: "DOI server record",
              }),
            ]
          : [],
        allowed_actions: ["literature.import_doi"],
        pagination: { ...pagination, total: imported ? 1 : 0 },
        meta,
      },
    })
  })

  await page.goto("/projects/project-1/literature")
  await page.getByRole("button", { name: "筛选" }).click()
  await page.locator("#literature-doi").fill("10.1000/duplicate")
  await page.getByRole("button", { name: "导入 DOI" }).click()
  await expect.poll(() => recordLoads).toBe(2)
  await page.getByRole("button", { name: "关闭筛选" }).click()
  await page.getByRole("tab", { name: /正式文献/ }).click()
  await expect(page.getByText("DOI server record")).toBeVisible()

  await page.getByRole("button", { name: "筛选" }).click()
  await page.getByRole("button", { name: "导入 DOI" }).click()
  await expect.poll(() => importCalls).toBe(2)
  await expect(page.getByText("DOI server record")).toHaveCount(1)
})

test("Literature retry requires matched retryability and project permission", async ({
  page,
}) => {
  await authenticate(page)
  let retryable = true
  let permissionKnown = true
  let runStatus: LiteratureSearchRunPublic["status"] = "FAILED"
  await routeProject(page, () => {
    const value = project({
      allowed_actions: permissionKnown
        ? ["project.read", "job.read", "job.retry"]
        : [],
    })
    if (permissionKnown) return value
    const { allowed_actions: _allowedActions, ...withoutActions } = value
    return withoutActions
  })
  await page.route("**/api/v1/projects/project-1/literature", (route) =>
    route.fulfill({
      json: {
        data: [],
        allowed_actions: ["literature.search", "literature.import_doi"],
        pagination: { ...pagination, total: 0, pages: 0 },
        meta,
      },
    }),
  )
  await page.route(
    "**/api/v1/literature-search-runs/search-1/results",
    (route) =>
      route.fulfill({
        json: {
          data: {
            search_run: searchRun({
              status: runStatus,
              error_code: runStatus === "FAILED" ? "PROVIDER_FAILED" : null,
              allowed_actions: ["literature_search.read"],
            }),
            results: [],
          },
          pagination: { ...pagination, total: 0, pages: 0 },
          meta,
        },
      }),
  )
  await page.route("**/api/v1/jobs/job-1**", async (route) => {
    if (route.request().method() === "POST") {
      expect(route.request().headers()["idempotency-key"]).toBeTruthy()
      runStatus = "QUEUED"
      retryable = false
      return route.fulfill({
        json: {
          data: job({ status: "QUEUED", retryable: false }),
          meta,
        },
      })
    }
    return route.fulfill({
      json: {
        data: job({
          status: runStatus,
          retryable,
          error:
            runStatus === "FAILED"
              ? {
                  code: "PROVIDER_FAILED",
                  message: "Provider failed.",
                  retryable,
                }
              : null,
        }),
        meta,
      },
    })
  })

  await page.goto("/projects/project-1/literature?searchRunId=search-1")
  await page.getByRole("button", { name: "详情" }).click()
  const retryButton = page.getByRole("button", { name: "重试任务" })
  await expect(retryButton).toBeEnabled()
  await retryButton.click()
  await expect(retryButton).toBeDisabled()
  await expect(page.getByText("QUEUED", { exact: true }).first()).toBeVisible()

  runStatus = "FAILED"
  retryable = false
  await page.reload()
  await page.getByRole("button", { name: "详情" }).click()
  await expect(retryButton).toBeDisabled()
  await expect(
    page.getByText("The server marked this Job as non-retryable."),
  ).toBeVisible()

  permissionKnown = false
  retryable = true
  await page.reload()
  await page.getByRole("button", { name: "详情" }).click()
  await expect(retryButton).toBeDisabled()
  await expect(page.getByText(/retry permission is unknown/)).toBeVisible()
})

test("Literature mutation invalidation stays resource exact", async () => {
  const search: LiteratureEvent = {
    action: "search",
    input: { queryPlanId: "plan-1", pageSize: 25, useCache: true },
  }
  const candidates: LiteratureEvent = {
    action: "import-candidates",
    input: { searchRunId: "search-1", candidateIds: ["candidate-1"] },
  }
  const doi: LiteratureEvent = {
    action: "import-doi",
    input: { doi: "10.1000/test" },
  }
  const retry: LiteratureEvent = {
    action: "retry-job",
    input: { jobId: "job-1" },
  }
  const client = new QueryClient()
  const keys = [
    literatureKeys.records("project-1"),
    literatureKeys.records("project-2"),
    literatureKeys.searchRun("search-1"),
    literatureKeys.searchRun("search-2"),
    literatureKeys.job("job-1"),
  ] as const
  keys.forEach((key) => client.setQueryData(key, {}))

  await invalidateLiteratureMutation(
    client,
    "project-1",
    "search-1",
    search,
    "search-2",
  )
  expect(
    client.getQueryState(literatureKeys.searchRun("search-2"))?.isInvalidated,
  ).toBe(true)
  expect(
    client.getQueryState(literatureKeys.records("project-1"))?.isInvalidated,
  ).toBe(false)

  await invalidateLiteratureMutation(
    client,
    "project-1",
    "search-1",
    candidates,
  )
  expect(
    client.getQueryState(literatureKeys.records("project-1"))?.isInvalidated,
  ).toBe(true)
  expect(
    client.getQueryState(literatureKeys.searchRun("search-1"))?.isInvalidated,
  ).toBe(true)
  expect(
    client.getQueryState(literatureKeys.records("project-2"))?.isInvalidated,
  ).toBe(false)

  client.setQueryData(literatureKeys.records("project-1"), {})
  await invalidateLiteratureMutation(client, "project-1", "search-1", doi)
  expect(
    client.getQueryState(literatureKeys.records("project-1"))?.isInvalidated,
  ).toBe(true)

  client.setQueryData(literatureKeys.job("job-1"), {})
  client.setQueryData(literatureKeys.searchRun("search-1"), {})
  await invalidateLiteratureMutation(client, "project-1", "search-1", retry)
  expect(client.getQueryState(literatureKeys.job("job-1"))?.isInvalidated).toBe(
    true,
  )
  expect(
    client.getQueryState(literatureKeys.searchRun("search-1"))?.isInvalidated,
  ).toBe(true)
})
