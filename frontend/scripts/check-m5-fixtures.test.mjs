import assert from "node:assert/strict"
import fs from "node:fs"
import path from "node:path"
import test from "node:test"
import { fileURLToPath } from "node:url"

const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)))
const read = (...parts) => fs.readFileSync(path.join(root, ...parts), "utf8")
const fixtures = read(
  "src",
  "features",
  "analysis-workspace",
  "fixtures",
  "index.ts",
)

test("M5 fixtures cover formal Analysis and Figure transport states", () => {
  for (const fixture of [
    "ready",
    "loading",
    "empty",
    "error",
    "forbidden",
    "read-only",
    "permissions-unknown",
    "degraded",
    "unknown",
    "unconfirmed-columns",
    "quality-warnings",
    "sensitive-ack-required",
    "plan-draft",
    "plan-needs-input",
    "plan-ready",
    "plan-pending-approval",
    "plan-approved",
    "plan-rejected",
    "plan-stale",
    "plan-invalidated",
    "assumption-pass",
    "assumption-warning",
    "assumption-fail",
    "assumption-confirm",
    "analysis-queued",
    "analysis-running",
    "analysis-completed",
    "analysis-failed-retryable",
    "analysis-failed-final",
    "analysis-invalidated",
    "job-retry-allowed",
    "job-cancel-allowed",
    "descriptive",
    "correlation-significant",
    "correlation-non-significant",
    "group-comparison",
    "regression",
    "figure-draft",
    "figure-rendering",
    "figure-ready",
    "figure-needs-review",
    "figure-confirmed",
    "figure-failed",
    "figure-invalidated",
    "figure-approval-decision",
    "figure-job-cancel-allowed",
    "masked-artifact",
    "download-scope-denied",
    "mutation-conflict",
    "desktop-light",
    "tablet-dark",
    "mobile-light",
  ]) {
    assert.match(fixtures, new RegExp(`"${fixture}"`), fixture)
  }
})

test("M5 fixtures preserve fail-closed and scientific fact distinctions", () => {
  for (const fact of [
    "permissionsKnown: false",
    "FUTURE_ANALYSIS_PLAN_STATE",
    'planStatus("APPROVED", true)',
    "deterministic: true",
    "interpretation: null",
    "transportAvailable: true",
    "[MASKED]",
    "EXTERNAL_OUTPUT_INVALID",
  ]) {
    assert.match(
      fixtures,
      new RegExp(fact.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")),
    )
  }
})

test("M5 freezes one production route and all deep-link keys", () => {
  const route = read(
    "src",
    "features",
    "analysis-workspace",
    "route-contract.ts",
  )
  assert.match(route, /\/projects\/\$projectId\/analysis/)
  assert.match(route, /productionIntegrationComplete: true/)
  for (const key of [
    "dataset",
    "version",
    "analysisPlan",
    "analysisRun",
    "analysisResult",
    "approval",
    "job",
    "figurePlan",
    "figure",
    "renderRun",
    "view",
  ]) {
    assert.match(route, new RegExp(`${key}:`), key)
  }
})

test("M5 UI events express intentions and include no success event", () => {
  const contracts = read(
    "src",
    "features",
    "analysis-workspace",
    "ui",
    "contracts.ts",
  )
  for (const action of [
    "create-analysis-plan",
    "update-analysis-plan",
    "validate-analysis-plan",
    "request-analysis-approval",
    "run-analysis",
    "invalidate-analysis-run",
    "retry-job",
    "cancel-job",
    "create-figure-plan",
    "render-figure",
    "request-figure-confirmation",
    "decide-figure-confirmation",
    "download-artifact",
    "request-suggestion",
    "request-interpretation",
  ]) {
    assert.match(contracts, new RegExp(`action: "${action}"`), action)
  }
  assert.doesNotMatch(contracts, /optimistic|success-event|mark-completed/)
})
