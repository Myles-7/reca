import type { UiErrorViewModel } from "../../projects/model"
import type { TopicCandidatesViewModel } from "../model"
import type { TopicCandidatesWorkspaceProps } from "../ui/contracts"

const noop = () => undefined
const noEvent: TopicCandidatesWorkspaceProps["onEvent"] = () => undefined
const failure = (
  code: string,
  forbidden = false,
  conflict = false,
): UiErrorViewModel => ({
  title: code,
  message: "Contract fixture error.",
  code,
  requestId: `request-${code.toLowerCase()}`,
  retryable: !forbidden && !conflict,
  forbidden,
  notFound: false,
  conflict,
})
const candidates: TopicCandidatesViewModel["candidates"] = [1, 2, 3].map(
  (order) => ({
    id: `topic-${order}`,
    order: order as 1 | 2 | 3,
    question: `How does generative AI use relate to learning engagement under study design ${order}?`,
    researchObject: "Teacher education students",
    variables: {
      independent: ["Generative AI use"],
      dependent: ["Learning engagement"],
    },
    literatureBasis: "Grounded in the current included literature set.",
    possibleInnovation: "Compare measurement and design assumptions.",
    dataRequirements: { sample: "Student survey and course context" },
    recommendedMethod:
      order === 1
        ? "Longitudinal panel"
        : order === 2
          ? "Cross-sectional survey"
          : "Mixed methods",
    literatureBasisLevel: "MEDIUM",
    dataAvailability: "MEDIUM",
    methodDifficulty: order === 1 ? "HIGH" : "MEDIUM",
    timeFeasibility: "MEDIUM",
    ethicalRisk: "LOW",
    majorRisks: ["Self-report bias"],
    limitations: ["Cross-sectional evidence cannot establish causality."],
    supervisorConfirmationItems: ["Confirm feasible sampling frame"],
    status: "PROPOSED",
    knownStatus: true,
    sources: [
      {
        literatureRecordId: `literature-${order}`,
        evidenceSpanId: null,
        relationType: "SUPPORTS",
        explanation: "Current included literature basis.",
      },
    ],
  }),
)
const ready: TopicCandidatesViewModel = {
  runId: "topic-run-1",
  researchQuestionVersionId: "rq-version-1",
  evidenceSummaryId: "summary-1",
  status: "COMPLETED",
  knownStatus: true,
  tone: "success",
  candidates,
  exactlyThree: true,
  sourcesValid: true,
  permissionsKnown: true,
  canGenerate: false,
  failureReason: null,
}
const base: TopicCandidatesWorkspaceProps = {
  content: { state: "ready", data: ready },
  pendingAction: null,
  mutationError: null,
  onRetry: noop,
  onEvent: noEvent,
}
const make = (
  id: string,
  label: string,
  props: TopicCandidatesWorkspaceProps,
  behavior: string,
) => ({ id, label, behavior, props })
export const topicCandidatesFixtures = [
  make(
    "ready-exactly-three",
    "Ready exactly 3",
    base,
    "Exactly three distinct sourced candidates.",
  ),
  make(
    "loading",
    "Loading",
    {
      ...base,
      content: { state: "loading", label: "Loading topic candidates" },
    },
    "Stable loading contract.",
  ),
  make(
    "empty",
    "Empty",
    {
      ...base,
      content: { state: "empty", message: "No topic run is selected." },
    },
    "No fabricated candidates.",
  ),
  make(
    "error",
    "Error",
    {
      ...base,
      content: { state: "error", error: failure("TOPIC_LOAD_FAILED") },
    },
    "Formal read failure.",
  ),
  make(
    "forbidden",
    "Forbidden",
    {
      ...base,
      content: { state: "error", error: failure("PROJECT_NOT_FOUND", true) },
    },
    "No-disclosure access state.",
  ),
  make(
    "read-only",
    "Read-only",
    {
      ...base,
      content: { state: "ready", data: { ...ready, canGenerate: false } },
    },
    "No adoption or hidden write intent.",
  ),
  make(
    "permissions-unknown",
    "Permissions unknown",
    {
      ...base,
      content: {
        state: "ready",
        data: { ...ready, permissionsKnown: false, canGenerate: false },
      },
    },
    "Unknown permissions fail closed.",
  ),
  make(
    "pending",
    "Pending",
    {
      ...base,
      pendingAction: "generate-topic",
      content: {
        state: "ready",
        data: {
          ...ready,
          status: "RUNNING",
          tone: "info",
          candidates: [],
          exactlyThree: false,
          failureReason: null,
        },
      },
    },
    "Job pending without optimistic candidates.",
  ),
  make(
    "conflict",
    "Conflict",
    {
      ...base,
      mutationError: failure("SUMMARY_VERSION_CONFLICT", false, true),
    },
    "Server conflict remains visible.",
  ),
  make(
    "degraded",
    "Degraded",
    {
      ...base,
      content: {
        state: "ready",
        data: {
          ...ready,
          tone: "degraded",
          failureReason: "Topic generation is temporarily degraded.",
        },
      },
    },
    "Known persistence limitation is explicit.",
  ),
  make(
    "unknown",
    "Unknown status",
    {
      ...base,
      content: {
        state: "ready",
        data: {
          ...ready,
          status: "FUTURE_STATE",
          knownStatus: false,
          tone: "degraded",
          permissionsKnown: false,
          canGenerate: false,
          failureReason: "Topic run status is unknown.",
        },
      },
    },
    "Unknown status fails closed.",
  ),
  make(
    "long-content",
    "Long content",
    {
      ...base,
      content: {
        state: "ready",
        data: {
          ...ready,
          candidates: ready.candidates.map((candidate, index) =>
            index
              ? candidate
              : {
                  ...candidate,
                  question: candidate.question.repeat(7),
                  literatureBasis: candidate.literatureBasis?.repeat(6) ?? null,
                },
          ),
        },
      },
    },
    "Long research questions wrap.",
  ),
  make(
    "failure-not-three",
    "Failure not 3",
    {
      ...base,
      content: {
        state: "ready",
        data: {
          ...ready,
          status: "FAILED",
          tone: "danger",
          candidates: ready.candidates.slice(0, 2),
          exactlyThree: false,
          failureReason:
            "The provider returned fewer than exactly three candidates.",
        },
      },
    },
    "Count failure is never silently padded.",
  ),
  make(
    "failure-invalid-source",
    "Failure invalid source",
    {
      ...base,
      content: {
        state: "ready",
        data: {
          ...ready,
          status: "FAILED",
          tone: "danger",
          sourcesValid: false,
          failureReason:
            "A candidate source did not validate against the project evidence set.",
        },
      },
    },
    "Invalid source IDs fail explicitly.",
  ),
] as const satisfies ReadonlyArray<{
  id: string
  label: string
  behavior: string
  props: TopicCandidatesWorkspaceProps
}>
