import { useMutation, useQueryClient } from "@tanstack/react-query"

import {
  DataCleaningApi,
  DataQualityApi,
  DatasetsApi,
  JobsApi,
} from "@/api/adapter"
import type { CleaningPlanCreate } from "@/api/generated/types.gen"

import { mapUiError } from "../projects/mappers"
import type {
  CleaningActionInput,
  CleaningRowSelector,
  DataWorkspaceViewModel,
} from "./model"
import { dataWorkspaceKeys } from "./queries"
import type { DataWorkspaceEvent } from "./ui/contracts"

const key = () => crypto.randomUUID()

type ApiCleaningAction = CleaningPlanCreate["actions"][number]

function toApiRowSelector(selector: CleaningRowSelector) {
  switch (selector.type) {
    case "ALL_ROWS":
      return { selector_type: "ALL_ROWS" as const }
    case "ISSUE_ROWS":
      return {
        selector_type: "ISSUE_ROWS" as const,
        issue_ids: [...selector.issueIds],
      }
    case "VALUE_EQUALS":
      return {
        selector_type: "VALUE_EQUALS" as const,
        column_id: selector.columnId,
        value: selector.value,
      }
    case "VALUE_IN":
      return {
        selector_type: "VALUE_IN" as const,
        column_id: selector.columnId,
        values: [...selector.values],
      }
    case "IS_NULL":
    case "IS_NOT_NULL":
      return { selector_type: selector.type, column_id: selector.columnId }
    case "NUMERIC_RANGE":
      return {
        selector_type: "NUMERIC_RANGE" as const,
        column_id: selector.columnId,
        minimum: selector.minimum,
        maximum: selector.maximum,
        include_minimum: selector.includeMinimum,
        include_maximum: selector.includeMaximum,
      }
  }
}

function toApiCleaningAction(action: CleaningActionInput): ApiCleaningAction {
  const common = {
    target_columns: [...action.targetColumnIds],
    row_selector: toApiRowSelector(action.rowSelector),
    reason: action.reason,
    source_issue_ids: [...action.sourceIssueIds],
  }
  switch (action.type) {
    case "MARK_MISSING":
      return {
        ...common,
        action_type: "MARK_MISSING",
        parameters: { replacement: null },
      }
    case "REPLACE_VALUE":
      return {
        ...common,
        action_type: "REPLACE_VALUE",
        parameters: { replacement: action.parameters.replacement },
      }
    case "MAP_CATEGORY":
      return {
        ...common,
        action_type: "MAP_CATEGORY",
        parameters: { mapping: { ...action.parameters.mapping } },
      }
    case "CAST_TYPE":
      return {
        ...common,
        action_type: "CAST_TYPE",
        parameters: {
          target_type: action.parameters.targetType,
          on_invalid: action.parameters.onInvalid,
        },
      }
    case "RENAME_COLUMN":
      return {
        ...common,
        action_type: "RENAME_COLUMN",
        parameters: { new_name: action.parameters.newName },
      }
  }
}

function validCleaningActions(actions: readonly CleaningActionInput[]) {
  const validSelector = (selector: CleaningRowSelector) => {
    switch (selector.type) {
      case "ALL_ROWS":
        return true
      case "ISSUE_ROWS":
        return (
          selector.issueIds.length > 0 &&
          selector.issueIds.length <= 50 &&
          new Set(selector.issueIds).size === selector.issueIds.length
        )
      case "VALUE_EQUALS":
      case "IS_NULL":
      case "IS_NOT_NULL":
        return selector.columnId.length > 0
      case "VALUE_IN":
        return (
          selector.columnId.length > 0 &&
          selector.values.length > 0 &&
          selector.values.length <= 100
        )
      case "NUMERIC_RANGE":
        return (
          selector.columnId.length > 0 &&
          (selector.minimum !== null || selector.maximum !== null) &&
          !(
            selector.minimum !== null &&
            selector.maximum !== null &&
            selector.minimum > selector.maximum
          )
        )
    }
  }
  const validParameters = (action: CleaningActionInput) => {
    switch (action.type) {
      case "MARK_MISSING":
        return action.parameters.replacement === null
      case "REPLACE_VALUE":
        return true
      case "MAP_CATEGORY": {
        const entries = Object.entries(action.parameters.mapping)
        return (
          action.targetColumnIds.length === 1 &&
          entries.length > 0 &&
          entries.length <= 100 &&
          entries.every(([key]) => key.length > 0 && key.length <= 256)
        )
      }
      case "CAST_TYPE":
        return [
          "STRING",
          "INTEGER",
          "NUMERIC",
          "BOOLEAN",
          "DATE",
          "DATETIME",
        ].includes(action.parameters.targetType)
      case "RENAME_COLUMN":
        return (
          action.targetColumnIds.length === 1 &&
          action.rowSelector.type === "ALL_ROWS" &&
          action.parameters.newName.trim().length > 0 &&
          action.parameters.newName.length <= 255
        )
    }
  }
  return (
    actions.length > 0 &&
    actions.length <= 50 &&
    actions.every(
      (action) =>
        action.targetColumnIds.length > 0 &&
        action.targetColumnIds.length <= 20 &&
        new Set(action.targetColumnIds).size ===
          action.targetColumnIds.length &&
        action.reason.trim().length > 0 &&
        action.reason.length <= 2000 &&
        action.sourceIssueIds.length <= 50 &&
        new Set(action.sourceIssueIds).size === action.sourceIssueIds.length &&
        validSelector(action.rowSelector) &&
        validParameters(action),
    )
  )
}

export function canExecuteDataWorkspaceEvent(
  workspace: DataWorkspaceViewModel | null,
  event: DataWorkspaceEvent,
) {
  if (!workspace?.capabilities.permissionsKnown) return false
  const capabilities = workspace.capabilities
  switch (event.action) {
    case "upload-dataset":
      return (
        capabilities.uploadDataset.allowed && event.input.name.trim().length > 0
      )
    case "select-worksheet":
      return (
        capabilities.selectWorksheet.allowed &&
        workspace.version?.id === event.input.versionId
      )
    case "update-dataset-identity":
      return (
        capabilities.updateDatasetIdentity.allowed &&
        workspace.dataset?.id === event.input.datasetId
      )
    case "update-column":
      return (
        capabilities.updateColumn.allowed &&
        workspace.columns.some((column) => column.id === event.input.columnId)
      )
    case "select-version":
      return workspace.datasets.some(
        (dataset) =>
          dataset.id === event.input.datasetId &&
          dataset.currentVersionId === event.input.versionId,
      )
    case "compare-versions":
      return (
        capabilities.compareVersions.allowed &&
        workspace.dataset?.id === event.input.datasetId &&
        workspace.version?.id === event.input.targetVersionId &&
        workspace.version.parentVersionId === event.input.baseVersionId
      )
    case "run-quality":
      return (
        capabilities.runQuality.allowed &&
        workspace.version?.id === event.input.versionId
      )
    case "acknowledge-issue":
      return (
        capabilities.acknowledgeIssue.allowed &&
        workspace.issues.some(
          (issue) =>
            issue.id === event.input.issueId &&
            issue.allowedActions.has("data_quality_issue.acknowledge"),
        )
      )
    case "ignore-issue":
      return (
        capabilities.ignoreIssue.allowed &&
        event.input.reason.trim().length > 0 &&
        workspace.issues.some(
          (issue) =>
            issue.id === event.input.issueId &&
            issue.allowedActions.has("data_quality_issue.ignore"),
        )
      )
    case "create-plan":
      return (
        capabilities.createPlan.allowed &&
        workspace.version?.id === event.input.versionId &&
        event.input.title.trim().length > 0 &&
        event.input.title.length <= 255 &&
        (event.input.rationale === null ||
          event.input.rationale.length <= 5000) &&
        validCleaningActions(event.input.actions)
      )
    case "update-plan":
      return (
        capabilities.updatePlan.allowed &&
        workspace.plan?.id === event.input.planId &&
        workspace.plan.lockVersion === event.input.lockVersion &&
        (event.input.title === undefined ||
          (event.input.title.trim().length > 0 &&
            event.input.title.length <= 255)) &&
        (event.input.rationale === undefined ||
          event.input.rationale === null ||
          event.input.rationale.length <= 5000) &&
        (event.input.actions === undefined ||
          validCleaningActions(event.input.actions))
      )
    case "preview-plan":
      return (
        capabilities.previewPlan.allowed &&
        workspace.plan?.id === event.input.planId
      )
    case "request-approval":
      return (
        capabilities.requestApproval.allowed &&
        workspace.plan?.id === event.input.planId
      )
    case "execute-plan":
      return (
        capabilities.executePlan.allowed &&
        workspace.plan?.id === event.input.planId
      )
    case "retry-job":
      return (
        capabilities.retryJob.allowed && workspace.job?.id === event.input.jobId
      )
  }
}

async function execute(projectId: string, event: DataWorkspaceEvent) {
  switch (event.action) {
    case "upload-dataset":
      return DatasetsApi.upload(projectId, event.input, key())
    case "select-worksheet":
      return DatasetsApi.selectWorksheet(
        event.input.versionId,
        {
          worksheet_name: event.input.worksheetName,
          acknowledge_hidden: event.input.acknowledgeHidden,
        },
        key(),
      )
    case "update-dataset-identity":
      return DatasetsApi.update(
        event.input.datasetId,
        {
          name: event.input.changes.name,
          description: event.input.changes.description,
          publisher: event.input.changes.publisher,
          license_name: event.input.changes.licenseName,
        },
        event.input.lockVersion,
      )
    case "update-column":
      return DatasetsApi.updateColumn(
        event.input.columnId,
        {
          display_name: event.input.changes.displayName,
          confirmed_type: event.input.changes.confirmedType as never,
          semantic_role: event.input.changes.semanticRole as never,
          unit: event.input.changes.unit,
          is_sensitive: event.input.changes.isSensitive,
          confirmation_status: event.input.changes.confirmationStatus,
        },
        event.input.lockVersion,
      )
    case "run-quality":
      return DataQualityApi.run(
        event.input.versionId,
        {
          rule_set: "RECA_P0_DEFAULT",
          include_sensitive_field_detection: true,
        },
        key(),
      )
    case "acknowledge-issue":
      return DataQualityApi.acknowledge(event.input.issueId, key())
    case "ignore-issue":
      return DataQualityApi.ignore(
        event.input.issueId,
        event.input.reason,
        key(),
      )
    case "create-plan":
      return DataCleaningApi.create(
        event.input.versionId,
        {
          title: event.input.title,
          rationale: event.input.rationale,
          actions: event.input.actions.map(toApiCleaningAction),
        },
        key(),
      )
    case "update-plan":
      return DataCleaningApi.update(
        event.input.planId,
        {
          title: event.input.title,
          rationale: event.input.rationale,
          actions: event.input.actions?.map(toApiCleaningAction),
        },
        event.input.lockVersion,
      )
    case "preview-plan":
      return DataCleaningApi.preview(event.input.planId, key())
    case "request-approval":
      return DataCleaningApi.requestApproval(event.input.planId, key())
    case "execute-plan":
      return DataCleaningApi.execute(event.input.planId, key())
    case "retry-job":
      return JobsApi.retry(event.input.jobId, key())
    case "select-version":
    case "compare-versions":
      return null
  }
}

export function useDataWorkspaceMutation(
  projectId: string,
  workspace: DataWorkspaceViewModel | null,
  onSuccess?: (
    event: DataWorkspaceEvent,
    result: Awaited<ReturnType<typeof execute>>,
  ) => void,
) {
  const queryClient = useQueryClient()
  const mutation = useMutation({
    mutationFn: (event: DataWorkspaceEvent) => execute(projectId, event),
    onSuccess: async (result, event) => {
      await queryClient.invalidateQueries({
        queryKey: dataWorkspaceKeys.workspace(projectId, {}),
        exact: false,
      })
      onSuccess?.(event, result)
    },
  })
  return {
    mutate: (event: DataWorkspaceEvent) => {
      if (canExecuteDataWorkspaceEvent(workspace, event)) mutation.mutate(event)
    },
    pendingAction: mutation.isPending
      ? (mutation.variables?.action ?? null)
      : null,
    uiError: mutation.error ? mapUiError(mutation.error) : null,
  }
}
