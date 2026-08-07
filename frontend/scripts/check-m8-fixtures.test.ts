import { expect, test } from "bun:test"

import {
  agentWorkspaceFixtureById as byId,
  agentWorkspaceFixtures as fixtures,
} from "../src/features/agent-workspace/fixtures"
import { canExecuteAgentWorkspaceEvent } from "../src/features/agent-workspace/mutations"
import {
  agentSourceWorkspaceHref,
  agentWorkspaceHref,
  parseAgentWorkspaceSearch,
} from "../src/features/agent-workspace/route-contract"

const workspace = (id: string) => {
  const fixture = byId[id]
  expect(fixture).toBeDefined()
  expect(fixture.content.state).toBe("ready")
  if (fixture.content.state !== "ready") throw new Error("fixture is not ready")
  return fixture.content.data
}

test("M8 fixture catalog is broad and carries responsive descriptors", () => {
  expect(fixtures.length).toBeGreaterThanOrEqual(50)
  expect(new Set(fixtures.map((fixture) => fixture.id)).size).toBe(
    fixtures.length,
  )
  expect(new Set(fixtures.map((fixture) => fixture.viewport))).toEqual(
    new Set(["desktop", "tablet", "mobile"]),
  )
  expect(new Set(fixtures.map((fixture) => fixture.theme))).toEqual(
    new Set(["light", "dark"]),
  )
  expect(fixtures.some((fixture) => fixture.pendingAction !== null)).toBeTrue()
  expect(fixtures.some((fixture) => fixture.mutationError?.conflict)).toBeTrue()
})

test("unknown permissions and status fail closed", () => {
  const unknown = workspace("permissions-unknown")
  expect(unknown.permissionsKnown).toBeFalse()
  expect(
    Object.entries(unknown.capabilities)
      .filter(([key]) => key !== "permissionsKnown")
      .every(([, value]) => typeof value === "object" && !value.allowed),
  ).toBeTrue()
  expect(workspace("tool-unknown").toolCalls[0].allowedActions.size).toBe(0)
  expect(workspace("source-stale").capabilities.cancelRun.allowed).toBeFalse()
  expect(workspace("resume-pending").capabilities.sendMessage.reason).toBe(
    "AGENT_RESUME_PENDING",
  )
})

test("events remain intents and require current server capability", () => {
  const waiting = workspace("waiting-user-input")
  expect(
    canExecuteAgentWorkspaceEvent(waiting, {
      action: "send-message",
      input: {
        runId: waiting.run!.id,
        message: "Continue with correlation only.",
      },
    }),
  ).toBeTrue()
  expect(
    canExecuteAgentWorkspaceEvent(waiting, {
      action: "send-message",
      input: { runId: "foreign", message: "Continue." },
    }),
  ).toBeFalse()
  expect(
    canExecuteAgentWorkspaceEvent(workspace("permissions-unknown"), {
      action: "create-run",
      input: { goal: "Review", mode: "PLAN_AND_EXPLAIN", allowToolCalls: true },
    }),
  ).toBeFalse()

  const cancellable = workspace("running-cancellable")
  const cancelBefore = structuredClone(cancellable)
  expect(
    canExecuteAgentWorkspaceEvent(cancellable, {
      action: "cancel-run",
      input: { runId: cancellable.run!.id },
    }),
  ).toBeTrue()
  expect(
    canExecuteAgentWorkspaceEvent(cancellable, {
      action: "cancel-run",
      input: { runId: "foreign" },
    }),
  ).toBeFalse()
  expect(cancellable).toEqual(cancelBefore)
  expect(byId["running-cancel-pending"].pendingAction).toBe("cancel-run")

  const retryable = workspace("tool-failed-retry-allowed")
  const retryBefore = structuredClone(retryable)
  expect(
    canExecuteAgentWorkspaceEvent(retryable, {
      action: "retry-or-restart",
      input: { runId: retryable.run!.id, goal: "Recheck current facts." },
    }),
  ).toBeTrue()
  expect(
    canExecuteAgentWorkspaceEvent(retryable, {
      action: "retry-or-restart",
      input: { runId: "foreign", goal: "Recheck current facts." },
    }),
  ).toBeFalse()
  const failedWithoutRetryableTool = workspace("agent-failed")
  expect(
    canExecuteAgentWorkspaceEvent(failedWithoutRetryableTool, {
      action: "retry-or-restart",
      input: {
        runId: failedWithoutRetryableTool.run!.id,
        goal: "Recheck current facts.",
      },
    }),
  ).toBeFalse()
  expect(retryable).toEqual(retryBefore)
  expect(byId["tool-retry-pending"].pendingAction).toBe("retry-or-restart")
})

test("suggestion, fact, result, confirmation and approval are distinct", () => {
  expect(
    new Set(
      workspace("fact-separation").timeline.map((event) => event.factKind),
    ),
  ).toEqual(
    new Set([
      "AGENT_SUGGESTION",
      "SYSTEM_FACT",
      "DETERMINISTIC_RESULT",
      "USER_CONFIRMATION",
      "FORMAL_APPROVAL",
    ]),
  )
  expect(workspace("suggestion-not-adopted").toolCalls[0].factKind).toBe(
    "AGENT_SUGGESTION",
  )
  expect(workspace("approval-stale").approvalStale).toBeTrue()
})

test("route contract rejects unsafe and incomplete deep links", () => {
  const run = "00000000-0000-4000-8000-000000000010"
  expect(
    parseAgentWorkspaceSearch({
      run,
      tool: "bad",
      sourceType: "Evidence Span",
      sourceId: run,
    }),
  ).toEqual({
    run,
    tool: undefined,
    sourceType: undefined,
    sourceId: undefined,
  })
  expect(agentWorkspaceHref("project 1", { run })).toBe(
    `/projects/project%201/agent?run=${run}`,
  )
  expect(agentSourceWorkspaceHref("project 1", "claim", run)).toBe(
    `/projects/project%201/evidence?claim=${run}&view=claims`,
  )
  expect(agentSourceWorkspaceHref("project 1", "generic_url", run)).toBeNull()
})

test("transport states do not become successful business facts", () => {
  expect(byId.loading.content.state).toBe("loading")
  expect(byId["empty-no-run"].content.state).toBe("empty")
  expect(byId["load-error"].content.state).toBe("error")
  expect(byId["mutation-pending"].pendingAction).toBe("send-message")
  expect(byId["mutation-conflict"].mutationError?.code).toBe(
    "IDEMPOTENCY_CONFLICT",
  )
})
