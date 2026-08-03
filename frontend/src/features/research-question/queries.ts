import { useQuery } from "@tanstack/react-query"

import {
  ApiError,
  type CurrentResearchQuestionEnvelope,
  ResearchQuestionsApi,
  type ResearchQuestionVersionPublic,
} from "@/api/adapter"

import { mapResearchQuestion } from "./mappers"

export type ResearchQuestionQueryPort = {
  getCurrent: (projectId: string) => Promise<CurrentResearchQuestionEnvelope>
  listVersions: (
    researchQuestionId: string,
  ) => Promise<{ data: ResearchQuestionVersionPublic[] }>
}

export const researchQuestionQueryPort: ResearchQuestionQueryPort = {
  getCurrent: ResearchQuestionsApi.current,
  listVersions: ResearchQuestionsApi.listVersions,
}

export const researchQuestionKeys = {
  current: (projectId: string) =>
    ["projects", projectId, "research-question"] as const,
}

export function validateResearchQuestionProjection(
  projectId: string,
  current: CurrentResearchQuestionEnvelope,
  versions: readonly ResearchQuestionVersionPublic[],
): void {
  const question = current.data.question
  if (!question) return
  const matches =
    question.project_id === projectId &&
    question.current_version_id === question.current_version.id &&
    question.current_version.project_id === projectId &&
    question.current_version.research_question_id === question.id &&
    versions.every(
      (version) =>
        version.project_id === projectId &&
        version.research_question_id === question.id,
    )
  if (!matches) {
    throw new ApiError(
      404,
      "NOT_FOUND",
      "The research question projection does not match this project route.",
      "RESEARCH_QUESTION_ROUTE_MISMATCH",
    )
  }
}

export async function loadResearchQuestion(
  projectId: string,
  port: ResearchQuestionQueryPort = researchQuestionQueryPort,
) {
  const current = await port.getCurrent(projectId)
  validateResearchQuestionProjection(projectId, current, [])
  const versions = current.data.question
    ? (await port.listVersions(current.data.question.id)).data
    : []
  validateResearchQuestionProjection(projectId, current, versions)
  return mapResearchQuestion({ current, versions })
}

export function useResearchQuestionQuery(projectId: string) {
  return useQuery({
    queryKey: researchQuestionKeys.current(projectId),
    queryFn: () => loadResearchQuestion(projectId),
    retry: (failureCount, error) => {
      if (error instanceof ApiError && [401, 403, 404].includes(error.status)) {
        return false
      }
      return failureCount < 2
    },
  })
}
