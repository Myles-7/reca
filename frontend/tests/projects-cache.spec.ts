import { expect, test } from "@playwright/test"
import { QueryClient } from "@tanstack/react-query"

import {
  invalidateProjectApprovals,
  invalidateProjectArtifacts,
  invalidateProjectDetail,
  invalidateProjectJobs,
  invalidateProjectLifecycle,
  invalidateProjectMembers,
} from "../src/features/projects/cache"
import { jobEventMatchesRoute } from "../src/features/projects/controller"
import {
  projectKeys,
  validateProjectProjection,
} from "../src/features/projects/queries"

function seed(queryClient: QueryClient, queryKey: readonly unknown[]) {
  queryClient.setQueryData(queryKey, { ready: true })
}

function isInvalidated(queryClient: QueryClient, queryKey: readonly unknown[]) {
  return queryClient.getQueryState(queryKey)?.isInvalidated ?? false
}

test("project lifecycle keeps the existing project-wide invalidation scope", async () => {
  const queryClient = new QueryClient()
  const projectId = "project-1"
  const projectKeysToSeed = [
    projectKeys.all,
    projectKeys.detail(projectId),
    projectKeys.overview(projectId),
    projectKeys.members(projectId),
    projectKeys.artifacts(projectId),
    projectKeys.jobs(projectId),
    projectKeys.approvals(projectId),
    projectKeys.audit(projectId),
  ]
  for (const queryKey of projectKeysToSeed) seed(queryClient, queryKey)
  seed(queryClient, ["users"])

  await invalidateProjectLifecycle(queryClient, projectId)

  for (const queryKey of projectKeysToSeed) {
    expect(isInvalidated(queryClient, queryKey)).toBe(true)
  }
  expect(isInvalidated(queryClient, ["users"])).toBe(false)
})

test("project detail keeps prefix invalidation for nested project queries", async () => {
  const queryClient = new QueryClient()
  const projectId = "project-1"
  seed(queryClient, projectKeys.detail(projectId))
  seed(queryClient, projectKeys.overview(projectId))
  seed(queryClient, projectKeys.detail("project-2"))

  await invalidateProjectDetail(queryClient, projectId)

  expect(isInvalidated(queryClient, projectKeys.detail(projectId))).toBe(true)
  expect(isInvalidated(queryClient, projectKeys.overview(projectId))).toBe(true)
  expect(isInvalidated(queryClient, projectKeys.detail("project-2"))).toBe(
    false,
  )
})

const resourceInvalidations = [
  ["members", invalidateProjectMembers, projectKeys.members],
  ["artifacts", invalidateProjectArtifacts, projectKeys.artifacts],
  ["jobs", invalidateProjectJobs, projectKeys.jobs],
  ["approvals", invalidateProjectApprovals, projectKeys.approvals],
] as const

for (const [resource, invalidate, resourceKey] of resourceInvalidations) {
  test(`${resource} invalidation remains scoped to its resource key`, async () => {
    const queryClient = new QueryClient()
    const projectId = "project-1"
    seed(queryClient, resourceKey(projectId))
    seed(queryClient, projectKeys.audit(projectId))

    await invalidate(queryClient, projectId)

    expect(isInvalidated(queryClient, resourceKey(projectId))).toBe(true)
    expect(isInvalidated(queryClient, projectKeys.audit(projectId))).toBe(false)
  })
}

test("project route projections and Job events reject cross-project identities", () => {
  expect(() =>
    validateProjectProjection("project-1", ["project-1"], "project jobs"),
  ).not.toThrow()
  expect(() =>
    validateProjectProjection("project-1", ["project-2"], "project jobs"),
  ).toThrow(/does not match this project route/)

  const event = {
    event_id: 1,
    event_type: "job.progress",
    job_id: "job-1",
    project_id: "project-1",
    status: "RUNNING",
    progress_percent: 50,
    message: "Running",
  }
  expect(jobEventMatchesRoute(event, "project-1", "job-1")).toBe(true)
  expect(jobEventMatchesRoute(event, "project-2", "job-1")).toBe(false)
  expect(jobEventMatchesRoute(event, "project-1", "job-2")).toBe(false)
})
