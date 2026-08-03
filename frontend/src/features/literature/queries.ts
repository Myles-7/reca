import { useQuery } from "@tanstack/react-query"

import {
  ApiError,
  JobsApi,
  LiteratureApi,
  type LiteratureRecordListEnvelope,
  type LiteratureSearchResultsEnvelope,
  ProjectsApi,
} from "@/api/adapter"

import {
  mapLiteratureCandidate,
  mapLiteratureRecord,
  mapLiteratureSearchRun,
} from "./mappers"

export const literatureKeys = {
  records: (projectId: string) =>
    ["projects", projectId, "literature", "records"] as const,
  searchRun: (searchRunId: string) =>
    ["literature-search-runs", searchRunId, "results"] as const,
  job: (jobId: string) => ["jobs", jobId] as const,
  retryPermission: (projectId: string) =>
    ["projects", projectId, "literature", "retry-permission"] as const,
}

const retry = (failureCount: number, error: Error) => {
  if (error instanceof ApiError && [401, 403, 404].includes(error.status)) {
    return false
  }
  return failureCount < 2
}

function validateResultsRoute(
  projectId: string,
  searchRunId: string,
  results: LiteratureSearchResultsEnvelope,
) {
  const run = results.data.search_run
  const matches =
    run.id === searchRunId &&
    run.project_id === projectId &&
    results.data.results.every(
      (candidate) =>
        candidate.project_id === projectId &&
        candidate.search_run_id === searchRunId,
    )
  if (!matches) {
    throw new ApiError(
      404,
      "NOT_FOUND",
      "The literature search projection does not match this project route.",
      "LITERATURE_ROUTE_MISMATCH",
    )
  }
  return results
}

function validateRecordsRoute(
  projectId: string,
  records: LiteratureRecordListEnvelope,
) {
  if (records.data.some((record) => record.project_id !== projectId)) {
    throw new ApiError(
      404,
      "NOT_FOUND",
      "The literature record projection does not match this project route.",
      "LITERATURE_ROUTE_MISMATCH",
    )
  }
  return records
}

export function useLiteratureQuery(projectId: string, searchRunId?: string) {
  const records = useQuery({
    queryKey: literatureKeys.records(projectId),
    queryFn: async () =>
      validateRecordsRoute(projectId, await LiteratureApi.list(projectId)),
    retry,
  })
  const results = useQuery({
    queryKey: literatureKeys.searchRun(searchRunId ?? "none"),
    queryFn: async () =>
      validateResultsRoute(
        projectId,
        searchRunId!,
        await LiteratureApi.results(searchRunId!),
      ),
    enabled: Boolean(searchRunId),
    retry,
  })
  const jobId = results.data?.data.search_run.job_id ?? null
  const job = useQuery({
    queryKey: literatureKeys.job(jobId ?? "none"),
    queryFn: () => JobsApi.get(jobId!),
    enabled: jobId !== null,
    retry,
  })
  const project = useQuery({
    queryKey: literatureKeys.retryPermission(projectId),
    queryFn: () => ProjectsApi.get(projectId),
    retry,
  })

  const coreLoading =
    records.isLoading || (Boolean(searchRunId) && results.isLoading)
  const coreError = records.error ?? results.error
  const data = records.data
    ? mapLiteratureWorkspace(
        records.data,
        results.data ?? null,
        job.data?.data ?? null,
        project.data?.data ?? null,
      )
    : undefined

  return {
    data: coreLoading || coreError ? undefined : data,
    error: coreError,
    isLoading: coreLoading,
    refetch: async () => {
      const reloads: Promise<unknown>[] = [records.refetch()]
      if (searchRunId) reloads.push(results.refetch())
      if (jobId) reloads.push(job.refetch())
      reloads.push(project.refetch())
      await Promise.all(reloads)
    },
  }
}

function mapLiteratureWorkspace(
  records: LiteratureRecordListEnvelope,
  results: LiteratureSearchResultsEnvelope | null,
  job: Parameters<typeof mapLiteratureSearchRun>[1],
  project: Parameters<typeof mapLiteratureSearchRun>[2],
) {
  const recordActionsKnown = Array.isArray(records.allowed_actions)
  const resultActionsKnown =
    results === null ||
    (Array.isArray(results.data.search_run.allowed_actions) &&
      results.data.results.every((candidate) =>
        Array.isArray(candidate.allowed_actions),
      ))
  const permissionsKnown = recordActionsKnown && resultActionsKnown
  return {
    records: records.data.map(mapLiteratureRecord),
    activeSearch: results
      ? mapLiteratureSearchRun(results.data.search_run, job, project)
      : null,
    candidates: results ? results.data.results.map(mapLiteratureCandidate) : [],
    permissionsKnown,
    permissions: {
      canSearch:
        permissionsKnown &&
        records.allowed_actions.includes("literature.search"),
      canImport:
        permissionsKnown &&
        (results?.data.search_run.allowed_actions.includes(
          "literature_search.import",
        ) ??
          false),
      canImportDoi:
        permissionsKnown &&
        records.allowed_actions.includes("literature.import_doi"),
    },
  }
}
