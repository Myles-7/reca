import { StrictMode } from "react"
import ReactDOM from "react-dom/client"

import { ThemeProvider } from "@/components/theme-provider"

import "../index.css"
import "../components/reca-visual-refresh/visual-refresh.css"
import "./design-preview-workbench.css"
import "./visual-foundations-preview.css"
import { DesignPreviewWorkbench } from "./DesignPreviewWorkbench"

declare const __RECA_OPEN_DESIGN_STATIC__: boolean

const isOpenDesignStatic =
  typeof __RECA_OPEN_DESIGN_STATIC__ !== "undefined" &&
  __RECA_OPEN_DESIGN_STATIC__

if (!import.meta.env.DEV && !isOpenDesignStatic) {
  throw new Error(
    "The design fixture preview is available only in development.",
  )
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ThemeProvider defaultTheme="dark" storageKey="reca-design-preview-theme">
      <DesignPreviewWorkbench />
    </ThemeProvider>
  </StrictMode>,
)
