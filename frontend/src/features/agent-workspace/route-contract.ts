export const agentWorkspaceRouteViews = [
  "run",
  "plan",
  "timeline",
  "tools",
] as const

export type AgentWorkspaceRouteView = (typeof agentWorkspaceRouteViews)[number]

export type AgentWorkspaceRouteSearch = {
  run?: string
  tool?: string
  sourceType?: string
  sourceId?: string
  approval?: string
  job?: string
  view?: AgentWorkspaceRouteView
}

const uuid =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i

const optionalUuid = (value: unknown) =>
  typeof value === "string" && uuid.test(value) ? value : undefined

export function parseAgentWorkspaceSearch(
  search: Record<string, unknown>,
): AgentWorkspaceRouteSearch {
  const sourceType =
    typeof search.sourceType === "string" &&
    /^[a-z][a-z0-9_]{0,99}$/.test(search.sourceType)
      ? search.sourceType
      : undefined
  const sourceId = optionalUuid(search.sourceId)
  const viewValue = search.view ?? search.surface
  const view =
    typeof viewValue === "string" &&
    agentWorkspaceRouteViews.includes(viewValue as AgentWorkspaceRouteView)
      ? (viewValue as AgentWorkspaceRouteView)
      : undefined
  return {
    run: optionalUuid(search.run) ?? optionalUuid(search.agentRun),
    tool: optionalUuid(search.tool),
    sourceType: sourceId ? sourceType : undefined,
    sourceId: sourceType ? sourceId : undefined,
    approval: optionalUuid(search.approval),
    job: optionalUuid(search.job),
    view,
  }
}

export function agentWorkspaceHref(
  projectId: string,
  search: AgentWorkspaceRouteSearch = {},
) {
  const query = new URLSearchParams()
  if (search.run) query.set("run", search.run)
  if (search.tool) query.set("tool", search.tool)
  if (search.sourceType) query.set("sourceType", search.sourceType)
  if (search.sourceId) query.set("sourceId", search.sourceId)
  if (search.approval) query.set("approval", search.approval)
  if (search.job) query.set("job", search.job)
  if (search.view) query.set("view", search.view)
  const suffix = query.size ? `?${query}` : ""
  return `/projects/${encodeURIComponent(projectId)}/agent${suffix}`
}

export function agentSourceWorkspaceHref(
  projectId: string,
  objectType: string,
  objectId: string,
) {
  if (!uuid.test(objectId)) return null
  const project = encodeURIComponent(projectId)
  const object = encodeURIComponent(objectId)
  const routes: Record<string, string> = {
    document: `/projects/${project}/documents/${object}`,
    dataset: `/projects/${project}/data?dataset=${object}`,
    dataset_version: `/projects/${project}/data?version=${object}`,
    claim: `/projects/${project}/evidence?claim=${object}&view=claims`,
    evidence_link: `/projects/${project}/evidence?link=${object}&view=claims`,
    export: `/projects/${project}/evidence?export=${object}&view=exports`,
    reproducibility_package: `/projects/${project}/evidence?package=${object}&view=exports`,
    manuscript: `/projects/${project}/manuscript?manuscript=${object}`,
    manuscript_version: `/projects/${project}/manuscript?version=${object}`,
    analysis_run: `/projects/${project}/analysis?analysisRun=${object}&view=runs`,
    analysis_result: `/projects/${project}/analysis?analysisResult=${object}&view=results`,
    figure: `/projects/${project}/analysis?figure=${object}&view=figures`,
  }
  return routes[objectType] ?? null
}

export const agentWorkspaceRouteContract = {
  recommendedPath: "/projects/$projectId/agent",
  productionRouteRegistered: true,
  deepLinkKeys: [
    "run",
    "agentRun",
    "tool",
    "sourceType",
    "sourceId",
    "approval",
    "job",
    "view",
    "surface",
  ],
  fallback: "authorized project Agent workspace without resource disclosure",
  refreshBehavior: "restore only from authorized server projections",
} as const
