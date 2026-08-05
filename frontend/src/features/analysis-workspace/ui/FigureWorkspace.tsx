import {
  AlertTriangle,
  Ban,
  CheckCircle2,
  CircleAlert,
  Download,
  FileBarChart,
  FileCode2,
  FileImage,
  FileText,
  ImageOff,
  Info,
  LoaderCircle,
  PanelRight,
  Play,
  RefreshCw,
  Save,
  ShieldAlert,
  ShieldCheck,
  Square,
  XCircle,
} from "lucide-react"
import { type ReactNode, useEffect, useMemo, useRef, useState } from "react"

import {
  DegradedNotice,
  JobProgress,
  MetadataList,
  PermissionNotice,
  StatusBadge,
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
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"

import type {
  ActionCapability,
  AnalysisWorkspaceViewModel,
  ArtifactReferenceViewModel,
  FigureChartType,
  FigurePlanInput,
  FigureValidationIssueViewModel,
  ResultValue,
} from "../model"
import type {
  AnalysisWorkspaceEvent,
  AnalysisWorkspaceWorkspaceProps,
} from "./contracts"
import "./figure-workspace.css"

type FigureMode = "plan" | "chart" | "issues" | "artifacts"

const chartTypes: ReadonlyArray<{ value: FigureChartType; label: string }> = [
  { value: "SCATTER", label: "散点图" },
  { value: "GROUP_COMPARISON", label: "组间比较" },
  { value: "HISTOGRAM", label: "直方图" },
  { value: "BOXPLOT", label: "箱线图" },
  { value: "CORRELATION_MATRIX", label: "相关矩阵" },
]

const knownIssueTypes = new Set([
  "MISSING_AXIS_LABEL",
  "MISSING_UNIT",
  "MISSING_LEGEND",
  "MISSING_CAPTION",
  "UNDEFINED_ERROR_BAR",
  "MISLEADING_AXIS_RANGE",
  "LOW_RESOLUTION",
  "VERSION_MISMATCH",
  "RESULT_MISMATCH",
])

const chartParameterKeys: Readonly<Record<FigureChartType, readonly string[]>> =
  {
    SCATTER: [
      "x_column_id",
      "y_column_id",
      "x_label",
      "y_label",
      "x_unit",
      "y_unit",
      "dpi",
    ],
    GROUP_COMPARISON: ["group_column_id", "y_column_id", "y_label", "y_unit"],
    HISTOGRAM: ["column_id", "x_label", "x_unit", "bins"],
    BOXPLOT: ["column_id", "group_column_id", "y_label", "y_unit"],
    CORRELATION_MATRIX: ["column_ids"],
  }

function chartLabel(value: FigureChartType | null) {
  return chartTypes.find((item) => item.value === value)?.label ?? "未提供"
}

function statusLabel(status: string, known = true) {
  if (!known) return `未知状态 · ${status}`
  const labels: Record<string, string> = {
    DRAFT: "草稿",
    READY: "已就绪",
    NEEDS_REVIEW: "需要复核",
    CONFIRMED: "已确认",
    INVALIDATED: "已失效",
    QUEUED: "排队中",
    RUNNING: "渲染中",
    COMPLETED: "渲染完成",
    FAILED: "渲染失败",
    AVAILABLE: "可下载",
    MASKED: "已遮蔽",
    OPEN: "待处理",
  }
  return labels[status] ?? status
}

function shortHash(value: string | null) {
  if (!value) return "未提供"
  if (value.length <= 20) return value
  return `${value.slice(0, 11)}…${value.slice(-7)}`
}

function parameterValue(value: ResultValue | undefined) {
  if (value === undefined || value === null) return "未投影"
  if (Array.isArray(value)) return value.join("、")
  if (typeof value === "object") return JSON.stringify(value)
  return String(value)
}

function actionReason({
  capability,
  pending,
  transportAvailable,
  permissionsKnown,
  extraReason,
}: {
  capability: ActionCapability
  pending: boolean
  transportAvailable: boolean
  permissionsKnown: boolean
  extraReason?: string | null
}) {
  if (pending) return "操作意图正在提交，请等待服务端响应。"
  if (!transportAvailable) return "Figure transport 尚未接线。"
  if (!permissionsKnown) return "权限状态未知，正式操作保持禁用。"
  if (extraReason) return extraReason
  if (!capability.allowed)
    return capability.disabledReason ?? "当前操作不可用。"
  return null
}

function FigureAction({
  capability,
  pending,
  transportAvailable,
  permissionsKnown,
  extraReason,
  icon,
  children,
  onClick,
  variant = "outline",
  iconOnly = false,
  label,
}: {
  capability: ActionCapability
  pending: boolean
  transportAvailable: boolean
  permissionsKnown: boolean
  extraReason?: string | null
  icon: ReactNode
  children?: ReactNode
  onClick: () => void
  variant?: "default" | "outline" | "destructive" | "ghost"
  iconOnly?: boolean
  label?: string
}) {
  const reason = actionReason({
    capability,
    pending,
    transportAvailable,
    permissionsKnown,
    extraReason,
  })
  return (
    <div className={iconOnly ? "m5-figure-icon-action" : "m5-action-control"}>
      <Button
        type="button"
        size={iconOnly ? "icon-sm" : "default"}
        variant={variant}
        disabled={Boolean(reason)}
        onClick={onClick}
        aria-label={label}
        title={label ?? reason ?? undefined}
      >
        {icon}
        {children}
      </Button>
      {!iconOnly && reason ? (
        <span className="m5-disabled-reason">{reason}</span>
      ) : null}
    </div>
  )
}

function defaultFigureDraft(data: AnalysisWorkspaceViewModel): FigurePlanInput {
  const first = data.columns[0]?.id ?? ""
  const second = data.columns[1]?.id ?? first
  return {
    datasetVersionId: data.dataset?.versionId ?? "",
    analysisRunId: data.run?.id ?? null,
    analysisResultId: data.results[0]?.id ?? null,
    chartType: "SCATTER",
    parameters: {
      x_column_id: first,
      y_column_id: second,
    },
    caption: "",
  }
}

function draftFromData(data: AnalysisWorkspaceViewModel): FigurePlanInput {
  if (!data.figurePlan) return defaultFigureDraft(data)
  return {
    datasetVersionId: data.figurePlan.datasetVersionId,
    analysisRunId: data.figurePlan.analysisRunId,
    analysisResultId: data.figurePlan.analysisResultId,
    chartType: data.figurePlan.chartType,
    parameters: data.figurePlan.parameters,
    caption: data.figurePlan.caption,
  }
}

function FigurePlanEditor({
  data,
  draft,
  setDraft,
  pendingAction,
  onCreate,
  unknownIntegrity,
}: {
  data: AnalysisWorkspaceViewModel
  draft: FigurePlanInput
  setDraft: (value: FigurePlanInput) => void
  pendingAction: AnalysisWorkspaceWorkspaceProps["pendingAction"]
  onCreate: () => void
  unknownIntegrity: boolean
}) {
  const projectedKeys = data.figurePlan
    ? Object.keys(data.figurePlan.parameters).filter((key) => key !== "kind")
    : ["x_column_id", "y_column_id"]
  const requiredKeys = chartParameterKeys[draft.chartType]
  const missingProjection = requiredKeys.filter(
    (key) => !projectedKeys.includes(key),
  )
  const canExpressType = missingProjection.length === 0
  const datasetMismatch =
    !data.dataset || draft.datasetVersionId !== data.dataset.versionId
  const runMismatch = Boolean(
    draft.analysisRunId && (!data.run || draft.analysisRunId !== data.run.id),
  )
  const resultMismatch = Boolean(
    draft.analysisResultId &&
      !data.results.some((result) => result.id === draft.analysisResultId),
  )
  const integrityReason = datasetMismatch
    ? "FigurePlan 绑定的数据版本与当前正式 DatasetVersion 不一致。"
    : runMismatch
      ? "FigurePlan 绑定的 AnalysisRun 与当前运行不一致。"
      : resultMismatch
        ? "FigurePlan 绑定的 AnalysisResult 不在当前正式结果中。"
        : unknownIntegrity
          ? "存在未知规范问题，不能创建正式 FigurePlan。"
          : !canExpressType
            ? `当前正式参数投影缺少 ${missingProjection.join("、")}，不能保存该类型。`
            : !draft.caption.trim()
              ? "请填写 caption。"
              : null

  const updateParameter = (key: string, value: ResultValue) =>
    setDraft({
      ...draft,
      parameters: { ...draft.parameters, [key]: value },
    })

  return (
    <section className="m5-figure-panel" data-od-id="figure-plan-editor">
      <div className="m5-figure-panel__header">
        <div>
          <span className="m5-eyebrow">FigurePlan</span>
          <h3>受控图表计划</h3>
        </div>
        <StatusBadge
          label={
            data.figurePlan
              ? statusLabel(data.figurePlan.status, data.figurePlan.knownStatus)
              : "本地草稿"
          }
          tone={data.figurePlan?.tone ?? "neutral"}
        />
      </div>
      <div className="m5-figure-binding">
        <MetadataList
          items={[
            {
              label: "DatasetVersion",
              value: data.dataset
                ? `v${data.dataset.versionNumber} · ${shortHash(data.dataset.versionId)}`
                : "未提供",
              mono: true,
            },
            {
              label: "AnalysisRun",
              value: data.run ? shortHash(data.run.id) : "未绑定",
              mono: true,
            },
            {
              label: "AnalysisResult",
              value: data.results[0] ? shortHash(data.results[0].id) : "未绑定",
              mono: true,
            },
          ]}
        />
      </div>
      <form
        className="m5-figure-form"
        onSubmit={(event) => event.preventDefault()}
      >
        <label>
          <span>图表类型</span>
          <select
            value={draft.chartType}
            onChange={(event) =>
              setDraft({
                ...draft,
                chartType: event.target.value as FigureChartType,
              })
            }
          >
            {chartTypes.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
        </label>
        {projectedKeys.map((key) => {
          const isColumn = key.endsWith("column_id")
          const isColumns = key === "column_ids"
          const value = draft.parameters[key]
          if (isColumn)
            return (
              <label key={key}>
                <span>{key}</span>
                <select
                  value={typeof value === "string" ? value : ""}
                  onChange={(event) => updateParameter(key, event.target.value)}
                >
                  <option value="">未选择</option>
                  {data.columns.map((column) => (
                    <option key={column.id} value={column.id}>
                      {column.name}
                    </option>
                  ))}
                </select>
              </label>
            )
          if (isColumns)
            return (
              <div key={key} className="m5-figure-readonly-field">
                <span>{key}</span>
                <code>{parameterValue(value)}</code>
              </div>
            )
          return (
            <label key={key}>
              <span>{key}</span>
              <input
                value={
                  parameterValue(value) === "未投影"
                    ? ""
                    : parameterValue(value)
                }
                type={key === "dpi" || key === "bins" ? "number" : "text"}
                onChange={(event) =>
                  updateParameter(
                    key,
                    key === "dpi" || key === "bins"
                      ? Number(event.target.value)
                      : event.target.value,
                  )
                }
              />
            </label>
          )
        })}
        <label className="m5-field-wide">
          <span>Caption</span>
          <textarea
            value={draft.caption}
            onChange={(event) =>
              setDraft({ ...draft, caption: event.target.value })
            }
          />
        </label>
      </form>
      {data.figurePlan ? (
        <p className="m5-figure-local-note">
          当前编辑仅为本地参数草稿，不覆盖已有 FigurePlan 或
          Figure；提交会创建新的正式计划意图。
        </p>
      ) : null}
      <div className="m5-plan-actions">
        <FigureAction
          capability={data.capabilities.createFigurePlan}
          pending={pendingAction === "create-figure-plan"}
          transportAvailable={data.figurePlan?.transportAvailable ?? true}
          permissionsKnown={data.capabilities.permissionsKnown}
          extraReason={integrityReason}
          onClick={onCreate}
          variant="default"
          icon={<Save aria-hidden="true" />}
        >
          {data.figurePlan ? "另存为新计划" : "创建 FigurePlan"}
        </FigureAction>
      </div>
    </section>
  )
}

function FigureImageSurface({ data }: { data: AnalysisWorkspaceViewModel }) {
  const figure = data.figure
  const renderRun = data.renderRun
  const isRendering =
    renderRun && ["QUEUED", "RUNNING"].includes(renderRun.status)
  const renderFailed = renderRun?.status === "FAILED"
  return (
    <section className="m5-figure-image-panel" data-od-id="figure-main-surface">
      <div className="m5-figure-panel__header">
        <div>
          <span className="m5-eyebrow">Figure 产物预览</span>
          <h3>
            {figure?.caption ?? data.figurePlan?.caption ?? "尚无正式 Figure"}
          </h3>
        </div>
        <StatusBadge
          label={
            figure
              ? statusLabel(figure.status, figure.knownStatus)
              : renderRun
                ? statusLabel(renderRun.status, renderRun.knownStatus)
                : "未生成"
          }
          tone={figure?.tone ?? renderRun?.tone ?? "neutral"}
        />
      </div>
      <div
        className="m5-figure-image-stage"
        data-state={
          renderFailed
            ? "failed"
            : isRendering
              ? "loading"
              : figure
                ? "metadata"
                : "empty"
        }
      >
        {isRendering ? (
          <>
            <LoaderCircle className="m5-figure-spinner" aria-hidden="true" />
            <strong>正式 Figure 正在渲染</strong>
            <span>渲染完成与 Figure 创建是两个独立状态。</span>
          </>
        ) : renderFailed ? (
          <>
            <XCircle aria-hidden="true" />
            <strong>Figure 渲染失败</strong>
            <span>{renderRun.errorCode ?? "服务端未提供 error code"}</span>
          </>
        ) : figure ? (
          <>
            <ImageOff aria-hidden="true" />
            <strong>图像预览待正式 Artifact</strong>
            <span>
              当前服务端仅提供 Artifact metadata，不在浏览器伪造科研图表。
            </span>
          </>
        ) : (
          <>
            <FileBarChart aria-hidden="true" />
            <strong>尚无正式 Figure</strong>
            <span>本地草稿和操作意图均不代表 Figure 已生成。</span>
          </>
        )}
      </div>
      <p className="m5-figure-authority-note">
        Figure image 是产物预览；结构化 AnalysisResult
        仍是数字权威，浏览器不会重算回归线、置信区间、误差线或相关矩阵。
      </p>
      <MetadataList
        items={[
          {
            label: "图表类型",
            value: chartLabel(
              figure?.chartType ?? data.figurePlan?.chartType ?? null,
            ),
          },
          {
            label: "DatasetVersion",
            value: shortHash(
              figure?.datasetVersionId ??
                data.figurePlan?.datasetVersionId ??
                null,
            ),
            mono: true,
          },
          {
            label: "AnalysisRun",
            value: shortHash(
              figure?.analysisRunId ?? data.figurePlan?.analysisRunId ?? null,
            ),
            mono: true,
          },
          {
            label: "aggregate hash",
            value: shortHash(figure?.aggregateHash ?? null),
            mono: true,
          },
          {
            label: "RenderRun",
            value: shortHash(renderRun?.id ?? null),
            mono: true,
          },
          {
            label: "确认状态",
            value: figure?.confirmationApprovalId
              ? figure.approvalStale
                ? "确认已陈旧"
                : statusLabel(figure.status, figure.knownStatus)
              : "未确认",
          },
        ]}
      />
    </section>
  )
}

function RenderSurface({
  data,
  pendingAction,
  unknownIntegrity,
  onRender,
  onRetry,
  onCancel,
}: {
  data: AnalysisWorkspaceViewModel
  pendingAction: AnalysisWorkspaceWorkspaceProps["pendingAction"]
  unknownIntegrity: boolean
  onRender: () => void
  onRetry: () => void
  onCancel: () => void
}) {
  const run = data.renderRun
  const transportAvailable =
    run?.transportAvailable ?? data.figurePlan?.transportAvailable ?? true
  const permissionsKnown =
    run?.permissionsKnown ??
    data.figurePlan?.permissionsKnown ??
    data.capabilities.permissionsKnown
  const completedWithoutFigure = run?.status === "COMPLETED" && !data.figure
  const runMismatch = Boolean(
    data.figurePlan &&
      data.run &&
      data.figurePlan.analysisRunId &&
      data.figurePlan.analysisRunId !== data.run.id,
  )
  return (
    <section className="m5-figure-panel" data-od-id="figure-render-run">
      <div className="m5-figure-panel__header">
        <div>
          <span className="m5-eyebrow">FigureRenderRun</span>
          <h3>渲染与 Job</h3>
        </div>
        {run ? (
          <StatusBadge
            label={statusLabel(run.status, run.knownStatus)}
            tone={run.tone}
          />
        ) : null}
      </div>
      {run && ["QUEUED", "RUNNING"].includes(run.status) ? (
        <JobProgress
          label={`Render #${run.renderNumber}`}
          statusLabel={statusLabel(run.status, run.knownStatus)}
          tone={run.tone}
          progress={null}
          step="等待正式 Figure render progress"
        />
      ) : null}
      {run?.status === "FAILED" ? (
        <div className="m5-figure-failure">
          <XCircle aria-hidden="true" />
          <div>
            <strong>{run.errorCode ?? "FIGURE_RENDER_FAILED"}</strong>
            <span>
              {run.retryable ? "服务端标记为可重试" : "服务端标记为不可重试"}
            </span>
          </div>
        </div>
      ) : null}
      {completedWithoutFigure ? (
        <PermissionNotice
          title="RenderRun 已完成，但 Figure 尚不存在"
          reason="界面不会把渲染完成误报为 Figure 成功。"
        />
      ) : null}
      <MetadataList
        items={[
          { label: "render number", value: run?.renderNumber ?? "未运行" },
          {
            label: "input hash",
            value: shortHash(run?.inputHash ?? null),
            mono: true,
          },
          {
            label: "parameters hash",
            value: shortHash(run?.parametersHash ?? null),
            mono: true,
          },
          {
            label: "environment hash",
            value: shortHash(run?.environmentHash ?? null),
            mono: true,
          },
        ]}
      />
      <div className="m5-plan-actions">
        <FigureAction
          capability={data.capabilities.renderFigure}
          pending={pendingAction === "render-figure"}
          transportAvailable={transportAvailable}
          permissionsKnown={permissionsKnown}
          extraReason={
            !data.figurePlan
              ? "尚无正式 FigurePlan。"
              : runMismatch
                ? "FigurePlan 与当前 AnalysisRun 不一致。"
                : unknownIntegrity
                  ? "存在未知规范问题，渲染操作保持禁用。"
                  : null
          }
          onClick={onRender}
          variant="default"
          icon={<Play aria-hidden="true" />}
        >
          渲染 Figure
        </FigureAction>
        <FigureAction
          capability={data.capabilities.retryJob}
          pending={pendingAction === "retry-job"}
          transportAvailable={transportAvailable}
          permissionsKnown={permissionsKnown}
          extraReason={
            !run?.jobId
              ? "RenderRun 没有可重试的 Job。"
              : !run.retryable
                ? "服务端未标记该 RenderRun 为可重试。"
                : null
          }
          onClick={onRetry}
          icon={<RefreshCw aria-hidden="true" />}
        >
          重试渲染
        </FigureAction>
        <FigureAction
          capability={data.capabilities.cancelJob}
          pending={pendingAction === "cancel-job"}
          transportAvailable={transportAvailable}
          permissionsKnown={permissionsKnown}
          extraReason={
            !run?.jobId || !["QUEUED", "RUNNING"].includes(run.status)
              ? "没有可取消的渲染 Job。"
              : null
          }
          onClick={onCancel}
          icon={<Square aria-hidden="true" />}
        >
          取消渲染
        </FigureAction>
      </div>
    </section>
  )
}

function issueIcon(issue: FigureValidationIssueViewModel) {
  if (issue.severity === "ERROR") return <CircleAlert aria-hidden="true" />
  if (issue.severity === "WARNING") return <AlertTriangle aria-hidden="true" />
  return <Info aria-hidden="true" />
}

function ValidationSurface({ data }: { data: AnalysisWorkspaceViewModel }) {
  const issues = data.figure?.issues ?? []
  return (
    <section className="m5-figure-panel" data-od-id="figure-validation-issues">
      <div className="m5-figure-panel__header">
        <div>
          <span className="m5-eyebrow">FigureValidationIssue</span>
          <h3>规范检查</h3>
        </div>
        <StatusBadge
          label={`${issues.length} 项`}
          tone={
            issues.some((item) => item.blocksConfirmation)
              ? "danger"
              : issues.length
                ? "warning"
                : "success"
          }
        />
      </div>
      {issues.length ? (
        <ul className="m5-figure-issue-list">
          {issues.map((issue) => {
            const known =
              issue.knownStatus && knownIssueTypes.has(issue.issueType)
            const integrity = ["VERSION_MISMATCH", "RESULT_MISMATCH"].includes(
              issue.issueType,
            )
            return (
              <li
                key={issue.id}
                data-severity={integrity ? "ERROR" : issue.severity}
                data-blocking={issue.blocksConfirmation || integrity}
              >
                {integrity ? (
                  <ShieldAlert aria-hidden="true" />
                ) : (
                  issueIcon(issue)
                )}
                <div>
                  <div>
                    <strong>
                      {known
                        ? issue.issueType
                        : `未知类型 · ${issue.issueType}`}
                    </strong>
                    <StatusBadge
                      label={integrity ? "科研完整性" : issue.severity}
                      tone={
                        integrity || issue.severity === "ERROR"
                          ? "danger"
                          : issue.severity === "WARNING"
                            ? "warning"
                            : "info"
                      }
                    />
                  </div>
                  <p>{issue.message}</p>
                  {issue.blocksConfirmation || integrity ? (
                    <span>持续阻止 Figure 确认</span>
                  ) : null}
                </div>
              </li>
            )
          })}
        </ul>
      ) : (
        <div className="m5-figure-empty-line">
          <CheckCircle2 aria-hidden="true" />
          <span>服务端未返回 FigureValidationIssue。</span>
        </div>
      )}
      <p className="m5-figure-local-note">
        Validation issue 是服务端事实；界面不提供关闭或本地 resolved 操作。
      </p>
    </section>
  )
}

function ConfirmationSurface({
  data,
  pendingAction,
  unknownIntegrity,
  onRequest,
  onDecision,
}: {
  data: AnalysisWorkspaceViewModel
  pendingAction: AnalysisWorkspaceWorkspaceProps["pendingAction"]
  unknownIntegrity: boolean
  onRequest: () => void
  onDecision: (decision: "APPROVE" | "REJECT") => void
}) {
  const figure = data.figure
  const blocking =
    figure?.issues.filter((item) => item.blocksConfirmation) ?? []
  const invalidated =
    figure?.status === "INVALIDATED" || Boolean(figure?.invalidationReason)
  const stale = figure?.approvalStale ?? false
  const noLifecycle =
    Boolean(figure?.confirmationApprovalId) &&
    !data.capabilities.decideFigureConfirmation.allowed
  const extraReason = !figure
    ? "尚无正式 Figure。"
    : !figure.knownStatus || unknownIntegrity
      ? "Figure 状态或规范问题未知，确认操作保持禁用。"
      : invalidated
        ? "Figure 已失效，不能确认。"
        : stale
          ? "Figure confirmation 已陈旧，不能继续决策。"
          : blocking.length
            ? `仍有 ${blocking.length} 个问题阻止确认。`
            : null
  return (
    <section className="m5-figure-panel" data-od-id="figure-confirmation">
      <div className="m5-figure-panel__header">
        <div>
          <span className="m5-eyebrow">Figure 确认</span>
          <h3>图表确认</h3>
        </div>
        <StatusBadge
          label={
            invalidated
              ? "Figure 已失效"
              : stale
                ? "确认已陈旧"
                : figure?.confirmationApprovalId
                  ? statusLabel(figure.status, figure.knownStatus)
                  : "未请求确认"
          }
          tone={
            invalidated || stale
              ? "danger"
              : figure?.confirmationApprovalId
                ? "approval"
                : "neutral"
          }
        />
      </div>
      <p className="m5-figure-confirmation-copy">
        该确认仅针对 Figure 产物及其规范状态，不替代 AnalysisPlan
        Approval，也不保证上游 AnalysisRun 永久有效。
      </p>
      {invalidated ? (
        <div className="m5-figure-integrity-alert">
          <Ban aria-hidden="true" />
          <div>
            <strong>上游失效关系已保留</strong>
            <span>
              {figure?.invalidationReason ?? "Figure 已被服务端标记为失效。"}
            </span>
          </div>
        </div>
      ) : null}
      {blocking.map((issue) => (
        <div className="m5-figure-blocker" key={issue.id}>
          <ShieldAlert aria-hidden="true" />
          <span>
            {issue.issueType} · {issue.message}
          </span>
        </div>
      ))}
      {noLifecycle ? (
        <PermissionNotice
          title="确认 decision lifecycle 未投影"
          reason="当前正式投影只有 confirmationApprovalId，没有可执行的 pending Approval decision；Approve/Reject 保持禁用。"
        />
      ) : null}
      <div className="m5-plan-actions">
        <FigureAction
          capability={data.capabilities.requestFigureConfirmation}
          pending={pendingAction === "request-figure-confirmation"}
          transportAvailable={figure?.transportAvailable ?? true}
          permissionsKnown={
            figure?.permissionsKnown ?? data.capabilities.permissionsKnown
          }
          extraReason={extraReason}
          onClick={onRequest}
          icon={<ShieldCheck aria-hidden="true" />}
        >
          请求 Figure 确认
        </FigureAction>
        <FigureAction
          capability={data.capabilities.decideFigureConfirmation}
          pending={pendingAction === "decide-figure-confirmation"}
          transportAvailable={figure?.transportAvailable ?? true}
          permissionsKnown={
            figure?.permissionsKnown ?? data.capabilities.permissionsKnown
          }
          extraReason={
            extraReason ??
            (!figure?.confirmationApprovalId
              ? "缺少正式 Figure Approval。"
              : null)
          }
          onClick={() => onDecision("APPROVE")}
          variant="default"
          icon={<CheckCircle2 aria-hidden="true" />}
        >
          确认 Figure
        </FigureAction>
        <FigureAction
          capability={data.capabilities.decideFigureConfirmation}
          pending={pendingAction === "decide-figure-confirmation"}
          transportAvailable={figure?.transportAvailable ?? true}
          permissionsKnown={
            figure?.permissionsKnown ?? data.capabilities.permissionsKnown
          }
          extraReason={
            extraReason ??
            (!figure?.confirmationApprovalId
              ? "缺少正式 Figure Approval。"
              : null)
          }
          onClick={() => onDecision("REJECT")}
          variant="destructive"
          icon={<XCircle aria-hidden="true" />}
        >
          拒绝 Figure
        </FigureAction>
      </div>
    </section>
  )
}

function artifactIcon(artifact: ArtifactReferenceViewModel) {
  if (artifact.kind === "PNG" || artifact.kind === "SVG")
    return <FileImage aria-hidden="true" />
  if (artifact.kind === "CODE") return <FileCode2 aria-hidden="true" />
  return <FileText aria-hidden="true" />
}

function ArtifactSurface({
  data,
  pendingAction,
  unknownIntegrity,
  onDownload,
}: {
  data: AnalysisWorkspaceViewModel
  pendingAction: AnalysisWorkspaceWorkspaceProps["pendingAction"]
  unknownIntegrity: boolean
  onDownload: (artifact: ArtifactReferenceViewModel) => void
}) {
  const figure = data.figure
  const artifacts =
    figure?.artifacts.filter((item) =>
      ["PNG", "SVG", "PDF", "CODE"].includes(item.kind),
    ) ?? []
  const canCopyHash = data.readScopes.includes("artifact")
  return (
    <section className="m5-figure-panel" data-od-id="figure-artifacts">
      <div className="m5-figure-panel__header">
        <div>
          <span className="m5-eyebrow">Artifact 来源</span>
          <h3>正式产物</h3>
        </div>
        <StatusBadge
          label={`${artifacts.length} 项`}
          tone={artifacts.length ? "info" : "neutral"}
        />
      </div>
      {artifacts.length ? (
        <ul className="m5-artifact-list">
          {artifacts.map((artifact) => {
            const extraReason = unknownIntegrity
              ? "存在未知规范问题，下载操作保持禁用。"
              : artifact.masked
                ? "该 Artifact 已遮蔽。"
                : !artifact.downloadable
                  ? "服务端未标记该 Artifact 为可下载。"
                  : !["PNG", "SVG", "PDF", "CODE"].includes(artifact.kind)
                    ? "该 Artifact 类型没有下载 Event contract。"
                    : null
            return (
              <li key={artifact.id} data-masked={artifact.masked}>
                <span className="m5-artifact-icon">
                  {artifactIcon(artifact)}
                </span>
                <div>
                  <div>
                    <strong>{artifact.label}</strong>
                    <StatusBadge
                      label={
                        artifact.masked
                          ? "已遮蔽"
                          : statusLabel(artifact.status, artifact.knownStatus)
                      }
                      tone={artifact.masked ? "degraded" : artifact.tone}
                    />
                  </div>
                  <span>{artifact.kind}</span>
                  <code
                    title={
                      canCopyHash ? (artifact.sha256 ?? undefined) : undefined
                    }
                  >
                    {canCopyHash
                      ? shortHash(artifact.sha256)
                      : "hash 受 read scope 限制"}
                  </code>
                </div>
                <FigureAction
                  capability={data.capabilities.downloadArtifact}
                  pending={pendingAction === "download-artifact"}
                  transportAvailable={figure?.transportAvailable ?? true}
                  permissionsKnown={
                    figure?.permissionsKnown ??
                    data.capabilities.permissionsKnown
                  }
                  extraReason={extraReason}
                  onClick={() => onDownload(artifact)}
                  icon={<Download aria-hidden="true" />}
                  iconOnly
                  label={`下载 ${artifact.label}`}
                />
              </li>
            )
          })}
        </ul>
      ) : (
        <div className="m5-figure-empty-line">
          <FileText aria-hidden="true" />
          <span>尚无 PNG、SVG、PDF 或 CODE Artifact metadata。</span>
        </div>
      )}
      <p className="m5-figure-local-note">
        下载只发出正式 Event；浏览器不会生成图像、PDF、SVG 或代码替代 Artifact。
      </p>
    </section>
  )
}

export function FigureWorkspace({
  data,
  pendingAction,
  onEvent,
}: {
  data: AnalysisWorkspaceViewModel
  pendingAction: AnalysisWorkspaceWorkspaceProps["pendingAction"]
  onEvent: (event: AnalysisWorkspaceEvent) => void
}) {
  const [mode, setMode] = useState<FigureMode>("chart")
  const [inspectorOpen, setInspectorOpen] = useState(false)
  const [cancelOpen, setCancelOpen] = useState(false)
  const [decision, setDecision] = useState<"APPROVE" | "REJECT" | null>(null)
  const [reason, setReason] = useState("")
  const [draft, setDraft] = useState<FigurePlanInput>(() => draftFromData(data))
  const returnFocusRef = useRef<HTMLElement | null>(null)

  useEffect(
    () => setDraft(draftFromData(data)),
    [data.figurePlan?.id, data.dataset?.versionId],
  )

  const unknownIntegrity = useMemo(
    () =>
      Boolean(
        (data.figure && !data.figure.knownStatus) ||
          (data.renderRun && !data.renderRun.knownStatus) ||
          data.figure?.issues.some(
            (issue) =>
              !issue.knownStatus || !knownIssueTypes.has(issue.issueType),
          ),
      ),
    [data.figure, data.renderRun],
  )
  const rememberTrigger = () => {
    returnFocusRef.current = document.activeElement as HTMLElement | null
  }
  const restoreTriggerFocus = (event: Event) => {
    event.preventDefault()
    returnFocusRef.current?.focus()
  }

  const renderSurface = (
    <RenderSurface
      data={data}
      pendingAction={pendingAction}
      unknownIntegrity={unknownIntegrity}
      onRender={() =>
        data.figurePlan &&
        onEvent({
          action: "render-figure",
          input: { figurePlanId: data.figurePlan.id, reason: null },
        })
      }
      onRetry={() =>
        data.renderRun?.jobId &&
        onEvent({ action: "retry-job", input: { jobId: data.renderRun.jobId } })
      }
      onCancel={() => {
        rememberTrigger()
        setReason("")
        setCancelOpen(true)
      }}
    />
  )
  const validationSurface = <ValidationSurface data={data} />
  const artifactSurface = (
    <ArtifactSurface
      data={data}
      pendingAction={pendingAction}
      unknownIntegrity={unknownIntegrity}
      onDownload={(artifact) => {
        if (
          data.figure &&
          ["PNG", "SVG", "PDF", "CODE"].includes(artifact.kind)
        )
          onEvent({
            action: "download-artifact",
            input: {
              figureId: data.figure.id,
              format: artifact.kind as "PNG" | "SVG" | "PDF" | "CODE",
            },
          })
      }}
    />
  )

  return (
    <div
      className="m5-view-stack m5-figure-workspace"
      data-od-id="analysis-figures-workspace"
    >
      <section className="m5-surface-heading">
        <div>
          <span className="m5-eyebrow">受控 Figure 工作流</span>
          <h2>图表计划、渲染与确认</h2>
          <p>
            只显示服务端事实和本地草稿边界；占位图、RenderRun
            完成或操作意图都不等于正式 Figure。
          </p>
        </div>
        <Button
          type="button"
          size="icon-sm"
          variant="outline"
          className="m5-figure-tablet-inspector"
          aria-label="打开图表问题与产物 Inspector"
          title="打开图表问题与产物 Inspector"
          onClick={() => {
            rememberTrigger()
            setInspectorOpen(true)
          }}
        >
          <PanelRight aria-hidden="true" />
        </Button>
      </section>

      {unknownIntegrity ? (
        <PermissionNotice
          title="Figure 状态或规范问题未知"
          reason="原始类型仍可查看，render、confirmation 与 download 正式操作保持 fail-closed。"
        />
      ) : null}
      {data.suggestions
        .filter((item) => item.kind === "FIGURE")
        .map((suggestion, index) => (
          <DegradedNotice
            key={`${suggestion.kind}-${index}`}
            title="AI Figure suggestion 不可用"
            message={suggestion.reason}
          />
        ))}

      <div
        className="m5-figure-mobile-modes"
        role="tablist"
        aria-label="图表工作流模式"
      >
        {(
          [
            ["plan", "计划"],
            ["chart", "图表"],
            ["issues", "问题"],
            ["artifacts", "产物"],
          ] as const
        ).map(([value, label]) => (
          <button
            key={value}
            type="button"
            role="tab"
            aria-selected={mode === value}
            onClick={() => setMode(value)}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="m5-figure-layout">
        <div className="m5-figure-primary">
          <div
            className="m5-figure-mode-surface"
            data-mode="plan"
            data-active={mode === "plan"}
          >
            <FigurePlanEditor
              data={data}
              draft={draft}
              setDraft={setDraft}
              pendingAction={pendingAction}
              unknownIntegrity={unknownIntegrity}
              onCreate={() =>
                onEvent({ action: "create-figure-plan", input: draft })
              }
            />
          </div>
          <div
            className="m5-figure-mode-surface"
            data-mode="chart"
            data-active={mode === "chart"}
          >
            <FigureImageSurface data={data} />
            {renderSurface}
            <ConfirmationSurface
              data={data}
              pendingAction={pendingAction}
              unknownIntegrity={unknownIntegrity}
              onRequest={() =>
                data.figure &&
                onEvent({
                  action: "request-figure-confirmation",
                  input: { figureId: data.figure.id },
                })
              }
              onDecision={(value) => {
                rememberTrigger()
                setReason("")
                setDecision(value)
              }}
            />
          </div>
        </div>
        <aside className="m5-figure-side">
          <div
            className="m5-figure-mode-surface"
            data-mode="issues"
            data-active={mode === "issues"}
          >
            {validationSurface}
          </div>
          <div
            className="m5-figure-mode-surface"
            data-mode="artifacts"
            data-active={mode === "artifacts"}
          >
            {artifactSurface}
          </div>
        </aside>
      </div>

      <Sheet open={inspectorOpen} onOpenChange={setInspectorOpen}>
        <SheetContent
          side="right"
          className="m5-sheet-content m5-figure-sheet"
          onCloseAutoFocus={restoreTriggerFocus}
        >
          <SheetHeader>
            <SheetTitle>Figure Inspector</SheetTitle>
            <SheetDescription>
              规范问题和正式 Artifact metadata 保持只读。
            </SheetDescription>
          </SheetHeader>
          <div className="m5-figure-sheet__body">
            {validationSurface}
            {artifactSurface}
          </div>
        </SheetContent>
      </Sheet>

      <Dialog open={cancelOpen} onOpenChange={setCancelOpen}>
        <DialogContent
          className="m5-dialog"
          data-od-id="cancel-figure-render-dialog"
          onCloseAutoFocus={restoreTriggerFocus}
        >
          <DialogHeader>
            <DialogTitle>取消 Figure 渲染</DialogTitle>
            <DialogDescription>
              只发送 cancel-job 意图；RenderRun 和 Figure 状态不会在本地改变。
            </DialogDescription>
          </DialogHeader>
          <label className="m5-dialog-field">
            <span>取消原因</span>
            <textarea
              autoFocus
              required
              value={reason}
              onChange={(event) => setReason(event.target.value)}
            />
          </label>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setCancelOpen(false)}
            >
              返回
            </Button>
            <Button
              type="button"
              disabled={!reason.trim() || pendingAction === "cancel-job"}
              onClick={() => {
                if (data.renderRun?.jobId && reason.trim()) {
                  onEvent({
                    action: "cancel-job",
                    input: {
                      jobId: data.renderRun.jobId,
                      reason: reason.trim(),
                    },
                  })
                  setCancelOpen(false)
                }
              }}
            >
              发送取消意图
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog
        open={decision !== null}
        onOpenChange={(open) => !open && setDecision(null)}
      >
        <DialogContent
          className="m5-dialog"
          data-od-id="figure-confirmation-decision-dialog"
          onCloseAutoFocus={restoreTriggerFocus}
        >
          <DialogHeader>
            <DialogTitle>
              {decision === "REJECT" ? "拒绝 Figure" : "确认 Figure"}
            </DialogTitle>
            <DialogDescription>
              该操作只发送 Figure confirmation decision
              Event，不会在本地改变正式状态。
            </DialogDescription>
          </DialogHeader>
          <label className="m5-dialog-field">
            <span>
              {decision === "REJECT" ? "拒绝原因（必填）" : "确认说明（可选）"}
            </span>
            <textarea
              autoFocus
              required={decision === "REJECT"}
              value={reason}
              onChange={(event) => setReason(event.target.value)}
            />
          </label>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setDecision(null)}
            >
              返回
            </Button>
            <Button
              type="button"
              variant={decision === "REJECT" ? "destructive" : "default"}
              disabled={
                !data.figure?.confirmationApprovalId ||
                (decision === "REJECT" && !reason.trim()) ||
                pendingAction === "decide-figure-confirmation"
              }
              onClick={() => {
                if (decision && data.figure?.confirmationApprovalId) {
                  onEvent({
                    action: "decide-figure-confirmation",
                    input: {
                      approvalId: data.figure.confirmationApprovalId,
                      decision,
                      reason: reason.trim() || null,
                    },
                  })
                  setDecision(null)
                }
              }}
            >
              发送决策意图
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
