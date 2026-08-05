import {
  AlertTriangle,
  BarChart3,
  Beaker,
  CheckCircle2,
  ChevronRight,
  Database,
  FileBarChart,
  Info,
  LockKeyhole,
  Menu,
  PanelRight,
  Play,
  RefreshCw,
  Save,
  ShieldCheck,
  Square,
  XCircle,
} from "lucide-react"
import { type ReactNode, useEffect, useRef, useState } from "react"

import {
  DegradedNotice,
  InspectorSection,
  JobProgress,
  LoadableState,
  MetadataList,
  MutationError,
  PermissionNotice,
  StatusBadge,
  useVisualTheme,
  WorkspaceHeader,
  WorkspaceLoadingSkeleton,
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
  AnalysisPlanInput,
  AnalysisWorkspaceViewModel,
  ColumnContextViewModel,
  SampleFilter,
} from "../model"
import type { AnalysisWorkspaceRouteView } from "../route-contract"
import { AnalysisResultCard } from "./AnalysisResultRenderers"
import type { AnalysisWorkspaceWorkspaceProps } from "./contracts"
import { FigureWorkspace } from "./FigureWorkspace"
import "./analysis-workspace.css"

const views: ReadonlyArray<{
  id: AnalysisWorkspaceRouteView
  label: string
  icon: typeof Beaker
}> = [
  { id: "plan", label: "分析计划", icon: Beaker },
  { id: "assumptions", label: "前提检查", icon: ShieldCheck },
  { id: "runs", label: "运行记录", icon: Play },
  { id: "results", label: "分析结果", icon: BarChart3 },
  { id: "figures", label: "图表", icon: FileBarChart },
]

const methods: ReadonlyArray<{
  value: AnalysisPlanInput["method"]
  label: string
}> = [
  { value: "DESCRIPTIVE_STATISTICS", label: "描述性统计" },
  { value: "PEARSON_CORRELATION", label: "Pearson 相关" },
  { value: "SPEARMAN_CORRELATION", label: "Spearman 相关" },
  { value: "INDEPENDENT_TWO_GROUP", label: "独立两组比较" },
  { value: "PAIRED_TWO_GROUP", label: "配对两组比较" },
  { value: "SIMPLE_LINEAR_REGRESSION", label: "简单线性回归" },
]

function statusLabel(status: string, known = true) {
  if (!known) return "未知状态"
  const labels: Record<string, string> = {
    AVAILABLE: "可用",
    DRAFT: "草稿",
    NEEDS_INPUT: "需要补充",
    READY: "已就绪",
    NEEDS_APPROVAL: "等待审批",
    APPROVED: "已批准",
    REJECTED: "已拒绝",
    INVALIDATED: "已失效",
    PASSED: "通过",
    WARNING: "警告",
    FAILED: "失败",
    REQUIRES_USER_CONFIRMATION: "需要确认",
    QUEUED: "排队中",
    RUNNING: "运行中",
    COMPLETED: "已完成",
    CONFIRMED: "已确认",
    NEEDS_REVIEW: "需要复核",
  }
  return labels[status] ?? status
}

function shortHash(value: string | null) {
  if (!value) return "未提供"
  if (value.length <= 18) return value
  return `${value.slice(0, 10)}…${value.slice(-6)}`
}

function percent(value: number | null) {
  if (value === null) return "未提供"
  return (
    new Intl.NumberFormat("zh-CN", { maximumFractionDigits: 2 }).format(
      value * 100,
    ) + "%"
  )
}

function defaultPlan(data: AnalysisWorkspaceViewModel): AnalysisPlanInput {
  const first = data.columns[0]?.id ?? ""
  const second = data.columns[1]?.id ?? first
  return {
    researchQuestionVersionId: data.plan?.researchQuestionVersionId ?? "",
    datasetVersionId: data.dataset?.versionId ?? "",
    analysisGoal: "CORRELATION",
    method: "PEARSON_CORRELATION",
    dependentVariableIds: second ? [second] : [],
    independentVariableIds: first ? [first] : [],
    controlVariableIds: [],
    missingDataMode: "COMPLETE_CASE",
    sampleFilter: null,
    confidenceLevel: 0.95,
    alternative: "TWO_SIDED",
    varianceMode: "WELCH",
    independenceConfirmed: false,
    pairingConfirmed: false,
    pairIdColumnId: null,
    assumptionConfirmations: [],
    acknowledgedQualityIssueIds: [],
    sensitiveColumnAcknowledgements: [],
  }
}

function CapabilityButton({
  capability,
  pending,
  children,
  onClick,
  variant = "outline",
  icon,
  extraDisabled,
  extraReason,
}: {
  capability: ActionCapability
  pending: boolean
  children: ReactNode
  onClick: () => void
  variant?: "default" | "outline" | "destructive"
  icon?: ReactNode
  extraDisabled?: boolean
  extraReason?: string
}) {
  const disabled = pending || !capability.allowed || Boolean(extraDisabled)
  const reason = pending
    ? "操作正在提交，请等待服务端响应。"
    : extraDisabled
      ? extraReason
      : capability.disabledReason
  return (
    <div className="m5-action-control">
      <Button
        type="button"
        variant={variant}
        disabled={disabled}
        onClick={onClick}
        title={reason ?? undefined}
      >
        {icon}
        {children}
      </Button>
      {disabled && reason ? (
        <span className="m5-disabled-reason">{reason}</span>
      ) : null}
    </div>
  )
}

function DatasetRail({
  data,
  view,
  onView,
}: {
  data: AnalysisWorkspaceViewModel
  view: AnalysisWorkspaceRouteView
  onView: (view: AnalysisWorkspaceRouteView) => void
}) {
  return (
    <div className="m5-context-rail__inner">
      <section
        className="m5-dataset-context"
        data-od-id="analysis-dataset-context"
      >
        <div className="m5-eyebrow">正式数据上下文</div>
        <div className="m5-dataset-context__title">
          <Database aria-hidden="true" />
          <strong>{data.dataset?.datasetName ?? "尚未选择数据集"}</strong>
        </div>
        {data.dataset ? (
          <>
            <span>版本 {data.dataset.versionNumber}</span>
            <StatusBadge
              label={statusLabel(data.dataset.status, data.dataset.knownStatus)}
              tone={data.dataset.tone}
            />
          </>
        ) : (
          <span>需要从 Data Workspace 选择正式版本</span>
        )}
      </section>
      <nav className="m5-view-nav" aria-label="分析工作台视图">
        {views.map((item) => {
          const Icon = item.icon
          const count =
            item.id === "assumptions"
              ? data.plan?.checks.length
              : item.id === "results"
                ? data.results.length
                : item.id === "figures"
                  ? data.figure
                    ? 1
                    : 0
                  : undefined
          return (
            <button
              key={item.id}
              type="button"
              aria-current={view === item.id ? "page" : undefined}
              onClick={() => onView(item.id)}
              data-od-id={`analysis-view-${item.id}`}
            >
              <Icon aria-hidden="true" />
              <span>{item.label}</span>
              {count !== undefined ? (
                <em>{count}</em>
              ) : (
                <ChevronRight aria-hidden="true" />
              )}
            </button>
          )
        })}
      </nav>
      <div className="m5-context-rail__footer">
        <Button type="button" variant="ghost" onClick={() => undefined}>
          <Database aria-hidden="true" /> 返回 Data Workspace
        </Button>
        <span>正式导航由 Codex 接线</span>
      </div>
    </div>
  )
}

function ColumnSummary({ column }: { column: ColumnContextViewModel }) {
  return (
    <article
      className="m5-column-row"
      data-warning={column.qualityWarning || undefined}
    >
      <div>
        <strong title={column.sensitive ? undefined : column.name}>
          {column.displayValue}
        </strong>
        <span>
          {column.confirmedType ?? "类型未知"}
          {column.unit ? ` · ${column.unit}` : ""}
        </span>
      </div>
      <div>
        <StatusBadge
          label={
            column.confirmationKnown
              ? column.confirmationStatus
              : "确认状态未知"
          }
          tone={column.confirmed ? "success" : "warning"}
        />
        <span>缺失 {percent(column.missingRatio)}</span>
      </div>
    </article>
  )
}

function PlanView({
  data,
  draft,
  setDraft,
  editable,
  unsafeReason,
  pendingAction,
  onSave,
  onValidate,
  onApproval,
  onRun,
}: {
  data: AnalysisWorkspaceViewModel
  draft: AnalysisPlanInput
  setDraft: (draft: AnalysisPlanInput) => void
  editable: boolean
  unsafeReason: string | null
  pendingAction: AnalysisWorkspaceWorkspaceProps["pendingAction"]
  onSave: () => void
  onValidate: () => void
  onApproval: () => void
  onRun: () => void
}) {
  const plan = data.plan
  const update = <K extends keyof AnalysisPlanInput>(
    key: K,
    value: AnalysisPlanInput[K],
  ) => setDraft({ ...draft, [key]: value })
  const filter = draft.sampleFilter
  const filterOperator = filter?.operator ?? "NONE"
  const setFilterOperator = (operator: string) => {
    const columnId = data.columns[0]?.id ?? ""
    let next: SampleFilter | null = null
    if (operator === "EQUALS") next = { operator, columnId, value: "" }
    if (operator === "IN") next = { operator, columnId, values: [] }
    if (operator === "IS_NULL" || operator === "IS_NOT_NULL")
      next = { operator, columnId }
    if (operator === "NUMERIC_RANGE")
      next = {
        operator,
        columnId,
        minimum: null,
        maximum: null,
        includeMinimum: true,
        includeMaximum: true,
      }
    update("sampleFilter", next)
  }

  return (
    <div className="m5-view-stack" data-od-id="analysis-plan-surface">
      <section className="m5-surface-heading">
        <div>
          <span className="m5-eyebrow">AnalysisPlan</span>
          <h2>{plan ? "编辑分析计划" : "创建分析计划"}</h2>
          <p>草稿只保存在本地界面；正式状态仅在服务端响应后变化。</p>
        </div>
        {plan ? (
          <StatusBadge
            label={statusLabel(plan.status, plan.knownStatus)}
            tone={plan.tone}
          />
        ) : null}
      </section>

      {!editable ? (
        <PermissionNotice
          title="当前计划保持只读"
          reason={
            plan?.approvalStale
              ? "审批已失效，需要创建或验证新的计划版本。"
              : `状态 ${statusLabel(plan?.status ?? "UNKNOWN", plan?.knownStatus)} 不允许原地覆盖正式计划。`
          }
        />
      ) : null}
      {unsafeReason ? (
        <PermissionNotice
          title="数据上下文尚未满足写入条件"
          reason={unsafeReason}
        />
      ) : null}

      <form
        className="m5-plan-form"
        onSubmit={(event) => {
          event.preventDefault()
          onSave()
        }}
      >
        <fieldset disabled={!editable || Boolean(pendingAction)}>
          <legend>方法与目标</legend>
          <label>
            <span>分析目标</span>
            <select
              value={draft.analysisGoal}
              onChange={(e) =>
                update(
                  "analysisGoal",
                  e.target.value as AnalysisPlanInput["analysisGoal"],
                )
              }
            >
              <option value="DESCRIBE">描述</option>
              <option value="CORRELATION">相关</option>
              <option value="COMPARE_GROUPS">组间比较</option>
              <option value="MODEL">建模</option>
            </select>
          </label>
          <label>
            <span>统计方法</span>
            <select
              value={draft.method}
              onChange={(e) =>
                update("method", e.target.value as AnalysisPlanInput["method"])
              }
            >
              {methods.map((method) => (
                <option key={method.value} value={method.value}>
                  {method.label}
                </option>
              ))}
            </select>
          </label>
          <label>
            <span>缺失数据模式</span>
            <select
              value={draft.missingDataMode}
              onChange={(e) =>
                update(
                  "missingDataMode",
                  e.target.value as AnalysisPlanInput["missingDataMode"],
                )
              }
            >
              <option value="COMPLETE_CASE">完整案例</option>
              <option value="PAIRWISE_COMPLETE">成对完整</option>
            </select>
          </label>
          <label>
            <span>置信水平</span>
            <input
              type="number"
              min="0.5"
              max="0.999"
              step="0.001"
              value={draft.confidenceLevel}
              onChange={(e) =>
                update("confidenceLevel", Number(e.target.value))
              }
            />
          </label>
        </fieldset>

        <fieldset disabled={!editable || Boolean(pendingAction)}>
          <legend>变量角色</legend>
          <label>
            <span>因变量</span>
            <select
              value={draft.dependentVariableIds[0] ?? ""}
              onChange={(e) =>
                update(
                  "dependentVariableIds",
                  e.target.value ? [e.target.value] : [],
                )
              }
            >
              <option value="">未选择</option>
              {data.columns.map((column) => (
                <option key={column.id} value={column.id}>
                  {column.displayValue}
                </option>
              ))}
            </select>
          </label>
          <label>
            <span>自变量</span>
            <select
              value={draft.independentVariableIds[0] ?? ""}
              onChange={(e) =>
                update(
                  "independentVariableIds",
                  e.target.value ? [e.target.value] : [],
                )
              }
            >
              <option value="">未选择</option>
              {data.columns.map((column) => (
                <option key={column.id} value={column.id}>
                  {column.displayValue}
                </option>
              ))}
            </select>
          </label>
          <label>
            <span>控制变量</span>
            <select
              value={draft.controlVariableIds[0] ?? ""}
              onChange={(e) =>
                update(
                  "controlVariableIds",
                  e.target.value ? [e.target.value] : [],
                )
              }
            >
              <option value="">无</option>
              {data.columns.map((column) => (
                <option key={column.id} value={column.id}>
                  {column.displayValue}
                </option>
              ))}
            </select>
          </label>
          <label>
            <span>备择假设</span>
            <select
              value={draft.alternative}
              onChange={(e) =>
                update(
                  "alternative",
                  e.target.value as AnalysisPlanInput["alternative"],
                )
              }
            >
              <option value="TWO_SIDED">双侧</option>
              <option value="LESS">小于</option>
              <option value="GREATER">大于</option>
            </select>
          </label>
        </fieldset>

        <fieldset disabled={!editable || Boolean(pendingAction)}>
          <legend>样本筛选</legend>
          <label>
            <span>操作符</span>
            <select
              value={filterOperator}
              onChange={(e) => setFilterOperator(e.target.value)}
            >
              <option value="NONE">不筛选</option>
              <option value="EQUALS">等于</option>
              <option value="IN">包含于列表</option>
              <option value="IS_NULL">为空</option>
              <option value="IS_NOT_NULL">不为空</option>
              <option value="NUMERIC_RANGE">数值范围</option>
            </select>
          </label>
          {filter ? (
            <label>
              <span>筛选字段</span>
              <select
                value={filter.columnId}
                onChange={(e) =>
                  update("sampleFilter", {
                    ...filter,
                    columnId: e.target.value,
                  } as SampleFilter)
                }
              >
                {data.columns.map((column) => (
                  <option key={column.id} value={column.id}>
                    {column.displayValue}
                  </option>
                ))}
              </select>
            </label>
          ) : null}
          {filter?.operator === "EQUALS" ? (
            <label>
              <span>匹配值</span>
              <input
                value={String(filter.value)}
                onChange={(e) =>
                  update("sampleFilter", { ...filter, value: e.target.value })
                }
              />
            </label>
          ) : null}
          {filter?.operator === "IN" ? (
            <label className="m5-field-wide">
              <span>值列表（逗号分隔）</span>
              <input
                value={filter.values.join(", ")}
                onChange={(e) =>
                  update("sampleFilter", {
                    ...filter,
                    values: e.target.value
                      .split(",")
                      .map((value) => value.trim())
                      .filter(Boolean),
                  })
                }
              />
            </label>
          ) : null}
          {filter?.operator === "NUMERIC_RANGE" ? (
            <>
              <label>
                <span>最小值</span>
                <input
                  type="number"
                  value={filter.minimum ?? ""}
                  onChange={(e) =>
                    update("sampleFilter", {
                      ...filter,
                      minimum:
                        e.target.value === "" ? null : Number(e.target.value),
                    })
                  }
                />
              </label>
              <label>
                <span>最大值</span>
                <input
                  type="number"
                  value={filter.maximum ?? ""}
                  onChange={(e) =>
                    update("sampleFilter", {
                      ...filter,
                      maximum:
                        e.target.value === "" ? null : Number(e.target.value),
                    })
                  }
                />
              </label>
            </>
          ) : null}
        </fieldset>

        <fieldset
          className="m5-checkbox-fieldset"
          disabled={!editable || Boolean(pendingAction)}
        >
          <legend>确认与致谢</legend>
          <label>
            <input
              type="checkbox"
              checked={draft.independenceConfirmed}
              onChange={(e) =>
                update("independenceConfirmed", e.target.checked)
              }
            />
            <span>已确认观测独立性</span>
          </label>
          <label>
            <input
              type="checkbox"
              checked={draft.pairingConfirmed}
              onChange={(e) => update("pairingConfirmed", e.target.checked)}
            />
            <span>已确认配对关系</span>
          </label>
          {data.qualityWarnings.map((warning) => (
            <label key={warning}>
              <input
                type="checkbox"
                checked={draft.acknowledgedQualityIssueIds.includes(warning)}
                onChange={(e) =>
                  update(
                    "acknowledgedQualityIssueIds",
                    e.target.checked
                      ? [...draft.acknowledgedQualityIssueIds, warning]
                      : draft.acknowledgedQualityIssueIds.filter(
                          (item) => item !== warning,
                        ),
                  )
                }
              />
              <span>确认质量警告：{warning}</span>
            </label>
          ))}
          {data.columns
            .filter((column) => column.sensitive)
            .map((column) => (
              <label key={column.id}>
                <input
                  type="checkbox"
                  checked={draft.sensitiveColumnAcknowledgements.includes(
                    column.id,
                  )}
                  onChange={(e) =>
                    update(
                      "sensitiveColumnAcknowledgements",
                      e.target.checked
                        ? [...draft.sensitiveColumnAcknowledgements, column.id]
                        : draft.sensitiveColumnAcknowledgements.filter(
                            (item) => item !== column.id,
                          ),
                    )
                  }
                />
                <span>确认敏感字段使用：{column.displayValue}</span>
              </label>
            ))}
        </fieldset>

        <div className="m5-plan-actions">
          <CapabilityButton
            capability={
              plan ? data.capabilities.updatePlan : data.capabilities.createPlan
            }
            pending={
              pendingAction === "create-analysis-plan" ||
              pendingAction === "update-analysis-plan"
            }
            extraDisabled={!editable || Boolean(unsafeReason)}
            extraReason={
              !editable ? "当前计划状态只读。" : (unsafeReason ?? undefined)
            }
            onClick={onSave}
            variant="default"
            icon={<Save aria-hidden="true" />}
          >
            保存草稿
          </CapabilityButton>
          <CapabilityButton
            capability={data.capabilities.validatePlan}
            pending={pendingAction === "validate-analysis-plan"}
            extraDisabled={!plan || Boolean(unsafeReason)}
            extraReason={
              !plan ? "请先创建正式计划。" : (unsafeReason ?? undefined)
            }
            onClick={onValidate}
            icon={<CheckCircle2 aria-hidden="true" />}
          >
            验证计划
          </CapabilityButton>
          <CapabilityButton
            capability={data.capabilities.requestPlanApproval}
            pending={pendingAction === "request-analysis-approval"}
            extraDisabled={!plan || Boolean(unsafeReason)}
            extraReason={
              !plan ? "请先创建并验证正式计划。" : (unsafeReason ?? undefined)
            }
            onClick={onApproval}
            icon={<ShieldCheck aria-hidden="true" />}
          >
            请求审批
          </CapabilityButton>
          <CapabilityButton
            capability={data.capabilities.runAnalysis}
            pending={pendingAction === "run-analysis"}
            extraDisabled={!plan || Boolean(unsafeReason)}
            extraReason={
              !plan ? "没有可运行的正式计划。" : (unsafeReason ?? undefined)
            }
            onClick={onRun}
            icon={<Play aria-hidden="true" />}
          >
            运行分析
          </CapabilityButton>
        </div>
      </form>

      <section className="m5-column-context">
        <div className="m5-section-title">
          <div>
            <span className="m5-eyebrow">字段上下文</span>
            <h3>正式版本字段</h3>
          </div>
          <span>{data.columns.length} 个字段</span>
        </div>
        <div className="m5-column-list">
          {data.columns.map((column) => (
            <ColumnSummary key={column.id} column={column} />
          ))}
        </div>
      </section>
    </div>
  )
}

function AssumptionsView({
  data,
  draft,
  setDraft,
}: {
  data: AnalysisWorkspaceViewModel
  draft: AnalysisPlanInput
  setDraft: (draft: AnalysisPlanInput) => void
}) {
  const checks = data.plan?.checks ?? []
  if (!data.plan)
    return (
      <LoadableState
        state="empty"
        title="尚无前提检查"
        message="创建并验证分析计划后，服务端检查会显示在这里。"
      />
    )
  const order = ["FAILED", "REQUIRES_USER_CONFIRMATION", "WARNING", "PASSED"]
  const sorted = [...checks].sort(
    (a, b) => order.indexOf(a.status) - order.indexOf(b.status),
  )
  return (
    <div className="m5-view-stack" data-od-id="analysis-assumptions-surface">
      <section className="m5-surface-heading">
        <div>
          <span className="m5-eyebrow">Assumption checks</span>
          <h2>前提检查</h2>
          <p>确认只更新本地计划草稿，不会把服务端检查改为通过。</p>
        </div>
        <StatusBadge label={`${checks.length} 项`} tone="info" />
      </section>
      <div className="m5-check-list">
        {sorted.map((check) => {
          const confirmed = draft.assumptionConfirmations.includes(check.id)
          return (
            <article
              key={check.id}
              className="m5-check-row"
              data-blocking={check.blocksApproval || undefined}
            >
              <StatusBadge
                label={statusLabel(check.status, check.knownStatus)}
                tone={check.tone}
              />
              <div className="m5-check-row__content">
                <strong>{check.code}</strong>
                <span className="m5-mono-wrap">{check.subjectKey}</span>
                <p>{check.explanation}</p>
                <small>
                  {new Date(check.checkedAt).toLocaleString("zh-CN")}
                </small>
              </div>
              <div className="m5-check-row__flags">
                {check.blocksApproval ? (
                  <span>
                    <LockKeyhole aria-hidden="true" /> 阻止审批
                  </span>
                ) : (
                  <span>
                    <Info aria-hidden="true" /> 不阻止审批
                  </span>
                )}
                {check.requiresConfirmation ? (
                  <label>
                    <input
                      type="checkbox"
                      checked={confirmed}
                      onChange={(e) =>
                        setDraft({
                          ...draft,
                          assumptionConfirmations: e.target.checked
                            ? [...draft.assumptionConfirmations, check.id]
                            : draft.assumptionConfirmations.filter(
                                (id) => id !== check.id,
                              ),
                        })
                      }
                    />
                    <span>加入确认草稿</span>
                  </label>
                ) : null}
              </div>
            </article>
          )
        })}
      </div>
    </div>
  )
}

function RunsView({
  data,
  pendingAction,
  onRetryJob,
  onCancelJob,
  onInvalidate,
}: {
  data: AnalysisWorkspaceViewModel
  pendingAction: AnalysisWorkspaceWorkspaceProps["pendingAction"]
  onRetryJob: () => void
  onCancelJob: () => void
  onInvalidate: () => void
}) {
  if (!data.run && !data.job)
    return (
      <LoadableState
        state="empty"
        title="尚无分析运行"
        message="已批准的计划运行后，Job 和不可变运行记录会显示在这里。"
      />
    )
  return (
    <div className="m5-view-stack" data-od-id="analysis-runs-surface">
      <section className="m5-surface-heading">
        <div>
          <span className="m5-eyebrow">AnalysisRun</span>
          <h2>运行与 Job</h2>
          <p>Event 只表达意图；pending 不会在本地生成 Result。</p>
        </div>
        {data.run ? (
          <StatusBadge
            label={statusLabel(data.run.status, data.run.knownStatus)}
            tone={data.run.tone}
          />
        ) : null}
      </section>
      {data.job ? (
        <JobProgress
          label={data.job.kind === "ANALYSIS" ? "分析任务" : "任务"}
          statusLabel={statusLabel(data.job.status, data.job.knownStatus)}
          tone={data.job.tone}
          progress={data.job.progress}
          step={data.job.currentStep}
        />
      ) : null}
      <div className="m5-run-grid">
        <section className="m5-detail-panel">
          <h3>运行事实</h3>
          <MetadataList
            items={[
              { label: "运行编号", value: data.run?.runNumber ?? "未提供" },
              {
                label: "有效 N",
                value: data.run?.effectiveN ?? "未提供",
                mono: true,
              },
              { label: "结果数量", value: data.run?.resultCount ?? 0 },
              {
                label: "错误代码",
                value: data.run?.errorCode ?? data.job?.errorCode ?? "无",
                mono: true,
              },
              { label: "可重试", value: data.job?.retryable ? "是" : "否" },
              {
                label: "输入 hash",
                value: shortHash(data.run?.inputHash ?? null),
                mono: true,
              },
            ]}
          />
        </section>
        <section className="m5-detail-panel">
          <h3>执行环境</h3>
          {data.run ? (
            <MetadataList
              items={Object.entries(data.run.environment).map(
                ([label, value]) => ({ label, value, mono: true }),
              )}
            />
          ) : (
            <p>未提供环境信息。</p>
          )}
        </section>
      </div>
      <div className="m5-plan-actions">
        <CapabilityButton
          capability={data.capabilities.retryJob}
          pending={pendingAction === "retry-job"}
          extraDisabled={!data.job?.retryable}
          extraReason={
            data.job
              ? "该 Job 不可重试或缺少正式允许动作。"
              : "没有可重试的 Job。"
          }
          onClick={onRetryJob}
          icon={<RefreshCw aria-hidden="true" />}
        >
          重试 Job
        </CapabilityButton>
        <CapabilityButton
          capability={data.capabilities.cancelJob}
          pending={pendingAction === "cancel-job"}
          extraDisabled={!data.job}
          extraReason="没有可取消的 Job。"
          onClick={onCancelJob}
          icon={<Square aria-hidden="true" />}
        >
          取消 Job
        </CapabilityButton>
        <CapabilityButton
          capability={data.capabilities.invalidateRun}
          pending={pendingAction === "invalidate-analysis-run"}
          extraDisabled={!data.run}
          extraReason="没有可失效的运行。"
          onClick={onInvalidate}
          variant="destructive"
          icon={<XCircle aria-hidden="true" />}
        >
          使运行失效
        </CapabilityButton>
      </div>
    </div>
  )
}

function ResultsView({ data }: { data: AnalysisWorkspaceViewModel }) {
  return (
    <div className="m5-view-stack" data-od-id="analysis-results-surface">
      <section className="m5-surface-heading">
        <div>
          <span className="m5-eyebrow">Immutable results</span>
          <h2>结构化分析结果</h2>
          <p>显示格式可调整，原始数值、显著性和正式状态不会在界面中重算。</p>
        </div>
        <StatusBadge
          label={`${data.results.length} 项结果`}
          tone={data.results.length ? "success" : "neutral"}
        />
      </section>
      {data.suggestions.map((suggestion, index) => (
        <DegradedNotice
          key={`${suggestion.kind}-${index}`}
          title={`${suggestion.kind} 建议不可用`}
          message={suggestion.reason}
        />
      ))}
      {data.results.length ? (
        <div className="m5-result-list">
          {data.results.map((result) => (
            <AnalysisResultCard key={result.id} result={result} />
          ))}
        </div>
      ) : (
        <LoadableState
          state="empty"
          title="尚无不可变结果"
          message="分析完成并由服务端返回结构化结果后，会显示在这里。"
        />
      )}
    </div>
  )
}

function Inspector({ data }: { data: AnalysisWorkspaceViewModel }) {
  return (
    <div className="m5-inspector__inner" data-od-id="analysis-inspector">
      <InspectorSection title="数据版本">
        <MetadataList
          items={[
            {
              label: "版本",
              value: data.dataset ? `v${data.dataset.versionNumber}` : "未选择",
            },
            {
              label: "data hash",
              value: shortHash(data.dataset?.dataHash ?? null),
              mono: true,
            },
            {
              label: "schema hash",
              value: shortHash(data.dataset?.schemaHash ?? null),
              mono: true,
            },
            {
              label: "projection hash",
              value: shortHash(data.dataset?.projectionHash ?? null),
              mono: true,
            },
          ]}
        />
      </InspectorSection>
      <InspectorSection title="审批">
        {data.approval ? (
          <>
            <StatusBadge
              label={statusLabel(
                data.approval.status,
                data.approval.knownStatus,
              )}
              tone={data.approval.tone}
            />
            <MetadataList
              items={[
                { label: "stale", value: data.approval.stale ? "是" : "否" },
                {
                  label: "expired",
                  value: data.approval.expired ? "是" : "否",
                },
                {
                  label: "payload hash",
                  value: shortHash(data.approval.payloadHash),
                  mono: true,
                },
                {
                  label: "说明",
                  value: data.approval.decisionReason ?? "未提供",
                },
              ]}
            />
          </>
        ) : (
          <p>未提供独立审批对象。</p>
        )}
      </InspectorSection>
      <InspectorSection title="权限与范围">
        <StatusBadge
          label={data.capabilities.permissionsKnown ? "权限已知" : "权限未知"}
          tone={data.capabilities.permissionsKnown ? "success" : "unknown"}
        />
        <div className="m5-scope-list">
          {data.readScopes.map((scope) => (
            <code key={scope}>{scope}</code>
          ))}
        </div>
      </InspectorSection>
      {data.qualityWarnings.length ? (
        <InspectorSection title="质量警告">
          <ul className="m5-warning-list">
            {data.qualityWarnings.map((warning) => (
              <li key={warning}>
                <AlertTriangle aria-hidden="true" />
                {warning}
              </li>
            ))}
          </ul>
        </InspectorSection>
      ) : null}
      {data.integrationPending.length ? (
        <InspectorSection title="接入状态">
          <ul className="m5-plain-list">
            {data.integrationPending.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </InspectorSection>
      ) : null}
    </div>
  )
}

export function AnalysisWorkspace(props: AnalysisWorkspaceWorkspaceProps) {
  const visualTheme = useVisualTheme() ?? "light"
  const readyData = props.content.state === "ready" ? props.content.data : null
  const [view, setView] = useState<AnalysisWorkspaceRouteView>(
    props.initialView ?? "plan",
  )
  const [draft, setDraft] = useState<AnalysisPlanInput | null>(
    readyData ? (readyData.plan?.input ?? defaultPlan(readyData)) : null,
  )
  const [navOpen, setNavOpen] = useState(false)
  const [inspectorOpen, setInspectorOpen] = useState(false)
  const [cancelOpen, setCancelOpen] = useState(false)
  const [invalidateOpen, setInvalidateOpen] = useState(false)
  const [reason, setReason] = useState("")
  const returnFocusRef = useRef<HTMLElement | null>(null)

  const rememberTrigger = () => {
    returnFocusRef.current = document.activeElement as HTMLElement | null
  }

  const restoreTriggerFocus = (event: Event) => {
    event.preventDefault()
    returnFocusRef.current?.focus()
  }

  useEffect(() => {
    if (!readyData) return
    setDraft(readyData.plan?.input ?? defaultPlan(readyData))
  }, [readyData?.plan?.id, readyData?.dataset?.versionId])

  useEffect(() => {
    if (props.initialView) setView(props.initialView)
  }, [props.initialView])

  const selectView = (next: AnalysisWorkspaceRouteView) => {
    setView(next)
    props.onViewChange?.(next)
    setNavOpen(false)
  }

  if (props.content.state === "loading") {
    return (
      <div
        className="m5-analysis-workspace reca-visual-refresh"
        data-theme={visualTheme}
        aria-busy="true"
        data-od-id="analysis-workspace"
      >
        <WorkspaceHeader
          title="分析与图表"
          context="Analysis Workspace"
          metadata={<StatusBadge label="正在加载" tone="info" />}
        />
        <div
          className="reca-notice reca-notice--degraded m5-loading-notice-placeholder"
          aria-hidden="true"
        >
          <AlertTriangle />
          <div>
            <div className="reca-notice__title">结果已降级</div>
            <p className="reca-notice__message">
              建议提供方不可用；确定性分析事实仍可阅读。
            </p>
          </div>
        </div>
        <div
          className="m5-mobile-view-selector m5-mobile-view-selector--loading"
          aria-hidden="true"
        >
          <label>
            <span>当前视图</span>
            <select disabled>
              <option>分析计划</option>
            </select>
          </label>
        </div>
        <WorkspaceLoadingSkeleton
          layout="three-pane"
          state="loading"
          title="正在加载分析工作台"
          message={props.content.label}
        />
      </div>
    )
  }

  if (props.content.state === "error") {
    const error = props.content.error
    return (
      <div
        className="m5-analysis-workspace reca-visual-refresh m5-analysis-workspace--state"
        data-theme={visualTheme}
        data-od-id="analysis-workspace"
      >
        <WorkspaceHeader title="分析与图表" context="Analysis Workspace" />
        <LoadableState
          state={error.forbidden || error.notFound ? "forbidden" : "error"}
          title={error.title}
          message={error.message}
          action={
            error.retryable ? (
              <Button type="button" variant="outline" onClick={props.onRetry}>
                重试
              </Button>
            ) : undefined
          }
        />
      </div>
    )
  }

  if (props.content.state === "empty") {
    return (
      <div
        className="m5-analysis-workspace reca-visual-refresh m5-analysis-workspace--state"
        data-theme={visualTheme}
        data-od-id="analysis-workspace"
      >
        <WorkspaceHeader title="分析与图表" context="Analysis Workspace" />
        <LoadableState
          state="empty"
          title="尚无分析上下文"
          message={props.content.message}
        />
      </div>
    )
  }

  const data = props.content.data
  const planDraft = draft ?? defaultPlan(data)
  const planEditable =
    !data.plan || ["DRAFT", "NEEDS_INPUT", "READY"].includes(data.plan.status)
  const unconfirmed = data.columns.filter(
    (column) => !column.confirmed || !column.confirmationKnown,
  )
  const sensitiveUnacknowledged = data.columns.filter(
    (column) =>
      column.sensitive &&
      !planDraft.sensitiveColumnAcknowledgements.includes(column.id),
  )
  const unsafeReason = !data.dataset?.available
    ? "正式数据版本不可用。"
    : unconfirmed.length
      ? `存在 ${unconfirmed.length} 个未确认字段。`
      : sensitiveUnacknowledged.length
        ? `存在 ${sensitiveUnacknowledged.length} 个敏感字段尚未确认。`
        : null

  const savePlan = () => {
    if (data.plan)
      props.onEvent({
        action: "update-analysis-plan",
        input: {
          planId: data.plan.id,
          lockVersion: data.plan.lockVersion,
          plan: planDraft,
        },
      })
    else props.onEvent({ action: "create-analysis-plan", input: planDraft })
  }

  const mainView =
    view === "plan" ? (
      <PlanView
        data={data}
        draft={planDraft}
        setDraft={setDraft}
        editable={planEditable}
        unsafeReason={unsafeReason}
        pendingAction={props.pendingAction}
        onSave={savePlan}
        onValidate={() =>
          data.plan &&
          props.onEvent({
            action: "validate-analysis-plan",
            input: { planId: data.plan.id },
          })
        }
        onApproval={() =>
          data.plan &&
          props.onEvent({
            action: "request-analysis-approval",
            input: { planId: data.plan.id },
          })
        }
        onRun={() =>
          data.plan &&
          props.onEvent({
            action: "run-analysis",
            input: { planId: data.plan.id, reason: null },
          })
        }
      />
    ) : view === "assumptions" ? (
      <AssumptionsView data={data} draft={planDraft} setDraft={setDraft} />
    ) : view === "runs" ? (
      <RunsView
        data={data}
        pendingAction={props.pendingAction}
        onRetryJob={() =>
          data.job &&
          props.onEvent({ action: "retry-job", input: { jobId: data.job.id } })
        }
        onCancelJob={() => {
          rememberTrigger()
          setReason("")
          setCancelOpen(true)
        }}
        onInvalidate={() => {
          rememberTrigger()
          setReason("")
          setInvalidateOpen(true)
        }}
      />
    ) : view === "results" ? (
      <ResultsView data={data} />
    ) : (
      <FigureWorkspace
        data={data}
        pendingAction={props.pendingAction}
        onEvent={props.onEvent}
      />
    )

  return (
    <div
      className="m5-analysis-workspace reca-visual-refresh"
      data-theme={visualTheme}
      data-view={view}
      data-od-id="analysis-workspace"
    >
      <WorkspaceHeader
        title="分析与图表"
        context={
          data.dataset
            ? `${data.dataset.datasetName} · v${data.dataset.versionNumber}`
            : "未选择数据集"
        }
        metadata={
          <div className="m5-header-status">
            <StatusBadge
              label={
                data.plan
                  ? statusLabel(data.plan.status, data.plan.knownStatus)
                  : "无计划"
              }
              tone={data.plan?.tone ?? "neutral"}
            />
            {data.run ? (
              <StatusBadge
                label={statusLabel(data.run.status, data.run.knownStatus)}
                tone={data.run.tone}
              />
            ) : null}
          </div>
        }
        actions={
          <div className="m5-header-actions">
            <Button
              type="button"
              size="icon-sm"
              variant="ghost"
              className="m5-mobile-action"
              aria-label="打开工作台导航"
              title="打开工作台导航"
              onClick={() => {
                rememberTrigger()
                setNavOpen(true)
              }}
            >
              <Menu aria-hidden="true" />
            </Button>
            <Button
              type="button"
              size="icon-sm"
              variant="ghost"
              className="m5-tablet-action"
              aria-label="打开 Inspector"
              title="打开 Inspector"
              onClick={() => {
                rememberTrigger()
                setInspectorOpen(true)
              }}
            >
              <PanelRight aria-hidden="true" />
            </Button>
          </div>
        }
      />

      {!data.capabilities.permissionsKnown ? (
        <PermissionNotice
          title="权限状态未知"
          reason="所有相关写操作保持禁用，直到服务端提供正式权限投影。"
        />
      ) : null}
      {!data.plan?.knownStatus && data.plan ? (
        <PermissionNotice
          title="计划状态未知"
          reason="未知状态不会映射为任何已知状态，相关写操作保持禁用。"
        />
      ) : null}
      {data.suggestions.some((item) => item.availability === "DEGRADED") &&
      view !== "results" ? (
        <DegradedNotice message="建议提供方不可用；确定性分析事实仍可阅读。" />
      ) : null}
      {props.mutationError ? (
        <MutationError
          message={props.mutationError.message}
          code={props.mutationError.code}
          requestId={props.mutationError.requestId}
          retryable={props.mutationError.retryable}
          onRetry={props.onRetry}
        />
      ) : null}

      <div className="m5-mobile-view-selector">
        <label>
          <span>当前视图</span>
          <select
            value={view}
            onChange={(e) =>
              selectView(e.target.value as AnalysisWorkspaceRouteView)
            }
          >
            {views.map((item) => (
              <option key={item.id} value={item.id}>
                {item.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="m5-workspace-grid">
        <aside className="m5-context-rail">
          <DatasetRail data={data} view={view} onView={selectView} />
        </aside>
        <main className="m5-main-pane">{mainView}</main>
        <aside className="m5-inspector">
          <Inspector data={data} />
        </aside>
      </div>

      <Sheet open={navOpen} onOpenChange={setNavOpen}>
        <SheetContent
          side="left"
          className="m5-sheet-content"
          onCloseAutoFocus={restoreTriggerFocus}
        >
          <SheetHeader>
            <SheetTitle>分析工作台导航</SheetTitle>
            <SheetDescription>
              视图选择只改变当前展示，不改变正式业务状态。
            </SheetDescription>
          </SheetHeader>
          <DatasetRail data={data} view={view} onView={selectView} />
        </SheetContent>
      </Sheet>
      <Sheet open={inspectorOpen} onOpenChange={setInspectorOpen}>
        <SheetContent
          side="right"
          className="m5-sheet-content"
          onCloseAutoFocus={restoreTriggerFocus}
        >
          <SheetHeader>
            <SheetTitle>Inspector</SheetTitle>
            <SheetDescription>
              只读展示正式数据、审批、权限和 hash。
            </SheetDescription>
          </SheetHeader>
          <Inspector data={data} />
        </SheetContent>
      </Sheet>

      <Dialog open={cancelOpen} onOpenChange={setCancelOpen}>
        <DialogContent
          className="m5-dialog"
          data-od-id="cancel-analysis-job-dialog"
          onCloseAutoFocus={restoreTriggerFocus}
        >
          <DialogHeader>
            <DialogTitle>取消分析 Job</DialogTitle>
            <DialogDescription>
              该操作只发送取消意图。当前 Job 状态不会在本地改变。
            </DialogDescription>
          </DialogHeader>
          <label className="m5-dialog-field">
            <span>取消原因</span>
            <textarea
              autoFocus
              required
              value={reason}
              onChange={(e) => setReason(e.target.value)}
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
              disabled={!reason.trim() || props.pendingAction === "cancel-job"}
              onClick={() => {
                if (data.job && reason.trim()) {
                  props.onEvent({
                    action: "cancel-job",
                    input: { jobId: data.job.id, reason: reason.trim() },
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
      <Dialog open={invalidateOpen} onOpenChange={setInvalidateOpen}>
        <DialogContent
          className="m5-dialog"
          data-od-id="invalidate-analysis-run-dialog"
          onCloseAutoFocus={restoreTriggerFocus}
        >
          <DialogHeader>
            <DialogTitle>使分析运行失效</DialogTitle>
            <DialogDescription>
              历史运行和结果仍会保留。必须由服务端确认后，正式状态才会变化。
            </DialogDescription>
          </DialogHeader>
          <label className="m5-dialog-field">
            <span>失效原因</span>
            <textarea
              autoFocus
              required
              value={reason}
              onChange={(e) => setReason(e.target.value)}
            />
          </label>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setInvalidateOpen(false)}
            >
              返回
            </Button>
            <Button
              type="button"
              variant="destructive"
              disabled={
                !reason.trim() ||
                props.pendingAction === "invalidate-analysis-run"
              }
              onClick={() => {
                if (data.run && reason.trim()) {
                  props.onEvent({
                    action: "invalidate-analysis-run",
                    input: { runId: data.run.id, reason: reason.trim() },
                  })
                  setInvalidateOpen(false)
                }
              }}
            >
              确认发送
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
