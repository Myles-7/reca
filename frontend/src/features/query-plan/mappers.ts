import type { QueryPlanPublic } from "@/api/adapter"

import type { QueryPlanFieldsViewModel, QueryPlanViewModel } from "./model"

export function mapQueryPlanFields(
  plan: QueryPlanPublic,
): QueryPlanFieldsViewModel {
  const filters = plan.filters ?? {}
  return {
    chineseTerms: plan.chinese_terms ?? [],
    englishTerms: plan.english_terms ?? [],
    synonyms: plan.synonyms ?? {},
    objectTerms: plan.object_terms ?? {},
    methodTerms: plan.method_terms ?? {},
    booleanQuery: plan.boolean_query,
    filters: {
      fromYear:
        typeof filters.from_year === "number" ? filters.from_year : null,
      toYear: typeof filters.to_year === "number" ? filters.to_year : null,
      languages: Array.isArray(filters.languages)
        ? filters.languages.filter((v): v is string => typeof v === "string")
        : [],
      workTypes: Array.isArray(filters.work_types)
        ? filters.work_types.filter((v): v is string => typeof v === "string")
        : [],
      openAccessOnly: filters.open_access_only === true,
    },
    limitations: plan.limitations ?? [],
  }
}

export function mapQueryPlan(plan: QueryPlanPublic): QueryPlanViewModel {
  const knownStatus = plan.status === "DRAFT"
  const permissionsKnown = Array.isArray(plan.allowed_actions)
  const actions =
    knownStatus && permissionsKnown
      ? new Set(plan.allowed_actions)
      : new Set<string>()
  return {
    id: plan.id,
    projectId: plan.project_id,
    researchQuestionVersionId: plan.research_question_version_id,
    status: plan.status,
    knownStatus,
    permissionsKnown,
    tone: knownStatus ? "info" : "degraded",
    lockVersion: plan.lock_version,
    fields: mapQueryPlanFields(plan),
    permissions: {
      canUpdate: actions.has("query_plan.update"),
      canGenerate: actions.has("query_plan.generate"),
    },
    generatedByAi: plan.source_model_invocation_id !== null,
    updatedAt: plan.updated_at,
  }
}
