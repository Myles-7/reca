import { useState } from "react"

import { projectWorkspaceFixtures } from "@/features/projects/fixtures"

import { ProjectWorkspacePreview } from "./ProjectWorkspacePreview"

export function ProjectFixturesPreview() {
  const [fixtureId, setFixtureId] = useState(projectWorkspaceFixtures[0].id)
  const fixture =
    projectWorkspaceFixtures.find((item) => item.id === fixtureId) ??
    projectWorkspaceFixtures[0]

  return (
    <main data-fixture-id={fixture.id}>
      <div className="project-standalone-fixture-control">
        <label htmlFor="design-fixture">Fixture</label>
        <select
          id="design-fixture"
          value={fixture.id}
          onChange={(event) => setFixtureId(event.target.value)}
        >
          {projectWorkspaceFixtures.map((item) => (
            <option key={item.id} value={item.id}>
              {item.label}
            </option>
          ))}
        </select>
      </div>
      <div className="reca-visual-refresh">
        <ProjectWorkspacePreview fixture={fixture} />
      </div>
    </main>
  )
}
