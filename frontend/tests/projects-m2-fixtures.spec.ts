import { expect, test } from "@playwright/test"

import { documentFixtures } from "../src/features/documents/fixtures"
import { literatureFixtures } from "../src/features/literature/fixtures"
import { projectWorkspaceFixtures } from "../src/features/projects/fixtures"
import { queryPlanFixtures } from "../src/features/query-plan/fixtures"
import { researchQuestionFixtures } from "../src/features/research-question/fixtures"

const fixtureRegistries = [
  queryPlanFixtures,
  literatureFixtures,
  documentFixtures,
  researchQuestionFixtures,
  projectWorkspaceFixtures,
] as const

test("M2 fixture registries describe one independent UI behavior per fixture", () => {
  for (const fixtures of fixtureRegistries) {
    expect(new Set(fixtures.map((fixture) => fixture.id)).size).toBe(
      fixtures.length,
    )
    for (const fixture of fixtures) {
      expect(fixture.behavior.trim().length).toBeGreaterThan(0)
    }
  }

  expect(queryPlanFixtures.map((fixture) => fixture.id)).toEqual(
    expect.arrayContaining([
      "load-error",
      "forbidden",
      "read-only",
      "permissions-unknown",
      "update-pending",
      "generate-pending",
      "mutation-conflict",
      "long-content",
    ]),
  )
  expect(literatureFixtures.map((fixture) => fixture.id)).toEqual(
    expect.arrayContaining([
      "no-active-search",
      "empty-result",
      "load-error",
      "forbidden",
      "read-only",
      "permissions-unknown",
      "search-pending",
      "candidate-import-pending",
      "doi-import-pending",
      "mutation-error",
      "long-metadata",
    ]),
  )
  expect(documentFixtures.map((fixture) => fixture.id)).toEqual(
    expect.arrayContaining([
      "draft",
      "queued",
      "grobid-completed",
      "failed-retryable",
      "failed-non-retryable",
      "load-error",
      "forbidden",
      "read-only",
      "upload-pending",
      "parse-pending",
      "retry-pending",
      "mutation-error",
      "scanned",
    ]),
  )
  expect(researchQuestionFixtures.map((fixture) => fixture.id)).toEqual(
    expect.arrayContaining([
      "needs-input",
      "confirmed",
      "read-only",
      "save-pending",
      "mark-ready-pending",
      "mutation-conflict",
    ]),
  )
  expect(projectWorkspaceFixtures.map((fixture) => fixture.id)).toEqual(
    expect.arrayContaining([
      "failed-retryable-job",
      "active-cancelable-job",
      "stale-no-actions-approval",
      "project-status-unknown",
      "project-permissions-unknown",
    ]),
  )
})

test("fixture-only formal actions remain driven by existing typed projections", () => {
  const queryReadOnly = queryPlanFixtures.find(
    (fixture) => fixture.id === "read-only",
  )
  expect(queryReadOnly?.props.content).toMatchObject({
    state: "ready",
    data: { permissions: { canUpdate: false, canGenerate: false } },
  })

  const retryableDocument = documentFixtures.find(
    (fixture) => fixture.id === "failed-retryable",
  )
  expect(retryableDocument?.props.content).toMatchObject({
    state: "ready",
    data: { job: { status: "FAILED", retryable: true } },
  })

  const staleApproval = projectWorkspaceFixtures.find(
    (fixture) => fixture.id === "stale-no-actions-approval",
  )
  expect(staleApproval?.approvals.content).toMatchObject({
    state: "ready",
    data: [{ stale: true, status: "SUPERSEDED" }],
  })
  if (staleApproval?.approvals.content.state === "ready") {
    expect(staleApproval.approvals.content.data[0].allowedActions.size).toBe(0)
  }
})
