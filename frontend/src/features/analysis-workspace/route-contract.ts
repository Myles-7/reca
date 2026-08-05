export const analysisWorkspaceViews = [
  "plan",
  "assumptions",
  "runs",
  "results",
  "figures",
] as const

export type AnalysisWorkspaceRouteView = (typeof analysisWorkspaceViews)[number]

export type AnalysisWorkspaceRouteSearch = {
  dataset?: string
  version?: string
  analysisPlan?: string
  analysisRun?: string
  analysisResult?: string
  approval?: string
  job?: string
  figurePlan?: string
  figure?: string
  renderRun?: string
  view?: AnalysisWorkspaceRouteView
}

const uuid =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i

function optionalUuid(value: unknown) {
  return typeof value === "string" && uuid.test(value) ? value : undefined
}

export function parseAnalysisWorkspaceSearch(
  search: Record<string, unknown>,
): AnalysisWorkspaceRouteSearch {
  const view =
    typeof search.view === "string" &&
    analysisWorkspaceViews.includes(search.view as AnalysisWorkspaceRouteView)
      ? (search.view as AnalysisWorkspaceRouteView)
      : undefined
  return {
    dataset: optionalUuid(search.dataset),
    version: optionalUuid(search.version),
    analysisPlan: optionalUuid(search.analysisPlan),
    analysisRun: optionalUuid(search.analysisRun),
    analysisResult: optionalUuid(search.analysisResult),
    approval: optionalUuid(search.approval),
    job: optionalUuid(search.job),
    figurePlan: optionalUuid(search.figurePlan),
    figure: optionalUuid(search.figure),
    renderRun: optionalUuid(search.renderRun),
    view,
  }
}

export const analysisWorkspaceRouteContract = {
  path: "/projects/$projectId/analysis",
  productionIntegrationComplete: true,
  projectMismatchBehavior: "RESOURCE_NOT_FOUND without object disclosure",
  refreshBehavior: "restore exclusively from authorized server facts",
  search: {
    dataset: "optional UUID",
    version: "optional UUID",
    analysisPlan: "optional UUID",
    analysisRun: "optional UUID",
    analysisResult: "optional UUID",
    approval: "optional UUID",
    job: "optional UUID",
    figurePlan: "optional UUID; resolved through formal FigurePlan transport",
    figure: "optional UUID; resolved through formal Figure transport",
    renderRun:
      "optional UUID; resolved through formal FigureRenderRun transport",
    view: "optional plan | assumptions | runs | results | figures",
  },
  ownership: {
    route: "Codex-owned; production integration complete",
    workspaceUi: "Open Design owns analysis-workspace/ui/**",
  },
} as const
