import assert from "node:assert/strict"
import fs from "node:fs"
import path from "node:path"
import test from "node:test"
import { fileURLToPath } from "node:url"

const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)))
const read = (...parts) => fs.readFileSync(path.join(root, ...parts), "utf8")

test("M6 typed fixtures cover the frozen state matrix", () => {
  const fixtures = read(
    "src",
    "features",
    "manuscript-workspace",
    "fixtures",
    "index.ts",
  )
  for (const name of [
    "no-manuscript",
    "upload-available",
    "upload-forbidden",
    "upload-pending",
    "invalid-docx",
    "original-ready",
    "multiple-versions",
    "long-filename-hash-title",
    "unknown-version-status",
    "check-queued",
    "check-parsing",
    "check-rules",
    "check-project-consistency",
    "check-needs-review",
    "check-completed",
    "check-failed-retryable",
    "check-failed-non-retryable",
    "check-low-confidence",
    "check-cancelled",
    "issues-mixed-severity",
    "citation",
    "numeric-mismatch",
    "causal-risk",
    "terminology",
    "format-only",
    "resolved",
    "rejected",
    "invalidated",
    "long-excerpt",
    "evidence-available",
    "evidence-denied",
    "evidence-missing",
    "evidence-stale",
    "evidence-hash-mismatch",
    "read-only",
    "permissions-unknown",
    "forbidden",
    "load-error",
    "degraded-unknown",
    "fix-preview",
    "approval-pending",
    "approval-approved",
    "approval-stale",
    "approval-rejected",
    "execute-pending",
    "execute-failed",
    "execute-success-new-version",
    "revision-audit-running",
    "revision-audit-completed-mixed",
    "revision-audit-insufficient",
    "revision-audit-failed",
    "claim-draft",
    "claim-needs-evidence",
    "claim-supported",
    "claim-conflicted",
    "claim-insufficient",
    "claim-approval-pending",
    "claim-confirmed",
    "claim-read-only",
    "claim-permissions-unknown",
    "loading",
    "empty",
    "error",
    "mutation-conflict",
    "desktop-light",
    "tablet-dark",
    "mobile-light",
    "long-content",
  ])
    assert.match(fixtures, new RegExp(`"${name}"`), name)
  assert.match(fixtures, /satisfies readonly/)
  assert.match(fixtures, /permissionsKnown: false/)
  assert.match(fixtures, /FUTURE_VERSION_STATE/)
  assert.match(
    fixtures,
    /checkFixture\("check-queued", "QUEUED", "QUEUED", 0, false\)/,
  )
  assert.match(
    fixtures,
    /checkFixture\(\s*"check-failed-retryable",\s*"FAILED",\s*"FAILED",\s*62,\s*true/,
  )
  assert.match(fixtures, /evidenceFixture\("evidence-denied", "DENIED", null/)
  assert.match(
    fixtures,
    /transformationFixture\(\s*"approval-stale",\s*"APPROVED",\s*"APPROVED",\s*true/,
  )
  assert.match(fixtures, /pendingAction: "upload-manuscript"/)
  assert.match(
    fixtures,
    /mutationError: uiError\(\{ code: "PRECONDITION_FAILED", conflict: true \}\)/,
  )
})

test("M6 project discovery crosses generated, adapter and query boundaries", () => {
  const generated = read("src", "api", "generated", "sdk.gen.ts")
  const adapter = read("src", "api", "adapter", "index.ts")
  const query = read("src", "features", "manuscript-workspace", "queries.ts")
  assert.match(
    generated,
    /manuscriptsDiscoverProjectManuscriptGetApiV1ProjectsProjectIdManuscript/,
  )
  assert.match(adapter, /static discover = \(projectId: string\)/)
  assert.match(query, /ManuscriptsApi\.discover\(projectId\)/)
  assert.match(query, /discovery\.current_manuscript/)
  assert.match(query, /discovery\.versions\.filter/)
})

test("M6 registers one production route and all deep-link keys", () => {
  const route = read(
    "src",
    "features",
    "manuscript-workspace",
    "route-contract.ts",
  )
  assert.match(route, /\/projects\/\$projectId\/manuscript/)
  assert.match(route, /productionIntegrationComplete: true/)
  for (const key of [
    "manuscript",
    "version",
    "checkRun",
    "issue",
    "transformation",
    "audit",
    "claim",
    "view",
  ]) {
    assert.match(route, new RegExp(`"${key}"`), key)
  }
})

test("M6 UI exposes intent events without optimistic completion", () => {
  const contracts = read(
    "src",
    "features",
    "manuscript-workspace",
    "ui",
    "contracts.ts",
  )
  for (const action of [
    "upload-manuscript",
    "select-version",
    "start-check",
    "retry-job",
    "cancel-job",
    "accept-issue",
    "reject-issue",
    "create-fix-plan",
    "preview-fix-plan",
    "request-fix-approval",
    "execute-fix-plan",
    "start-revision-audit",
    "create-claim",
    "update-claim",
    "request-claim-confirmation",
    "download-version",
    "refresh",
  ])
    assert.match(contracts, new RegExp(`action: "${action}"`), action)
  assert.doesNotMatch(
    contracts,
    /mark-completed|optimistic-success|local-success/,
  )
})

test("M6 UI directory contains the contract and production display", () => {
  const ui = path.join(root, "src", "features", "manuscript-workspace", "ui")
  assert.deepEqual(fs.readdirSync(ui).sort(), [
    "ManuscriptWorkspace.tsx",
    "contracts.ts",
  ])
})
