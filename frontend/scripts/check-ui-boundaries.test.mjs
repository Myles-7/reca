import assert from "node:assert/strict"
import fs from "node:fs"
import os from "node:os"
import path from "node:path"
import test from "node:test"

import { forbiddenUiImports, scanUiBoundaries } from "./check-ui-boundaries.mjs"

test("allows pure UI dependencies and project models", () => {
  const source = `
    import { Button } from "@/components/ui/button"
    import type { ProjectViewModel } from "../model"
    export { Badge } from "@/components/ui/badge"
  `

  assert.deepEqual(forbiddenUiImports(source), [])
})

test("rejects transport, query, mutation, and controller dependencies", () => {
  const source = `
    import { ProjectsApi } from "@/api/adapter"
    import type { ProjectPublic } from "@/api/generated"
    import { useQuery } from "@tanstack/react-query"
    import { projectCommands } from "../controller"
    import { useProjectMutation } from "../mutations"
    export { useProject } from "../queries"
  `

  assert.deepEqual(forbiddenUiImports(source), [
    "@/api/adapter",
    "@/api/generated",
    "@tanstack/react-query",
    "../controller",
    "../mutations",
    "../queries",
  ])
})

test("rejects dynamic imports of forbidden feature modules", () => {
  const source = `const module = await import("../../projects/queries")`

  assert.deepEqual(forbiddenUiImports(source), ["../../projects/queries"])
})

test("scans nested feature UI directories", (context) => {
  const temporaryRoot = fs.mkdtempSync(
    path.join(os.tmpdir(), "reca-ui-boundaries-"),
  )
  context.after(() =>
    fs.rmSync(temporaryRoot, { recursive: true, force: true }),
  )
  const uiDirectory = path.join(
    temporaryRoot,
    "features",
    "literature",
    "review",
    "ui",
  )
  fs.mkdirSync(uiDirectory, { recursive: true })
  fs.writeFileSync(
    path.join(uiDirectory, "ReviewPanel.tsx"),
    'import { useReview } from "../queries"\n',
  )

  assert.deepEqual(
    scanUiBoundaries(path.join(temporaryRoot, "features"), temporaryRoot),
    [
      {
        file: path.join(
          "features",
          "literature",
          "review",
          "ui",
          "ReviewPanel.tsx",
        ),
        imports: ["../queries"],
      },
    ],
  )
})
