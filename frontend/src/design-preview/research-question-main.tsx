import { StrictMode } from "react"
import ReactDOM from "react-dom/client"

import { ThemeProvider } from "@/components/theme-provider"

import "../index.css"
import { ResearchQuestionFixturesPreview } from "./ResearchQuestionFixturesPreview"

if (!import.meta.env.DEV) {
  throw new Error(
    "The design fixture preview is available only in development.",
  )
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ThemeProvider defaultTheme="dark" storageKey="reca-design-preview-theme">
      <ResearchQuestionFixturesPreview />
    </ThemeProvider>
  </StrictMode>,
)
