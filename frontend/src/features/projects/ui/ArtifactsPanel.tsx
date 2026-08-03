import { Download, LockKeyhole, PanelRightOpen, Upload, X } from "lucide-react"
import { useEffect, useState } from "react"

import {
  InspectorSection,
  MetadataList,
  MutationError,
  PaneHeader,
  PermissionNotice,
  SourceBadge,
  StatusBadge,
} from "@/components/reca-visual-refresh"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

import type { ArtifactViewModel } from "../model"
import type { ArtifactsPanelProps } from "./contracts"
import { DisabledReason, ProjectPanel } from "./ProjectPanel"

function ArtifactInspector({
  artifact,
  open,
  onClose,
  onDownload,
}: {
  artifact: ArtifactViewModel | null
  open: boolean
  onClose: () => void
  onDownload: (artifactId: string) => void
}) {
  return (
    <aside
      className={`project-artifact-inspector${open ? " project-artifact-inspector--open" : ""}`}
      aria-label="Artifact 详情"
    >
      <PaneHeader
        title="Artifact Inspector"
        subtitle="选择仅影响本地详情视图"
        actions={
          <Button
            className="project-inspector-close"
            type="button"
            size="icon-sm"
            variant="ghost"
            aria-label="关闭 Artifact 详情"
            onClick={onClose}
          >
            <X aria-hidden="true" />
          </Button>
        }
      />
      {artifact ? (
        <>
          <InspectorSection
            title="身份与来源"
            accessory={
              <SourceBadge
                label={artifact.origin === "ORIGINAL" ? "Original" : "Derived"}
                kind={artifact.origin === "ORIGINAL" ? "verified" : "evidence"}
              />
            }
          >
            <MetadataList
              items={[
                { label: "文件名", value: artifact.filename },
                { label: "Artifact ID", value: artifact.id, mono: true },
                { label: "类型", value: artifact.kind },
                { label: "大小", value: artifact.size },
                { label: "创建时间", value: artifact.createdAt },
              ]}
            />
          </InspectorSection>
          <InspectorSection title="完整性">
            <MetadataList
              items={[
                {
                  label: "状态",
                  value: (
                    <StatusBadge label={artifact.status} tone={artifact.tone} />
                  ),
                },
                {
                  label: "不可变",
                  value: artifact.immutable ? "是 · 服务端记录" : "否",
                },
                { label: "SHA-256", value: artifact.sha256, mono: true },
              ]}
            />
          </InspectorSection>
          <InspectorSection title="操作">
            <Button
              type="button"
              variant="outline"
              aria-label={`Download ${artifact.filename}`}
              disabled={!artifact.canDownload}
              onClick={() => onDownload(artifact.id)}
            >
              <Download aria-hidden="true" />
              下载 Artifact
            </Button>
            {!artifact.canDownload ? (
              <DisabledReason>服务端未允许下载当前 Artifact。</DisabledReason>
            ) : null}
          </InspectorSection>
        </>
      ) : (
        <p className="project-section-copy">
          请选择一个 Artifact 查看完整元数据。
        </p>
      )}
    </aside>
  )
}

export function ArtifactsPanel(props: ArtifactsPanelProps) {
  return (
    <ProjectPanel
      title="Artifacts"
      description="Original 与 Derived Artifact 保持来源、不可变性、哈希和下载权限可追溯。"
      content={props.content}
      loadError={props.loadError}
      onRetry={props.onRetry}
    >
      {(artifacts) => <ArtifactsReady {...props} artifacts={artifacts} />}
    </ProjectPanel>
  )
}

function ArtifactsReady({
  artifacts,
  canUpload,
  uploading,
  mutationError,
  onUpload,
  onDownload,
}: ArtifactsPanelProps & { artifacts: ArtifactViewModel[] }) {
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [inspectorOpen, setInspectorOpen] = useState(false)
  const selected = artifacts.find((item) => item.id === selectedId) ?? null

  useEffect(() => {
    if (selectedId && !artifacts.some((item) => item.id === selectedId)) {
      setSelectedId(artifacts[0]?.id ?? null)
    }
  }, [artifacts, selectedId])

  return (
    <>
      <div className="project-inline-form">
        <div className="project-field">
          <label htmlFor="artifact-file">上传 Original Artifact</label>
          <Input
            id="artifact-file"
            type="file"
            disabled={!canUpload || uploading}
            onChange={(event) => {
              const file = event.target.files?.[0]
              if (file) onUpload(file)
            }}
          />
        </div>
        <span className="project-readonly-mark">
          <Upload aria-hidden="true" />
          {uploading ? "上传并校验中" : "选择文件后发出上传意图"}
        </span>
        <Button
          className="project-inspector-toggle"
          type="button"
          variant="outline"
          disabled={!selected}
          onClick={() => setInspectorOpen(true)}
        >
          <PanelRightOpen aria-hidden="true" />
          查看详情
        </Button>
      </div>
      {!canUpload ? (
        <PermissionNotice reason="当前权限不允许上传 Artifact；现有记录仍保持可读。" />
      ) : null}
      {uploading ? (
        <StatusBadge label="上传意图处理中 · 尚未完成完整性校验" tone="info" />
      ) : null}
      {mutationError ? (
        <MutationError
          message={mutationError.message}
          code={mutationError.code}
          requestId={mutationError.requestId}
        />
      ) : null}
      {artifacts.length === 0 ? (
        <p className="project-section-copy">
          当前没有 Artifact。No artifacts have been uploaded.
        </p>
      ) : (
        <div className="project-artifacts-layout">
          <div
            className="project-artifact-list"
            role="listbox"
            aria-label="Artifact 列表"
          >
            {artifacts.map((artifact) => (
              <div
                key={artifact.id}
                className="project-artifact-row"
                role="option"
                tabIndex={0}
                aria-selected={selected?.id === artifact.id}
                onClick={() => {
                  setSelectedId(artifact.id)
                  setInspectorOpen(true)
                }}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault()
                    setSelectedId(artifact.id)
                    setInspectorOpen(true)
                  }
                }}
              >
                <span>
                  <span className="project-table__primary">
                    {artifact.filename}
                  </span>
                  <span className="project-table__secondary project-code">
                    {artifact.sha256}
                  </span>
                </span>
                <SourceBadge
                  label={artifact.origin}
                  kind={
                    artifact.origin === "ORIGINAL" ? "verified" : "evidence"
                  }
                />
                <StatusBadge label={artifact.status} tone={artifact.tone} />
                <span className="project-inline-meta">
                  {artifact.immutable ? (
                    <LockKeyhole aria-hidden="true" />
                  ) : null}
                  {artifact.size}
                </span>
                <Button
                  type="button"
                  size="icon-sm"
                  variant="ghost"
                  aria-label={`Download ${artifact.filename}`}
                  disabled={!artifact.canDownload}
                  onClick={(event) => {
                    event.stopPropagation()
                    onDownload(artifact.id)
                  }}
                >
                  <Download aria-hidden="true" />
                </Button>
              </div>
            ))}
          </div>
          <ArtifactInspector
            artifact={selected}
            open={inspectorOpen}
            onClose={() => setInspectorOpen(false)}
            onDownload={onDownload}
          />
        </div>
      )}
    </>
  )
}
