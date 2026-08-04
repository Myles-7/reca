import { expect, test } from "@playwright/test"

import type { CleaningPlanDto } from "../src/api/adapter"
import {
  dataWorkspaceEmptyFixture,
  dataWorkspacePlanDraftFixture,
  dataWorkspacePlanReadyFixture,
  dataWorkspaceReadyFixture,
  dataWorkspaceXlsxFixture,
} from "../src/features/data-workspace/fixtures"
import { mapCleaningPlan } from "../src/features/data-workspace/mappers"
import type { DataWorkspaceViewModel } from "../src/features/data-workspace/model"
import { canExecuteDataWorkspaceEvent } from "../src/features/data-workspace/mutations"
import { parseDataWorkspaceSearch } from "../src/features/data-workspace/route-contract"
import type { DataWorkspaceWorkspaceProps } from "../src/features/data-workspace/ui/contracts"

function readyData(props: DataWorkspaceWorkspaceProps): DataWorkspaceViewModel {
  if (props.content.state !== "ready") throw new Error("Expected ready fixture")
  return props.content.data
}

test("M4 empty and XLSX fixtures project executable capabilities consistently", () => {
  const empty = readyData(dataWorkspaceEmptyFixture)
  expect(empty.datasets).toEqual([])
  expect(empty.capabilities.uploadDataset.allowed).toBe(true)

  const xlsx = readyData(dataWorkspaceXlsxFixture)
  expect(xlsx.version?.status).toBe("CREATING")
  expect(xlsx.capabilities.selectWorksheet.allowed).toBe(true)
  expect(
    canExecuteDataWorkspaceEvent(xlsx, {
      action: "select-worksheet",
      input: {
        versionId: xlsx.version!.id,
        worksheetName: "Archive",
        acknowledgeHidden: true,
      },
    }),
  ).toBe(true)
})

test("M4 Plan fixtures keep workspace capabilities aligned with formal Plan actions", () => {
  const draft = readyData(dataWorkspacePlanDraftFixture)
  expect(draft.plan?.allowedActions.has("cleaning_plan.preview")).toBe(true)
  expect(draft.capabilities.updatePlan.allowed).toBe(true)
  expect(draft.capabilities.previewPlan.allowed).toBe(true)
  expect(draft.capabilities.requestApproval.allowed).toBe(false)

  const ready = readyData(dataWorkspacePlanReadyFixture)
  expect(ready.plan?.allowedActions.has("cleaning_plan.request_approval")).toBe(
    true,
  )
  expect(ready.capabilities.updatePlan.allowed).toBe(false)
  expect(ready.capabilities.requestApproval.allowed).toBe(true)
})

test("typed Cleaning Actions map all M4 executable variants and fail closed", () => {
  const dto: CleaningPlanDto = {
    id: "plan-typed",
    project_id: "project-1",
    dataset_version_id: "version-1",
    title: "Typed plan",
    rationale: "Deterministic actions only",
    status: "DRAFT",
    actions: [
      {
        action_type: "MARK_MISSING",
        target_columns: ["column-1"],
        row_selector: { selector_type: "ALL_ROWS" },
        parameters: { replacement: null },
        reason: "Normalize missing markers",
        source_issue_ids: [],
      },
      {
        action_type: "REPLACE_VALUE",
        target_columns: ["column-1"],
        row_selector: {
          selector_type: "VALUE_EQUALS",
          column_id: "column-1",
          value: "N/A",
        },
        parameters: { replacement: null },
        reason: "Replace explicit marker",
        source_issue_ids: [],
      },
      {
        action_type: "MAP_CATEGORY",
        target_columns: ["column-2"],
        row_selector: { selector_type: "ALL_ROWS" },
        parameters: { mapping: { Control: "control" } },
        reason: "Normalize category labels",
        source_issue_ids: [],
      },
      {
        action_type: "CAST_TYPE",
        target_columns: ["column-3"],
        row_selector: { selector_type: "ALL_ROWS" },
        parameters: { target_type: "NUMERIC", on_invalid: "FAIL" },
        reason: "Confirm numeric representation",
        source_issue_ids: [],
      },
      {
        action_type: "RENAME_COLUMN",
        target_columns: ["column-4"],
        row_selector: { selector_type: "ALL_ROWS" },
        parameters: { new_name: "outcome_score" },
        reason: "Use the reviewed field name",
        source_issue_ids: [],
      },
    ],
    preview_summary: null,
    preview_hash: null,
    affected_row_count: null,
    affected_column_count: null,
    source_model_invocation_id: null,
    approval_record_id: null,
    payload_hash: null,
    lock_version: 1,
    transformation_id: null,
    job_id: null,
    created_at: "2026-08-04T00:00:00Z",
    updated_at: "2026-08-04T00:00:00Z",
    allowed_actions: ["cleaning_plan.update", "cleaning_plan.preview"],
  }

  const mapped = mapCleaningPlan(dto)
  expect(mapped.actionsEditable).toBe(true)
  expect(mapped.editorActions.map((action) => action.type)).toEqual([
    "MARK_MISSING",
    "REPLACE_VALUE",
    "MAP_CATEGORY",
    "CAST_TYPE",
    "RENAME_COLUMN",
  ])

  const unavailable = mapCleaningPlan({
    ...dto,
    actions: [
      {
        action_type: "DROP_ROWS",
        target_columns: ["column-1"],
        row_selector: { selector_type: "ALL_ROWS" },
        parameters: {},
        reason: "Unavailable in M4",
        source_issue_ids: [],
      },
    ],
  })
  expect(unavailable.actionsEditable).toBe(false)
  expect(unavailable.editorActions).toEqual([])
})

test("create, update and compare guards require typed facts and capabilities", () => {
  const draft = readyData(dataWorkspacePlanDraftFixture)
  const action = draft.plan!.editorActions[0]
  expect(
    canExecuteDataWorkspaceEvent(draft, {
      action: "update-plan",
      input: {
        planId: draft.plan!.id,
        lockVersion: draft.plan!.lockVersion,
        title: "Updated plan",
        rationale: "Reviewed",
        actions: [action],
      },
    }),
  ).toBe(true)

  const ready = readyData(dataWorkspaceReadyFixture)
  expect(ready.integrationPending).toEqual([])
  expect(
    canExecuteDataWorkspaceEvent(ready, {
      action: "create-plan",
      input: {
        versionId: ready.version!.id,
        title: "New deterministic plan",
        rationale: "Focused Stage 4.5 contract coverage",
        actions: [action],
      },
    }),
  ).toBe(true)

  expect(
    canExecuteDataWorkspaceEvent(draft, {
      action: "compare-versions",
      input: {
        datasetId: draft.dataset!.id,
        baseVersionId: draft.version!.parentVersionId!,
        targetVersionId: draft.version!.id,
      },
    }),
  ).toBe(true)
})

test("M4 production search accepts only frozen UUIDs and views", () => {
  const dataset = "11111111-1111-4111-8111-111111111111"
  expect(
    parseDataWorkspaceSearch({
      dataset,
      approval: "22222222-2222-4222-8222-222222222222",
      view: "versions",
      job: "not-a-uuid",
      unexpected: "ignored",
    }),
  ).toEqual({
    dataset,
    version: undefined,
    qualityRun: undefined,
    plan: undefined,
    approval: "22222222-2222-4222-8222-222222222222",
    job: undefined,
    compareWith: undefined,
    view: "versions",
  })
  expect(parseDataWorkspaceSearch({ view: "future-view" }).view).toBeUndefined()
})
