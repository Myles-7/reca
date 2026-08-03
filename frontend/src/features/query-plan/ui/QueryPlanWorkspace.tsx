import { RefreshCw, Save, Sparkles } from "lucide-react"
import { type FormEvent, useEffect, useState } from "react"

import {
  DegradedNotice,
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
import { Button } from "@/components/ui/button"

import type { QueryPlanFieldsViewModel } from "../model"
import type { QueryPlanWorkspaceProps } from "./contracts"
import "./query-plan-workspace.css"

function parseList(value: string): string[] {
  return value
    .split(/[,，\n]/)
    .map((item) => item.trim())
    .filter(Boolean)
}

function formatTimestamp(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(date)
}

function TermEditor({
  id,
  label,
  description,
  values,
  disabled,
  onChange,
}: {
  id: string
  label: string
  description: string
  values: readonly string[]
  disabled: boolean
  onChange: (values: string[]) => void
}) {
  return (
    <div className="query-plan-field">
      <label htmlFor={id}>{label}</label>
      <p>{description}</p>
      <div className="query-plan-token-list" aria-label={`${label}当前值`}>
        {values.length > 0 ? (
          values.map((value) => <span key={value}>{value}</span>)
        ) : (
          <span data-empty="true">尚未设置</span>
        )}
      </div>
      <textarea
        id={id}
        rows={2}
        value={values.join("，")}
        disabled={disabled}
        onChange={(event) => onChange(parseList(event.target.value))}
        aria-describedby={`${id}-hint`}
      />
      <small id={`${id}-hint`}>
        使用逗号或换行分隔；编辑仅保存在当前界面，提交后由服务端决定正式状态。
      </small>
    </div>
  )
}

function RecordTermEditor({
  id,
  label,
  description,
  value,
  disabled,
  onChange,
}: {
  id: string
  label: string
  description: string
  value: Readonly<Record<string, readonly string[]>>
  disabled: boolean
  onChange: (value: Readonly<Record<string, readonly string[]>>) => void
}) {
  const entries = Object.entries(value)
  return (
    <div className="query-plan-field">
      <div className="query-plan-field__label">{label}</div>
      <p>{description}</p>
      {entries.length > 0 ? (
        <div className="query-plan-record-list">
          {entries.map(([language, terms]) => (
            <div key={language}>
              <label htmlFor={`${id}-${language}`}>{language}</label>
              <input
                id={`${id}-${language}`}
                value={terms.join("，")}
                disabled={disabled}
                onChange={(event) =>
                  onChange({
                    ...value,
                    [language]: parseList(event.target.value),
                  })
                }
              />
            </div>
          ))}
        </div>
      ) : (
        <div className="query-plan-empty-value">当前契约数据未提供词项。</div>
      )}
    </div>
  )
}

function QueryPlanEditor({
  fields,
  disabled,
  saving,
  changeReason,
  onFieldsChange,
  onChangeReason,
  onSubmit,
}: {
  fields: QueryPlanFieldsViewModel
  disabled: boolean
  saving: boolean
  changeReason: string
  onFieldsChange: (fields: QueryPlanFieldsViewModel) => void
  onChangeReason: (value: string) => void
  onSubmit: (event: FormEvent<HTMLFormElement>) => void
}) {
  return (
    <form className="query-plan-editor" onSubmit={onSubmit}>
      <section className="query-plan-section">
        <SectionHeader
          title="核心关键词"
          description="中英文关键词共同定义检索主题，词项保持紧凑并可快速扫描。"
        />
        <div className="query-plan-section__body query-plan-two-columns">
          <TermEditor
            id="query-plan-chinese-terms"
            label="中文核心词"
            description="用于中文来源和本地术语匹配。"
            values={fields.chineseTerms}
            disabled={disabled}
            onChange={(values) =>
              onFieldsChange({ ...fields, chineseTerms: values })
            }
          />
          <TermEditor
            id="query-plan-english-terms"
            label="英文核心词"
            description="用于英文数据库和跨语言检索。"
            values={fields.englishTerms}
            disabled={disabled}
            onChange={(values) =>
              onFieldsChange({ ...fields, englishTerms: values })
            }
          />
        </div>
      </section>

      <section className="query-plan-section">
        <SectionHeader
          title="扩展词与研究边界"
          description="按语言保留同义词、研究对象和方法词，不将本地编辑视为正式计划。"
        />
        <div className="query-plan-section__body query-plan-record-grid">
          <RecordTermEditor
            id="query-plan-synonyms"
            label="同义词"
            description="扩展表达与常用缩写。"
            value={fields.synonyms}
            disabled={disabled}
            onChange={(value) => onFieldsChange({ ...fields, synonyms: value })}
          />
          <RecordTermEditor
            id="query-plan-object-terms"
            label="对象词"
            description="限定研究对象或人群。"
            value={fields.objectTerms}
            disabled={disabled}
            onChange={(value) =>
              onFieldsChange({ ...fields, objectTerms: value })
            }
          />
          <RecordTermEditor
            id="query-plan-method-terms"
            label="方法词"
            description="补充方法或研究设计。"
            value={fields.methodTerms}
            disabled={disabled}
            onChange={(value) =>
              onFieldsChange({ ...fields, methodTerms: value })
            }
          />
        </div>
      </section>

      <section className="query-plan-section">
        <SectionHeader
          title="Boolean Query"
          description="稳定展示完整检索式；长表达只在数据表面内部滚动或安全换行。"
        />
        <div className="query-plan-section__body">
          <label
            className="query-plan-sr-only"
            htmlFor="query-plan-boolean-query"
          >
            Boolean Query
          </label>
          <textarea
            id="query-plan-boolean-query"
            className="query-plan-boolean-query"
            rows={5}
            value={fields.booleanQuery ?? ""}
            disabled={disabled}
            spellCheck={false}
            onChange={(event) =>
              onFieldsChange({
                ...fields,
                booleanQuery: event.target.value.trim() || null,
              })
            }
          />
        </div>
      </section>

      <section className="query-plan-section">
        <SectionHeader
          title="筛选条件"
          description="年份、语言、文献类型和开放获取条件共同随完整 fields 提交。"
        />
        <div className="query-plan-section__body query-plan-filter-grid">
          <label>
            起始年份
            <input
              type="number"
              inputMode="numeric"
              value={fields.filters.fromYear ?? ""}
              disabled={disabled}
              onChange={(event) =>
                onFieldsChange({
                  ...fields,
                  filters: {
                    ...fields.filters,
                    fromYear: event.target.value
                      ? Number(event.target.value)
                      : null,
                  },
                })
              }
            />
          </label>
          <label>
            结束年份
            <input
              type="number"
              inputMode="numeric"
              value={fields.filters.toYear ?? ""}
              disabled={disabled}
              onChange={(event) =>
                onFieldsChange({
                  ...fields,
                  filters: {
                    ...fields.filters,
                    toYear: event.target.value
                      ? Number(event.target.value)
                      : null,
                  },
                })
              }
            />
          </label>
          <label>
            语言
            <input
              value={fields.filters.languages.join("，")}
              disabled={disabled}
              onChange={(event) =>
                onFieldsChange({
                  ...fields,
                  filters: {
                    ...fields.filters,
                    languages: parseList(event.target.value),
                  },
                })
              }
            />
          </label>
          <label>
            文献类型
            <input
              value={fields.filters.workTypes.join("，")}
              disabled={disabled}
              onChange={(event) =>
                onFieldsChange({
                  ...fields,
                  filters: {
                    ...fields.filters,
                    workTypes: parseList(event.target.value),
                  },
                })
              }
            />
          </label>
          <label className="query-plan-checkbox">
            <input
              type="checkbox"
              checked={fields.filters.openAccessOnly}
              disabled={disabled}
              onChange={(event) =>
                onFieldsChange({
                  ...fields,
                  filters: {
                    ...fields.filters,
                    openAccessOnly: event.target.checked,
                  },
                })
              }
            />
            <span>仅开放获取（OA）</span>
          </label>
        </div>
      </section>

      <section className="query-plan-section query-plan-save-section">
        <SectionHeader
          title="变更说明"
          description="保存新内容前说明本次调整原因；本地表单状态不会覆盖服务端正式版本。"
        />
        <div className="query-plan-section__body query-plan-save-row">
          <label htmlFor="query-plan-change-reason">变更原因</label>
          <input
            id="query-plan-change-reason"
            value={changeReason}
            disabled={disabled}
            required
            onChange={(event) => onChangeReason(event.target.value)}
            placeholder="例如：补充对象词并缩小年份范围"
          />
          <Button
            type="submit"
            size="sm"
            className="query-plan-save-button"
            disabled={disabled || changeReason.trim().length === 0}
          >
            <Save aria-hidden="true" />
            {saving ? "正在提交" : "保存变更"}
          </Button>
        </div>
      </section>
    </form>
  )
}

export function QueryPlanWorkspace(props: QueryPlanWorkspaceProps) {
  const visualTheme = useVisualTheme()
  const plan = props.content.state === "ready" ? props.content.data : null
  const [fields, setFields] = useState<QueryPlanFieldsViewModel | null>(
    plan?.fields ?? null,
  )
  const [changeReason, setChangeReason] = useState("")

  useEffect(() => {
    if (!plan) return
    setFields(plan.fields)
    setChangeReason("")
  }, [plan?.id, plan?.lockVersion])

  if (!plan || !fields) {
    const loadError =
      props.content.state === "error" ? props.content.error : null
    const canRetry = loadError?.retryable === true
    return (
      <section
        className="reca-visual-refresh reca-query-plan-workspace"
        data-theme={visualTheme}
        aria-label="检索计划"
      >
        <WorkspaceHeader title="检索计划" context="RECA / Query Plan" />
        <WorkspaceLoadingFrame layout="dual-pane">
          <LoadableState
            state={loadError?.forbidden ? "forbidden" : props.content.state}
            title={loadError?.title}
            message={loadError?.message}
            action={
              canRetry ? (
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  onClick={props.onRetry}
                >
                  <RefreshCw aria-hidden="true" />
                  重新加载
                </Button>
              ) : undefined
            }
          />
        </WorkspaceLoadingFrame>
      </section>
    )
  }

  const currentPlan = plan
  const currentFields = fields
  const pending = props.pendingAction !== null
  const safeToWrite = plan.knownStatus && plan.permissions.canUpdate
  const safeToGenerate = plan.knownStatus && plan.permissions.canGenerate
  const disabledReason = !plan.knownStatus
    ? "服务端返回了当前前端未识别的状态；更新与 AI 生成均保持禁用。"
    : !plan.permissions.canUpdate && !plan.permissions.canGenerate
      ? "当前权限不允许更新或生成检索计划。"
      : !plan.permissions.canUpdate
        ? "当前权限不允许更新检索计划。"
        : !plan.permissions.canGenerate
          ? "当前权限不允许 AI 生成检索计划。"
          : null

  function submitUpdate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!safeToWrite || pending || !changeReason.trim()) return
    props.onEvent({
      action: "update",
      input: {
        queryPlanId: currentPlan.id,
        lockVersion: currentPlan.lockVersion,
        changeReason: changeReason.trim(),
        fields: currentFields,
      },
    })
  }

  return (
    <section
      className="reca-visual-refresh reca-query-plan-workspace"
      data-theme={visualTheme}
      aria-label="检索计划"
    >
      <WorkspaceHeader
        title="检索计划"
        context="RECA / Query Plan"
        metadata={
          <div className="query-plan-header-meta">
            <StatusBadge
              label={plan.status}
              tone={plan.knownStatus ? plan.tone : "unknown"}
            />
            <SourceBadge
              label={plan.generatedByAi ? "AI 生成" : "用户维护"}
              kind={plan.generatedByAi ? "ai-suggestion" : "human-decision"}
            />
            <time dateTime={plan.updatedAt}>
              {formatTimestamp(plan.updatedAt)}
            </time>
          </div>
        }
        actions={
          safeToGenerate ? (
            <Button
              type="button"
              size="sm"
              variant="outline"
              className="query-plan-primary-action"
              disabled={pending}
              onClick={() =>
                props.onEvent({
                  action: "generate",
                  input: { queryPlanId: plan.id },
                })
              }
            >
              <Sparkles aria-hidden="true" />
              {props.pendingAction === "generate" ? "正在提交" : "AI 生成"}
            </Button>
          ) : undefined
        }
      />

      {props.mutationError ? (
        <div className="query-plan-top-notice">
          <MutationError message={props.mutationError.message} />
        </div>
      ) : null}
      {!plan.knownStatus ? (
        <div className="query-plan-top-notice">
          <DegradedNotice
            title="未知检索计划状态"
            message="该状态未被当前展示契约识别；字段仍可复核，但所有写操作保持禁用。"
          />
        </div>
      ) : null}

      <div className="query-plan-layout">
        <QueryPlanEditor
          fields={fields}
          disabled={!safeToWrite || pending}
          saving={props.pendingAction === "update"}
          changeReason={changeReason}
          onFieldsChange={setFields}
          onChangeReason={setChangeReason}
          onSubmit={submitUpdate}
        />

        <aside className="query-plan-inspector" aria-label="检索计划 Inspector">
          <InspectorSection title="当前状态">
            <div className="query-plan-inspector-stack">
              <StatusBadge
                label={plan.status}
                tone={plan.knownStatus ? plan.tone : "unknown"}
              />
              <SourceBadge
                label={
                  plan.generatedByAi
                    ? "AI-generated · 有来源限制"
                    : "User-authored · 用户维护"
                }
                kind={plan.generatedByAi ? "ai-suggestion" : "human-decision"}
              />
            </div>
          </InspectorSection>
          <InspectorSection title="关联与版本">
            <MetadataList
              items={[
                {
                  label: "Research Question Version",
                  value: plan.researchQuestionVersionId,
                  mono: true,
                },
                { label: "Query Plan ID", value: plan.id, mono: true },
                { label: "Lock Version", value: plan.lockVersion, mono: true },
                { label: "Updated", value: formatTimestamp(plan.updatedAt) },
              ]}
            />
          </InspectorSection>
          <InspectorSection title="限制">
            {plan.fields.limitations.length > 0 ? (
              <div className="query-plan-limitations">
                {plan.fields.limitations.map((limitation) => (
                  <DegradedNotice
                    key={limitation}
                    title="覆盖限制"
                    message={limitation}
                  />
                ))}
              </div>
            ) : (
              <p className="query-plan-inspector-copy">
                服务端未提供限制说明。
              </p>
            )}
          </InspectorSection>
          {disabledReason ? (
            <InspectorSection title="操作限制">
              <PermissionNotice reason={disabledReason} />
            </InspectorSection>
          ) : null}
          <InspectorSection title="保存语义">
            <p className="query-plan-inspector-copy">
              表单编辑仅存在于本地界面。只有发出的 update 事件包含完整
              fields、lockVersion 与变更原因；正式保存结果仍由服务端决定。
            </p>
          </InspectorSection>
        </aside>
      </div>
    </section>
  )
}
