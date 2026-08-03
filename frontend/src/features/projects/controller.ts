import {
  ApprovalsApi,
  ArtifactsApi,
  type ArtifactType,
  JobsApi,
  type MemberAdd,
  MembersApi,
  ProjectsApi,
  type ProjectUpdate,
} from "@/api/adapter"

import type { MemberUpdateCommand, ProjectCreateCommand } from "./model"

export function operationKey(): string {
  return crypto.randomUUID()
}

export const projectCommands = {
  create: (input: ProjectCreateCommand) =>
    ProjectsApi.create(
      {
        name: input.name,
        description: input.description,
        discipline: input.discipline,
        project_type: input.projectType,
      },
      operationKey(),
    ),
  update: (projectId: string, input: ProjectUpdate, lockVersion: number) =>
    ProjectsApi.update(projectId, input, lockVersion),
  archive: (projectId: string) => ProjectsApi.archive(projectId),
  restore: (projectId: string) => ProjectsApi.restore(projectId),
}

export const memberCommands = {
  add: (projectId: string, input: MemberAdd) =>
    MembersApi.add(projectId, input, operationKey()),
  update: (projectId: string, memberId: string, input: MemberUpdateCommand) =>
    MembersApi.update(
      projectId,
      memberId,
      {
        role: input.role,
        transfer_ownership: input.transferOwnership,
        previous_owner_role: input.previousOwnerRole,
        reason: input.reason,
      },
      operationKey(),
    ),
  remove: (projectId: string, memberId: string) =>
    MembersApi.remove(projectId, memberId, operationKey()),
}

async function sha256(file: File): Promise<string> {
  const digest = await crypto.subtle.digest("SHA-256", await file.arrayBuffer())
  return Array.from(new Uint8Array(digest), (byte) =>
    byte.toString(16).padStart(2, "0"),
  ).join("")
}

export async function uploadArtifact(
  projectId: string,
  file: File,
  artifactType: ArtifactType,
) {
  const hash = await sha256(file)
  const initiated = await ArtifactsApi.initiate(
    projectId,
    {
      artifact_type: artifactType,
      filename: file.name,
      mime_type: file.type || "application/octet-stream",
      size_bytes: file.size,
      sha256: hash,
      is_original: true,
    },
    operationKey(),
  )
  await ArtifactsApi.transfer(initiated.data.upload_id, file)
  return ArtifactsApi.complete(
    projectId,
    initiated.data.upload_id,
    { sha256: hash, size_bytes: file.size },
    operationKey(),
  )
}

export async function downloadArtifact(artifactId: string): Promise<string> {
  const response = await ArtifactsApi.download(artifactId)
  return response.data.download_url
}

export const jobCommands = {
  retry: (jobId: string) => JobsApi.retry(jobId, operationKey()),
  cancel: (jobId: string, reason: string) =>
    JobsApi.cancel(jobId, reason, operationKey()),
}

export const approvalCommands = {
  approve: (approvalId: string, reason: string | null) =>
    ApprovalsApi.approve(
      approvalId,
      { decision_reason: reason },
      operationKey(),
    ),
  reject: (approvalId: string, reason: string) =>
    ApprovalsApi.reject(
      approvalId,
      { decision_reason: reason },
      operationKey(),
    ),
  cancel: (approvalId: string) =>
    ApprovalsApi.cancel(approvalId, operationKey()),
}

export type JobEvent = {
  event_id: number
  event_type: string
  job_id: string
  project_id: string
  status: string
  progress_percent: number
  message: string
}

export function jobEventMatchesRoute(
  event: JobEvent,
  projectId: string,
  jobId: string,
): boolean {
  return event.project_id === projectId && event.job_id === jobId
}

export async function consumeJobEventStream(
  stream: ReadableStream<Uint8Array>,
  onEvent: (event: JobEvent) => void,
): Promise<number | null> {
  const reader = stream.getReader()
  const decoder = new TextDecoder()
  let buffer = ""
  let lastEventId: number | null = null
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const frames = buffer.split("\n\n")
    buffer = frames.pop() ?? ""
    for (const frame of frames) {
      const data = frame
        .split("\n")
        .find((line) => line.startsWith("data: "))
        ?.slice(6)
      if (!data) continue
      const parsed = JSON.parse(data) as JobEvent
      lastEventId = parsed.event_id
      onEvent(parsed)
    }
  }
  return lastEventId
}
