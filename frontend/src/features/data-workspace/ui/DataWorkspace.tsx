import {
  AlertTriangle,
  Archive,
  Check,
  ChevronRight,
  Clipboard,
  Columns3,
  Database,
  FileSpreadsheet,
  History,
  Info,
  LockKeyhole,
  Menu,
  PanelRight,
  Pencil,
  RefreshCw,
  Rows3,
  Search,
  ShieldAlert,
  ShieldCheck,
  Upload,
  XCircle,
} from "lucide-react"
import type { FormEvent, ReactNode } from "react"
import { useEffect, useRef, useState } from "react"

import {
  MutationError,
  StatusBadge,
  useVisualTheme,
} from "@/components/reca-visual-refresh"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"

import type {
  ActionCapability,
  DatasetColumnViewModel,
  DataWorkspaceViewModel,
  QualityIssueViewModel,
  WorksheetViewModel,
} from "../model"
import type { DataWorkspaceWorkspaceProps } from "./contracts"
import {
  CleaningView,
  IssueActionDialogs,
  OperationsInspector,
  QualityView,
  VersionsOperationsView,
} from "./DataWorkspaceOperations"
import "./data-workspace.css"

type WorkspaceView = "data" | "columns" | "quality" | "cleaning" | "versions"
type MobileSurface = "datasets" | "workspace" | "columns" | "inspector"

const views: ReadonlyArray<{
  id: WorkspaceView
  label: string
  icon: typeof Database
}> = [
  { id: "data", label: "数据", icon: Rows3 },
  { id: "columns", label: "字段", icon: Columns3 },
  { id: "quality", label: "质量", icon: ShieldCheck },
  { id: "cleaning", label: "清洗", icon: RefreshCw },
  { id: "versions", label: "版本", icon: History },
]

function formatDate(value: string) {
  const date = new Date(value)
  return Number.isNaN(date.getTime())
    ? value
    : new Intl.DateTimeFormat("zh-CN", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
      }).format(date)
}

function formatNumber(value: number | null) {
  return value === null ? "未知" : new Intl.NumberFormat("zh-CN").format(value)
}

function displayValue(value: string | null | undefined) {
  return value && value.trim() ? value : "未提供"
}

function CapabilityButton({
  capability,
  label,
  pending,
  icon,
  variant = "outline",
  buttonType = "button",
  onClick,
}: {
  capability: ActionCapability
  label: string
  pending: boolean
  icon: ReactNode
  variant?: "default" | "outline" | "ghost"
  buttonType?: "button" | "submit"
  onClick: () => void
}) {
  const reason = capability.disabledReason ?? label
  return (
    <Button
      type={buttonType}
      size="sm"
      variant={variant}
      disabled={!capability.allowed || pending}
      title={reason}
      aria-label={!capability.allowed ? `${label}：${reason}` : label}
      onClick={onClick}
    >
      {pending ? <RefreshCw className="m4-spin" aria-hidden="true" /> : icon}
      {pending ? "处理中" : label}
    </Button>
  )
}

function MetadataValue({
  label,
  value,
}: {
  label: string
  value: string | null
}) {
  const shown = displayValue(value)
  return (
    <div className="m4-metadata-value">
      <dt>{label}</dt>
      <dd title={shown}>{shown}</dd>
      {value ? (
        <button
          type="button"
          className="m4-icon-button"
          aria-label={`复制${label}`}
          title={`复制${label}`}
          onClick={() => void navigator.clipboard?.writeText(value)}
        >
          <Clipboard aria-hidden="true" />
        </button>
      ) : null}
    </div>
  )
}

function DatasetRail({
  data,
  onSelect,
}: {
  data: DataWorkspaceViewModel
  onSelect: (datasetId: string, versionId: string | null) => void
}) {
  return (
    <aside className="m4-dataset-rail" data-od-id="dataset-version-rail">
      <div className="m4-pane-heading">
        <div>
          <Database aria-hidden="true" />
          <strong>数据集</strong>
        </div>
        <span>{data.datasets.length}</span>
      </div>
      <nav className="m4-dataset-list" aria-label="数据集与当前版本">
        {data.datasets.map((dataset) => {
          const selected = data.dataset?.id === dataset.id
          return (
            <button
              key={dataset.id}
              type="button"
              aria-current={selected ? "page" : undefined}
              onClick={() => onSelect(dataset.id, dataset.currentVersionId)}
            >
              <span className="m4-dataset-icon" aria-hidden="true">
                <FileSpreadsheet />
              </span>
              <span className="m4-dataset-copy">
                <strong title={dataset.name}>{dataset.name}</strong>
                <small>
                  {dataset.sourceType} · {dataset.licenseStatus}
                </small>
                <small>{formatDate(dataset.updatedAt)}</small>
              </span>
              <ChevronRight aria-hidden="true" />
            </button>
          )
        })}
      </nav>
      {data.version ? (
        <section className="m4-rail-version" aria-label="当前版本摘要">
          <div className="m4-section-label">当前上下文</div>
          <div className="m4-rail-version__line">
            <strong>版本 {data.version.versionNumber}</strong>
            <StatusBadge label={data.version.status} tone={data.version.tone} />
          </div>
          <dl>
            <div>
              <dt>类型</dt>
              <dd>{data.version.versionType}</dd>
            </div>
            <div>
              <dt>格式</dt>
              <dd>{data.version.fileFormat}</dd>
            </div>
            <div>
              <dt>行</dt>
              <dd>{formatNumber(data.version.rowCount)}</dd>
            </div>
            <div>
              <dt>列</dt>
              <dd>{formatNumber(data.version.columnCount)}</dd>
            </div>
          </dl>
          {data.version.invalidated ? (
            <p className="m4-inline-notice" data-tone="danger">
              <XCircle aria-hidden="true" />{" "}
              此版本已失效，不可作为当前执行输入。
            </p>
          ) : null}
          {data.versions.length > 0 ? (
            <div className="m4-version-history" aria-label="正式版本历史">
              <div className="m4-section-label">版本历史</div>
              {data.versions.map((version) => (
                <button
                  key={version.id}
                  type="button"
                  aria-current={
                    version.id === data.version?.id ? "page" : undefined
                  }
                  onClick={() => onSelect(version.datasetId, version.id)}
                >
                  <span>
                    <strong>版本 {version.versionNumber}</strong>
                    <small>{version.versionType}</small>
                  </span>
                  <StatusBadge label={version.status} tone={version.tone} />
                </button>
              ))}
            </div>
          ) : null}
        </section>
      ) : null}
    </aside>
  )
}

function WorkspaceHeader({
  data,
  onOpenDatasets,
  onOpenInspector,
  onOpenUpload,
  pendingUpload,
}: {
  data: DataWorkspaceViewModel
  onOpenDatasets: () => void
  onOpenInspector: () => void
  onOpenUpload: () => void
  pendingUpload: boolean
}) {
  const dataset = data.dataset
  const version = data.version
  return (
    <header className="m4-workspace-header" data-od-id="data-workspace-header">
      <div className="m4-header-mobile-actions">
        <Button
          type="button"
          size="icon"
          variant="ghost"
          onClick={onOpenDatasets}
          aria-label="打开数据集列表"
          title="数据集"
        >
          <Menu aria-hidden="true" />
        </Button>
      </div>
      <div className="m4-header-copy">
        <div className="m4-breadcrumb">
          项目数据 / {version ? `版本 ${version.versionNumber}` : "未选择版本"}
        </div>
        <h1 data-od-id="dataset-title">{dataset?.name ?? "数据工作台"}</h1>
        <p>{displayValue(dataset?.description)}</p>
        <div className="m4-status-line">
          {dataset ? (
            <StatusBadge label={dataset.status} tone={dataset.tone} />
          ) : null}
          {version ? (
            <StatusBadge label={version.status} tone={version.tone} />
          ) : null}
          {version?.original ? (
            <span>
              <Archive aria-hidden="true" /> Original
            </span>
          ) : null}
          {version?.current ? (
            <span>
              <Check aria-hidden="true" /> 当前版本
            </span>
          ) : null}
          {version?.invalidated ? (
            <span data-tone="danger">
              <XCircle aria-hidden="true" /> 已失效
            </span>
          ) : null}
          {version?.selectedWorksheetName ? (
            <span>
              <FileSpreadsheet aria-hidden="true" />{" "}
              {version.selectedWorksheetName}
            </span>
          ) : null}
          {version ? (
            <span>
              {formatNumber(version.rowCount)} 行 ·{" "}
              {formatNumber(version.columnCount)} 列
            </span>
          ) : null}
        </div>
      </div>
      <div className="m4-header-actions">
        <CapabilityButton
          capability={data.capabilities.uploadDataset}
          label="上传数据集"
          pending={pendingUpload}
          icon={<Upload aria-hidden="true" />}
          variant="default"
          onClick={onOpenUpload}
        />
        <Button
          type="button"
          size="sm"
          variant="outline"
          className="m4-inspector-trigger"
          onClick={onOpenInspector}
        >
          <PanelRight aria-hidden="true" /> 详情
        </Button>
      </div>
    </header>
  )
}

function WorkspaceTabs({
  value,
  onChange,
}: {
  value: WorkspaceView
  onChange: (view: WorkspaceView) => void
}) {
  return (
    <nav
      className="m4-workspace-tabs"
      aria-label="数据工作台视图"
      data-od-id="workspace-tabs"
    >
      {views.map((view) => {
        const Icon = view.icon
        return (
          <button
            key={view.id}
            type="button"
            aria-current={value === view.id ? "page" : undefined}
            onClick={() => onChange(view.id)}
          >
            <Icon aria-hidden="true" />
            {view.label}
          </button>
        )
      })}
    </nav>
  )
}

function ContextNotices({ data }: { data: DataWorkspaceViewModel }) {
  const notices: Array<{ tone: string; icon: ReactNode; text: string }> = []
  if (!data.capabilities.permissionsKnown)
    notices.push({
      tone: "unknown",
      icon: <LockKeyhole />,
      text: "权限状态未知，所有写操作已安全关闭。",
    })
  if (data.dataset?.licenseWarning)
    notices.push({
      tone: "warning",
      icon: <AlertTriangle />,
      text: `许可状态 ${data.dataset.licenseStatus}：需在复用或发布前复核。`,
    })
  if (data.version && !data.version.knownStatus)
    notices.push({
      tone: "degraded",
      icon: <ShieldAlert />,
      text: "检测到未知版本状态，当前写操作保持关闭。",
    })
  if (data.version?.invalidated)
    notices.push({
      tone: "danger",
      icon: <XCircle />,
      text: data.version.invalidationReason ?? "此版本已失效，仅保留查看。",
    })
  if (!notices.length) return null
  return (
    <div className="m4-notice-stack" aria-label="数据可信状态">
      {notices.map((notice, index) => (
        <p
          key={`${notice.tone}-${index}`}
          className="m4-inline-notice"
          data-tone={notice.tone}
        >
          {notice.icon}
          {notice.text}
        </p>
      ))}
    </div>
  )
}

function WorksheetStrip({
  data,
  onRequest,
}: {
  data: DataWorkspaceViewModel
  onRequest: (worksheet: WorksheetViewModel) => void
}) {
  const version = data.version
  if (!version || version.fileFormat !== "XLSX") return null
  return (
    <section
      className="m4-worksheet-strip"
      data-od-id="worksheet-selector"
      aria-labelledby="worksheet-heading"
    >
      <div className="m4-section-heading">
        <div>
          <FileSpreadsheet aria-hidden="true" />
          <h2 id="worksheet-heading">工作表</h2>
        </div>
        <span>{version.worksheets.length} 个</span>
      </div>
      <div className="m4-worksheet-scroll">
        {version.worksheets.map((worksheet) => {
          const risky = worksheet.visibility !== "VISIBLE"
          return (
            <button
              key={worksheet.name}
              type="button"
              disabled={!data.capabilities.selectWorksheet.allowed}
              aria-pressed={worksheet.selected}
              title={
                data.capabilities.selectWorksheet.disabledReason ??
                worksheet.name
              }
              onClick={() => onRequest(worksheet)}
            >
              <span className="m4-sheet-name">{worksheet.name}</span>
              <span className="m4-sheet-meta">
                {worksheet.estimatedRows} 行 · {worksheet.estimatedColumns} 列
              </span>
              <span
                className="m4-sheet-visibility"
                data-risk={risky ? "true" : "false"}
              >
                {risky ? (
                  <AlertTriangle aria-hidden="true" />
                ) : (
                  <Check aria-hidden="true" />
                )}
                {worksheet.visibility}
              </span>
            </button>
          )
        })}
      </div>
      {!data.capabilities.selectWorksheet.allowed ? (
        <p className="m4-disabled-reason">
          <LockKeyhole aria-hidden="true" />{" "}
          {data.capabilities.selectWorksheet.disabledReason}
        </p>
      ) : null}
    </section>
  )
}

function PreviewTable({
  data,
  onSelectColumn,
  onSelectCell,
}: {
  data: DataWorkspaceViewModel
  onSelectColumn: (column: DatasetColumnViewModel | null) => void
  onSelectCell: (columnName: string, value: string, row: number) => void
}) {
  const preview = data.preview
  const findColumn = (name: string) =>
    data.columns.find((column) => column.sourceName === name) ?? null
  return (
    <section className="m4-primary-surface" data-od-id="data-preview">
      <div className="m4-table-toolbar">
        <div>
          <Rows3 aria-hidden="true" />
          <h2>有界数据预览</h2>
        </div>
        <div className="m4-preview-status">
          {preview?.masked ? (
            <span>
              <ShieldAlert aria-hidden="true" /> 敏感值已遮蔽
            </span>
          ) : null}
          {preview?.truncated ? (
            <span>
              <Info aria-hidden="true" /> 仅返回 {preview.returned} /{" "}
              {formatNumber(preview.totalRows)} 行
            </span>
          ) : null}
        </div>
      </div>
      {preview ? (
        <div
          className="m4-preview-scroller"
          role="region"
          aria-label="数据预览表，可横向滚动"
          tabIndex={0}
        >
          <table>
            <thead>
              <tr>
                <th className="m4-row-number">#</th>
                {preview.columns.map((name) => {
                  const column = findColumn(name)
                  return (
                    <th key={name} scope="col">
                      <button
                        type="button"
                        onClick={() => onSelectColumn(column)}
                        title={name}
                      >
                        <span>{column?.displayName ?? name}</span>
                        <small>{name}</small>
                      </button>
                    </th>
                  )
                })}
              </tr>
            </thead>
            <tbody>
              {preview.rows.map((row, rowIndex) => (
                <tr key={`${rowIndex}-${preview.returned}`}>
                  <th className="m4-row-number" scope="row">
                    {rowIndex + 1}
                  </th>
                  {preview.columns.map((name) => {
                    const value = row[name] ?? ""
                    const empty = value.trim() === ""
                    return (
                      <td key={name}>
                        <button
                          type="button"
                          onClick={() =>
                            onSelectCell(name, value, rowIndex + 1)
                          }
                          title={empty ? "空值" : value}
                        >
                          <span className={empty ? "m4-null-value" : undefined}>
                            {empty ? "NULL" : value}
                          </span>
                        </button>
                      </td>
                    )
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="m4-surface-empty">
          <Rows3 aria-hidden="true" />
          <strong>当前版本没有可用预览</strong>
          <p>这可能是版本状态、工作表选择或正式投影尚未就绪。</p>
        </div>
      )}
      {preview ? (
        <footer className="m4-table-footer">
          <span>返回 {preview.returned} 行</span>
          <span>总计 {formatNumber(preview.totalRows)} 行</span>
          <span>{preview.masked ? "遮蔽预览" : "标准预览"}</span>
          <span>{preview.truncated ? "已截断" : "完整窗口"}</span>
        </footer>
      ) : null}
    </section>
  )
}

function ColumnsTable({
  data,
  selectedId,
  onSelect,
}: {
  data: DataWorkspaceViewModel
  selectedId: string | null
  onSelect: (column: DatasetColumnViewModel) => void
}) {
  return (
    <section className="m4-primary-surface" data-od-id="columns-workbench">
      <div className="m4-table-toolbar">
        <div>
          <Columns3 aria-hidden="true" />
          <h2>字段字典</h2>
        </div>
        <span>{data.columns.length} 个字段</span>
      </div>
      <div
        className="m4-columns-scroller"
        role="region"
        aria-label="字段字典表"
        tabIndex={0}
      >
        <table>
          <thead>
            <tr>
              <th>字段</th>
              <th>推断类型</th>
              <th>确认类型</th>
              <th>语义角色</th>
              <th>缺失率</th>
              <th>唯一值</th>
              <th>敏感性</th>
              <th>确认状态</th>
            </tr>
          </thead>
          <tbody>
            {data.columns.map((column) => (
              <tr
                key={column.id}
                data-selected={selectedId === column.id ? "true" : "false"}
              >
                <td>
                  <button
                    type="button"
                    className="m4-column-name"
                    onClick={() => onSelect(column)}
                  >
                    <strong title={column.displayName ?? column.sourceName}>
                      {column.displayName ?? column.sourceName}
                    </strong>
                    <small title={column.sourceName}>{column.sourceName}</small>
                  </button>
                </td>
                <td>
                  <code>{column.inferredType}</code>
                </td>
                <td>
                  <code>{column.confirmedType ?? "未确认"}</code>
                </td>
                <td>{displayValue(column.semanticRole)}</td>
                <td>
                  {column.missingRatio === null
                    ? "未知"
                    : `${(column.missingRatio * 100).toFixed(1)}%`}
                </td>
                <td>{formatNumber(column.uniqueCount)}</td>
                <td>
                  <span
                    className="m4-cell-status"
                    data-tone={
                      column.sensitiveConfirmed
                        ? "danger"
                        : column.sensitiveCandidate
                          ? "warning"
                          : "muted"
                    }
                  >
                    {column.sensitiveConfirmed ? (
                      <ShieldAlert aria-hidden="true" />
                    ) : (
                      <ShieldCheck aria-hidden="true" />
                    )}
                    {column.sensitiveConfirmed
                      ? "已确认"
                      : column.sensitiveCandidate
                        ? "候选"
                        : "否"}
                  </span>
                </td>
                <td>
                  {column.confirmationKnown
                    ? column.confirmationStatus
                    : "UNKNOWN"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}

function IdentityInspector({
  data,
  props,
}: {
  data: DataWorkspaceViewModel
  props: DataWorkspaceWorkspaceProps
}) {
  const dataset = data.dataset
  const [name, setName] = useState(dataset?.name ?? "")
  const [description, setDescription] = useState(dataset?.description ?? "")
  const [publisher, setPublisher] = useState(dataset?.publisher ?? "")
  const [licenseName, setLicenseName] = useState(dataset?.licenseName ?? "")
  useEffect(() => {
    setName(dataset?.name ?? "")
    setDescription(dataset?.description ?? "")
    setPublisher(dataset?.publisher ?? "")
    setLicenseName(dataset?.licenseName ?? "")
  }, [dataset?.id, dataset?.lockVersion])
  if (!dataset) return <p className="m4-inspector-empty">未选择数据集。</p>
  const capability = data.capabilities.updateDatasetIdentity
  const submit = (event: FormEvent) => {
    event.preventDefault()
    if (!capability.allowed) return
    props.onEvent({
      action: "update-dataset-identity",
      input: {
        datasetId: dataset.id,
        lockVersion: dataset.lockVersion,
        changes: {
          name,
          description: description || null,
          publisher: publisher || null,
          licenseName: licenseName || null,
        },
      },
    })
  }
  return (
    <form className="m4-inspector-form" onSubmit={submit}>
      <div className="m4-inspector-title">
        <div>
          <Pencil aria-hidden="true" />
          <strong>数据身份证</strong>
        </div>
        <span>lock {dataset.lockVersion}</span>
      </div>
      <label>
        名称
        <Input
          value={name}
          onChange={(event) => setName(event.target.value)}
          disabled={!capability.allowed}
        />
      </label>
      <label>
        描述
        <textarea
          value={description}
          onChange={(event) => setDescription(event.target.value)}
          disabled={!capability.allowed}
          rows={3}
        />
      </label>
      <label>
        发布者
        <Input
          value={publisher}
          onChange={(event) => setPublisher(event.target.value)}
          disabled={!capability.allowed}
        />
      </label>
      <label>
        许可名称
        <Input
          value={licenseName}
          onChange={(event) => setLicenseName(event.target.value)}
          disabled={!capability.allowed}
        />
      </label>
      <div className="m4-readonly-fields">
        <MetadataValue label="来源平台" value={dataset.sourcePlatform} />
        <MetadataValue label="来源标识" value={dataset.sourceIdentifier} />
        <MetadataValue label="DOI" value={dataset.doi} />
        <MetadataValue label="建议引文" value={dataset.recommendedCitation} />
        <MetadataValue label="已知局限" value={dataset.knownLimitations} />
      </div>
      <CapabilityButton
        capability={capability}
        label="保存身份证"
        pending={props.pendingAction === "update-dataset-identity"}
        icon={<Check aria-hidden="true" />}
        variant="default"
        buttonType="submit"
        onClick={() => undefined}
      />
      {!capability.allowed ? (
        <p className="m4-disabled-reason">
          <LockKeyhole aria-hidden="true" /> {capability.disabledReason}
        </p>
      ) : null}
    </form>
  )
}

function ColumnInspector({
  column,
  data,
  props,
}: {
  column: DatasetColumnViewModel
  data: DataWorkspaceViewModel
  props: DataWorkspaceWorkspaceProps
}) {
  const [displayName, setDisplayName] = useState(column.displayName ?? "")
  const [confirmedType, setConfirmedType] = useState(column.confirmedType ?? "")
  const [semanticRole, setSemanticRole] = useState(column.semanticRole ?? "")
  const [unit, setUnit] = useState(column.unit ?? "")
  const [sensitive, setSensitive] = useState(column.sensitiveConfirmed)
  const [confirmed, setConfirmed] = useState(
    column.confirmationStatus === "CONFIRMED",
  )
  useEffect(() => {
    setDisplayName(column.displayName ?? "")
    setConfirmedType(column.confirmedType ?? "")
    setSemanticRole(column.semanticRole ?? "")
    setUnit(column.unit ?? "")
    setSensitive(column.sensitiveConfirmed)
    setConfirmed(column.confirmationStatus === "CONFIRMED")
  }, [
    column.id,
    column.lockVersion,
    column.displayName,
    column.confirmedType,
    column.semanticRole,
    column.unit,
    column.sensitiveConfirmed,
    column.confirmationStatus,
  ])
  const capability = data.capabilities.updateColumn
  const submit = (event: FormEvent) => {
    event.preventDefault()
    if (!capability.allowed) return
    props.onEvent({
      action: "update-column",
      input: {
        columnId: column.id,
        lockVersion: column.lockVersion,
        changes: {
          displayName: displayName || null,
          confirmedType: confirmedType || null,
          semanticRole: semanticRole || null,
          unit: unit || null,
          isSensitive: sensitive,
          confirmationStatus: confirmed ? "CONFIRMED" : "UNCONFIRMED",
        },
      },
    })
  }
  return (
    <form className="m4-inspector-form" onSubmit={submit}>
      <div className="m4-inspector-title">
        <div>
          <Columns3 aria-hidden="true" />
          <strong>字段定义</strong>
        </div>
        <span>lock {column.lockVersion}</span>
      </div>
      <div className="m4-field-origin">
        <span>源字段</span>
        <code title={column.sourceName}>{column.sourceName}</code>
      </div>
      <div className="m4-field-origin">
        <span>推断类型（只读）</span>
        <code>{column.inferredType}</code>
      </div>
      <label>
        显示名称
        <Input
          value={displayName}
          onChange={(event) => setDisplayName(event.target.value)}
          disabled={!capability.allowed}
        />
      </label>
      <label>
        确认类型
        <Input
          value={confirmedType}
          onChange={(event) => setConfirmedType(event.target.value)}
          disabled={!capability.allowed}
        />
      </label>
      <label>
        语义角色
        <Input
          value={semanticRole}
          onChange={(event) => setSemanticRole(event.target.value)}
          disabled={!capability.allowed}
        />
      </label>
      <label>
        单位
        <Input
          value={unit}
          onChange={(event) => setUnit(event.target.value)}
          disabled={!capability.allowed}
        />
      </label>
      <label className="m4-checkbox-field">
        <input
          type="checkbox"
          checked={sensitive}
          onChange={(event) => setSensitive(event.target.checked)}
          disabled={!capability.allowed}
        />
        <span>确认为敏感字段</span>
      </label>
      <label className="m4-checkbox-field">
        <input
          type="checkbox"
          aria-label="Confirm field definition"
          checked={confirmed}
          onChange={(event) => setConfirmed(event.target.checked)}
          disabled={!capability.allowed || !confirmedType}
        />
        <span>确认该字段定义</span>
      </label>
      <div className="m4-readonly-fields">
        <MetadataValue label="继承来源" value={column.inheritedFromColumnId} />
        <MetadataValue label="描述（只读）" value={column.description} />
      </div>
      <CapabilityButton
        capability={capability}
        label="保存字段定义"
        pending={props.pendingAction === "update-column"}
        icon={<Check aria-hidden="true" />}
        variant="default"
        buttonType="submit"
        onClick={() => undefined}
      />
      {!capability.allowed ? (
        <p className="m4-disabled-reason">
          <LockKeyhole aria-hidden="true" /> {capability.disabledReason}
        </p>
      ) : null}
    </form>
  )
}

function ContextInspector({
  data,
  props,
  view,
  selectedColumn,
  selectedCell,
  selectedIssueId,
  onAcknowledgeIssue,
  onIgnoreIssue,
}: {
  data: DataWorkspaceViewModel
  props: DataWorkspaceWorkspaceProps
  view: WorkspaceView
  selectedColumn: DatasetColumnViewModel | null
  selectedCell: { column: string; value: string; row: number } | null
  selectedIssueId: string | null
  onAcknowledgeIssue: (issue: QualityIssueViewModel) => void
  onIgnoreIssue: (issue: QualityIssueViewModel) => void
}) {
  return (
    <aside className="m4-context-inspector" data-od-id="context-inspector">
      <div className="m4-pane-heading">
        <div>
          <PanelRight aria-hidden="true" />
          <strong>检查器</strong>
        </div>
      </div>
      <div className="m4-inspector-scroll">
        {view === "quality" || view === "cleaning" || view === "versions" ? (
          <OperationsInspector
            view={view}
            data={data}
            props={props}
            selectedIssueId={selectedIssueId}
            onAcknowledge={onAcknowledgeIssue}
            onIgnore={onIgnoreIssue}
          />
        ) : selectedCell ? (
          <section className="m4-cell-inspector">
            <div className="m4-inspector-title">
              <div>
                <Search aria-hidden="true" />
                <strong>单元格</strong>
              </div>
              <span>第 {selectedCell.row} 行</span>
            </div>
            <MetadataValue label="字段" value={selectedCell.column} />
            <div className="m4-cell-value">
              <span>预览值</span>
              <code>{selectedCell.value || "NULL"}</code>
            </div>
            {data.preview?.masked ? (
              <p className="m4-inline-notice" data-tone="warning">
                <ShieldAlert aria-hidden="true" />{" "}
                预览已遮蔽，无法在本地显示完整敏感值。
              </p>
            ) : null}
          </section>
        ) : selectedColumn ? (
          <ColumnInspector column={selectedColumn} data={data} props={props} />
        ) : (
          <IdentityInspector data={data} props={props} />
        )}
        {data.version ? (
          <section className="m4-inspector-metadata">
            <div className="m4-section-label">版本元数据</div>
            <MetadataValue label="Data hash" value={data.version.dataHash} />
            <MetadataValue
              label="Schema hash"
              value={data.version.schemaHash}
            />
            <MetadataValue
              label="Projection hash"
              value={data.version.projectionHash}
            />
          </section>
        ) : null}
      </div>
    </aside>
  )
}

function UploadDialog({
  open,
  onOpenChange,
  data,
  props,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  data: DataWorkspaceViewModel
  props: DataWorkspaceWorkspaceProps
}) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File | null>(null)
  const [name, setName] = useState("")
  const pending = props.pendingAction === "upload-dataset"
  const capability = data.capabilities.uploadDataset
  const chooseFile = (next: File | null) => {
    setFile(next)
    if (next && !name) setName(next.name.replace(/\.(csv|xlsx)$/i, ""))
  }
  const emitUploadIntent = () => {
    if (!file || !name.trim() || !capability.allowed || pending) return
    props.onEvent({
      action: "upload-dataset",
      input: { file, name: name.trim() },
    })
  }
  const submit = (event: FormEvent) => {
    event.preventDefault()
    emitUploadIntent()
  }
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="m4-dialog" data-od-id="upload-dataset-dialog">
        <DialogHeader>
          <DialogTitle>上传科研数据集</DialogTitle>
          <DialogDescription>
            选择 CSV 或 XLSX。上传事件只提交文件与数据集名称，结果由正式 Props
            返回。
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={submit} className="m4-upload-form">
          <input
            ref={inputRef}
            type="file"
            accept=".csv,.xlsx,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            hidden
            onChange={(event) => chooseFile(event.target.files?.[0] ?? null)}
          />
          <button
            type="button"
            className="m4-dropzone"
            onClick={() => inputRef.current?.click()}
            disabled={!capability.allowed || pending}
          >
            <Upload aria-hidden="true" />
            <strong>{file ? file.name : "选择 CSV / XLSX 文件"}</strong>
            <span>
              {file
                ? `${(file.size / 1024).toFixed(1)} KB · ${file.name.split(".").pop()?.toUpperCase()}`
                : "单个文件；选择后仍需确认提交"}
            </span>
          </button>
          <label>
            数据集名称
            <Input
              value={name}
              onChange={(event) => setName(event.target.value)}
              disabled={!capability.allowed || pending}
              placeholder="输入数据集名称"
            />
          </label>
          {props.mutationError ? (
            <MutationError {...props.mutationError} />
          ) : null}
          {!capability.allowed ? (
            <p className="m4-disabled-reason">
              <LockKeyhole aria-hidden="true" /> {capability.disabledReason}
            </p>
          ) : null}
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              关闭
            </Button>
            <Button
              type="submit"
              disabled={!file || !name.trim() || !capability.allowed || pending}
              onClick={(event) => {
                event.preventDefault()
                emitUploadIntent()
              }}
            >
              {pending ? (
                <RefreshCw className="m4-spin" aria-hidden="true" />
              ) : (
                <Upload aria-hidden="true" />
              )}
              {pending ? "上传处理中" : "提交上传"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

function HiddenWorksheetDialog({
  worksheet,
  versionId,
  pending,
  onClose,
  onConfirm,
}: {
  worksheet: WorksheetViewModel | null
  versionId: string | null
  pending: boolean
  onClose: () => void
  onConfirm: (versionId: string, worksheetName: string) => void
}) {
  return (
    <Dialog
      open={Boolean(worksheet)}
      onOpenChange={(open) => !open && onClose()}
    >
      <DialogContent className="m4-dialog" data-od-id="hidden-worksheet-dialog">
        <DialogHeader>
          <DialogTitle>确认选择隐藏工作表</DialogTitle>
          <DialogDescription>
            该工作表标记为 {worksheet?.visibility}
            。隐藏状态可能表示归档、辅助计算或不应直接分析的数据。
          </DialogDescription>
        </DialogHeader>
        <div className="m4-hidden-sheet-summary">
          <AlertTriangle aria-hidden="true" />
          <div>
            <strong>{worksheet?.name}</strong>
            <span>
              {worksheet?.estimatedRows} 行 · {worksheet?.estimatedColumns} 列
            </span>
          </div>
        </div>
        <p className="m4-inline-notice" data-tone="warning">
          <ShieldAlert aria-hidden="true" /> 继续将发送正式
          acknowledgeHidden=true；不会在本地把它改成已选状态。
        </p>
        <DialogFooter>
          <Button type="button" variant="outline" onClick={onClose}>
            取消
          </Button>
          <Button
            type="button"
            disabled={!worksheet || !versionId || pending}
            onClick={() =>
              worksheet && versionId && onConfirm(versionId, worksheet.name)
            }
          >
            {pending ? (
              <RefreshCw className="m4-spin" aria-hidden="true" />
            ) : (
              <Check aria-hidden="true" />
            )}{" "}
            确认选择
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

function StableStateShell({
  state,
  message,
  error,
  onRetry,
}: {
  state: "loading" | "empty" | "error"
  message?: string
  error?: DataWorkspaceWorkspaceProps["mutationError"]
  onRetry?: () => void
}) {
  const visualTheme = useVisualTheme()
  return (
    <section
      className="m4-data-workspace reca-visual-refresh"
      data-state={state}
      data-theme={visualTheme}
      aria-busy={state === "loading"}
    >
      <aside className="m4-dataset-rail m4-state-rail">
        <div className="m4-skeleton-block m4-skeleton-title" />
        <div className="m4-skeleton-block m4-skeleton-item" />
      </aside>
      <main className="m4-workspace-center">
        <header className="m4-workspace-header m4-state-header">
          <div className="m4-skeleton-copy">
            <div className="m4-skeleton-block m4-skeleton-kicker" />
            <div className="m4-skeleton-block m4-skeleton-heading" />
            <div className="m4-skeleton-block m4-skeleton-text" />
          </div>
        </header>
        <WorkspaceTabs value="data" onChange={() => undefined} />
        <div className="m4-state-surface">
          {state === "loading" ? (
            <>
              <div className="m4-skeleton-block m4-skeleton-toolbar" />
              <div className="m4-skeleton-table">
                {Array.from({ length: 8 }, (_, index) => (
                  <div key={index} />
                ))}
              </div>
            </>
          ) : null}
          {state === "empty" ? (
            <div className="m4-surface-empty">
              <Database aria-hidden="true" />
              <strong>尚无数据集</strong>
              <p>{message}</p>
              <Button type="button" disabled title="缺少正式 capability 投影">
                <Upload aria-hidden="true" /> 上传数据集
              </Button>
            </div>
          ) : null}
          {state === "error" && error ? (
            <MutationError {...error} onRetry={onRetry} />
          ) : null}
        </div>
      </main>
      <aside className="m4-context-inspector m4-state-inspector">
        <div className="m4-skeleton-block m4-skeleton-title" />
        <div className="m4-skeleton-block m4-skeleton-item" />
      </aside>
    </section>
  )
}

export function DataWorkspace(props: DataWorkspaceWorkspaceProps) {
  const visualTheme = useVisualTheme()
  const [view, setView] = useState<WorkspaceView>(props.initialView ?? "data")
  const [mobileSurface, setMobileSurface] = useState<MobileSurface>("workspace")
  const [selectedColumnId, setSelectedColumnId] = useState<string | null>(null)
  const [selectedCell, setSelectedCell] = useState<{
    column: string
    value: string
    row: number
  } | null>(null)
  const [uploadOpen, setUploadOpen] = useState(false)
  const [datasetSheetOpen, setDatasetSheetOpen] = useState(false)
  const [inspectorSheetOpen, setInspectorSheetOpen] = useState(false)
  const [hiddenWorksheet, setHiddenWorksheet] =
    useState<WorksheetViewModel | null>(null)
  const [selectedIssueId, setSelectedIssueId] = useState<string | null>(null)
  const [acknowledgeIssue, setAcknowledgeIssue] =
    useState<QualityIssueViewModel | null>(null)
  const [ignoreIssue, setIgnoreIssue] = useState<QualityIssueViewModel | null>(
    null,
  )
  const uploadTriggerRef = useRef<HTMLElement | null>(null)
  const datasetSheetTriggerRef = useRef<HTMLElement | null>(null)
  const inspectorSheetTriggerRef = useRef<HTMLElement | null>(null)
  const worksheetTriggerRef = useRef<HTMLElement | null>(null)
  const issueActionTriggerRef = useRef<HTMLElement | null>(null)

  useEffect(() => {
    setView(props.initialView ?? "data")
  }, [props.initialView])

  const rememberTrigger = (ref: { current: HTMLElement | null }) => {
    ref.current = document.activeElement as HTMLElement | null
  }
  const restoreTrigger = (ref: { current: HTMLElement | null }) => {
    const trigger = ref.current
    ref.current = null
    requestAnimationFrame(() => trigger?.focus())
  }

  if (props.content.state === "loading")
    return <StableStateShell state="loading" />
  if (props.content.state === "empty")
    return <StableStateShell state="empty" message={props.content.message} />
  if (props.content.state === "error")
    return (
      <StableStateShell
        state="error"
        error={props.content.error}
        onRetry={props.onRetry}
      />
    )

  const data = props.content.data
  const selectedColumn =
    data.columns.find((column) => column.id === selectedColumnId) ?? null
  const selectVersion = (datasetId: string, versionId: string | null) => {
    if (!versionId) return
    props.onEvent({ action: "select-version", input: { datasetId, versionId } })
    setDatasetSheetOpen(false)
  }
  const chooseColumn = (column: DatasetColumnViewModel | null) => {
    setSelectedColumnId(column?.id ?? null)
    setSelectedCell(null)
    if (column && window.matchMedia("(max-width: 1180px)").matches)
      setInspectorSheetOpen(true)
  }
  const chooseWorksheet = (worksheet: WorksheetViewModel) => {
    if (!data.version || !data.capabilities.selectWorksheet.allowed) return
    if (worksheet.visibility !== "VISIBLE") {
      rememberTrigger(worksheetTriggerRef)
      setHiddenWorksheet(worksheet)
      return
    }
    props.onEvent({
      action: "select-worksheet",
      input: {
        versionId: data.version.id,
        worksheetName: worksheet.name,
        acknowledgeHidden: false,
      },
    })
  }
  const renderView = () => {
    if (view === "data")
      return (
        <>
          <WorksheetStrip data={data} onRequest={chooseWorksheet} />
          <PreviewTable
            data={data}
            onSelectColumn={chooseColumn}
            onSelectCell={(column, value, row) => {
              setSelectedColumnId(null)
              setSelectedCell({ column, value, row })
              if (window.matchMedia("(max-width: 1180px)").matches)
                setInspectorSheetOpen(true)
            }}
          />
        </>
      )
    if (view === "columns")
      return (
        <ColumnsTable
          data={data}
          selectedId={selectedColumnId}
          onSelect={chooseColumn}
        />
      )
    if (view === "versions")
      return <VersionsOperationsView data={data} props={props} />
    if (view === "quality")
      return (
        <QualityView
          data={data}
          props={props}
          selectedIssueId={selectedIssueId}
          onSelectIssue={(issue) => {
            setSelectedIssueId(issue.id)
            if (window.matchMedia("(max-width: 1180px)").matches)
              setInspectorSheetOpen(true)
          }}
        />
      )
    return <CleaningView data={data} props={props} />
  }

  return (
    <section
      className="m4-data-workspace reca-visual-refresh"
      data-od-id="m4-data-workspace"
      data-mobile-surface={mobileSurface}
      data-theme={visualTheme}
    >
      <DatasetRail data={data} onSelect={selectVersion} />
      <main className="m4-workspace-center">
        <WorkspaceHeader
          data={data}
          onOpenDatasets={() => {
            rememberTrigger(datasetSheetTriggerRef)
            setDatasetSheetOpen(true)
          }}
          onOpenInspector={() => {
            rememberTrigger(inspectorSheetTriggerRef)
            setInspectorSheetOpen(true)
          }}
          onOpenUpload={() => {
            rememberTrigger(uploadTriggerRef)
            setUploadOpen(true)
          }}
          pendingUpload={props.pendingAction === "upload-dataset"}
        />
        <WorkspaceTabs
          value={view}
          onChange={(next) => {
            setView(next)
            props.onViewChange?.(next)
            if (next === "columns") setMobileSurface("columns")
            else setMobileSurface("workspace")
          }}
        />
        <nav className="m4-mobile-switcher" aria-label="移动端主要表面">
          <button
            type="button"
            aria-current={mobileSurface === "datasets" ? "page" : undefined}
            onClick={() => {
              rememberTrigger(datasetSheetTriggerRef)
              setDatasetSheetOpen(true)
            }}
          >
            <Database aria-hidden="true" />
            数据集
          </button>
          <button
            type="button"
            aria-current={mobileSurface === "inspector" ? "page" : undefined}
            onClick={() => {
              rememberTrigger(inspectorSheetTriggerRef)
              setInspectorSheetOpen(true)
            }}
          >
            <PanelRight aria-hidden="true" />
            详情
          </button>
        </nav>
        <ContextNotices data={data} />
        {props.mutationError ? (
          <div className="m4-mutation-error">
            <MutationError {...props.mutationError} />
          </div>
        ) : null}
        <div className="m4-view-content" data-view={view}>
          {renderView()}
        </div>
      </main>
      <ContextInspector
        data={data}
        props={props}
        view={view}
        selectedColumn={selectedColumn}
        selectedCell={selectedCell}
        selectedIssueId={selectedIssueId}
        onAcknowledgeIssue={(issue) => {
          rememberTrigger(issueActionTriggerRef)
          setAcknowledgeIssue(issue)
        }}
        onIgnoreIssue={(issue) => {
          rememberTrigger(issueActionTriggerRef)
          setIgnoreIssue(issue)
        }}
      />

      <Sheet
        open={datasetSheetOpen}
        onOpenChange={(open) => {
          setDatasetSheetOpen(open)
          if (!open) restoreTrigger(datasetSheetTriggerRef)
        }}
      >
        <SheetContent side="left" className="m4-sheet-content">
          <SheetHeader>
            <SheetTitle>数据集与版本</SheetTitle>
            <SheetDescription>
              选择只发送正式 select-version 意图，不改写当前版本事实。
            </SheetDescription>
          </SheetHeader>
          <DatasetRail data={data} onSelect={selectVersion} />
        </SheetContent>
      </Sheet>
      <Sheet
        open={inspectorSheetOpen}
        onOpenChange={(open) => {
          setInspectorSheetOpen(open)
          if (!open) restoreTrigger(inspectorSheetTriggerRef)
        }}
      >
        <SheetContent side="right" className="m4-sheet-content">
          <SheetHeader>
            <SheetTitle>上下文检查器</SheetTitle>
            <SheetDescription>
              编辑草稿仅在提交时发送正式事件。
            </SheetDescription>
          </SheetHeader>
          <ContextInspector
            data={data}
            props={props}
            view={view}
            selectedColumn={selectedColumn}
            selectedCell={selectedCell}
            selectedIssueId={selectedIssueId}
            onAcknowledgeIssue={(issue) => {
              rememberTrigger(issueActionTriggerRef)
              setAcknowledgeIssue(issue)
            }}
            onIgnoreIssue={(issue) => {
              rememberTrigger(issueActionTriggerRef)
              setIgnoreIssue(issue)
            }}
          />
        </SheetContent>
      </Sheet>
      <UploadDialog
        open={uploadOpen}
        onOpenChange={(open) => {
          setUploadOpen(open)
          if (!open) restoreTrigger(uploadTriggerRef)
        }}
        data={data}
        props={props}
      />
      <HiddenWorksheetDialog
        worksheet={hiddenWorksheet}
        versionId={data.version?.id ?? null}
        pending={props.pendingAction === "select-worksheet"}
        onClose={() => {
          setHiddenWorksheet(null)
          restoreTrigger(worksheetTriggerRef)
        }}
        onConfirm={(versionId, worksheetName) => {
          props.onEvent({
            action: "select-worksheet",
            input: { versionId, worksheetName, acknowledgeHidden: true },
          })
          setHiddenWorksheet(null)
          restoreTrigger(worksheetTriggerRef)
        }}
      />
      <IssueActionDialogs
        acknowledgeIssue={acknowledgeIssue}
        ignoreIssue={ignoreIssue}
        props={props}
        onCloseAcknowledge={() => {
          setAcknowledgeIssue(null)
          restoreTrigger(issueActionTriggerRef)
        }}
        onCloseIgnore={() => {
          setIgnoreIssue(null)
          restoreTrigger(issueActionTriggerRef)
        }}
      />
    </section>
  )
}
