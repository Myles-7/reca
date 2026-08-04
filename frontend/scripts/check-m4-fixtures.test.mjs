import assert from "node:assert/strict"
import fs from "node:fs"
import path from "node:path"
import test from "node:test"
import { fileURLToPath } from "node:url"

const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)))
const read = (...parts) => fs.readFileSync(path.join(root, ...parts), "utf8")

const fixtureSource = read(
  "src",
  "features",
  "data-workspace",
  "fixtures",
  "index.ts",
)

test("M4 fixtures cover the frozen workspace state matrix", () => {
  for (const fixture of [
    "ready",
    "loading",
    "empty",
    "error",
    "forbidden",
    "read-only",
    "permissions-unknown",
    "upload-pending",
    "upload-failure",
    "xlsx-worksheets",
    "invalidated",
    "quality-queued",
    "quality-running",
    "quality-failed",
    "quality-unknown",
    "plan-draft",
    "plan-needs-input",
    "plan-ready",
    "approval-pending",
    "approval-rejected",
    "approval-stale",
    "conflict",
    "transform-queued",
    "transform-running",
    "transform-failed",
    "future-enums",
    "long-content",
    "desktop-light",
    "tablet-dark",
    "mobile-light",
  ]) {
    assert.match(fixtureSource, new RegExp(`"${fixture}"`), fixture)
  }
})

test("fixtures preserve distinctions that UI must not collapse", () => {
  for (const fact of [
    "CREATING",
    "AVAILABLE",
    "inferredType",
    "confirmedType",
    "sensitiveCandidate",
    "sensitiveConfirmed",
    "clueOnly: true",
    "accepted: true",
    "completed: false",
    "stale: true",
    "RESOURCE_NOT_FOUND",
  ]) {
    assert.match(fixtureSource, new RegExp(fact))
  }
})

test("future enums and unknown permissions fail closed", () => {
  assert.match(fixtureSource, /FUTURE_VERSION_STATE/)
  assert.match(fixtureSource, /FUTURE_PLAN_STATE/)
  assert.match(fixtureSource, /FUTURE_JOB_STATE/)
  assert.match(fixtureSource, /Permissions are unknown\./)
  assert.match(fixtureSource, /permissionsKnown[^\n]*false/)
})

test("route draft freezes one project data workspace", () => {
  const source = read("src", "features", "data-workspace", "route-contract.ts")
  assert.match(source, /\/projects\/\$projectId\/data/)
  for (const key of [
    "dataset",
    "version",
    "qualityRun",
    "plan",
    "job",
    "compareWith",
  ]) {
    assert.match(source, new RegExp(`${key}:`))
  }
  assert.match(source, /productionIntegrationComplete: true/)
})

test("workspace events remain user intents and preview is registered", () => {
  const contracts = read(
    "src",
    "features",
    "data-workspace",
    "ui",
    "contracts.ts",
  )
  for (const action of [
    "upload-dataset",
    "select-worksheet",
    "update-dataset-identity",
    "update-column",
    "select-version",
    "compare-versions",
    "run-quality",
    "acknowledge-issue",
    "ignore-issue",
    "create-plan",
    "update-plan",
    "preview-plan",
    "request-approval",
    "execute-plan",
    "retry-job",
  ]) {
    assert.match(contracts, new RegExp(`action: "${action}"`), action)
  }

  const preview = read("src", "design-preview", "DesignPreviewWorkbench.tsx")
  assert.match(preview, /"data-workspace"/)
  assert.match(preview, /<DataWorkspace/)
  assert.match(preview, /logIntent\(event\.action, event\.input\)/)
})

test("M4 CleaningPlan actions and version comparison use typed projections", () => {
  const model = read("src", "features", "data-workspace", "model.ts")
  const contracts = read(
    "src",
    "features",
    "data-workspace",
    "ui",
    "contracts.ts",
  )
  for (const actionType of [
    "MARK_MISSING",
    "REPLACE_VALUE",
    "MAP_CATEGORY",
    "CAST_TYPE",
    "RENAME_COLUMN",
  ]) {
    assert.match(model, new RegExp(`type: "${actionType}"`), actionType)
  }
  assert.match(model, /compareVersions: ActionCapability/)
  assert.match(contracts, /readonly CleaningActionInput\[\]/)
  assert.doesNotMatch(contracts, /Record<string, unknown>/)
})

test("M4 capability fixtures keep empty, worksheet and Plan actions explicit", () => {
  assert.match(
    fixtureSource,
    /dataWorkspaceEmptyFixture[\s\S]*?uploadDataset: allowed\(true/,
  )
  assert.match(
    fixtureSource,
    /dataWorkspaceXlsxFixture[\s\S]*?selectWorksheet: allowed\(true/,
  )
  assert.match(
    fixtureSource,
    /dataWorkspacePlanDraftFixture[\s\S]*?updatePlan: allowed\(true[\s\S]*?previewPlan: allowed\(true/,
  )
  assert.match(
    fixtureSource,
    /dataWorkspacePlanReadyFixture[\s\S]*?requestApproval: allowed\(true/,
  )
})

test("M4 pure UI does not import protected integration layers", () => {
  const uiRoot = path.join(root, "src", "features", "data-workspace", "ui")
  for (const entry of fs.readdirSync(uiRoot)) {
    if (!/\.(ts|tsx)$/.test(entry)) continue
    const source = fs.readFileSync(path.join(uiRoot, entry), "utf8")
    assert.doesNotMatch(
      source,
      /@\/api\/(?:adapter|generated)|@tanstack\/react-query|\.\.\/(?:queries|mutations|containers)/,
      entry,
    )
  }
})
