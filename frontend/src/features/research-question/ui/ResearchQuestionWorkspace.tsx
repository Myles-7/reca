import {
  CheckCircle2,
  FilePlus2,
  History,
  LockKeyhole,
  Save,
  Send,
} from "lucide-react"
import type { FormEvent, ReactNode } from "react"

import {
  DegradedNotice,
  EmptyState,
  InspectorSection,
  LoadableState,
  MetadataList,
  MutationError,
  PermissionNotice,
  SectionHeader,
  SourceBadge,
  StatusBadge,
  useVisualTheme,
  WorkspaceHeader,
  WorkspaceLoadingFrame,
} from "@/components/reca-visual-refresh"
import "@/components/reca-visual-refresh/visual-refresh.css"

import type {
  CapabilityState,
  ResearchQuestionCapabilityAvailability,
  ResearchQuestionFields,
  ResearchQuestionViewModel,
} from "../model"
import type { ResearchQuestionWorkspaceProps } from "./contracts"
import "./research-question-workspace.css"

type FieldName =
  | "normalizedQuestion"
  | "researchObject"
  | "population"
  | "context"

const FIELD_DEFINITIONS: readonly {
  name: FieldName
  label: string
  description: string
}[] = [
  {
    name: "normalizedQuestion",
    label: "规范化问题",
    description: "当前版本的结构化问题表述",
  },
  {
    name: "researchObject",
    label: "研究对象",
    description: "研究关注的主体或现象",
  },
  {
    name: "population",
    label: "研究人群",
    description: "样本或目标人群范围",
  },
  {
    name: "context",
    label: "研究情境",
    description: "研究发生的制度、环境或场景",
  },
]

const CAPABILITY_LABELS = {
  researchQuestion: "Research Question",
  aiParse: "AI Parse",
  queryPlan: "Query Plan",
  literature: "Literature",
} satisfies Record<keyof ResearchQuestionCapabilityAvailability, string>

function optionalText(value: FormDataEntryValue | null): string | null {
  const normalized = String(value ?? "").trim()
  return normalized || null
}

function listValue(value: FormDataEntryValue | null): string[] {
  return String(value ?? "")
    .split(/[\n,，]/)
    .map((item) => item.trim())
    .filter(Boolean)
}

function formatList(items: readonly string[]): string {
  return items.join("，")
}

function statusLabel(status: string, known: boolean): string {
  if (!known) return "未知状态"
  const labels: Record<string, string> = {
    DRAFT: "草稿",
    NEEDS_INPUT: "需要补充",
    READY: "待确认",
    CONFIRMED: "已确认",
    SUPERSEDED: "已被新版本替代",
  }
  return labels[status] ?? status
}

function goalLabel(value: ResearchQuestionFields["researchGoal"]): string {
  const labels = {
    DESCRIBE: "描述",
    COMPARE: "比较",
    RELATE: "关联",
    PREDICT: "预测",
  } as const
  return value ? labels[value] : "未指定"
}

function relationshipLabel(
  value: ResearchQuestionFields["relationshipType"],
): string {
  const labels = {
    ASSOCIATION: "关联",
    COMPARISON: "比较",
    PREDICTION: "预测",
    UNSPECIFIED: "未指定",
  } as const
  return value ? labels[value] : "未指定"
}

function capabilityPresentation(state: CapabilityState) {
  if (state === "AVAILABLE") {
    return { label: "可用", tone: "info" }
  }
  if (state === "NOT_AVAILABLE") {
    return { label: "不可用", tone: "neutral" }
  }
  return { label: "状态未知", tone: "unknown" }
}

function metadataValue(value: Readonly<Record<string, unknown>> | null) {
  if (!value || Object.keys(value).length === 0) {
    return <span className="rq-empty-value">未提供</span>
  }
  return (
    <dl className="rq-structured-metadata">
      {Object.entries(value).map(([key, item]) => (
        <div key={key}>
          <dt>{key.replace(/_/g, " ")}</dt>
          <dd>{readableMetadataValue(item)}</dd>
        </div>
      ))}
    </dl>
  )
}

function readableMetadataValue(value: unknown): string {
  if (value === null || value === undefined) return "未提供"
  if (Array.isArray(value)) {
    return value.map(readableMetadataValue).join("，")
  }
  if (typeof value === "object") {
    return Object.entries(value as Record<string, unknown>)
      .map(
        ([key, item]) =>
          `${key.replace(/_/g, " ")}：${readableMetadataValue(item)}`,
      )
      .join("；")
  }
  if (typeof value === "boolean") return value ? "是" : "否"
  return String(value)
}

function ActionButton({
  label,
  pendingLabel,
  pending,
  primary = false,
  disabled,
  reason,
  icon,
  type = "button",
  form,
  onClick,
}: {
  label: string
  pendingLabel: string
  pending: boolean
  primary?: boolean
  disabled: boolean
  reason: string | null
  icon: ReactNode
  type?: "button" | "submit"
  form?: string
  onClick?: () => void
}) {
  return (
    <button
      type={type}
      form={form}
      className={`rq-button${primary ? " rq-button--primary" : ""}`}
      disabled={disabled}
      title={reason ?? label}
      onClick={onClick}
    >
      {icon}
      <span>{pending ? pendingLabel : label}</span>
    </button>
  )
}

function CapabilityList({
  capabilities,
}: {
  capabilities: ResearchQuestionCapabilityAvailability
}) {
  return (
    <div className="rq-capability-list">
      {(
        Object.keys(CAPABILITY_LABELS) as Array<keyof typeof CAPABILITY_LABELS>
      ).map((key) => {
        const presentation = capabilityPresentation(capabilities[key])
        return (
          <div key={key} className="rq-capability-row">
            <span>{CAPABILITY_LABELS[key]}</span>
            <StatusBadge label={presentation.label} tone={presentation.tone} />
          </div>
        )
      })}
    </div>
  )
}

function CreateWorkspace({ props }: { props: ResearchQuestionWorkspaceProps }) {
  const visualTheme = useVisualTheme()
  const pending = props.pendingAction !== null
  const capability = props.capabilities.researchQuestion
  const canCreate = props.canCreate && capability === "AVAILABLE"
  const disabledReason = !props.canCreate
    ? "服务端未授予创建 Research Question 的能力。"
    : capability === "NOT_AVAILABLE"
      ? "Research Question capability 当前不可用。"
      : capability === "UNKNOWN"
        ? "Capability 状态未知，创建操作已安全禁用。"
        : null

  const create = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!canCreate || pending) return
    const form = new FormData(event.currentTarget)
    const rawInput = String(form.get("rawInput") ?? "").trim()
    if (!rawInput) return
    props.onEvent({ action: "create", input: { rawInput } })
  }

  return (
    <div
      className="reca-visual-refresh rq-workspace"
      data-theme={visualTheme}
      data-od-id="research-question-workspace-empty"
    >
      <WorkspaceHeader
        title="Research Question"
        context="尚未创建"
        metadata={<StatusBadge label="未创建" tone="neutral" />}
      />
      <div className="rq-empty-layout">
        <main className="rq-empty-main">
          <EmptyState
            title="从原始研究想法开始"
            message="创建事件只提交用户输入；正式版本号、状态和结构化字段由服务端决定。"
          />
          {disabledReason ? (
            <PermissionNotice title="当前无法创建" reason={disabledReason} />
          ) : null}
          <form className="rq-create-form" onSubmit={create}>
            <label htmlFor="rq-create-raw-input">
              <span>用户原始输入</span>
              <small>保留问题的原始措辞，不自动改写为正式版本。</small>
            </label>
            <textarea
              id="rq-create-raw-input"
              name="rawInput"
              required
              readOnly={!canCreate || pending}
              placeholder="输入研究对象、关系、范围与约束"
            />
            <ActionButton
              label="创建 Research Question"
              pendingLabel="正在提交…"
              pending={props.pendingAction === "create"}
              primary
              disabled={!canCreate || pending}
              reason={disabledReason}
              icon={<FilePlus2 aria-hidden="true" />}
              type="submit"
            />
          </form>
        </main>
        <aside className="rq-empty-inspector" aria-label="Capability 状态">
          <InspectorSection title="Capability availability">
            <CapabilityList capabilities={props.capabilities} />
          </InspectorSection>
        </aside>
      </div>
    </div>
  )
}

function VersionHistory({ question }: { question: ResearchQuestionViewModel }) {
  return (
    <ol className="rq-version-list">
      {question.versions.map((version) => {
        const superseded = version.status === "SUPERSEDED" || !version.isCurrent
        return (
          <li
            key={version.id}
            className={`${version.isCurrent ? "is-current" : ""}${
              superseded ? " is-superseded" : ""
            }`}
          >
            <div className="rq-version-list__heading">
              <strong>版本 {version.versionNumber}</strong>
              <StatusBadge
                label={statusLabel(version.status, version.knownStatus)}
                tone={version.knownStatus ? version.tone : "unknown"}
              />
            </div>
            <div className="rq-version-list__meta">
              <span>{version.createdAt}</span>
              <span>{version.isCurrent ? "当前版本" : "只读历史"}</span>
            </div>
            <code>{version.id}</code>
          </li>
        )
      })}
    </ol>
  )
}

function ResearchQuestionEditor({
  question,
  editable,
  onSave,
}: {
  question: ResearchQuestionViewModel
  editable: boolean
  onSave: (event: FormEvent<HTMLFormElement>) => void
}) {
  const fields = question.fields
  return (
    <form
      id="rq-version-form"
      key={question.currentVersionId}
      className="rq-editor"
      onSubmit={onSave}
    >
      <section className="rq-editor-section" data-od-id="rq-raw-input-section">
        <SectionHeader
          title="用户原始输入"
          description="原始措辞作为版本依据保存，不与结构化结果混合。"
          actions={<SourceBadge label="User input" kind="human-decision" />}
        />
        <label className="rq-field rq-field--stacked" htmlFor="rq-raw-input">
          <span>rawInput</span>
          <textarea
            id="rq-raw-input"
            name="rawInput"
            defaultValue={fields.rawInput}
            readOnly={!editable}
            required
          />
        </label>
      </section>

      <section
        className="rq-editor-section"
        data-od-id="rq-structured-question-section"
      >
        <SectionHeader
          title="结构化问题"
          description="当前契约没有来源投影，因此不会把规范化字段标记为 AI 已确认内容。"
          actions={<SourceBadge label="来源未投影" kind="unknown" />}
        />
        <div className="rq-label-grid">
          {FIELD_DEFINITIONS.map((field) => (
            <label key={field.name} className="rq-field">
              <span>
                <strong>{field.label}</strong>
                <small>{field.description}</small>
              </span>
              {field.name === "normalizedQuestion" ? (
                <textarea
                  name={field.name}
                  defaultValue={fields[field.name] ?? ""}
                  readOnly={!editable}
                />
              ) : (
                <input
                  name={field.name}
                  defaultValue={fields[field.name] ?? ""}
                  readOnly={!editable}
                />
              )}
            </label>
          ))}
        </div>
      </section>

      <section className="rq-editor-section" data-od-id="rq-variable-section">
        <SectionHeader
          title="变量与关系"
          description="列表支持逗号或换行分隔；本地编辑不会改变当前正式版本。"
        />
        <div className="rq-label-grid">
          <label className="rq-field">
            <span>
              <strong>自变量</strong>
              <small>independentVariables</small>
            </span>
            <textarea
              name="independentVariables"
              defaultValue={formatList(fields.independentVariables)}
              readOnly={!editable}
            />
          </label>
          <label className="rq-field">
            <span>
              <strong>因变量</strong>
              <small>dependentVariables</small>
            </span>
            <textarea
              name="dependentVariables"
              defaultValue={formatList(fields.dependentVariables)}
              readOnly={!editable}
            />
          </label>
          <label className="rq-field">
            <span>
              <strong>控制变量</strong>
              <small>controlVariables</small>
            </span>
            <textarea
              name="controlVariables"
              defaultValue={formatList(fields.controlVariables)}
              readOnly={!editable}
            />
          </label>
          <label className="rq-field">
            <span>
              <strong>研究目标</strong>
              <small>{goalLabel(fields.researchGoal)}</small>
            </span>
            <select
              name="researchGoal"
              defaultValue={fields.researchGoal ?? ""}
              disabled={!editable}
            >
              <option value="">未指定</option>
              <option value="DESCRIBE">描述</option>
              <option value="COMPARE">比较</option>
              <option value="RELATE">关联</option>
              <option value="PREDICT">预测</option>
            </select>
          </label>
          <label className="rq-field">
            <span>
              <strong>关系类型</strong>
              <small>{relationshipLabel(fields.relationshipType)}</small>
            </span>
            <select
              name="relationshipType"
              defaultValue={fields.relationshipType ?? ""}
              disabled={!editable}
            >
              <option value="">未指定</option>
              <option value="ASSOCIATION">关联</option>
              <option value="COMPARISON">比较</option>
              <option value="PREDICTION">预测</option>
              <option value="UNSPECIFIED">未指定关系</option>
            </select>
          </label>
        </div>
      </section>

      <section className="rq-editor-section" data-od-id="rq-scope-section">
        <SectionHeader
          title="方法与范围"
          description="保留服务端结构化 metadata，不以原始 JSON 字符串展示。"
        />
        <div className="rq-metadata-grid">
          <div>
            <h3>方法偏好</h3>
            {metadataValue(fields.methodPreference)}
          </div>
          <div>
            <h3>时间范围</h3>
            {metadataValue(fields.timeScope)}
          </div>
          <div>
            <h3>区域范围</h3>
            {metadataValue(fields.regionScope)}
          </div>
          <div>
            <h3>语言范围</h3>
            {metadataValue(fields.languageScope)}
          </div>
        </div>
      </section>

      <section
        className="rq-editor-section"
        data-od-id="rq-constraints-section"
      >
        <SectionHeader
          title="资源、伦理与不确定性"
          description="约束使用稳定 definition list；不确定性不是已确认事实。"
        />
        <div className="rq-metadata-grid rq-metadata-grid--three">
          <div>
            <h3>资源约束</h3>
            {metadataValue(fields.resourceConstraints)}
          </div>
          <div>
            <h3>伦理约束</h3>
            {metadataValue(fields.ethicalConstraints)}
          </div>
          <div>
            <h3>不确定性</h3>
            {metadataValue(fields.uncertainties)}
          </div>
        </div>
      </section>

      <section className="rq-change-reason" data-od-id="rq-change-reason">
        <label htmlFor="rq-change-reason-input">
          <span>
            <strong>版本变更原因</strong>
            <small>
              新版本将明确基于 {question.currentVersionId}
              ；本地编辑本身不会推进版本。
            </small>
          </span>
          <input
            id="rq-change-reason-input"
            name="changeReason"
            required
            readOnly={!editable}
            placeholder="说明本次范围、变量或约束调整"
          />
        </label>
      </section>
    </form>
  )
}

export function ResearchQuestionWorkspace(
  props: ResearchQuestionWorkspaceProps,
) {
  const visualTheme = useVisualTheme()
  if (props.content.state === "loading") {
    return (
      <div
        className="reca-visual-refresh rq-workspace rq-workspace--loadable"
        data-theme={visualTheme}
        data-od-id="research-question-workspace-loading"
      >
        <WorkspaceHeader
          title="Research Question"
          context="RECA / Research Question"
        />
        <WorkspaceLoadingFrame layout="dual-pane">
          <LoadableState
            state="loading"
            title="正在加载 Research Question"
            message="正在读取版本、权限和 capability；布局将保持稳定。"
          />
        </WorkspaceLoadingFrame>
      </div>
    )
  }

  if (props.content.state === "error") {
    const error = props.content.error
    return (
      <div
        className="reca-visual-refresh rq-workspace rq-workspace--loadable"
        data-theme={visualTheme}
        data-od-id="research-question-workspace-error"
      >
        <WorkspaceHeader
          title="Research Question"
          context="RECA / Research Question"
        />
        <WorkspaceLoadingFrame layout="dual-pane">
          <LoadableState
            state={error.forbidden ? "forbidden" : "error"}
            title={error.forbidden ? "无权查看 Research Question" : error.title}
            message={error.message}
            action={
              error.retryable ? (
                <button
                  type="button"
                  className="rq-button"
                  onClick={props.onRetry}
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

  if (props.content.state === "empty") {
    return <CreateWorkspace props={props} />
  }

  const question = props.content.data
  const pending = props.pendingAction !== null
  const known = question.knownStatus
  const editable =
    known &&
    question.permissions.canEdit &&
    question.permissions.canCreateVersion
  const saveDisabledReason = !known
    ? "当前版本状态未知，保存新版本已禁用。"
    : !question.permissions.canCreateVersion
      ? "服务端未授予创建新版本的能力。"
      : !question.permissions.canEdit
        ? "当前版本为只读状态。"
        : null
  const readyDisabledReason = !known
    ? "当前状态未知，不能标记为 ready。"
    : !question.permissions.canMarkReady
      ? "服务端未授予 mark-ready 能力。"
      : null
  const confirmationDisabledReason = !known
    ? "当前状态未知，不能请求确认。"
    : question.pendingApproval
      ? "已有待处理确认；pending 不等于 confirmed。"
      : !question.permissions.canRequestConfirmation
        ? "服务端未授予 request-confirmation 能力。"
        : null

  const saveVersion = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!editable || pending) return
    const form = new FormData(event.currentTarget)
    const changeReason = String(form.get("changeReason") ?? "").trim()
    if (!changeReason) return
    props.onEvent({
      action: "save-version",
      input: {
        questionId: question.questionId,
        basedOnVersionId: question.currentVersionId,
        changeReason,
        fields: {
          ...question.fields,
          rawInput: String(form.get("rawInput") ?? "").trim(),
          normalizedQuestion: optionalText(form.get("normalizedQuestion")),
          researchObject: optionalText(form.get("researchObject")),
          population: optionalText(form.get("population")),
          context: optionalText(form.get("context")),
          independentVariables: listValue(form.get("independentVariables")),
          dependentVariables: listValue(form.get("dependentVariables")),
          controlVariables: listValue(form.get("controlVariables")),
          researchGoal:
            (optionalText(
              form.get("researchGoal"),
            ) as ResearchQuestionFields["researchGoal"]) ?? null,
          relationshipType:
            (optionalText(
              form.get("relationshipType"),
            ) as ResearchQuestionFields["relationshipType"]) ?? null,
        },
      },
    })
  }

  return (
    <div
      className="reca-visual-refresh rq-workspace"
      data-theme={visualTheme}
      data-od-id="research-question-workspace"
    >
      <WorkspaceHeader
        title="Research Question"
        context={`版本 ${question.versionNumber}`}
        metadata={
          <>
            <StatusBadge
              label={statusLabel(question.status, question.knownStatus)}
              tone={question.knownStatus ? question.tone : "unknown"}
            />
            {question.pendingApproval ? (
              <SourceBadge
                label={`待确认 · ${question.pendingApproval.status}`}
                kind="approval"
                title="待确认不等于已确认"
              />
            ) : null}
          </>
        }
        actions={
          <>
            <ActionButton
              label="保存新版本"
              pendingLabel="正在保存…"
              pending={props.pendingAction === "save-version"}
              primary
              disabled={pending || !editable}
              reason={saveDisabledReason}
              icon={<Save aria-hidden="true" />}
              type="submit"
              form="rq-version-form"
            />
            <ActionButton
              label="标记为待确认"
              pendingLabel="正在提交…"
              pending={props.pendingAction === "mark-ready"}
              disabled={pending || Boolean(readyDisabledReason)}
              reason={readyDisabledReason}
              icon={<CheckCircle2 aria-hidden="true" />}
              onClick={() =>
                props.onEvent({
                  action: "mark-ready",
                  input: { versionId: question.currentVersionId, reason: null },
                })
              }
            />
            <ActionButton
              label="请求确认"
              pendingLabel="正在请求…"
              pending={props.pendingAction === "request-confirmation"}
              disabled={pending || Boolean(confirmationDisabledReason)}
              reason={confirmationDisabledReason}
              icon={<Send aria-hidden="true" />}
              onClick={() =>
                props.onEvent({
                  action: "request-confirmation",
                  input: { versionId: question.currentVersionId },
                })
              }
            />
          </>
        }
      />

      {props.mutationError ? (
        <div className="rq-workspace-notice">
          <MutationError
            title={props.mutationError.title}
            message={props.mutationError.message}
            code={props.mutationError.code}
            requestId={props.mutationError.requestId}
            retryable={props.mutationError.retryable}
            onRetry={props.onRetry}
          />
        </div>
      ) : null}
      {!known ? (
        <div className="rq-workspace-notice">
          <DegradedNotice
            title="Research Question 状态未知"
            message="所有正式操作已安全禁用；当前字段仅用于读取，不会被解释为可编辑版本。"
          />
        </div>
      ) : null}
      {question.pendingApproval ? (
        <div className="rq-workspace-notice">
          <PermissionNotice
            title="确认仍在等待处理"
            reason="pending confirmation 不是 confirmed；在服务端返回正式结果前不会推进状态。"
          />
        </div>
      ) : null}

      <div className="rq-layout">
        <main className="rq-main" data-od-id="research-question-editor">
          <ResearchQuestionEditor
            question={question}
            editable={editable && !pending}
            onSave={saveVersion}
          />
        </main>
        <aside
          className="rq-inspector"
          data-od-id="research-question-inspector"
        >
          <InspectorSection
            title="当前版本"
            accessory={<History aria-hidden="true" />}
          >
            <MetadataList
              items={[
                { label: "版本", value: question.versionNumber },
                {
                  label: "状态",
                  value: statusLabel(question.status, question.knownStatus),
                },
                {
                  label: "Version ID",
                  value: question.currentVersionId,
                  mono: true,
                },
                {
                  label: "Question ID",
                  value: question.questionId,
                  mono: true,
                },
                { label: "Project ID", value: question.projectId, mono: true },
                { label: "创建时间", value: question.createdAt },
              ]}
            />
          </InspectorSection>

          <InspectorSection title="版本历史">
            <VersionHistory question={question} />
          </InspectorSection>

          <InspectorSection title="状态与权限">
            <MetadataList
              items={[
                { label: "状态已知", value: known ? "是" : "否" },
                {
                  label: "可编辑",
                  value: question.permissions.canEdit ? "是" : "否",
                },
                {
                  label: "可创建版本",
                  value: question.permissions.canCreateVersion ? "是" : "否",
                },
                {
                  label: "可标记待确认",
                  value: question.permissions.canMarkReady ? "是" : "否",
                },
                {
                  label: "可请求确认",
                  value: question.permissions.canRequestConfirmation
                    ? "是"
                    : "否",
                },
              ]}
            />
            {!editable ? (
              <p className="rq-readonly-note">
                <LockKeyhole aria-hidden="true" />
                <span>{saveDisabledReason ?? "当前版本为只读状态。"}</span>
              </p>
            ) : null}
          </InspectorSection>

          <InspectorSection title="Capability availability">
            <CapabilityList capabilities={props.capabilities} />
            {props.capabilities.aiParse === "NOT_AVAILABLE" ? (
              <p className="rq-capability-note">
                AI Parse 当前不可用，因此 Workspace 不显示虚假解析入口。
              </p>
            ) : null}
            {Object.values(props.capabilities).includes("UNKNOWN") ? (
              <p className="rq-capability-note rq-capability-note--unknown">
                未知 capability 不会被推断为可用。
              </p>
            ) : null}
          </InspectorSection>

          <InspectorSection title="Pending approval">
            {question.pendingApproval ? (
              <MetadataList
                items={[
                  {
                    label: "Approval ID",
                    value: question.pendingApproval.id,
                    mono: true,
                  },
                  { label: "状态", value: question.pendingApproval.status },
                  { label: "正式确认", value: "尚未完成" },
                ]}
              />
            ) : (
              <p className="rq-empty-value">当前没有 pending approval。</p>
            )}
          </InspectorSection>
        </aside>
      </div>
    </div>
  )
}
