import type { UiErrorViewModel } from "../../projects/model"
import type { ResearchQuestionViewModel } from "../model"
import type { ResearchQuestionWorkspaceProps } from "../ui/contracts"

const noRetry = () => undefined
const noEvent: ResearchQuestionWorkspaceProps["onEvent"] = () => undefined

const readyQuestion = {
  questionId: "research-question-design",
  projectId: "project-design",
  currentVersionId: "research-question-version-2",
  versionNumber: 2,
  status: "DRAFT",
  tone: "info",
  knownStatus: true,
  permissionsKnown: true,
  fields: {
    rawInput:
      "How is generative AI use associated with learning engagement among teacher education students?",
    normalizedQuestion:
      "What is the association between generative AI use and learning engagement among teacher education students?",
    researchObject: "Teacher education students",
    population: "Undergraduate teacher education students",
    context: "Higher education coursework",
    independentVariables: ["Generative AI use"],
    dependentVariables: ["Learning engagement"],
    controlVariables: ["Year of study", "Prior AI experience"],
    researchGoal: "RELATE",
    relationshipType: "ASSOCIATION",
    methodPreference: { design: "cross-sectional survey" },
    timeScope: { academic_year: "2026-2027" },
    regionScope: { country: "China" },
    languageScope: { languages: ["zh", "en"] },
    resourceConstraints: { duration_months: 6 },
    ethicalConstraints: { human_participants: true },
    uncertainties: { data_source: "Needs confirmation" },
  },
  permissions: {
    canEdit: true,
    canCreateVersion: true,
    canMarkReady: true,
    canRequestConfirmation: false,
  },
  pendingApproval: null,
  createdAt: "Aug 1, 2026, 11:20 AM",
  versions: [
    {
      id: "research-question-version-2",
      versionNumber: 2,
      status: "DRAFT",
      tone: "info",
      knownStatus: true,
      createdAt: "Aug 1, 2026, 11:20 AM",
      isCurrent: true,
    },
    {
      id: "research-question-version-1",
      versionNumber: 1,
      status: "SUPERSEDED",
      tone: "neutral",
      knownStatus: true,
      createdAt: "Aug 1, 2026, 10:45 AM",
      isCurrent: false,
    },
  ],
} satisfies ResearchQuestionViewModel

const requestError = {
  title: "Request failed",
  message: "The research question could not be loaded.",
  code: "RESEARCH_QUESTION_LOAD_FAILED",
  requestId: "request-rq-error",
  retryable: true,
  forbidden: false,
  notFound: false,
  conflict: false,
} satisfies UiErrorViewModel

const forbiddenError = {
  title: "Access denied",
  message: "You do not have access to this research question.",
  code: "PROJECT_ACCESS_DENIED",
  requestId: "request-rq-forbidden",
  retryable: false,
  forbidden: true,
  notFound: false,
  conflict: false,
} satisfies UiErrorViewModel

const conflictError = {
  title: "Research Question changed",
  message: "The current version is stale; reload before saving a new version.",
  code: "RESEARCH_QUESTION_VERSION_CONFLICT",
  requestId: "request-rq-conflict",
  retryable: false,
  forbidden: false,
  notFound: false,
  conflict: true,
} satisfies UiErrorViewModel

export const researchQuestionReadyFixture = {
  content: { state: "ready", data: readyQuestion },
  canCreate: false,
  capabilities: {
    researchQuestion: "AVAILABLE",
    aiParse: "NOT_AVAILABLE",
    queryPlan: "NOT_AVAILABLE",
    literature: "NOT_AVAILABLE",
  },
  pendingAction: null,
  mutationError: null,
  onRetry: noRetry,
  onEvent: noEvent,
} satisfies ResearchQuestionWorkspaceProps

export const researchQuestionLoadingFixture = {
  ...researchQuestionReadyFixture,
  content: { state: "loading", label: "Loading research question" },
  capabilities: {
    researchQuestion: "UNKNOWN",
    aiParse: "UNKNOWN",
    queryPlan: "UNKNOWN",
    literature: "UNKNOWN",
  },
} satisfies ResearchQuestionWorkspaceProps

export const researchQuestionEmptyFixture = {
  ...researchQuestionReadyFixture,
  content: {
    state: "empty",
    message: "No research question has been created for this project.",
  },
  canCreate: true,
} satisfies ResearchQuestionWorkspaceProps

export const researchQuestionErrorFixture = {
  ...researchQuestionReadyFixture,
  content: { state: "error", error: requestError },
  capabilities: researchQuestionLoadingFixture.capabilities,
} satisfies ResearchQuestionWorkspaceProps

export const researchQuestionForbiddenFixture = {
  ...researchQuestionReadyFixture,
  content: { state: "error", error: forbiddenError },
  capabilities: researchQuestionLoadingFixture.capabilities,
} satisfies ResearchQuestionWorkspaceProps

export const researchQuestionDegradedFixture = {
  ...researchQuestionReadyFixture,
  content: {
    state: "ready",
    data: {
      ...readyQuestion,
      status: "FUTURE_RESEARCH_QUESTION_STATE",
      tone: "degraded",
      knownStatus: false,
      permissionsKnown: false,
      permissions: {
        canEdit: false,
        canCreateVersion: false,
        canMarkReady: false,
        canRequestConfirmation: false,
      },
      pendingApproval: null,
    },
  },
} satisfies ResearchQuestionWorkspaceProps

export const researchQuestionNeedsInputFixture = {
  ...researchQuestionReadyFixture,
  content: {
    state: "ready",
    data: {
      ...readyQuestion,
      status: "NEEDS_INPUT",
      tone: "warning",
      permissions: {
        canEdit: true,
        canCreateVersion: true,
        canMarkReady: false,
        canRequestConfirmation: false,
      },
    },
  },
} satisfies ResearchQuestionWorkspaceProps

export const researchQuestionConfirmedFixture = {
  ...researchQuestionReadyFixture,
  content: {
    state: "ready",
    data: {
      ...readyQuestion,
      status: "CONFIRMED",
      tone: "success",
      permissions: {
        canEdit: false,
        canCreateVersion: true,
        canMarkReady: false,
        canRequestConfirmation: false,
      },
    },
  },
} satisfies ResearchQuestionWorkspaceProps

export const researchQuestionReadOnlyFixture = {
  ...researchQuestionReadyFixture,
  content: {
    state: "ready",
    data: {
      ...readyQuestion,
      permissions: {
        canEdit: false,
        canCreateVersion: false,
        canMarkReady: false,
        canRequestConfirmation: false,
      },
    },
  },
} satisfies ResearchQuestionWorkspaceProps

export const researchQuestionPermissionsUnknownFixture = {
  ...researchQuestionReadyFixture,
  content: {
    state: "ready",
    data: {
      ...readyQuestion,
      permissionsKnown: false,
      permissions: {
        canEdit: false,
        canCreateVersion: false,
        canMarkReady: false,
        canRequestConfirmation: false,
      },
    },
  },
} satisfies ResearchQuestionWorkspaceProps

export const researchQuestionSavePendingFixture = {
  ...researchQuestionReadyFixture,
  pendingAction: "save-version",
} satisfies ResearchQuestionWorkspaceProps

export const researchQuestionMarkReadyPendingFixture = {
  ...researchQuestionReadyFixture,
  pendingAction: "mark-ready",
} satisfies ResearchQuestionWorkspaceProps

export const researchQuestionConflictFixture = {
  ...researchQuestionReadyFixture,
  mutationError: conflictError,
} satisfies ResearchQuestionWorkspaceProps

export const researchQuestionPendingConfirmationFixture = {
  ...researchQuestionReadyFixture,
  content: {
    state: "ready",
    data: {
      ...readyQuestion,
      status: "READY",
      tone: "info",
      permissions: {
        canEdit: false,
        canCreateVersion: true,
        canMarkReady: false,
        canRequestConfirmation: false,
      },
      pendingApproval: {
        id: "approval-design-pending",
        status: "PENDING",
      },
    },
  },
  pendingAction: "request-confirmation",
} satisfies ResearchQuestionWorkspaceProps

export const researchQuestionLongContentFixture = {
  ...researchQuestionReadyFixture,
  content: {
    state: "ready",
    data: {
      ...readyQuestion,
      fields: {
        ...readyQuestion.fields,
        rawInput:
          "How do patterns of sustained, intermittent, and assessment-specific generative artificial intelligence use relate to multidimensional learning engagement among undergraduate teacher education students across institutions with substantially different digital learning policies?",
        normalizedQuestion:
          "Among undergraduate teacher education students enrolled across institutions with different digital learning policies, what associations exist between sustained, intermittent, and assessment-specific generative AI use and behavioral, emotional, cognitive, and social learning engagement?",
        researchObject:
          "Undergraduate teacher education students enrolled in multi-institutional programs with heterogeneous digital learning policies",
        context:
          "Credit-bearing higher education coursework delivered through blended, online, and classroom learning environments",
      },
    },
  },
} satisfies ResearchQuestionWorkspaceProps

export const researchQuestionFixtures = [
  {
    id: "ready",
    label: "Ready",
    behavior: "Renders the editable DRAFT projection and its mapped actions.",
    props: researchQuestionReadyFixture,
  },
  {
    id: "loading",
    label: "Loading",
    behavior: "Keeps the dual-pane layout stable while capabilities load.",
    props: researchQuestionLoadingFixture,
  },
  {
    id: "empty",
    label: "Empty",
    behavior:
      "Shows creation only when the mapped create capability is available.",
    props: researchQuestionEmptyFixture,
  },
  {
    id: "error",
    label: "Error",
    behavior: "Offers reload only for the retryable load error.",
    props: researchQuestionErrorFixture,
  },
  {
    id: "forbidden",
    label: "Forbidden",
    behavior: "Shows access denial without presenting a retry action.",
    props: researchQuestionForbiddenFixture,
  },
  {
    id: "needs-input",
    label: "NEEDS_INPUT",
    behavior:
      "Keeps editing available while mark-ready remains permission-blocked.",
    props: researchQuestionNeedsInputFixture,
  },
  {
    id: "confirmed",
    label: "CONFIRMED",
    behavior:
      "Presents the confirmed version as read-only without a fake pending approval.",
    props: researchQuestionConfirmedFixture,
  },
  {
    id: "read-only",
    label: "Read-only",
    behavior: "Disables every mutation from explicit mapped permissions.",
    props: researchQuestionReadOnlyFixture,
  },
  {
    id: "permissions-unknown",
    label: "Permissions unknown",
    behavior:
      "Keeps existing question fields readable while every mutation remains disabled.",
    props: researchQuestionPermissionsUnknownFixture,
  },
  {
    id: "save-pending",
    label: "Save pending",
    behavior:
      "Disables duplicate commands while save-version intent is pending.",
    props: researchQuestionSavePendingFixture,
  },
  {
    id: "mark-ready-pending",
    label: "Mark-ready pending",
    behavior: "Shows mark-ready submission pending without advancing status.",
    props: researchQuestionMarkReadyPendingFixture,
  },
  {
    id: "mutation-conflict",
    label: "Mutation conflict",
    behavior:
      "Surfaces a stale-version conflict without claiming a saved version.",
    props: researchQuestionConflictFixture,
  },
  {
    id: "degraded",
    label: "Degraded",
    behavior:
      "Fails closed when the server returns an unknown lifecycle state.",
    props: researchQuestionDegradedFixture,
  },
  {
    id: "pending-confirmation",
    label: "Pending confirmation",
    behavior:
      "Keeps pending approval distinct from formal confirmation success.",
    props: researchQuestionPendingConfirmationFixture,
  },
  {
    id: "long-content",
    label: "Long content",
    behavior:
      "Exercises wrapping for long research question fields and metadata.",
    props: researchQuestionLongContentFixture,
  },
] as const satisfies ReadonlyArray<{
  id: string
  label: string
  behavior: string
  props: ResearchQuestionWorkspaceProps
}>
