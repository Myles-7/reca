import { useState } from "react"

import type { ProjectViewModel } from "../model"
import {
  canExecuteProjectAction,
  useProjectLifecycleMutation,
  useProjectUpdateMutation,
} from "../mutations"
import {
  EditProjectDialog,
  ProjectLifecycleControl,
} from "../ui/ProjectActions"

export function ProjectActionsContainer({
  projectId,
  project,
}: {
  projectId: string
  project: ProjectViewModel
}) {
  const [editOpen, setEditOpen] = useState(false)
  const lifecycleAction =
    project.status === "ARCHIVED"
      ? "restore"
      : project.status === "ACTIVE"
        ? "archive"
        : null
  const lifecycle = useProjectLifecycleMutation(
    projectId,
    lifecycleAction === "restore",
  )
  const update = useProjectUpdateMutation(projectId, project.lockVersion, () =>
    setEditOpen(false),
  )

  return (
    <>
      {project.canUpdate ? (
        <EditProjectDialog
          project={project}
          open={editOpen}
          pending={update.isPending}
          error={update.uiError}
          onOpenChange={setEditOpen}
          onUpdate={(input) => {
            if (canExecuteProjectAction(project, "update")) {
              update.mutate(input)
            }
          }}
        />
      ) : null}
      {project.canDelete && lifecycleAction ? (
        <ProjectLifecycleControl
          action={lifecycleAction}
          pending={lifecycle.isPending}
          error={lifecycle.uiError}
          onAction={() => {
            if (canExecuteProjectAction(project, "lifecycle")) {
              lifecycle.mutate()
            }
          }}
        />
      ) : null}
    </>
  )
}
