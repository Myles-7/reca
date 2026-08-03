import useAuth from "@/hooks/useAuth"

import { mapUiError } from "../mappers"
import type { JobViewModel, Loadable } from "../model"
import { canExecuteJobAction, useJobActionMutation } from "../mutations"
import { useJobEvents, useJobs, useMembers } from "../queries"
import { JobsPanel } from "../ui/JobsPanel"

export function JobsContainer({ projectId }: { projectId: string }) {
  const { user } = useAuth()
  const query = useJobs(projectId)
  const members = useMembers(projectId, user?.id)
  const activeJobId = query.data?.find((job) => job.active)?.id
  const streamState = useJobEvents(projectId, activeJobId)
  const mutation = useJobActionMutation(projectId)
  const content: Loadable<JobViewModel[]> = query.data
    ? { state: "ready", data: query.data }
    : query.isLoading
      ? { state: "loading", label: "Loading jobs" }
      : { state: "error", error: mapUiError(query.error) }
  const loadError = query.error && query.data ? mapUiError(query.error) : null
  const permissions =
    members.data?.permissions.permissionsKnown === true
      ? members.data.permissions
      : null

  return (
    <JobsPanel
      content={content}
      permissions={permissions}
      streamState={streamState}
      submittingJobId={mutation.submittingJobId}
      loadError={loadError}
      mutationError={mutation.uiError}
      onRetryLoad={() => void query.refetch()}
      onAction={(event) => {
        if (canExecuteJobAction(query.data ?? [], permissions, event)) {
          mutation.mutate(event)
        }
      }}
    />
  )
}
