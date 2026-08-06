import { expect, test } from "bun:test"

import { readFileSync } from "node:fs"
import { resolve } from "node:path"

const source = readFileSync(
  resolve(
    import.meta.dir,
    "../src/routes/_layout/projects.$projectId_.evidence.tsx",
  ),
  "utf8",
)
const mutationSource = readFileSync(
  resolve(import.meta.dir, "../src/features/evidence-workspace/mutations.ts"),
  "utf8",
)

test("M7 production route uses the frozen workspace integration chain", () => {
  expect(source).toContain(
    'createFileRoute("/_layout/projects/$projectId_/evidence")',
  )
  expect(source).toContain("parseEvidenceWorkspaceSearch")
  expect(source).toContain("EvidenceWorkspaceContainer")
  expect(source).toContain("View={EvidenceWorkspace}")
  expect(source).not.toContain("fixtures")
  expect(source).not.toContain("fetch(")
})

test("M7 route preserves authority and server-response navigation boundaries", () => {
  expect(source).toContain('case "expand-graph-node"')
  expect(source).toContain(
    'updateSearch({ node: event.nodeId, view: "graph" })',
  )
  expect(source).not.toContain("connect")
  expect(source).toContain('nested(data, "audit_result")')
  expect(source).toContain('nested(data, "export")')
  expect(source).toContain('nested(data, "download")')
  expect(source).toContain("window.location.assign(downloadUrl)")
})

test("M7 Export confirmation covers every server-projected Approval item", () => {
  expect(mutationSource).toContain("workspace.approval?.items.map")
  expect(mutationSource).toContain('decision: "ACCEPT"')
  expect(mutationSource).toContain("item_decisions:")
  expect(mutationSource).not.toContain(
    "ApprovalsApi.approve(event.approvalId, {},",
  )
})
