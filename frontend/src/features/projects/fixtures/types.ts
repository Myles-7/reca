import type { ProjectViewModel } from "../model"
import type {
  ApprovalsPanelProps,
  ArtifactsPanelProps,
  AuditPanelProps,
  JobsPanelProps,
  MembersPanelProps,
  OverviewPanelProps,
} from "../ui/contracts"

export type ProjectWorkspaceDesignFixture = {
  id: string
  label: string
  behavior: string
  project: ProjectViewModel
  overview: OverviewPanelProps
  members: MembersPanelProps
  artifacts: ArtifactsPanelProps
  jobs: JobsPanelProps
  approvals: ApprovalsPanelProps
  audit: AuditPanelProps
}
