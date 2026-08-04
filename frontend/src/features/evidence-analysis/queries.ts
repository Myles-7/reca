import { useQuery } from "@tanstack/react-query"

import { ApiError, EvidenceApi } from "@/api/adapter"

import { mapEvidenceAnalysisCapabilities, mapEvidenceSummary } from "./mappers"

export const evidenceAnalysisKeys = {
  capabilities: (projectId: string) =>
    ["projects", projectId, "evidence-analysis-capabilities"] as const,
  summary: (summaryId: string) =>
    ["evidence-set-summaries", summaryId] as const,
}

export function useEvidenceAnalysisCapabilitiesQuery(projectId: string) {
  return useQuery({
    queryKey: evidenceAnalysisKeys.capabilities(projectId),
    queryFn: async () =>
      mapEvidenceAnalysisCapabilities(
        await EvidenceApi.matrix(projectId, { page: 1, page_size: 1 }),
      ),
    retry: (count, error) =>
      !(error instanceof ApiError && [401, 403, 404].includes(error.status)) &&
      count < 2,
  })
}

export function useEvidenceSummaryQuery(projectId: string, summaryId?: string) {
  return useQuery({
    queryKey: evidenceAnalysisKeys.summary(summaryId ?? "none"),
    queryFn: async () => {
      const response = await EvidenceApi.summary(summaryId!)
      if (response.data.project_id !== projectId) {
        throw new ApiError(
          404,
          "NOT_FOUND",
          "The evidence summary does not match this project route.",
          "SUMMARY_ROUTE_MISMATCH",
        )
      }
      return mapEvidenceSummary(response.data)
    },
    enabled: Boolean(summaryId),
    retry: (count, error) =>
      !(error instanceof ApiError && [401, 403, 404].includes(error.status)) &&
      count < 2,
  })
}
