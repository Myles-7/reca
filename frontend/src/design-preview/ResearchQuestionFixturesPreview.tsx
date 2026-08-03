import { useState } from "react"

import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { researchQuestionFixtures } from "@/features/research-question/fixtures"
import { ResearchQuestionWorkspace } from "@/features/research-question/ui/ResearchQuestionWorkspace"

export function ResearchQuestionFixturesPreview() {
  const [fixtureId, setFixtureId] = useState<string>(
    researchQuestionFixtures[0].id,
  )
  const fixture =
    researchQuestionFixtures.find((item) => item.id === fixtureId) ??
    researchQuestionFixtures[0]

  return (
    <main
      className="mx-auto min-h-screen max-w-6xl space-y-6 px-4 py-6 sm:px-6"
      data-fixture-id={fixture.id}
    >
      <div className="ml-auto w-64 space-y-2">
        <Label htmlFor="research-question-fixture">Fixture</Label>
        <Select value={fixture.id} onValueChange={setFixtureId}>
          <SelectTrigger id="research-question-fixture">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {researchQuestionFixtures.map((item) => (
              <SelectItem key={item.id} value={item.id}>
                {item.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <ResearchQuestionWorkspace key={fixture.id} {...fixture.props} />
    </main>
  )
}
