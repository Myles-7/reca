import useAuth from "@/hooks/useAuth"

import { mapUiError } from "../mappers"
import type { Loadable } from "../model"
import { canExecuteMemberCommand, useMemberMutation } from "../mutations"
import { useMembers } from "../queries"
import type { MembersPanelData } from "../ui/contracts"
import { MembersPanel } from "../ui/MembersPanel"

export function MembersContainer({ projectId }: { projectId: string }) {
  const { user } = useAuth()
  const query = useMembers(projectId, user?.id)
  const mutation = useMemberMutation(projectId)
  const content: Loadable<MembersPanelData> = query.isLoading
    ? { state: "loading", label: "Loading members" }
    : query.data
      ? { state: "ready", data: query.data }
      : { state: "error", error: mapUiError(query.error) }
  const loadError = query.error && query.data ? mapUiError(query.error) : null

  return (
    <MembersPanel
      content={content}
      submitting={mutation.isPending}
      loadError={loadError}
      mutationError={mutation.uiError}
      onRetry={() => void query.refetch()}
      onAddMember={(input) => {
        const command = { action: "add", input } as const
        if (
          canExecuteMemberCommand(
            query.data?.members ?? [],
            query.data?.permissions ?? null,
            command,
          )
        ) {
          mutation.mutate(command)
        }
      }}
      onChangeRole={(input) => {
        const command = { action: "change-role", input } as const
        if (
          canExecuteMemberCommand(
            query.data?.members ?? [],
            query.data?.permissions ?? null,
            command,
          )
        ) {
          mutation.mutate(command)
        }
      }}
      onTransferOwnership={(input) => {
        const command = { action: "transfer-ownership", input } as const
        if (
          canExecuteMemberCommand(
            query.data?.members ?? [],
            query.data?.permissions ?? null,
            command,
          )
        ) {
          mutation.mutate(command)
        }
      }}
      onRemoveMember={(memberId) => {
        const command = { action: "remove", memberId } as const
        if (
          canExecuteMemberCommand(
            query.data?.members ?? [],
            query.data?.permissions ?? null,
            command,
          )
        ) {
          mutation.mutate(command)
        }
      }}
    />
  )
}
