import {
  AlertTriangle,
  Check,
  ChevronRight,
  CircleAlert,
  CircleCheck,
  Clock3,
  FileCheck2,
  GitCompareArrows,
  History,
  Info,
  ListFilter,
  LockKeyhole,
  Pencil,
  Play,
  Plus,
  RefreshCw,
  RotateCcw,
  ShieldAlert,
  ShieldCheck,
  Trash2,
  TriangleAlert,
  XCircle,
} from "lucide-react"
import type { FormEvent, ReactNode } from "react"
import { useEffect, useMemo, useState } from "react"

import { StatusBadge } from "@/components/reca-visual-refresh"
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

import type {
  ActionCapability,
  CleaningActionInput,
  DataWorkspaceViewModel,
  QualityIssueViewModel,
} from "../model"
import type { DataWorkspaceWorkspaceProps } from "./contracts"
import "./data-workspace-operations.css"

type OperationView = "quality" | "cleaning" | "versions"

function formatNumber(value: number | null) {
  return value === null ? "未知" : new Intl.NumberFormat("zh-CN").format(value)
}

function formatDate(value: string | null) {
  if (!value) return "未提供"
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

function effectiveCapability(
  capability: ActionCapability,
  guards: readonly { allowed: boolean; reason: string }[],
): ActionCapability {
  const failed = guards.find((guard) => !guard.allowed)
  if (failed) return { allowed: false, disabledReason: failed.reason }
  return capability
}

function OperationButton({
  capability,
  label,
  pending,
  icon,
  primary = false,
  onClick,
}: {
  capability: ActionCapability
  label: string
  pending: boolean
  icon: ReactNode
  primary?: boolean
  onClick: () => void
}) {
  return (
    <Button
      type="button"
      size="sm"
      variant={primary ? "default" : "outline"}
      disabled={!capability.allowed || pending}
      title={capability.disabledReason ?? label}
      aria-label={
        capability.allowed
          ? label
          : `${label}：${capability.disabledReason ?? "当前不可用"}`
      }
      onClick={onClick}
    >
      {pending ? <RefreshCw className="m4-spin" aria-hidden="true" /> : icon}
      {pending ? "处理中" : label}
    </Button>
  )
}

function QualitySummary({
  data,
  props,
}: {
  data: DataWorkspaceViewModel
  props: DataWorkspaceWorkspaceProps
}) {
  const run = data.qualityRun
  const runCapability = effectiveCapability(data.capabilities.runQuality, [
    {
      allowed: data.capabilities.permissionsKnown,
      reason: "权限状态未知，不能运行质量检查。",
    },
    {
      allowed: Boolean(data.version?.knownStatus && !data.version.invalidated),
      reason: "当前版本状态未知或已失效，不能作为质量检查输入。",
    },
    {
      allowed: !run || (run.knownStatus && !run.degraded),
      reason: "当前 Quality Run 状态未知或降级，不能启动新的运行。",
    },
  ])
  return (
    <section className="m4-quality-summary" data-od-id="quality-summary">
      <div className="m4-ops-heading">
        <div>
          <ShieldCheck aria-hidden="true" />
          <div>
            <h2>质量检查</h2>
            <p>确定性错误与复核线索分层显示，不由可见行推导正式结论。</p>
          </div>
        </div>
        <OperationButton
          capability={runCapability}
          label="运行质量检查"
          pending={props.pendingAction === "run-quality"}
          icon={<Play aria-hidden="true" />}
          primary
          onClick={() =>
            data.version &&
            props.onEvent({
              action: "run-quality",
              input: { versionId: data.version.id },
            })
          }
        />
      </div>
      <dl className="m4-quality-facts">
        <div>
          <dt>Run 状态</dt>
          <dd>
            {run ? (
              <StatusBadge label={run.status} tone={run.tone} />
            ) : (
              "尚未运行"
            )}
          </dd>
        </div>
        <div>
          <dt>Ruleset</dt>
          <dd title={run?.rulesetHash}>
            {run ? `${run.rulesetId} · ${run.rulesetVersion}` : "未提供"}
          </dd>
        </div>
        <div>
          <dt>Issue</dt>
          <dd>{formatNumber(run?.issueCount ?? data.issues.length)}</dd>
        </div>
        <div>
          <dt>高风险</dt>
          <dd>{formatNumber(run?.highIssueCount ?? 0)}</dd>
        </div>
        <div>
          <dt>Run Job</dt>
          <dd title={run?.jobId ?? ""}>{run?.jobId ?? "未提供"}</dd>
        </div>
      </dl>
      {run && (!run.knownStatus || run.degraded || run.errorCode) ? (
        <p
          className="m4-ops-notice"
          data-tone={run.errorCode ? "danger" : "degraded"}
        >
          <TriangleAlert aria-hidden="true" />
          <span>
            {run.errorCode
              ? `质量检查错误：${run.errorCode}`
              : `未知或降级状态：${run.status}`}
            。写操作保持关闭。
          </span>
        </p>
      ) : null}
    </section>
  )
}

export function QualityView({
  data,
  props,
  selectedIssueId,
  onSelectIssue,
}: {
  data: DataWorkspaceViewModel
  props: DataWorkspaceWorkspaceProps
  selectedIssueId: string | null
  onSelectIssue: (issue: QualityIssueViewModel) => void
}) {
  const [severity, setSeverity] = useState("ALL")
  const [issueType, setIssueType] = useState("ALL")
  const [status, setStatus] = useState("ALL")
  const [column, setColumn] = useState("ALL")
  const [mode, setMode] = useState("ALL")
  const values = (key: "severity" | "issueType" | "status") =>
    Array.from(new Set(data.issues.map((issue) => issue[key]))).sort()
  const columnValues = Array.from(
    new Set(data.issues.map((issue) => issue.columnId).filter(Boolean)),
  ) as string[]
  const filtered = useMemo(
    () =>
      data.issues.filter((issue) => {
        if (severity !== "ALL" && issue.severity !== severity) return false
        if (issueType !== "ALL" && issue.issueType !== issueType) return false
        if (status !== "ALL" && issue.status !== status) return false
        if (column !== "ALL" && issue.columnId !== column) return false
        if (mode === "CLUE" && !issue.clueOnly) return false
        if (
          mode === "SENSITIVE" &&
          !issue.sensitiveCandidate &&
          !issue.sensitiveConfirmed
        )
          return false
        if (mode === "DETERMINISTIC" && issue.clueOnly) return false
        return true
      }),
    [data.issues, severity, issueType, status, column, mode],
  )
  const columnName = (columnId: string | null) => {
    if (!columnId) return "全数据集"
    const item = data.columns.find((candidate) => candidate.id === columnId)
    return item?.displayName ?? item?.sourceName ?? columnId
  }
  return (
    <div className="m4-quality-view">
      <QualitySummary data={data} props={props} />
      <section className="m4-quality-filters" aria-label="质量 Issue 本地筛选">
        <div className="m4-filter-label">
          <ListFilter aria-hidden="true" />
          <span>本地筛选</span>
        </div>
        <label>
          严重度
          <select
            value={severity}
            onChange={(event) => setSeverity(event.target.value)}
          >
            <option value="ALL">全部</option>
            {values("severity").map((value) => (
              <option key={value}>{value}</option>
            ))}
          </select>
        </label>
        <label>
          类型
          <select
            value={issueType}
            onChange={(event) => setIssueType(event.target.value)}
          >
            <option value="ALL">全部</option>
            {values("issueType").map((value) => (
              <option key={value}>{value}</option>
            ))}
          </select>
        </label>
        <label>
          状态
          <select
            value={status}
            onChange={(event) => setStatus(event.target.value)}
          >
            <option value="ALL">全部</option>
            {values("status").map((value) => (
              <option key={value}>{value}</option>
            ))}
          </select>
        </label>
        <label>
          字段
          <select
            value={column}
            onChange={(event) => setColumn(event.target.value)}
          >
            <option value="ALL">全部</option>
            {columnValues.map((value) => (
              <option key={value} value={value}>
                {columnName(value)}
              </option>
            ))}
          </select>
        </label>
        <label>
          语义
          <select
            value={mode}
            onChange={(event) => setMode(event.target.value)}
          >
            <option value="ALL">全部</option>
            <option value="DETERMINISTIC">确定性事实</option>
            <option value="CLUE">线索 / 需复核</option>
            <option value="SENSITIVE">敏感性</option>
          </select>
        </label>
        <span className="m4-filter-count">
          {filtered.length} / {data.issues.length}
        </span>
      </section>
      <section className="m4-quality-table" data-od-id="quality-issue-table">
        <div
          className="m4-ops-table-scroll"
          role="region"
          aria-label="质量 Issue 表"
          tabIndex={0}
        >
          <table>
            <thead>
              <tr>
                <th>规则 / 类型</th>
                <th>严重度</th>
                <th>字段</th>
                <th>影响行</th>
                <th>语义</th>
                <th>状态</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((issue) => {
                const selected =
                  (selectedIssueId ?? data.issues[0]?.id) === issue.id
                return (
                  <tr
                    key={issue.id}
                    data-selected={selected ? "true" : "false"}
                    data-degraded={!issue.knownStatus ? "true" : "false"}
                  >
                    <td>
                      <button
                        type="button"
                        className="m4-issue-name"
                        onClick={() => onSelectIssue(issue)}
                      >
                        <strong>{issue.ruleCode}</strong>
                        <small>{issue.issueType}</small>
                      </button>
                    </td>
                    <td>
                      <StatusBadge
                        label={issue.severity}
                        tone={
                          issue.severity === "HIGH"
                            ? "danger"
                            : issue.severity === "MEDIUM"
                              ? "warning"
                              : "info"
                        }
                      />
                    </td>
                    <td title={columnName(issue.columnId)}>
                      {columnName(issue.columnId)}
                    </td>
                    <td>{formatNumber(issue.affectedRowCount)}</td>
                    <td>
                      <span
                        className="m4-issue-semantic"
                        data-tone={
                          issue.clueOnly
                            ? "clue"
                            : issue.sensitiveCandidate
                              ? "warning"
                              : "fact"
                        }
                      >
                        {issue.clueOnly ? (
                          <Info aria-hidden="true" />
                        ) : issue.sensitiveCandidate ? (
                          <ShieldAlert aria-hidden="true" />
                        ) : (
                          <CircleCheck aria-hidden="true" />
                        )}
                        {issue.clueOnly
                          ? "线索"
                          : issue.sensitiveCandidate
                            ? "需复核"
                            : "检测事实"}
                      </span>
                    </td>
                    <td>
                      {issue.knownStatus ? (
                        issue.status
                      ) : (
                        <span className="m4-degraded-label">
                          <AlertTriangle aria-hidden="true" />
                          {issue.status}
                        </span>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
        {!filtered.length ? (
          <div className="m4-ops-empty">
            <ListFilter aria-hidden="true" />
            <strong>没有匹配的 Issue</strong>
            <p>调整本地筛选不会改变正式 Issue 状态。</p>
          </div>
        ) : null}
      </section>
    </div>
  )
}

function ProcessTrack({ data }: { data: DataWorkspaceViewModel }) {
  const plan = data.plan
  const targetVersion = data.transformation?.targetVersionId
  const steps = [
    { label: "Plan", value: plan?.status ?? "NOT_AVAILABLE" },
    {
      label: "Deterministic Preview",
      value: plan?.preview ? "AVAILABLE" : "NOT_AVAILABLE",
    },
    {
      label: "Formal Approval",
      value: data.approval?.status ?? "NOT_REQUESTED",
    },
    { label: "Job", value: data.job?.status ?? "NOT_ACCEPTED" },
    {
      label: "Transformation",
      value: data.transformation?.status ?? "NOT_AVAILABLE",
    },
    {
      label: "Target Version",
      value:
        targetVersion && data.version?.id === targetVersion
          ? data.version.status
          : (targetVersion ?? "NOT_PROJECTED"),
    },
    {
      label: "Quality recheck",
      value:
        targetVersion && data.qualityRun?.versionId === targetVersion
          ? data.qualityRun.status
          : "NOT_PROJECTED",
    },
  ]
  return (
    <ol className="m4-process-track" aria-label="清洗与转换正式状态轨道">
      {steps.map((step, index) => (
        <li key={step.label}>
          <span className="m4-track-index">{index + 1}</span>
          <div>
            <strong>{step.label}</strong>
            <small title={step.value}>{step.value}</small>
          </div>
          {index < steps.length - 1 ? (
            <ChevronRight aria-hidden="true" />
          ) : null}
        </li>
      ))}
    </ol>
  )
}

function ApprovalPanel({ data }: { data: DataWorkspaceViewModel }) {
  const approval = data.approval
  return (
    <section className="m4-operation-panel" data-od-id="approval-status-panel">
      <div className="m4-panel-heading">
        <div>
          <FileCheck2 aria-hidden="true" />
          <h3>Formal Approval</h3>
        </div>
        {approval ? (
          <StatusBadge label={approval.status} tone={approval.tone} />
        ) : null}
      </div>
      {approval ? (
        <dl className="m4-compact-facts">
          <div>
            <dt>过期时间</dt>
            <dd>{formatDate(approval.expiresAt)}</dd>
          </div>
          <div>
            <dt>expired</dt>
            <dd>{approval.expired ? "是" : "否"}</dd>
          </div>
          <div>
            <dt>stale</dt>
            <dd>{approval.stale ? "是" : "否"}</dd>
          </div>
          <div>
            <dt>决策说明</dt>
            <dd>{approval.decisionReason ?? "未提供"}</dd>
          </div>
        </dl>
      ) : (
        <p className="m4-panel-empty">尚无正式 Approval 记录。</p>
      )}
      {approval?.stale || approval?.expired ? (
        <p className="m4-ops-notice" data-tone="warning">
          <Clock3 aria-hidden="true" />
          {approval.stale
            ? "Approval payload 已过时，不能视为当前批准。"
            : "Approval 已过期，不能用于执行。"}
        </p>
      ) : null}
      <p className="m4-panel-footnote">
        <LockKeyhole aria-hidden="true" />本 Workspace 不提供批准或驳回操作。
      </p>
    </section>
  )
}

function JobPanel({
  data,
  props,
}: {
  data: DataWorkspaceViewModel
  props: DataWorkspaceWorkspaceProps
}) {
  const job = data.job
  const retryCapability = effectiveCapability(data.capabilities.retryJob, [
    { allowed: Boolean(job?.knownStatus), reason: "Job 状态未知，不能重试。" },
    { allowed: Boolean(job?.retryable), reason: "正式 Job 状态未允许重试。" },
    {
      allowed: data.capabilities.permissionsKnown,
      reason: "权限状态未知，不能重试。",
    },
  ])
  return (
    <section
      className="m4-operation-panel"
      data-od-id="transformation-job-panel"
    >
      <div className="m4-panel-heading">
        <div>
          <RefreshCw aria-hidden="true" />
          <h3>Transformation Job</h3>
        </div>
        {job ? <StatusBadge label={job.status} tone={job.tone} /> : null}
      </div>
      {job ? (
        <>
          <div className="m4-job-flags">
            <span data-active={job.accepted ? "true" : "false"}>
              <Check aria-hidden="true" />
              已接受
            </span>
            <span data-active={job.queued ? "true" : "false"}>
              <Clock3 aria-hidden="true" />
              排队
            </span>
            <span data-active={job.running ? "true" : "false"}>
              <RefreshCw aria-hidden="true" />
              运行
            </span>
            <span data-active={job.completed ? "true" : "false"}>
              <CircleCheck aria-hidden="true" />
              完成
            </span>
            <span data-active={job.failed ? "true" : "false"}>
              <XCircle aria-hidden="true" />
              失败
            </span>
          </div>
          <div
            className="m4-job-progress"
            aria-label={`Job 进度 ${job.progress}%`}
          >
            <div>
              <span
                style={{
                  width: `${Math.max(0, Math.min(100, job.progress))}%`,
                }}
              />
            </div>
            <strong>{job.progress}%</strong>
          </div>
          <dl className="m4-compact-facts">
            <div>
              <dt>当前步骤</dt>
              <dd>{job.currentStep ?? "未提供"}</dd>
            </div>
            <div>
              <dt>错误代码</dt>
              <dd>{job.errorCode ?? "无"}</dd>
            </div>
          </dl>
          {job.failed ? (
            <p className="m4-ops-notice" data-tone="danger">
              <XCircle aria-hidden="true" />
              转换失败；源版本仍作为正式只读事实保留，UI 不推断输出是否存在。
            </p>
          ) : null}
          <OperationButton
            capability={retryCapability}
            label="重试 Job"
            pending={props.pendingAction === "retry-job"}
            icon={<RotateCcw aria-hidden="true" />}
            onClick={() =>
              props.onEvent({ action: "retry-job", input: { jobId: job.id } })
            }
          />
        </>
      ) : (
        <p className="m4-panel-empty">尚无正式 Job 状态。</p>
      )}
    </section>
  )
}

const actionLabels: Record<CleaningActionInput["type"], string> = {
  MARK_MISSING: "标记为空值",
  REPLACE_VALUE: "替换值",
  MAP_CATEGORY: "映射类别",
  CAST_TYPE: "转换类型",
  RENAME_COLUMN: "重命名字段",
}

function parseCategoryMapping(value: string) {
  const entries = value
    .split("\n")
    .map((line) => line.split("=>").map((part) => part.trim()))
    .filter(([source, target]) => source && target)
  if (entries.length === 0 || entries.length > 100) return null
  return Object.fromEntries(entries.map(([source, target]) => [source, target]))
}

function CleaningPlanEditorDialog({
  data,
  props,
  open,
  onOpenChange,
}: {
  data: DataWorkspaceViewModel
  props: DataWorkspaceWorkspaceProps
  open: boolean
  onOpenChange: (open: boolean) => void
}) {
  const plan = data.plan
  const updating = Boolean(plan && data.capabilities.updatePlan.allowed)
  const [title, setTitle] = useState("")
  const [rationale, setRationale] = useState("")
  const [actions, setActions] = useState<readonly CleaningActionInput[]>([])
  const [actionType, setActionType] =
    useState<CleaningActionInput["type"]>("MARK_MISSING")
  const [targetColumnId, setTargetColumnId] = useState("")
  const [reason, setActionReason] = useState("")
  const [parameterValue, setParameterValue] = useState("")
  const [castType, setCastType] = useState<
    "STRING" | "INTEGER" | "NUMERIC" | "BOOLEAN" | "DATE" | "DATETIME"
  >("STRING")

  const reset = () => {
    setTitle(updating ? (plan?.title ?? "") : "")
    setRationale(updating ? (plan?.rationale ?? "") : "")
    setActions(updating && plan?.actionsEditable ? plan.editorActions : [])
    setActionType("MARK_MISSING")
    setTargetColumnId(data.columns[0]?.id ?? "")
    setActionReason("")
    setParameterValue("")
    setCastType("STRING")
  }

  useEffect(() => {
    if (open) reset()
  }, [open])

  const addAction = () => {
    if (!targetColumnId || !reason.trim()) return
    const base = {
      targetColumnIds: [targetColumnId],
      rowSelector: { type: "ALL_ROWS" as const },
      reason: reason.trim(),
      sourceIssueIds: [] as readonly string[],
    }
    let action: CleaningActionInput | null = null
    if (actionType === "MARK_MISSING") {
      action = {
        ...base,
        type: "MARK_MISSING",
        parameters: { replacement: null },
      }
    } else if (actionType === "REPLACE_VALUE" && parameterValue.trim()) {
      action = {
        ...base,
        type: "REPLACE_VALUE",
        parameters: { replacement: parameterValue.trim() },
      }
    } else if (actionType === "MAP_CATEGORY") {
      const mapping = parseCategoryMapping(parameterValue)
      if (mapping) {
        action = { ...base, type: "MAP_CATEGORY", parameters: { mapping } }
      }
    } else if (actionType === "CAST_TYPE") {
      action = {
        ...base,
        type: "CAST_TYPE",
        parameters: { targetType: castType, onInvalid: "FAIL" },
      }
    } else if (actionType === "RENAME_COLUMN" && parameterValue.trim()) {
      action = {
        ...base,
        type: "RENAME_COLUMN",
        parameters: { newName: parameterValue.trim() },
      }
    }
    if (!action) return
    setActions((current) => [...current, action])
    setActionReason("")
    setParameterValue("")
  }

  const submitPlan = () => {
    if (!title.trim() || actions.length === 0 || !data.version) return
    if (updating && plan) {
      props.onEvent({
        action: "update-plan",
        input: {
          planId: plan.id,
          lockVersion: plan.lockVersion,
          title: title.trim(),
          rationale: rationale.trim() || null,
          actions,
        },
      })
    } else {
      props.onEvent({
        action: "create-plan",
        input: {
          versionId: data.version.id,
          title: title.trim(),
          rationale: rationale.trim() || null,
          actions,
        },
      })
    }
    onOpenChange(false)
  }

  const submit = (event: FormEvent) => {
    event.preventDefault()
    submitPlan()
  }

  const pending =
    props.pendingAction === "create-plan" ||
    props.pendingAction === "update-plan"
  const requiresParameter = !["MARK_MISSING", "CAST_TYPE"].includes(actionType)
  const parameterLabel =
    actionType === "MAP_CATEGORY"
      ? "类别映射（每行：原值 => 新值）"
      : actionType === "RENAME_COLUMN"
        ? "新字段名"
        : "替换值"

  return (
    <Dialog
      open={open}
      onOpenChange={(nextOpen) => {
        if (nextOpen) reset()
        onOpenChange(nextOpen)
      }}
    >
      <DialogContent className="m4-dialog m4-plan-editor-dialog">
        <DialogHeader>
          <DialogTitle>
            {updating ? "编辑 CleaningPlan" : "创建 CleaningPlan"}
          </DialogTitle>
          <DialogDescription>
            仅允许 M4 确定性白名单 Action。提交只发送意图，不代表
            Preview、审批或执行成功。
          </DialogDescription>
        </DialogHeader>
        <form className="m4-plan-editor" onSubmit={submit}>
          <label>
            计划标题
            <Input
              value={title}
              maxLength={255}
              onChange={(event) => setTitle(event.target.value)}
              disabled={pending}
              autoFocus
            />
          </label>
          <label>
            计划理由
            <textarea
              value={rationale}
              maxLength={5000}
              onChange={(event) => setRationale(event.target.value)}
              disabled={pending}
            />
          </label>
          <fieldset className="m4-action-builder" disabled={pending}>
            <legend>添加确定性 Action</legend>
            <label>
              Action 类型
              <select
                value={actionType}
                onChange={(event) => {
                  setActionType(
                    event.target.value as CleaningActionInput["type"],
                  )
                  setParameterValue("")
                }}
              >
                {Object.entries(actionLabels).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              目标字段
              <select
                value={targetColumnId}
                onChange={(event) => setTargetColumnId(event.target.value)}
              >
                {data.columns.map((column) => (
                  <option key={column.id} value={column.id}>
                    {column.displayName ?? column.sourceName}
                  </option>
                ))}
              </select>
            </label>
            {actionType === "CAST_TYPE" ? (
              <label>
                目标类型
                <select
                  value={castType}
                  onChange={(event) =>
                    setCastType(event.target.value as typeof castType)
                  }
                >
                  {[
                    "STRING",
                    "INTEGER",
                    "NUMERIC",
                    "BOOLEAN",
                    "DATE",
                    "DATETIME",
                  ].map((value) => (
                    <option key={value} value={value}>
                      {value}
                    </option>
                  ))}
                </select>
              </label>
            ) : null}
            {requiresParameter ? (
              <label className="m4-action-parameter">
                {parameterLabel}
                <textarea
                  value={parameterValue}
                  maxLength={actionType === "MAP_CATEGORY" ? 5000 : 255}
                  onChange={(event) => setParameterValue(event.target.value)}
                />
              </label>
            ) : null}
            <label className="m4-action-reason">
              操作理由
              <Input
                value={reason}
                maxLength={2000}
                onChange={(event) => setActionReason(event.target.value)}
              />
            </label>
            <div className="m4-action-builder-footer">
              <span>行范围固定为 ALL_ROWS；复杂 selector 不在本入口推断。</span>
              <Button
                type="button"
                variant="outline"
                onClick={addAction}
                disabled={
                  !targetColumnId ||
                  !reason.trim() ||
                  (requiresParameter && !parameterValue.trim()) ||
                  actions.length >= 50
                }
              >
                <Plus aria-hidden="true" />
                添加 Action
              </Button>
            </div>
          </fieldset>
          <div className="m4-plan-editor-actions" aria-live="polite">
            {actions.map((action, index) => (
              <div key={`${action.type}-${index}`}>
                <span>{index + 1}</span>
                <div>
                  <strong>{actionLabels[action.type]}</strong>
                  <small>{action.reason}</small>
                </div>
                <Button
                  type="button"
                  size="icon"
                  variant="ghost"
                  aria-label={`删除 Action ${index + 1}`}
                  onClick={() =>
                    setActions((current) =>
                      current.filter(
                        (_, currentIndex) => currentIndex !== index,
                      ),
                    )
                  }
                  disabled={pending}
                >
                  <Trash2 aria-hidden="true" />
                </Button>
              </div>
            ))}
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              取消
            </Button>
            <Button
              type="button"
              onClick={submitPlan}
              disabled={pending || !title.trim() || actions.length === 0}
            >
              {pending ? (
                <RefreshCw className="m4-spin" aria-hidden="true" />
              ) : (
                <Check aria-hidden="true" />
              )}
              {updating ? "保存计划" : "创建计划"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export function CleaningView({
  data,
  props,
}: {
  data: DataWorkspaceViewModel
  props: DataWorkspaceWorkspaceProps
}) {
  const [editorOpen, setEditorOpen] = useState(false)
  const plan = data.plan
  const planKnown = Boolean(plan?.knownStatus && plan.permissionsKnown)
  const previewCapability = effectiveCapability(data.capabilities.previewPlan, [
    { allowed: planKnown, reason: "Plan 状态或权限未知，不能生成 Preview。" },
    {
      allowed: Boolean(plan?.allowedActions.has("cleaning_plan.preview")),
      reason: "Plan allowed action 未包含 preview。",
    },
  ])
  const requestCapability = effectiveCapability(
    data.capabilities.requestApproval,
    [
      { allowed: planKnown, reason: "Plan 状态或权限未知，不能请求审批。" },
      {
        allowed: Boolean(
          plan?.allowedActions.has("cleaning_plan.request_approval"),
        ),
        reason: "Plan allowed action 未包含 request approval。",
      },
    ],
  )
  const executeCapability = effectiveCapability(data.capabilities.executePlan, [
    { allowed: planKnown, reason: "Plan 状态或权限未知，不能执行。" },
    {
      allowed: Boolean(plan?.allowedActions.has("cleaning_plan.execute")),
      reason: "Plan allowed action 未包含 execute。",
    },
    {
      allowed: Boolean(
        data.approval && !data.approval.expired && !data.approval.stale,
      ),
      reason: "缺少当前有效的 Formal Approval。",
    },
  ])
  const editorCapability =
    plan && data.capabilities.updatePlan.allowed
      ? effectiveCapability(data.capabilities.updatePlan, [
          {
            allowed: plan.actionsEditable,
            reason:
              plan.actionsDisabledReason ??
              "Plan Action 未通过当前 typed whitelist 校验。",
          },
        ])
      : data.capabilities.createPlan
  return (
    <div className="m4-cleaning-view">
      <section
        className="m4-cleaning-summary"
        data-od-id="cleaning-plan-summary"
      >
        <div className="m4-ops-heading">
          <div>
            <RefreshCw aria-hidden="true" />
            <div>
              <h2>{plan?.title ?? "清洗与转换"}</h2>
              <p>{plan?.rationale ?? "当前没有正式 CleaningPlan。"}</p>
            </div>
          </div>
          {plan ? <StatusBadge label={plan.status} tone={plan.tone} /> : null}
        </div>
        <ProcessTrack data={data} />
        <div className="m4-cleaning-actions">
          <OperationButton
            capability={previewCapability}
            label="生成确定性 Preview"
            pending={props.pendingAction === "preview-plan"}
            icon={<Play aria-hidden="true" />}
            onClick={() =>
              plan &&
              props.onEvent({
                action: "preview-plan",
                input: { planId: plan.id },
              })
            }
          />
          <OperationButton
            capability={requestCapability}
            label="请求正式审批"
            pending={props.pendingAction === "request-approval"}
            icon={<ShieldCheck aria-hidden="true" />}
            onClick={() =>
              plan &&
              props.onEvent({
                action: "request-approval",
                input: { planId: plan.id },
              })
            }
          />
          <OperationButton
            capability={executeCapability}
            label="执行已批准计划"
            pending={props.pendingAction === "execute-plan"}
            icon={<Play aria-hidden="true" />}
            primary
            onClick={() =>
              plan &&
              props.onEvent({
                action: "execute-plan",
                input: { planId: plan.id },
              })
            }
          />
          <OperationButton
            capability={editorCapability}
            label={
              plan && data.capabilities.updatePlan.allowed
                ? "编辑计划"
                : "新建计划"
            }
            pending={
              props.pendingAction === "create-plan" ||
              props.pendingAction === "update-plan"
            }
            icon={<Pencil aria-hidden="true" />}
            onClick={() => setEditorOpen(true)}
          />
        </div>
      </section>
      <div className="m4-cleaning-grid">
        <section
          className="m4-operation-panel m4-action-summary"
          data-od-id="cleaning-action-summary"
        >
          <div className="m4-panel-heading">
            <div>
              <ListFilter aria-hidden="true" />
              <h3>Action 摘要</h3>
            </div>
            <span>{plan?.actionCount ?? 0}</span>
          </div>
          {plan?.actions.length ? (
            <div className="m4-action-list">
              {plan.actions.map((action, index) => (
                <article key={`${action.type}-${index}`}>
                  <span>{index + 1}</span>
                  <div>
                    <strong>{action.type}</strong>
                    <p>{action.reason}</p>
                  </div>
                  <small>{action.targetCount} 个目标</small>
                </article>
              ))}
            </div>
          ) : (
            <p className="m4-panel-empty">没有正式 Action 摘要。</p>
          )}
        </section>
        <section
          className="m4-operation-panel"
          data-od-id="deterministic-preview-panel"
        >
          <div className="m4-panel-heading">
            <div>
              <CircleCheck aria-hidden="true" />
              <h3>Deterministic Preview</h3>
            </div>
            {plan?.preview ? (
              <StatusBadge
                label={plan.preview.readyForApproval ? "READY" : "NOT_READY"}
                tone={plan.preview.readyForApproval ? "success" : "warning"}
              />
            ) : null}
          </div>
          {plan?.preview ? (
            <>
              <dl className="m4-compact-facts">
                <div>
                  <dt>影响行</dt>
                  <dd>{formatNumber(plan.preview.affectedRows)}</dd>
                </div>
                <div>
                  <dt>影响列</dt>
                  <dd>{formatNumber(plan.preview.affectedColumns)}</dd>
                </div>
                <div>
                  <dt>行数前 / 后</dt>
                  <dd>
                    {formatNumber(plan.preview.rowCountBefore)} /{" "}
                    {formatNumber(plan.preview.rowCountAfter)}
                  </dd>
                </div>
                <div>
                  <dt>风险</dt>
                  <dd>{plan.preview.risk}</dd>
                </div>
                <div>
                  <dt>Preview hash</dt>
                  <dd title={plan.preview.hash}>{plan.preview.hash}</dd>
                </div>
              </dl>
              {plan.preview.warnings.length ? (
                <ul className="m4-warning-list">
                  {plan.preview.warnings.map((warning) => (
                    <li key={warning}>
                      <AlertTriangle aria-hidden="true" />
                      {warning}
                    </li>
                  ))}
                </ul>
              ) : null}
            </>
          ) : (
            <p className="m4-panel-empty">尚无正式 Preview 结果。</p>
          )}
        </section>
        <ApprovalPanel data={data} />
        <JobPanel data={data} props={props} />
        <section
          className="m4-operation-panel"
          data-od-id="transformation-result-panel"
        >
          <div className="m4-panel-heading">
            <div>
              <GitCompareArrows aria-hidden="true" />
              <h3>Transformation</h3>
            </div>
            {data.transformation ? (
              <StatusBadge
                label={data.transformation.status}
                tone={data.transformation.tone}
              />
            ) : null}
          </div>
          {data.transformation ? (
            <dl className="m4-compact-facts">
              <div>
                <dt>源版本</dt>
                <dd>{data.transformation.sourceVersionId}</dd>
              </div>
              <div>
                <dt>目标版本</dt>
                <dd>{data.transformation.targetVersionId ?? "未提供"}</dd>
              </div>
              <div>
                <dt>输出 Artifact</dt>
                <dd>{data.transformation.outputArtifactId ?? "未提供"}</dd>
              </div>
              <div>
                <dt>影响行 / 列</dt>
                <dd>
                  {formatNumber(data.transformation.affectedRows)} /{" "}
                  {formatNumber(data.transformation.affectedColumns)}
                </dd>
              </div>
              <div>
                <dt>错误代码</dt>
                <dd>{data.transformation.errorCode ?? "无"}</dd>
              </div>
            </dl>
          ) : (
            <p className="m4-panel-empty">尚无正式 Transformation 结果。</p>
          )}
        </section>
      </div>
      <CleaningPlanEditorDialog
        data={data}
        props={props}
        open={editorOpen}
        onOpenChange={setEditorOpen}
      />
    </div>
  )
}

export function VersionsOperationsView({
  data,
  props,
}: {
  data: DataWorkspaceViewModel
  props: DataWorkspaceWorkspaceProps
}) {
  const version = data.version
  const comparison = data.comparison
  if (!version)
    return (
      <div className="m4-ops-empty">
        <History aria-hidden="true" />
        <strong>没有版本上下文</strong>
        <p>选择数据集后查看正式版本与比较事实。</p>
      </div>
    )
  return (
    <div
      className="m4-versions-operations"
      data-od-id="versions-comparison-view"
    >
      <section className="m4-version-current">
        <div className="m4-ops-heading">
          <div>
            <History aria-hidden="true" />
            <div>
              <h2>版本 {version.versionNumber}</h2>
              <p>
                {version.versionType} · {version.fileFormat} ·{" "}
                {formatDate(version.createdAt)}
              </p>
            </div>
          </div>
          <StatusBadge label={version.status} tone={version.tone} />
        </div>
        <div className="m4-version-flags">
          <span>
            <CircleCheck aria-hidden="true" />
            {version.original ? "Original" : "Derived"}
          </span>
          <span>
            <CircleCheck aria-hidden="true" />
            {version.current ? "当前版本" : "非当前版本"}
          </span>
          <span data-tone={version.invalidated ? "danger" : "muted"}>
            {version.invalidated ? (
              <XCircle aria-hidden="true" />
            ) : (
              <CircleCheck aria-hidden="true" />
            )}
            {version.invalidated ? "已失效" : "有效标识"}
          </span>
        </div>
        <dl className="m4-lineage-hashes">
          <div>
            <dt>Data hash</dt>
            <dd title={version.dataHash}>{version.dataHash}</dd>
          </div>
          <div>
            <dt>Schema hash</dt>
            <dd title={version.schemaHash ?? ""}>
              {version.schemaHash ?? "未提供"}
            </dd>
          </div>
          <div>
            <dt>Projection hash</dt>
            <dd title={version.projectionHash ?? ""}>
              {version.projectionHash ?? "未提供"}
            </dd>
          </div>
        </dl>
      </section>
      <section className="m4-lineage-list" aria-label="当前版本血缘事实">
        <div className="m4-panel-heading">
          <div>
            <GitCompareArrows aria-hidden="true" />
            <h3>血缘</h3>
          </div>
        </div>
        <ol>
          <li>
            <span>1</span>
            <div>
              <strong>Parent Version</strong>
              <small>{version.parentVersionId ?? "无"}</small>
            </div>
          </li>
          <li>
            <span>2</span>
            <div>
              <strong>Transformation</strong>
              <small>{version.transformationId ?? "无"}</small>
            </div>
          </li>
          <li>
            <span>3</span>
            <div>
              <strong>Current Version</strong>
              <small>{version.id}</small>
            </div>
          </li>
          <li>
            <span>4</span>
            <div>
              <strong>Artifact</strong>
              <small>{version.artifactId}</small>
            </div>
          </li>
        </ol>
      </section>
      <section className="m4-comparison-panel" data-od-id="version-comparison">
        <div className="m4-panel-heading">
          <div>
            <GitCompareArrows aria-hidden="true" />
            <h3>正式版本比较</h3>
          </div>
          {comparison ? (
            <span>
              {comparison.baseVersionId} → {comparison.targetVersionId}
            </span>
          ) : null}
        </div>
        {version.parentVersionId ? (
          <div className="m4-comparison-command">
            <OperationButton
              capability={data.capabilities.compareVersions}
              label="与父版本比较"
              pending={props.pendingAction === "compare-versions"}
              icon={<GitCompareArrows aria-hidden="true" />}
              onClick={() =>
                data.dataset &&
                props.onEvent({
                  action: "compare-versions",
                  input: {
                    datasetId: data.dataset.id,
                    baseVersionId: version.parentVersionId!,
                    targetVersionId: version.id,
                  },
                })
              }
            />
          </div>
        ) : null}
        {comparison ? (
          <>
            <dl className="m4-comparison-facts">
              <div>
                <dt>行变化</dt>
                <dd>
                  {comparison.rowDelta >= 0 ? "+" : ""}
                  {comparison.rowDelta}
                </dd>
              </div>
              <div>
                <dt>列变化</dt>
                <dd>
                  {comparison.columnDelta >= 0 ? "+" : ""}
                  {comparison.columnDelta}
                </dd>
              </div>
              <div>
                <dt>缺失值</dt>
                <dd>
                  {comparison.missingBefore} → {comparison.missingAfter}
                </dd>
              </div>
              <div>
                <dt>影响行</dt>
                <dd>{formatNumber(comparison.affectedRows)}</dd>
              </div>
              <div>
                <dt>影响列</dt>
                <dd>{formatNumber(comparison.affectedColumns)}</dd>
              </div>
            </dl>
            <div className="m4-comparison-actions">
              <span>Action types</span>
              {comparison.actionTypes.map((action) => (
                <code key={action}>{action}</code>
              ))}
            </div>
            <dl className="m4-compact-facts">
              <div>
                <dt>Parent</dt>
                <dd>{comparison.parentVersionId ?? "未提供"}</dd>
              </div>
              <div>
                <dt>Transformation</dt>
                <dd>{comparison.transformationId ?? "未提供"}</dd>
              </div>
              <div>
                <dt>Output Artifact</dt>
                <dd>{comparison.outputArtifactId ?? "未提供"}</dd>
              </div>
            </dl>
          </>
        ) : (
          <div className="m4-ops-empty">
            <GitCompareArrows aria-hidden="true" />
            <strong>暂无正式比较结果</strong>
            <p>当前只显示已选择版本的正式事实。</p>
          </div>
        )}
      </section>
    </div>
  )
}

function IssueInspector({
  data,
  props,
  issue,
  onAcknowledge,
  onIgnore,
}: {
  data: DataWorkspaceViewModel
  props: DataWorkspaceWorkspaceProps
  issue: QualityIssueViewModel | null
  onAcknowledge: (issue: QualityIssueViewModel) => void
  onIgnore: (issue: QualityIssueViewModel) => void
}) {
  if (!issue)
    return <p className="m4-inspector-empty">选择一个 Issue 查看正式详情。</p>
  const known =
    issue.knownStatus &&
    issue.permissionsKnown &&
    data.capabilities.permissionsKnown &&
    data.qualityRun?.knownStatus !== false &&
    !data.qualityRun?.degraded
  const acknowledgeCapability = effectiveCapability(
    data.capabilities.acknowledgeIssue,
    [
      { allowed: known, reason: "Issue 状态或权限未知。" },
      {
        allowed: issue.allowedActions.has("data_quality_issue.acknowledge"),
        reason: "Issue allowed action 未包含 acknowledge。",
      },
    ],
  )
  const ignoreCapability = effectiveCapability(data.capabilities.ignoreIssue, [
    { allowed: known, reason: "Issue 状态或权限未知。" },
    {
      allowed: issue.allowedActions.has("data_quality_issue.ignore"),
      reason: "Issue allowed action 未包含 ignore。",
    },
  ])
  return (
    <section className="m4-issue-inspector">
      <div className="m4-inspector-title">
        <div>
          <CircleAlert aria-hidden="true" />
          <strong>{issue.issueType}</strong>
        </div>
        <StatusBadge
          label={issue.severity}
          tone={
            issue.severity === "HIGH"
              ? "danger"
              : issue.severity === "MEDIUM"
                ? "warning"
                : "info"
          }
        />
      </div>
      <p className="m4-issue-description">{issue.description}</p>
      <dl className="m4-compact-facts">
        <div>
          <dt>规则</dt>
          <dd>{issue.ruleCode}</dd>
        </div>
        <div>
          <dt>状态</dt>
          <dd>{issue.status}</dd>
        </div>
        <div>
          <dt>影响行</dt>
          <dd>{formatNumber(issue.affectedRowCount)}</dd>
        </div>
        <div>
          <dt>需审批</dt>
          <dd>{issue.requiresApproval ? "是" : "否"}</dd>
        </div>
        <div>
          <dt>敏感候选</dt>
          <dd>{issue.sensitiveCandidate ? "是" : "否"}</dd>
        </div>
        <div>
          <dt>敏感已确认</dt>
          <dd>{issue.sensitiveConfirmed ? "是" : "否"}</dd>
        </div>
      </dl>
      <div className="m4-example-summary">
        <span>有界示例</span>
        {issue.exampleSummary.length ? (
          <ul>
            {issue.exampleSummary.map((example, index) => (
              <li key={`${index}-${example}`}>
                <code>{example}</code>
              </li>
            ))}
          </ul>
        ) : (
          <p>未提供示例。</p>
        )}
      </div>
      {issue.clueOnly || issue.sensitiveCandidate ? (
        <p className="m4-ops-notice" data-tone="warning">
          <Info aria-hidden="true" />
          这是需人工复核的线索，不应显示为已确认错误。
        </p>
      ) : (
        <p className="m4-ops-notice" data-tone="info">
          <CircleCheck aria-hidden="true" />
          这是规则返回的检测事实；处置状态仍由服务端决定。
        </p>
      )}
      {!issue.knownStatus ? (
        <p className="m4-ops-notice" data-tone="degraded">
          <AlertTriangle aria-hidden="true" />
          未知状态 {issue.status}，操作已关闭。
        </p>
      ) : null}
      <div className="m4-inspector-actions">
        <OperationButton
          capability={acknowledgeCapability}
          label="确认已复核"
          pending={props.pendingAction === "acknowledge-issue"}
          icon={<Check aria-hidden="true" />}
          onClick={() => onAcknowledge(issue)}
        />
        <OperationButton
          capability={ignoreCapability}
          label="忽略并说明原因"
          pending={props.pendingAction === "ignore-issue"}
          icon={<XCircle aria-hidden="true" />}
          onClick={() => onIgnore(issue)}
        />
      </div>
    </section>
  )
}

export function OperationsInspector({
  view,
  data,
  props,
  selectedIssueId,
  onAcknowledge,
  onIgnore,
}: {
  view: OperationView
  data: DataWorkspaceViewModel
  props: DataWorkspaceWorkspaceProps
  selectedIssueId: string | null
  onAcknowledge: (issue: QualityIssueViewModel) => void
  onIgnore: (issue: QualityIssueViewModel) => void
}) {
  if (view === "quality") {
    const issue =
      data.issues.find((candidate) => candidate.id === selectedIssueId) ??
      data.issues[0] ??
      null
    return (
      <IssueInspector
        data={data}
        props={props}
        issue={issue}
        onAcknowledge={onAcknowledge}
        onIgnore={onIgnore}
      />
    )
  }
  if (view === "cleaning") {
    return (
      <div className="m4-operations-inspector">
        <div className="m4-inspector-title">
          <div>
            <RefreshCw aria-hidden="true" />
            <strong>执行上下文</strong>
          </div>
        </div>
        <dl className="m4-compact-facts">
          <div>
            <dt>Plan lock</dt>
            <dd>{data.plan?.lockVersion ?? "未提供"}</dd>
          </div>
          <div>
            <dt>Approval ID</dt>
            <dd>{data.plan?.approvalRecordId ?? "未提供"}</dd>
          </div>
          <div>
            <dt>Transformation ID</dt>
            <dd>{data.plan?.transformationId ?? "未提供"}</dd>
          </div>
          <div>
            <dt>Job ID</dt>
            <dd>{data.plan?.jobId ?? "未提供"}</dd>
          </div>
          <div>
            <dt>Approval 状态</dt>
            <dd>{data.approval?.status ?? "未提供"}</dd>
          </div>
          <div>
            <dt>Job 状态</dt>
            <dd>{data.job?.status ?? "未提供"}</dd>
          </div>
        </dl>
        <p className="m4-ops-notice" data-tone="info">
          <Info aria-hidden="true" />
          Preview、Approval、Job accepted 和 Transformation result
          是独立正式事实。
        </p>
      </div>
    )
  }
  return (
    <div className="m4-operations-inspector">
      <div className="m4-inspector-title">
        <div>
          <History aria-hidden="true" />
          <strong>版本上下文</strong>
        </div>
      </div>
      <dl className="m4-compact-facts">
        <div>
          <dt>当前 Version</dt>
          <dd>{data.version?.id ?? "未提供"}</dd>
        </div>
        <div>
          <dt>Parent</dt>
          <dd>{data.version?.parentVersionId ?? "未提供"}</dd>
        </div>
        <div>
          <dt>Transformation</dt>
          <dd>{data.version?.transformationId ?? "未提供"}</dd>
        </div>
        <div>
          <dt>Comparison</dt>
          <dd>
            {data.comparison
              ? `${data.comparison.baseVersionId} → ${data.comparison.targetVersionId}`
              : "未提供"}
          </dd>
        </div>
      </dl>
    </div>
  )
}

export function IssueActionDialogs({
  acknowledgeIssue,
  ignoreIssue,
  props,
  onCloseAcknowledge,
  onCloseIgnore,
}: {
  acknowledgeIssue: QualityIssueViewModel | null
  ignoreIssue: QualityIssueViewModel | null
  props: DataWorkspaceWorkspaceProps
  onCloseAcknowledge: () => void
  onCloseIgnore: () => void
}) {
  const [reason, setReason] = useState("")
  const submitIgnore = (event: FormEvent) => {
    event.preventDefault()
    if (
      !ignoreIssue ||
      !reason.trim() ||
      props.pendingAction === "ignore-issue"
    )
      return
    props.onEvent({
      action: "ignore-issue",
      input: { issueId: ignoreIssue.id, reason: reason.trim() },
    })
    setReason("")
    onCloseIgnore()
  }
  return (
    <>
      <Dialog
        open={Boolean(acknowledgeIssue)}
        onOpenChange={(open) => !open && onCloseAcknowledge()}
      >
        <DialogContent
          className="m4-dialog"
          data-od-id="acknowledge-issue-dialog"
        >
          <DialogHeader>
            <DialogTitle>确认已复核 Issue</DialogTitle>
            <DialogDescription>
              此操作只发送 acknowledge 意图，不会在本地把 Issue 改为已确认。
            </DialogDescription>
          </DialogHeader>
          <div className="m4-dialog-summary">
            <CircleAlert aria-hidden="true" />
            <div>
              <strong>{acknowledgeIssue?.issueType}</strong>
              <span>{acknowledgeIssue?.ruleCode}</span>
            </div>
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={onCloseAcknowledge}
            >
              取消
            </Button>
            <Button
              type="button"
              disabled={
                !acknowledgeIssue || props.pendingAction === "acknowledge-issue"
              }
              onClick={() => {
                if (!acknowledgeIssue) return
                props.onEvent({
                  action: "acknowledge-issue",
                  input: { issueId: acknowledgeIssue.id },
                })
                onCloseAcknowledge()
              }}
            >
              <Check aria-hidden="true" />
              确认已复核
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      <Dialog
        open={Boolean(ignoreIssue)}
        onOpenChange={(open) => {
          if (!open) {
            setReason("")
            onCloseIgnore()
          }
        }}
      >
        <DialogContent
          className="m4-dialog"
          data-od-id="ignore-issue-dialog"
          onOpenAutoFocus={(event) => {
            event.preventDefault()
            requestAnimationFrame(() =>
              document.getElementById("m4-ignore-reason")?.focus(),
            )
          }}
        >
          <DialogHeader>
            <DialogTitle>忽略 Issue</DialogTitle>
            <DialogDescription>
              必须记录原因。忽略意图不会在本地改变正式 Issue 状态。
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={submitIgnore} className="m4-ignore-form">
            <div className="m4-dialog-summary">
              <XCircle aria-hidden="true" />
              <div>
                <strong>{ignoreIssue?.issueType}</strong>
                <span>{ignoreIssue?.ruleCode}</span>
              </div>
            </div>
            <label htmlFor="m4-ignore-reason">
              忽略原因
              <Input
                id="m4-ignore-reason"
                value={reason}
                onChange={(event) => setReason(event.target.value)}
                placeholder="说明为何不处理此 Issue"
                disabled={props.pendingAction === "ignore-issue"}
              />
            </label>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setReason("")
                  onCloseIgnore()
                }}
              >
                取消
              </Button>
              <Button
                type="submit"
                disabled={
                  !reason.trim() || props.pendingAction === "ignore-issue"
                }
              >
                {props.pendingAction === "ignore-issue" ? (
                  <RefreshCw className="m4-spin" aria-hidden="true" />
                ) : (
                  <Check aria-hidden="true" />
                )}
                {props.pendingAction === "ignore-issue"
                  ? "提交中"
                  : "提交忽略原因"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </>
  )
}
