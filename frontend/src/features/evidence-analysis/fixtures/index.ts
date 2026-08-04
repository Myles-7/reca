import type { UiErrorViewModel } from "../../projects/model"
import type { EvidenceAnalysisViewModel } from "../model"
import type { EvidenceAnalysisWorkspaceProps } from "../ui/contracts"

const noop = () => undefined
const noEvent: EvidenceAnalysisWorkspaceProps["onEvent"] = () => undefined
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
const ready: EvidenceAnalysisViewModel = {
  summaryId: "summary-1",
  jobId: "job-summary-1",
  status: "COMPLETED",
  knownStatus: true,
  tone: "success",
  scopeStatement:
    "This summary is limited to the current included literature set.",
  includedLiteratureIds: ["literature-1", "literature-2"],
  items: [
    {
      kind: "CONSENSUS",
      claim:
        "Included studies report an association in their observed samples.",
      strength: "MEDIUM",
      limitations: ["Observational designs limit causal interpretation."],
      sources: {
        literatureRecordIds: ["literature-1"],
        contradictingLiteratureRecordIds: [],
        evidenceSpanIds: ["span-1"],
      },
    },
    {
      kind: "COUNTEREXAMPLE",
      claim:
        "One included cohort did not observe the association after adjustment.",
      strength: "MEDIUM",
      limitations: ["Different measurement timing."],
      sources: {
        literatureRecordIds: ["literature-2"],
        contradictingLiteratureRecordIds: ["literature-1"],
        evidenceSpanIds: ["span-2"],
      },
    },
    {
      kind: "EVIDENCE_GAP",
      claim:
        "The current literature set has insufficient longitudinal evidence.",
      strength: "LOW",
      limitations: ["This is not a claim about all scholarship."],
      sources: {
        literatureRecordIds: ["literature-1", "literature-2"],
        contradictingLiteratureRecordIds: [],
        evidenceSpanIds: [],
      },
    },
  ],
  missingInformation: ["Additional longitudinal studies"],
  limitations: ["Current literature set only"],
  permissionsKnown: true,
  canSearchEvidence: true,
  canCreateSummary: true,
  canGenerateTopics: true,
  canRetry: false,
  actionDisabledReason: null,
}
const base: EvidenceAnalysisWorkspaceProps = {
  content: { state: "ready", data: ready },
  capabilities: {
    permissionsKnown: true,
    canSearchEvidence: true,
    canCreateSummary: true,
    disabledReason: null,
  },
  searchResult: {
    query: "engagement",
    retrievalRunId: "retrieval-1",
    candidates: [
      {
        candidateId: "candidate-1",
        literatureRecordId: "literature-1",
        documentId: "document-1",
        pageNumber: 4,
        sourceText: "Observed association in the current sample.",
        sourceTextHash: "b".repeat(64),
        evidenceSpanId: null,
        hasCoordinates: true,
        limitations: ["Candidate is not yet a verified EvidenceSpan."],
      },
    ],
    limitations: [],
  },
  pendingAction: null,
  mutationError: null,
  onRetry: noop,
  onEvent: noEvent,
}
const make = (
  id: string,
  label: string,
  props: EvidenceAnalysisWorkspaceProps,
  behavior: string,
) => ({ id, label, behavior, props })
export const evidenceAnalysisFixtures = [
  make(
    "ready",
    "Ready",
    base,
    "Consensus, counterexample and bounded gap language.",
  ),
  make(
    "loading",
    "Loading",
    {
      ...base,
      content: { state: "loading", label: "Loading evidence analysis" },
      searchResult: null,
    },
    "Stable loading contract.",
  ),
  make(
    "empty",
    "Empty",
    {
      ...base,
      content: {
        state: "empty",
        message: "No included evidence is available.",
      },
      searchResult: {
        query: "engagement",
        retrievalRunId: "retrieval-empty",
        candidates: [],
        limitations: ["No included literature matched the bounded search."],
      },
    },
    "Empty candidates are not provider failure.",
  ),
  make(
    "error",
    "Error",
    {
      ...base,
      content: { state: "error", error: failure("SUMMARY_LOAD_FAILED") },
      searchResult: null,
    },
    "Retryable load failure.",
  ),
  make(
    "forbidden",
    "Forbidden",
    {
      ...base,
      content: { state: "error", error: failure("PROJECT_NOT_FOUND", true) },
      searchResult: null,
    },
    "No-disclosure access state.",
  ),
  make(
    "read-only",
    "Read-only",
    {
      ...base,
      content: {
        state: "ready",
        data: {
          ...ready,
          canGenerateTopics: false,
          actionDisabledReason: "Read-only access.",
        },
      },
    },
    "Generation disabled by capability.",
  ),
  make(
    "permissions-unknown",
    "Permissions unknown",
    {
      ...base,
      content: {
        state: "ready",
        data: {
          ...ready,
          permissionsKnown: false,
          canGenerateTopics: false,
          actionDisabledReason: "Summary permissions are unknown.",
        },
      },
    },
    "Unknown permissions fail closed.",
  ),
  make(
    "pending",
    "Pending",
    { ...base, pendingAction: "create-summary" },
    "Job request pending without summary success.",
  ),
  make(
    "conflict",
    "Conflict",
    { ...base, mutationError: failure("INCLUDED_SET_CHANGED", false, true) },
    "Included-set conflict remains visible.",
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
          limitations: [
            ...ready.limitations,
            "One source is awaiting verification.",
          ],
        },
      },
    },
    "Limitations stay explicit.",
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
          canGenerateTopics: false,
          actionDisabledReason: "Summary status is unknown.",
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
          items: ready.items.map((item, index) =>
            index ? item : { ...item, claim: item.claim.repeat(8) },
          ),
        },
      },
    },
    "Long claims and limitations wrap.",
  ),
] as const satisfies ReadonlyArray<{
  id: string
  label: string
  behavior: string
  props: EvidenceAnalysisWorkspaceProps
}>
