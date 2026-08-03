import { Link } from "@tanstack/react-router"
import { ArrowLeft, FileQuestion } from "lucide-react"

import {
  EmptyState,
  ErrorState,
  LoadingState,
} from "@/components/Common/PageState"
import {
  SourceBadge,
  StatusBadge,
  WorkspaceHeader,
} from "@/components/reca-visual-refresh"
import "@/components/reca-visual-refresh/visual-refresh.css"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

import { ApprovalsContainer } from "./containers/ApprovalsContainer"
import { ArtifactsContainer } from "./containers/ArtifactsContainer"
import { AuditContainer } from "./containers/AuditContainer"
import { JobsContainer } from "./containers/JobsContainer"
import { MembersContainer } from "./containers/MembersContainer"
import { OverviewContainer } from "./containers/OverviewContainer"
import { ProjectActionsContainer } from "./containers/ProjectActionsContainer"
import { mapUiError } from "./mappers"
import { useProject } from "./queries"
import "./ui/project-workspace.css"

const workspaceTabs = [
  { id: "overview", label: "Overview" },
  { id: "members", label: "Members" },
  { id: "artifacts", label: "Artifacts" },
  { id: "jobs", label: "Jobs" },
  { id: "approvals", label: "Approvals" },
  { id: "audit", label: "Audit" },
] as const

export function ProjectWorkspacePage({ projectId }: { projectId: string }) {
  const project = useProject(projectId)

  if (project.isLoading)
    return <LoadingState label="Loading project workspace" />
  if (project.error) {
    const error = mapUiError(project.error)
    return (
      <ErrorState
        message={
          error.forbidden
            ? "You do not have access to this project."
            : error.message
        }
      />
    )
  }
  if (!project.data) return <EmptyState>Project not found.</EmptyState>

  return (
    <section
      className="reca-visual-refresh project-workspace-shell"
      aria-label="Project Workspace"
    >
      <WorkspaceHeader
        title={project.data.name}
        context={`Project Workspace · ${project.data.id}`}
        metadata={
          <>
            <StatusBadge
              label={project.data.status}
              tone={project.data.knownStatus ? "info" : "degraded"}
            />
            <StatusBadge label={`Stage ${project.data.stage}`} tone="neutral" />
            <SourceBadge label={project.data.type} kind="verified" />
          </>
        }
        actions={
          <div className="project-workspace-shell__production-actions">
            <Button asChild size="sm" variant="ghost">
              <Link to="/projects">
                <ArrowLeft aria-hidden="true" /> Projects
              </Link>
            </Button>
            <Button asChild size="sm" variant="outline">
              <Link
                to="/projects/$projectId/research-question"
                params={{ projectId }}
              >
                <FileQuestion aria-hidden="true" /> Research question
              </Link>
            </Button>
            <SourceBadge
              label={`lock v${project.data.lockVersion}`}
              kind="verified"
              title="Server project version"
            />
            <ProjectActionsContainer
              projectId={projectId}
              project={project.data}
            />
          </div>
        }
      />
      <p className="project-workspace-shell__description">
        {project.data.description || "No project description"}
        <span className="project-workspace-shell__updated">
          Updated {project.data.updatedAt}
        </span>
      </p>

      <Tabs defaultValue="overview" className="project-workspace-shell__tabs">
        <div className="project-workspace-shell__nav">
          <TabsList aria-label="Project workspace sections">
            {workspaceTabs.map((tab) => (
              <TabsTrigger key={tab.id} value={tab.id}>
                {tab.label}
              </TabsTrigger>
            ))}
          </TabsList>
        </div>
        <TabsContent
          value="overview"
          className="project-workspace-shell__panel"
        >
          <OverviewContainer projectId={projectId} />
        </TabsContent>
        <TabsContent value="members" className="project-workspace-shell__panel">
          <MembersContainer projectId={projectId} />
        </TabsContent>
        <TabsContent
          value="artifacts"
          className="project-workspace-shell__panel"
        >
          <ArtifactsContainer projectId={projectId} />
        </TabsContent>
        <TabsContent value="jobs" className="project-workspace-shell__panel">
          <JobsContainer projectId={projectId} />
        </TabsContent>
        <TabsContent
          value="approvals"
          className="project-workspace-shell__panel"
        >
          <ApprovalsContainer projectId={projectId} />
        </TabsContent>
        <TabsContent value="audit" className="project-workspace-shell__panel">
          <AuditContainer projectId={projectId} />
        </TabsContent>
      </Tabs>
    </section>
  )
}
