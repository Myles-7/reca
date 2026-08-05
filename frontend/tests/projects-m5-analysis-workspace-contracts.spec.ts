import { expect, test } from "@playwright/test"

import type {
  AnalysisPlanPublic,
  AnalysisResultPublic,
} from "../src/api/adapter"
import {
  analysisWorkspaceFigureReadyFixture,
  analysisWorkspaceFixtureCatalog,
  analysisWorkspaceJobCancelAllowedFixture,
  analysisWorkspaceJobRetryAllowedFixture,
  analysisWorkspacePermissionsUnknownFixture,
  analysisWorkspacePlanStaleFixture,
  analysisWorkspaceReadyFixture,
} from "../src/features/analysis-workspace/fixtures"
import {
  mapAnalysisPlan,
  mapAnalysisResult,
} from "../src/features/analysis-workspace/mappers"
import type { AnalysisWorkspaceViewModel } from "../src/features/analysis-workspace/model"
import {
  apiPlanUpdate,
  canExecuteAnalysisWorkspaceEvent,
} from "../src/features/analysis-workspace/mutations"
import { parseAnalysisWorkspaceSearch } from "../src/features/analysis-workspace/route-contract"
import type { AnalysisWorkspaceWorkspaceProps } from "../src/features/analysis-workspace/ui/contracts"

function readyData(
  props: AnalysisWorkspaceWorkspaceProps,
): AnalysisWorkspaceViewModel {
  if (props.content.state !== "ready") throw new Error("Expected ready fixture")
  return props.content.data
}

test("M5 mapper preserves server actions, stale approval and unknown status", () => {
  const dto = {
    id: "44444444-4444-4444-8444-444444444444",
    project_id: "11111111-1111-4111-8111-111111111111",
    research_question_version_id: "14141414-1414-4414-8414-141414141414",
    dataset_version_id: "33333333-3333-4333-8333-333333333333",
    analysis_goal: "CORRELATION",
    method: "PEARSON_CORRELATION",
    dependent_variable_ids: ["13131313-1313-4313-8313-131313131313"],
    independent_variable_ids: ["12121212-1212-4212-8212-121212121212"],
    control_variable_ids: [],
    missing_data_policy: { mode: "COMPLETE_CASE" },
    sample_filter: null,
    parameters: { confidence_level: 0.95 },
    status: "APPROVED",
    validation_hash: "1".repeat(64),
    validation_warnings: [],
    approval_record_id: "55555555-5555-4555-8555-555555555555",
    payload_hash: "2".repeat(64),
    approval_stale: true,
    lock_version: 2,
    created_by: null,
    created_at: "2026-08-04T00:00:00Z",
    updated_at: "2026-08-04T00:00:00Z",
    invalidated_at: null,
    invalidation_reason: null,
    checks: [],
    allowed_actions: ["analysis_plan.read", "analysis_plan.run"],
  } satisfies AnalysisPlanPublic
  const mapped = mapAnalysisPlan(dto)
  expect(mapped.approvalStale).toBe(true)
  expect(mapped.permissionsKnown).toBe(true)
  expect(mapped.allowedActions.has("analysis_plan.run")).toBe(true)

  const future = mapAnalysisPlan({ ...dto, status: "FUTURE" as never })
  expect(future.knownStatus).toBe(false)
})

test("M5 result mapper keeps deterministic numbers numeric and interpretation separate", () => {
  const dto = {
    id: "77777777-7777-4777-8777-777777777777",
    project_id: "11111111-1111-4111-8111-111111111111",
    analysis_run_id: "66666666-6666-4666-8666-666666666666",
    result_key: "correlation",
    result_type: "CORRELATION",
    schema_version: "1.0",
    is_primary: true,
    payload: { coefficient: 0.4123456789012345, p_value: null },
    result_hash: "a".repeat(64),
    created_at: "2026-08-04T00:00:00Z",
  } satisfies AnalysisResultPublic
  const mapped = mapAnalysisResult(dto, "COMPLETED")
  expect(mapped.payload.coefficient).toBe(0.4123456789012345)
  expect(mapped.payload.p_value).toBeNull()
  expect(mapped.deterministic).toBe(true)
  expect(mapped.interpretation).toBeNull()
})

test("M5 mutation guards fail closed and accept only current formal relationships", () => {
  const ready = readyData(analysisWorkspaceReadyFixture)
  expect(
    canExecuteAnalysisWorkspaceEvent(ready, {
      action: "run-analysis",
      input: { planId: ready.plan!.id, reason: null },
    }),
  ).toBe(true)

  const stale = readyData(analysisWorkspacePlanStaleFixture)
  expect(
    canExecuteAnalysisWorkspaceEvent(stale, {
      action: "run-analysis",
      input: { planId: stale.plan!.id, reason: null },
    }),
  ).toBe(false)

  const unknown = readyData(analysisWorkspacePermissionsUnknownFixture)
  expect(
    canExecuteAnalysisWorkspaceEvent(unknown, {
      action: "run-analysis",
      input: { planId: unknown.plan!.id, reason: null },
    }),
  ).toBe(false)

  const figure = readyData(analysisWorkspaceFigureReadyFixture)
  expect(figure.figure?.transportAvailable).toBe(true)
  expect(
    canExecuteAnalysisWorkspaceEvent(figure, {
      action: "download-artifact",
      input: { figureId: figure.figure!.id, format: "PNG" },
    }),
  ).toBe(true)

  const retry = readyData(analysisWorkspaceJobRetryAllowedFixture)
  expect(
    canExecuteAnalysisWorkspaceEvent(retry, {
      action: "retry-job",
      input: { jobId: retry.job!.id },
    }),
  ).toBe(true)
  const cancel = readyData(analysisWorkspaceJobCancelAllowedFixture)
  expect(
    canExecuteAnalysisWorkspaceEvent(cancel, {
      action: "cancel-job",
      input: { jobId: cancel.job!.id, reason: "Stop requested." },
    }),
  ).toBe(true)
})

test("M5 PATCH payload excludes immutable create-only fields", () => {
  const ready = readyData(analysisWorkspaceReadyFixture)
  const payload = apiPlanUpdate(ready.plan!.input)
  expect(payload).not.toHaveProperty("research_question_version_id")
  expect(payload).not.toHaveProperty("dataset_version_id")
  expect(payload.method).toBe("PEARSON_CORRELATION")
})

test("M5 route search accepts only frozen UUID keys and views", () => {
  const dataset = "22222222-2222-4222-8222-222222222222"
  expect(
    parseAnalysisWorkspaceSearch({
      dataset,
      analysisPlan: "44444444-4444-4444-8444-444444444444",
      figure: "not-a-uuid",
      view: "results",
      unexpected: "ignored",
    }),
  ).toEqual({
    dataset,
    version: undefined,
    analysisPlan: "44444444-4444-4444-8444-444444444444",
    analysisRun: undefined,
    analysisResult: undefined,
    approval: undefined,
    job: undefined,
    figurePlan: undefined,
    figure: undefined,
    renderRun: undefined,
    view: "results",
  })
})

test("M5 typed fixture catalog covers the required workspace state families", () => {
  const names = analysisWorkspaceFixtureCatalog.map(([name]) => name)
  for (const required of [
    "ready",
    "loading",
    "empty",
    "forbidden",
    "read-only",
    "permissions-unknown",
    "degraded",
    "unknown",
    "plan-stale",
    "analysis-failed-retryable",
    "correlation-non-significant",
    "figure-needs-review",
    "desktop-light",
    "tablet-dark",
    "mobile-light",
  ]) {
    expect(names).toContain(required)
  }
})
