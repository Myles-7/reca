import { expect, test } from "@playwright/test"

import {
  type DocumentPublic,
  DocumentsApi,
  LiteratureApi,
  type LiteratureSearchRunPublic,
  type QueryPlanPublic,
  QueryPlansApi,
} from "../src/api/adapter"
import { client } from "../src/api/generated/client.gen"
import {
  documentDegradedFixture,
  documentFallbackFixture,
} from "../src/features/documents/fixtures"
import { mapDocument } from "../src/features/documents/mappers"
import { documentHref } from "../src/features/documents/model"
import { canExecuteDocumentEvent } from "../src/features/documents/mutations"
import {
  literatureDegradedFixture,
  literatureReadyFixture,
} from "../src/features/literature/fixtures"
import {
  mapLiteratureCandidate,
  mapLiteratureRecord,
  mapLiteratureSearchRun,
} from "../src/features/literature/mappers"
import { literatureHref } from "../src/features/literature/model"
import { canExecuteLiteratureEvent } from "../src/features/literature/mutations"
import {
  queryPlanDegradedFixture,
  queryPlanPermissionsUnknownFixture,
  queryPlanReadyFixture,
} from "../src/features/query-plan/fixtures"
import { mapQueryPlan } from "../src/features/query-plan/mappers"
import { queryPlanHref } from "../src/features/query-plan/model"
import { canExecuteQueryPlanEvent } from "../src/features/query-plan/mutations"

test("M2 route semantics remain project scoped and resource explicit", () => {
  expect(queryPlanHref("project-1", "plan-1")).toBe(
    "/projects/project-1/query-plans/plan-1",
  )
  expect(literatureHref("project-1")).toBe("/projects/project-1/literature")
  expect(documentHref("project-1", "document-1")).toBe(
    "/projects/project-1/documents/document-1",
  )
})

test("unknown lifecycle values fail closed", () => {
  const plan = mapQueryPlan({
    id: "plan-1",
    project_id: "project-1",
    research_question_version_id: "version-1",
    chinese_terms: [],
    english_terms: [],
    synonyms: null,
    object_terms: null,
    method_terms: null,
    boolean_query: null,
    filters: null,
    limitations: null,
    source_model_invocation_id: null,
    status: "FUTURE" as QueryPlanPublic["status"],
    lock_version: 1,
    created_at: "2026-08-01T00:00:00Z",
    updated_at: "2026-08-01T00:00:00Z",
    allowed_actions: ["query_plan.update", "query_plan.generate"],
  })
  expect(plan).toMatchObject({
    knownStatus: false,
    tone: "degraded",
    permissions: { canUpdate: false, canGenerate: false },
  })

  const run = mapLiteratureSearchRun({
    id: "run-1",
    project_id: "project-1",
    query_plan_id: "plan-1",
    provider: "OPENALEX",
    provider_query: {},
    result_count: 0,
    cache_hit: false,
    cache_stale: false,
    cache_source_run_id: null,
    degraded: false,
    limitations: [],
    fetched_at: "2026-08-01T00:00:00Z",
    status: "FUTURE" as LiteratureSearchRunPublic["status"],
    error_code: null,
    job_id: null,
    created_at: "2026-08-01T00:00:00Z",
    allowed_actions: ["literature_search.read"],
  })
  expect(run).toMatchObject({
    knownStatus: false,
    tone: "degraded",
    degraded: true,
  })
})

test("pypdf fallback is visible as low-confidence degraded output", () => {
  const document = mapDocument({
    id: "document-1",
    project_id: "project-1",
    artifact_id: "artifact-1",
    literature_record_id: "literature-1",
    document_type: "SCHOLARLY_PDF",
    parser_type: "PYPDF",
    parser_version: "5.0",
    parse_status: "COMPLETED",
    page_count: 10,
    language: "en",
    is_scanned: false,
    parse_confidence: "LOW",
    created_at: "2026-08-01T00:00:00Z",
    updated_at: "2026-08-01T00:00:00Z",
    allowed_actions: ["document.read"],
  } satisfies DocumentPublic)
  expect(document).toMatchObject({
    tone: "degraded",
    literatureRecordId: "literature-1",
    parseConfidence: "LOW",
    permissions: { canParse: false },
  })
})

test("vertical mapper handoff preserves Recorded search and parser provenance", () => {
  const plan = mapQueryPlan({
    id: "plan-vertical",
    project_id: "project-vertical",
    research_question_version_id: "version-confirmed",
    chinese_terms: ["生成式人工智能", "学习投入"],
    english_terms: ["generative AI", "learning engagement"],
    synonyms: null,
    object_terms: null,
    method_terms: null,
    boolean_query: '("generative AI" OR GenAI) AND "learning engagement"',
    filters: { languages: ["zh", "en"], open_access_only: false },
    limitations: [],
    source_model_invocation_id: null,
    status: "DRAFT",
    lock_version: 1,
    created_at: "2026-08-01T00:00:00Z",
    updated_at: "2026-08-01T00:00:00Z",
    allowed_actions: ["query_plan.update", "query_plan.generate"],
  })
  const search = mapLiteratureSearchRun({
    id: "search-vertical",
    project_id: "project-vertical",
    query_plan_id: plan.id,
    provider: "OPENALEX_PYALEX",
    provider_query: { search: "generative AI learning engagement" },
    result_count: 1,
    cache_hit: false,
    cache_stale: false,
    cache_source_run_id: null,
    degraded: true,
    limitations: ["Recorded OpenAlex response; results are not live."],
    fetched_at: "2026-08-01T00:00:00Z",
    status: "COMPLETED",
    error_code: null,
    job_id: "job-search",
    created_at: "2026-08-01T00:00:00Z",
    allowed_actions: ["literature_search.read", "literature_search.import"],
  })
  const document = mapDocument({
    id: "document-vertical",
    project_id: "project-vertical",
    artifact_id: "artifact-original",
    literature_record_id: null,
    document_type: "SCHOLARLY_PDF",
    parser_type: "GROBID",
    parser_version: "0.8.2",
    parse_status: "COMPLETED",
    page_count: 2,
    language: "en",
    is_scanned: false,
    parse_confidence: "HIGH",
    created_at: "2026-08-01T00:00:00Z",
    updated_at: "2026-08-01T00:00:00Z",
    allowed_actions: ["document.read", "document.parse"],
  })

  expect(plan).toMatchObject({
    knownStatus: true,
    permissionsKnown: true,
    tone: "info",
  })
  expect(search).toMatchObject({
    knownStatus: true,
    tone: "degraded",
    degraded: true,
    resultCount: 1,
  })
  expect(document).toMatchObject({
    knownStatus: true,
    tone: "success",
    parserType: "GROBID",
    pageCount: 2,
    permissions: { canParse: true },
  })
})

test("resource action projections drive literature command permissions", () => {
  const candidate = mapLiteratureCandidate({
    id: "candidate-1",
    project_id: "project-1",
    search_run_id: "run-1",
    result_order: 1,
    source_identifier: "https://openalex.org/W1",
    title: "A verified record",
    abstract: null,
    publication_year: 2026,
    journal_name: null,
    doi: "10.1000/reca",
    authors_text: "Li",
    keywords: [],
    work_type: "article",
    open_access_status: "open",
    verification_status: "VERIFIED",
    fetched_at: "2026-08-01T00:00:00Z",
    degraded: false,
    imported_literature_record_id: null,
    allowed_actions: [
      "literature_candidate.read",
      "literature_candidate.import",
    ],
  })
  const record = mapLiteratureRecord({
    id: "record-1",
    project_id: "project-1",
    document_id: null,
    source_type: "OPENALEX",
    source_identifier: "https://openalex.org/W1",
    title: "A verified record",
    abstract: null,
    publication_year: 2026,
    journal_name: null,
    doi: "10.1000/reca",
    authors_text: "Li",
    keywords: [],
    work_type: "article",
    open_access_status: "open",
    verification_status: "VERIFIED",
    current_decision: "UNCERTAIN",
    created_at: "2026-08-01T00:00:00Z",
    updated_at: "2026-08-01T00:00:00Z",
    allowed_actions: ["literature.read", "document.upload"],
  })

  expect(candidate.canImport).toBe(true)
  expect(record.canUploadDocument).toBe(true)
})

test("typed fixtures cover Open Design degraded and fallback states", () => {
  expect(queryPlanDegradedFixture.content.state).toBe("ready")
  expect(literatureDegradedFixture.content.state).toBe("ready")
  expect(documentDegradedFixture.content.state).toBe("ready")
  expect(documentFallbackFixture.content.state).toBe("ready")
})

test("Codex event boundaries reject commands from unknown or unprojected states", () => {
  const queryPlan = queryPlanDegradedFixture.content
  const literature = literatureDegradedFixture.content
  const document = documentDegradedFixture.content
  expect(queryPlan.state).toBe("ready")
  expect(literature.state).toBe("ready")
  expect(document.state).toBe("ready")
  if (
    queryPlan.state !== "ready" ||
    literature.state !== "ready" ||
    document.state !== "ready"
  )
    return

  expect(
    canExecuteQueryPlanEvent(queryPlan.data, {
      action: "generate",
      input: { queryPlanId: queryPlan.data.id },
    }),
  ).toBe(false)
  expect(
    canExecuteLiteratureEvent(literature.data, {
      action: "import-doi",
      input: { doi: "10.1000/reca" },
    }),
  ).toBe(false)
  expect(
    canExecuteDocumentEvent(document.data, {
      action: "parse",
      input: {
        documentId: document.data.document.id,
        allowFallback: true,
        extractCoordinates: true,
      },
    }),
  ).toBe(false)
})

test("Query Plan guard distinguishes known, false, and unknown permissions", () => {
  const ready = queryPlanReadyFixture.content
  const unknown = queryPlanPermissionsUnknownFixture.content
  expect(ready.state).toBe("ready")
  expect(unknown.state).toBe("ready")
  if (ready.state !== "ready" || unknown.state !== "ready") return
  const event = {
    action: "generate",
    input: { queryPlanId: ready.data.id },
  } as const
  expect(canExecuteQueryPlanEvent(ready.data, event)).toBe(true)
  expect(
    canExecuteQueryPlanEvent(
      {
        ...ready.data,
        permissions: { canUpdate: false, canGenerate: false },
      },
      event,
    ),
  ).toBe(false)
  expect(canExecuteQueryPlanEvent(unknown.data, event)).toBe(false)
  expect(
    canExecuteQueryPlanEvent(ready.data, {
      action: "generate",
      input: { queryPlanId: "plan-outside-projection" },
    }),
  ).toBe(false)
  expect(
    canExecuteQueryPlanEvent(ready.data, {
      action: "update",
      input: {
        queryPlanId: ready.data.id,
        lockVersion: ready.data.lockVersion + 1,
        changeReason: "Stale view",
        fields: ready.data.fields,
      },
    }),
  ).toBe(false)
})

test("Literature retry remains closed without a formal Job action projection", () => {
  const content = literatureReadyFixture.content
  expect(content.state).toBe("ready")
  if (content.state !== "ready") return
  expect(
    canExecuteLiteratureEvent(content.data, {
      action: "retry-job",
      input: { jobId: "job-design" },
    }),
  ).toBe(false)
})

test("adapter preserves optimistic concurrency and idempotency headers", async () => {
  const requests: Request[] = []
  client.setConfig({
    baseUrl: "https://api.test",
    fetch: async (request) => {
      requests.push(request instanceof Request ? request : new Request(request))
      return new Response(
        JSON.stringify({ data: {}, meta: { request_id: "test" } }),
        {
          status: 200,
          headers: { "content-type": "application/json" },
        },
      )
    },
  })

  await QueryPlansApi.update(
    "plan-1",
    { fields: {}, change_reason: "Reviewed" },
    7,
  )
  await LiteratureApi.importDoi("project-1", { doi: "10.1000/reca" }, "doi-key")
  await DocumentsApi.parse(
    "document-1",
    { allow_fallback: true, extract_coordinates: true },
    "parse-key",
  )

  expect(requests[0].headers.get("if-match")).toBe('"7"')
  expect(requests[1].headers.get("idempotency-key")).toBe("doi-key")
  expect(requests[2].headers.get("idempotency-key")).toBe("parse-key")
})
