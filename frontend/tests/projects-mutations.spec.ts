import { expect, test } from "@playwright/test"
import {
  projectPermissionsUnknownFixture,
  projectUnknownStatusFixture,
  readyFixture,
} from "../src/features/projects/fixtures"
import {
  canExecuteApprovalAction,
  canExecuteArtifactDownload,
  canExecuteArtifactUpload,
  canExecuteJobAction,
  canExecuteMemberCommand,
  canExecuteMemberMutation,
  canExecuteProjectAction,
  executeApprovalAction,
  executeArtifactUpload,
  executeJobAction,
  executeMemberMutation,
  executeProjectLifecycle,
  executeProjectUpdate,
  getArtifactDownloadUrl,
  mutationUiError,
} from "../src/features/projects/mutations"

test("project mutations dispatch without changing lifecycle or lock semantics", async () => {
  const calls: unknown[] = []
  const commands = {
    archive: async (projectId: string) => calls.push(["archive", projectId]),
    restore: async (projectId: string) => calls.push(["restore", projectId]),
    update: async (projectId: string, input: unknown, lockVersion: number) =>
      calls.push(["update", projectId, input, lockVersion]),
  }

  await executeProjectLifecycle("project-1", false, commands)
  await executeProjectLifecycle("project-1", true, commands)
  await executeProjectUpdate(
    "project-1",
    { name: "Updated", description: null },
    7,
    commands,
  )

  expect(calls).toEqual([
    ["archive", "project-1"],
    ["restore", "project-1"],
    ["update", "project-1", { name: "Updated", description: null }, 7],
  ])
})

test("member mutations preserve add, role, ownership, and removal commands", async () => {
  const calls: unknown[] = []
  const commands = {
    add: async (projectId: string, input: unknown) =>
      calls.push(["add", projectId, input]),
    update: async (projectId: string, memberId: string, input: unknown) =>
      calls.push(["update", projectId, memberId, input]),
    remove: async (projectId: string, memberId: string) =>
      calls.push(["remove", projectId, memberId]),
  }

  await executeMemberMutation(
    "project-1",
    {
      action: "add",
      input: { userId: "user-2", role: "VIEWER" },
    },
    commands,
  )
  await executeMemberMutation(
    "project-1",
    {
      action: "change-role",
      input: { memberId: "member-2", role: "EDITOR" },
    },
    commands,
  )
  await executeMemberMutation(
    "project-1",
    {
      action: "transfer-ownership",
      input: {
        memberId: "member-2",
        previousOwnerRole: "EDITOR",
        reason: "Explicit ownership transfer",
      },
    },
    commands,
  )
  await executeMemberMutation(
    "project-1",
    { action: "remove", memberId: "member-2" },
    commands,
  )

  expect(calls).toEqual([
    ["add", "project-1", { user_id: "user-2", role: "VIEWER" }],
    ["update", "project-1", "member-2", { role: "EDITOR" }],
    [
      "update",
      "project-1",
      "member-2",
      {
        role: "OWNER",
        transferOwnership: true,
        previousOwnerRole: "EDITOR",
        reason: "Explicit ownership transfer",
      },
    ],
    ["remove", "project-1", "member-2"],
  ])
})

test("artifact, job, and approval commands retain safe fixed semantics", async () => {
  const calls: unknown[] = []
  const file = new File(["fixture"], "fixture.txt", { type: "text/plain" })
  const artifactCommands = {
    upload: async (projectId: string, inputFile: File, artifactType: "OTHER") =>
      calls.push(["upload", projectId, inputFile.name, artifactType]),
    download: async (artifactId: string) => {
      calls.push(["download", artifactId])
      return "https://example.test/artifact"
    },
  }
  const jobCommands = {
    retry: async (jobId: string) => calls.push(["retry", jobId]),
    cancel: async (jobId: string, reason: string) =>
      calls.push(["cancel-job", jobId, reason]),
  }
  const approvalCommands = {
    approve: async (approvalId: string, reason: string | null) =>
      calls.push(["approve", approvalId, reason]),
    reject: async (approvalId: string, reason: string) =>
      calls.push(["reject", approvalId, reason]),
    cancel: async (approvalId: string) =>
      calls.push(["cancel-approval", approvalId]),
  }

  await executeArtifactUpload("project-1", file, artifactCommands)
  expect(await getArtifactDownloadUrl("artifact-1", artifactCommands)).toBe(
    "https://example.test/artifact",
  )
  await executeJobAction({ jobId: "job-1", action: "retry" }, jobCommands)
  await executeJobAction({ jobId: "job-2", action: "cancel" }, jobCommands)
  await executeApprovalAction(
    { approvalId: "approval-1", action: "approve", reason: null },
    approvalCommands,
  )
  await executeApprovalAction(
    {
      approvalId: "approval-2",
      action: "reject",
      reason: "Rejected from project workspace",
    },
    approvalCommands,
  )
  await executeApprovalAction(
    { approvalId: "approval-3", action: "cancel", reason: null },
    approvalCommands,
  )

  expect(calls).toEqual([
    ["upload", "project-1", "fixture.txt", "OTHER"],
    ["download", "artifact-1"],
    ["retry", "job-1"],
    ["cancel-job", "job-2", "Cancelled from project workspace"],
    ["approve", "approval-1", null],
    ["reject", "approval-2", "Rejected from project workspace"],
    ["cancel-approval", "approval-3"],
  ])
})

test("mutation errors use the shared safe UI mapping", () => {
  expect(mutationUiError(null)).toBeNull()
  expect(mutationUiError(new Error("sensitive transport detail"))).toEqual({
    title: "Connection problem",
    message: "The workspace could not be loaded.",
    code: "NETWORK_ERROR",
    requestId: null,
    retryable: true,
    forbidden: false,
    notFound: false,
    conflict: false,
  })
})

test("project container guards fail closed for unknown permissions and status", () => {
  expect(canExecuteProjectAction(readyFixture.project, "update")).toBe(true)
  expect(
    canExecuteProjectAction(projectUnknownStatusFixture.project, "update"),
  ).toBe(false)

  const readyMembers = readyFixture.members.content
  const unknownMembers = projectPermissionsUnknownFixture.members.content
  expect(readyMembers.state).toBe("ready")
  expect(unknownMembers.state).toBe("ready")
  if (readyMembers.state !== "ready" || unknownMembers.state !== "ready") return
  expect(canExecuteMemberMutation(readyMembers.data.permissions)).toBe(true)
  expect(canExecuteMemberMutation(unknownMembers.data.permissions)).toBe(false)
  expect(
    canExecuteMemberCommand(
      readyMembers.data.members,
      readyMembers.data.permissions,
      { action: "remove", memberId: "member-reviewer" },
    ),
  ).toBe(true)
  expect(
    canExecuteMemberCommand(
      readyMembers.data.members,
      readyMembers.data.permissions,
      { action: "remove", memberId: "member-outside-projection" },
    ),
  ).toBe(false)
  expect(
    canExecuteMemberCommand(
      readyMembers.data.members,
      readyMembers.data.permissions,
      { action: "remove", memberId: "member-owner" },
    ),
  ).toBe(false)

  expect(
    canExecuteArtifactUpload({
      artifacts: [],
      permissionsKnown: true,
      canUpload: true,
    }),
  ).toBe(true)
  expect(
    canExecuteArtifactUpload({
      artifacts: [],
      permissionsKnown: false,
      canUpload: true,
    }),
  ).toBe(false)
  const artifacts = readyFixture.artifacts.content
  expect(artifacts.state).toBe("ready")
  if (artifacts.state !== "ready") return
  const artifactWorkspace = {
    artifacts: artifacts.data,
    permissionsKnown: true,
    canUpload: true,
  }
  expect(
    canExecuteArtifactDownload(artifactWorkspace, "artifact-protocol"),
  ).toBe(true)
  expect(
    canExecuteArtifactDownload(
      artifactWorkspace,
      "artifact-outside-projection",
    ),
  ).toBe(false)

  const jobs = readyFixture.jobs.content
  const approvals = readyFixture.approvals.content
  expect(jobs.state).toBe("ready")
  expect(approvals.state).toBe("ready")
  if (jobs.state !== "ready" || approvals.state !== "ready") return
  expect(
    canExecuteJobAction(jobs.data, readyFixture.jobs.permissions, {
      jobId: "job-parse",
      action: "cancel",
    }),
  ).toBe(true)
  expect(
    canExecuteJobAction(jobs.data, null, {
      jobId: "job-parse",
      action: "cancel",
    }),
  ).toBe(false)
  expect(
    canExecuteJobAction(jobs.data, readyFixture.jobs.permissions, {
      jobId: "job-parse",
      action: "retry",
    }),
  ).toBe(false)

  const approval = approvals.data[0]
  expect(
    canExecuteApprovalAction(approvals.data, {
      approvalId: approval.id,
      action: "approve",
      reason: null,
    }),
  ).toBe(true)
  expect(
    canExecuteApprovalAction([{ ...approval, stale: true }], {
      approvalId: approval.id,
      action: "approve",
      reason: null,
    }),
  ).toBe(false)
})
