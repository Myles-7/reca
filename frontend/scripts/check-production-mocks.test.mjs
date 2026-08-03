import assert from "node:assert/strict"
import fs from "node:fs"
import os from "node:os"
import path from "node:path"
import test from "node:test"

import { scanProductionMockViolations } from "./check-production-mocks.mjs"

function workspace(files) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "reca-mock-guard-"))
  for (const [file, source] of Object.entries(files)) {
    const target = path.join(root, file)
    fs.mkdirSync(path.dirname(target), { recursive: true })
    fs.writeFileSync(target, source)
  }
  return root
}

test("allows ordinary production source without fixtures", () => {
  const root = workspace({
    "feature/query.ts": 'import type { Loadable } from "./model"',
  })
  assert.deepEqual(scanProductionMockViolations(root, root), [])
})

test("allows fixtures and the explicit design preview to reference fixtures", () => {
  const root = workspace({
    "features/projects/fixtures/index.ts":
      'import type { Loadable } from "../model"; export const readyFixture = { state: "ready" } satisfies Loadable<unknown>',
    "design-preview/main.tsx":
      'import { readyFixture } from "../features/projects/fixtures"',
  })
  assert.deepEqual(scanProductionMockViolations(root, root), [])
})

test("rejects API and data-layer imports from fixture definitions", () => {
  const root = workspace({
    "features/research-question/fixtures/index.ts":
      'import type { ProjectPublic } from "../../../api/adapter"',
  })
  assert.equal(scanProductionMockViolations(root, root).length, 1)
})

test("rejects fixture imports from production data paths", () => {
  const root = workspace({
    "features/projects/queries.ts": 'import { readyFixture } from "./fixtures"',
  })
  assert.deepEqual(scanProductionMockViolations(root, root), [
    {
      file: path.join("features", "projects", "queries.ts"),
      imports: ["./fixtures"],
    },
  ])
})

test("rejects production imports of the design preview", () => {
  const root = workspace({
    "main.tsx": 'import "./design-preview/main"',
  })
  assert.equal(scanProductionMockViolations(root, root).length, 1)
})

test("retains the legacy contract mock marker check", () => {
  const root = workspace({ "feature.ts": "const M1_CONTRACT_MOCK = {}" })
  assert.equal(scanProductionMockViolations(root, root).length, 1)
})
