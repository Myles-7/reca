import type { Loadable, UiErrorViewModel } from "../../projects/model"
import type {
  AnalysisPlanInput,
  AnalysisWorkspaceViewModel,
  FigurePlanInput,
} from "../model"
import type { AnalysisWorkspaceRouteView } from "../route-contract"

export type AnalysisWorkspaceEvent =
  | { action: "create-analysis-plan"; input: AnalysisPlanInput }
  | {
      action: "update-analysis-plan"
      input: {
        planId: string
        lockVersion: number
        plan: AnalysisPlanInput
      }
    }
  | { action: "validate-analysis-plan"; input: { planId: string } }
  | { action: "request-analysis-approval"; input: { planId: string } }
  | {
      action: "run-analysis"
      input: { planId: string; reason: string | null }
    }
  | {
      action: "invalidate-analysis-run"
      input: { runId: string; reason: string }
    }
  | { action: "retry-job"; input: { jobId: string } }
  | { action: "cancel-job"; input: { jobId: string; reason: string } }
  | {
      action: "create-figure-plan"
      input: FigurePlanInput
    }
  | {
      action: "render-figure"
      input: { figurePlanId: string; reason: string | null }
    }
  | {
      action: "request-figure-confirmation"
      input: { figureId: string }
    }
  | {
      action: "decide-figure-confirmation"
      input: {
        approvalId: string
        decision: "APPROVE" | "REJECT"
        reason: string | null
      }
    }
  | {
      action: "download-artifact"
      input: { figureId: string; format: "PNG" | "SVG" | "PDF" | "CODE" }
    }
  | {
      action: "request-suggestion"
      input: { kind: "METHOD" | "FIGURE"; datasetVersionId: string }
    }
  | {
      action: "request-interpretation"
      input: { analysisResultId: string }
    }

export type AnalysisWorkspaceWorkspaceProps = {
  content: Loadable<AnalysisWorkspaceViewModel>
  pendingAction: AnalysisWorkspaceEvent["action"] | null
  mutationError: UiErrorViewModel | null
  onRetry: () => void
  onEvent: (event: AnalysisWorkspaceEvent) => void
  initialView?: AnalysisWorkspaceRouteView
  onViewChange?: (view: AnalysisWorkspaceRouteView) => void
}
