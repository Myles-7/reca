import type { UiErrorViewModel } from "../../projects/model"
import type { QueryPlanWorkspaceProps } from "../ui/contracts"

const noop = () => undefined
const ready = {
  id: "query-plan-design",
  projectId: "project-design",
  researchQuestionVersionId: "rq-version-design",
  status: "DRAFT",
  knownStatus: true,
  permissionsKnown: true,
  tone: "info",
  lockVersion: 1,
  fields: {
    chineseTerms: ["生成式人工智能", "学习投入"],
    englishTerms: ["generative AI", "learning engagement"],
    synonyms: { en: ["GenAI"] },
    objectTerms: { en: ["teacher education students"] },
    methodTerms: { en: ["survey"] },
    booleanQuery: '("generative AI" OR GenAI) AND "learning engagement"',
    filters: {
      fromYear: 2020,
      toYear: 2026,
      languages: ["zh", "en"],
      workTypes: ["article"],
      openAccessOnly: false,
    },
    limitations: ["Provider coverage varies by language."],
  },
  permissions: { canUpdate: true, canGenerate: true },
  generatedByAi: false,
  updatedAt: "2026-08-01T04:00:00Z",
} as const

const loadError = {
  title: "Query plan unavailable",
  message: "The query plan could not be loaded from the service.",
  code: "QUERY_PLAN_LOAD_FAILED",
  requestId: "request-query-plan-load",
  retryable: true,
  forbidden: false,
  notFound: false,
  conflict: false,
} satisfies UiErrorViewModel

const forbiddenError = {
  title: "Access denied",
  message: "You do not have access to this query plan.",
  code: "PROJECT_ACCESS_DENIED",
  requestId: "request-query-plan-forbidden",
  retryable: false,
  forbidden: true,
  notFound: false,
  conflict: false,
} satisfies UiErrorViewModel

const conflictError = {
  title: "Query plan changed",
  message: "This query plan is stale; reload before creating a new version.",
  code: "QUERY_PLAN_VERSION_CONFLICT",
  requestId: "request-query-plan-conflict",
  retryable: false,
  forbidden: false,
  notFound: false,
  conflict: true,
} satisfies UiErrorViewModel

export const queryPlanReadyFixture = {
  content: { state: "ready", data: ready },
  pendingAction: null,
  mutationError: null,
  onRetry: noop,
  onEvent: noop,
} satisfies QueryPlanWorkspaceProps

export const queryPlanLoadingFixture = {
  ...queryPlanReadyFixture,
  content: { state: "loading", label: "Loading query plan" },
} satisfies QueryPlanWorkspaceProps

export const queryPlanLoadErrorFixture = {
  ...queryPlanReadyFixture,
  content: { state: "error", error: loadError },
} satisfies QueryPlanWorkspaceProps

export const queryPlanForbiddenFixture = {
  ...queryPlanReadyFixture,
  content: { state: "error", error: forbiddenError },
} satisfies QueryPlanWorkspaceProps

export const queryPlanReadOnlyFixture = {
  ...queryPlanReadyFixture,
  content: {
    state: "ready",
    data: { ...ready, permissions: { canUpdate: false, canGenerate: false } },
  },
} satisfies QueryPlanWorkspaceProps

export const queryPlanPermissionsUnknownFixture = {
  ...queryPlanReadyFixture,
  content: {
    state: "ready",
    data: {
      ...ready,
      permissionsKnown: false,
      permissions: { canUpdate: false, canGenerate: false },
    },
  },
} satisfies QueryPlanWorkspaceProps

export const queryPlanUpdatePendingFixture = {
  ...queryPlanReadyFixture,
  pendingAction: "update",
} satisfies QueryPlanWorkspaceProps

export const queryPlanGeneratePendingFixture = {
  ...queryPlanReadyFixture,
  pendingAction: "generate",
} satisfies QueryPlanWorkspaceProps

export const queryPlanConflictFixture = {
  ...queryPlanReadyFixture,
  mutationError: conflictError,
} satisfies QueryPlanWorkspaceProps

export const queryPlanLongContentFixture = {
  ...queryPlanReadyFixture,
  content: {
    state: "ready",
    data: {
      ...ready,
      fields: {
        ...ready.fields,
        englishTerms: [
          "responsible generative artificial intelligence use in teacher education",
          "multidimensional behavioral emotional cognitive and social learning engagement",
        ],
        synonyms: {
          en: [
            "large language model assisted learning",
            "AI-supported academic task completion",
          ],
        },
        booleanQuery:
          '(("responsible generative artificial intelligence use" OR "large language model assisted learning") AND ("behavioral engagement" OR "emotional engagement" OR "cognitive engagement" OR "social engagement")) AND "undergraduate teacher education students"',
        limitations: [
          "Provider-specific field support may truncate unusually long Boolean expressions and requires manual verification before reuse.",
        ],
      },
    },
  },
} satisfies QueryPlanWorkspaceProps

export const queryPlanDegradedFixture = {
  ...queryPlanReadyFixture,
  content: {
    state: "ready",
    data: {
      ...ready,
      status: "FUTURE_QUERY_PLAN_STATE",
      knownStatus: false,
      permissionsKnown: false,
      tone: "degraded",
      permissions: { canUpdate: false, canGenerate: false },
    },
  },
} satisfies QueryPlanWorkspaceProps

export const queryPlanFixtures = [
  {
    id: "ready",
    label: "Ready",
    behavior:
      "Renders a writable query plan with both mapped actions available.",
    props: queryPlanReadyFixture,
  },
  {
    id: "loading",
    label: "Loading",
    behavior: "Keeps the dual-pane layout stable while query facts load.",
    props: queryPlanLoadingFixture,
  },
  {
    id: "load-error",
    label: "Load error",
    behavior: "Shows a retry action only for a retryable load failure.",
    props: queryPlanLoadErrorFixture,
  },
  {
    id: "forbidden",
    label: "Forbidden",
    behavior: "Shows access denial without presenting mutation controls.",
    props: queryPlanForbiddenFixture,
  },
  {
    id: "read-only",
    label: "Read-only",
    behavior:
      "Disables update and generation from explicit mapped permissions.",
    props: queryPlanReadOnlyFixture,
  },
  {
    id: "permissions-unknown",
    label: "Permissions unknown",
    behavior:
      "Keeps both mutations disabled when permission projection is unavailable.",
    props: queryPlanPermissionsUnknownFixture,
  },
  {
    id: "update-pending",
    label: "Update pending",
    behavior: "Locks duplicate actions while an update intent is pending.",
    props: queryPlanUpdatePendingFixture,
  },
  {
    id: "generate-pending",
    label: "Generate pending",
    behavior: "Labels and disables actions while generation intent is pending.",
    props: queryPlanGeneratePendingFixture,
  },
  {
    id: "mutation-conflict",
    label: "Mutation conflict",
    behavior:
      "Surfaces a stale-version conflict without inventing a successful save.",
    props: queryPlanConflictFixture,
  },
  {
    id: "long-content",
    label: "Long content",
    behavior: "Exercises wrapping for long terms, queries, and limitations.",
    props: queryPlanLongContentFixture,
  },
  {
    id: "degraded",
    label: "Degraded",
    behavior:
      "Fails closed when the server projects an unknown lifecycle state.",
    props: queryPlanDegradedFixture,
  },
] as const satisfies ReadonlyArray<{
  id: string
  label: string
  behavior: string
  props: QueryPlanWorkspaceProps
}>
