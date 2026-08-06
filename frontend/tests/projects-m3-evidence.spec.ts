import fs from "node:fs"
import path from "node:path"
import { fileURLToPath } from "node:url"
import { expect, type Page, test } from "@playwright/test"

import type {
  LiteratureExtractionFieldPublic,
  LiteratureMatrixField,
} from "../src/api/adapter"
import { mapTopicCandidates } from "../src/features/topic-candidates/mappers"
import type { TopicRunProjection } from "../src/features/topic-candidates/model"

const root = path.dirname(fileURLToPath(import.meta.url))
const pdfBytes = fs.readFileSync(path.join(root, "fixtures", "minimal.pdf"))
const meta = { request_id: "request-m3", schema_version: "1.0" }
const pagination = { page: 1, page_size: 20, total: 1, pages: 1 }
const fieldCodes = [
  "TITLE",
  "AUTHORS",
  "YEAR",
  "RESEARCH_OBJECT",
  "SAMPLE_SIZE",
  "CORE_VARIABLES",
  "RESEARCH_DESIGN",
  "ANALYSIS_METHOD",
  "MAIN_CONCLUSION",
  "LIMITATION",
] as const

async function expectTrustedPdfHighlight(page: Page) {
  await expect(page.locator(".m3-pdf-canvas-wrap")).toHaveAttribute(
    "data-render-state",
    "ready",
    { timeout: 15_000 },
  )
  await expect(page.locator(".m3-pdf-highlight")).toHaveCount(1)
}

async function captureVisual(page: Page, name: string) {
  const outputDirectory = process.env.RECA_M3_VISUAL_DIR
  if (!outputDirectory) return
  fs.mkdirSync(outputDirectory, { recursive: true })
  await page.screenshot({
    path: path.join(outputDirectory, `${name}.png`),
    fullPage: true,
  })
}

function matrixField(code: (typeof fieldCodes)[number]): LiteratureMatrixField {
  return {
    field_code: code,
    value_text:
      code === "MAIN_CONCLUSION"
        ? "Server conclusion with located evidence"
        : `${code} server value`,
    value_json: null,
    confidence_level: code === "SAMPLE_SIZE" ? "LOW" : "HIGH",
    confidence_score: code === "SAMPLE_SIZE" ? 0.31 : 0.92,
    confirmation_status:
      code === "MAIN_CONCLUSION" ? "UNREVIEWED" : "CONFIRMED",
    evidence_status:
      code === "SAMPLE_SIZE"
        ? "NO_LOCATED_EVIDENCE"
        : code === "YEAR"
          ? "LOCATION_UNCERTAIN"
          : "LOCATED",
    evidence_span_id: code === "MAIN_CONCLUSION" ? "span-1" : null,
    evidence_limitations: code === "SAMPLE_SIZE" ? "NO_LOCATED_EVIDENCE" : null,
    lock_version: 2,
  }
}

function extractionField(
  code: (typeof fieldCodes)[number],
): LiteratureExtractionFieldPublic {
  const matrix = matrixField(code)
  return {
    id: `field-${code.toLowerCase()}`,
    project_id: "project-1",
    extraction_id: "extraction-1",
    field_code: code,
    model_value_text: matrix.value_text,
    model_value_json: null,
    value_text: matrix.value_text,
    value_json: null,
    confidence_score: matrix.confidence_score,
    confidence_level: matrix.confidence_level,
    evidence_span_id: matrix.evidence_span_id,
    confirmation_status: matrix.confirmation_status,
    evidence_status: matrix.evidence_status,
    evidence_limitations: matrix.evidence_limitations,
    lock_version: 2,
    created_at: "2026-08-03T01:00:00Z",
    updated_at: "2026-08-03T01:00:00Z",
    allowed_actions: [
      "literature_extraction_field.read",
      "literature_extraction_field.update",
    ],
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
  await page.route("**/api/v1/projects/project-1", (route) =>
    route.fulfill({
      json: {
        data: {
          id: "project-1",
          owner_id: "user-1",
          name: "M3 evidence project",
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
          created_at: "2026-08-03T00:00:00Z",
          updated_at: "2026-08-03T00:00:00Z",
          permissions: { role: "OWNER", inherited: false },
          allowed_actions: ["project.read", "project.update"],
        },
        meta,
      },
    }),
  )
}

async function routeEvidence(
  page: Page,
  options: {
    parser?: "GROBID" | "PYPDF"
    boxes?: Array<Record<string, number>>
    unknown?: boolean
    onDecision?: () => void
    onCorrection?: () => void
  } = {},
) {
  let decision: "INCLUDED" | "EXCLUDED" | "UNCERTAIN" = "UNCERTAIN"
  await page.route(
    "**/api/v1/projects/project-1/literature-matrix**",
    (route) =>
      route.fulfill({
        json: {
          data: [
            {
              literature_record_id: "literature-1",
              document_id: "document-1",
              extraction_id: "extraction-1",
              extraction_status: options.unknown
                ? "FUTURE_STATE"
                : "NEEDS_REVIEW",
              title: "Server evidence literature",
              authors_text: "Li; Smith",
              publication_year: 2026,
              current_decision: decision,
              fields: fieldCodes.map(matrixField),
              allowed_actions: options.unknown
                ? []
                : [
                    "literature.read",
                    "literature.update_fields",
                    "literature.decide",
                  ],
            },
          ],
          allowed_actions: options.unknown
            ? []
            : [
                "literature_matrix.read",
                "evidence_span.create",
                "evidence_span.verify",
                "literature.decide",
              ],
          pagination,
          meta,
        },
      }),
  )
  await page.route("**/api/v1/literature-extractions/extraction-1", (route) =>
    route.fulfill({
      json: {
        data: {
          id: "extraction-1",
          project_id: "project-1",
          literature_record_id: "literature-1",
          document_id: "document-1",
          extraction_version: 1,
          schema_version: "1.0",
          status: "NEEDS_REVIEW",
          overall_confidence: "MEDIUM",
          source_model_invocation_id: "invocation-1",
          processing_run_id: "processing-1",
          document_level_limitations: [],
          lock_version: 1,
          fields: fieldCodes.map((code) => ({
            ...extractionField(code),
            allowed_actions: options.unknown
              ? ["literature_extraction_field.read"]
              : extractionField(code).allowed_actions,
          })),
          allowed_actions: ["literature_extraction.read"],
          created_at: "2026-08-03T01:00:00Z",
          updated_at: "2026-08-03T01:00:00Z",
        },
        meta,
      },
    }),
  )
  await page.route("**/api/v1/evidence-spans/span-1", (route) =>
    route.fulfill({
      json: {
        data: {
          id: "span-1",
          project_id: "project-1",
          document_id: "document-1",
          document_page_id: "page-4",
          chunk_id: "chunk-4",
          page_number: 1,
          section_path: null,
          source_text: "Located server evidence on the PDF page.",
          context_before: null,
          context_after: null,
          bounding_boxes: options.boxes ?? [
            { page: 1, x: 0.12, y: 0.16, width: 0.58, height: 0.08 },
          ],
          char_start: 0,
          char_end: 40,
          evidence_type: "FIELD_SUPPORT",
          confidence_level: options.parser === "PYPDF" ? "LOW" : "HIGH",
          confidence_score: options.parser === "PYPDF" ? 0.35 : 0.94,
          parser_type: options.parser ?? "GROBID",
          parser_version: "1.0",
          model_invocation_id: null,
          source_text_hash: "a".repeat(64),
          location_verification_status:
            options.boxes?.length === 0 ? "LOCATION_UNCERTAIN" : "LOCATED",
          review_status: "UNREVIEWED",
          parser_coverage:
            options.parser === "PYPDF" ? "PARTIAL_TEXT" : "FULL_TEXT",
          user_declared_read_scope: "SECTIONS",
          reviewed_by_actor_type: null,
          reviewed_by_actor_id: null,
          reviewed_at: null,
          verified_by_actor_id: null,
          verified_at: null,
          allowed_actions: options.unknown
            ? ["evidence_span.read"]
            : [
                "evidence_span.read",
                "evidence_span.verify",
                "evidence_span.reject",
              ],
          created_at: "2026-08-03T01:00:00Z",
        },
        meta,
      },
    }),
  )
  await page.route("**/api/v1/documents/document-1", (route) =>
    route.fulfill({
      json: {
        data: {
          id: "document-1",
          project_id: "project-1",
          artifact_id: "artifact-1",
          literature_record_id: "literature-1",
          document_type: "SCHOLARLY_PDF",
          parser_type: options.parser ?? "GROBID",
          parser_version: "1.0",
          parse_status: "COMPLETED",
          page_count: 1,
          language: "en",
          is_scanned: false,
          parse_confidence: options.parser === "PYPDF" ? "LOW" : "HIGH",
          created_at: "2026-08-03T00:00:00Z",
          updated_at: "2026-08-03T00:00:00Z",
          allowed_actions: ["document.read"],
        },
        meta,
      },
    }),
  )
  await page.route("**/api/v1/documents/document-1/pages/1", (route) =>
    route.fulfill({
      json: {
        data: {
          document_id: "document-1",
          project_id: "project-1",
          page_number: 1,
          printed_page_label: "1",
          text_content: "Located server evidence on the PDF page.",
          width: 612,
          height: 792,
          parser_metadata: null,
          created_at: "2026-08-03T00:00:00Z",
        },
        meta,
      },
    }),
  )
  await page.route("**/api/v1/artifacts/artifact-1/download", (route) =>
    route.fulfill({
      json: {
        data: {
          artifact_id: "artifact-1",
          download_url: "/authorized-m3.pdf",
          expires_at: "2026-08-03T02:00:00Z",
          disposition_filename: "evidence.pdf",
        },
        meta,
      },
    }),
  )
  await page.route("**/authorized-m3.pdf", (route) =>
    route.fulfill({ body: pdfBytes, contentType: "application/pdf" }),
  )
  await page.route(
    "**/api/v1/literature-extraction-fields/field-main_conclusion",
    (route) => {
      options.onCorrection?.()
      return route.fulfill({
        status: 409,
        json: {
          error: {
            code: "STALE_IF_MATCH",
            message: "The extraction field changed on the server.",
            request_id: "request-field-conflict",
            retryable: false,
          },
        },
      })
    },
  )
  await page.route("**/api/v1/literature/literature-1/decisions", (route) => {
    decision = route.request().postDataJSON().decision
    options.onDecision?.()
    return route.fulfill({
      status: 201,
      json: {
        data: {
          id: "decision-1",
          project_id: "project-1",
          literature_record_id: "literature-1",
          decision,
          reason_code: "RELEVANT_OBJECT_AND_METHOD",
          reason_text: "Included after evidence review.",
          ai_recommendation: null,
          ai_score: null,
          decided_by_user_id: "user-1",
          supersedes_decision_id: null,
          is_current: true,
          created_at: "2026-08-03T01:10:00Z",
        },
        meta,
      },
    })
  })
}

const deepLink =
  "/projects/project-1/literature?view=matrix&documentId=document-1&extractionId=extraction-1&fieldId=field-main_conclusion&evidenceSpanId=span-1"

test("M3 deep link refresh restores server matrix, PDF page and trusted highlight", async ({
  page,
}) => {
  await page.setViewportSize({ width: 1440, height: 900 })
  await authenticate(page)
  let matrixLoads = 0
  await routeEvidence(page)
  page.on("request", (request) => {
    if (request.url().includes("literature-matrix")) matrixLoads += 1
  })
  await page.goto(deepLink)
  await expect(
    page.getByRole("heading", { name: "Evidence Matrix" }),
  ).toBeVisible()
  await expect(
    page.getByText("Server evidence literature").first(),
  ).toBeVisible()
  await expect(page.locator(".m3-pdf-canvas-wrap canvas")).toBeVisible()
  await expectTrustedPdfHighlight(page)
  const matrixPane = await page.locator(".m3-matrix-pane").boundingBox()
  const pdfPane = await page.locator(".m3-pdf-pane").boundingBox()
  expect(matrixPane).not.toBeNull()
  expect(pdfPane).not.toBeNull()
  expect(matrixPane!.x + matrixPane!.width).toBeLessThanOrEqual(pdfPane!.x + 1)
  expect(matrixPane!.width).toBeGreaterThanOrEqual(560)
  expect(pdfPane!.width).toBeGreaterThanOrEqual(320)
  expect(
    await page.evaluate(
      () =>
        document.documentElement.scrollWidth -
        document.documentElement.clientWidth,
    ),
  ).toBe(0)
  await captureVisual(page, "m3-desktop-matrix-pdf")
  await page.reload()
  await expectTrustedPdfHighlight(page)
  expect(matrixLoads).toBeGreaterThanOrEqual(2)
})

test("tablet switches between stable matrix and evidence panes", async ({
  page,
}) => {
  await page.setViewportSize({ width: 820, height: 1024 })
  await authenticate(page)
  await routeEvidence(page)
  await page.goto(deepLink)

  const matrixPane = page.locator(".m3-matrix-pane")
  const pdfPane = page.locator(".m3-pdf-pane")
  await expect(matrixPane).toBeVisible()
  await expect(pdfPane).toBeHidden()

  await page.getByRole("button", { name: "Evidence", exact: true }).click()
  await expect(matrixPane).toBeHidden()
  await expect(pdfPane).toBeVisible()
  await expectTrustedPdfHighlight(page)
  await captureVisual(page, "m3-tablet-evidence-pane")

  const overflow = await page.evaluate(() => ({
    delta:
      document.documentElement.scrollWidth -
      document.documentElement.clientWidth,
    offenders: Array.from(document.querySelectorAll("body *"))
      .map((element) => ({
        className: element.className,
        right: Math.round(element.getBoundingClientRect().right),
        width: Math.round(element.getBoundingClientRect().width),
      }))
      .filter((item) => item.right > window.innerWidth + 1)
      .slice(0, 8),
  }))
  expect(overflow.delta, JSON.stringify(overflow.offenders)).toBe(0)
})

test("keyboard focus traverses view tabs with a visible focus indicator", async ({
  page,
}) => {
  await authenticate(page)
  await routeEvidence(page)
  await page.goto(deepLink)

  const matrixTab = page.getByRole("tab", { name: "Matrix" })
  const analysisTab = page.getByRole("tab", { name: "Analysis" })
  const topicsTab = page.getByRole("tab", { name: "Topics" })
  await matrixTab.focus()
  await page.keyboard.press("Tab")
  await expect(analysisTab).toBeFocused()
  const focusStyle = await analysisTab.evaluate((element) => {
    const style = getComputedStyle(element)
    return {
      outlineStyle: style.outlineStyle,
      outlineWidth: style.outlineWidth,
    }
  })
  expect(focusStyle.outlineStyle).not.toBe("none")
  expect(focusStyle.outlineWidth).not.toBe("0px")
  await page.keyboard.press("Tab")
  await expect(topicsTab).toBeFocused()
})

test("pypdf without coordinates degrades to page text and fits 390px", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await authenticate(page)
  await routeEvidence(page, { parser: "PYPDF", boxes: [] })
  await page.goto(deepLink)
  await page.getByRole("button", { name: "Evidence", exact: true }).click()
  await expect(page.getByText(/pypdf provides degraded text/i)).toBeVisible()
  await expect(page.locator(".m3-pdf-highlight")).toHaveCount(0)
  await expect(
    page.getByRole("button", { name: "Verify location" }),
  ).toBeDisabled()
  await expect(
    page.getByText("Located server evidence on the PDF page.").first(),
  ).toBeVisible()
  await captureVisual(page, "m3-390-pypdf-degraded")
  const overflow = await page.evaluate(
    () =>
      document.documentElement.scrollWidth -
      document.documentElement.clientWidth,
  )
  expect(overflow).toBe(0)
})

test("field conflict preserves server value and decision refreshes from server", async ({
  page,
}) => {
  await authenticate(page)
  let correctionCalled = false
  let decisionCalled = false
  await routeEvidence(page, {
    onCorrection: () => {
      correctionCalled = true
    },
    onDecision: () => {
      decisionCalled = true
    },
  })
  await page.goto(deepLink)
  await page.getByLabel("Correction reason").fill("Manual source review")
  await page.getByRole("button", { name: "Correct" }).click()
  await expect(
    page.getByText("The extraction field changed on the server."),
  ).toBeVisible()
  await expect(page.getByLabel("Field value")).toHaveValue(
    "Server conclusion with located evidence",
  )
  expect(correctionCalled).toBe(true)
  await page.getByRole("button", { name: "Include" }).click()
  await expect(page.getByText("INCLUDED").first()).toBeVisible()
  expect(decisionCalled).toBe(true)
})

test("unknown projections fail closed and topic mapper never pads invalid counts", async ({
  page,
}) => {
  await authenticate(page)
  await routeEvidence(page, { unknown: true })
  await page.goto(deepLink)
  await expect(page.getByRole("button", { name: "Correct" })).toBeDisabled()
  await expect(page.getByRole("button", { name: "Include" })).toBeDisabled()

  const projection = {
    id: "run-1",
    project_id: "project-1",
    research_question_version_id: "rq-version-1",
    evidence_summary_id: "summary-1",
    status: "COMPLETED",
    candidates: [],
  } satisfies TopicRunProjection
  const mapped = mapTopicCandidates(projection)
  expect(mapped.exactlyThree).toBe(false)
  expect(mapped.candidates).toHaveLength(0)
  expect(mapped.failureReason).toContain("exactly three")
})
