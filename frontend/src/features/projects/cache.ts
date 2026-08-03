import type { QueryClient } from "@tanstack/react-query"

import { projectKeys } from "./queries"

async function invalidate(
  queryClient: QueryClient,
  queryKeys: ReadonlyArray<readonly unknown[]>,
) {
  await Promise.all(
    queryKeys.map((queryKey) => queryClient.invalidateQueries({ queryKey })),
  )
}

export function invalidateProjectLifecycle(
  queryClient: QueryClient,
  projectId: string,
) {
  return invalidate(queryClient, [
    projectKeys.all,
    projectKeys.detail(projectId),
    projectKeys.overview(projectId),
    projectKeys.audit(projectId),
  ])
}

export function invalidateProjectDetail(
  queryClient: QueryClient,
  projectId: string,
) {
  return invalidate(queryClient, [projectKeys.detail(projectId)])
}

export function invalidateProjectMembers(
  queryClient: QueryClient,
  projectId: string,
) {
  return invalidate(queryClient, [projectKeys.members(projectId)])
}

export function invalidateProjectArtifacts(
  queryClient: QueryClient,
  projectId: string,
) {
  return invalidate(queryClient, [projectKeys.artifacts(projectId)])
}

export function invalidateProjectJobs(
  queryClient: QueryClient,
  projectId: string,
) {
  return invalidate(queryClient, [projectKeys.jobs(projectId)])
}

export function invalidateProjectApprovals(
  queryClient: QueryClient,
  projectId: string,
) {
  return invalidate(queryClient, [projectKeys.approvals(projectId)])
}
