import { createFileRoute } from "@tanstack/react-router"

import { ProjectListPage } from "@/features/projects/ProjectListPage"

export const Route = createFileRoute("/_layout/projects/")({
  component: ProjectListPage,
  head: () => ({ meta: [{ title: "Projects - RECA" }] }),
})
