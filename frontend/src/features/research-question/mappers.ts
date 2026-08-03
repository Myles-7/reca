import type {
  CurrentResearchQuestionEnvelope,
  ResearchQuestionVersionPublic,
} from "@/api/adapter"

import type { SemanticTone } from "../projects/model"
import {
  type CapabilityState,
  type ResearchQuestionCapabilityAvailability,
  type ResearchQuestionFields,
  type ResearchQuestionPageViewModel,
  type ResearchQuestionPermissions,
  type ResearchQuestionVersionSummaryViewModel,
  type ResearchQuestionViewModel,
  researchQuestionVersionStatuses,
} from "./model"

export type ResearchQuestionProjection = {
  current: CurrentResearchQuestionEnvelope
  versions: ResearchQuestionVersionPublic[]
}

const noPermissions: ResearchQuestionPermissions = {
  canEdit: false,
  canCreateVersion: false,
  canMarkReady: false,
  canRequestConfirmation: false,
}

export function mapResearchQuestionStatus(status: string): {
  knownStatus: boolean
  tone: SemanticTone
} {
  const knownStatus = researchQuestionVersionStatuses.some(
    (known) => known === status,
  )
  if (!knownStatus) return { knownStatus: false, tone: "degraded" }
  if (status === "CONFIRMED") return { knownStatus: true, tone: "success" }
  if (status === "NEEDS_INPUT") return { knownStatus: true, tone: "warning" }
  if (status === "SUPERSEDED") return { knownStatus: true, tone: "neutral" }
  return { knownStatus: true, tone: "info" }
}

function mapPermissions(
  actions: readonly string[],
  knownStatus: boolean,
): ResearchQuestionPermissions {
  if (!knownStatus) return noPermissions
  const allowed = new Set(actions)
  return {
    canEdit: allowed.has("research_question.edit"),
    canCreateVersion: allowed.has("research_question.create_version"),
    canMarkReady: allowed.has("research_question.mark_ready"),
    canRequestConfirmation: allowed.has(
      "research_question.request_confirmation",
    ),
  }
}

function mapFields(
  version: ResearchQuestionVersionPublic,
): ResearchQuestionFields {
  return {
    rawInput: version.raw_input,
    normalizedQuestion: version.normalized_question,
    researchObject: version.research_object,
    population: version.population,
    context: version.context,
    independentVariables: version.independent_variables ?? [],
    dependentVariables: version.dependent_variables ?? [],
    controlVariables: version.control_variables ?? [],
    researchGoal: version.research_goal,
    relationshipType: version.relationship_type,
    methodPreference: version.method_preference,
    timeScope: version.time_scope,
    regionScope: version.region_scope,
    languageScope: version.language_scope,
    resourceConstraints: version.resource_constraints,
    ethicalConstraints: version.ethical_constraints,
    uncertainties: version.uncertainties,
  }
}

function mapVersion(
  version: ResearchQuestionVersionPublic,
): ResearchQuestionVersionSummaryViewModel {
  const status = mapResearchQuestionStatus(version.status)
  return {
    id: version.id,
    versionNumber: version.version_number,
    status: version.status,
    createdAt: version.created_at,
    isCurrent: version.is_current,
    ...status,
  }
}

function availability(value: string | undefined): CapabilityState {
  if (value === "AVAILABLE" || value === "NOT_AVAILABLE") return value
  return "UNKNOWN"
}

function mapCapabilities(
  values: Record<string, string>,
): ResearchQuestionCapabilityAvailability {
  return {
    researchQuestion: availability(values.research_question),
    aiParse: availability(values.ai_parse),
    queryPlan: availability(values.query_plan),
    literature: availability(values.literature),
  }
}

export function mapResearchQuestion(
  projection: ResearchQuestionProjection,
): ResearchQuestionPageViewModel {
  const source = projection.current.data
  const question = source.question
  if (!question) {
    return {
      question: null,
      canCreate: source.allowed_actions.includes("research_question.create"),
      capabilities: mapCapabilities(source.capability_availability),
    }
  }
  const version = question.current_version
  const status = mapResearchQuestionStatus(version.status)
  const mapped: ResearchQuestionViewModel = {
    questionId: question.id,
    projectId: question.project_id,
    currentVersionId: version.id,
    versionNumber: version.version_number,
    status: version.status,
    permissionsKnown: true,
    fields: mapFields(version),
    permissions: mapPermissions(version.allowed_actions, status.knownStatus),
    pendingApproval:
      version.pending_approval_id && version.pending_approval_status
        ? {
            id: version.pending_approval_id,
            status: version.pending_approval_status,
          }
        : null,
    createdAt: version.created_at,
    versions: projection.versions.map(mapVersion),
    ...status,
  }
  return {
    question: mapped,
    canCreate: false,
    capabilities: mapCapabilities(source.capability_availability),
  }
}
