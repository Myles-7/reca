import { createFileRoute } from "@tanstack/react-router"

import NotFound from "@/components/Common/NotFound"

export const Route = createFileRoute("/404")({
  component: NotFound,
  head: () => ({ meta: [{ title: "Page not found | RECA" }] }),
})
