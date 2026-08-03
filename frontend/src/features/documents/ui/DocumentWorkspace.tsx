import {
  ChevronLeft,
  ChevronRight,
  FileText,
  ListTree,
  Minus,
  PanelRight,
  RotateCcw,
  Search,
  Upload,
  X,
  ZoomIn,
} from "lucide-react"
import {
  type ChangeEvent,
  type CSSProperties,
  type DragEvent,
  type FormEvent,
  type ReactNode,
  useRef,
  useState,
} from "react"

import {
  DegradedNotice,
  EmptyState,
  InspectorSection,
  JobProgress,
  LoadableState,
  MetadataList,
  MutationError,
  PaneHeader,
  PermissionNotice,
  SourceBadge,
  StatusBadge,
  useVisualTheme,
  WorkspaceHeader,
  WorkspaceLoadingFrame,
} from "@/components/reca-visual-refresh"
import "@/components/reca-visual-refresh/visual-refresh.css"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet"

import type {
  DocumentPageViewModel,
  DocumentWorkspaceViewModel,
} from "../model"
import type { DocumentEvent, DocumentWorkspaceProps } from "./contracts"
import "./document-workspace.css"

type MobileMode = "viewer" | "pages" | "details"
type DocumentType = Extract<
  DocumentEvent,
  { action: "upload" }
>["input"]["documentType"]

const DOCUMENT_TYPES: readonly { value: DocumentType; label: string }[] = [
  { value: "SCHOLARLY_PDF", label: "学术 PDF" },
  { value: "MANUSCRIPT", label: "手稿" },
  { value: "OTHER", label: "其他文档" },
]

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function formatDate(value: string): string {
  const date = new Date(value)
  return Number.isNaN(date.getTime())
    ? value
    : new Intl.DateTimeFormat("zh-CN", {
        dateStyle: "medium",
        timeStyle: "short",
      }).format(date)
}

function statusLabel(status: string, known: boolean): string {
  if (!known) return "未知解析状态"
  const labels: Record<string, string> = {
    DRAFT: "草稿",
    QUEUED: "等待解析",
    RUNNING: "解析中",
    COMPLETED: "解析完成",
    FAILED: "解析失败",
  }
  return labels[status] ?? status
}

function parserPresentation(data: DocumentWorkspaceViewModel) {
  const parser = data.document.parserType.toUpperCase()
  const fallback = parser === "PYPDF"
  if (!data.document.knownStatus) {
    return { label: "解析器来源未知", kind: "unknown" as const, fallback }
  }
  if (fallback) {
    return { label: "pypdf fallback", kind: "degraded" as const, fallback }
  }
  if (parser === "GROBID") {
    return {
      label: "GROBID 结构化解析",
      kind: "verified" as const,
      fallback,
    }
  }
  return { label: data.document.parserType, kind: "unknown" as const, fallback }
}

function IconButton({
  label,
  disabled,
  onClick,
  children,
}: {
  label: string
  disabled?: boolean
  onClick?: () => void
  children: ReactNode
}) {
  return (
    <button
      type="button"
      className="document-icon-button"
      aria-label={label}
      title={label}
      disabled={disabled}
      onClick={onClick}
    >
      {children}
    </button>
  )
}

function UploadIntentPanel({
  open,
  allowed,
  pending,
  disabledReason,
  onClose,
  onUpload,
}: {
  open: boolean
  allowed: boolean
  pending: boolean
  disabledReason: string | null
  onClose: () => void
  onUpload: (event: Extract<DocumentEvent, { action: "upload" }>) => void
}) {
  const [file, setFile] = useState<File | null>(null)
  const [documentType, setDocumentType] =
    useState<DocumentType>("SCHOLARLY_PDF")
  const [literatureRecordId, setLiteratureRecordId] = useState("")
  const [dragging, setDragging] = useState(false)

  if (!open) return null

  const chooseFile = (event: ChangeEvent<HTMLInputElement>) => {
    setFile(event.target.files?.[0] ?? null)
  }
  const dropFile = (event: DragEvent<HTMLLabelElement>) => {
    event.preventDefault()
    setDragging(false)
    setFile(event.dataTransfer.files?.[0] ?? null)
  }
  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!file || !allowed || pending) return
    onUpload({
      action: "upload",
      input: {
        file,
        documentType,
        literatureRecordId: literatureRecordId.trim() || null,
      },
    })
  }

  return (
    <section className="document-upload-panel" aria-labelledby="upload-title">
      <div className="document-upload-panel__header">
        <div>
          <h2 id="upload-title">上传文档</h2>
          <p>上传只提交 Artifact 意图；解析状态由服务端另行返回。</p>
        </div>
        <IconButton label="关闭上传区" onClick={onClose}>
          <X aria-hidden="true" />
        </IconButton>
      </div>
      {disabledReason ? (
        <PermissionNotice title="上传不可用" reason={disabledReason} />
      ) : null}
      <form className="document-upload-form" onSubmit={submit}>
        <label
          className={`document-drop-zone${dragging ? " is-dragging" : ""}`}
          onDragEnter={(event) => {
            event.preventDefault()
            setDragging(true)
          }}
          onDragOver={(event) => event.preventDefault()}
          onDragLeave={() => setDragging(false)}
          onDrop={dropFile}
        >
          <input
            type="file"
            onChange={chooseFile}
            disabled={!allowed || pending}
          />
          <Upload aria-hidden="true" />
          <span>{file ? "更换文件" : "选择文件或拖放到此处"}</span>
          <small>系统仅读取文件名、大小和 MIME；正文由服务端处理。</small>
        </label>
        <div className="document-upload-fields">
          <label>
            <span>目标文档类型</span>
            <select
              value={documentType}
              onChange={(event) =>
                setDocumentType(event.target.value as DocumentType)
              }
              disabled={!allowed || pending}
            >
              {DOCUMENT_TYPES.map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </label>
          <label>
            <span>关联 LiteratureRecord ID（可选）</span>
            <input
              value={literatureRecordId}
              onChange={(event) => setLiteratureRecordId(event.target.value)}
              placeholder="仅随上传意图提交"
              disabled={!allowed || pending}
            />
          </label>
        </div>
        <div className="document-upload-summary" aria-live="polite">
          {file ? (
            <MetadataList
              items={[
                { label: "文件名", value: file.name },
                { label: "大小", value: formatBytes(file.size) },
                { label: "MIME", value: file.type || "未提供" },
              ]}
            />
          ) : (
            <p>尚未选择文件。</p>
          )}
        </div>
        <div className="document-upload-actions">
          <p>Artifact 上传成功不代表 Document 解析成功。</p>
          <button
            type="submit"
            className="document-button document-button--primary"
            disabled={!file || !allowed || pending}
          >
            <Upload aria-hidden="true" />
            <span>{pending ? "正在提交…" : "提交上传意图"}</span>
          </button>
        </div>
      </form>
    </section>
  )
}

function PageNavigation({
  pages,
  selectedPage,
  declaredPageCount,
  onSelect,
}: {
  pages: readonly DocumentPageViewModel[]
  selectedPage: number | null
  declaredPageCount: number | null
  onSelect: (page: number) => void
}) {
  return (
    <div className="document-page-navigation">
      {pages.length > 0 ? (
        <ol>
          {pages.map((page) => (
            <li key={page.pageNumber}>
              <button
                type="button"
                className={
                  selectedPage === page.pageNumber ? "is-selected" : undefined
                }
                aria-current={
                  selectedPage === page.pageNumber ? "page" : undefined
                }
                onClick={() => onSelect(page.pageNumber)}
              >
                <FileText aria-hidden="true" />
                <span>
                  <strong>第 {page.pageNumber} 页</strong>
                  <small>
                    {page.printedPageLabel
                      ? `印刷页 ${page.printedPageLabel}`
                      : "无印刷页码"}
                  </small>
                </span>
              </button>
            </li>
          ))}
        </ol>
      ) : (
        <EmptyState
          title="页面内容尚未就绪"
          message={
            declaredPageCount
              ? `服务端已报告 ${declaredPageCount} 页，页面文本仍未返回。`
              : "解析完成后，页面导航将在此显示。"
          }
        />
      )}
    </div>
  )
}

function Viewer({
  page,
  pageCount,
  zoom,
  searchTerm,
  onSearch,
  onZoom,
  onPrevious,
  onNext,
}: {
  page: DocumentPageViewModel | null
  pageCount: number | null
  zoom: number
  searchTerm: string
  onSearch: (value: string) => void
  onZoom: (value: number) => void
  onPrevious: () => void
  onNext: () => void
}) {
  return (
    <section className="document-viewer" aria-label="文档阅读区">
      <div className="document-viewer-toolbar">
        <div className="document-viewer-toolbar__search">
          <Search aria-hidden="true" />
          <input
            type="search"
            value={searchTerm}
            onChange={(event) => onSearch(event.target.value)}
            placeholder="在当前页面中查找"
            aria-label="在当前页面中查找"
          />
        </div>
        <div className="document-viewer-toolbar__group">
          <IconButton
            label="上一页"
            disabled={!page || page.pageNumber <= 1}
            onClick={onPrevious}
          >
            <ChevronLeft aria-hidden="true" />
          </IconButton>
          <span className="document-page-position">
            {page ? `${page.pageNumber} / ${pageCount ?? "?"}` : "— / —"}
          </span>
          <IconButton
            label="下一页"
            disabled={
              !page || (pageCount !== null && page.pageNumber >= pageCount)
            }
            onClick={onNext}
          >
            <ChevronRight aria-hidden="true" />
          </IconButton>
        </div>
        <div className="document-viewer-toolbar__group">
          <IconButton
            label="缩小"
            disabled={zoom <= 75}
            onClick={() => onZoom(Math.max(75, zoom - 25))}
          >
            <Minus aria-hidden="true" />
          </IconButton>
          <span className="document-zoom-value">{zoom}%</span>
          <IconButton
            label="放大"
            disabled={zoom >= 150}
            onClick={() => onZoom(Math.min(150, zoom + 25))}
          >
            <ZoomIn aria-hidden="true" />
          </IconButton>
          <IconButton label="重置缩放" onClick={() => onZoom(100)}>
            <RotateCcw aria-hidden="true" />
          </IconButton>
        </div>
      </div>
      <div className="document-page-stage">
        {page ? (
          <article
            className="document-page-sheet"
            style={{ "--document-zoom": zoom / 100 } as CSSProperties}
          >
            <header>
              <span>第 {page.pageNumber} 页</span>
              <span>{page.printedPageLabel ?? "无印刷页码"}</span>
            </header>
            <pre>{page.textContent ?? "当前页面没有可显示的文本投影。"}</pre>
            {searchTerm &&
            !(page.textContent ?? "")
              .toLocaleLowerCase()
              .includes(searchTerm.toLocaleLowerCase()) ? (
              <p className="document-search-result" role="status">
                当前页面未找到“{searchTerm}”。
              </p>
            ) : null}
          </article>
        ) : (
          <EmptyState
            title="阅读内容尚未返回"
            message="文档实体与页面文本是独立服务端投影；当前状态不会被解释为空文档。"
          />
        )}
      </div>
    </section>
  )
}

export function DocumentWorkspace({
  content,
  pendingAction,
  mutationError,
  onRetry,
  onEvent,
}: DocumentWorkspaceProps) {
  const visualTheme = useVisualTheme()
  const [selectedPageNumber, setSelectedPageNumber] = useState<number | null>(
    null,
  )
  const [zoom, setZoom] = useState(100)
  const [searchTerm, setSearchTerm] = useState("")
  const [uploadOpen, setUploadOpen] = useState(false)
  const [pageDrawerOpen, setPageDrawerOpen] = useState(false)
  const [inspectorOpen, setInspectorOpen] = useState(false)
  const [mobileMode, setMobileMode] = useState<MobileMode>("viewer")
  const [allowFallback, setAllowFallback] = useState(false)
  const [extractCoordinates, setExtractCoordinates] = useState(false)
  const pageDrawerTitleRef = useRef<HTMLHeadingElement>(null)
  const inspectorDrawerTitleRef = useRef<HTMLHeadingElement>(null)

  if (content.state !== "ready") {
    const loadError = content.state === "error" ? content.error : null
    return (
      <div
        className="reca-visual-refresh document-workspace document-workspace--loadable"
        data-theme={visualTheme}
        data-od-id="document-workspace-loadable"
      >
        <WorkspaceHeader title="文档阅读" context="RECA / Document" />
        <WorkspaceLoadingFrame layout="three-pane">
          <LoadableState
            state={loadError?.forbidden ? "forbidden" : content.state}
            title={
              content.state === "loading" ? "正在加载文档" : loadError?.title
            }
            message={loadError?.message}
            action={
              loadError?.retryable ? (
                <button
                  type="button"
                  className="document-button"
                  onClick={onRetry}
                >
                  重新加载
                </button>
              ) : undefined
            }
          />
        </WorkspaceLoadingFrame>
      </div>
    )
  }

  const data = content.data
  const { document, pages, job } = data
  const parser = parserPresentation(data)
  const unknown = !document.knownStatus || !data.permissionsKnown
  const degraded = parser.fallback || document.tone === "degraded" || unknown
  const uploadAllowed = data.permissionsKnown && data.canUpload
  const parseAllowed =
    data.permissionsKnown &&
    document.knownStatus &&
    document.permissions.canParse
  const retryAllowed =
    data.permissionsKnown &&
    document.knownStatus &&
    job?.knownStatus === true &&
    job.canRetry
  const selectedPage =
    pages.find((page) => page.pageNumber === selectedPageNumber) ??
    pages[0] ??
    null
  const pageCount = document.pageCount ?? (pages.length || null)
  const pending = pendingAction !== null
  const statusTone = degraded ? "degraded" : document.tone

  const uploadDisabledReason = !data.permissionsKnown
    ? "权限状态未知，写操作已安全禁用。"
    : !data.canUpload
      ? "服务端未授予当前文档的上传能力。"
      : null
  const parseDisabledReason = !data.permissionsKnown
    ? "权限状态未知，无法发出解析意图。"
    : !document.knownStatus
      ? "解析状态未知，请先刷新服务端状态。"
      : !document.permissions.canParse
        ? "服务端未授予当前文档的解析能力。"
        : null
  const retryDisabledReason = !job
    ? "当前没有可重试的 Job 投影。"
    : !data.permissionsKnown
      ? "Document 权限状态未知，重试已禁用。"
      : job.retryDisabledReason

  const orderedPages = [...pages].sort((a, b) => a.pageNumber - b.pageNumber)
  const movePage = (direction: -1 | 1) => {
    if (!selectedPage) return
    const index = orderedPages.findIndex(
      (page) => page.pageNumber === selectedPage.pageNumber,
    )
    const target = orderedPages[index + direction]
    if (target) setSelectedPageNumber(target.pageNumber)
  }

  const pagePane = (
    <aside
      className={`document-pane document-page-pane${
        pageDrawerOpen ? " is-open" : ""
      }`}
      data-od-id="document-page-navigation"
      aria-label="页面导航"
    >
      <PaneHeader
        title="页面"
        subtitle={pageCount === null ? "页数未知" : `${pageCount} 页`}
        actions={
          <IconButton
            label="关闭页面导航"
            onClick={() => setPageDrawerOpen(false)}
          >
            <X aria-hidden="true" />
          </IconButton>
        }
      />
      <InspectorSection title="文档关系">
        <MetadataList
          items={[
            { label: "Document", value: document.id, mono: true },
            { label: "Artifact", value: document.artifactId, mono: true },
            {
              label: "LiteratureRecord",
              value: document.literatureRecordId ?? "未绑定",
              mono: document.literatureRecordId !== null,
            },
          ]}
        />
      </InspectorSection>
      <PageNavigation
        pages={orderedPages}
        selectedPage={selectedPage?.pageNumber ?? null}
        declaredPageCount={pageCount}
        onSelect={(page) => {
          setSelectedPageNumber(page)
          setMobileMode("viewer")
          setPageDrawerOpen(false)
        }}
      />
    </aside>
  )

  const inspector = (
    <aside
      className={`document-pane document-inspector${
        inspectorOpen ? " is-open" : ""
      }`}
      data-od-id="document-inspector"
      aria-label="文档详情"
    >
      <PaneHeader
        title="详情"
        subtitle="服务端投影"
        actions={
          <IconButton label="关闭详情" onClick={() => setInspectorOpen(false)}>
            <X aria-hidden="true" />
          </IconButton>
        }
      />
      <InspectorSection
        title="身份与解析"
        accessory={<SourceBadge label={parser.label} kind={parser.kind} />}
      >
        <MetadataList
          items={[
            { label: "Document ID", value: document.id, mono: true },
            { label: "Artifact ID", value: document.artifactId, mono: true },
            { label: "文档类型", value: document.documentType },
            {
              label: "解析状态",
              value: statusLabel(document.parseStatus, document.knownStatus),
            },
            { label: "解析器", value: document.parserType },
            { label: "置信度", value: document.parseConfidence },
            { label: "语言", value: document.language ?? "未知" },
            { label: "页数", value: pageCount ?? "未知" },
            {
              label: "扫描文档",
              value:
                document.isScanned === null
                  ? "未知"
                  : document.isScanned
                    ? "是 · 文本可能有限"
                    : "否",
            },
            { label: "更新时间", value: formatDate(document.updatedAt) },
          ]}
        />
      </InspectorSection>
      <InspectorSection title="解析 Job">
        {job ? (
          <>
            <JobProgress
              label="解析进度"
              statusLabel={statusLabel(job.status, job.knownStatus)}
              tone={degraded ? "degraded" : job.tone}
              progress={job.knownStatus ? job.progressPercent : null}
              step={job.currentStep}
            />
            {job.errorMessage ? (
              <p className="document-job-error" role="alert">
                {job.errorCode
                  ? `${job.errorCode}: ${job.errorMessage}`
                  : job.errorMessage}
              </p>
            ) : null}
            <button
              type="button"
              className="document-button document-button--wide"
              disabled={!retryAllowed || pending}
              title={retryDisabledReason ?? "重试解析 Job"}
              onClick={() =>
                onEvent({ action: "retry-job", input: { jobId: job.id } })
              }
            >
              <RotateCcw aria-hidden="true" />
              <span>
                {pendingAction === "retry-job" ? "正在提交…" : "重试解析"}
              </span>
            </button>
            {retryDisabledReason ? (
              <p className="document-disabled-reason">{retryDisabledReason}</p>
            ) : null}
          </>
        ) : (
          <EmptyState
            title="没有 Job 投影"
            message="当前状态不提供进度或正式 retryability。"
          />
        )}
      </InspectorSection>
      <InspectorSection title="解析选项">
        <div className="document-parse-options">
          <label>
            <input
              type="checkbox"
              checked={allowFallback}
              disabled={!parseAllowed || pending}
              onChange={(event) => setAllowFallback(event.target.checked)}
            />
            <span>
              <strong>允许 fallback</strong>
              <small>GROBID 不可用时，允许服务端选择降级解析器。</small>
            </span>
          </label>
          <label>
            <input
              type="checkbox"
              checked={extractCoordinates}
              disabled={!parseAllowed || pending}
              onChange={(event) => setExtractCoordinates(event.target.checked)}
            />
            <span>
              <strong>提取坐标</strong>
              <small>仅表达提取意图；坐标由服务端结果决定。</small>
            </span>
          </label>
        </div>
        {parseDisabledReason ? (
          <p className="document-disabled-reason">{parseDisabledReason}</p>
        ) : null}
      </InspectorSection>
      <InspectorSection title="安全边界">
        <ul className="document-boundary-list">
          <li>Artifact 上传与 Document 解析是两个独立结果。</li>
          <li>Document 与 LiteratureRecord 是不同服务端实体。</li>
          <li>未知状态不会启用 parse 或 retry。</li>
        </ul>
      </InspectorSection>
    </aside>
  )

  return (
    <div
      className="reca-visual-refresh document-workspace"
      data-theme={visualTheme}
      data-od-id="document-workspace"
    >
      <WorkspaceHeader
        title="文档阅读"
        context={`Document · ${document.id}`}
        metadata={
          <>
            <StatusBadge
              label={statusLabel(document.parseStatus, document.knownStatus)}
              tone={statusTone}
            />
            <SourceBadge label={parser.label} kind={parser.kind} />
            <span className="document-updated-at">
              {formatDate(document.updatedAt)}
            </span>
          </>
        }
        actions={
          <>
            <button
              type="button"
              className="document-button"
              disabled={!uploadAllowed || pending}
              title={uploadDisabledReason ?? "上传文档"}
              onClick={() => setUploadOpen((value) => !value)}
            >
              <Upload aria-hidden="true" />
              <span>上传</span>
            </button>
            <button
              type="button"
              className="document-button document-button--primary"
              disabled={!parseAllowed || pending}
              title={parseDisabledReason ?? "开始解析"}
              onClick={() =>
                onEvent({
                  action: "parse",
                  input: {
                    documentId: document.id,
                    allowFallback,
                    extractCoordinates,
                  },
                })
              }
            >
              <FileText aria-hidden="true" />
              <span>
                {pendingAction === "parse" ? "正在提交…" : "开始解析"}
              </span>
            </button>
          </>
        }
      />

      <div
        className="document-mobile-tabs"
        role="tablist"
        aria-label="文档视图"
      >
        {(
          [
            ["viewer", "阅读"],
            ["pages", "页面"],
            ["details", "详情"],
          ] as const
        ).map(([mode, label]) => (
          <button
            key={mode}
            type="button"
            role="tab"
            aria-selected={mobileMode === mode}
            onClick={() => setMobileMode(mode)}
          >
            {label}
          </button>
        ))}
      </div>

      <UploadIntentPanel
        open={uploadOpen}
        allowed={uploadAllowed}
        pending={pendingAction === "upload"}
        disabledReason={uploadDisabledReason}
        onClose={() => setUploadOpen(false)}
        onUpload={onEvent}
      />

      {mutationError ? (
        <div className="document-workspace-notice">
          <MutationError
            message={mutationError.message}
            code={mutationError.code}
            requestId={mutationError.requestId}
            retryable={mutationError.retryable}
            onRetry={onRetry}
          />
        </div>
      ) : null}
      {unknown ? (
        <div className="document-workspace-notice">
          <PermissionNotice
            title="状态或权限尚未确认"
            reason="解析与重试操作已安全禁用；请等待服务端返回已知状态。"
          />
        </div>
      ) : null}
      {parser.fallback ? (
        <div className="document-workspace-notice">
          <DegradedNotice
            title="正在显示 pypdf fallback 结果"
            message="该结果不是 GROBID 高置信度结构化解析；请结合 LOW confidence 与页面文本限制复核。"
          />
        </div>
      ) : null}
      {document.isScanned ? (
        <div className="document-workspace-notice">
          <DegradedNotice
            title="扫描型 PDF"
            message="页面可能仅提供有限文本；当前展示不代表 OCR 或结构化解析完整。"
          />
        </div>
      ) : null}

      <div className="document-tablet-controls">
        <Sheet open={pageDrawerOpen} onOpenChange={setPageDrawerOpen}>
          <SheetTrigger asChild>
            <button type="button" className="document-button">
              <ListTree aria-hidden="true" />
              <span>页面</span>
            </button>
          </SheetTrigger>
          <SheetContent
            side="left"
            className="reca-visual-refresh document-drawer-sheet"
            data-theme={visualTheme}
            onOpenAutoFocus={(event) => {
              event.preventDefault()
              pageDrawerTitleRef.current?.focus()
            }}
          >
            <SheetHeader>
              <SheetTitle ref={pageDrawerTitleRef} tabIndex={-1}>
                页面导航
              </SheetTitle>
              <SheetDescription>选择文档页面并返回阅读区。</SheetDescription>
            </SheetHeader>
            {pagePane}
          </SheetContent>
        </Sheet>
        <Sheet open={inspectorOpen} onOpenChange={setInspectorOpen}>
          <SheetTrigger asChild>
            <button type="button" className="document-button">
              <PanelRight aria-hidden="true" />
              <span>详情</span>
            </button>
          </SheetTrigger>
          <SheetContent
            side="right"
            className="reca-visual-refresh document-drawer-sheet"
            data-theme={visualTheme}
            onOpenAutoFocus={(event) => {
              event.preventDefault()
              inspectorDrawerTitleRef.current?.focus()
            }}
          >
            <SheetHeader>
              <SheetTitle ref={inspectorDrawerTitleRef} tabIndex={-1}>
                文档详情
              </SheetTitle>
              <SheetDescription>
                复核服务端投影、解析状态与允许操作。
              </SheetDescription>
            </SheetHeader>
            {inspector}
          </SheetContent>
        </Sheet>
      </div>

      <div className={`document-layout document-mobile-mode--${mobileMode}`}>
        {pagePane}
        <main className="document-main-pane" data-od-id="document-viewer-pane">
          <Viewer
            page={selectedPage}
            pageCount={pageCount}
            zoom={zoom}
            searchTerm={searchTerm}
            onSearch={setSearchTerm}
            onZoom={setZoom}
            onPrevious={() => movePage(-1)}
            onNext={() => movePage(1)}
          />
        </main>
        {inspector}
      </div>
    </div>
  )
}
