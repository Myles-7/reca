import type { SemanticTone } from "../projects/model"

export const queryPlanRoute =
  "/projects/$projectId/query-plans/$queryPlanId" as const

export type QueryPlanFieldsViewModel = {
  chineseTerms: readonly string[]
  englishTerms: readonly string[]
  synonyms: Readonly<Record<string, readonly string[]>>
  objectTerms: Readonly<Record<string, readonly string[]>>
  methodTerms: Readonly<Record<string, readonly string[]>>
  booleanQuery: string | null
  filters: {
    fromYear: number | null
    toYear: number | null
    languages: readonly string[]
    workTypes: readonly string[]
    openAccessOnly: boolean
  }
  limitations: readonly string[]
}

export type QueryPlanViewModel = {
  id: string
  projectId: string
  researchQuestionVersionId: string
  status: string
  knownStatus: boolean
  permissionsKnown: boolean
  tone: SemanticTone
  lockVersion: number
  fields: QueryPlanFieldsViewModel
  permissions: { canUpdate: boolean; canGenerate: boolean }
  generatedByAi: boolean
  updatedAt: string
}

export function queryPlanHref(projectId: string, queryPlanId: string): string {
  return queryPlanRoute
    .replace("$projectId", projectId)
    .replace("$queryPlanId", queryPlanId)
}
