import { useState } from "react"

import {
  SourceBadge,
  StatusBadge,
  useVisualTheme,
  WorkspaceHeader,
} from "@/components/reca-visual-refresh"
import type { ProjectWorkspaceDesignFixture } from "@/features/projects/fixtures"
import { ApprovalsPanel } from "@/features/projects/ui/ApprovalsPanel"
import { ArtifactsPanel } from "@/features/projects/ui/ArtifactsPanel"
import { AuditPanel } from "@/features/projects/ui/AuditPanel"
import { JobsPanel } from "@/features/projects/ui/JobsPanel"
import { MembersPanel } from "@/features/projects/ui/MembersPanel"
import { OverviewPanel } from "@/features/projects/ui/OverviewPanel"

const projectTabs = [
  { id: "overview", label: "概览" },
  { id: "members", label: "成员" },
  { id: "artifacts", label: "Artifacts" },
  { id: "jobs", label: "Jobs" },
  { id: "approvals", label: "Approvals" },
  { id: "audit", label: "Audit" },
] as const

type ProjectTab = (typeof projectTabs)[number]["id"]

export function ProjectWorkspacePreview({
  fixture,
  onIntent = () => undefined,
}: {
  fixture: ProjectWorkspaceDesignFixture
  onIntent?: (action: string, input?: unknown) => void
}) {
  const [tab, setTab] = useState<ProjectTab>("overview")
  const visualTheme = useVisualTheme()

  return (
    <section
      className="reca-visual-refresh project-workspace-shell"
      data-theme={visualTheme}
      aria-label="Project Workspace"
      data-od-id="project-workspace"
    >
      <WorkspaceHeader
        title={fixture.project.name}
        context={`Project Workspace · ${fixture.project.id}`}
        metadata={
          <>
            <StatusBadge label={fixture.project.status} tone="info" />
            <StatusBadge
              label={`阶段 ${fixture.project.stage}`}
              tone="neutral"
            />
          </>
        }
        actions={
          <>
            <SourceBadge
              label={`lock v${fixture.project.lockVersion}`}
              kind="verified"
              title="服务端项目版本"
            />
            <span className="project-workspace-shell__updated">
              更新于 {fixture.project.updatedAt}
            </span>
          </>
        }
      />
      <p className="project-workspace-shell__description">
        {fixture.project.description ?? "暂无项目说明"}
      </p>
      <div className="project-workspace-shell__nav">
        <nav aria-label="项目工作台区域">
          {projectTabs.map((item) => (
            <button
              key={item.id}
              type="button"
              aria-current={tab === item.id ? "page" : undefined}
              onClick={() => setTab(item.id)}
            >
              {item.label}
            </button>
          ))}
        </nav>
        <label>
          <span>当前 Panel</span>
          <select
            value={tab}
            onChange={(event) => setTab(event.target.value as ProjectTab)}
          >
            {projectTabs.map((item) => (
              <option key={item.id} value={item.id}>
                {item.label}
              </option>
            ))}
          </select>
        </label>
      </div>
      <div className="project-workspace-shell__panel" data-panel={tab}>
        {tab === "overview" ? (
          <OverviewPanel
            {...fixture.overview}
            onRetry={() => onIntent("overview.retry")}
          />
        ) : null}
        {tab === "members" ? (
          <MembersPanel
            {...fixture.members}
            onRetry={() => onIntent("members.retry")}
            onAddMember={(input) => onIntent("members.add", input)}
            onChangeRole={(input) => onIntent("members.change-role", input)}
            onTransferOwnership={(input) =>
              onIntent("members.transfer-ownership", input)
            }
            onRemoveMember={(input) =>
              onIntent("members.remove", { memberId: input })
            }
          />
        ) : null}
        {tab === "artifacts" ? (
          <ArtifactsPanel
            {...fixture.artifacts}
            onRetry={() => onIntent("artifacts.retry")}
            onUpload={(input) => onIntent("artifacts.upload", input)}
            onDownload={(input) =>
              onIntent("artifacts.download", { artifactId: input })
            }
          />
        ) : null}
        {tab === "jobs" ? (
          <JobsPanel
            {...fixture.jobs}
            onRetryLoad={() => onIntent("jobs.retry-load")}
            onAction={(input) => onIntent(`jobs.${input.action}`, input)}
          />
        ) : null}
        {tab === "approvals" ? (
          <ApprovalsPanel
            {...fixture.approvals}
            onRetry={() => onIntent("approvals.retry")}
            onAction={(input) => onIntent(`approvals.${input.action}`, input)}
          />
        ) : null}
        {tab === "audit" ? (
          <AuditPanel
            {...fixture.audit}
            onRetry={() => onIntent("audit.retry")}
          />
        ) : null}
      </div>
    </section>
  )
}
