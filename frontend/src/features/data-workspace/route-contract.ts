export const dataWorkspaceViews = [
  "data",
  "columns",
  "quality",
  "cleaning",
  "versions",
] as const

export type DataWorkspaceRouteView = (typeof dataWorkspaceViews)[number]

export type DataWorkspaceRouteSearch = {
  dataset?: string
  version?: string
  qualityRun?: string
  plan?: string
  approval?: string
  job?: string
  compareWith?: string
  view?: DataWorkspaceRouteView
}

const uuid =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i

function optionalUuid(value: unknown) {
  return typeof value === "string" && uuid.test(value) ? value : undefined
}

export function parseDataWorkspaceSearch(
  search: Record<string, unknown>,
): DataWorkspaceRouteSearch {
  const view =
    typeof search.view === "string" &&
    dataWorkspaceViews.includes(search.view as DataWorkspaceRouteView)
      ? (search.view as DataWorkspaceRouteView)
      : undefined
  return {
    dataset: optionalUuid(search.dataset),
    version: optionalUuid(search.version),
    qualityRun: optionalUuid(search.qualityRun),
    plan: optionalUuid(search.plan),
    approval: optionalUuid(search.approval),
    job: optionalUuid(search.job),
    compareWith: optionalUuid(search.compareWith),
    view,
  }
}

export const dataWorkspaceRouteContract = {
  path: "/projects/$projectId/data",
  productionIntegrationComplete: true,
  search: {
    dataset: "optional UUID",
    version: "optional UUID",
    qualityRun: "optional UUID",
    plan: "optional UUID",
    approval: "optional UUID",
    job: "optional UUID",
    compareWith: "optional UUID",
    view: "optional data | columns | quality | cleaning | versions",
  },
  ownership: {
    route: "Codex-owned production route",
    workspaceUi: "Open Design may modify ui/** and UI CSS only",
  },
} as const
