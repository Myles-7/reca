import { useQuery, useQueryClient } from "@tanstack/react-query"
import { useEffect, useRef, useState } from "react"

import {
  ApiError,
  ApprovalsApi,
  ArtifactsApi,
  AuditApi,
  JobsApi,
  MembersApi,
  ProjectsApi,
} from "@/api/adapter"
import { invalidateProjectJobs } from "./cache"
import { consumeJobEventStream, jobEventMatchesRoute } from "./controller"
import {
  mapApproval,
  mapArtifactList,
  mapAuditList,
  mapJob,
  mapMembers,
  mapOverview,
  mapProject,
  mapProjectListItem,
} from "./mappers"
import type { JobStreamState } from "./model"

export const projectKeys = {
  all: ["projects"] as const,
  detail: (projectId: string) => ["projects", projectId] as const,
  overview: (projectId: string) => ["projects", projectId, "overview"] as const,
  members: (projectId: string) => ["projects", projectId, "members"] as const,
  artifacts: (projectId: string) =>
    ["projects", projectId, "artifacts"] as const,
  jobs: (projectId: string) => ["projects", projectId, "jobs"] as const,
  approvals: (projectId: string) =>
    ["projects", projectId, "approvals"] as const,
  audit: (projectId: string) => ["projects", projectId, "audit"] as const,
}

export function validateProjectProjection(
  projectId: string,
  projectedIds: readonly (string | null)[],
  resource: string,
): void {
  if (projectedIds.some((projectedId) => projectedId !== projectId)) {
    throw new ApiError(
      404,
      "NOT_FOUND",
      `The ${resource} projection does not match this project route.`,
      "PROJECT_ROUTE_MISMATCH",
    )
  }
}

const retryProjectQuery = (failureCount: number, error: Error) => {
  if (error instanceof ApiError && [401, 403, 404].includes(error.status)) {
    return false
  }
  return failureCount < 2
}

export function useProjects() {
  return useQuery({
    queryKey: projectKeys.all,
    queryFn: () => ProjectsApi.list({ page_size: 100 }),
    select: (response) => response.data.map(mapProjectListItem),
  })
}

export function useProject(projectId: string) {
  return useQuery({
    queryKey: projectKeys.detail(projectId),
    queryFn: async () => {
      const response = await ProjectsApi.get(projectId)
      validateProjectProjection(projectId, [response.data.id], "project")
      return response
    },
    select: (response) => mapProject(response.data),
    retry: retryProjectQuery,
  })
}

export function useOverview(projectId: string) {
  return useQuery({
    queryKey: projectKeys.overview(projectId),
    queryFn: async () => {
      const response = await ProjectsApi.overview(projectId)
      validateProjectProjection(
        projectId,
        [response.data.project_id],
        "project overview",
      )
      return response
    },
    select: (response) => mapOverview(response.data),
    retry: retryProjectQuery,
  })
}

export function useMembers(projectId: string, currentUserId?: string) {
  return useQuery({
    queryKey: projectKeys.members(projectId),
    queryFn: async () => {
      const response = await MembersApi.list(projectId, { page_size: 100 })
      validateProjectProjection(
        projectId,
        response.data.map((member) => member.project_id),
        "project members",
      )
      return response
    },
    select: (response) =>
      mapMembers(response.data, currentUserId, response.allowed_actions),
    retry: retryProjectQuery,
  })
}

export function useArtifacts(projectId: string) {
  return useQuery({
    queryKey: projectKeys.artifacts(projectId),
    queryFn: async () => {
      const response = await ArtifactsApi.list(projectId, { page_size: 100 })
      validateProjectProjection(
        projectId,
        response.data.map((artifact) => artifact.project_id),
        "project artifacts",
      )
      return response
    },
    select: (response) =>
      mapArtifactList(response.data, response.allowed_actions),
    retry: retryProjectQuery,
  })
}

export function useJobs(projectId: string) {
  return useQuery({
    queryKey: projectKeys.jobs(projectId),
    queryFn: async () => {
      const response = await JobsApi.list(projectId, { page_size: 100 })
      validateProjectProjection(
        projectId,
        response.data.map((job) => job.project_id),
        "project jobs",
      )
      return response
    },
    select: (response) => response.data.map(mapJob),
    refetchInterval: (query) =>
      query.state.data?.data?.some((job) => mapJob(job).active) ? 5_000 : false,
    retry: retryProjectQuery,
  })
}

export function useApprovals(projectId: string) {
  return useQuery({
    queryKey: projectKeys.approvals(projectId),
    queryFn: async () => {
      const response = await ApprovalsApi.list(projectId, { page_size: 100 })
      validateProjectProjection(
        projectId,
        response.data.map((approval) => approval.project_id),
        "project approvals",
      )
      return response
    },
    select: (response) => response.data.map(mapApproval),
    retry: retryProjectQuery,
  })
}

export function useAudit(projectId: string) {
  return useQuery({
    queryKey: projectKeys.audit(projectId),
    queryFn: async () => {
      const response = await AuditApi.list(projectId, { page_size: 100 })
      validateProjectProjection(
        projectId,
        response.data.map((event) => event.project_id),
        "project audit",
      )
      return response
    },
    select: mapAuditList,
    retry: retryProjectQuery,
  })
}

export function useJobEvents(projectId: string, jobId: string | undefined) {
  const queryClient = useQueryClient()
  const lastEventId = useRef<number | undefined>(undefined)
  const [state, setState] = useState<JobStreamState>("idle")

  useEffect(() => {
    if (!jobId) {
      setState("idle")
      return
    }
    lastEventId.current = undefined
    const controller = new AbortController()
    let reconnectTimer: ReturnType<typeof setTimeout> | undefined
    const connect = async () => {
      try {
        const stream = await JobsApi.stream(
          jobId,
          lastEventId.current,
          controller.signal,
        )
        setState("connected")
        const received = await consumeJobEventStream(stream, (event) => {
          if (!jobEventMatchesRoute(event, projectId, jobId)) return
          void invalidateProjectJobs(queryClient, projectId)
        })
        if (received !== null) lastEventId.current = received
        if (!controller.signal.aborted) {
          setState("stale")
          reconnectTimer = setTimeout(connect, 1_000)
        }
      } catch {
        if (!controller.signal.aborted) {
          setState("degraded")
          reconnectTimer = setTimeout(connect, 5_000)
        }
      }
    }
    void connect()
    return () => {
      controller.abort()
      if (reconnectTimer) clearTimeout(reconnectTimer)
    }
  }, [jobId, projectId, queryClient])

  return state
}
