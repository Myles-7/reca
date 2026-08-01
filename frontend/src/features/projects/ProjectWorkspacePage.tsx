import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import {
  Archive,
  ArchiveRestore,
  ArrowLeft,
  Check,
  Download,
  RotateCcw,
  Trash2,
  Upload,
  X,
} from "lucide-react"
import { type FormEvent, useState } from "react"

import {
  EmptyState,
  ErrorState,
  LoadingState,
} from "@/components/Common/PageState"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import useAuth from "@/hooks/useAuth"

import {
  approvalCommands,
  downloadArtifact,
  jobCommands,
  memberCommands,
  projectCommands,
  uploadArtifact,
} from "./controller"
import { mapUiError } from "./mappers"
import type {
  MemberRoleOption,
  MemberUpdateCommand,
  SemanticTone,
  WorkspacePermissions,
} from "./model"
import {
  projectKeys,
  useApprovals,
  useArtifacts,
  useAudit,
  useJobEvents,
  useJobs,
  useMembers,
  useOverview,
  useProject,
} from "./queries"

function toneVariant(
  tone: SemanticTone,
): "default" | "secondary" | "destructive" | "outline" {
  if (tone === "danger") return "destructive"
  if (tone === "success" || tone === "info") return "default"
  if (tone === "warning" || tone === "degraded") return "secondary"
  return "outline"
}

function QueryState({
  query,
  label,
}: {
  query: { isLoading: boolean; error: unknown }
  label: string
}) {
  if (query.isLoading) return <LoadingState label={`Loading ${label}`} />
  if (query.error)
    return <ErrorState message={mapUiError(query.error).message} />
  return null
}

export function ProjectWorkspacePage({ projectId }: { projectId: string }) {
  const { user } = useAuth()
  const project = useProject(projectId)
  const overview = useOverview(projectId)
  const members = useMembers(projectId, user?.id)
  const artifacts = useArtifacts(projectId)
  const jobs = useJobs(projectId)
  const approvals = useApprovals(projectId)
  const audit = useAudit(projectId)

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
    <section aria-labelledby="workspace-title" className="space-y-6">
      <header className="space-y-4">
        <Button asChild size="sm" variant="ghost">
          <Link to="/projects">
            <ArrowLeft aria-hidden="true" /> Projects
          </Link>
        </Button>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h1 id="workspace-title" className="text-2xl font-semibold">
                {project.data.name}
              </h1>
              <Badge variant="outline">{project.data.status}</Badge>
            </div>
            <p className="mt-1 text-sm text-muted-foreground">
              {project.data.description || "No project description"}
            </p>
          </div>
          <div className="flex items-start gap-3">
            <div className="text-right text-xs text-muted-foreground">
              <p>{project.data.type}</p>
              <p>{project.data.stage}</p>
            </div>
            {project.data.canUpdate ? (
              <EditProjectDialog projectId={projectId} project={project.data} />
            ) : null}
            {project.data.canDelete && project.data.status !== "DELETED" ? (
              <ProjectLifecycleButton
                projectId={projectId}
                status={project.data.status}
              />
            ) : null}
          </div>
        </div>
      </header>

      <Tabs defaultValue="overview">
        <TabsList className="h-auto w-full flex-wrap justify-start">
          {[
            "overview",
            "members",
            "artifacts",
            "jobs",
            "approvals",
            "audit",
          ].map((tab) => (
            <TabsTrigger key={tab} value={tab} className="capitalize">
              {tab}
            </TabsTrigger>
          ))}
        </TabsList>
        <TabsContent value="overview">
          <OverviewPanel query={overview} />
        </TabsContent>
        <TabsContent value="members">
          <MembersPanel projectId={projectId} query={members} />
        </TabsContent>
        <TabsContent value="artifacts">
          <ArtifactsPanel
            projectId={projectId}
            query={artifacts}
            canUpload={members.data?.permissions.canUploadArtifact === true}
          />
        </TabsContent>
        <TabsContent value="jobs">
          <JobsPanel
            projectId={projectId}
            query={jobs}
            permissions={members.data?.permissions}
          />
        </TabsContent>
        <TabsContent value="approvals">
          <ApprovalsPanel projectId={projectId} query={approvals} />
        </TabsContent>
        <TabsContent value="audit">
          <AuditPanel query={audit} />
        </TabsContent>
      </Tabs>
    </section>
  )
}

function ProjectLifecycleButton({
  projectId,
  status,
}: {
  projectId: string
  status: string
}) {
  const queryClient = useQueryClient()
  const restore = status === "ARCHIVED"
  const mutation = useMutation({
    mutationFn: () =>
      restore
        ? projectCommands.restore(projectId)
        : projectCommands.archive(projectId),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: projectKeys.all }),
        queryClient.invalidateQueries({
          queryKey: projectKeys.detail(projectId),
        }),
        queryClient.invalidateQueries({
          queryKey: projectKeys.overview(projectId),
        }),
        queryClient.invalidateQueries({
          queryKey: projectKeys.audit(projectId),
        }),
      ])
    },
  })
  return (
    <div>
      <Button
        size="sm"
        variant="outline"
        disabled={mutation.isPending}
        onClick={() => mutation.mutate()}
      >
        {restore ? (
          <ArchiveRestore aria-hidden="true" />
        ) : (
          <Archive aria-hidden="true" />
        )}
        {restore ? "Restore" : "Archive"}
      </Button>
      {mutation.error ? (
        <div className="mt-2">
          <ErrorState message={mapUiError(mutation.error).message} />
        </div>
      ) : null}
    </div>
  )
}

function EditProjectDialog({
  projectId,
  project,
}: {
  projectId: string
  project: NonNullable<ReturnType<typeof useProject>["data"]>
}) {
  const queryClient = useQueryClient()
  const [open, setOpen] = useState(false)
  const update = useMutation({
    mutationFn: (input: { name: string; description: string | null }) =>
      projectCommands.update(projectId, input, project.lockVersion),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: projectKeys.detail(projectId),
      })
      setOpen(false)
    },
  })
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const data = new FormData(event.currentTarget)
    update.mutate({
      name: String(data.get("name") ?? "").trim(),
      description: String(data.get("description") ?? "").trim() || null,
    })
  }
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm" variant="outline">
          Edit project
        </Button>
      </DialogTrigger>
      <DialogContent>
        <form className="space-y-5" onSubmit={submit}>
          <DialogHeader>
            <DialogTitle>Edit project</DialogTitle>
            <DialogDescription>
              Updates use the current project version for conflict detection.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            <Label htmlFor="edit-project-name">Name</Label>
            <Input
              id="edit-project-name"
              name="name"
              defaultValue={project.name}
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="edit-project-description">Description</Label>
            <Input
              id="edit-project-description"
              name="description"
              defaultValue={project.description ?? ""}
            />
          </div>
          {update.error ? (
            <ErrorState message={mapUiError(update.error).message} />
          ) : null}
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setOpen(false)}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={update.isPending}>
              {update.isPending ? "Saving..." : "Save"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

function OverviewPanel({ query }: { query: ReturnType<typeof useOverview> }) {
  return (
    <div className="space-y-6 py-4">
      <QueryState query={query} label="project overview" />
      {query.data ? (
        <>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
            {query.data.foundationCounts.map((item) => (
              <div key={item.label} className="rounded-lg border bg-card p-4">
                <p className="text-xs text-muted-foreground">{item.label}</p>
                <p className="mt-2 text-2xl font-semibold">
                  {item.value ?? "Unavailable"}
                </p>
              </div>
            ))}
          </div>
          <div>
            <h2 className="mb-3 font-semibold">Research capabilities</h2>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {query.data.capabilities.map((capability) => (
                <div
                  key={capability.key}
                  className="flex items-center justify-between rounded-lg border p-4"
                >
                  <span className="text-sm font-medium">
                    {capability.label}
                  </span>
                  <Badge variant={toneVariant(capability.tone)}>
                    {capability.availability === "AVAILABLE"
                      ? (capability.value ?? "Available")
                      : capability.availability === "DEGRADED"
                        ? "Degraded"
                        : "Not available"}
                  </Badge>
                </div>
              ))}
            </div>
          </div>
        </>
      ) : null}
    </div>
  )
}

function MembersPanel({
  projectId,
  query,
}: {
  projectId: string
  query: ReturnType<typeof useMembers>
}) {
  const queryClient = useQueryClient()
  const [role, setRole] = useState<MemberRoleOption>("VIEWER")
  const mutation = useMutation<
    unknown,
    Error,
    {
      memberId?: string
      input?: MemberUpdateCommand
      userId?: string
      remove?: boolean
    }
  >({
    mutationFn: async (command) => {
      if (command.remove && command.memberId)
        return await memberCommands.remove(projectId, command.memberId)
      if (command.memberId && command.input)
        return await memberCommands.update(
          projectId,
          command.memberId,
          command.input,
        )
      return await memberCommands.add(projectId, {
        user_id: command.userId ?? "",
        role,
      })
    },
    onSuccess: () =>
      queryClient.invalidateQueries({
        queryKey: projectKeys.members(projectId),
      }),
  })
  function add(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const data = new FormData(event.currentTarget)
    mutation.mutate({ userId: String(data.get("user_id") ?? "").trim() })
    event.currentTarget.reset()
  }
  return (
    <div className="space-y-4 py-4">
      <QueryState query={query} label="members" />
      {query.data?.permissions.canManageMembers ? (
        <form
          className="flex flex-wrap items-end gap-3 rounded-lg border p-4"
          onSubmit={add}
        >
          <div className="min-w-64 flex-1 space-y-2">
            <Label htmlFor="member-user-id">User ID</Label>
            <Input id="member-user-id" name="user_id" required />
          </div>
          <Select
            value={role}
            onValueChange={(value) => setRole(value as typeof role)}
          >
            <SelectTrigger aria-label="Member role">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="EDITOR">EDITOR</SelectItem>
              <SelectItem value="REVIEWER">REVIEWER</SelectItem>
              <SelectItem value="VIEWER">VIEWER</SelectItem>
            </SelectContent>
          </Select>
          <Button disabled={mutation.isPending} type="submit">
            Add member
          </Button>
        </form>
      ) : null}
      {mutation.error ? (
        <ErrorState message={mapUiError(mutation.error).message} />
      ) : null}
      {query.data?.members.length === 0 ? (
        <EmptyState>No project members.</EmptyState>
      ) : null}
      {query.data?.members.length ? (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Member</TableHead>
              <TableHead>Role</TableHead>
              <TableHead>Joined</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {query.data.members.map((member) => (
              <TableRow key={member.id}>
                <TableCell>
                  <p className="font-medium">{member.displayName}</p>
                  <p className="text-xs text-muted-foreground">
                    {member.email}
                  </p>
                </TableCell>
                <TableCell>
                  <Badge variant={member.isOwner ? "default" : "outline"}>
                    {member.role}
                  </Badge>
                </TableCell>
                <TableCell>{member.joinedAt}</TableCell>
                <TableCell className="text-right">
                  {query.data.permissions.canManageMembers &&
                  !member.isOwner ? (
                    <div className="flex justify-end gap-2">
                      <Select
                        value={member.role}
                        onValueChange={(value) =>
                          mutation.mutate({
                            memberId: member.id,
                            input: {
                              role: value as MemberRoleOption,
                            },
                          })
                        }
                      >
                        <SelectTrigger
                          size="sm"
                          aria-label={`Role for ${member.displayName}`}
                        >
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="EDITOR">EDITOR</SelectItem>
                          <SelectItem value="REVIEWER">REVIEWER</SelectItem>
                          <SelectItem value="VIEWER">VIEWER</SelectItem>
                        </SelectContent>
                      </Select>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() =>
                          mutation.mutate({
                            memberId: member.id,
                            input: {
                              role: "OWNER",
                              transferOwnership: true,
                              previousOwnerRole: "EDITOR",
                              reason: "Explicit ownership transfer",
                            },
                          })
                        }
                      >
                        Transfer ownership
                      </Button>
                      <Button
                        aria-label={`Remove ${member.displayName}`}
                        size="icon-sm"
                        variant="ghost"
                        onClick={() =>
                          mutation.mutate({ memberId: member.id, remove: true })
                        }
                      >
                        <Trash2 aria-hidden="true" />
                      </Button>
                    </div>
                  ) : null}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      ) : null}
    </div>
  )
}

function ArtifactsPanel({
  projectId,
  query,
  canUpload,
}: {
  projectId: string
  query: ReturnType<typeof useArtifacts>
  canUpload: boolean
}) {
  const queryClient = useQueryClient()
  const upload = useMutation({
    mutationFn: (file: File) => uploadArtifact(projectId, file, "OTHER"),
    onSuccess: () =>
      queryClient.invalidateQueries({
        queryKey: projectKeys.artifacts(projectId),
      }),
  })
  async function download(artifactId: string) {
    window.location.assign(await downloadArtifact(artifactId))
  }
  return (
    <div className="space-y-4 py-4">
      <QueryState query={query} label="artifacts" />
      {canUpload ? (
        <div className="flex flex-wrap items-center gap-3 rounded-lg border p-4">
          <Label htmlFor="artifact-file">Upload original artifact</Label>
          <Input
            id="artifact-file"
            type="file"
            className="max-w-md"
            disabled={upload.isPending}
            onChange={(event) => {
              const file = event.target.files?.[0]
              if (file) upload.mutate(file)
            }}
          />
          <Upload aria-hidden="true" className="size-4 text-muted-foreground" />
        </div>
      ) : null}
      {upload.isPending ? (
        <LoadingState label="Uploading and verifying artifact" />
      ) : null}
      {upload.error ? (
        <ErrorState message={mapUiError(upload.error).message} />
      ) : null}
      {query.data?.length === 0 ? (
        <EmptyState>No artifacts have been uploaded.</EmptyState>
      ) : null}
      {query.data?.length ? (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>File</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Size</TableHead>
              <TableHead className="text-right">Download</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {query.data.map((artifact) => (
              <TableRow key={artifact.id}>
                <TableCell>
                  <p className="font-medium">{artifact.filename}</p>
                  <p className="font-mono text-xs text-muted-foreground">
                    {artifact.sha256.slice(0, 16)}...
                  </p>
                </TableCell>
                <TableCell>
                  {artifact.origin} · {artifact.kind}
                </TableCell>
                <TableCell>
                  <Badge variant="outline">{artifact.status}</Badge>
                </TableCell>
                <TableCell>{artifact.size}</TableCell>
                <TableCell className="text-right">
                  <Button
                    aria-label={`Download ${artifact.filename}`}
                    disabled={!artifact.canDownload}
                    size="icon-sm"
                    variant="ghost"
                    onClick={() => download(artifact.id)}
                  >
                    <Download aria-hidden="true" />
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      ) : null}
    </div>
  )
}

function JobsPanel({
  projectId,
  query,
  permissions,
}: {
  projectId: string
  query: ReturnType<typeof useJobs>
  permissions: WorkspacePermissions | undefined
}) {
  const queryClient = useQueryClient()
  const activeJobId = query.data?.find((job) => job.active)?.id
  const streamState = useJobEvents(activeJobId)
  const action = useMutation({
    mutationFn: ({ id, kind }: { id: string; kind: "retry" | "cancel" }) =>
      kind === "retry"
        ? jobCommands.retry(id)
        : jobCommands.cancel(id, "Cancelled from project workspace"),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: projectKeys.jobs(projectId) }),
  })
  return (
    <div className="space-y-4 py-4">
      <QueryState query={query} label="jobs" />
      <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
        <span>Live updates</span>
        <Badge variant={streamState === "degraded" ? "secondary" : "outline"}>
          {streamState}
        </Badge>
        <span>Polling remains the fallback for active jobs.</span>
      </div>
      {action.error ? (
        <ErrorState message={mapUiError(action.error).message} />
      ) : null}
      {query.data?.length === 0 ? (
        <EmptyState>
          No jobs have been created by M1 domain services.
        </EmptyState>
      ) : null}
      {query.data?.length ? (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Job</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Progress</TableHead>
              <TableHead>Attempts</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {query.data.map((job) => (
              <TableRow key={job.id}>
                <TableCell>
                  <p className="font-medium">{job.taskLabel}</p>
                  {job.error ? (
                    <p className="text-xs text-destructive">{job.error}</p>
                  ) : null}
                </TableCell>
                <TableCell>
                  <Badge variant={toneVariant(job.tone)}>{job.status}</Badge>
                </TableCell>
                <TableCell>{job.progress}%</TableCell>
                <TableCell>
                  {job.retryCount}/{job.maxRetries}
                </TableCell>
                <TableCell className="text-right">
                  <div className="flex justify-end gap-1">
                    <Button
                      aria-label="Retry job"
                      disabled={!job.retryable || !permissions?.canRetryJob}
                      size="icon-sm"
                      variant="ghost"
                      onClick={() =>
                        action.mutate({ id: job.id, kind: "retry" })
                      }
                    >
                      <RotateCcw aria-hidden="true" />
                    </Button>
                    <Button
                      aria-label="Cancel job"
                      disabled={!job.active || !permissions?.canCancelJob}
                      size="icon-sm"
                      variant="ghost"
                      onClick={() =>
                        action.mutate({ id: job.id, kind: "cancel" })
                      }
                    >
                      <X aria-hidden="true" />
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      ) : null}
    </div>
  )
}

function ApprovalsPanel({
  projectId,
  query,
}: {
  projectId: string
  query: ReturnType<typeof useApprovals>
}) {
  const queryClient = useQueryClient()
  const action = useMutation({
    mutationFn: ({
      id,
      kind,
    }: {
      id: string
      kind: "approve" | "reject" | "cancel"
    }) =>
      kind === "approve"
        ? approvalCommands.approve(id, null)
        : kind === "reject"
          ? approvalCommands.reject(id, "Rejected from project workspace")
          : approvalCommands.cancel(id),
    onSuccess: () =>
      queryClient.invalidateQueries({
        queryKey: projectKeys.approvals(projectId),
      }),
  })
  return (
    <div className="space-y-4 py-4">
      <QueryState query={query} label="approvals" />
      <p className="text-xs text-muted-foreground">
        Approvals are created only by their owning domain service.
      </p>
      {action.error ? (
        <ErrorState message={mapUiError(action.error).message} />
      ) : null}
      {query.data?.length === 0 ? (
        <EmptyState>No approval requests require attention.</EmptyState>
      ) : null}
      {query.data?.length ? (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Approval</TableHead>
              <TableHead>Target</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Requested</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {query.data.map((approval) => (
              <TableRow key={approval.id}>
                <TableCell>
                  <p className="font-medium">{approval.type}</p>
                  <p className="font-mono text-xs text-muted-foreground">
                    {approval.payloadHash.slice(0, 16)}...
                  </p>
                </TableCell>
                <TableCell>{approval.target}</TableCell>
                <TableCell>
                  <Badge variant={toneVariant(approval.tone)}>
                    {approval.status}
                  </Badge>
                </TableCell>
                <TableCell>{approval.requestedAt}</TableCell>
                <TableCell className="text-right">
                  <div className="flex justify-end gap-1">
                    <Button
                      aria-label="Approve"
                      disabled={
                        !approval.allowedActions.has("approval.approve")
                      }
                      size="icon-sm"
                      variant="ghost"
                      onClick={() =>
                        action.mutate({ id: approval.id, kind: "approve" })
                      }
                    >
                      <Check aria-hidden="true" />
                    </Button>
                    <Button
                      aria-label="Reject"
                      disabled={!approval.allowedActions.has("approval.reject")}
                      size="icon-sm"
                      variant="ghost"
                      onClick={() =>
                        action.mutate({ id: approval.id, kind: "reject" })
                      }
                    >
                      <X aria-hidden="true" />
                    </Button>
                    <Button
                      aria-label="Cancel approval"
                      disabled={!approval.allowedActions.has("approval.cancel")}
                      size="icon-sm"
                      variant="ghost"
                      onClick={() =>
                        action.mutate({ id: approval.id, kind: "cancel" })
                      }
                    >
                      <Trash2 aria-hidden="true" />
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      ) : null}
    </div>
  )
}

function AuditPanel({ query }: { query: ReturnType<typeof useAudit> }) {
  return (
    <div className="space-y-4 py-4">
      <QueryState query={query} label="audit history" />
      {query.data?.length === 0 ? (
        <EmptyState>No audit events are visible.</EmptyState>
      ) : null}
      {query.data?.length ? (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Action</TableHead>
              <TableHead>Actor</TableHead>
              <TableHead>Target</TableHead>
              <TableHead>Outcome</TableHead>
              <TableHead>Time</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {query.data.map((event) => (
              <TableRow key={event.id}>
                <TableCell>
                  <p className="font-medium">{event.action}</p>
                  {event.requestId ? (
                    <p className="font-mono text-xs text-muted-foreground">
                      {event.requestId}
                    </p>
                  ) : null}
                </TableCell>
                <TableCell>{event.actor}</TableCell>
                <TableCell>{event.target}</TableCell>
                <TableCell>
                  <Badge variant={toneVariant(event.tone)}>
                    {event.outcome}
                  </Badge>
                </TableCell>
                <TableCell>{event.occurredAt}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      ) : null}
    </div>
  )
}
