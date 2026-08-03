import { useState } from "react"

import { mapUiError } from "../mappers"
import type { ArtifactViewModel, Loadable, UiErrorViewModel } from "../model"
import {
  canExecuteArtifactDownload,
  canExecuteArtifactUpload,
  getArtifactDownloadUrl,
  useArtifactUploadMutation,
} from "../mutations"
import { useArtifacts } from "../queries"
import { ArtifactsPanel } from "../ui/ArtifactsPanel"

export function ArtifactsContainer({ projectId }: { projectId: string }) {
  const query = useArtifacts(projectId)
  const upload = useArtifactUploadMutation(projectId)
  const [downloadError, setDownloadError] = useState<UiErrorViewModel | null>(
    null,
  )
  const content: Loadable<ArtifactViewModel[]> = query.data
    ? { state: "ready", data: query.data.artifacts }
    : query.isLoading
      ? { state: "loading", label: "Loading artifacts" }
      : { state: "error", error: mapUiError(query.error) }
  const loadError = query.error && query.data ? mapUiError(query.error) : null

  async function download(artifactId: string) {
    setDownloadError(null)
    try {
      window.location.assign(await getArtifactDownloadUrl(artifactId))
    } catch (error) {
      setDownloadError(mapUiError(error))
    }
  }

  return (
    <ArtifactsPanel
      content={content}
      permissionsKnown={query.data?.permissionsKnown === true}
      canUpload={
        query.data?.permissionsKnown === true && query.data.canUpload === true
      }
      uploading={upload.isPending}
      loadError={loadError}
      mutationError={downloadError ?? upload.uiError}
      onRetry={() => void query.refetch()}
      onUpload={(file) => {
        if (canExecuteArtifactUpload(query.data ?? null)) {
          upload.mutate(file)
        }
      }}
      onDownload={(artifactId) => {
        if (canExecuteArtifactDownload(query.data ?? null, artifactId)) {
          void download(artifactId)
        }
      }}
    />
  )
}
