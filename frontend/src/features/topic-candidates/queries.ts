import { useQuery } from "@tanstack/react-query"
import { ApiError, EvidenceApi } from "@/api/adapter"
import { mapTopicCandidates } from "./mappers"

export const topicCandidateKeys = {
  run: (runId: string) => ["topic-generation-runs", runId] as const,
}

export function useTopicGenerationRunQuery(projectId: string, runId?: string) {
  return useQuery({
    queryKey: topicCandidateKeys.run(runId ?? "none"),
    queryFn: async () => {
      const response = await EvidenceApi.topicRun(runId!)
      if (response.data.project_id !== projectId)
        throw new ApiError(
          404,
          "NOT_FOUND",
          "The topic run does not match this project route.",
          "TOPIC_RUN_ROUTE_MISMATCH",
        )
      return mapTopicCandidates(response.data)
    },
    enabled: Boolean(runId),
    retry: (count, error) =>
      !(error instanceof ApiError && [401, 403, 404].includes(error.status)) &&
      count < 2,
  })
}
