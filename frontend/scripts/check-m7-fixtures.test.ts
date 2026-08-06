import { expect, test } from "bun:test"

import {
  evidenceWorkspaceFixtureById as byId,
  evidenceWorkspaceFixtures as fixtures,
} from "../src/features/evidence-workspace/fixtures"
import { canExecuteEvidenceWorkspaceEvent } from "../src/features/evidence-workspace/mutations"
import {
  evidenceWorkspaceHref,
  parseEvidenceWorkspaceSearch,
} from "../src/features/evidence-workspace/route-contract"

const workspace = (fixtureId: string) => {
  const fixture = byId[fixtureId]
  expect(fixture).toBeDefined()
  expect(fixture.content.state).toBe("ready")
  if (fixture.content.state !== "ready") throw new Error("fixture is not ready")
  return fixture.content.data
}

test("M7 fixtures are unique, broad and carry acceptance descriptors", () => {
  expect(fixtures.length).toBeGreaterThanOrEqual(60)
  expect(new Set(fixtures.map((fixture) => fixture.id)).size).toBe(
    fixtures.length,
  )
  expect(fixtures.some((fixture) => fixture.pendingAction !== null)).toBeTrue()
  expect(fixtures.some((fixture) => fixture.mutationError?.conflict)).toBeTrue()
  expect(new Set(fixtures.map((fixture) => fixture.viewport))).toEqual(
    new Set(["desktop", "tablet", "mobile"]),
  )
  expect(new Set(fixtures.map((fixture) => fixture.theme))).toEqual(
    new Set(["light", "dark"]),
  )
})

test("graph authority remains server-projected and progressive", () => {
  const large = workspace("graph-large-500")
  expect(large.graph.nodes).toHaveLength(500)
  expect(large.graph.partial).toBeTrue()
  expect(large.graph.complete).toBeFalse()
  expect(large.graph.nextCursor).toBe("cursor-after-500")
  expect(large.graph.canvasNodes.every((node) => !node.connectable)).toBeTrue()
  expect(
    large.graph.canvasEdges.every((edge) => !edge.reconnectable),
  ).toBeTrue()
  const full = workspace("graph-full-chain")
  expect(
    full.graph.edges.some((edge) => edge.sourceKind === "STORED"),
  ).toBeTrue()
  expect(
    full.graph.edges.some((edge) => edge.sourceKind === "DERIVED"),
  ).toBeTrue()
})

test("unknown permissions, status and denied scope fail closed", () => {
  const unknown = workspace("permissions-unknown")
  expect(unknown.permissionsKnown).toBeFalse()
  expect(
    Object.entries(unknown.capabilities)
      .filter(([key]) => key !== "permissionsKnown")
      .every(([, value]) => typeof value === "object" && !value.allowed),
  ).toBeTrue()
  expect(workspace("link-unknown").selectedLink?.allowedActions.size).toBe(0)
  const denied = workspace("evidence-denied-no-disclosure")
  expect(
    denied.scopeNotices.some((notice) => notice.scope === "DENIED"),
  ).toBeTrue()
  expect(denied.graph.nodes.some((node) => node.scope === "DENIED")).toBeFalse()
})

test("completeness remains categorical and never becomes a quality score", () => {
  for (const fixtureId of [
    "completeness-satisfied",
    "completeness-missing",
    "completeness-restricted",
    "completeness-conflicted",
    "completeness-unknown",
    "completeness-not-applicable",
  ]) {
    const item = Object.values(workspace(fixtureId).completeness)[0]
    expect(item.isScientificQualityScore).toBeFalse()
    expect(
      item.items.every((entry) => entry.scientificQualityScore === null),
    ).toBeTrue()
  }
  expect(
    Object.values(workspace("completeness-unknown").completeness)[0].items[0]
      .knownStatus,
  ).toBeFalse()
})

test("export, approval, manifest and package facts stay distinct", () => {
  expect(workspace("readiness-license-blocker").readiness?.ready).toBeFalse()
  expect(
    workspace("readiness-sensitive-warning").readiness?.requiresConfirmation,
  ).toBeTrue()
  expect(workspace("approval-stale").approval?.stale).toBeTrue()
  expect(
    workspace("approval-stale").capabilities.requestExportConfirmation.allowed,
  ).toBeFalse()
  expect(workspace("export-packaging").package).toBeNull()
  expect(workspace("export-completed").package?.status).toBe("AVAILABLE")
  expect(workspace("package-tampered").package?.tampered).toBeTrue()
  expect(workspace("package-tampered").package?.allowedActions.size).toBe(0)
  const manifest = workspace("graph-full-chain").package?.manifest
  expect(manifest?.agentLogs).toBe("NOT_AVAILABLE")
  expect(
    manifest?.files.some((file) => file.redistribution === "METADATA_ONLY"),
  ).toBeTrue()
  const history = workspace("package-history-versions")
  expect(history.packageHistory).toHaveLength(3)
  expect(new Set(history.packageHistory.map((item) => item.id)).size).toBe(3)
  expect(history.packageHistory.filter((item) => item.selected)).toHaveLength(1)
  expect(new Set(history.packageHistory.map((item) => item.sha256)).size).toBe(
    3,
  )
})

test("audit jobs and executable job fixtures remain distinct", () => {
  const audit = workspace("graph-full-chain")
  expect(audit.audit?.jobId).toBe(audit.auditJob?.id)
  expect(audit.auditJob?.taskType).toBe("EVIDENCE_AUDIT")
  expect(audit.job?.taskType).toBe("REPRO_PACKAGE_EXPORT")

  const suggested = workspace("link-suggested")
  expect(suggested.capabilities.confirmEvidenceLink.allowed).toBeTrue()
  expect(
    canExecuteEvidenceWorkspaceEvent(suggested, {
      action: "confirm-evidence-link",
      linkId: suggested.selectedLink?.id ?? "",
      lockVersion: suggested.selectedLink?.lockVersion ?? 0,
    }),
  ).toBeTrue()

  const failed = workspace("export-failed-retryable")
  expect(
    canExecuteEvidenceWorkspaceEvent(failed, {
      action: "retry-job",
      jobId: failed.job?.id ?? "",
    }),
  ).toBeTrue()

  const running = workspace("export-running-cancellable")
  expect(
    canExecuteEvidenceWorkspaceEvent(running, {
      action: "cancel-job",
      jobId: running.job?.id ?? "",
      reason: "Stop this export.",
    }),
  ).toBeTrue()
})

test("transport states are not represented as successful business facts", () => {
  expect(byId.loading.content.state).toBe("loading")
  expect(byId.empty.content.state).toBe("empty")
  expect(byId["load-error"].content.state).toBe("error")
  expect(byId["mutation-pending"].pendingAction).toBe("create-repro-package")
  expect(byId["mutation-conflict"].mutationError?.code).toBe(
    "PRECONDITION_FAILED",
  )
})

test("route and mutation contracts fail closed on stale or mismatched facts", () => {
  expect(
    parseEvidenceWorkspaceSearch({
      claim: "claim-1",
      view: "exports",
      node: "",
      audit: "x".repeat(256),
    }),
  ).toEqual({ claim: "claim-1", view: "exports" })
  expect(evidenceWorkspaceHref("project 1", { claim: "claim-1" })).toBe(
    "/projects/project%201/evidence?claim=claim-1",
  )

  const current = workspace("graph-full-chain")
  expect(
    canExecuteEvidenceWorkspaceEvent(current, {
      action: "invalidate-evidence-link",
      linkId: current.selectedLink?.id ?? "",
      lockVersion: current.selectedLink?.lockVersion ?? 0,
      reason: "Source was invalidated.",
    }),
  ).toBeTrue()
  expect(
    canExecuteEvidenceWorkspaceEvent(current, {
      action: "invalidate-evidence-link",
      linkId: current.selectedLink?.id ?? "",
      lockVersion: 999,
      reason: "Source was invalidated.",
    }),
  ).toBeFalse()
  expect(
    canExecuteEvidenceWorkspaceEvent(workspace("permissions-unknown"), {
      action: "run-export-readiness",
      input: {
        includeOriginalLiteratureFiles: false,
        includeDatasetVersions: true,
        includeSensitiveData: false,
        includeAgentLogs: false,
        includeModelOutputArtifacts: false,
        acknowledgeLicenseWarnings: false,
      },
    }),
  ).toBeFalse()
  const stale = workspace("approval-stale")
  expect(
    canExecuteEvidenceWorkspaceEvent(stale, {
      action: "request-export-confirmation",
      exportId: stale.export?.id ?? "",
      approvalId: stale.approval?.id ?? "",
    }),
  ).toBeFalse()
  const tampered = workspace("package-tampered")
  expect(
    canExecuteEvidenceWorkspaceEvent(tampered, {
      action: "download-repro-package",
      packageId: tampered.package?.id ?? "",
    }),
  ).toBeFalse()
})
