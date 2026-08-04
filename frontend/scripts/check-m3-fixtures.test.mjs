import assert from "node:assert/strict"
import fs from "node:fs"
import path from "node:path"
import test from "node:test"
import { fileURLToPath } from "node:url"

const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)))
const read = (...parts) => fs.readFileSync(path.join(root, ...parts), "utf8")

test("M3 fixtures cover shared fail-closed states", () => {
  for (const feature of [
    "evidence-matrix",
    "evidence-analysis",
    "topic-candidates",
  ]) {
    const source = read("src", "features", feature, "fixtures", "index.ts")
    for (const state of [
      "ready",
      "loading",
      "empty",
      "error",
      "forbidden",
      "read-only",
      "permissions-unknown",
      "pending",
      "conflict",
      "degraded",
      "unknown",
      "long-content",
    ]) {
      assert.match(
        source,
        new RegExp(`\\"${state}`),
        `${feature} missing ${state}`,
      )
    }
  }
})

test("matrix fixtures preserve fixed evidence distinctions", () => {
  const source = read(
    "src",
    "features",
    "evidence-matrix",
    "fixtures",
    "index.ts",
  )
  for (const fact of [
    "NO_LOCATED_EVIDENCE",
    "LOCATION_UNCERTAIN",
    "VERIFIED",
    "PYPDF",
    "INCLUDED",
    "EXCLUDED",
    "UNCERTAIN",
  ])
    assert.match(source, new RegExp(fact))
})

test("analysis and topic fixtures retain scientific constraints", () => {
  const analysis = read(
    "src",
    "features",
    "evidence-analysis",
    "fixtures",
    "index.ts",
  )
  assert.match(analysis, /COUNTEREXAMPLE/)
  assert.match(analysis, /current included literature set/i)
  const topics = read(
    "src",
    "features",
    "topic-candidates",
    "fixtures",
    "index.ts",
  )
  assert.match(topics, /ready-exactly-three/)
  assert.match(topics, /failure-not-three/)
  assert.match(topics, /limitations: \["Cross-sectional evidence/)
  assert.doesNotMatch(topics, /limitations: null/)
})

test("preview registers all M3 workspaces and logs intents", () => {
  const source = read("src", "design-preview", "DesignPreviewWorkbench.tsx")
  for (const module of [
    "evidence-matrix",
    "evidence-analysis",
    "topic-candidates",
  ])
    assert.match(source, new RegExp(module))
  assert.match(source, /logIntent\(event\.action, event\.input\)/)
})

test("route draft freezes the single workspace search contract", () => {
  const source = read("src", "features", "literature", "m3-route-contract.ts")
  for (const key of [
    "documentId",
    "extractionId",
    "fieldId",
    "evidenceSpanId",
    "summaryId",
    "topicRunId",
  ])
    assert.match(source, new RegExp(key))
  assert.match(source, /\[\"matrix\", \"analysis\", \"topics\"\]/)
})
