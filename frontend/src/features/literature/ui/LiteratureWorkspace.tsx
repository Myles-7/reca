import {
  ArrowLeft,
  BookOpenCheck,
  Filter,
  PanelRight,
  RefreshCw,
  Search,
  X,
} from "lucide-react"
import { type FormEvent, useEffect, useMemo, useState } from "react"

import {
  DegradedNotice,
  InspectorSection,
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
import { Button } from "@/components/ui/button"

import type {
  LiteratureCandidateViewModel,
  LiteratureRecordViewModel,
  LiteratureWorkspaceViewModel,
} from "../model"
import type { LiteratureWorkspaceProps } from "./contracts"
import "./literature-workspace.css"

type ActiveList = "candidates" | "records"
type SelectedItem =
  | { kind: "candidate"; id: string }
  | { kind: "record"; id: string }

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

function verificationTone(status: string): string {
  return status === "VERIFIED" ? "success" : "unknown"
}

function decisionTone(decision: string): string {
  if (decision === "INCLUDED" || decision === "APPROVED") return "success"
  if (decision === "EXCLUDED" || decision === "REJECTED") return "danger"
  return "warning"
}

function RowValue({
  value,
  mono = false,
}: {
  value: string | number | null
  mono?: boolean
}) {
  return (
    <span
      className={
        mono
          ? "literature-row-value literature-row-value--mono"
          : "literature-row-value"
      }
      title={value == null ? undefined : String(value)}
    >
      {value ?? "—"}
    </span>
  )
}

function CandidateRow({
  candidate,
  selected,
  pending,
  canImport,
  canShowImportedRecord,
  activeSearchId,
  onSelect,
  onImport,
  onShowRecord,
}: {
  candidate: LiteratureCandidateViewModel
  selected: boolean
  pending: boolean
  canImport: boolean
  canShowImportedRecord: boolean
  activeSearchId: string | null
  onSelect: () => void
  onImport: () => void
  onShowRecord: (recordId: string) => void
}) {
  const importAllowed =
    canImport && candidate.canImport && activeSearchId !== null
  return (
    <div
      className="literature-row literature-row--candidate"
      role="row"
      data-selected={selected}
    >
      <button
        type="button"
        className="literature-row__select"
        onClick={onSelect}
        aria-pressed={selected}
      >
        <span className="literature-row__title" title={candidate.title}>
          {candidate.title}
        </span>
        <RowValue value={candidate.authors} />
        <RowValue value={candidate.year} />
        <RowValue value={candidate.doi} mono />
        <SourceBadge
          label="Candidate result"
          kind={candidate.degraded ? "degraded" : "unknown"}
        />
        <StatusBadge
          label={candidate.verificationStatus}
          tone={verificationTone(candidate.verificationStatus)}
        />
      </button>
      <div className="literature-row__action">
        {candidate.importedRecordId ? (
          <Button
            type="button"
            size="sm"
            variant="ghost"
            disabled={!canShowImportedRecord}
            title={
              canShowImportedRecord
                ? "查看正式记录"
                : "对应正式记录未包含在当前列表中"
            }
            onClick={() => onShowRecord(candidate.importedRecordId!)}
          >
            查看正式记录
          </Button>
        ) : (
          <Button
            type="button"
            size="sm"
            variant="ghost"
            disabled={pending || !importAllowed}
            title={importAllowed ? "导入候选结果" : "当前候选或权限不允许导入"}
            onClick={onImport}
          >
            导入
          </Button>
        )}
      </div>
    </div>
  )
}

function RecordRow({
  record,
  selected,
  onSelect,
}: {
  record: LiteratureRecordViewModel
  selected: boolean
  onSelect: () => void
}) {
  return (
    <div
      className="literature-row literature-row--record"
      role="row"
      data-selected={selected}
    >
      <button
        type="button"
        className="literature-row__select"
        onClick={onSelect}
        aria-pressed={selected}
      >
        <span className="literature-row__title" title={record.title}>
          {record.title}
        </span>
        <RowValue value={record.authors} />
        <RowValue value={record.year} />
        <RowValue value={record.doi} mono />
        <SourceBadge
          label="Literature record"
          kind={
            record.verificationStatus === "VERIFIED" ? "verified" : "unknown"
          }
        />
        <StatusBadge
          label={record.verificationStatus}
          tone={verificationTone(record.verificationStatus)}
        />
      </button>
      <div className="literature-row__action">
        <StatusBadge
          label={record.decision}
          tone={decisionTone(record.decision)}
        />
      </div>
    </div>
  )
}

function SearchControls({
  data,
  pending,
  onSearch,
  onImportDoi,
}: {
  data: LiteratureWorkspaceViewModel
  pending: string | null
  onSearch: (pageSize: number, useCache: boolean) => void
  onImportDoi: (doi: string) => void
}) {
  const [pageSize, setPageSize] = useState(25)
  const [useCache, setUseCache] = useState(true)
  const [doi, setDoi] = useState("")
  const searchRun = data.activeSearch
  const searchAllowed =
    data.permissionsKnown && data.permissions.canSearch && searchRun !== null
  const doiAllowed = data.permissionsKnown && data.permissions.canImportDoi

  function submitSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!searchAllowed || pending !== null) return
    onSearch(Math.max(1, Math.min(100, pageSize || 25)), useCache)
  }

  function submitDoi(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!doiAllowed || pending !== null || !doi.trim()) return
    onImportDoi(doi.trim())
  }

  return (
    <div className="literature-search-controls">
      <form onSubmit={submitSearch}>
        <label htmlFor="literature-page-size">每页结果</label>
        <input
          id="literature-page-size"
          type="number"
          min={1}
          max={100}
          value={pageSize}
          disabled={!searchAllowed || pending !== null}
          onChange={(event) => setPageSize(Number(event.target.value))}
        />
        <label className="literature-checkbox">
          <input
            type="checkbox"
            checked={useCache}
            disabled={!searchAllowed || pending !== null}
            onChange={(event) => setUseCache(event.target.checked)}
          />
          <span>允许使用缓存</span>
        </label>
        <Button
          type="submit"
          size="sm"
          className="literature-action-button"
          disabled={!searchAllowed || pending !== null}
        >
          <Search aria-hidden="true" />
          {pending === "search" ? "正在提交" : "执行检索"}
        </Button>
        {!searchAllowed ? (
          <small>
            {!data.permissionsKnown
              ? "权限状态未知，检索保持禁用。"
              : searchRun === null
                ? "当前 contract 未提供可用 Query Plan 关联。"
                : "当前权限不允许检索。"}
          </small>
        ) : null}
      </form>
      <form onSubmit={submitDoi}>
        <label htmlFor="literature-doi">DOI Import</label>
        <input
          id="literature-doi"
          value={doi}
          disabled={!doiAllowed || pending !== null}
          onChange={(event) => setDoi(event.target.value)}
          placeholder="10.xxxx/xxxxx"
        />
        <Button
          type="submit"
          size="sm"
          variant="outline"
          className="literature-action-button"
          disabled={!doiAllowed || pending !== null || !doi.trim()}
        >
          {pending === "import-doi" ? "正在提交" : "导入 DOI"}
        </Button>
        {!doiAllowed ? (
          <small>
            {data.permissionsKnown
              ? "当前权限不允许 DOI 导入。"
              : "权限状态未知，DOI 导入保持禁用。"}
          </small>
        ) : null}
      </form>
    </div>
  )
}

export function LiteratureWorkspace(props: LiteratureWorkspaceProps) {
  const visualTheme = useVisualTheme()
  const data = props.content.state === "ready" ? props.content.data : null
  const [activeList, setActiveList] = useState<ActiveList>("candidates")
  const [selected, setSelected] = useState<SelectedItem | null>(null)
  const [filterText, setFilterText] = useState("")
  const [filtersOpen, setFiltersOpen] = useState(false)
  const [inspectorOpen, setInspectorOpen] = useState(false)
  const [mobileDetail, setMobileDetail] = useState(false)

  useEffect(() => {
    if (!data) return
    const candidate = data.candidates[0]
    const record = data.records[0]
    setSelected(
      candidate
        ? { kind: "candidate", id: candidate.id }
        : record
          ? { kind: "record", id: record.id }
          : null,
    )
    setActiveList(candidate ? "candidates" : "records")
    setMobileDetail(false)
  }, [data?.activeSearch?.id])

  const visibleCandidates = useMemo(() => {
    if (!data) return []
    const term = filterText.trim().toLocaleLowerCase()
    if (!term) return data.candidates
    return data.candidates.filter((item) =>
      [item.title, item.authors, item.doi].some((value) =>
        value?.toLocaleLowerCase().includes(term),
      ),
    )
  }, [data, filterText])
  const visibleRecords = useMemo(() => {
    if (!data) return []
    const term = filterText.trim().toLocaleLowerCase()
    if (!term) return data.records
    return data.records.filter((item) =>
      [item.title, item.authors, item.doi].some((value) =>
        value?.toLocaleLowerCase().includes(term),
      ),
    )
  }, [data, filterText])

  if (!data) {
    const loadError =
      props.content.state === "error" ? props.content.error : null
    const canRetry = loadError?.retryable === true
    return (
      <section
        className="reca-visual-refresh reca-literature-workspace"
        data-theme={visualTheme}
        aria-label="文献工作台"
        data-od-id="literature-workspace-loading"
      >
        <WorkspaceHeader title="文献工作台" context="RECA / Literature" />
        <WorkspaceLoadingFrame layout="three-pane">
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

  const currentData = data
  const searchRun = data.activeSearch
  const permissionsSafe = data.permissionsKnown
  const pending = props.pendingAction !== null
  const selectedCandidate =
    selected?.kind === "candidate"
      ? (data.candidates.find((item) => item.id === selected.id) ?? null)
      : null
  const selectedRecord =
    selected?.kind === "record"
      ? (data.records.find((item) => item.id === selected.id) ?? null)
      : null

  function selectItem(item: SelectedItem) {
    setSelected(item)
    setInspectorOpen(true)
    setMobileDetail(true)
  }

  function showImportedRecord(recordId: string) {
    const record = currentData.records.find((item) => item.id === recordId)
    if (!record) return
    setActiveList("records")
    selectItem({ kind: "record", id: record.id })
  }

  return (
    <section
      className="reca-visual-refresh reca-literature-workspace"
      data-theme={visualTheme}
      aria-label="文献工作台"
      data-mobile-view={mobileDetail ? "detail" : "list"}
      data-od-id="literature-workspace"
    >
      <WorkspaceHeader
        title="文献工作台"
        context="RECA / Literature"
        metadata={
          searchRun ? (
            <div className="literature-header-meta">
              <StatusBadge
                label={searchRun.status}
                tone={searchRun.knownStatus ? searchRun.tone : "unknown"}
              />
              <SourceBadge
                label={
                  searchRun.cacheHit
                    ? "Recorded · cache hit"
                    : "Live · 未命中缓存"
                }
                kind={searchRun.degraded ? "degraded" : "evidence"}
              />
            </div>
          ) : (
            <StatusBadge label="无 Search Run" tone="unknown" />
          )
        }
        actions={
          <div className="literature-responsive-actions">
            <Button
              type="button"
              size="sm"
              variant="outline"
              onClick={() => setFiltersOpen(true)}
            >
              <Filter aria-hidden="true" />
              筛选
            </Button>
            <Button
              type="button"
              size="sm"
              variant="outline"
              onClick={() => setInspectorOpen(true)}
              disabled={!selected && !searchRun}
            >
              <PanelRight aria-hidden="true" />
              详情
            </Button>
          </div>
        }
      />

      {props.mutationError ? (
        <div className="literature-top-notice">
          <MutationError message={props.mutationError.message} />
        </div>
      ) : null}
      {!permissionsSafe ? (
        <div className="literature-top-notice">
          <PermissionNotice
            title="权限状态未知"
            reason="所有检索、候选导入和 DOI 导入操作保持禁用；现有结果仍保持清晰可读。"
          />
        </div>
      ) : null}
      {searchRun?.cacheStale ? (
        <div className="literature-top-notice">
          <DegradedNotice
            title="缓存已过期"
            message="当前结果来自过期缓存，需要重新同步；cache hit 不代表结果质量。"
          />
        </div>
      ) : null}
      {searchRun?.degraded ? (
        <div className="literature-top-notice">
          <DegradedNotice
            title="Provider 结果已降级"
            message={
              searchRun.limitations.join("；") ||
              "提供方结果不完整，正式使用前需要人工复核。"
            }
          />
        </div>
      ) : null}
      {searchRun?.errorCode ? (
        <div className="literature-top-notice">
          <MutationError
            title="Provider failure"
            message={`提供方返回错误代码 ${searchRun.errorCode}。`}
          />
        </div>
      ) : null}

      <div className="literature-responsive-back">
        <Button
          type="button"
          size="sm"
          variant="ghost"
          onClick={() => setMobileDetail(false)}
        >
          <ArrowLeft aria-hidden="true" />
          返回列表
        </Button>
      </div>

      <div className="literature-layout">
        <aside
          className={`literature-pane literature-left-pane${filtersOpen ? " is-open" : ""}`}
          aria-label="检索与筛选"
          data-od-id="literature-search-pane"
        >
          <PaneHeader
            title="检索上下文"
            subtitle={
              searchRun ? formatTimestamp(searchRun.fetchedAt) : "无运行记录"
            }
            actions={
              <Button
                type="button"
                size="icon-sm"
                variant="ghost"
                className="literature-pane-close"
                aria-label="关闭筛选"
                onClick={() => setFiltersOpen(false)}
              >
                <X aria-hidden="true" />
              </Button>
            }
          />
          <div className="literature-left-content">
            <InspectorSection title="Query Plan 关联">
              <MetadataList
                items={[
                  {
                    label: "Query Plan",
                    value: searchRun?.queryPlanId ?? "未提供",
                    mono: true,
                  },
                  {
                    label: "Search Run",
                    value: searchRun?.id ?? "无",
                    mono: true,
                  },
                  {
                    label: "Result count",
                    value: searchRun?.resultCount ?? "—",
                  },
                ]}
              />
            </InspectorSection>
            <InspectorSection title="运行来源">
              <div className="literature-source-stack">
                {searchRun ? (
                  <>
                    <StatusBadge
                      label={searchRun.status}
                      tone={searchRun.knownStatus ? searchRun.tone : "unknown"}
                    />
                    <SourceBadge
                      label={
                        searchRun.cacheHit
                          ? "Recorded · cache hit"
                          : "Live fetch"
                      }
                      kind={searchRun.degraded ? "degraded" : "evidence"}
                    />
                    {searchRun.cacheStale ? (
                      <StatusBadge
                        label="Cache stale · 需要同步"
                        tone="degraded"
                      />
                    ) : null}
                  </>
                ) : (
                  <StatusBadge label="无 Search Run" tone="unknown" />
                )}
              </div>
            </InspectorSection>
            <div className="literature-local-filter">
              <label htmlFor="literature-local-filter">本地筛选</label>
              <div>
                <Search aria-hidden="true" />
                <input
                  id="literature-local-filter"
                  type="search"
                  value={filterText}
                  onChange={(event) => setFilterText(event.target.value)}
                  placeholder="标题、作者或 DOI"
                />
              </div>
              <small>只影响当前 UI 列表，不改变正式检索结果。</small>
            </div>
            <SearchControls
              data={data}
              pending={props.pendingAction}
              onSearch={(pageSize, useCache) => {
                if (!searchRun) return
                props.onEvent({
                  action: "search",
                  input: {
                    queryPlanId: searchRun.queryPlanId,
                    pageSize,
                    useCache,
                  },
                })
              }}
              onImportDoi={(doi) =>
                props.onEvent({ action: "import-doi", input: { doi } })
              }
            />
          </div>
        </aside>

        <main
          className="literature-pane literature-center-pane"
          aria-label="文献列表"
          data-od-id="literature-results-pane"
        >
          <div className="literature-tabs" role="tablist" aria-label="文献类型">
            <button
              type="button"
              role="tab"
              aria-selected={activeList === "candidates"}
              onClick={() => setActiveList("candidates")}
            >
              候选结果 <span>{data.candidates.length}</span>
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={activeList === "records"}
              onClick={() => setActiveList("records")}
            >
              正式文献 <span>{data.records.length}</span>
            </button>
          </div>
          <div
            className="literature-list"
            role="table"
            aria-label={activeList === "candidates" ? "候选结果" : "正式文献"}
          >
            <div className="literature-list-header" role="row">
              <span>Title</span>
              <span>Authors</span>
              <span>Year</span>
              <span>DOI</span>
              <span>Source</span>
              <span>
                {activeList === "candidates" ? "Verification" : "Decision"}
              </span>
              <span>Action</span>
            </div>
            {activeList === "candidates"
              ? visibleCandidates.map((candidate) => (
                  <CandidateRow
                    key={candidate.id}
                    candidate={candidate}
                    selected={
                      selected?.kind === "candidate" &&
                      selected.id === candidate.id
                    }
                    pending={pending}
                    canImport={permissionsSafe && data.permissions.canImport}
                    canShowImportedRecord={
                      candidate.importedRecordId !== null &&
                      data.records.some(
                        (record) => record.id === candidate.importedRecordId,
                      )
                    }
                    activeSearchId={searchRun?.id ?? null}
                    onSelect={() =>
                      selectItem({ kind: "candidate", id: candidate.id })
                    }
                    onImport={() => {
                      if (!searchRun) return
                      props.onEvent({
                        action: "import-candidates",
                        input: {
                          searchRunId: searchRun.id,
                          candidateIds: [candidate.id],
                        },
                      })
                    }}
                    onShowRecord={showImportedRecord}
                  />
                ))
              : visibleRecords.map((record) => (
                  <RecordRow
                    key={record.id}
                    record={record}
                    selected={
                      selected?.kind === "record" && selected.id === record.id
                    }
                    onSelect={() =>
                      selectItem({ kind: "record", id: record.id })
                    }
                  />
                ))}
            {(activeList === "candidates" ? visibleCandidates : visibleRecords)
              .length === 0 ? (
              <div className="literature-list-empty">
                当前筛选下没有可显示的
                {activeList === "candidates" ? "候选结果" : "正式文献"}。
              </div>
            ) : null}
          </div>
        </main>

        <aside
          className={`literature-pane literature-inspector${inspectorOpen ? " is-open" : ""}`}
          aria-label="文献详情 Inspector"
          data-od-id="literature-inspector-pane"
        >
          <PaneHeader
            title="Inspector"
            subtitle={
              selectedCandidate
                ? "Candidate result"
                : selectedRecord
                  ? "Literature record"
                  : "未选择"
            }
            actions={
              <Button
                type="button"
                size="icon-sm"
                variant="ghost"
                className="literature-pane-close"
                aria-label="关闭详情"
                onClick={() => {
                  setInspectorOpen(false)
                  setMobileDetail(false)
                }}
              >
                <X aria-hidden="true" />
              </Button>
            }
          />
          {selectedCandidate ? (
            <CandidateInspector
              candidate={selectedCandidate}
              data={data}
              searchRunId={searchRun?.id ?? null}
              pending={pending}
              onImport={() => {
                if (!searchRun) return
                props.onEvent({
                  action: "import-candidates",
                  input: {
                    searchRunId: searchRun.id,
                    candidateIds: [selectedCandidate.id],
                  },
                })
              }}
              onShowRecord={showImportedRecord}
            />
          ) : selectedRecord ? (
            <RecordInspector record={selectedRecord} />
          ) : (
            <div className="literature-inspector-empty">
              <BookOpenCheck aria-hidden="true" />
              <p>选择一条候选结果或正式文献以查看完整 metadata。</p>
            </div>
          )}
          {searchRun ? (
            <InspectorSection title="Search Run 状态">
              <MetadataList
                items={[
                  { label: "Status", value: searchRun.status },
                  {
                    label: "Source",
                    value: searchRun.cacheHit
                      ? "Recorded / cache hit"
                      : "Live fetch",
                  },
                  {
                    label: "Cache stale",
                    value: searchRun.cacheStale ? "是 · 需要重新同步" : "否",
                  },
                  {
                    label: "Fetched",
                    value: formatTimestamp(searchRun.fetchedAt),
                  },
                ]}
              />
              {searchRun.limitations.length > 0 ? (
                <div className="literature-search-limitations">
                  {searchRun.limitations.map((limitation) => (
                    <DegradedNotice
                      key={limitation}
                      title="Provider limitation"
                      message={limitation}
                    />
                  ))}
                </div>
              ) : null}
            </InspectorSection>
          ) : null}
          <InspectorSection title="Job retry">
            <Button
              type="button"
              size="sm"
              variant="outline"
              disabled={!searchRun?.canRetry || pending}
              onClick={() => {
                if (!searchRun?.progressJobId) return
                props.onEvent({
                  action: "retry-job",
                  input: { jobId: searchRun.progressJobId },
                })
              }}
            >
              {props.pendingAction === "retry-job" ? "正在提交" : "重试任务"}
            </Button>
            {searchRun?.retryDisabledReason ? (
              <p className="literature-inspector-copy">
                {searchRun.retryDisabledReason}
              </p>
            ) : null}
          </InspectorSection>
        </aside>
      </div>
    </section>
  )
}

function CandidateInspector({
  candidate,
  data,
  searchRunId,
  pending,
  onImport,
  onShowRecord,
}: {
  candidate: LiteratureCandidateViewModel
  data: LiteratureWorkspaceViewModel
  searchRunId: string | null
  pending: boolean
  onImport: () => void
  onShowRecord: (recordId: string) => void
}) {
  const importedRecordAvailable = candidate.importedRecordId
    ? data.records.some((record) => record.id === candidate.importedRecordId)
    : false
  const allowed =
    data.permissionsKnown &&
    data.permissions.canImport &&
    candidate.canImport &&
    searchRunId !== null
  const reason = !data.permissionsKnown
    ? "权限状态未知。"
    : !data.permissions.canImport
      ? "当前权限不允许候选导入。"
      : !candidate.canImport
        ? "该候选结果不可导入。"
        : searchRunId === null
          ? "缺少 Search Run 关联。"
          : null
  return (
    <>
      <InspectorSection title="类型与验证">
        <div className="literature-source-stack">
          <SourceBadge
            label="Candidate result · 候选结果"
            kind={candidate.degraded ? "degraded" : "unknown"}
          />
          <StatusBadge
            label={candidate.verificationStatus}
            tone={verificationTone(candidate.verificationStatus)}
          />
        </div>
      </InspectorSection>
      <InspectorSection title="Metadata">
        <MetadataList
          items={[
            { label: "Title", value: candidate.title },
            { label: "Authors", value: candidate.authors ?? "—" },
            { label: "Year", value: candidate.year ?? "—" },
            { label: "DOI", value: candidate.doi ?? "—", mono: true },
            { label: "Candidate ID", value: candidate.id, mono: true },
          ]}
        />
      </InspectorSection>
      <InspectorSection title="导入状态">
        {candidate.importedRecordId ? (
          <>
            <StatusBadge label="已导入正式记录" tone="success" />
            <Button
              type="button"
              size="sm"
              variant="outline"
              disabled={!importedRecordAvailable}
              title={
                importedRecordAvailable
                  ? "查看正式记录"
                  : "对应正式记录未包含在当前列表中"
              }
              onClick={() => onShowRecord(candidate.importedRecordId!)}
            >
              查看正式记录
            </Button>
          </>
        ) : (
          <>
            <Button
              type="button"
              size="sm"
              disabled={!allowed || pending}
              onClick={onImport}
            >
              {pending ? "正在提交" : "导入候选"}
            </Button>
            {reason ? (
              <p className="literature-inspector-copy">{reason}</p>
            ) : null}
          </>
        )}
      </InspectorSection>
      {candidate.degraded ? (
        <InspectorSection title="来源限制">
          <DegradedNotice message="该候选来自降级提供方，需要人工复核后再决定是否导入。" />
        </InspectorSection>
      ) : null}
    </>
  )
}

function RecordInspector({ record }: { record: LiteratureRecordViewModel }) {
  return (
    <>
      <InspectorSection title="类型与判断">
        <div className="literature-source-stack">
          <SourceBadge
            label="Literature record · 正式文献"
            kind={
              record.verificationStatus === "VERIFIED" ? "verified" : "unknown"
            }
          />
          <StatusBadge
            label={record.verificationStatus}
            tone={verificationTone(record.verificationStatus)}
          />
          <StatusBadge
            label={record.decision}
            tone={decisionTone(record.decision)}
          />
        </div>
        <p className="literature-inspector-copy">
          Verification 与 Literature Decision 是不同语义，不互相替代。
        </p>
      </InspectorSection>
      <InspectorSection title="Metadata">
        <MetadataList
          items={[
            { label: "Title", value: record.title },
            { label: "Authors", value: record.authors ?? "—" },
            { label: "Year", value: record.year ?? "—" },
            { label: "DOI", value: record.doi ?? "—", mono: true },
            { label: "Source", value: record.sourceType },
            { label: "Record ID", value: record.id, mono: true },
          ]}
        />
      </InspectorSection>
      <InspectorSection title="Document binding">
        <MetadataList
          items={[
            {
              label: "Document",
              value: record.documentId ?? "未绑定",
              mono: true,
            },
            {
              label: "Can upload",
              value: record.canUploadDocument ? "允许" : "不允许",
            },
          ]}
        />
        <p className="literature-inspector-copy">
          Literature contract 不提供文档上传事件；相关操作应由 Document
          模块表达。
        </p>
      </InspectorSection>
    </>
  )
}
