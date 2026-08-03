import type { SemanticTone, UiErrorViewModel } from "../projects/model"

export const researchQuestionRoute =
  "/projects/$projectId/research-question" as const

export const researchQuestionVersionStatuses = [
  "DRAFT",
  "NEEDS_INPUT",
  "READY",
  "CONFIRMED",
  "SUPERSEDED",
] as const

export type ResearchQuestionVersionStatus =
  (typeof researchQuestionVersionStatuses)[number]

export type ResearchQuestionFields = {
  rawInput: string
  normalizedQuestion: string | null
  researchObject: string | null
  population: string | null
  context: string | null
  independentVariables: string[]
  dependentVariables: string[]
  controlVariables: string[]
  researchGoal: "DESCRIBE" | "COMPARE" | "RELATE" | "PREDICT" | null
  relationshipType:
    | "ASSOCIATION"
    | "COMPARISON"
    | "PREDICTION"
    | "UNSPECIFIED"
    | null
  methodPreference: Readonly<Record<string, unknown>> | null
  timeScope: Readonly<Record<string, unknown>> | null
  regionScope: Readonly<Record<string, unknown>> | null
  languageScope: Readonly<Record<string, unknown>> | null
  resourceConstraints: Readonly<Record<string, unknown>> | null
  ethicalConstraints: Readonly<Record<string, unknown>> | null
  uncertainties: Readonly<Record<string, unknown>> | null
}

export type ResearchQuestionPermissions = {
  canEdit: boolean
  canCreateVersion: boolean
  canMarkReady: boolean
  canRequestConfirmation: boolean
}

export type ResearchQuestionVersionSummaryViewModel = {
  id: string
  versionNumber: number
  status: string
  tone: SemanticTone
  knownStatus: boolean
  createdAt: string
  isCurrent: boolean
}

export type ResearchQuestionViewModel = {
  questionId: string
  projectId: string
  currentVersionId: string
  versionNumber: number
  status: string
  tone: SemanticTone
  knownStatus: boolean
  permissionsKnown: boolean
  fields: ResearchQuestionFields
  permissions: ResearchQuestionPermissions
  pendingApproval: { id: string; status: string } | null
  createdAt: string
  versions: ResearchQuestionVersionSummaryViewModel[]
}

export type CapabilityState = "AVAILABLE" | "NOT_AVAILABLE" | "UNKNOWN"

export type ResearchQuestionCapabilityAvailability = {
  researchQuestion: CapabilityState
  aiParse: CapabilityState
  queryPlan: CapabilityState
  literature: CapabilityState
}

export type ResearchQuestionPageViewModel = {
  question: ResearchQuestionViewModel | null
  canCreate: boolean
  capabilities: ResearchQuestionCapabilityAvailability
}

export type ResearchQuestionLoadError = UiErrorViewModel

export function researchQuestionHref(projectId: string): string {
  return researchQuestionRoute.replace("$projectId", projectId)
}
