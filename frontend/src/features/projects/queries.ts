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
import { consumeJobEventStream } from "./controller"
import {
  mapApproval,
  mapArtifact,
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
    queryFn: () => ProjectsApi.get(projectId),
    select: (response) => mapProject(response.data),
    retry: (failureCount, error) => {
      if (error instanceof ApiError && [401, 403, 404].includes(error.status)) {
        return false
      }
      return failureCount < 2
    },
  })
}

export function useOverview(projectId: string) {
  return useQuery({
    queryKey: projectKeys.overview(projectId),
    queryFn: () => ProjectsApi.overview(projectId),
    select: (response) => mapOverview(response.data),
  })
}

export function useMembers(projectId: string, currentUserId?: string) {
  return useQuery({
    queryKey: projectKeys.members(projectId),
    queryFn: () => MembersApi.list(projectId, { page_size: 100 }),
    select: (response) => mapMembers(response.data, currentUserId),
  })
}

export function useArtifacts(projectId: string) {
  return useQuery({
    queryKey: projectKeys.artifacts(projectId),
    queryFn: () => ArtifactsApi.list(projectId, { page_size: 100 }),
    select: (response) => response.data.map(mapArtifact),
  })
}

export function useJobs(projectId: string) {
  return useQuery({
    queryKey: projectKeys.jobs(projectId),
    queryFn: () => JobsApi.list(projectId, { page_size: 100 }),
    select: (response) => response.data.map(mapJob),
    refetchInterval: (query) =>
      query.state.data?.data?.some((job) => mapJob(job).active) ? 5_000 : false,
  })
}

export function useApprovals(projectId: string) {
  return useQuery({
    queryKey: projectKeys.approvals(projectId),
    queryFn: () => ApprovalsApi.list(projectId, { page_size: 100 }),
    select: (response) => response.data.map(mapApproval),
  })
}

export function useAudit(projectId: string) {
  return useQuery({
    queryKey: projectKeys.audit(projectId),
    queryFn: () => AuditApi.list(projectId, { page_size: 100 }),
    select: mapAuditList,
  })
}

export function useJobEvents(jobId: string | undefined) {
  const queryClient = useQueryClient()
  const lastEventId = useRef<number | undefined>(undefined)
  const [state, setState] = useState<JobStreamState>("idle")

  useEffect(() => {
    if (!jobId) {
      setState("idle")
      return
    }
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
        const received = await consumeJobEventStream(stream, () => {
          void queryClient.invalidateQueries({ queryKey: ["projects"] })
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
  }, [jobId, queryClient])

  return state
}
