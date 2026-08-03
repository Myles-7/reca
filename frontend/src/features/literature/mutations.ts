import type { QueryClient } from "@tanstack/react-query"
import { useMutation, useQueryClient } from "@tanstack/react-query"

import { JobsApi, LiteratureApi } from "@/api/adapter"

import { mapUiError } from "../projects/mappers"
import type { LiteratureWorkspaceViewModel } from "./model"
import { literatureKeys } from "./queries"
import type { LiteratureEvent } from "./ui/contracts"

const key = () => crypto.randomUUID()

export function canExecuteLiteratureEvent(
  workspace: LiteratureWorkspaceViewModel | null,
  event: LiteratureEvent,
): boolean {
  if (!workspace || !workspace.permissionsKnown) return false
  if (event.action === "search") {
    return (
      workspace.permissions.canSearch &&
      workspace.activeSearch?.queryPlanId === event.input.queryPlanId
    )
  }
  if (event.action === "import-candidates") {
    return (
      workspace.permissions.canImport &&
      workspace.activeSearch?.id === event.input.searchRunId &&
      event.input.candidateIds.length > 0 &&
      event.input.candidateIds.every((id) =>
        workspace.candidates.some(
          (candidate) => candidate.id === id && candidate.canImport,
        ),
      )
    )
  }
  if (event.action === "import-doi") {
    return (
      workspace.permissions.canImportDoi && event.input.doi.trim().length > 0
    )
  }
  return (
    workspace.activeSearch?.progressJobId === event.input.jobId &&
    workspace.activeSearch.canRetry
  )
}

export async function executeLiteratureEvent(
  projectId: string,
  event: LiteratureEvent,
) {
  if (event.action === "search") {
    const response = await LiteratureApi.search(
      event.input.queryPlanId,
      { page_size: event.input.pageSize, use_cache: event.input.useCache },
      key(),
    )
    return {
      action: event.action,
      searchRunId: response.data.search_run.id,
    } as const
  }
  if (event.action === "import-candidates") {
    await LiteratureApi.importCandidates(
      projectId,
      {
        search_run_id: event.input.searchRunId,
        result_ids: event.input.candidateIds,
      },
      key(),
    )
    return { action: event.action } as const
  }
  if (event.action === "import-doi") {
    await LiteratureApi.importDoi(projectId, { doi: event.input.doi }, key())
    return { action: event.action } as const
  }
  await JobsApi.retry(event.input.jobId, key())
  return { action: event.action } as const
}

export async function invalidateLiteratureMutation(
  client: QueryClient,
  projectId: string,
  searchRunId: string | undefined,
  event: LiteratureEvent,
  nextSearchRunId?: string,
) {
  const invalidations: Promise<unknown>[] = []
  if (event.action === "search" && nextSearchRunId) {
    invalidations.push(
      client.invalidateQueries({
        queryKey: literatureKeys.searchRun(nextSearchRunId),
      }),
    )
  }
  if (event.action === "import-candidates") {
    invalidations.push(
      client.invalidateQueries({ queryKey: literatureKeys.records(projectId) }),
      client.invalidateQueries({
        queryKey: literatureKeys.searchRun(event.input.searchRunId),
      }),
    )
  }
  if (event.action === "import-doi") {
    invalidations.push(
      client.invalidateQueries({ queryKey: literatureKeys.records(projectId) }),
    )
  }
  if (event.action === "retry-job") {
    invalidations.push(
      client.invalidateQueries({
        queryKey: literatureKeys.job(event.input.jobId),
      }),
    )
    if (searchRunId) {
      invalidations.push(
        client.invalidateQueries({
          queryKey: literatureKeys.searchRun(searchRunId),
        }),
      )
    }
  }
  await Promise.all(invalidations)
}

export function useLiteratureMutation(
  projectId: string,
  searchRunId: string | undefined,
  onSearchRunCreated?: (searchRunId: string) => void,
) {
  const client = useQueryClient()
  const mutation = useMutation({
    mutationFn: (event: LiteratureEvent) =>
      executeLiteratureEvent(projectId, event),
    onSuccess: async (result, event) => {
      const nextSearchRunId =
        result.action === "search" ? result.searchRunId : undefined
      await invalidateLiteratureMutation(
        client,
        projectId,
        searchRunId,
        event,
        nextSearchRunId,
      )
      if (nextSearchRunId) onSearchRunCreated?.(nextSearchRunId)
    },
  })
  return {
    mutate: mutation.mutate,
    pendingAction: mutation.isPending
      ? (mutation.variables?.action ?? null)
      : null,
    uiError: mutation.error ? mapUiError(mutation.error) : null,
  }
}
