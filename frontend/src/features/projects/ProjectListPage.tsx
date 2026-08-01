import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import { ArrowRight, FolderKanban, Plus } from "lucide-react"
import { type FormEvent, useState } from "react"

import {
  EmptyState,
  ErrorState,
  LoadingState,
} from "@/components/Common/PageState"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

import { projectCommands } from "./controller"
import { mapUiError } from "./mappers"
import type { ProjectCreateCommand, ProjectTypeOption } from "./model"
import { projectKeys, useProjects } from "./queries"

const projectTypes: ProjectTypeOption[] = [
  "RESEARCH",
  "THESIS",
  "COURSE",
  "INNOVATION",
  "DEMO",
]

export function ProjectListPage() {
  const queryClient = useQueryClient()
  const projects = useProjects()
  const [open, setOpen] = useState(false)
  const [projectType, setProjectType] = useState<ProjectTypeOption>("RESEARCH")
  const createProject = useMutation({
    mutationFn: projectCommands.create,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: projectKeys.all })
      setOpen(false)
    },
  })

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const data = new FormData(event.currentTarget)
    const input: ProjectCreateCommand = {
      name: String(data.get("name") ?? "").trim(),
      description: String(data.get("description") ?? "").trim() || null,
      discipline: String(data.get("discipline") ?? "").trim() || null,
      projectType,
    }
    createProject.mutate(input)
  }

  return (
    <section aria-labelledby="projects-title" className="space-y-6">
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 id="projects-title" className="text-2xl font-semibold">
            Projects
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Research workspaces available to your account.
          </p>
        </div>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus aria-hidden="true" />
              New project
            </Button>
          </DialogTrigger>
          <DialogContent>
            <form className="space-y-5" onSubmit={submit}>
              <DialogHeader>
                <DialogTitle>Create project</DialogTitle>
                <DialogDescription>
                  The creator becomes the project owner.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-2">
                <Label htmlFor="project-name">Name</Label>
                <Input id="project-name" name="name" required maxLength={200} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="project-description">Description</Label>
                <Input
                  id="project-description"
                  name="description"
                  maxLength={2000}
                />
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="project-discipline">Discipline</Label>
                  <Input
                    id="project-discipline"
                    name="discipline"
                    maxLength={200}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Project type</Label>
                  <Select
                    value={projectType}
                    onValueChange={(value) =>
                      setProjectType(value as ProjectTypeOption)
                    }
                  >
                    <SelectTrigger className="w-full" aria-label="Project type">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {projectTypes.map((type) => (
                        <SelectItem key={type} value={type}>
                          {type}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              {createProject.error ? (
                <ErrorState message={mapUiError(createProject.error).message} />
              ) : null}
              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setOpen(false)}
                >
                  Cancel
                </Button>
                <Button disabled={createProject.isPending} type="submit">
                  {createProject.isPending ? "Creating..." : "Create"}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </header>

      {projects.isLoading ? <LoadingState label="Loading projects" /> : null}
      {projects.error ? (
        <ErrorState message={mapUiError(projects.error).message} />
      ) : null}
      {projects.data?.length === 0 ? (
        <EmptyState>No projects are available.</EmptyState>
      ) : null}
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {projects.data?.map((project) => (
          <article key={project.id} className="rounded-lg border bg-card p-5">
            <div className="flex items-start justify-between gap-3">
              <FolderKanban
                aria-hidden="true"
                className="mt-0.5 size-5 text-primary"
              />
              <Badge variant="outline">{project.status}</Badge>
            </div>
            <h2 className="mt-4 font-semibold">{project.name}</h2>
            <p className="mt-2 min-h-10 text-sm text-muted-foreground">
              {project.description || "No description"}
            </p>
            <div className="mt-4 flex items-center justify-between gap-3 text-xs text-muted-foreground">
              <span>{project.stage}</span>
              <span>{project.updatedAt}</span>
            </div>
            <Button asChild className="mt-5 w-full" variant="outline">
              <Link
                to="/projects/$projectId"
                params={{ projectId: project.id }}
              >
                Open workspace
                <ArrowRight aria-hidden="true" />
              </Link>
            </Button>
          </article>
        ))}
      </div>
    </section>
  )
}
