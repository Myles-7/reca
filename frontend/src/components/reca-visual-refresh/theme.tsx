import { createContext, type ReactNode, useContext } from "react"

export type VisualTheme = "light" | "dark"

const VisualThemeContext = createContext<VisualTheme | undefined>(undefined)

export function VisualThemeProvider({
  theme,
  children,
}: {
  theme: VisualTheme
  children: ReactNode
}) {
  return (
    <VisualThemeContext.Provider value={theme}>
      {children}
    </VisualThemeContext.Provider>
  )
}

export function useVisualTheme() {
  return useContext(VisualThemeContext)
}
